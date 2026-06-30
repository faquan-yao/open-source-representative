#!/usr/bin/env python3
"""Batch generate narrated videos for a weekly report directory."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("week_report_dir", help="e.g. output/2026年第26周/报告")
    parser.add_argument("--only", nargs="*", help="Optional slug filter")
    args = parser.parse_args()

    base = Path(args.week_report_dir)
    script = Path(".cursor/skills/presentation-to-video/scripts/generate-video.py")
    ready: list[Path] = []
    for ppt in sorted(base.glob("*/PPT/developer-onboarding-report")):
        slug = ppt.parts[-3]
        if args.only and slug not in args.only:
            continue
        if not (ppt / "narration-script.md").exists():
            print(f"[SKIP] {slug}: no narration-script.md")
            continue
        if not (ppt / "slides.marp.md").exists():
            print(f"[SKIP] {slug}: no slides.marp.md")
            continue
        ready.append(ppt)

    ok = fail = 0
    for ppt in ready:
        slug = ppt.parts[-3]
        out = base / slug / "video" / "developer-onboarding-report" / "narrated.mp4"
        if out.exists() and out.stat().st_size > 100_000:
            print(f"[DONE] {slug}: existing {out.stat().st_size} bytes")
            ok += 1
            continue
        print(f"\n=== Video: {slug} ===", flush=True)
        r = subprocess.run([sys.executable, str(script.resolve()), str(ppt.resolve())])
        if r.returncode == 0 and out.exists():
            ok += 1
            print(f"[OK] {slug}")
        else:
            fail += 1
            print(f"[FAIL] {slug} exit={r.returncode}")

    print(f"\nSummary: {ok} ok, {fail} fail, {len(ready)} attempted")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
