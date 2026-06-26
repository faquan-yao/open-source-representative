#!/usr/bin/env python3
"""GPT-SoVITS API client for per-slide TTS synthesis."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_GPT_SOVITS = {
    "api_url": "http://127.0.0.1:9880",
    "ref_audio_path": "",
    "prompt_text": "",
    "prompt_text_file": "",
    "prompt_lang": "zh",
    "text_lang": "zh",
    "speed_factor": 0.95,
    "repetition_penalty": 1.35,
    "text_split_method": "cut5",
    "timeout_seconds": 300,
}

_API_START_HINT = (
    "请先启动 GPT-SoVITS API：整合包双击 go-api.bat，"
    "或 runtime\\python.exe -I api_v2.py -a 127.0.0.1 -p 9880 "
    "（详见 presentation-to-video/references/gpt-sovits-setup.md）"
)
_HALF_CPU_HINT = (
    "GPT-SoVITS 正在 CPU 上以半精度 (fp16) 推理，PyTorch 不支持。"
    "请编辑 {GPT-SoVITS}/GPT_SoVITS/configs/tts_infer.yaml 的 custom 段："
    "device: cpu、is_half: false，然后重启 go-api.bat。"
    "若有 NVIDIA GPU，请安装驱动/CUDA 并确认整合包 runtime 能识别 GPU。"
)


def _resolve_path(path_str: str, project_root: Path) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p.resolve()
    return (project_root / p).resolve()


def resolve_gpt_sovits_config(cfg: dict, project_root: Path) -> dict:
    """Merge and resolve paths / prompt text from video-config."""
    raw = dict(DEFAULT_GPT_SOVITS)
    raw.update(cfg.get("gpt_sovits") or {})

    ref = raw.get("ref_audio_path", "")
    if not ref:
        raise ValueError("gpt_sovits.ref_audio_path is required")
    raw["ref_audio_path"] = str(_resolve_path(ref, project_root))

    prompt_text = (raw.get("prompt_text") or "").strip()
    prompt_file = (raw.get("prompt_text_file") or "").strip()
    if not prompt_text and prompt_file:
        pf = _resolve_path(prompt_file, project_root)
        if not pf.exists():
            raise FileNotFoundError(f"prompt_text_file not found: {pf}")
        prompt_text = pf.read_text(encoding="utf-8").strip()
    if not prompt_text:
        raise ValueError("gpt_sovits.prompt_text or prompt_text_file is required")
    raw["prompt_text"] = prompt_text

    api_url = (raw.get("api_url") or DEFAULT_GPT_SOVITS["api_url"]).rstrip("/")
    raw["api_url"] = api_url
    return raw


def validate_ref_audio(ref_path: Path, *, min_seconds: float = 3.0, max_seconds: float = 10.0) -> None:
    """Ensure reference audio duration is within GPT-SoVITS limits."""
    if not ref_path.exists():
        raise FileNotFoundError(f"Reference audio not found: {ref_path}")
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(ref_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        duration = float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as exc:
        raise RuntimeError(f"Cannot probe reference audio duration: {ref_path}") from exc
    if duration < min_seconds or duration > max_seconds:
        raise ValueError(
            f"Reference audio duration {duration:.1f}s is outside GPT-SoVITS "
            f"required range ({min_seconds:g}-{max_seconds:g}s): {ref_path}. "
            "Trim tools/voice/ref.wav and update ref.txt to match the spoken text."
        )


def check_api_available(api_url: str, timeout: float = 3.0) -> None:
    """Verify GPT-SoVITS api_v2.py is reachable."""
    probe = f"{api_url.rstrip('/')}/set_gpt_weights?weights_path="
    try:
        req = urllib.request.Request(probe, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (400, 422):
            return
        if exc.code == 404:
            raise RuntimeError(
                f"GPT-SoVITS API not found at {api_url}. {_API_START_HINT}"
            ) from exc
        raise RuntimeError(
            f"GPT-SoVITS API error at {api_url} (HTTP {exc.code}). {_API_START_HINT}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"无法连接 GPT-SoVITS API ({api_url}): {exc.reason}. {_API_START_HINT}"
        ) from exc


def _build_tts_payload(text: str, gpt_cfg: dict) -> dict[str, Any]:
    return {
        "text": text,
        "text_lang": gpt_cfg["text_lang"],
        "ref_audio_path": gpt_cfg["ref_audio_path"],
        "prompt_text": gpt_cfg["prompt_text"],
        "prompt_lang": gpt_cfg["prompt_lang"],
        "speed_factor": float(gpt_cfg.get("speed_factor", 0.95)),
        "repetition_penalty": float(gpt_cfg.get("repetition_penalty", 1.35)),
        "text_split_method": gpt_cfg.get("text_split_method", "cut5"),
        "media_type": "wav",
        "streaming_mode": False,
    }


def _post_tts_wav(text: str, gpt_cfg: dict) -> bytes:
    url = f"{gpt_cfg['api_url']}/tts"
    payload = json.dumps(_build_tts_payload(text, gpt_cfg), ensure_ascii=False).encode("utf-8")
    timeout = float(gpt_cfg.get("timeout_seconds", 300))
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            body = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(detail)
            msg = body.get("message", detail)
            if body.get("Exception"):
                msg = f"{msg}: {body['Exception']}"
        except json.JSONDecodeError:
            msg = detail
        if "slow_conv2d_cpu" in msg or "not implemented for 'Half'" in msg:
            msg = f"{msg}. {_HALF_CPU_HINT}"
        raise RuntimeError(f"GPT-SoVITS /tts failed (HTTP {exc.code}): {msg}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GPT-SoVITS /tts request failed: {exc.reason}") from exc

    if "json" in content_type.lower():
        try:
            err = json.loads(body.decode("utf-8"))
            raise RuntimeError(f"GPT-SoVITS /tts failed: {err.get('message', err)}")
        except json.JSONDecodeError as exc:
            raise RuntimeError("GPT-SoVITS /tts returned unexpected JSON") from exc
    return body


def _split_tts_text(text: str, max_chars: int = 35, min_chars: int = 4) -> list[str]:
    """Split long narration into GPT-SoVITS-safe chunks (API may drop long requests)."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    raw_chunks: list[str] = []
    parts = re.split(r"([。！？；，、：])", text)
    current = ""
    for part in parts:
        if not part:
            continue
        candidate = current + part
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current.strip():
            raw_chunks.append(current.strip())
        if len(part) <= max_chars:
            current = part
        else:
            for i in range(0, len(part), max_chars):
                segment = part[i : i + max_chars].strip()
                if segment:
                    raw_chunks.append(segment)
            current = ""
    if current.strip():
        raw_chunks.append(current.strip())

    # Merge tiny / punctuation-only chunks into neighbors (GPT-SoVITS rejects 1-char text).
    merged: list[str] = []
    for chunk in raw_chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if merged and (len(chunk) < min_chars or re.fullmatch(r"[\W_]+", chunk)):
            merged[-1] = (merged[-1] + chunk).strip()
        elif merged and len(merged[-1]) < min_chars:
            merged[-1] = (merged[-1] + chunk).strip()
        else:
            merged.append(chunk)
    return merged or [text]


def _concat_wav_bytes(wav_parts: list[bytes]) -> bytes:
    if len(wav_parts) == 1:
        return wav_parts[0]
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        list_file = tmp_dir / "concat.txt"
        paths: list[Path] = []
        for i, data in enumerate(wav_parts):
            p = tmp_dir / f"part_{i:03d}.wav"
            p.write_bytes(data)
            paths.append(p)
        list_file.write_text(
            "\n".join(f"file '{p.as_posix()}'" for p in paths),
            encoding="utf-8",
        )
        out = tmp_dir / "merged.wav"
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
                str(out),
            ],
            check=True,
            capture_output=True,
        )
        return out.read_bytes()


def synthesize_text_wav(text: str, gpt_cfg: dict, *, chunk_delay: float = 2.0) -> bytes:
    """Synthesize text to WAV bytes, chunking when needed."""
    import time

    chunks = _split_tts_text(text)
    if not chunks:
        raise ValueError("Empty TTS text")
    wav_parts: list[bytes] = []
    for i, chunk in enumerate(chunks):
        if i:
            time.sleep(chunk_delay)
        last_err: Exception | None = None
        for attempt in range(1, 5):
            try:
                wav_parts.append(_post_tts_wav(chunk, gpt_cfg))
                break
            except Exception as exc:
                last_err = exc
                if attempt == 4:
                    raise
                wait = 3.0 * attempt
                print(f"[RETRY] TTS chunk ({len(chunk)} chars) attempt {attempt}/4, wait {wait:.0f}s: {exc}")
                time.sleep(wait)
        else:
            if last_err:
                raise last_err
    return _concat_wav_bytes(wav_parts)


def wav_to_mp3(wav_path: Path, mp3_path: Path) -> None:
    mp3_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(wav_path),
            "-codec:a",
            "libmp3lame",
            "-qscale:a",
            "2",
            str(mp3_path),
        ],
        check=True,
        capture_output=True,
    )


def synthesize_page(text: str, out_mp3: Path, gpt_cfg: dict) -> None:
    """Synthesize one page via GPT-SoVITS API and write MP3."""
    wav_bytes = synthesize_text_wav(text, gpt_cfg)
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    wav_tmp = out_mp3.with_suffix(".wav")
    wav_tmp.write_bytes(wav_bytes)
    try:
        wav_to_mp3(wav_tmp, out_mp3)
    finally:
        if wav_tmp.exists():
            wav_tmp.unlink()


def synthesize_all_pages(
    slides: list,
    audio_dir: Path,
    gpt_cfg: dict,
) -> list[Path]:
    """Synthesize MP3 for each slide; slides need .page and .tts_text."""
    audio_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for slide in slides:
        out = audio_dir / f"{slide.page:03d}.mp3"
        synthesize_page(slide.tts_text, out, gpt_cfg)
        paths.append(out)
        print(f"[TTS] Page {slide.page:03d}: {out.name} ({len(slide.tts_text)} chars)")
    return paths
