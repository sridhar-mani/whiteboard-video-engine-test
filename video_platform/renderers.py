from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Protocol

from .models import SegmentSpec


class SegmentRenderer(Protocol):
    name: str

    def render(
        self,
        segment: SegmentSpec,
        repo_root: Path,
        output_path: Path,
    ) -> None:
        ...


class WhiteboardRenderer:
    name = "whiteboard"

    def render(
        self,
        segment: SegmentSpec,
        repo_root: Path,
        output_path: Path,
    ) -> None:
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
        fps = int(config.get("fps", 24))
        width = int(config.get("width", 1920))
        height = int(config.get("height", 1080))
        hand = str(config.get("hand", "asian"))
        preset = str(config.get("animation_preset", "classic"))

        output_path.parent.mkdir(parents=True, exist_ok=True)

        command = [
            "whiteboard",
            "render-image",
            str(input_path),
            "--output",
            str(output_path),
            "--duration",
            str(segment.duration_sec),
            "--fps",
            str(fps),
            "--width",
            str(width),
            "--height",
            str(height),
            "--hand",
            hand,
            "--animation-preset",
            preset,
            "--stroke-detail",
            str(config.get("stroke_detail", "rich")),
            "--line-reveal",
            str(config.get("line_reveal", "stroke")),
            "--tail-color",
            str(config.get("tail_color", 1.5)),
            "--color-fill",
            str(config.get("color_fill", "contour-wipe")),
            "--block-fill-style",
            str(config.get("block_fill_style", "crayon")),
            "--color-fill-scope",
            str(config.get("color_fill_scope", "block")),
            "--line-thickness",
            str(config.get("line_thickness", 0)),
        ]
        subprocess.run(command, cwd=repo_root, check=True)


RENDERERS: dict[str, SegmentRenderer] = {
    WhiteboardRenderer.name: WhiteboardRenderer(),
}


def get_renderer(name: str) -> SegmentRenderer:
    try:
        return RENDERERS[name]
    except KeyError as exc:
        available = ", ".join(sorted(RENDERERS))
        raise ValueError(
            f"Unsupported renderer {name!r}; available: {available}"
        ) from exc
