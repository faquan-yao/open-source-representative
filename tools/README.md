# tools/

公用脚本，详见各文件 `--help`。

| 脚本 | 用途 |
|------|------|
| `collect_weekly_stars.py` | 周增 Star 采集 → CSV/JSON |
| `clone_repos.py` | 从 CSV 批量浅克隆到 `output/tmp/{周次}/repos/` |
| `synthesize_narration.py` | GPT-SoVITS 配音（带重试，API 偶发失败时） |

PPT / 视频脚本见 `.cursor/skills/`（`document-to-presentation`、`presentation-to-video`）。

## collect_weekly_stars.py

采集指定日期区间内 GitHub 仓库 star 增量，按 topic 白名单分为 AI / 新能源 / 自动驾驶，每类输出 Top 10。

## 性能优化（v2）

- **GitHub Search 批量建索引**：按 topic 白名单搜索，一次拿到仓库 topics，避免逐仓库 API
- **GH Archive 并行扫描**：默认 12 线程同时下载/解析小时文件
- **解析过滤**：只统计索引内仓库的 `WatchEvent`，跳过无关事件
- **行级快速过滤**：JSON 行预检 `WatchEvent` + `started`，减少完整解析
- **本地缓存**：Archive → `output/tmp/YYYY年第WW周/stars_*.json`；topic 索引 → `output/tmp/cache/topic_index.json`
- **元数据刷新**：仅对最终 Top 30 调用 `GET /repos`（约 30 次 API）

典型耗时（有网络、无 token）：索引 ~2–5 分钟 + Archive 并行 ~3–8 分钟 + 导出 <1 分钟。

## 用法

```powershell
python tools/collect_weekly_stars.py --start 2026-06-08 --end 2026-06-14
python tools/collect_weekly_stars.py --start 2026-06-08 --end 2026-06-14 --week-dir "2026年第24周"
python tools/collect_weekly_stars.py --start 2026-06-08 --end 2026-06-14 --use-cache   # 复用 Archive 缓存
python tools/collect_weekly_stars.py --start 2026-06-08 --end 2026-06-14 --workers 16
```

## 参数

| 参数 | 说明 |
|------|------|
| `--start` | 起始日期 `YYYY-MM-DD`（UTC） |
| `--end` | 结束日期 `YYYY-MM-DD`（UTC） |
| `--week-dir` | 覆盖输出子文件夹名，默认 `YYYY年第WW周` |
| `--allowlist` | topic 白名单 YAML，默认 `tools/topic_allowlists.yaml` |
| `--root` | 工作区根目录，默认脚本上级目录 |
| `--workers` | GH Archive 并行线程数，默认 12 |
| `--pages-per-topic` | 每个 topic 搜索页数，0=自动 |
| `--use-cache` | 复用 `output/tmp/{周次}/stars_*.json` |
| `--refresh-cache` | 强制重新扫描 Archive |
| `--skip-archive` | 跳过 GH Archive（调试） |
| `--skip-metadata` | 跳过最终 Top 30 元数据刷新 |

## 环境变量

- `GITHUB_TOKEN` 或 `GH_TOKEN`：GitHub Personal Access Token（`public_repo` 只读即可）

## 数据流

1. GitHub Search API：按 topic 白名单批量建索引（含 topics 字段）
2. GH Archive：并行下载/解析，仅统计索引内仓库
3. 严格 topic 过滤 + 跨类去重（AI > 自动驾驶 > 新能源）
4. 仅对最终 Top 30 刷新元数据
5. 正式产出 → `output/{周次}/`；运行日志 → `output/logs/{周次}/`；缓存 → `output/tmp/`

## 输出列（CSV）

`category`, `rank`, `repo`, `url`, `stars_gained`, `total_stars`, `language`, `description`, `matched_topics`, `period`

## 限制

- Star 统计来自 GH Archive 公开事件
- `total_stars` 为脚本运行时的 API 值，非期末精确快照
- 每类最多 10 条；若合格仓库不足 10，见 `run-log.txt`
