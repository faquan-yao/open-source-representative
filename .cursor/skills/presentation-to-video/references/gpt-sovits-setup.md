# GPT-SoVITS 部署与口播配置

presentation-to-video 使用本地 **GPT-SoVITS `api_v2.py`** 逐页合成口播。

## 硬件要求

| 场景 | 建议 |
|------|------|
| 零样本推理 | NVIDIA GPU 6GB+ 显存 |
| V2Pro 微调 + 批量周报 | 8GB+ 显存 |
| 仅 CPU | 极慢，不适合 30 条批量 |

## 1. 安装 GPT-SoVITS（Windows 整合包，推荐）

Windows 用户优先使用官方 **整合包**：自带 Python/CUDA 运行时与预训练模型，无需 conda 与 `install.ps1`。

### 下载与解压

| 来源 | 链接 |
|------|------|
| Hugging Face | [GPT-SoVITS-windows-package](https://huggingface.co/lj1995/GPT-SoVITS-windows-package) |
| 国内镜像 | [语雀 · 整合包下载](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#KTvnO) |

解压到 **纯英文路径**（无空格、无中文），例如 `D:\GPT-SoVITS`。下文称此目录为 **`{GPT-SoVITS}`**。

确认以下目录存在（整合包通常已包含）：

- `{GPT-SoVITS}/GPT_SoVITS/pretrained_models/`
- `{GPT-SoVITS}/GPT_SoVITS/text/G2PWModel/`（中文 TTS 必需）
- `{GPT-SoVITS}/runtime/python.exe`（整合包内置 Python）

### WebUI（微调 / 试听）

双击 `{GPT-SoVITS}/go-webui.bat`，或在 PowerShell 中：

```powershell
cd D:\GPT-SoVITS
.\go-webui.bat
```

### 启动 API（生成视频前必须运行）

整合包 **不含** `go-api.bat`，需自行创建一次。可复制本仓库 [`tools/voice/go-api.bat.template`](../../../tools/voice/go-api.bat.template) 到 `{GPT-SoVITS}` 根目录并重命名为 `go-api.bat`，或手动创建：

```bat
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"
set "PATH=%SCRIPT_DIR%\runtime;%PATH%"
runtime\python.exe -I api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
pause
```

之后 **双击 `go-api.bat`** 启动 API，保持窗口运行；另开终端执行 `generate-video.py`。

等效命令行（不创建 bat 时）：

```powershell
cd D:\GPT-SoVITS
.\runtime\python.exe -I api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

服务默认监听 `http://127.0.0.1:9880`。

## 2. 备选：源码安装（Linux / 进阶 Windows）

非 Windows，或需跟踪 GitHub 最新代码时：

```powershell
git clone https://github.com/RVC-Boss/GPT-SoVITS.git
cd GPT-SoVITS
conda create -n GPTSoVits python=3.10 -y
conda activate GPTSoVits
.\install.ps1 -Device CU128 -Source HF-Mirror   # Windows
# bash install.sh --device CU128 --source HF-Mirror  # Linux
```

启动 API：

```powershell
conda activate GPTSoVits
cd GPT-SoVITS
python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

更多环境见 [官方中文 README](https://github.com/RVC-Boss/GPT-SoVITS/blob/main/docs/cn/README.md) 与 [语雀手册](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e)。

## 3. 准备科代表参考声线

在本仓库 [`tools/voice/`](../../../tools/voice/) 放置：

| 文件 | 说明 |
|------|------|
| `ref.wav` | 5–10 秒干声（无 BGM、无混响） |
| `ref.txt` | 与 `ref.wav` **逐字一致**的文本 |
| `gpt-sovits.defaults.yaml` | 已提供默认 API 与合成参数 |
| `go-api.bat.template` | 复制到 `{GPT-SoVITS}` 根目录并重命名为 `go-api.bat` |

**合规：** 仅使用自有或已授权的声音。

## 4. 模型策略

| 阶段 | 做法 | 预期 |
|------|------|------|
| 快速起步 | 预训练底模 + 零样本（仅 ref.wav） | 可用，长稿偶发漏字 |
| 质量稳定 | WebUI 用 3–5 分钟干声微调 **V2Pro** | 固定品牌声线，批量更稳 |

微调权重在 GPT-SoVITS 侧配置 `GPT_SoVITS/configs/tts_infer.yaml`，不由本仓库管理。

### WebUI 微调概要（整合包）

1. 双击 `go-webui.bat`
2. 在 `1A-训练`：切分 → ASR → 校对 → 生成 `.list`
3. 在 `1B-微调训练`：先 SoVITS 再 GPT

## 5. 生成口播视频

```powershell
pip install -r .cursor/skills/presentation-to-video/scripts/requirements.txt
python .cursor/skills/presentation-to-video/scripts/generate-video.py `
  "output/2026年第25周/报告/{slug}/PPT/developer-onboarding-report"
```

复用已有 PNG / 音频：

```powershell
python .../generate-video.py "..." --skip-images --skip-tts
```

覆盖 API 地址：

```powershell
python .../generate-video.py "..." --gpt-sovits-url http://192.168.1.10:9880
```

**路径注意：** `ref_audio_path` 必须是 **api_v2.py 所在机器**上的绝对路径。本机同时跑 API 与生成脚本时，使用项目内绝对路径即可，例如：

`D:/work/work/open-source-representative/tools/voice/ref.wav`

## 6. 配置合并顺序

1. 脚本内置默认值
2. `tools/voice/gpt-sovits.defaults.yaml`
3. `.cursor/skills/presentation-to-video/templates/video-config.yaml`
4. `{产出目录}/PPT/{basename}/video-config.yaml` 或 `{产出目录}/video/{basename}/video-config.yaml`

单报告可只覆盖 `gpt_sovits.speed_factor` 等字段。

### 示例 video-config.yaml

```yaml
gpt_sovits:
  speed_factor: 0.95
  repetition_penalty: 1.35
output: narrated.mp4
```

## 7. API 参数（供调试）

`POST http://127.0.0.1:9880/tts` 必填：

- `text`, `text_lang`, `ref_audio_path`, `prompt_text`, `prompt_lang`

常用可选：`speed_factor`, `repetition_penalty`, `text_split_method`（默认 `cut5`）。

## 8. 常见问题

| 现象 | 处理 |
|------|------|
| 整合包解压后缺模型 | 从 [语雀预训练模型](https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#nVNhX) 补全到 `GPT_SoVITS/pretrained_models/` |
| `runtime\python.exe` 找不到 | 确认在整合包根目录执行；勿混用系统 Python |
| 无法连接 API | 确认已运行 `go-api.bat` 或上述 `api_v2.py` 命令，端口 9880 未被占用 |
| ref_audio_path 报错 | 路径必须是 API 进程所在机器可访问的绝对路径 |
| 漏字、重复 | 提高 `repetition_penalty`；缩短单页口播；检查 ASR 标注 |
| 不像本人 | 增加训练数据或微调 V2Pro；换更匹配的 ref.wav |
| CUDA OOM | 缩短单页文本；关闭其他 GPU 占用 |
| `slow_conv2d_cpu` / `not implemented for 'Half'` | GPT-SoVITS 在 CPU 上用了 fp16。编辑 `{GPT-SoVITS}/GPT_SoVITS/configs/tts_infer.yaml` 的 `custom` 段：`device: cpu`、`is_half: false`，重启 API；有 GPU 则检查驱动/CUDA |

## 参考

- [GPT-SoVITS GitHub](https://github.com/RVC-Boss/GPT-SoVITS)
- [tools/voice/README.md](../../../tools/voice/README.md)
