---
name: document-to-presentation
description: >-
  从 Markdown/长文档提取关键信息，生成专业写实 PPTX 与诙谐口播稿。
  使用 tech-briefing 主题与版式组件，事实与幽默分层、页码对齐。
  适用于技术分享、项目汇报、产品宣讲。用户提到 PPT、幻灯片、
  口播稿、演讲稿、Marp、汇报材料、pptx 时使用。
version: 1.2.0
disable-model-invocation: true
---

# 文档 → 专业 PPTX + 诙谐口播稿

从任意 Markdown/长文档提取关键信息，产出**演示套件**（统一放入 `{产出目录}/PPT/{源文档basename}/`）。

**核心原则：** 一条事实链、两种表达。PPT 必须专业版式，禁止白底 bullet 清单风。

## 路径约定

**{项目根}** = 当前工作区或被分析项目的根目录（不是 skill 安装目录、不是源文档所在子目录）。阶段 0 须确认。

**{产出目录}** = 用户指定的输出目录；若用户未指定，默认为 `{项目根}/项目汇总/`。阶段 0 须确认并创建（不存在则 `mkdir`）。

下文路径均相对 `{产出目录}`，除非标注为相对 `{项目根}`。

## 输出目录（必遵）

```
{产出目录}/PPT/{源文档basename}/
```

| 源文档 | 产出目录 |
|--------|----------|
| `{项目根}/项目汇总/user-project-info.md` | `{产出目录}/PPT/user-project-info/` |
| `{项目根}/docs/report.md` | `{产出目录}/PPT/report/` |

默认情况下 `{产出目录}` = `{项目根}/项目汇总/`，即 `{项目根}/项目汇总/PPT/{basename}/`。

不得写入源文档同目录或 skill 安装目录。

## 产出文件

均在上述目录内，**文件名不带源文档前缀**：

| 文件 | 交付？ | 说明 |
|------|--------|------|
| `fact-kernel.md` | 可选 | 事实内核 |
| `slide-outline.md` | 可选 | 幻灯片大纲 |
| `slides.marp.md` | 可选 | Marp 源稿（`tech-briefing`） |
| **`slides.pptx`** | **必交付** | 最终幻灯片 |
| **`narration-script.md`** | **必交付** | 口播稿（仅可念内容） |
| `presentation-scratch.md` | 否 | 草稿、统计、阶段 4 校验 |

## 前置条件

- 可读源文档
- **Node.js + npx**（导出 PPTX 必需）
- 写权限

## 工作流

```
演示产出进度：
- [ ] 阶段 0：侦察与参数 + 确认 {产出目录} + 创建 PPT/{basename}/ 目录
- [ ] 阶段 1：fact-kernel.md
- [ ] 阶段 2：slide-outline.md + slides.marp.md + 导出 slides.pptx
- [ ] 阶段 3：narration-script.md
- [ ] 阶段 4：事实对齐 + PPTX 存在性校验（记入 presentation-scratch.md）
```

### 阶段 2：PPT 轨道

1. 写入 `PPT/{basename}/slide-outline.md`
2. 写入 `PPT/{basename}/slides.marp.md`：
   - **必须** `theme: tech-briefing`、`size: 16:9`
   - **必须**按页选用 class：`lead` / `agenda` / `cols3` / `compare` / `steps` / `fit` / `grid` / `emphasis`
   - 规则见 [slide-design-rules.md](references/slide-design-rules.md)
3. **必须**导出 `slides.pptx`：

**Windows（在项目根目录执行）：**

```powershell
& ".cursor/skills/document-to-presentation/scripts/export-pptx.ps1" `
  -MarpFile "{产出目录}/PPT/{basename}/slides.marp.md"
```

**macOS/Linux：**

```bash
bash .cursor/skills/document-to-presentation/scripts/export-pptx.sh \
  "{产出目录}/PPT/{basename}/slides.marp.md"
```

4. 验证 `slides.pptx` 存在且 > 50KB

### 阶段 3：口播轨道

写入 `PPT/{basename}/narration-script.md`（[模板](templates/narration-script.md)）。

**口播稿只含可念内容。** 全文统计、阶段 4 校验写入 `presentation-scratch.md`，勿入口播稿。

### 阶段 4：校验清单

校验结果写入 `presentation-scratch.md`：

- [ ] 口播每页与 slide-outline 页码标题一致
- [ ] 事实与 PPT 一致
- [ ] `slides.pptx` 已生成且可打开
- [ ] 幻灯片使用 tech-briefing，≥3 种版式
- [ ] 口播时长 ±20%

## 反模式

- 把 PPT 产出写入源文档同目录（如 `docs/user-project-info-slides.marp.md`），而非 `{产出目录}/PPT/{basename}/`
- 只交付 Marp 不导出 PPTX
- 使用 `theme: default` 或满屏 bullet
- 口播稿附全文统计、校验记录

## 配套资源

| 资源 | 路径 |
|------|------|
| **README** | [README.md](README.md) |
| 幻灯片规则 | [references/slide-design-rules.md](references/slide-design-rules.md) |
| 主题 CSS | [templates/theme/tech-briefing.css](templates/theme/tech-briefing.css) |
| 导出脚本 Win | [scripts/export-pptx.ps1](scripts/export-pptx.ps1) |
| 导出脚本 Unix | [scripts/export-pptx.sh](scripts/export-pptx.sh) |
| Marp 模板 | [templates/slides.marp.md](templates/slides.marp.md) |
| 幽默指南 | [references/humor-guidelines.md](references/humor-guidelines.md) |
| 提取规则 | [references/extraction-rubric.md](references/extraction-rubric.md) |

其余阶段（0 侦察、1 内核）见各 reference / template。
