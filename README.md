# AccessWiki

**Conversational audio and source evidence for accessible document reading.**

[中文说明](README.zh-CN.md) · [Reproduction guide](docs/REPRODUCING.md) · [Validation](docs/VALIDATION.md)

AccessWiki pairs prerecorded audio overviews with screen-reader-friendly evidence pages. It provides neutral single-speaker narration and two-speaker question–answer dialogue for railway travel, hospital visits, and online returns. Both audio formats share the evidence page for each topic. Bus travel is used for practice.

This repository packages the existing research prototype, formal stimulus scripts, evidence-page generator, speech-generation program, and Windows group launcher. It does not include participant responses or identifiable research records.

## Try the materials

Download and extract the repository, then open **index.html** in a browser. The entry page links to source materials, audio players, and Evidence HTML. Playback uses the included WAV files and does not require Python, a model, or an API key.

GitHub's file preview does not run HTML. Download the repository to use the pages locally; online hosting is a separate setup step.

## Windows group launcher

Double-click **Launch-AccessWiki.cmd** and select group 1–6, or run this from the repository directory:

```powershell
powershell.exe -NoExit -NoProfile -ExecutionPolicy Bypass -File ".\Start-AccessWiki.ps1" -Group G6
```

The launcher then requests a predefined session ID; G6 accepts P06 or P12. These IDs select the schedule and do not load participant data. See the [group table and menu instructions](README.zh-CN.md).

| Paper condition | Material label | Configuration |
|---|---|---|
| M1 | B1 | Screen-reader source access, including accessible source replacements |
| M2 | B2 | Single-speaker narration + Evidence HTML |
| M3 | P | Two-speaker Q&A dialogue + the same Evidence HTML |

Researchers manually switched materials and interleaved questions during the actual sessions. The menu is a material-access tool, not a playback log or an automated reconstruction of individual sessions.

## Generate Evidence HTML

Using Python 3, run from the repository directory:

```bash
python generators/generate_formal_evidence_html.py
```

The three regenerated pages and their manifest are written to `generated/evidence_html/`, preserving the included study pages. This command uses only the Python standard library. The source text, fact sheets, source metadata and inline HTML template are included.

## Speech generation

Check the eight script JSON files without installing speech dependencies:

```bash
python generators/generate_formal_audio.py --scripts-only
```

New synthesis requires an external CosyVoice installation, compatible Torch/TorchAudio, model files, reference voices, and FFmpeg. See [setup and commands](docs/REPRODUCING.md). Existing WAV files remain the reference playback assets. Some final stimuli were assembled from manually selected candidate segments; the batch generator alone is not a verified reconstruction of those final files.

## Repository layout

```text
index.html                         Material browser
Launch-AccessWiki.cmd               Windows group selection
Start-AccessWiki.ps1                Portable launcher entry
generators/                        Formal HTML and speech generators
experiments/formal_v01/
  audio/                           Eight formal WAV stimuli and manifests
  scripts/                         Eight speech-script JSON files
  fact_sheets/                     Claims and source-line references
  html/                            Three original Evidence HTML pages
  launch/                          Audio/source/task entry pages
  b1_sources/                      Source snapshots and accessible replacements
  practice/ and clips/             Bus practice assets
  AccessWiki_组别快捷启动器/          Group launcher
topics/                            Required source text and source metadata
docs/                              Usage, provenance and verification notes
```

## Verification and limitations

- All three regenerated Evidence HTML files match the supplied study pages as UTF-8 text: 7 railway, 7 hospital and 9 returns entries.
- All eight speech scripts pass input-structure validation.
- G1–G6 resolve all 12 launcher bindings.
- The nine included WAV files, including practice, retain their original hashes.

This packaging check does not establish NVDA usability, synthesis equivalence, or autonomous participant navigation. Original third-party website snapshots retain missing site assets/navigation dependencies. Those issues are documented separately from the generated evidence pages. Deliberately incorrect audio is provided only as controlled research stimuli, not factual guidance.

## Paper and licensing

Associated manuscript: *AccessWiki: Conversational Audio and Source Evidence for Helping the Blind in Accessible Document Reading*. No publication acceptance is asserted here.

This package does not include participant spreadsheets, consent forms, questionnaires, interview recordings, or participant photos. Source and voice-material attribution and redistribution terms must be confirmed by the maintainers. No blanket project license has been selected; see [NOTICE.md](NOTICE.md).
