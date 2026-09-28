from mcp_server.models import SegmentSpec, VideoProject


def test_video_project_accepts_modular_segments() -> None:
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
                narration="Hook",
                input_path="tests/fixtures/apple.svg",
            ),
            SegmentSpec(
                id="diagram",
                kind="diagram",
                renderer="motion-canvas",
                duration_sec=8,
            ),
        ],
    )

    assert len(project.segments) == 2
    assert project.segments[1].renderer == "motion-canvas"


def test_tags_are_normalized_and_deduplicated() -> None:
    project = VideoProject(
        project_id="tag-demo",
        title="Demo",
        topic="Demo",
        tags=[" YUGHO ", "yugho", "whiteboard"],
        segments=[SegmentSpec(id="s1", duration_sec=1)],
    )

    assert project.tags == ["YUGHO", "whiteboard"]
