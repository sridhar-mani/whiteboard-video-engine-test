from __future__ import annotations

import base64
from typing import Any

import httpx

from .config import Settings


class GitHubAPIError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, settings: Settings, timeout: float = 30.0) -> None:
        self.settings = settings
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.settings.github_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self.settings.github_api_base}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(method, url, headers=self._headers(), **kwargs)
        if response.status_code >= 400:
            raise GitHubAPIError(f"GitHub API {response.status_code}: {response.text[:2000]}")
        return response

    async def put_json_file(self, path: str, content: str, message: str) -> dict[str, Any]:
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        get_path = f"/repos/{self.settings.github_repo}/contents/{path}"
        existing_sha: str | None = None
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                get_path,
                headers=self._headers(),
                params={"ref": self.settings.github_ref},
            )
            if response.status_code == 200:
                existing_sha = response.json().get("sha")
            elif response.status_code != 404:
                raise GitHubAPIError(
                    f"GitHub API {response.status_code}: {response.text[:2000]}"
                )

            payload: dict[str, Any] = {
                "message": message,
                "content": encoded,
                "branch": self.settings.github_ref,
            }
            if existing_sha:
                payload["sha"] = existing_sha

            response = await client.put(get_path, headers=self._headers(), json=payload)

        if response.status_code >= 400:
            raise GitHubAPIError(f"GitHub API {response.status_code}: {response.text[:2000]}")
        return response.json()

    async def read_text_file(self, path: str) -> str:
        response = await self._request(
            "GET",
            f"/repos/{self.settings.github_repo}/contents/{path}",
            params={"ref": self.settings.github_ref},
        )
        payload = response.json()
        encoded = payload.get("content", "")
        return base64.b64decode(encoded.replace("\n", "")).decode("utf-8")

    async def dispatch_workflow(self, project_path: str, profile: str, publish: bool) -> None:
        path = (
            f"/repos/{self.settings.github_repo}/actions/workflows/"
            f"{self.settings.github_workflow}/dispatches"
        )
        response = await self._request(
            "POST",
            path,
            json={
                "ref": self.settings.github_ref,
                "inputs": {
                    "project_path": project_path,
                    "profile": profile,
                    "publish": "true" if publish else "false",
                },
            },
        )
        if response.status_code != 204:
            raise GitHubAPIError(
                f"Unexpected workflow dispatch response: {response.status_code}"
            )

    async def workflow_runs(self, per_page: int = 20) -> list[dict[str, Any]]:
        response = await self._request(
            "GET",
            f"/repos/{self.settings.github_repo}/actions/workflows/"
            f"{self.settings.github_workflow}/runs",
            params={"per_page": per_page},
        )
        return response.json().get("workflow_runs", [])
