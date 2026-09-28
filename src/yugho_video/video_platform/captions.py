from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from yugho_video.mcp_server.models import VideoProject


def _timestamp(seconds: float) -> str:
    total_ms = int(max(0.0, seconds) * 1000)
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    millis = remainder % 1000
    seconds_part = (remainder // 1000) % 60
    return f"{hours:02d}:{minutes:02d}:{seconds_part:02d},{millis:03d}"


def write_srt(project: VideoProject, output: Path) -> bool:
    cues: list[str] = []
    clock = 0.0
    sequence = 1

    for segment in project.segments:
        if segment.dialogue:
            for turn in segment.dialogue:
                start = clock
                clock += _estimated_turn_duration(turn)
                label = f"{turn.speaker}: " if turn.speaker else ""
                cues.append(
                    f"{sequence}\n"
                    f"{_timestamp(start)} --> {_timestamp(clock)}\n"
                    f"{label}{turn.text}\n"
                )
                sequence += 1
                clock += turn.pause_after_sec
            continue

        narration = segment.narration.strip()
        start = clock
        clock += segment.duration_sec
        if narration:
            cues.append(
                f"{sequence}\n"
                f"{_timestamp(start)} --> {_timestamp(clock)}\n"
                f"{narration}\n"
            )
            sequence += 1

    if not cues:
        return False

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(cues) + "\n", encoding="utf-8")
    return True


def _estimated_turn_duration(turn) -> float:
    # Captions are authored from text before TTS timing is available.
    # The render manifest can later be used to replace this with exact
    # provider timings if we add a word-timestamp provider.
    words = max(1, len(turn.text.split()))
    return max(0.45, words / 2.65)
