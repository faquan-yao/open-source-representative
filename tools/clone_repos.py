#!/usr/bin/env python3
"""Batch clone repos from weekly star-growth CSV into output/tmp/{week}/repos/{slug}/."""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR_NAME = "output"
LOGS_DIR_NAME = "logs"
TMP_DIR_NAME = "tmp"


def repo_to_slug(full_name: str) -> str:
    return full_name.replace("/", "-")


def read_csv_rows(
    csv_path: Path,
    *,
    rank: int | None = None,
    category: str | None = None,
    slug: str | None = None,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if rank is not None and str(row.get("rank", "")) != str(rank):
                continue
            if category is not None and row.get("category") != category:
                continue
            if slug is not None and repo_to_slug(row.get("repo", "")) != slug:
                continue
            rows.append(row)
    return rows


def append_log(log_path: Path, lines: list[str]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def clone_repo(url: str, dest: Path, *, depth: int, force: bool) -> tuple[bool, str]:
    if dest.exists():
        if (dest / ".git").is_dir() and not force:
            return True, "skipped (exists)"
        if force:
            shutil.rmtree(dest)

    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", "--depth", str(depth), url, str(dest)]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        return False, "timeout after 600s"
    except FileNotFoundError:
        return False, "git not found in PATH"

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "unknown error").strip()
        return False, err[:500]
    return True, "cloned"


def infer_week_dir(csv_path: Path) -> str:
    # CSV lives at {root}/output/{week_dir}/github-star-growth.csv
    if csv_path.name != "github-star-growth.csv":
        raise ValueError(f"Cannot infer week dir from CSV path: {csv_path}")
    parent = csv_path.parent
    if parent.parent.name == OUTPUT_DIR_NAME:
        return parent.name
    if parent.parent == ROOT:
        return parent.name  # legacy: {root}/{week_dir}/...
    raise ValueError(f"Cannot infer week dir from CSV path: {csv_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Clone repos from weekly star-growth CSV.")
    parser.add_argument("--csv", type=Path, required=True, help="Path to github-star-growth.csv")
    parser.add_argument("--week-dir", help='Override week folder e.g. "2026年第25周"')
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--rank", type=int, help="Only clone repos with this rank")
    parser.add_argument("--category", help="Only clone repos in this category (AI/新能源/自动驾驶)")
    parser.add_argument("--slug", help="Only clone owner-repo slug")
    parser.add_argument("--depth", type=int, default=1, help="Shallow clone depth (default 1)")
    parser.add_argument("--force", action="store_true", help="Re-clone even if directory exists")
    args = parser.parse_args()

    csv_path = args.csv if args.csv.is_absolute() else args.root / args.csv
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        return 1

    week_name = args.week_dir or infer_week_dir(csv_path)
    out_base = args.root / OUTPUT_DIR_NAME
    repos_dir = out_base / TMP_DIR_NAME / week_name / "repos"
    log_path = out_base / LOGS_DIR_NAME / week_name / "run-log.txt"

    rows = read_csv_rows(csv_path, rank=args.rank, category=args.category, slug=args.slug)
    if not rows:
        print("No matching repos in CSV.", file=sys.stderr)
        return 1

    ts = datetime.now(timezone.utc).isoformat()
    log_lines = [f"\n=== Clone repos @ {ts} ===", f"CSV: {csv_path}", f"Target: {repos_dir}", f"Repos: {len(rows)}"]

    ok_count = 0
    fail_count = 0
    for row in rows:
        repo = row.get("repo", "")
        url = row.get("url", "") or f"https://github.com/{repo}"
        slug = repo_to_slug(repo)
        dest = repos_dir / slug
        success, msg = clone_repo(url, dest, depth=args.depth, force=args.force)
        status = "OK" if success else "FAIL"
        line = f"[{status}] {repo} -> {dest.name}: {msg}"
        print(line, flush=True)
        log_lines.append(line)
        if success:
            ok_count += 1
        else:
            fail_count += 1

    log_lines.append(f"Clone summary: ok={ok_count}, fail={fail_count}")
    append_log(log_path, log_lines)

    return 0 if fail_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
