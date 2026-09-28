from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from yugho_video.mcp_server.models import VideoProject
from yugho_video.video_platform.captions import write_srt
from yugho_video.video_platform.renderers import get_renderer


def _concat_file_line(path: Path) -> str:
    escaped = path.as_posix().replace("'", "'\\''")
    return f"file '{escaped}'\n"


def render_project(project_path: Path, output_dir: Path) -> dict[str, object]:
    repo_root = Path.cwd().resolve()
    project_path = project_path.resolve()

    if repo_root not in project_path.parents and project_path != repo_root:
        raise ValueError("Project file must live inside the repository")

    project = VideoProject.model_validate_json(
        project_path.read_text(encoding="utf-8")
    )

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    segments_dir = output_dir / "segments"
    if segments_dir.exists():
        shutil.rmtree(segments_dir)
    segments_dir.mkdir(parents=True)

    rendered: list[Path] = []

    for segment in project.segments:
        output = segments_dir / f"{segment.id}.mp4"
        renderer = get_renderer(segment.renderer)
        renderer.render(segment, repo_root, output)

        if not output.is_file() or output.stat().st_size == 0:
            raise RuntimeError(
                f"Renderer produced no output for segment {segment.id}"
            )
        rendered.append(output)

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
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(final_path),
        ],
        cwd=repo_root,
        check=True,
    )

    captions_path = output_dir / "captions.srt"
    captions_created = write_srt(project, captions_path)

    manifest = {
        "project_id": project.project_id,
        "title": project.title,
        "segments": len(rendered),
        "final_video": str(final_path),
        "captions": str(captions_path) if captions_created else None,
    }
    (output_dir / "project-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "project_id": project.project_id,
        "final_video": str(final_path),
        "segments": len(rendered),
        "captions": captions_created,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a YUGHO modular video project"
    )
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    result = render_project(args.project, args.output_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
