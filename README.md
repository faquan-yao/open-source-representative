# 开源科代表 · GitHub 周增 Star 榜

按周统计 GitHub 上 **AI、新能源、自动驾驶** 三类开源项目的 star 增长 Top 10，产出 CSV / JSON。

## 目录约定

```
open-source-representative/
├── README.md
├── requirements.txt
├── tools/                    # 公用脚本与配置（仅源码）
├── .cursor/skills/           # 全链路 Agent Skills（自包含）
└── output/                   # 全部生成物（gitignore）
    ├── logs/YYYY年第WW周/    # 运行日志
    ├── tmp/                  # 缓存与临时文件
    └── YYYY年第WW周/         # 正式产出（CSV + JSON + 报告）
```

详见 [`.cursor/rules/storage-paths.mdc`](.cursor/rules/storage-paths.mdc)。

## 快速开始

```powershell
cd "d:\work\work\open-source-representative"
pip install -r requirements.txt
$env:GITHUB_TOKEN="your_github_token"   # 强烈建议
python tools/collect_weekly_stars.py --start 2026-06-08 --end 2026-06-14
```

| 产出 | 路径 |
|------|------|
| 周报 CSV/JSON | `output/2026年第24周/` |
| 运行日志 | `output/logs/2026年第24周/run-log.txt` |
| Archive 缓存 | `output/tmp/2026年第24周/stars_*.json` |

## 统计口径

- **时间范围**：UTC 自然日，`--start` ～ `--end` 对应 GH Archive 小时文件
- **增星指标**：`WatchEvent` 中 `action=started`（毛增）
- **分类规则**：严格 topic 白名单，见 [`tools/topic_allowlists.yaml`](tools/topic_allowlists.yaml)
- **跨类去重**：AI > 自动驾驶 > 新能源

## 已知限制

- GH Archive 与 GitHub 页面 star 数可能有小幅偏差
- 未打 topic 的相关项目不会入榜
- 首次 Archive 扫描约 4–8 分钟（16 线程）；`--use-cache` 可快速重跑
- topic 索引缓存：`output/tmp/cache/topic_index.json`

详见 [`tools/README.md`](tools/README.md)。

## 全链路快速开始

从榜单采集到项目讲解短视频（试点：每类 Top 1，共 3 个项目）：

```powershell
cd "d:\work\work\open-source-representative"
pip install -r requirements.txt

# 0. 视频口播：下载 GPT-SoVITS 整合包并启动 go-api.bat（见 .cursor/skills/presentation-to-video/references/gpt-sovits-setup.md）

# 1. 采集（示例：第25周）
python tools/collect_weekly_stars.py --start 2026-06-15 --end 2026-06-21 --workers 16

# 2. Clone 每类 #1
python tools/clone_repos.py --csv "output/2026年第25周/github-star-growth.csv" --rank 1

# 3–5. 报告 / PPT / 视频 — 由 Agent 按 weekly-open-source-pipeline skill 执行
```

| 阶段 | 产出 | 路径 |
|------|------|------|
| 榜单 | CSV/JSON | `output/2026年第25周/github-star-growth.csv` |
| Clone | 源码 | `output/tmp/2026年第25周/repos/{slug}/` |
| 报告 | 开发者概览 | `output/2026年第25周/报告/{slug}/developer-onboarding-report.md` |
| PPT | 幻灯片 + 口播稿 | `output/2026年第25周/报告/{slug}/PPT/developer-onboarding-report/` |
| 视频 | 口播成片 | `output/2026年第25周/报告/{slug}/video/developer-onboarding-report/narrated.mp4` |

全链路编排见 [`.cursor/skills/weekly-open-source-pipeline/SKILL.md`](.cursor/skills/weekly-open-source-pipeline/SKILL.md)。  
Skills 索引见 [`.cursor/skills/README.md`](.cursor/skills/README.md)。

### PPT / 视频命令（项目内 skills）

```powershell
# 导出 PPTX
& ".cursor/skills/document-to-presentation/scripts/export-pptx.ps1" `
  -MarpFile "output/2026年第25周/报告/{slug}/PPT/developer-onboarding-report/slides.marp.md"

# 生成口播视频
python ".cursor/skills/presentation-to-video/scripts/generate-video.py" `
  "output/2026年第25周/报告/{slug}/PPT/developer-onboarding-report"
```
