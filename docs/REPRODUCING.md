# 生成与复现说明

## 1 直接查看现有材料

不需要 Python、CosyVoice 或模型。完整解压，打开 index.html。Windows 分组入口与操作说明见 README.zh-CN.md。

## 2 生成三个证据网页

只用 Python 标准库，无第三方包依赖。在仓库根目录运行：

```bash
python generators/generate_formal_evidence_html.py
```

输出到 generated/evidence_html，不覆盖 experiments/formal_v01/html 中的研究时材料。也可以指定输出目录：

```bash
python generators/generate_formal_evidence_html.py --output-dir generated/check
```

输入为 fact_sheets/formal_fact_sheets.json、topics/formal_source_manifest.json、四份保留原始行序的来源文本。模板写在 Python 程序中，无需寻找独立模板文件。请勿随意删除来源文本空行，否则行号引用会改变。

原服务器程序与复制到本包后的修改说明见 CODE-CHANGES.md；网页正文、HTML 和 CSS 未改。一次本地重建得到 7/7/9 个条目，输出文本与已有三页完全一致。

## 3 只检查语音文本

```bash
python generators/generate_formal_audio.py --scripts-only
```

该选项不加载 Torch、模型或参考音频，仅验证 8 个 JSON 文件的条件、文本、角色和话轮结构。结构通过不等于人工事实核查通过。

## 4 重新合成候选音频

以下步骤适用于已有 CosyVoice 环境的机器。本次没有重新运行 GPU 合成，也没有确认原服务器依赖锁定版本。

需要：CosyVoice 代码及其子模块、与该版本兼容的 Python/Torch/TorchAudio 依赖、模型目录、asset/zero_shot_prompt.wav、asset/cross_lingual_prompt.wav，以及 PATH 中的 FFmpeg。按 [CosyVoice 官方项目](https://github.com/QwenAudio/CosyVoice) 对应版本的安装说明准备，不把最新环境自动视为原研究环境。

程序的默认外部目录是 vendor/CosyVoice。也可以用环境变量指定，以下路径必须替换为你机器上已存在的实际路径：

```bash
export COSYVOICE_ROOT="/path/to/CosyVoice"
export COSYVOICE_MODEL_DIR="/path/to/model-checkpoint"
python generators/generate_formal_audio.py --validate-only
python generators/generate_formal_audio.py --output-root generated/audio
```

Windows PowerShell 的等价配置：

```powershell
$env:COSYVOICE_ROOT = "D:\path\to\CosyVoice"
$env:COSYVOICE_MODEL_DIR = "D:\path\to\model-checkpoint"
python generators/generate_formal_audio.py --validate-only
python generators/generate_formal_audio.py --output-root generated/audio
```

validate-only 检查文件和 FFmpeg 是否存在，不验证模型加载或完整依赖兼容性。默认输出 generated/audio；已有同名音频会跳过，除非明确传入 --overwrite。不要用正式音频目录作为尝试生成的输出目录。

原脚本默认模型文件夹名为 Fun-CosyVoice3-0.5B，生成清单中的模型标签写作 Fun-CosyVoice3-0.5B-2512；文件夹名和标签不能替代检查点哈希。原模型实际文件版本仍需从服务器记录确认。

## 5 最终音频与生成候选的区别

正式发布音频中，部分文件的 manifest 带有 assembly_version 和 segment_selections，是人工挑选候选片段后拼接的结果。本次代码包中没有完整的候选生成、挑选和最终拼接可执行流水线；也未包含候选片段或模型权重。

原合成程序支持 --seed、--jobs、--overwrite、--output-root。本次保留原切句、声音提示、响度处理和随机种子算法。由于原算法会根据选中任务在列表中的序号计算种子，单独执行 --jobs 不能直接假定与完整批次中该任务的种子一致。应记录完整命令、选中任务顺序、模型/声音样本哈希、软件版本和人工拼接选择。

实际演示使用现有正式 WAV 即可；完整音频再现是后续补充工作。
