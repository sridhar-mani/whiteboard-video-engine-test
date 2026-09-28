from __future__ import annotations

import json
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


def write_srt(
    project: VideoProject,
    output: Path,
    timing_dir: Path | None = None,
) -> bool:
    cues: list[str] = []
    clock = 0.0
    sequence = 1

    for segment in project.segments:
        timing_file = (
            timing_dir / f"{segment.id}.timing.json"
            if timing_dir
            else None
        )

        if segment.dialogue and timing_file and timing_file.exists():
            payload = json.loads(
                timing_file.read_text(encoding="utf-8")
            )
            for turn in payload.get("turns", []):
                start = clock + float(turn["start_sec"])
                end = clock + float(turn["end_sec"])
                cues.append(
                    f"{sequence}\n"
                    f"{_timestamp(start)} --> {_timestamp(end)}\n"
                    f"{turn['speaker']}: {turn['text']}\n"
                )
                sequence += 1
            clock += max(
                segment.duration_sec,
                float(payload.get("turns", [{}])[-1].get("end_sec", 0.0))
                if payload.get("turns")
                else 0.0,
            )
            continue

        if segment.dialogue:
            for turn in segment.dialogue:
                duration = max(0.45, len(turn.text.split()) / 2.65)
                start = clock
                end = start + duration
                cues.append(
                    f"{sequence}\n"
                    f"{_timestamp(start)} --> {_timestamp(end)}\n"
                    f"{turn.speaker}: {turn.text}\n"
                )
                sequence += 1
                clock = end + turn.pause_after_sec
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
