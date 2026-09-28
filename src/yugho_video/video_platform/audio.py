from __future__ import annotations

import subprocess
from pathlib import Path

from yugho_video.mcp_server.models import AudioSpec, SegmentSpec


def _duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def synthesize_segment_narration(
    segment: SegmentSpec,
    audio: AudioSpec,
    output_dir: Path,
) -> tuple[Path | None, float | None]:
    if audio.provider == "none" or not segment.narration.strip():
        return None, None

    if audio.provider != "edge":
        raise ValueError(f"Unsupported narration provider: {audio.provider}")

    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError(
            "Install edge-tts or set project.audio.provider='none'."
        ) from exc

    voice = audio.voice or "en-US-AriaNeural"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"{segment.id}.mp3"

    async def synthesize() -> None:
        communicate = edge_tts.Communicate(
            segment.narration,
            voice=voice,
        )
        await communicate.save(str(output))

    import asyncio
    asyncio.run(synthesize())

    duration = _duration(output)
    if duration <= 0:
        raise RuntimeError(f"Narration produced an invalid duration: {output}")

    return output, duration


def mux_narration(
    video_path: Path,
    audio_path: Path | None,
    output_path: Path,
) -> None:
    if audio_path is None:
        if video_path != output_path:
            output_path.write_bytes(video_path.read_bytes())
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            str(output_path),
        ],
        check=True,
    )


def mix_background_music(
    video_path: Path,
    music_path: Path,
    output_path: Path,
    volume: float,
) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-i", str(video_path),
            "-stream_loop", "-1",
            "-i", str(music_path),
            "-filter_complex",
            (
                f"[1:a]volume={volume:.4f},aloop=loop=-1:size=2e+09[m];"
                "[0:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]"
            ),
            "-map", "0:v:0",
            "-map", "[a]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_path),
        ],
        check=True,
    )
