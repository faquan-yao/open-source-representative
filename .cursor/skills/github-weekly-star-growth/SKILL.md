---
name: github-weekly-star-growth
description: >-
  统计指定 UTC 周内 GitHub 开源项目 star 增量，按 topic 白名单分为多类（默认 AI、
  新能源、自动驾驶），每类输出 Top N 至 CSV/JSON。基于 GH Archive WatchEvent +
  GitHub Search 索引。Use when user asks for weekly star growth, trending repos,
  周增 star 榜, GitHub 热门开源, or 开源科代表周报.
version: 1.1.0
---

# GitHub 周增 Star 榜采集

统计 **指定 UTC 日期区间**内各仓库 star **毛增量**（`WatchEvent` + `action=started`），
按 **严格 GitHub Topics 白名单** 分类排行，产出 CSV / JSON；运行日志与缓存单独存放。

默认中文说明；仓库名、路径、命令保留原文。

## 何时使用

- 用户要「上周 / 某周 star 增长最快的开源项目」
- 按领域（AI、新能源、自动驾驶等）出 Top 10 榜单
- 定期「开源科代表」周报数据更新

## 前置条件

- 工作区含 `tools/collect_weekly_stars.py`
- Python 3.10+，`pip install -r requirements.txt`
- 可选：`GITHUB_TOKEN` / `GH_TOKEN`
- 目录约定见 `.cursor/rules/storage-paths.mdc`

## 路径约定（必遵）

```
{项目根}/
├── tools/                          # 公用脚本与配置（仅源码，不写 log/cache）
│   ├── collect_weekly_stars.py
│   └── topic_allowlists.yaml
└── output/                         # 全部生成物（gitignore）
    ├── logs/YYYY年第WW周/          # 运行日志
    │   └── run-log.txt
    ├── tmp/                        # 临时文件与缓存
    │   ├── cache/topic_index.json
    │   └── YYYY年第WW周/stars_{start}_{end}.json
    └── YYYY年第WW周/               # 正式产出（仅交付物）
        ├── github-star-growth.csv
        └── github-star-growth.json
```

- **正式产出** → `output/YYYY年第WW周/`（仅 CSV + JSON）
- **运行日志** → `output/logs/YYYY年第WW周/`
- **缓存/临时** → `output/tmp/`（禁止混进产出目录或根目录）

## 工作流

```
进度：
- [ ] 0. 确认统计区间（UTC）与类别/白名单
- [ ] 1. 运行采集脚本
- [ ] 2. 检查 output/logs/{周次}/run-log.txt
- [ ] 3. QA 交叉验证（AI 类）
- [ ] 4. 向用户交付 CSV 摘要
```

### 阶段 1：执行采集

```powershell
python tools/collect_weekly_stars.py --start YYYY-MM-DD --end YYYY-MM-DD --workers 16
python tools/collect_weekly_stars.py --start YYYY-MM-DD --end YYYY-MM-DD --use-cache
```

| 参数 | 用途 |
|------|------|
| `--refresh-cache` | 强制重扫 GH Archive |
| `--refresh-topic-cache` | 强制重建 `output/tmp/cache/topic_index.json` |
| `--workers N` | Archive 并行线程（默认 12） |

### 阶段 2：检查产出

读取 `output/logs/{周次}/run-log.txt`；交付物在 `output/{周次}/github-star-growth.csv`。

### 阶段 3–4

QA 与交付见 [reference.md](reference.md)。

## 延伸阅读

- 统计口径、故障排查：[reference.md](reference.md)
- 脚本参数：`tools/README.md`
