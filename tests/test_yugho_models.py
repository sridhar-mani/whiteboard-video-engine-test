from yugho_video.mcp_server.models import SegmentSpec, VideoProject


def test_yugho_project_supports_renderer_selection() -> None:
    project = VideoProject(
        project_id="demo-project",
        title="Demo",
        topic="Demo topic",
        segments=[
            SegmentSpec(
                id="hook",
                kind="hook",
                renderer="whiteboard",
                duration_sec=5,
            ),
            SegmentSpec(
                id="diagram",
                kind="diagram",
                renderer="motion-canvas",
                duration_sec=8,
            ),
        ],
    )

    assert [segment.renderer for segment in project.segments] == [
        "whiteboard",
        "motion-canvas",
    ]


def test_tags_are_normalized_and_deduplicated() -> None:
    project = VideoProject(
        project_id="tag-demo",
        title="Demo",
        topic="Demo",
        tags=[" YUGHO ", "yugho", "whiteboard"],
        segments=[SegmentSpec(id="s1", duration_sec=1)],
    )

    assert project.tags == ["YUGHO", "whiteboard"]
