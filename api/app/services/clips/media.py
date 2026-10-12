"""Clip pipeline: media IO (yt-dlp + ffmpeg).

All heavy work is executed in subprocesses / threads so the event loop stays free.
"""
import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from api.app.config import settings
from api.app.errors import AppError


class ClipToolingError(AppError):
    def __init__(self, message: str):
        super().__init__("CLIP_TOOLING_ERROR", message, 502)


_filter_cache: dict[str, bool] = {}


def has_filter(name: str) -> bool:
    """Whether this ffmpeg build exposes `name` as a video/audio filter.

    The Homebrew/LibreSSL builds often ship without libass, which means the
    `subtitles` filter is simply absent — checked once and memoized.
    """
    if name in _filter_cache:
        return _filter_cache[name]
    present = False
    try:
        proc = subprocess.run(
            [ffmpeg_path(), "-hide_banner", "-filters"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        for line in proc.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == name:
                present = True
                break
    except (OSError, subprocess.SubprocessError):
        present = False
    _filter_cache[name] = present
    return present


def ffmpeg_path() -> str:
    return shutil.which("ffmpeg") or "ffmpeg"


def ffprobe_path() -> str:
    return shutil.which("ffprobe") or "ffprobe"


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


async def _run(cmd: list[str], timeout: float) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.wait()
        raise ClipToolingError(
            f"Perintah melebihi batas waktu {timeout:g} detik: {Path(cmd[0]).name}"
        ) from exc
    return proc.returncode or 0, out.decode(errors="replace"), err.decode(errors="replace")


async def probe_duration(path: Path) -> float:
    if not ffmpeg_available():
        raise ClipToolingError("ffmpeg/ffprobe tidak ditemukan di PATH.")
    rc, out, err = await _run(
        [
            ffprobe_path(),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        timeout=settings.clip_ffprobe_timeout_seconds,
    )
    if rc != 0:
        raise ClipToolingError(f"ffprobe gagal: {err.strip()}")
    try:
        return float(json.loads(out)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise ClipToolingError(f"Durasi tidak terbaca: {exc}") from exc


def _download_sync(url: str, dest_dir: Path, socket_timeout: float) -> Path:
    try:
        import yt_dlp  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise ClipToolingError("yt-dlp tidak terpasang.") from exc

    dest_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(dest_dir / "source.%(ext)s")
    opts: dict[str, Any] = {
        "outtmpl": outtmpl,
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        "quiet": True,
        "noplaylist": True,
        "socket_timeout": socket_timeout,
        "retries": 3,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
        ydl.download([url])

    candidates = sorted(dest_dir.glob("source.*"))
    if not candidates:
        raise ClipToolingError("Unduhan selesai tetapi berkas video tidak ditemukan.")
    return candidates[0]


async def download_source(url: str, dest_dir: Path) -> Path:
    timeout = settings.clip_download_timeout_seconds
    try:
        # Hard cap on the awaited download; yt-dlp also enforces socket_timeout
        # so individual connections cannot hang indefinitely.
        return await asyncio.wait_for(
            asyncio.to_thread(_download_sync, url, dest_dir, timeout), timeout=timeout + 30
        )
    except asyncio.TimeoutError as exc:
        raise ClipToolingError(f"Unduhan melebihi batas waktu {timeout} detik.") from exc


async def extract_audio(video_path: Path, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rc, _out, err = await _run(
        [
            ffmpeg_path(),
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            str(out_path),
        ],
        timeout=settings.clip_ffmpeg_timeout_seconds,
    )
    if rc != 0:
        raise ClipToolingError(f"Ekstraksi audio gagal: {err.strip()}")
    return out_path


def _crop_filter() -> str:
    return "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"


def _escape_filter_path(path: Path) -> str:
    """Escape a filesystem path embedded in an ffmpeg filter argument.

    Paths are passed as argparse-built argv (no shell), but ffmpeg's own filter
    parser treats `:`, `\\` and `'` specially.
    """
    return str(path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _subtitle_filter(srt_path: Path) -> str:
    # `filename=` keeps ffmpeg from mis-parsing the path as filter options.
    return f"subtitles=filename='{_escape_filter_path(srt_path)}'"


def _blur_filter() -> str:
    return (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:1[bgblur];"
        "[fg]scale=1080:-2[fgscaled];"
        "[bgblur][fgscaled]overlay=(W-w)/2:(H-h)/2"
    )


def build_render_command(
    input_path: Path, output_path: Path, start: float, end: float, mode: str, srt_path: Path | None = None
) -> list[str]:
    duration = max(end - start, 0.1)
    cmd = [
        ffmpeg_path(),
        "-y",
        "-ss",
        f"{start}",
        "-t",
        f"{duration}",
        "-i",
        str(input_path),
    ]

    if mode == "blur":
        vf = _blur_filter()
        if srt_path is not None:
            vf = vf + "," + _subtitle_filter(srt_path)
        vf = vf + "[v]"
        cmd += ["-filter_complex", vf, "-map", "[v]", "-map", "0:a?"]
    else:
        vf = _crop_filter()
        if srt_path is not None:
            vf = vf + "," + _subtitle_filter(srt_path)
        cmd += ["-vf", vf]

    cmd += [
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(output_path),
    ]
    return cmd


async def render_clip(
    input_path: Path, output_path: Path, start: float, end: float, mode: str, srt_path: Path | None = None
) -> Path:
    if not ffmpeg_available():
        raise ClipToolingError("ffmpeg tidak ditemukan di PATH.")
    if srt_path is not None and not has_filter("subtitles"):
        raise ClipToolingError(
            "ffmpeg ini tidak mendukung filter 'subtitles' (libass tidak aktif). "
            "Pasang ffmpeg dengan libass, atau buat klip tanpa subtitle."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = build_render_command(input_path, output_path, start, end, mode, srt_path)
    rc, _out, err = await _run(cmd, timeout=settings.clip_ffmpeg_timeout_seconds)
    if rc != 0:
        raise ClipToolingError(f"Render gagal: {err.strip()}")
    return output_path


def write_srt(segments: list[dict], clip_start: float, clip_end: float, out_path: Path) -> Path:
    """Write an .srt for the segments overlapping [clip_start, clip_end]."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    index = 1
    for seg in segments:
        seg_start = float(seg.get("start", 0))
        seg_end = float(seg.get("end", 0))
        if seg_end <= clip_start or seg_start >= clip_end:
            continue
        start = max(seg_start, clip_start) - clip_start
        end = min(seg_end, clip_end) - clip_start
        lines.append(str(index))
        lines.append(f"{_srt_time(start)} --> {_srt_time(end)}")
        lines.append(str(seg.get("text", "")).strip())
        lines.append("")
        index += 1
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def _srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"
