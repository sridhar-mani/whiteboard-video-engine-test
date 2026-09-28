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

    @staticmethod
    def result_path(project_id: str) -> str:
        return f"projects/{project_id}/result.json"

    async def create_project(self, project: VideoProject) -> dict[str, Any]:
        path = self.project_path(project.project_id)
        content = (
            json.dumps(
                project.model_dump(mode="json"),
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
        result = await self.github.put_json_file(
            path,
            content,
            f"video: create project {project.project_id}",
        )
        return {
            "project_id": project.project_id,
            "project_path": path,
            "commit_sha": result["commit"]["sha"],
            "state": "created",
        }

    async def get_project(self, project_id: str) -> VideoProject:
        content = await self.github.read_text_file(
            self.project_path(project_id)
        )
        return VideoProject.model_validate_json(content)

    async def start_render(
        self,
        project_id: str,
        profile: str,
        publish: bool,
        segment_id: str | None = None,
    ) -> dict[str, Any]:
        project = await self.get_project(project_id)
        if segment_id and segment_id not in {
            segment.id for segment in project.segments
        }:
            raise ValueError(
                f"Segment {segment_id!r} does not exist in {project_id!r}"
            )

        path = self.project_path(project_id)

        if publish and not project.publish.enabled:
            project.publish.enabled = True
            content = (
                json.dumps(
                    project.model_dump(mode="json"),
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n"
            )
            await self.github.put_json_file(
                path,
                content,
                f"video: enable publish for {project_id}",
            )

        await self.github.dispatch_workflow(
            path,
            profile,
            publish,
            segment_id=segment_id,
        )

        return {
            "project_id": project_id,
            "project_path": path,
            "profile": profile,
            "publish": publish,
            "segment_id": segment_id,
            "state": "dispatched",
        }

    async def status(self, project_id: str) -> dict[str, Any]:
        path = self.project_path(project_id)
        prefix = f"YUGHO | {path} |"
        runs = await self.github.workflow_runs()
        matches = [
            run
            for run in runs
            if str(
                run.get("display_title")
                or run.get("run_name")
                or run.get("name", "")
            ).startswith(prefix)
        ]

        result_payload: dict[str, Any] | None = None
        result_raw = await self.github.read_optional_text_file(
            self.result_path(project_id)
        )
        if result_raw:
            try:
                result_payload = json.loads(result_raw)
            except json.JSONDecodeError:
                result_payload = None

        if not matches:
            return {
                "project_id": project_id,
                "state": result_payload.get("state", "not_started")
                if result_payload
                else "not_started",
                "project_path": path,
                "result": result_payload,
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
            "result": result_payload,
        }
