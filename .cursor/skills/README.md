# 开源科代表 · Cursor Skills

本仓库自包含全链路所需的 Agent Skills，均位于 `.cursor/skills/`。

| Skill | 用途 |
|-------|------|
| [github-weekly-star-growth](github-weekly-star-growth/SKILL.md) | 周增 Star 采集（CSV/JSON） |
| [weekly-open-source-pipeline](weekly-open-source-pipeline/SKILL.md) | 全链路编排（采集 → 报告 → PPT → 视频） |
| [open-source-dev-onboarding-extractor](open-source-dev-onboarding-extractor/SKILL.md) | 开发者项目概览报告 |
| [document-to-presentation](document-to-presentation/SKILL.md) | Markdown → PPTX + 口播稿 |
| [presentation-to-video](presentation-to-video/SKILL.md) | PPT + 口播稿 → narrated.mp4 |

## 脚本路径（相对项目根）

```powershell
# 导出 PPTX
& ".cursor/skills/document-to-presentation/scripts/export-pptx.ps1" `
  -MarpFile "output/2026年第25周/报告/{slug}/PPT/developer-onboarding-report/slides.marp.md"

# 生成视频（需先启动 GPT-SoVITS go-api.bat，见 presentation-to-video/references/gpt-sovits-setup.md）
python ".cursor/skills/presentation-to-video/scripts/generate-video.py" `
  "output/2026年第25周/报告/{slug}/PPT/developer-onboarding-report"

# TTS 带重试（API 偶发失败时）
python tools/synthesize_narration.py `
  "output/2026年第25周/报告/{slug}/PPT/developer-onboarding-report" --delay 4
python ".cursor/skills/presentation-to-video/scripts/generate-video.py" `
  "output/2026年第25周/报告/{slug}/PPT/developer-onboarding-report" --skip-images --skip-tts
```

## 依赖

- 采集：`pip install -r requirements.txt`
- 视频：GPT-SoVITS 整合包（`go-api.bat`）+ `tools/voice/ref.wav` + Node.js + ffmpeg
