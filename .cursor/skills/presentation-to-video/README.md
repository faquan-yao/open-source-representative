# presentation-to-video

将 **PPT 目录**（`slides.marp.md` + `narration-script.md`）合成为 **GPT-SoVITS 口播视频**。

- **版本：** 1.1.0  
- **位置：** `.cursor/skills/presentation-to-video/`（开源科代表项目内）  
- **上游：** [document-to-presentation](../document-to-presentation/README.md)

## 快速开始

**1. 下载 GPT-SoVITS 整合包、创建 `go-api.bat` 并启动 API**（首次，见 [gpt-sovits-setup.md](references/gpt-sovits-setup.md)）

**2. 准备参考声线：** `tools/voice/ref.wav` + `tools/voice/ref.txt`

**3. 生成视频：**

```powershell
pip install -r .cursor/skills/presentation-to-video/scripts/requirements.txt
python .cursor/skills/presentation-to-video/scripts/generate-video.py `
  "output/2026年第25周/报告/{slug}/PPT/developer-onboarding-report"
```

产出：`{产出目录}/video/{basename}/narrated.mp4`

## 管线

```
slides.marp.md  ──► video/{basename}/slides/*.png        (Marp CLI)
narration-script.md ──► video/{basename}/audio/*.mp3     (GPT-SoVITS API)
PNG + MP3 ──► video/{basename}/segments/*.mp4 ──► narrated.mp4  (ffmpeg)
```

## 环境依赖

| 依赖 | 安装 |
|------|------|
| Node.js | Marp 导出 PNG |
| Python 3.10+ | `pip install -r scripts/requirements.txt` |
| ffmpeg | `winget install Gyan.FFmpeg`（Windows） |
| GPT-SoVITS | Windows 整合包 + `go-api.bat`（或源码 `api_v2.py`，见 setup 文档） |

pip 若遇代理 SSL 错误，可试：

```powershell
$env:NO_PROXY="*"
py -3 -m pip install -r scripts/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 配置（可选）

全局默认：`tools/voice/gpt-sovits.defaults.yaml`

单报告覆盖：`{产出目录}/PPT/{basename}/video-config.yaml`

```yaml
gpt_sovits:
  speed_factor: 0.95
output: narrated.mp4
```

## 目录结构

```
presentation-to-video/
├── README.md
├── SKILL.md
├── references/
│   └── gpt-sovits-setup.md
├── templates/video-config.yaml
└── scripts/
    ├── generate-video.py
    ├── gpt_sovits_tts.py
    ├── parse_narration.py
    ├── export-slide-images.ps1
    └── requirements.txt

tools/voice/          # 项目根下共享参考声线
├── ref.wav           # 需自备
├── ref.txt
├── gpt-sovits.defaults.yaml
└── go-api.bat.template   # 复制到 GPT-SoVITS 整合包根目录
```

## 已知限制

- 需本地 GPU、GPT-SoVITS 整合包（或等价环境）与已启动的 API
- `ref_audio_path` 必须是 API 进程所在机器可访问的路径
- 视频画面以 Marp PNG 为准，与 PPTX 可能略有差异
- 首期不支持仅从 PPTX 生成（需 `slides.marp.md`）

## 延伸阅读

- [SKILL.md](SKILL.md) — Agent 工作流
- [gpt-sovits-setup.md](references/gpt-sovits-setup.md) — 部署与微调
