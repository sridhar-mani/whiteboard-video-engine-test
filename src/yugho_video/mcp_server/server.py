from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from .config import Settings
from .github import GitHubClient
from .models import VideoProject
from .services import VideoControlService


settings = Settings.from_env()
github = GitHubClient(settings)
service = VideoControlService(github)

mcp = FastMCP(
    settings.mcp_name,
    instructions=(
        "Control the YUGHO modular video production pipeline. "
        "Create projects, start renders, inspect render status, and request "
        "YouTube publishing. The server is a control plane; rendering happens "
        "in GitHub Actions."
    ),
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
async def create_video_project(project: VideoProject) -> dict[str, object]:
    """Create or replace a YUGHO video project in the GitHub project store."""
    return await service.create_project(project)


@mcp.tool()
async def get_video_project(project_id: str) -> dict[str, object]:
    """Read and validate a YUGHO project from GitHub."""
    project = await service.get_project(project_id)
    return project.model_dump(mode="json")


@mcp.tool()
async def start_video_render(
    project_id: str,
    profile: str = "preview",
    publish: bool = False,
) -> dict[str, object]:
    """Dispatch a GitHub Actions render for a project."""
    if profile not in {"smoke", "preview", "final"}:
        raise ValueError("profile must be smoke, preview, or final")
    return await service.start_render(project_id, profile, publish)


@mcp.tool()
async def get_video_status(project_id: str) -> dict[str, object]:
    """Return the latest GitHub Actions state for a project render."""
    return await service.status(project_id)


@mcp.tool()
async def publish_video(project_id: str, profile: str = "final") -> dict[str, object]:
    """Enable the project's YouTube publish setting and dispatch a final publish job."""
    if profile not in {"preview", "final"}:
        raise ValueError("profile must be preview or final")
    return await service.start_render(project_id, profile, True)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
    )
