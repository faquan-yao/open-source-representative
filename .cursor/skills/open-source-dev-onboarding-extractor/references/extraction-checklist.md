# 草稿提取检查清单

写入 `{产出目录}/dev-onboarding-scratch.md`。合成时**提炼**进终稿，勿原样粘贴。

终稿须通顺中文，见 [writing-style.md](writing-style.md)。

---

## 侦察

| 问题 | 去哪找 |
|------|--------|
| 解决什么问题？ | README、VISION |
| 面向谁？ | README、docs |
| 技术形态？ | 包清单、入口（用完整中文描述，勿写「CLI 与库」短语） |
| 架构概览？ | `ARCHITECTURE*`、docs |

---

## 终稿必备字段（合成前核对）

| 终稿章节 | 草稿须收集 | 终稿约束 |
|----------|------------|----------|
| 摘要 | 5 个信息点草稿 | 3～5 句通顺中文 |
| 整体架构图 | 组件、外部依赖、数据流 | 1 张图 + 组件表 |
| 问题域与边界 | 角色、3 场景、范围内/外 | 场景各 1～2 句 |
| 主执行链路 | 触发点、4～6 步、路径 | 1 张主链路图 + 每步 1 个 `path` 表 |
| 代码导航 | 6～8 个能力域 | 6～8 行表 |
| 配置与运行 | 3～6 关键配置、install/build/run | 命令块 + 验证一行 |
| 注意事项 | 2～4 条踩坑 | bullet 列表 |
| 延伸阅读 | 5～7 文档/文件 | 表格 |

---

## 各维度去哪找

### 问题域与边界

README、ARCHITECTURE、教程、e2e 描述、issue 模板。

### 系统组成

`cmd/`、`services/`、compose、deploy、env 示例。

### 主执行链路

路由、CLI 子命令、consumer；跟 4～6 跳调用。草稿可记 file:function；终稿须绘主链路 Mermaid 图（步骤顺序）+ 表（每步 1 个 path）。

### 代码导航

main、server 启动、方面 3 枢纽、config loader、plugin/API、代表性测试。

### 配置与运行

`.env.example`、config loader、README 命令、CONTRIBUTING 测试章节。

### 注意事项

CHANGELOG、@deprecated、文档与实现不一致处、CONTRIBUTING 警告。

---

## 仍不写入终稿（除非「详细模式」）

- 完整配置键表（>6 项）
- CI/lint/format 全矩阵
- 架构原则、依赖方向长文
- 必读 10 文件
- 第三张及以上 Mermaid（架构图 + 主链路图已足够）
- 逐步 file:function 表（>6 行）

---

## 合成核对

- [ ] 摘要读出声通顺，无「是一个 X CLI 与库」
- [ ] 主链路含流程图（4～6 步）与路径锚点表
- [ ] 有可复制运行命令
- [ ] 约 150～250 行，关键节齐全
- [ ] 2 张 Mermaid：架构图 + 主链路图
