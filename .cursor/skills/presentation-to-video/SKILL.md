---
name: presentation-to-video
description: >-
  从 PPT 目录（slides.marp.md + narration-script.md）生成 GPT-SoVITS 口播视频。
  使用 Marp 导出 PNG、本地 GPT-SoVITS API、ffmpeg 合成 MP4。适用于
  document-to-presentation 产出后的视频化。用户提到口播视频、TTS、配音视频、
  narrated.mp4 时使用。
version: 1.1.0
disable-model-invocation: true
---

# PPT + 口播稿 → 口播视频

将 [`document-to-presentation`](../document-to-presentation/SKILL.md) 产出合成为 **`{产出目录}/video/{basename}/narrated.mp4`**。

## 路径约定

**{项目根}** = 当前工作区或被分析项目的根目录。与上游 skill 一致。

**{产出目录}** = 用户指定的输出目录；若用户未指定，默认为 `{项目根}/项目汇总/`。

## 输入（目录 `{产出目录}/PPT/{basename}/`）

| 文件 | 必需 |
|------|------|
| `narration-script.md` | 是 |
| `slides.marp.md` | 是（优先；保留 tech-briefing 样式） |
| `video-config.yaml` | 否（可放在 PPT 目录或 `{产出目录}/video/{basename}/` 覆盖默认参数） |

## 输出

```
{产出目录}/video/{basename}/
├── slides/          # PNG 逐页
├── audio/           # MP3 逐页配音
├── segments/        # 逐页 MP4
├── narrated.mp4     # 最终成片（必交付）
└── generation-log.md
```

输入仍从 `{产出目录}/PPT/{basename}/` 读取；视频产物写入 `{产出目录}/video/{basename}/`，与 PPT 目录平级。

## 前置条件

- Node.js + npx（Marp 导出 PNG）
- Python 3.10+ + `pip install -r scripts/requirements.txt`
- ffmpeg + ffprobe（PATH 中可用）
- **GPT-SoVITS `api_v2.py` 已启动**（默认 `http://127.0.0.1:9880`）
- **`tools/voice/ref.wav`** 与 **`tools/voice/ref.txt`** 已配置

首次部署见 [references/gpt-sovits-setup.md](references/gpt-sovits-setup.md)。

## 工作流

```
视频产出进度：
- [ ] 阶段 0：检测目录、ffmpeg、GPT-SoVITS API、参考音频
- [ ] 阶段 1：Marp 导出 slides PNG
- [ ] 阶段 2：解析口播稿 + GPT-SoVITS API 逐页合成
- [ ] 阶段 3：ffmpeg 合成 narrated.mp4
- [ ] 阶段 4：校验页数对齐、记录 generation-log.md
```

### 启动 GPT-SoVITS API（阶段 0 之前）

**Windows 整合包（推荐）：** 在 `{GPT-SoVITS}` 根目录创建并双击 `go-api.bat`（见 [gpt-sovits-setup.md](references/gpt-sovits-setup.md)），或：

```powershell
cd D:\GPT-SoVITS
.\runtime\python.exe -I api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

**源码 / conda 安装：**

```powershell
conda activate GPTSoVits
cd GPT-SoVITS
python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

### 一键生成

```powershell
pip install -r .cursor/skills/presentation-to-video/scripts/requirements.txt
python .cursor/skills/presentation-to-video/scripts/generate-video.py \
  "项目汇总/PPT/developer-onboarding-report"
```

**Windows PowerShell：**

```powershell
pip install -r .cursor/skills/presentation-to-video/scripts/requirements.txt
python .cursor/skills/presentation-to-video/scripts/generate-video.py `
  "output/2026年第25周/报告/{slug}/PPT/developer-onboarding-report"
```

### 阶段 0：检测

- 目录含 `narration-script.md` 与 `slides.marp.md`
- `ffmpeg -version`、`ffprobe -version` 可用
- GPT-SoVITS API 可达（`api_v2.py` 运行中）
- `tools/voice/ref.wav` 存在

### 阶段 4：校验

- 口播解析页数 = PNG 页数
- `narrated.mp4` 存在于 `{产出目录}/video/{basename}/` 且 > 1MB
- 总时长与口播稿预估 ±25%（记入 `{产出目录}/video/{basename}/generation-log.md`）

## 配置

配置合并顺序（后者覆盖前者）：

1. `tools/voice/gpt-sovits.defaults.yaml`
2. [templates/video-config.yaml](templates/video-config.yaml)
3. `{产出目录}/PPT/{basename}/video-config.yaml` 或 `{产出目录}/video/{basename}/video-config.yaml`

常用覆盖项：

- `gpt_sovits.speed_factor`：语速（默认 `0.95`）
- `gpt_sovits.repetition_penalty`：抑制漏字/重复（默认 `1.35`）
- `min_slide_seconds`：章节页保底时长

CLI 覆盖 API 地址：`--gpt-sovits-url http://127.0.0.1:9880`

## 口播稿解析

见 [scripts/parse_narration.py](scripts/parse_narration.py)：

- 按 `### 第 N 页｜标题` 分节
- 提取 `**口播：**` 正文
- `**过渡：**` 并入当前页 TTS（最后一页「结束」过渡忽略）

## 反模式

- 仅有 `slides.pptx` 无 `slides.marp.md`（首期不支持 PPTX 转图）
- 口播页数与幻灯片页数不一致仍强行合成
- 未启动 GPT-SoVITS API 仍声称成片完成
- 未装 ffmpeg 仍声称成片完成

## 配套资源

| 资源 | 路径 |
|------|------|
| README | [README.md](README.md) |
| 主脚本 | [scripts/generate-video.py](scripts/generate-video.py) |
| GPT-SoVITS 客户端 | [scripts/gpt_sovits_tts.py](scripts/gpt_sovits_tts.py) |
| 解析器 | [scripts/parse_narration.py](scripts/parse_narration.py) |
| 导出 PNG Win | [scripts/export-slide-images.ps1](scripts/export-slide-images.ps1) |
| GPT-SoVITS 部署 | [references/gpt-sovits-setup.md](references/gpt-sovits-setup.md) |
| 共享声线配置 | [tools/voice/](../../../tools/voice/) |
| ffmpeg | [references/ffmpeg-compose.md](references/ffmpeg-compose.md) |

## 上游 Skill

- [document-to-presentation](../document-to-presentation/SKILL.md) — 生成 slides + 口播稿
