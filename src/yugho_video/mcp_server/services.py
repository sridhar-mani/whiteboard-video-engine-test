from __future__ import annotations

import json
from typing import Any

from .github import GitHubClient
from .models import VideoProject


class VideoControlService:
    def __init__(self, github: GitHubClient) -> None:
        self.github = github

    @staticmethod
    def project_path(project_id: str) -> str:
        return f"projects/{project_id}/project.json"

    async def create_project(self, project: VideoProject) -> dict[str, Any]:
        path = self.project_path(project.project_id)
        content = json.dumps(
            project.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
        ) + "\n"
        result = await self.github.put_json_file(
            path,
            content,
            f"video: create project {project.project_id}",
        )
        return {
            "project_id": project.project_id,
            "project_path": path,
            "commit_sha": result["commit"]["sha"],
        }

    async def get_project(self, project_id: str) -> VideoProject:
        content = await self.github.read_text_file(self.project_path(project_id))
        return VideoProject.model_validate_json(content)

    async def start_render(
        self,
        project_id: str,
        profile: str,
        publish: bool,
    ) -> dict[str, Any]:
        project = await self.get_project(project_id)
        path = self.project_path(project_id)

        if publish and not project.publish.enabled:
            project.publish.enabled = True
            content = json.dumps(
                project.model_dump(mode="json"),
                indent=2,
                ensure_ascii=False,
            ) + "\n"
            await self.github.put_json_file(
                path,
                content,
                f"video: enable publish for {project_id}",
            )

        await self.github.dispatch_workflow(path, profile, publish)
        return {
            "project_id": project_id,
            "project_path": path,
            "profile": profile,
            "publish": publish,
            "state": "dispatched",
        }

    async def status(self, project_id: str) -> dict[str, Any]:
        path = self.project_path(project_id)
        prefix = f"YUGHO | {path} |"
        runs = await self.github.workflow_runs()
        matches = [
            run for run in runs if str(run.get("name", "")).startswith(prefix)
        ]
        if not matches:
            return {
                "project_id": project_id,
                "state": "not_started",
                "project_path": path,
            }

        run = sorted(
            matches,
            key=lambda item: item.get("created_at", ""),
            reverse=True,
        )[0]
        return {
            "project_id": project_id,
            "project_path": path,
            "run_id": run.get("id"),
            "run_number": run.get("run_number"),
            "state": run.get("status"),
            "conclusion": run.get("conclusion"),
            "html_url": run.get("html_url"),
            "created_at": run.get("created_at"),
            "updated_at": run.get("updated_at"),
        }
