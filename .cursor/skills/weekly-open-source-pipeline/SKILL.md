---
name: weekly-open-source-pipeline
description: >-
  开源科代表全链路：周增 Star 采集 → clone → 开发者报告 → PPT/口播稿 → 短视频。
  按 storage-paths 约定产出。Use when user asks for 开源科代表周报、全链路、
  项目讲解视频、批量报告.
version: 1.0.0
---

# 开源科代表 · 周榜全链路

从 GitHub 周增 Star 榜到项目讲解短视频的完整工作流。

## 路径约定

**{项目根}** = `d:\work\work\open-source-representative`（或当前工作区根）

**{周次}** = ISO 8601，如 `2026年第25周`

**{slug}** = `owner/repo` → `owner-repo`

| 类型 | 路径 |
|------|------|
| 榜单 CSV | `output/{周次}/github-star-growth.csv` |
| 运行日志 | `output/logs/{周次}/run-log.txt` |
| Clone | `output/tmp/{周次}/repos/{slug}/` |
| 报告 | `output/{周次}/报告/{slug}/developer-onboarding-report.md` |
| PPT | `output/{周次}/报告/{slug}/PPT/developer-onboarding-report/` |
| 视频 | `output/{周次}/报告/{slug}/video/developer-onboarding-report/narrated.mp4` |

## 工作流

```
进度：
- [ ] 1. 采集榜单（github-weekly-star-growth skill）
- [ ] 2. Clone 仓库（clone_repos.py）
- [ ] 3. 开发者报告（open-source-dev-onboarding-extractor）
- [ ] 4. PPT + 口播稿（document-to-presentation）
- [ ] 5. 短视频（presentation-to-video）
- [ ] 6. 更新 报告/README.md 索引
```

### 阶段 1：采集

```powershell
python tools/collect_weekly_stars.py --start YYYY-MM-DD --end YYYY-MM-DD --workers 16
```

详见 `.cursor/skills/github-weekly-star-growth/SKILL.md`。

### 阶段 2：Clone

**试点（每类 #1）：**

```powershell
python tools/clone_repos.py --csv "output/{周次}/github-star-growth.csv" --rank 1
```

**全量（30 个）：**

```powershell
python tools/clone_repos.py --csv "output/{周次}/github-star-growth.csv"
```

### 阶段 3：开发者报告

对每个 slug，使用 `open-source-dev-onboarding-extractor`：

- **{项目根}** = `output/tmp/{周次}/repos/{slug}/`
- **{产出目录}** = `output/{周次}/报告/{slug}/`
- **终稿** = `developer-onboarding-report.md`

### 阶段 4：PPT + 口播稿

对每个报告，使用 `document-to-presentation`：

- 源文档 = `output/{周次}/报告/{slug}/developer-onboarding-report.md`
- **{产出目录}** = `output/{周次}/报告/{slug}/`

导出 PPTX（Windows，在项目根目录执行）：

```powershell
& ".cursor/skills/document-to-presentation/scripts/export-pptx.ps1" `
  -MarpFile "output/{周次}/报告/{slug}/PPT/developer-onboarding-report/slides.marp.md"
```

### 阶段 5：短视频

**先启动 GPT-SoVITS API**（见 `presentation-to-video/references/gpt-sovits-setup.md`）。

Windows 整合包：双击 `{GPT-SoVITS}/go-api.bat`（首次需按 setup 文档创建），或：

```powershell
cd D:\GPT-SoVITS
.\runtime\python.exe -I api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

源码安装时改用 `conda activate GPTSoVits` + `python api_v2.py ...`。

**再生成视频**（另开终端，项目根目录）：

```powershell
python ".cursor/skills/presentation-to-video/scripts/generate-video.py" `
  "output/{周次}/报告/{slug}/PPT/developer-onboarding-report"
```

TTS 失败需重试时，可用 `tools/synthesize_narration.py` 单独合成音频，再 `--skip-images --skip-tts` 只跑 ffmpeg 合成。

### 阶段 6：索引

更新 `output/{周次}/报告/README.md`，含报告、PPT、视频链接。

## 模式切换

| 模式 | Clone 参数 | 报告/PPT/视频数量 |
|------|------------|-------------------|
| 试点 | `--rank 1` | 3（每类 1 个） |
| 全量 | 无 filter | 30 |

## 上游 Skills

| Skill | 路径 |
|-------|------|
| `github-weekly-star-growth` | `.cursor/skills/github-weekly-star-growth/` |
| `open-source-dev-onboarding-extractor` | `.cursor/skills/open-source-dev-onboarding-extractor/` |
| `document-to-presentation` | `.cursor/skills/document-to-presentation/` |
| `presentation-to-video` | `.cursor/skills/presentation-to-video/` |

## 前置条件

- Python 3.10+、Node.js、ffmpeg、git
- 可选 `GITHUB_TOKEN`（采集加速）
- GPT-SoVITS 整合包（或源码安装）+ `tools/voice/ref.wav`（视频口播，见 `presentation-to-video/references/gpt-sovits-setup.md`）
