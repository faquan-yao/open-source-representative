#!/usr/bin/env python3
"""Parse narration-script.md into per-slide speech text."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

SECTION_RE = re.compile(r"^###\s*第\s*(\d+)\s*页[｜|](.+?)\s*$", re.MULTILINE)
NARRATION_START = "**口播：**"
TRANSITION_START = "**过渡：**"


@dataclass
class SlideNarration:
    page: int
    title: str
    narration: str
    transition: str

    @property
    def tts_text(self) -> str:
        """Narration + transition merged for TTS (one audio per slide)."""
        text = self.narration.strip()
        trans = self.transition.strip()
        if not trans or trans in ("（结束）", "(结束)"):
            return text
        if trans.startswith("（结束") or trans.startswith("(结束"):
            return text
        return f"{text} {trans}" if text else trans


def _extract_block(body: str, marker: str) -> tuple[str, str]:
    idx = body.find(marker)
    if idx == -1:
        return "", body
    rest = body[idx + len(marker) :].lstrip("\n")
    next_markers = [m for m in (TRANSITION_START, NARRATION_START) if m != marker]
    end = len(rest)
    for nm in next_markers:
        pos = rest.find(nm)
        if pos != -1:
            end = min(end, pos)
    block = rest[:end].strip()
    block = re.sub(r"\n---+\s*$", "", block).strip()
    remainder = rest[end:]
    return block, remainder


def parse_narration_markdown(content: str) -> list[SlideNarration]:
    matches = list(SECTION_RE.finditer(content))
    if not matches:
        raise ValueError("No slide sections found (expected '### 第 N 页｜标题')")

    slides: list[SlideNarration] = []
    for i, match in enumerate(matches):
        page = int(match.group(1))
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end]

        narration, _ = _extract_block(body, NARRATION_START)
        transition, _ = _extract_block(body, TRANSITION_START)

        if not narration:
            raise ValueError(f"Slide {page} ({title}): missing narration text")

        slides.append(
            SlideNarration(
                page=page,
                title=title,
                narration=narration,
                transition=transition,
            )
        )

    # Ensure pages are sequential 1..N
    pages = [s.page for s in slides]
    expected = list(range(1, len(slides) + 1))
    if pages != expected:
        raise ValueError(f"Slide pages must be 1..N contiguous, got {pages}")

    return slides


def parse_narration_file(path: Path) -> list[SlideNarration]:
    return parse_narration_markdown(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse narration-script.md")
    parser.add_argument("file", type=Path, help="Path to narration-script.md")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    slides = parse_narration_file(args.file)
    if args.json:
        import json

        print(
            json.dumps(
                [
                    {
                        "page": s.page,
                        "title": s.title,
                        "tts_text": s.tts_text,
                    }
                    for s in slides
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for s in slides:
            print(f"--- Page {s.page}: {s.title} ({len(s.tts_text)} chars)")
            print(s.tts_text[:120] + ("..." if len(s.tts_text) > 120 else ""))


if __name__ == "__main__":
    main()
