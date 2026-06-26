# GitHub 周增 Star — 统计口径与排错

## stars_gained 计算

| 项 | 说明 |
|----|------|
| 数据源 | GH Archive 小时 JSON（**必须 HTTPS**） |
| 事件类型 | `WatchEvent` |
| 计数条件 | `payload.action == "started"` |
| 口径 | **毛增**（不计 `deleted` 取消 star） |
| 去重 | **不按用户去重**（与 GitHub 页面可能有 ±几个百分点偏差） |
| 范围 | 仅统计 **topic 索引内** 仓库（Search 按白名单预建） |

### 流水线

```
topic_allowlists.yaml
    → GitHub Search 批量索引（~4000+ repos）
    → GH Archive 168 小时并行扫描（默认 12–16 workers）
    → 严格 topic 分类 + 跨类去重（AI > 自动驾驶 > 新能源）
    → 每类 Top 10
    → GET /repos 刷新 Top 30 元数据
    → 写入 output/{周次}/（CSV+JSON）、output/logs/{周次}/（run-log）、output/tmp/（缓存）
```

### 分类规则

- 仓库 GitHub Topics 须与 YAML 白名单有交集
- 多类命中时按 `category_priority` 保留一类
- 类内排序键：`stars_gained` 降序

## 缓存

| 路径 | 用途 |
|------|------|
| `output/tmp/cache/topic_index.json` | topic 索引，跨周复用 |
| `output/tmp/{周次}/stars_{start}_{end}.json` | 当周 Archive 计数，`--use-cache` 跳过重扫 |
| `output/logs/{周次}/run-log.txt` | 运行日志与 QA 记录 |

## 故障排查

| 现象 | 原因 | 处理 |
|------|------|------|
| Archive 全部 403 | 使用了 `http://` | 脚本已固定 `https://data.gharchive.org` |
| 0 条结果 | 小时文件未下载或索引为空 | 查 run-log 的 `hours_processed`、`topic_index_size` |
| Search 极慢 / 频繁 sleep | 无 token，60 次/小时 | 设置 `GITHUB_TOKEN`；复用 topic 索引缓存 |
| 部分小时缺失 | SSL / 网络 | run-log 记录 `missing_hour_tags`；完整率 <95% 须在 QA 说明 |
| AI 与 star-history 数值差 | 日期窗口不同 | 比排名与量级，不要求完全一致 |

## 扩展

- **新增类别**：`tools/topic_allowlists.yaml` 增加块 + 更新 `category_priority`
- **改 Top N**：`tools/collect_weekly_stars.py` 中 `TOP_N`
- **放宽/收紧 topic**：编辑各类 `topics` 列表

## QA 检查清单

- [ ] `data_completeness_pct` ≥ 95%
- [ ] 三类合计目标行数（默认 30）或 run-log 解释不足原因
- [ ] AI Top 3 与 star-history 周榜头部同量级
- [ ] 无跨类重复 `repo`
- [ ] CSV 可在 Excel 正常打开（UTF-8 BOM）
