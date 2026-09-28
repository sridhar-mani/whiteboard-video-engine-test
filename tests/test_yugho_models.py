from yugho_video.mcp_server.models import SegmentSpec, SpeakerTurn, VideoProject


def test_yugho_project_supports_renderer_selection_and_dialogue() -> None:
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
                id="dialogue",
                kind="dialogue",
                renderer="whiteboard",
                duration_sec=8,
                dialogue=[
                    SpeakerTurn(
                        speaker="host",
                        text="What happened?",
                        voice="en-US-AriaNeural",
                        rate="-5%",
                    ),
                    SpeakerTurn(
                        speaker="guest",
                        text="The system changed.",
                        voice="en-US-GuyNeural",
                        pitch="+4Hz",
                    ),
                ],
            ),
        ],
    )

    assert [segment.renderer for segment in project.segments] == [
        "whiteboard",
        "whiteboard",
    ]
    assert project.segments[1].dialogue[1].pitch == "+4Hz"


def test_tags_are_normalized_and_deduplicated() -> None:
    project = VideoProject(
        project_id="tag-demo",
        title="Demo",
        topic="Demo",
        tags=[" YUGHO ", "yugho", "whiteboard"],
        segments=[SegmentSpec(id="s1", duration_sec=1)],
    )

    assert project.tags == ["YUGHO", "whiteboard"]
