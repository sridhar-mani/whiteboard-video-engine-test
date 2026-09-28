from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from yugho_video.mcp_server.models import VideoProject
from yugho_video.video_platform.audio import (
    mix_background_music,
    mux_narration,
    synthesize_segment_narration,
)
from yugho_video.video_platform.captions import write_srt
from yugho_video.video_platform.renderers import get_renderer


RENDER_PROFILES: dict[str, dict[str, object]] = {
    "smoke": {
        "width": 960,
        "height": 540,
        "fps": 12,
        "crf": 30,
        "preset": "veryfast",
    },
    "preview": {
        "width": 1920,
        "height": 1080,
        "fps": 24,
        "crf": 23,
        "preset": "fast",
    },
    "final": {
        "width": 1920,
        "height": 1080,
        "fps": 24,
        "crf": 18,
        "preset": "medium",
    },
}


def get_render_profile(profile: str) -> dict[str, object]:
    try:
        return dict(RENDER_PROFILES[profile])
    except KeyError as exc:
        raise ValueError(f"Unknown render profile: {profile}") from exc


def apply_render_profile(
    project: VideoProject,
    profile: str,
) -> dict[str, object]:
    settings = get_render_profile(profile)
    for segment in project.segments:
        config = dict(segment.config)
        config["width"] = int(settings["width"])
        config["height"] = int(settings["height"])
        config["fps"] = int(settings["fps"])
        segment.config = config
    return settings


def _concat_file_line(path: Path) -> str:
    escaped = path.as_posix().replace("'", "'\\''")
    return f"file '{escaped}'\n"


def _safe_repo_path(repo_root: Path, relative: str) -> Path:
    candidate = (repo_root / relative).resolve()
    if repo_root not in candidate.parents and candidate != repo_root:
        raise ValueError(f"Path escapes repository: {relative}")
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def render_project(
    project_path: Path,
    output_dir: Path,
    segment_id: str | None = None,
    profile: str = "preview",
) -> dict[str, object]:
    repo_root = Path.cwd().resolve()
    project_path = project_path.resolve()

    if repo_root not in project_path.parents and project_path != repo_root:
        raise ValueError("Project file must live inside the repository")

    project = VideoProject.model_validate_json(
        project_path.read_text(encoding="utf-8")
    )

    if segment_id is not None:
        selected = [item for item in project.segments if item.id == segment_id]
        if not selected:
            raise ValueError(
                f"Segment {segment_id!r} was not found in project {project.project_id!r}"
            )
        project.segments = selected

    profile_settings = apply_render_profile(project, profile)

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    segments_dir = output_dir / "segments"
    audio_dir = output_dir / "audio"
    if segments_dir.exists():
        shutil.rmtree(segments_dir)
    if audio_dir.exists():
        shutil.rmtree(audio_dir)
    segments_dir.mkdir(parents=True)
    audio_dir.mkdir(parents=True)

    rendered: list[Path] = []

    for segment in project.segments:
        audio_path, audio_duration = synthesize_segment_narration(
            segment,
            project.audio,
            audio_dir,
        )
        if audio_duration and project.audio.fit_segments_to_narration:
            segment.duration_sec = max(
                segment.duration_sec,
                audio_duration + float(segment.config.get("tail_color", 1.5)),
            )

        raw_video = segments_dir / f"{segment.id}.raw.mp4"
        final_segment = segments_dir / f"{segment.id}.mp4"
        renderer = get_renderer(segment.renderer)
        renderer.render(segment, repo_root, raw_video)

        mux_narration(raw_video, audio_path, final_segment)
        if raw_video.exists() and raw_video != final_segment:
            raw_video.unlink()

        if not final_segment.is_file() or final_segment.stat().st_size == 0:
            raise RuntimeError(
                f"Renderer produced no output for segment {segment.id}"
            )
        rendered.append(final_segment)

    concat_list = output_dir / "concat.txt"
    concat_list.write_text(
        "".join(_concat_file_line(path) for path in rendered),
        encoding="utf-8",
    )

    final_path = output_dir / "final.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c:v", "libx264",
            "-preset", str(profile_settings["preset"]),
            "-crf", str(profile_settings["crf"]),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "160k",
            "-movflags", "+faststart",
            str(final_path),
        ],
        cwd=repo_root,
        check=True,
    )

    music_relative = project.audio.background_music_path
    if music_relative:
        music = _safe_repo_path(repo_root, music_relative)
        mixed = output_dir / "final-with-music.mp4"
        mix_background_music(
            final_path,
            music,
            mixed,
            project.audio.background_music_volume,
        )
        final_path.unlink()
        mixed.rename(final_path)

    captions_path = output_dir / "captions.srt"
    captions_created = write_srt(project, captions_path, timing_dir=audio_dir)

    manifest = {
        "project_id": project.project_id,
        "title": project.title,
        "segment_count": len(rendered),
        "segment_ids": [segment.id for segment in project.segments],
        "final_video": str(final_path),
        "captions": str(captions_path) if captions_created else None,
        "audio_provider": project.audio.provider,
        "voice": project.audio.voice,
        "profile": profile,
        "output": {
            "width": profile_settings["width"],
            "height": profile_settings["height"],
            "fps": profile_settings["fps"],
            "crf": profile_settings["crf"],
            "preset": profile_settings["preset"],
        },
    }
    (output_dir / "project-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return {
        "project_id": project.project_id,
        "final_video": str(final_path),
        "segments": len(rendered),
        "segment_id": segment_id,
        "captions": captions_created,
        "audio_provider": project.audio.provider,
        "profile": profile,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a YUGHO modular video project"
    )
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--segment-id")
    parser.add_argument(
        "--profile",
        choices=tuple(RENDER_PROFILES),
        default="preview",
    )
    args = parser.parse_args()

    result = render_project(
        args.project,
        args.output_dir,
        segment_id=args.segment_id,
        profile=args.profile,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
