#!/usr/bin/env python3
"""Generate narrated video from slides.marp.md + narration-script.md."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Allow running as script from scripts/
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from gpt_sovits_tts import (  # noqa: E402
    check_api_available,
    resolve_gpt_sovits_config,
    synthesize_all_pages,
    validate_ref_audio,
)
from parse_narration import SlideNarration, parse_narration_file  # noqa: E402

DEFAULT_CONFIG = {
    "resolution": "1920x1080",
    "fps": 30,
    "min_slide_seconds": 2,
    "padding_seconds": 0.3,
    "output": "narrated.mp4",
    "gpt_sovits": {},
}


def find_project_root() -> Path:
    cur = _SCRIPT_DIR
    for _ in range(8):
        if (cur / "tools" / "voice").is_dir():
            return cur
        if (cur / "requirements.txt").is_file() and (cur / "tools").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return _SCRIPT_DIR.parent.parent.parent.parent


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def resolve_video_dir(ppt_dir: Path) -> Path:
    """Map {产出目录}/PPT/{basename}/ → {产出目录}/video/{basename}/."""
    return ppt_dir.parent.parent / "video" / ppt_dir.name


def load_config(ppt_dir: Path, project_root: Path) -> dict:
    cfg = dict(DEFAULT_CONFIG)

    defaults_path = project_root / "tools" / "voice" / "gpt-sovits.defaults.yaml"
    cfg = _deep_merge(cfg, _load_yaml(defaults_path))

    template = _SCRIPT_DIR.parent / "templates" / "video-config.yaml"
    cfg = _deep_merge(cfg, _load_yaml(template))

    video_dir = resolve_video_dir(ppt_dir)
    for candidate in (
        ppt_dir / "video-config.yaml",
        video_dir / "video-config.yaml",
    ):
        if candidate.exists():
            cfg = _deep_merge(cfg, _load_yaml(candidate))
            break

    return cfg


def check_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required command not found in PATH: {name}")


def export_slide_images(ppt_dir: Path, marp_file: Path, slides_dir: Path) -> int:
    slides_dir.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        ps1 = _SCRIPT_DIR / "export-slide-images.ps1"
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(ps1),
                "-MarpFile",
                str(marp_file),
                "-OutputDir",
                str(slides_dir),
            ],
            check=True,
        )
    else:
        sh = _SCRIPT_DIR / "export-slide-images.sh"
        subprocess.run([str(sh), str(marp_file), str(slides_dir)], check=True)

    images = sorted(slides_dir.glob("*.png"))
    return len(images)


def _natural_sort_key(path: Path) -> tuple:
    parts = re.split(r"(\d+)", path.stem)
    return tuple(int(p) if p.isdigit() else p for p in parts)


def ordered_slide_images(slides_dir: Path) -> list[Path]:
    images = sorted(slides_dir.glob("*.png"), key=_natural_sort_key)
    if images:
        return images
    video_dir = slides_dir.parent
    raw = sorted(video_dir.glob("slides.*"), key=_natural_sort_key)
    raw = [p for p in raw if p.is_file() and p.suffix != ".mp4"]
    if raw:
        return raw
    raise FileNotFoundError(f"No slide images in {slides_dir}")


def synthesize_audio(
    slides: list[SlideNarration],
    audio_dir: Path,
    gpt_cfg: dict,
) -> list[Path]:
    return synthesize_all_pages(slides, audio_dir, gpt_cfg)


def probe_duration_seconds(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def make_segment(
    image: Path,
    audio: Path,
    output: Path,
    cfg: dict,
) -> float:
    output.parent.mkdir(parents=True, exist_ok=True)
    min_dur = float(cfg.get("min_slide_seconds", 2))
    padding = float(cfg.get("padding_seconds", 0.3))
    audio_dur = probe_duration_seconds(audio)
    duration = max(audio_dur + padding, min_dur)
    res = cfg.get("resolution", "1920x1080")
    fps = int(cfg.get("fps", 30))

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(image),
            "-i",
            str(audio),
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-vf",
            f"scale={res.replace('x', ':')}:force_original_aspect_ratio=decrease,pad={res.replace('x', ':')}:(ow-iw)/2:(oh-ih)/2",
            "-r",
            str(fps),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-t",
            f"{duration:.3f}",
            str(output),
        ],
        check=True,
        capture_output=True,
    )
    return duration


def concat_segments(segment_paths: list[Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    list_file = output.parent / "concat.txt"
    with list_file.open("w", encoding="utf-8") as f:
        for p in segment_paths:
            escaped = str(p.resolve()).replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(output),
        ],
        check=True,
        capture_output=True,
    )


def write_generation_log(
    log_path: Path,
    ppt_dir: Path,
    slide_count: int,
    total_seconds: float,
    output: Path,
    cfg: dict,
    gpt_cfg: dict,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Video generation log",
        "",
        f"- **时间：** {datetime.now().isoformat(timespec='seconds')}",
        f"- **目录：** {ppt_dir}",
        f"- **页数：** {slide_count}",
        f"- **总时长：** {total_seconds:.1f}s ({total_seconds / 60:.1f} min)",
        f"- **输出：** {output}",
        f"- **TTS：** GPT-SoVITS",
        f"- **API：** {gpt_cfg.get('api_url')}",
        f"- **参考音频：** {gpt_cfg.get('ref_audio_path')}",
        f"- **语速：** speed_factor={gpt_cfg.get('speed_factor')}",
        f"- **校验：** 页数对齐通过",
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate narrated video from PPT bundle")
    parser.add_argument(
        "ppt_dir",
        type=Path,
        help="Path to {产出目录}/PPT/{basename}/ input directory (video writes to sibling video/{basename}/)",
    )
    parser.add_argument("--skip-images", action="store_true", help="Reuse existing slide PNGs")
    parser.add_argument("--skip-tts", action="store_true", help="Reuse existing audio MP3s")
    parser.add_argument(
        "--gpt-sovits-url",
        type=str,
        default=None,
        help="Override gpt_sovits.api_url (e.g. http://127.0.0.1:9880)",
    )
    args = parser.parse_args()

    ppt_dir = Path(args.ppt_dir).resolve()
    if not ppt_dir.is_dir():
        raise FileNotFoundError(f"PPT directory not found: {ppt_dir}")

    narration_file = ppt_dir / "narration-script.md"
    marp_file = ppt_dir / "slides.marp.md"
    if not narration_file.exists():
        raise FileNotFoundError(f"Missing {narration_file}")
    if not marp_file.exists():
        raise FileNotFoundError(
            f"Missing {marp_file}. Run document-to-presentation first or provide Marp source."
        )

    project_root = find_project_root()
    cfg = load_config(ppt_dir, project_root)
    if args.gpt_sovits_url:
        cfg.setdefault("gpt_sovits", {})
        cfg["gpt_sovits"]["api_url"] = args.gpt_sovits_url.rstrip("/")

    gpt_cfg = resolve_gpt_sovits_config(cfg, project_root)
    ref_path = Path(gpt_cfg["ref_audio_path"])
    validate_ref_audio(ref_path)

    video_dir = resolve_video_dir(ppt_dir)
    slides_dir = video_dir / "slides"
    audio_dir = video_dir / "audio"
    segments_dir = video_dir / "segments"
    output_key = cfg["output"]
    if not Path(output_key).is_absolute() and str(output_key).startswith("video/"):
        output_key = str(Path(output_key).name)
    output = Path(output_key) if Path(output_key).is_absolute() else video_dir / output_key

    check_command("ffmpeg")
    check_command("ffprobe")
    check_api_available(gpt_cfg["api_url"])
    print(f"[INFO] GPT-SoVITS API: {gpt_cfg['api_url']}")

    slides_narration = parse_narration_file(narration_file)
    print(f"[INFO] Parsed {len(slides_narration)} narration sections")

    if args.skip_images and slides_dir.exists() and list(slides_dir.glob("*.png")):
        image_count = len(list(slides_dir.glob("*.png")))
        print(f"[INFO] Reusing {image_count} existing slide images")
    else:
        image_count = export_slide_images(ppt_dir, marp_file, slides_dir)
        print(f"[INFO] Exported {image_count} slide images")

    slide_images = ordered_slide_images(slides_dir)
    if len(slide_images) != len(slides_narration):
        raise ValueError(
            f"Slide count mismatch: {len(slide_images)} images vs "
            f"{len(slides_narration)} narration pages"
        )

    if args.skip_tts and audio_dir.exists():
        audio_files = sorted(audio_dir.glob("*.mp3"))
        if len(audio_files) != len(slides_narration):
            raise ValueError("Cached audio count mismatch; delete video/audio and retry")
        print(f"[INFO] Reusing {len(audio_files)} audio files")
    else:
        synthesize_audio(slides_narration, audio_dir, gpt_cfg)
        audio_files = sorted(audio_dir.glob("*.mp3"))

    if len(slide_images) != len(audio_files):
        raise ValueError(
            f"Image/audio count mismatch: {len(slide_images)} vs {len(audio_files)}"
        )

    segment_paths: list[Path] = []
    total_seconds = 0.0
    for i, (image, audio) in enumerate(zip(slide_images, audio_files)):
        seg = segments_dir / f"{i + 1:03d}.mp4"
        dur = make_segment(image, audio, seg, cfg)
        total_seconds += dur
        segment_paths.append(seg)
        print(f"[SEG] {seg.name} ({dur:.1f}s)")

    concat_segments(segment_paths, output)
    print(f"[OK] Video: {output} ({total_seconds / 60:.1f} min)")

    write_generation_log(
        video_dir / "generation-log.md",
        ppt_dir,
        len(slides_narration),
        total_seconds,
        output,
        cfg,
        gpt_cfg,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
