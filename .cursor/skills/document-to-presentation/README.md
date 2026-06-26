# document-to-presentation

从 Markdown / 长文档提取关键信息，生成**专业写实 PPTX** 与**诙谐口播稿**。

- **版本：** 1.2.0  
- **位置：** `.cursor/skills/document-to-presentation/`（开源科代表项目内）  
- **调用：** 需在对话中显式提及（`disable-model-invocation: true`）

## 做什么

一条事实链、两种表达：

1. 先从源文档抽出不可篡改的「事实内核」
2. **PPT 轨道** — 写实、专业版式（`tech-briefing` 主题），导出可打开的 `slides.pptx`
3. **口播轨道** — 同页码、诙谐幽默，事实与 PPT 一致

适合：技术分享、项目汇报、产品宣讲、onboarding 文档转演讲。

## 快速开始

```
用 document-to-presentation 把 user-project-info.md 做成 15 分钟产品宣讲，幽默度中等
```

## 输出目录

所有 PPT 相关文件放入 **{产出目录}** 下的 `PPT/{源文档basename}/`：

```
{产出目录}/PPT/{源文档basename}/
```

**{产出目录}** = 用户指定的输出目录；若用户未指定，默认为 `{项目根}/项目汇总/`。

示例（默认）：源文档 `{项目根}/项目汇总/user-project-info.md` → 产出 **`{项目根}/项目汇总/PPT/user-project-info/`**

## 产出文件

| 文件 | 交付？ | 说明 |
|------|--------|------|
| `fact-kernel.md` | 可选 | 事实内核 |
| `slide-outline.md` | 可选 | 幻灯片大纲 |
| `slides.marp.md` | 可选 | Marp 源稿 |
| **`slides.pptx`** | **必交付** | 最终幻灯片 |
| **`narration-script.md`** | **必交付** | 口播稿 |
| `presentation-scratch.md` | 否 | 草稿与校验记录 |

口播稿**不包含**全文统计、阶段 4 校验等非念稿内容。

### 目录示例

```
{项目根}/
├── docs/                         # 源文档可在任意位置
└── 项目汇总/                     # 默认 {产出目录}
    ├── user-project-info.md
    ├── developer-onboarding-report.md
    ├── PPT/
    │   └── user-project-info/
    │       ├── fact-kernel.md
    │       ├── slide-outline.md
    │       ├── slides.marp.md
    │       ├── slides.pptx
    │       ├── narration-script.md
    │       └── presentation-scratch.md
    └── video/                    # presentation-to-video 产出
        └── user-project-info/
            ├── slides/
            ├── audio/
            ├── segments/
            ├── narrated.mp4
            └── generation-log.md
```

## 可调参数

| 参数 | 默认 |
|------|------|
| 受众 | 混合（业务 + 技术） |
| 时长 | 15 分钟 |
| 幽默度 | 中 |
| 输出目录 | `{产出目录}/PPT/{basename}/`（默认 `{项目根}/项目汇总/PPT/{basename}/`） |

## Skill 目录结构

```
document-to-presentation/
├── README.md
├── SKILL.md
├── references/
├── templates/
│   └── theme/tech-briefing.css
├── scripts/
│   ├── export-pptx.ps1
│   └── export-pptx.sh
└── examples/
```

## 手动导出 PPTX

**Windows：**

```powershell
& ".cursor/skills/document-to-presentation/scripts/export-pptx.ps1" `
  -MarpFile "项目汇总/PPT/user-project-info/slides.marp.md"
```

**macOS / Linux：**

```bash
bash .cursor/skills/document-to-presentation/scripts/export-pptx.sh \
  "项目汇总/PPT/user-project-info/slides.marp.md"
```

默认输出同目录下的 `slides.pptx`。

## 幻灯片版式

主题 `tech-briefing`：`lead` · `agenda` · `section` · `cols3` · `compare` · `steps` · `fit` · `grid` · `emphasis`

详见 [references/slide-design-rules.md](references/slide-design-rules.md)。

## 示例产出

仓库内试跑：`项目汇总/PPT/user-project-info/`、`项目汇总/PPT/developer-onboarding-report/`

## 下一步：口播视频

PPT 与口播稿就绪后，使用姊妹 Skill **[presentation-to-video](../presentation-to-video/README.md)** 生成 `{产出目录}/video/{basename}/narrated.mp4`（GPT-SoVITS + ffmpeg）。

```
用 presentation-to-video 把 项目汇总/PPT/developer-onboarding-report 生成口播视频
```

## 延伸阅读

- [SKILL.md](SKILL.md) — Agent 工作流
- [examples/agent-reach-mini.md](examples/agent-reach-mini.md) — 双轨样例
