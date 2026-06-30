#!/usr/bin/env python3
"""Batch export slides.marp.md to slides.pptx for a week directory."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("week_dir", help='e.g. output/2026年第26周/报告')
    args = parser.parse_args()
    base = Path(args.week_dir)
    script = Path(".cursor/skills/document-to-presentation/scripts/export-pptx.ps1")
    marps = sorted(base.glob("*/PPT/developer-onboarding-report/slides.marp.md"))
    ok = fail = 0
    for m in marps:
        slug = m.parts[-4]
        print(f"Exporting {slug}...", flush=True)
        r = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-File",
                str(script.resolve()),
                "-MarpFile",
                str(m.resolve()),
            ],
            capture_output=True,
            text=True,
        )
        ppt = m.parent / "slides.pptx"
        if ppt.exists() and ppt.stat().st_size > 50_000:
            ok += 1
            print(f"  OK ({ppt.stat().st_size} bytes)")
        else:
            fail += 1
            err = (r.stderr or r.stdout or "").strip()[-500:]
            print(f"  FAIL: {err}")
    print(f"Done: {ok} ok, {fail} fail, {len(marps)} total")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
