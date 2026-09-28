import json
from pathlib import Path

import pytest

from yugho_video.mcp_server.services import VideoControlService


class FakeGitHub:
    async def workflow_runs(self):
        return [
            {
                "id": 42,
                "run_number": 7,
                "name": "YUGHO Video Engine",
                "display_title": "YUGHO | projects/demo-project/project.json | preview",
                "status": "in_progress",
                "conclusion": None,
                "html_url": "https://github.com/example/actions/runs/42",
                "created_at": "2026-09-28T10:00:00Z",
                "updated_at": "2026-09-28T10:01:00Z",
            }
        ]

    async def read_optional_text_file(self, path: str):
        if path == "projects/demo-project/result.json":
            return json.dumps({"state": "succeeded", "project_id": "demo-project"})
        raise AssertionError(path)


@pytest.mark.asyncio
async def test_status_matches_custom_workflow_run_name() -> None:
    service = VideoControlService(FakeGitHub())

    result = await service.status("demo-project")

    assert result["run_id"] == 42
    assert result["state"] == "in_progress"
    assert result["html_url"].endswith("/42")
