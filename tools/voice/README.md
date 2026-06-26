# 科代表口播声线（GPT-SoVITS）

本目录存放 **presentation-to-video** 流水线共用的 GPT-SoVITS 参考音频与默认配置。

## 必需文件

| 文件 | 说明 |
|------|------|
| `ref.wav` | 5–10 秒干声参考（**需自行录制并替换**；勿提交占位静音文件） |
| `ref.txt` | 与 `ref.wav` **逐字一致**的文本 |
| `gpt-sovits.defaults.yaml` | 全局默认 API 与合成参数 |
| `go-api.bat.template` | 复制到 GPT-SoVITS 整合包根目录并重命名为 `go-api.bat` |

## 录制建议

- 内容与最终口播风格接近（平稳、中等语速）
- 采样率 44100 Hz 或 48000 Hz 均可
- 仅使用自有或已授权的声音

## 配置优先级

`generate-video.py` 合并顺序（后者覆盖前者）：

1. 脚本内置默认值
2. `tools/voice/gpt-sovits.defaults.yaml`
3. `.cursor/skills/presentation-to-video/templates/video-config.yaml`
4. `{产出目录}/PPT/{basename}/video-config.yaml` 或 `{产出目录}/video/{basename}/video-config.yaml`

## 部署

Windows 推荐 [GPT-SoVITS 整合包](https://huggingface.co/lj1995/GPT-SoVITS-windows-package)，解压后在根目录创建 `go-api.bat` 启动 API。完整步骤见 [.cursor/skills/presentation-to-video/references/gpt-sovits-setup.md](../.cursor/skills/presentation-to-video/references/gpt-sovits-setup.md)。
