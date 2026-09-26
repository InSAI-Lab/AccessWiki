#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import shutil
import sys
from datetime import datetime
from pathlib import Path



PROJECT_ROOT = Path(__file__).resolve().parents[1]
COSYVOICE_ROOT = Path(os.environ.get("COSYVOICE_ROOT", str(PROJECT_ROOT / "vendor/CosyVoice"))).expanduser().resolve()
MODEL_DIR = Path(os.environ.get("COSYVOICE_MODEL_DIR", str(COSYVOICE_ROOT / "pretrained_models/Fun-CosyVoice3-0.5B"))).expanduser().resolve()

SCRIPT_DIR = PROJECT_ROOT / "experiments/formal_v01/scripts"
OUTPUT_ROOT = PROJECT_ROOT / "generated/audio"

TAIL_GUARD_TEXT = "本段内容结束。"
CLOSING_SILENCE_SECONDS = 0.8

NEUTRAL_PROMPT = COSYVOICE_ROOT / "asset/zero_shot_prompt.wav"
HOST_A_PROMPT = COSYVOICE_ROOT / "asset/zero_shot_prompt.wav"
HOST_B_PROMPT = (
    COSYVOICE_ROOT / "asset/cross_lingual_prompt.wav"
)

JOBS = [
    "rail_travel_neutral_correct.json",
    "rail_travel_conversational_correct.json",
    "hospital_visit_neutral_correct.json",
    "hospital_visit_conversational_correct.json",
    "online_returns_neutral_correct.json",
    "online_returns_conversational_correct.json",
    "online_returns_neutral_incorrect.json",
    "hospital_visit_conversational_incorrect.json",
]

INSTRUCTIONS = {
    "narrator": (
        "You are a helpful assistant. "
        "请使用平稳、中性、克制的中文播报语气。"
        "语速适中，咬字清楚，不加入笑声、夸张情绪或对话感。"
        "<|endofprompt|>"
    ),
    "host_a": (
        "You are a helpful assistant. "
        "请使用自然、清晰、平稳、克制的中文主持人口吻。"
        "保持适度亲切感，但不要表演、撒娇或突然改变音色。"
        "不要笑，不要发出吸气声、叹气声、咳嗽声或其他非语言声音。"
        "疑问句只做轻微自然上扬，不要突然提高音高或拖长尾音。"
        "语速适中，完整、稳定地读完每句话。"
        "<|endofprompt|>"
    ),
    "host_b": (
        "You are a helpful assistant. "
        "请使用自然、清晰、沉稳、克制的中文主持人口吻。"
        "保持稳定音色和适度回应感，不要使用表演化或做作的语气。"
        "不要笑，不要发出吸气声、叹气声、咳嗽声或其他非语言声音。"
        "不要突然升高音调，不要拖长尾音，语速适中。"
        "完整、稳定地读完每句话。"
        "<|endofprompt|>"
    ),
}

PROMPTS = {
    "narrator": NEUTRAL_PROMPT,
    "host_a": HOST_A_PROMPT,
    "host_b": HOST_B_PROMPT,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="AccessWiki正式实验音频批量生成器"
    )
    parser.add_argument(
        "--scripts-only", action="store_true",
        help="Validate the eight script JSON files without models, audio dependencies, or synthesis",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="只检查脚本和参考音频，不加载模型",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="覆盖已存在的正式音频",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260903,
    )
    parser.add_argument(
        "--jobs",
        nargs="+",
        help="只生成指定任务；可填写不带.json的任务名",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=OUTPUT_ROOT,
        help="独立输出目录，避免覆盖已通过的音频",
    )
    return parser.parse_args()


def clean_text(text):
    return re.sub(r"\s+", "", text).strip()


def split_neutral_text(text):
    text = clean_text(text)
    parts = re.split(r"(?<=[。！？；])", text)
    parts = [part for part in parts if part]

    chunks = []
    current = ""

    for part in parts:
        if current and len(current) + len(part) > 95:
            chunks.append(current)
            current = part
        else:
            current += part

    if current:
        chunks.append(current)

    return chunks


def validate_inputs(check_runtime=True):
    failures = []

    if check_runtime:
        if not (COSYVOICE_ROOT / "cosyvoice").is_dir():
            failures.append(f"CosyVoice代码目录不存在：{COSYVOICE_ROOT}")
        if not MODEL_DIR.is_dir():
            failures.append(f"模型目录不存在：{MODEL_DIR}")
        for prompt_path in set(PROMPTS.values()):
            if not prompt_path.is_file():
                failures.append(f"参考音频不存在：{prompt_path}")
        if shutil.which("ffmpeg") is None:
            failures.append("FFmpeg不在PATH中")

    expected_conditions = {
        "neutral_single_speaker",
        "conversational_two_speaker",
    }

    summaries = []

    for filename in JOBS:
        path = SCRIPT_DIR / filename

        if not path.is_file():
            failures.append(f"脚本不存在：{path}")
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append(f"脚本读取失败：{path}: {exc}")
            continue

        condition = data.get("condition")
        if condition not in expected_conditions:
            failures.append(
                f"{filename} condition异常：{condition}"
            )
            continue

        if condition == "neutral_single_speaker":
            if not clean_text(data.get("text", "")):
                failures.append(f"{filename} 缺少text")
        else:
            turns = data.get("turns", [])
            if not turns:
                failures.append(f"{filename} 缺少turns")

            for turn in turns:
                if turn.get("speaker") not in {"host_a", "host_b"}:
                    failures.append(
                        f"{filename} 主播异常：{turn.get('speaker')}"
                    )
                if not clean_text(turn.get("text", "")):
                    failures.append(
                        f"{filename} 存在空话轮"
                    )

        summaries.append(
            {
                "file": filename,
                "topic_id": data.get("topic_id"),
                "condition": condition,
                "variant": data.get("variant"),
                "characters": data.get("spoken_character_count"),
                "estimated_seconds": data.get(
                    "estimated_duration_seconds"
                ),
            }
        )

    if failures:
        print("\n".join(f"FAIL: {item}" for item in failures))
        raise SystemExit("FORMAL_AUDIO_INPUT_VALIDATION_FAILED")

    for summary in summaries:
        print(
            f"{summary['file']} | "
            f"{summary['condition']} | "
            f"{summary['variant']} | "
            f"{summary['characters']}字 | "
            f"预计{summary['estimated_seconds']}秒"
        )

    print(f"VALID_JOBS: {len(summaries)}")
    print("FORMAL_AUDIO_INPUTS_OK")


def fade_audio(audio, sample_rate):
    fade_length = min(
        int(sample_rate * 0.015),
        audio.shape[-1] // 4,
    )

    if fade_length > 0:
        fade_in = torch.linspace(
            0,
            1,
            fade_length,
            dtype=audio.dtype,
        )
        fade_out = torch.linspace(
            1,
            0,
            fade_length,
            dtype=audio.dtype,
        )
        audio[:, :fade_length] *= fade_in
        audio[:, -fade_length:] *= fade_out

    return audio


def synthesize_segment(
    cosyvoice,
    text,
    speaker,
    seed,
):
    from cosyvoice.utils.common import set_all_random_seed

    set_all_random_seed(seed)

    chunks = []

    for result in cosyvoice.inference_instruct2(
        clean_text(text),
        INSTRUCTIONS[speaker],
        str(PROMPTS[speaker]),
        stream=False,
    ):
        chunks.append(result["tts_speech"].cpu())

    if not chunks:
        raise RuntimeError("没有生成任何音频")

    audio = torch.cat(chunks, dim=-1)
    return fade_audio(audio, cosyvoice.sample_rate)


def build_units(data):
    condition = data["condition"]

    if condition == "neutral_single_speaker":
        chunks = split_neutral_text(data["text"])
        claim_ids = data.get("evidence_claim_ids", [])

        return [
            {
                "turn_id": f"N{index:02d}",
                "speaker": "narrator",
                "text": text,
                "evidence_claim_ids": claim_ids,
            }
            for index, text in enumerate(chunks, start=1)
        ]

    units = []

    for turn in data["turns"]:
        turn_text = clean_text(turn["text"])
        parts = re.split(r"(?<=[。！？；，])", turn_text)
        parts = [part for part in parts if part]

        chunks = []
        current = ""

        for part in parts:
            if current and len(current) + len(part) > 52:
                chunks.append(current)
                current = part
            else:
                current += part

        if current:
            chunks.append(current)

        for part_index, chunk in enumerate(chunks, start=1):
            turn_id = turn["turn_id"]

            if len(chunks) > 1:
                turn_id = f"{turn_id}_{part_index:02d}"

            units.append(
                {
                    "turn_id": turn_id,
                    "speaker": turn["speaker"],
                    "text": chunk,
                    "evidence_claim_ids": turn.get(
                        "evidence_claim_ids", []
                    ),
                }
            )

    return units


def generate_one(
    cosyvoice,
    script_path,
    job_index,
    base_seed,
    overwrite,
    output_root,
):
    data = json.loads(script_path.read_text(encoding="utf-8"))
    version = script_path.stem
    output_dir = output_root / version
    segment_dir = output_dir / "segments"
    final_path = output_dir / f"{version}.wav"

    if final_path.is_file() and not overwrite:
        print(f"{version}: SKIPPED_EXISTING")
        return {
            "version": version,
            "status": "skipped_existing",
            "final_file": str(final_path),
        }

    segment_dir.mkdir(parents=True, exist_ok=True)

    units = build_units(data)
    sample_rate = cosyvoice.sample_rate

    opening_silence = torch.zeros(
        1,
        int(sample_rate * 0.4),
    )

    gap_seconds = (
        0.28
        if data["condition"] == "neutral_single_speaker"
        else 0.38
    )

    between_silence = torch.zeros(
        1,
        int(sample_rate * gap_seconds),
    )

    closing_silence = torch.zeros(
        1,
        int(sample_rate * CLOSING_SILENCE_SECONDS),
    )

    full_parts = [opening_silence]
    manifest_turns = []

    for unit_index, unit in enumerate(units, start=1):
        seed = (
            base_seed
            + job_index * 100
            + unit_index
        )

        print(
            f"[{version}] "
            f"[{unit_index:02d}/{len(units):02d}] "
            f"{unit['speaker']}"
        )
        print(unit["text"])

        is_final_unit = unit_index == len(units)
        synthesis_text = unit["text"]

        if is_final_unit:
            synthesis_text += TAIL_GUARD_TEXT

        audio = synthesize_segment(
            cosyvoice=cosyvoice,
            text=synthesis_text,
            speaker=unit["speaker"],
            seed=seed,
        )

        segment_name = (
            f"{unit['turn_id']}_{unit['speaker']}.wav"
        )
        segment_path = segment_dir / segment_name

        torchaudio.save(
            str(segment_path),
            audio,
            sample_rate,
        )

        duration = audio.shape[-1] / sample_rate

        manifest_turns.append(
            {
                "turn_id": unit["turn_id"],
                "speaker": unit["speaker"],
                "text": unit["text"],
                "synthesis_text": synthesis_text,
                "tail_guard_added": is_final_unit,
                "seed": seed,
                "duration_seconds": round(duration, 3),
                "segment_file": str(segment_path),
                "prompt_wav": str(PROMPTS[unit["speaker"]]),
                "evidence_claim_ids": unit[
                    "evidence_claim_ids"
                ],
            }
        )

        full_parts.append(audio)

        if unit_index < len(units):
            full_parts.append(between_silence)

    full_parts.append(closing_silence)
    full_audio = torch.cat(full_parts, dim=-1)

    raw_path = output_dir / f"{version}_raw.wav"
    manifest_path = output_dir / "manifest.json"

    torchaudio.save(
        str(raw_path),
        full_audio,
        sample_rate,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(raw_path),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            str(final_path),
        ],
        check=True,
    )

    final_audio, final_rate = torchaudio.load(str(final_path))
    final_duration = final_audio.shape[-1] / final_rate

    manifest = {
        "version": version,
        "topic_id": data["topic_id"],
        "condition": data["condition"],
        "variant": data["variant"],
        "model": "Fun-CosyVoice3-0.5B-2512",
        "sample_rate_hz": final_rate,
        "channels": int(final_audio.shape[0]),
        "duration_seconds": round(final_duration, 3),
        "loudness_target": "I=-16 LUFS, TP=-1.5 dB, LRA=11",
        "source_script": str(script_path),
        "manipulation": data.get("manipulation"),
        "turns": manifest_turns,
        "auditory_qc": "not_performed",
    }

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    duration_status = (
        "within_target"
        if 55 <= final_duration <= 90
        else "outside_target"
    )

    print(
        f"{version}: GENERATED | "
        f"{final_duration:.2f}s | "
        f"{duration_status}"
    )

    return {
        "version": version,
        "status": "generated",
        "duration_seconds": round(final_duration, 3),
        "duration_status": duration_status,
        "final_file": str(final_path),
        "manifest_file": str(manifest_path),
    }


def main():
    args = parse_args()
    output_root = args.output_root.expanduser().resolve()
    validate_inputs(check_runtime=not args.scripts_only)

    if args.scripts_only or args.validate_only:
        return

    global torch, torchaudio
    import torch
    import torchaudio

    sys.path.insert(0, str(COSYVOICE_ROOT))
    sys.path.append(
        str(COSYVOICE_ROOT / "third_party/Matcha-TTS")
    )
    os.chdir(COSYVOICE_ROOT)

    from cosyvoice.cli.cosyvoice import AutoModel

    output_root.mkdir(parents=True, exist_ok=True)

    requested_jobs = set(args.jobs or [])
    selected_jobs = []

    for filename in JOBS:
        stem = Path(filename).stem

        if not requested_jobs:
            selected_jobs.append(filename)
        elif filename in requested_jobs or stem in requested_jobs:
            selected_jobs.append(filename)

    if requested_jobs:
        matched_names = {
            name
            for filename in selected_jobs
            for name in (filename, Path(filename).stem)
        }
        unknown_jobs = sorted(requested_jobs - matched_names)

        if unknown_jobs:
            raise ValueError(
                "未知任务名称：" + ", ".join(unknown_jobs)
            )

    print(f"OUTPUT_ROOT={output_root}")
    print(f"SELECTED_JOBS={len(selected_jobs)}")
    print("开始加载CosyVoice 3……")

    cosyvoice = AutoModel(
        model_dir=str(MODEL_DIR)
    )

    results = []

    for job_index, filename in enumerate(selected_jobs):
        results.append(
            generate_one(
                cosyvoice=cosyvoice,
                script_path=SCRIPT_DIR / filename,
                job_index=job_index,
                base_seed=args.seed,
                overwrite=args.overwrite,
                output_root=output_root,
            )
        )

    batch_manifest = {
        "created": datetime.now().astimezone().isoformat(),
        "model": "Fun-CosyVoice3-0.5B-2512",
        "job_count": len(results),
        "results": results,
        "auditory_qc": "not_performed",
    }

    batch_manifest_path = (
        output_root / "formal_audio_batch_manifest.json"
    )

    batch_manifest_path.write_text(
        json.dumps(
            batch_manifest,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"BATCH_MANIFEST={batch_manifest_path}")
    print("ACCESSWIKI_FORMAL_AUDIO_OK")


if __name__ == "__main__":
    main()
