from pathlib import Path

from yugho_video.mcp_server.models import SegmentSpec, VideoProject
from yugho_video.video_platform.captions import write_srt


def test_write_srt_uses_segment_timeline(tmp_path: Path) -> None:
    project = VideoProject(
        project_id="caption-demo",
        title="Caption Demo",
        topic="Demo",
        segments=[
            SegmentSpec(id="one", duration_sec=2.5, narration="First line"),
            SegmentSpec(id="two", duration_sec=3.0, narration="Second line"),
        ],
    )

    output = tmp_path / "captions.srt"
    assert write_srt(project, output) is True

    text = output.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:02,500" in text
    assert "00:00:02,500 --> 00:00:05,500" in text
