from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import imageio_ffmpeg
from yt_dlp import YoutubeDL


ProgressFn = Callable[[str], None]


class ClipError(RuntimeError):
    """A user-facing clipping failure."""


@dataclass(frozen=True)
class VideoInfo:
    title: str
    duration: int | None
    uploader: str | None
    webpage_url: str
    thumbnail: str | None


@dataclass(frozen=True)
class ClipResult:
    path: Path
    filename: str
    mime_type: str


def get_ffmpeg_path() -> str:
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def parse_timestamp(value: str) -> int:
    raw = value.strip()
    if not raw:
        raise ClipError("Enter a timestamp.")

    parts = raw.split(":")
    if len(parts) > 3 or any(not part.isdigit() for part in parts):
        raise ClipError("Use timestamps like 75, 1:15, or 00:01:15.")

    nums = [int(part) for part in parts]
    if len(nums) == 1:
        hours, minutes, seconds = 0, 0, nums[0]
    elif len(nums) == 2:
        hours, minutes, seconds = 0, nums[0], nums[1]
    else:
        hours, minutes, seconds = nums

    if minutes > 59 or seconds > 59:
        raise ClipError("Minutes and seconds must be between 0 and 59.")
    return hours * 3600 + minutes * 60 + seconds


def format_timestamp(total_seconds: int) -> str:
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def clean_filename(value: str, fallback: str = "youtube_clip") -> str:
    cleaned = re.sub(r"[^\w\s.-]", "", value, flags=re.ASCII).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = cleaned[:80].strip("._-")
    return cleaned or fallback


def _base_ydl_opts(ffmpeg_path: str, cookies_path: Path | None = None) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "ffmpeg_location": ffmpeg_path,
        "retries": 8,
        "fragment_retries": 8,
        "extractor_retries": 3,
        "socket_timeout": 30,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        # Recent YouTube changes sometimes break one client while another works.
        # Keeping a small fallback set avoids many "HTTP Error 403" failures.
        "extractor_args": {
            "youtube": {
                "player_client": ["default", "tv"],
            }
        },
    }
    if cookies_path:
        opts["cookiefile"] = str(cookies_path)
    return opts


def fetch_video_info(url: str, cookies_path: Path | None = None) -> VideoInfo:
    ffmpeg_path = get_ffmpeg_path()
    opts = _base_ydl_opts(ffmpeg_path, cookies_path)
    opts["skip_download"] = True

    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        raise ClipError(_friendly_ytdlp_error(exc)) from exc

    return VideoInfo(
        title=info.get("title") or "Untitled video",
        duration=info.get("duration"),
        uploader=info.get("uploader"),
        webpage_url=info.get("webpage_url") or url,
        thumbnail=info.get("thumbnail"),
    )


def create_clip(
    url: str,
    start_seconds: int,
    end_seconds: int,
    output_kind: str,
    quality: str,
    cookies_path: Path | None = None,
    progress: ProgressFn | None = None,
) -> ClipResult:
    if end_seconds <= start_seconds:
        raise ClipError("End time must be after start time.")

    ffmpeg_path = get_ffmpeg_path()
    progress = progress or (lambda _message: None)
    clip_id = uuid.uuid4().hex[:10]

    with tempfile.TemporaryDirectory(prefix="yt_clip_") as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        progress("Reading video metadata...")
        info = fetch_video_info(url, cookies_path)

        if info.duration is not None and start_seconds >= info.duration:
            raise ClipError("Start time is beyond the video duration.")
        if info.duration is not None and end_seconds > info.duration:
            raise ClipError("End time is beyond the video duration.")

        source_template = tmp_dir / f"source_{clip_id}.%(ext)s"
        source_path = _download_source(
            url=url,
            output_template=source_template,
            quality=quality,
            ffmpeg_path=ffmpeg_path,
            cookies_path=cookies_path,
            progress=progress,
        )

        title = clean_filename(info.title)
        start_label = format_timestamp(start_seconds).replace(":", "-")
        end_label = format_timestamp(end_seconds).replace(":", "-")

        if output_kind == "mp3":
            output_path = tmp_dir / f"{title}_{start_label}_{end_label}.mp3"
            progress("Extracting audio clip...")
            _run_ffmpeg(
                [
                    ffmpeg_path,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-ss",
                    format_timestamp(start_seconds),
                    "-to",
                    format_timestamp(end_seconds),
                    "-i",
                    str(source_path),
                    "-vn",
                    "-codec:a",
                    "libmp3lame",
                    "-q:a",
                    "2",
                    str(output_path),
                ]
            )
            mime = "audio/mpeg"
        else:
            output_path = tmp_dir / f"{title}_{start_label}_{end_label}.mp4"
            progress("Rendering video clip...")
            _clip_video(ffmpeg_path, source_path, output_path, start_seconds, end_seconds)
            mime = "video/mp4"

        final_dir = Path.cwd() / "clips"
        final_dir.mkdir(exist_ok=True)
        final_path = final_dir / output_path.name
        shutil.copy2(output_path, final_path)
        progress("Done.")
        return ClipResult(path=final_path, filename=final_path.name, mime_type=mime)


def _download_source(
    url: str,
    output_template: Path,
    quality: str,
    ffmpeg_path: str,
    cookies_path: Path | None,
    progress: ProgressFn,
) -> Path:
    height_limit = {"Small": 480, "Balanced": 720, "Best": 2160}[quality]
    opts = _base_ydl_opts(ffmpeg_path, cookies_path)
    opts.update(
        {
            "outtmpl": str(output_template),
            "merge_output_format": "mp4",
            "format": (
                f"bv*[height<={height_limit}][vcodec^=avc1][ext=mp4]+ba[ext=m4a]/"
                f"b[height<={height_limit}][ext=mp4]/"
                f"bv*[height<={height_limit}]+ba/"
                "b[ext=mp4]/best"
            ),
            "format_sort": ["hasvid", "height", "fps", "codec:avc:m4a"],
            "progress_hooks": [lambda data: _download_hook(data, progress)],
        }
    )

    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            prepared = Path(ydl.prepare_filename(info))
    except Exception as exc:
        raise ClipError(_friendly_ytdlp_error(exc)) from exc

    candidates = list(output_template.parent.glob(f"{output_template.stem}.*"))
    candidates = [path for path in candidates if path.suffix not in {".part", ".ytdl"}]
    if not candidates and prepared.exists():
        candidates = [prepared]
    if not candidates:
        raise ClipError("The download finished, but the video file could not be found.")

    return max(candidates, key=lambda path: path.stat().st_size)


def _download_hook(data: dict, progress: ProgressFn) -> None:
    if data.get("status") == "downloading":
        percent = data.get("_percent_str", "").strip()
        speed = data.get("_speed_str", "").strip()
        eta = data.get("_eta_str", "").strip()
        detail = " ".join(part for part in [percent, speed, f"ETA {eta}" if eta else ""] if part)
        progress(f"Downloading source video... {detail}".strip())
    elif data.get("status") == "finished":
        progress("Preparing downloaded media...")


def _clip_video(
    ffmpeg_path: str,
    source_path: Path,
    output_path: Path,
    start_seconds: int,
    end_seconds: int,
) -> None:
    start = format_timestamp(start_seconds)
    end = format_timestamp(end_seconds)

    # Fast path: copies streams. If the cut lands between keyframes, retry with
    # a light re-encode so the resulting MP4 opens reliably.
    try:
        _run_ffmpeg(
            [
                ffmpeg_path,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                start,
                "-to",
                end,
                "-i",
                str(source_path),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )
        if output_path.exists() and output_path.stat().st_size > 0:
            return
    except ClipError:
        pass

    _run_ffmpeg(
        [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            start,
            "-to",
            end,
            "-i",
            str(source_path),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )


def _run_ffmpeg(args: list[str]) -> None:
    completed = subprocess.run(args, capture_output=True, text=True)
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "FFmpeg failed."
        raise ClipError(message)


def _friendly_ytdlp_error(exc: Exception) -> str:
    text = str(exc)
    lowered = text.lower()
    if "winerror 10013" in lowered or "failed to establish a new connection" in lowered:
        return (
            "The app could not reach YouTube from this Python process. Check your "
            "network, firewall, VPN, or sandbox permissions and try again."
        )
    if "http error 403" in lowered or "403: forbidden" in lowered:
        return (
            "YouTube rejected the media request with HTTP 403. Update yt-dlp first; "
            "if the video is private, age-restricted, members-only, or region-limited, "
            "export cookies from a browser account that can view it and upload them here."
        )
    if "ffmpeg" in lowered:
        return "FFmpeg is missing or failed. Reinstall requirements and try again."
    return text
