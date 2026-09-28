from __future__ import annotations

from pathlib import Path
from typing import Protocol

from yugho_video.mcp_server.models import SegmentSpec
from yugho_video.engines.whiteboard import render_segment as render_whiteboard_segment


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
        render_whiteboard_segment(segment, repo_root, output_path)


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
