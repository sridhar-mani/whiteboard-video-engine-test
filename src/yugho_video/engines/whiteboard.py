from __future__ import annotations

from pathlib import Path

from whiteboard_skill.whiteboard import render_image
from yugho_video.mcp_server.models import SegmentSpec


def render_segment(
    segment: SegmentSpec,
    repo_root: Path,
    output_path: Path,
) -> None:
    """Render one segment through the vendored upstream whiteboard engine.

    The upstream fork remains a standalone package under src/whiteboard_skill.
    This adapter is the stable YUGHO interface around it, so the rest of the
    platform never depends on the upstream CLI or internal implementation.
    """
    if not segment.input_path:
        raise ValueError(
            f"Whiteboard segment {segment.id!r} requires input_path"
        )

    root = repo_root.resolve()
    input_path = (root / segment.input_path).resolve()

    if root not in input_path.parents and input_path != root:
        raise ValueError(
            f"Segment input escapes repository: {segment.input_path}"
        )
    if not input_path.is_file():
        raise FileNotFoundError(input_path)

    config = segment.config
    output_path.parent.mkdir(parents=True, exist_ok=True)

    render_image(
        input_path,
        output_path,
        duration=segment.duration_sec,
        fps=int(config.get("fps", 24)),
        resolution=(
            int(config.get("width", 1920)),
            int(config.get("height", 1080)),
        ),
        tail_color_sec=float(config.get("tail_color", 1.5)),
        hand_style=str(config.get("hand", "asian")),
        line_reveal_mode=str(config.get("line_reveal", "stroke")),
        color_fill_mode=str(config.get("color_fill", "contour-wipe")),
        stroke_detail=str(config.get("stroke_detail", "rich")),
        animation_preset=str(config.get("animation_preset", "classic")),
        line_thickness=int(config.get("line_thickness", 0)),
        block_fill_style=str(config.get("block_fill_style", "crayon")),
        color_fill_scope=str(config.get("color_fill_scope", "block")),
    )
