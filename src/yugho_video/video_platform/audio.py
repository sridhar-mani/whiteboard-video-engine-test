from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Iterable

from yugho_video.mcp_server.models import AudioSpec, SegmentSpec, SpeakerTurn


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


def _run(coro):
    return asyncio.run(coro)


async def _edge_save(
    text: str,
    output: Path,
    voice: str,
    rate: str,
    pitch: str,
    volume: str,
) -> None:
    import edge_tts

    output.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(
        text,
        voice=voice,
        rate=rate,
        pitch=pitch,
        volume=volume,
    )
    await communicate.save(str(output))


def _validate_setting(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def synthesize_segment_narration(
    segment: SegmentSpec,
    audio: AudioSpec,
    output_dir: Path,
) -> tuple[Path | None, float | None]:
    has_dialogue = bool(segment.dialogue)
    has_narration = bool(segment.narration.strip())

    if audio.provider == "none" or not (has_dialogue or has_narration):
        return None, None

    if audio.provider != "edge":
        raise ValueError(f"Unsupported narration provider: {audio.provider}")

    try:
        import edge_tts  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Install edge-tts or set project.audio.provider='none'."
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)

    if has_dialogue:
        return _synthesize_dialogue(segment, audio, output_dir)

    voice = audio.voice or "en-US-EmmaMultilingualNeural"
    output = output_dir / f"{segment.id}.mp3"
    _run(
        _edge_save(
            segment.narration,
            output,
            voice,
            _validate_setting("rate", audio.rate),
            _validate_setting("pitch", audio.pitch),
            _validate_setting("volume", audio.volume),
        )
    )
    duration = _duration(output)
    if duration <= 0:
        raise RuntimeError(f"Narration produced an invalid duration: {output}")
    return output, duration


def _synthesize_dialogue(
    segment: SegmentSpec,
    audio: AudioSpec,
    output_dir: Path,
) -> tuple[Path, float]:
    clips_dir = output_dir / segment.id / "turns"
    clips_dir.mkdir(parents=True, exist_ok=True)

    clips: list[Path] = []
    pauses: list[float] = []

    for index, turn in enumerate(segment.dialogue, start=1):
        voice = turn.voice or audio.speaker_voices.get(turn.speaker) or audio.voice
        if not voice:
            raise ValueError(
                f"No voice configured for speaker {turn.speaker!r}. "
                "Set turn.voice, audio.speaker_voices, or audio.voice."
            )

        voice = _validate_setting("voice", voice)
        rate = _validate_setting("rate", turn.rate)
        pitch = _validate_setting("pitch", turn.pitch)
        volume = _validate_setting("volume", turn.volume)
        path = clips_dir / f"{index:03d}-{turn.speaker}.mp3"

        _run(
            _edge_save(
                turn.text,
                path,
                voice,
                rate,
                pitch,
                volume,
            )
        )
        clips.append(path)
        pauses.append(turn.pause_after_sec)

    output = output_dir / f"{segment.id}.dialogue.mp3"
    _concat_audio_clips(clips, pauses, output)
    duration = _duration(output)
    if duration <= 0:
        raise RuntimeError(f"Dialogue produced an invalid duration: {output}")

    return output, duration


def _concat_audio_clips(
    clips: Iterable[Path],
    pauses: Iterable[float],
    output: Path,
) -> None:
    clips = list(clips)
    pauses = list(pauses)
    if not clips:
        raise ValueError("At least one dialogue clip is required")
    if len(pauses) != len(clips):
        raise ValueError("Dialogue clip/pause counts must match")

    output.parent.mkdir(parents=True, exist_ok=True)
    list_file = output.with_suffix(".concat.txt")

    lines: list[str] = []
    for clip, pause in zip(clips, pauses, strict=True):
        escaped = clip.as_posix().replace("'", "'\\''")
        lines.append(f"file '{escaped}'\n")
        if pause > 0:
            # A tiny generated silence clip keeps the concat operation
            # deterministic and avoids expensive audio filter graphs.
            silence = output.parent / f".silence-{int(pause * 1000):04d}ms.wav"
            if not silence.exists():
                subprocess.run(
                    [
                        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "lavfi",
                        "-i", "anullsrc=r=48000:cl=stereo",
                        "-t", f"{pause:.3f}",
                        str(silence),
                    ],
                    check=True,
                )
            escaped_silence = silence.as_posix().replace("'", "'\\''")
            lines.append(f"file '{escaped_silence}'\n")

    list_file.write_text("".join(lines), encoding="utf-8")
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-vn",
            "-c:a", "libmp3lame",
            "-b:a", "160k",
            str(output),
        ],
        check=True,
    )


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
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
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
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
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
