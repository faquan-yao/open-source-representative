# 写实 PPT 设计规则

PPT 轨道承载事实内核：**专业、克制、可独立阅读**——禁止「白底 + 黑字 bullet 清单」的小学生作业风。

## 视觉标准（必达）

| 维度 | 要求 |
|------|------|
| 主题 | 必须使用 `theme: tech-briefing`（见 `templates/theme/tech-briefing.css`） |
| 字体 | 系统无衬线：Segoe UI / 微软雅黑 / PingFang SC |
| 配色 | 深蓝封面 + 浅灰内容页 + 蓝色强调；对比用绿/红底卡片，非裸表格 |
| 层次 | 标题左色条、卡片阴影、圆角、步骤编号圆点 |
| 密度 | 每页视觉焦点 ≤ 1 个；宁可多一页，不要堆字 |

**禁止：** `theme: default` 裸主题、满屏 bullet、无结构纯表格、封面与内页同款白底。

## 页面类型与 Marp class

每页必须选用一种版式（可组合 `<!-- _class: xxx -->`）：

| class | 用途 | 结构 |
|-------|------|------|
| `lead` | 封面 | 大标题 + 副标题 + 元信息；深色渐变底 |
| `agenda` | 议程 | 有序列表 + 序号条 |
| `section` | 章节分隔 | 单句章节名，居中蓝底 |
| `cols3` | 三点并列（痛点/差异化） | `.cards` > `.card` × 3，含 `.num` |
| `compare` | Before/After | `.row` > `.before` + `.after` |
| `steps` | 流程/上手 | 有序列表，圆形步骤号 |
| `fit` | 适合/不适合 | `.row` > `.yes` + `.no` |
| `grid` | 能力一览 | `.items` > `.item` + `.tag` |
| `emphasis` | 总结/CTA | 浅绿底 + `pre` 代码块 CTA |
| （默认） | 单观点页 | 左色条 `h1` + ≤4 bullet |

## 一页一观点

- **标题 = 结论句**
  - 差：「系统上下文」
  - 好：「Agent 直调上游 CLI，本项目只做胶水层」
- 两个结论 → 拆两页

## 字数与条目

| 元素 | 上限 |
|------|------|
| 正文 bullet | ≤ 4 条/页 |
| 单条 bullet | ≤ 18 字 |
| 代码块 | 2～5 行 |
| 三列卡片 | 每卡标题 ≤ 8 字，正文 ≤ 30 字 |

数字、命令、URL、版本号**保留原文**。

## 主链路结构

```
封面(lead) → 议程(agenda) → [可选 section] → 背景
→ 痛点(cols3) → 转变(compare) → 差异化(cols3 或默认)
→ 上手(steps) → 适合谁(fit) → 核心命令(默认)
→ 能力(grid) → 安全(默认) → 总结(emphasis) → Q&A
```

## Marp 文件头（固定）

```yaml
---
marp: true
theme: tech-briefing
paginate: true
size: 16:9
header: '{演讲标题}'
footer: '{演讲者} · {日期}'
---
```

## 三列卡片示例

```markdown
<!-- _class: cols3 -->

# 三个痛点，各有一条解

<div class="cards">
<div class="card">
<span class="num">1</span>
<h3>平台门槛</h3>
<p>API 付费、登录、风控各异 → 首选+备选自动探测</p>
</div>
...
</div>
```

## 对比页示例

```markdown
<!-- _class: compare -->

# 装完之后：你说话，Agent 去干活

<div class="row">
<div class="before">
<div class="label">BEFORE</div>
只能改本地文件，或自己复制粘贴
</div>
<div class="after">
<div class="label">AFTER</div>
自然语言提问，Agent 直调上游工具
</div>
</div>
```

## 导出 PPTX（必做，非可选）

阶段 2 末尾**必须**执行导出，产出同目录下的 `slides.pptx`：

**Windows：**

```powershell
```powershell
& ".cursor/skills/document-to-presentation/scripts/export-pptx.ps1" `
  -MarpFile "{产出目录}/PPT/{basename}/slides.marp.md"
```

**macOS/Linux：**

```bash
bash .cursor/skills/document-to-presentation/scripts/export-pptx.sh \
  "{产出目录}/PPT/{basename}/slides.marp.md"
```

导出后验证：`PPT/{basename}/slides.pptx` 存在且 > 50KB。

## 反模式

- 白底 default 主题 + 纯 bullet
- 把口播稿贴进幻灯片
- 满屏表格无配色
- 封面与内页无视觉区分
- 只交付 `.marp.md` 不导出 `.pptx`
- 产出文件散落在源文档同目录（应放入 `{产出目录}/PPT/{basename}/`）
