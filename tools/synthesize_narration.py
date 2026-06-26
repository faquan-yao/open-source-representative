#!/usr/bin/env python3
"""Synthesize narration audio via GPT-SoVITS with retry on transient failures."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT = _SCRIPT_DIR.parent
_SKILL_SCRIPTS = _ROOT / ".cursor/skills/presentation-to-video/scripts"
if str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from gpt_sovits_tts import resolve_gpt_sovits_config, synthesize_page  # noqa: E402
from parse_narration import parse_narration_file  # noqa: E402


def find_project_root() -> Path:
    cur = _SCRIPT_DIR
    for _ in range(8):
        if (cur / "tools" / "voice").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return _ROOT


def load_merged_config(ppt_dir: Path, project_root: Path) -> dict:
    import yaml

    cfg: dict = {"gpt_sovits": {}}
    defaults = project_root / "tools" / "voice" / "gpt-sovits.defaults.yaml"
    if defaults.exists():
        with defaults.open(encoding="utf-8") as f:
            merged = yaml.safe_load(f) or {}
            if "gpt_sovits" in merged:
                cfg["gpt_sovits"].update(merged["gpt_sovits"])

    for candidate in (
        ppt_dir / "video-config.yaml",
        ppt_dir.parent.parent / "video" / ppt_dir.name / "video-config.yaml",
    ):
        if candidate.exists():
            with candidate.open(encoding="utf-8") as f:
                merged = yaml.safe_load(f) or {}
                if "gpt_sovits" in merged:
                    cfg["gpt_sovits"].update(merged["gpt_sovits"])
            break
    return cfg


def synthesize_with_retry(
    text: str,
    out: Path,
    gpt_cfg: dict,
    retries: int,
    delay: float,
) -> None:
    for attempt in range(1, retries + 1):
        try:
            synthesize_page(text, out, gpt_cfg)
            return
        except Exception as exc:
            if attempt == retries:
                raise
            wait = delay * attempt
            print(f"[RETRY] {out.name} attempt {attempt}/{retries}, wait {wait:.0f}s: {exc}")
            time.sleep(wait)


def main() -> int:
    parser = argparse.ArgumentParser(description="GPT-SoVITS TTS with retry")
    parser.add_argument("ppt_dir", type=Path, help="PPT bundle directory")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between pages / backoff base")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--gpt-sovits-url", type=str, default=None)
    args = parser.parse_args()

    ppt_dir = Path(args.ppt_dir).resolve()
    project_root = find_project_root()
    cfg = load_merged_config(ppt_dir, project_root)
    if args.gpt_sovits_url:
        cfg.setdefault("gpt_sovits", {})
        cfg["gpt_sovits"]["api_url"] = args.gpt_sovits_url.rstrip("/")

    gpt_cfg = resolve_gpt_sovits_config(cfg, project_root)
    slides = parse_narration_file(ppt_dir / "narration-script.md")

    video_dir = ppt_dir.parent.parent / "video" / ppt_dir.name
    audio_dir = video_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    for slide in slides:
        out = audio_dir / f"{slide.page:03d}.mp3"
        if out.exists() and out.stat().st_size > 1000:
            print(f"[SKIP] Page {slide.page:03d}: {out.name} (exists)")
            continue
        print(f"[TTS] Page {slide.page:03d}: {len(slide.tts_text)} chars")
        synthesize_with_retry(slide.tts_text, out, gpt_cfg, args.retries, args.delay)
        time.sleep(max(args.delay, 2.0))

    print(f"[OK] {len(slides)} audio files -> {audio_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
