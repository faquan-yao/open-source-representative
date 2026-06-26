# 金标准样例：Agent Reach 技术分享（迷你版）

> **用途：** 展示 `document-to-presentation` 双轨差异  
> **源文档：** `developer-onboarding-report.md` §1～§3  
> **参数：** 10 分钟 · 混合受众 · 幽默度中

---

## 阶段 1 产出摘要（fact-kernel 节选）

**主结论：** Agent Reach 是胶水层 CLI，帮 Agent 选型、安装、体检上游工具；读内容由 Agent 直调 twitter-cli、yt-dlp 等，Python 层不包装 read/search。

**支柱：**
1. 问题域：各平台 API/反爬使「Agent 能上网」变成重复配置工程
2. 边界：做安装/探测/SKILL；不做 read 包装、不改上游源码
3. 核心链路：`agent-reach doctor` 遍历 13 channel，probe_command 真跑 CLI

---

## 阶段 2 vs 阶段 3：同页双轨对照

### 第 1 页｜封面

| 轨道 | 内容 |
|------|------|
| **PPT** | 标题：Agent Reach 开发者速览 · 副标题：胶水层，不是内容包装器 |
| **口播** | 大家好，今天不画大饼，讲一个诚实到有点「甩锅」的项目：它负责把 Agent 送上互联网，但内容读取这事——它真不管，全交给上游 CLI。 |

### 第 3 页｜各平台门槛让「Agent 能上网」变成配置工程

| 轨道 | 内容 |
|------|------|
| **PPT** | Twitter API 付费；Reddit 匿名接口受限；小红书要登录；B 站风控拦截通用工具 |
| **口播** | 想让 Agent 上网？欢迎加入「平台门槛受害者互助会」。API 要钱、Cookie 要泪、风控要你命——Agent Reach 的定位就是：这些坑我们踩过了，你跟着 doctor 走就行。 |

### 第 5 页｜doctor 是核心链路：真实探测 13 个渠道

| 轨道 | 内容 |
|------|------|
| **PPT** | `agent-reach doctor` · 遍历 channels/ · probe_command 真跑 CLI · 单渠道失败不拖垮报告 |
| **口播** | doctor 就是给 13 个渠道做全员核酸：谁阳了标谁，绝不连坐。不用 `which` 敷衍——空壳骗得了 `shutil`，骗不了用户。 |

### 第 7 页｜明确边界：我们不包装 read/search

| 轨道 | 内容 |
|------|------|
| **PPT** | **做：** 安装、探测、凭据、SKILL **不做：** Python 层 read/search、改上游源码、复杂写操作、云端常驻 |
| **口播** | 边界页，请记好——我们不是瑞士军刀，是开瓶器。Agent 读完内容别夸我们，去夸 yt-dlp；出事了先看 doctor，别指望我们替你 curl。 |

---

## 阶段 4 校验记录（本样例）

| 检查项 | 结果 |
|--------|------|
| 页码对齐 | 通过 |
| 13 / doctor / probe_command 一致 | 通过 |
| 边界「不包装 read」口播未弱化 | 通过 |
| 10 分钟约 1800 字口播（迷你版） | 通过 |

完整 15 分钟版见对 `user-project-info.md` 的试跑产出。
