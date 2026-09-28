import pytest

from yugho_video.mcp_server.models import SegmentSpec, VideoProject
from yugho_video.video_platform.render_project import (
    apply_render_profile,
    get_render_profile,
)


def _project() -> VideoProject:
    return VideoProject(
        project_id="profile-demo",
        title="Profile Demo",
        topic="Render profiles",
        segments=[
            SegmentSpec(
                id="scene",
                duration_sec=4,
                config={"fps": 30, "width": 1280, "height": 720, "tail_color": 1.5},
            )
        ],
    )


def test_smoke_profile_is_fast_and_low_resolution() -> None:
    project = _project()

    settings = get_render_profile("smoke")
    apply_render_profile(project, "smoke")

    assert settings == {
        "width": 960,
        "height": 540,
        "fps": 12,
        "crf": 30,
        "preset": "veryfast",
    }
    assert project.segments[0].config["width"] == 960
    assert project.segments[0].config["height"] == 540
    assert project.segments[0].config["fps"] == 12


def test_preview_and_final_profiles_keep_platform_output_shape() -> None:
    for profile in ("preview", "final"):
        project = _project()
        settings = get_render_profile(profile)
        apply_render_profile(project, profile)

        assert (settings["width"], settings["height"], settings["fps"]) == (
            1920,
            1080,
            24,
        )
        assert project.segments[0].config["width"] == 1920
        assert project.segments[0].config["height"] == 1080
        assert project.segments[0].config["fps"] == 24


def test_unknown_render_profile_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown render profile"):
        get_render_profile("invalid")
