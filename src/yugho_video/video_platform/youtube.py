from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from yugho_video.mcp_server.models import VideoProject

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def _credentials() -> Credentials:
    values = {
        "YOUTUBE_CLIENT_ID": os.getenv("YOUTUBE_CLIENT_ID"),
        "YOUTUBE_CLIENT_SECRET": os.getenv("YOUTUBE_CLIENT_SECRET"),
        "YOUTUBE_REFRESH_TOKEN": os.getenv("YOUTUBE_REFRESH_TOKEN"),
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise RuntimeError(
            f"Missing YouTube credentials: {', '.join(missing)}"
        )

    return Credentials(
        token=None,
        refresh_token=values["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=values["YOUTUBE_CLIENT_ID"],
        client_secret=values["YOUTUBE_CLIENT_SECRET"],
        scopes=SCOPES,
    )


def _validate_publish_at(value: str | None) -> None:
    if not value:
        return

    normalized = value.replace("Z", "+00:00")
    try:
        when = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            "publish_at must be an ISO-8601 timestamp, e.g. 2026-10-03T13:30:00Z"
        ) from exc

    if when.tzinfo is None:
        raise ValueError("publish_at must include a timezone")
    if when.astimezone(timezone.utc) <= datetime.now(timezone.utc):
        raise ValueError("publish_at must be in the future")


def upload_project(
    project: VideoProject,
    video_path: Path,
    thumbnail_path: Path | None,
    captions_path: Path | None,
) -> dict[str, str | bool]:
    if not project.publish.enabled:
        raise ValueError("Project publish.enabled must be true for YouTube upload")
    if not video_path.is_file() or video_path.stat().st_size == 0:
        raise FileNotFoundError(video_path)

    if project.publish.publish_at:
        if project.publish.privacy_status != "private":
            raise ValueError(
                "publish_at requires privacy_status='private'"
            )
        _validate_publish_at(project.publish.publish_at)

    service = build(
        "youtube",
        "v3",
        credentials=_credentials(),
        cache_discovery=False,
    )

    status: dict[str, str] = {
        "privacyStatus": project.publish.privacy_status,
    }

    if project.publish.publish_at:
        status["publishAt"] = project.publish.publish_at

    body = {
        "snippet": {
            "title": project.title,
            "description": project.description,
            "tags": project.tags,
            "categoryId": project.publish.category_id,
            "defaultLanguage": project.publish.language,
            "defaultAudioLanguage": project.publish.language,
        },
        "status": status,
    }

    request = service.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=8 * 1024 * 1024,
        ),
        notifySubscribers=False,
    )

    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response["id"]

    if thumbnail_path and thumbnail_path.exists():
        service.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(
                str(thumbnail_path),
                mimetype="image/jpeg",
            ),
        ).execute()

    captions_uploaded = False
    if captions_path and captions_path.exists() and captions_path.stat().st_size:
        service.captions().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "language": project.publish.language,
                    "name": "English",
                    "isDraft": False,
                }
            },
            media_body=MediaFileUpload(
                str(captions_path),
                mimetype="application/x-subrip",
            ),
        ).execute()
        captions_uploaded = True

    return {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "scheduled": bool(project.publish.publish_at),
        "privacy_status": project.publish.privacy_status,
        "thumbnail_uploaded": bool(
            thumbnail_path and thumbnail_path.exists()
        ),
        "captions_uploaded": captions_uploaded,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload a YUGHO project to YouTube")
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--thumbnail", type=Path)
    parser.add_argument("--captions", type=Path)
    args = parser.parse_args()

    project = VideoProject.model_validate_json(
        args.project.read_text(encoding="utf-8")
    )
    result = upload_project(
        project,
        args.video,
        args.thumbnail,
        args.captions,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
