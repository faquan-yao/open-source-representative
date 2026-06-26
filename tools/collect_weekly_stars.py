#!/usr/bin/env python3
"""
Collect GitHub weekly star growth Top 10 for AI, new energy, and autonomous driving.

Optimized pipeline:
  1. Build repo->topics index via GitHub Search (batch, not per-repo)
  2. Parallel GH Archive hour downloads + parse (cached locally)
  3. Rank by category with strict topic allowlist
  4. Fetch metadata only for final Top 10 x 3 repos
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parent
DEFAULT_ALLOWLIST = TOOLS / "topic_allowlists.yaml"
OUTPUT_DIR_NAME = "output"
LOGS_DIR_NAME = "logs"
TMP_DIR_NAME = "tmp"
GH_ARCHIVE_BASE = "https://data.gharchive.org"
OSSINSIGHT_RANKING = "https://ossinsight.io/api/mcp"
GITHUB_API = "https://api.github.com"
AI_COLLECTION_ID = 10010
CATEGORY_KEYS = ("AI", "new_energy", "autonomous_driving")
TOP_N = 10
MIN_STARS_SEARCH = 5
DEFAULT_WORKERS = 12


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def iso_week_dir(start: date) -> str:
    iso = start.isocalendar()
    return f"{iso.year}年第{iso.week:02d}周"


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def date_range(start: date, end: date) -> list[date]:
    days: list[date] = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += timedelta(days=1)
    return days


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "opensource-weekly-star-collector",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def has_github_token() -> bool:
    return bool(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))


class GitHubClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(github_headers())

    def _get(self, url: str, params: dict | None = None) -> Any:
        last_exc: Exception | None = None
        for attempt in range(6):
            try:
                resp = self.session.get(url, params=params, timeout=90)
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as exc:
                last_exc = exc
                time.sleep(min(2 ** attempt, 20))
                continue
            if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
                reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait = max(reset - int(time.time()) + 1, 1)
                print(f"  GitHub rate limit, sleep {wait}s...", flush=True)
                time.sleep(wait)
                continue
            if resp.status_code in (422, 429):
                time.sleep(10)
                continue
            if resp.status_code in (502, 503, 504):
                time.sleep(5)
                continue
            resp.raise_for_status()
            return resp.json()
        raise last_exc or RuntimeError(f"Failed GET {url}")

    def search_by_topic(self, topic: str, pages: int = 1) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for page in range(1, pages + 1):
            data = self._get(
                f"{GITHUB_API}/search/repositories",
                params={
                    "q": f"topic:{topic} stars:>{MIN_STARS_SEARCH}",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 100,
                    "page": page,
                },
            )
            batch = data.get("items", [])
            items.extend(batch)
            if len(batch) < 100:
                break
        return items

    def get_repo(self, full_name: str) -> dict[str, Any]:
        return self._get(f"{GITHUB_API}/repos/{full_name}")


def output_base(root: Path) -> Path:
    """Root for all generated artifacts."""
    return root / OUTPUT_DIR_NAME


def output_dir(root: Path, week_name: str) -> Path:
    """Weekly deliverables: CSV + JSON only."""
    return output_base(root) / week_name


def logs_dir(root: Path, week_name: str) -> Path:
    """Runtime logs, separate from deliverables."""
    d = output_base(root) / LOGS_DIR_NAME / week_name
    d.mkdir(parents=True, exist_ok=True)
    return d


def tmp_week_dir(root: Path, week_name: str) -> Path:
    """Per-week temporary/cache files."""
    d = output_base(root) / TMP_DIR_NAME / week_name
    d.mkdir(parents=True, exist_ok=True)
    return d


def topic_index_cache_path(root: Path) -> Path:
    d = output_base(root) / TMP_DIR_NAME / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d / "topic_index.json"


def load_topic_index_cache(path: Path, max_age_hours: int = 168) -> dict[str, dict[str, Any]] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        saved = datetime.fromisoformat(payload["saved_at"].replace("Z", "+00:00"))
        age_h = (datetime.now(timezone.utc) - saved).total_seconds() / 3600
        if age_h > max_age_hours:
            return None
        return payload["index"]
    except (KeyError, ValueError, json.JSONDecodeError):
        return None


def save_topic_index_cache(path: Path, index: dict[str, dict[str, Any]]) -> None:
    path.write_text(
        json.dumps({"saved_at": datetime.now(timezone.utc).isoformat(), "index": index}, ensure_ascii=False),
        encoding="utf-8",
    )


def build_topic_index(
    config: dict[str, Any],
    gh: GitHubClient,
    log: list[str],
    *,
    pages_per_topic: int = 1,
    cache_path: Path | None = None,
    use_cache: bool = False,
) -> dict[str, dict[str, Any]]:
    if use_cache and cache_path:
        cached = load_topic_index_cache(cache_path)
        if cached:
            log.append(f"Loaded topic index cache: {len(cached)} repos")
            return cached

    index: dict[str, dict[str, Any]] = {}
    queried: set[str] = set()
    allow_all: set[str] = set()
    for key in CATEGORY_KEYS:
        allow_all.update(t.lower() for t in config[key]["topics"])

    for key in CATEGORY_KEYS:
        label = config[key]["label"]
        topics = config[key]["topics"]
        print(f"  Indexing {label} ({len(topics)} topics, {pages_per_topic} page/topic)...", flush=True)
        for topic in topics:
            if topic in queried:
                continue
            queried.add(topic)
            try:
                items = gh.search_by_topic(topic, pages=pages_per_topic)
            except Exception as exc:  # noqa: BLE001
                log.append(f"Search skip topic {topic}: {exc}")
                continue
            for item in items:
                fn = item["full_name"]
                raw_topics = item.get("topics") or []
                topics_lower = [t.lower() for t in raw_topics]
                if fn in index:
                    index[fn]["topics"] = sorted(set(index[fn]["topics"]) | set(topics_lower))
                else:
                    index[fn] = {
                        "topics": topics_lower,
                        "description": (item.get("description") or "")[:200],
                        "language": item.get("language") or "",
                        "total_stars": item.get("stargazers_count", 0),
                        "url": item.get("html_url", f"https://github.com/{fn}"),
                    }

    # Keep only repos that match at least one allowlist topic
    filtered = {
        fn: meta
        for fn, meta in index.items()
        if set(meta["topics"]) & allow_all
    }
    log.append(f"Topic index: {len(filtered)} repos (from {len(index)} search hits, {len(queried)} topic queries)")
    if cache_path:
        save_topic_index_cache(cache_path, filtered)
        log.append(f"Saved topic index cache: {cache_path}")
    return filtered


def fetch_ossinsight_ai_repos(log: list[str]) -> set[str]:
    repos: set[str] = set()
    try:
        resp = requests.get(
            OSSINSIGHT_RANKING,
            params={
                "action": "ranking",
                "collectionId": AI_COLLECTION_ID,
                "metric": "stars",
                "range": "last-28-days",
            },
            timeout=60,
        )
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("ok"):
            return repos
        data = payload.get("data", {})
        rows = data if isinstance(data, list) else data.get("data", data.get("list", []))
        if isinstance(rows, dict):
            rows = rows.get("data", [])
        for row in rows or []:
            if isinstance(row, dict):
                name = row.get("repo_name") or row.get("repoName") or row.get("name")
                if name and "/" in name:
                    repos.add(name)
        log.append(f"OSSInsight AI seed names: {len(repos)}")
    except Exception as exc:  # noqa: BLE001
        log.append(f"OSSInsight skip: {exc}")
    return repos


def gharchive_url(day: date, hour: int) -> str:
    return f"{GH_ARCHIVE_BASE}/{day.strftime('%Y-%m-%d')}-{hour}.json.gz"


def hour_tags(start: date, end: date) -> list[str]:
    tags: list[str] = []
    for day in date_range(start, end):
        for hour in range(24):
            tags.append(f"{day.isoformat()}-{hour:02d}")
    return tags


def download_gz(url: str, retries: int = 3) -> bytes | None:
    headers = {"User-Agent": "opensource-weekly-star-collector/2.0"}
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=120)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.content
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                return None
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
        except (requests.RequestException, OSError):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return None


def parse_hour_stars(tag: str, repo_filter: set[str] | None) -> tuple[str, dict[str, int], str | None]:
    day_s, hour_s = tag.rsplit("-", 1)
    url = f"{GH_ARCHIVE_BASE}/{day_s}-{int(hour_s)}.json.gz"
    try:
        raw = download_gz(url)
    except Exception as exc:  # noqa: BLE001
        return tag, {}, str(exc)
    if raw is None:
        return tag, {}, "404"

    counts: dict[str, int] = defaultdict(int)
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
            for line in gz:
                if b"WatchEvent" not in line or b'"started"' not in line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") != "WatchEvent":
                    continue
                if event.get("payload", {}).get("action") != "started":
                    continue
                repo_name = event.get("repo", {}).get("name")
                if not repo_name:
                    continue
                if repo_filter is not None and repo_name not in repo_filter:
                    continue
                counts[repo_name] += 1
    except Exception as exc:  # noqa: BLE001
        return tag, {}, str(exc)
    return tag, dict(counts), None


def merge_counts(target: dict[str, int], part: dict[str, int]) -> None:
    for repo, n in part.items():
        target[repo] = target.get(repo, 0) + n


def stars_cache_path(root: Path, week_name: str, start: date, end: date) -> Path:
    return tmp_week_dir(root, week_name) / f"stars_{start.isoformat()}_{end.isoformat()}.json"


def scan_gharchive_parallel(
    start: date,
    end: date,
    repo_filter: set[str],
    log: list[str],
    workers: int,
    cache_file: Path | None,
    use_cache: bool,
) -> tuple[dict[str, int], list[str], int, int]:
    tags = hour_tags(start, end)
    total = len(tags)

    if use_cache and cache_file and cache_file.exists():
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        log.append(f"Loaded star cache: {cache_file} ({len(data.get('stars', {}))} repos)")
        return data.get("stars", {}), data.get("missing", []), total, data.get("processed", total)

    stars: dict[str, int] = {}
    missing: list[str] = []
    processed = 0
    done = 0

    print(f"  Parallel scan {total} hours, workers={workers}, filter={len(repo_filter)} repos...", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(parse_hour_stars, tag, repo_filter): tag
            for tag in tags
        }
        for fut in as_completed(futures):
            tag, counts, err = fut.result()
            done += 1
            if err:
                missing.append(tag)
                if err != "404":
                    log.append(f"Hour {tag} error: {err}")
            else:
                processed += 1
                merge_counts(stars, counts)
            if done % 24 == 0 or done == total:
                print(f"  Progress {done}/{total} hours, stars repos={len(stars)}", flush=True)

    if cache_file:
        cache_file.write_text(
            json.dumps({"stars": stars, "missing": missing, "processed": processed}, ensure_ascii=False),
            encoding="utf-8",
        )
        log.append(f"Saved star cache: {cache_file}")

    return stars, missing, total, processed


def match_categories(topics: list[str], config: dict[str, Any]) -> list[str]:
    topic_set = set(topics)
    matched: list[str] = []
    for key in CATEGORY_KEYS:
        allow = {t.lower() for t in config[key]["topics"]}
        if topic_set & allow:
            matched.append(config[key]["label"])
    return matched


def rank_by_category(
    stars_started: dict[str, int],
    topic_index: dict[str, dict[str, Any]],
    config: dict[str, Any],
    log: list[str],
) -> dict[str, list[dict[str, Any]]]:
    priority = config.get("category_priority", ["AI", "自动驾驶", "新能源"])
    priority_index = {name: i for i, name in enumerate(priority)}
    allow_map = {
        config[k]["label"]: {t.lower() for t in config[k]["topics"]}
        for k in CATEGORY_KEYS
    }

    # Assign each indexed repo to one category
    repo_rows: dict[str, dict[str, Any]] = {}
    for repo, gain in stars_started.items():
        if gain <= 0 or repo not in topic_index:
            continue
        meta = topic_index[repo]
        cats = match_categories(meta["topics"], config)
        if not cats:
            continue
        best = min(cats, key=lambda c: priority_index.get(c, 999))
        matched_topics: list[str] = []
        for cat in cats:
            matched_topics.extend(sorted(set(meta["topics"]) & allow_map[cat]))
        repo_rows[repo] = {
            "repo": repo,
            "url": meta["url"],
            "stars_gained": gain,
            "total_stars": meta["total_stars"],
            "language": meta["language"],
            "description": meta["description"],
            "matched_topics": ",".join(sorted(set(matched_topics))),
            "category": best,
        }

    log.append(f"Ranked pool after topic filter: {len(repo_rows)} repos")

    results: dict[str, list[dict[str, Any]]] = {config[k]["label"]: [] for k in CATEGORY_KEYS}
    by_cat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in repo_rows.values():
        by_cat[row["category"]].append(row)

    for label, rows in by_cat.items():
        rows.sort(key=lambda r: r["stars_gained"], reverse=True)
        results[label] = rows[:TOP_N]
        for rank, row in enumerate(results[label], 1):
            row["rank"] = rank
        log.append(f"Top {TOP_N} {label}: {len(results[label])} entries")

    return results


def refresh_top_metadata(results: dict[str, list[dict[str, Any]]], gh: GitHubClient, log: list[str]) -> None:
    """Refresh total_stars/description for final rows only (~30 API calls)."""
    count = 0
    for rows in results.values():
        for row in rows:
            try:
                info = gh.get_repo(row["repo"])
                row["total_stars"] = info.get("stargazers_count", row["total_stars"])
                row["language"] = info.get("language") or row["language"]
                row["description"] = (info.get("description") or row["description"])[:200]
                row["url"] = info.get("html_url", row["url"])
                count += 1
            except Exception as exc:  # noqa: BLE001
                log.append(f"Metadata refresh skip {row['repo']}: {exc}")
    log.append(f"Refreshed metadata for {count} final repos")


def export_results(
    out_dir: Path,
    log_dir: Path,
    results: dict[str, list[dict[str, Any]]],
    period: str,
    log: list[str],
    stats: dict[str, Any],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    columns = [
        "category", "rank", "repo", "url", "stars_gained", "total_stars",
        "language", "description", "matched_topics", "period",
    ]
    rows: list[dict[str, Any]] = []
    for label in ["AI", "自动驾驶", "新能源"]:
        for item in results.get(label, []):
            row = {col: item.get(col, "") for col in columns if col != "period"}
            row["period"] = period
            rows.append(row)

    csv_path = out_dir / "github-star-growth.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    json_path = out_dir / "github-star-growth.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump({"period": period, "stats": stats, "results": results, "rows": rows}, f, ensure_ascii=False, indent=2)

    log_path = log_dir / "run-log.txt"
    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"Period: {period}\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")
        f.write("=== Stats ===\n")
        for k, v in stats.items():
            f.write(f"{k}: {v}\n")
        f.write("\n=== Log ===\n")
        for line in log:
            f.write(line + "\n")

    print(f"Wrote {csv_path}", flush=True)
    print(f"Wrote {json_path}", flush=True)
    print(f"Wrote {log_path}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect weekly GitHub star growth Top 10 by category.")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD (UTC)")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD (UTC)")
    parser.add_argument("--week-dir", help='Override output folder e.g. "2026年第24周"')
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Parallel GH Archive workers")
    parser.add_argument("--pages-per-topic", type=int, default=0, help="Search pages per topic (0=auto)")
    parser.add_argument("--use-cache", action="store_true", help="Reuse cached GH Archive star counts")
    parser.add_argument("--use-topic-cache", action="store_true", help="Reuse output/tmp/cache/topic_index.json")
    parser.add_argument("--refresh-cache", action="store_true", help="Ignore archive cache and re-scan")
    parser.add_argument("--refresh-topic-cache", action="store_true", help="Rebuild topic index cache")
    parser.add_argument("--skip-archive", action="store_true", help="Skip GH Archive (debug)")
    parser.add_argument("--skip-metadata", action="store_true", help="Skip final metadata refresh")
    args = parser.parse_args()

    start = parse_date(args.start)
    end = parse_date(args.end)
    if end < start:
        print("Error: --end must be >= --start", file=sys.stderr)
        return 1

    pages = args.pages_per_topic or (2 if has_github_token() else 1)
    week_name = args.week_dir or iso_week_dir(start)
    out_dir = output_dir(args.root, week_name)
    log_dir = logs_dir(args.root, week_name)
    period = f"{start.isoformat()}~{end.isoformat()} UTC"
    cache_file = stars_cache_path(args.root, week_name, start, end)
    use_cache = args.use_cache and not args.refresh_cache
    topic_cache = topic_index_cache_path(args.root)
    use_topic_cache = not args.refresh_topic_cache and topic_cache.exists()

    config = load_config(args.allowlist)
    log: list[str] = []
    gh = GitHubClient()
    t0 = time.time()

    print("=== Step 1: Build topic index (GitHub Search batch) ===", flush=True)
    topic_index = build_topic_index(
        config, gh, log,
        pages_per_topic=pages,
        cache_path=topic_cache,
        use_cache=use_topic_cache,
    )
    oss_seed = fetch_ossinsight_ai_repos(log)
    topic_index = {k: v for k, v in topic_index.items()}  # ensure copy
    log.append(f"Topic index ready: {len(topic_index)} repos in {time.time()-t0:.1f}s")

    stars_started: dict[str, int] = {}
    missing: list[str] = []
    total_hours = 0
    processed_hours = 0

    if args.skip_archive:
        log.append("Skipped GH Archive (--skip-archive)")
    else:
        print("=== Step 2: Parallel GH Archive scan (filtered) ===", flush=True)
        t1 = time.time()
        stars_started, missing, total_hours, processed_hours = scan_gharchive_parallel(
            start,
            end,
            set(topic_index.keys()),
            log,
            workers=args.workers,
            cache_file=cache_file,
            use_cache=use_cache,
        )
        log.append(f"Archive scan done in {time.time()-t1:.1f}s, repos with stars={len(stars_started)}")

    stats = {
        "total_hours_expected": total_hours,
        "hours_processed": processed_hours,
        "hours_missing": len(missing),
        "missing_hour_tags": missing[:20],
        "repos_with_star_events": len(stars_started),
        "topic_index_size": len(topic_index),
        "workers": args.workers,
        "elapsed_seconds": round(time.time() - t0, 1),
    }
    if total_hours:
        stats["data_completeness_pct"] = round(100 * processed_hours / total_hours, 2)

    print("=== Step 3: Rank by category ===", flush=True)
    results = rank_by_category(stars_started, topic_index, config, log)

    if not args.skip_metadata:
        print("=== Step 4: Refresh metadata (Top 30 only) ===", flush=True)
        refresh_top_metadata(results, gh, log)

    print("=== Step 5: Export ===", flush=True)
    stats["elapsed_seconds"] = round(time.time() - t0, 1)
    export_results(out_dir, log_dir, results, period, log, stats)

    total_rows = sum(len(results.get(l, [])) for l in ["AI", "自动驾驶", "新能源"])
    print(f"Done in {stats['elapsed_seconds']}s. {total_rows} rows -> {out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
