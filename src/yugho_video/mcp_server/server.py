from __future__ import annotations

import os

from mcp.server.mcpserver import MCPServer

from .auth import build_auth_settings
from .config import Settings
from .github import GitHubClient
from .models import VideoProject
from .render_catalog import list_renderers, list_segment_kinds
from .services import VideoControlService


settings = Settings.from_env()
github = GitHubClient(settings)
service = VideoControlService(github)

auth_pair = build_auth_settings()
allow_anonymous = os.getenv("MCP_ALLOW_ANONYMOUS", "").lower() == "true"

if auth_pair is None and not allow_anonymous:
    raise RuntimeError(
        "MCP OAuth is not configured. Set MCP_AUTH_ISSUER, MCP_AUTH_AUDIENCE, "
        "MCP_AUTH_JWKS_URL and MCP_PUBLIC_URL, or set MCP_ALLOW_ANONYMOUS=true "
        "only for local development."
    )

server_kwargs = {
    "instructions": (
        "Control the YUGHO modular video production pipeline. "
        "ChatGPT chooses the topic, story structure, segment kinds, and renderer. "
        "The MCP stores validated projects, dispatches GitHub Actions, reports status, "
        "and can publish the completed video to YouTube."
    ),
}

if auth_pair is not None:
    verifier, auth_settings = auth_pair
    server_kwargs["token_verifier"] = verifier
    server_kwargs["auth"] = auth_settings

mcp = MCPServer(settings.mcp_name, **server_kwargs)


@mcp.tool()
async def list_available_renderers() -> list[dict[str, object]]:
    """List renderer backends and the kinds of content each backend is suited for."""
    return list_renderers()


@mcp.tool()
async def list_video_segment_kinds() -> list[dict[str, str]]:
    """List semantic segment types that ChatGPT can compose into a video."""
    return list_segment_kinds()


@mcp.tool()
async def create_video_project(project: VideoProject) -> dict[str, object]:
    """Create or replace a validated YUGHO video project in GitHub."""
    return await service.create_project(project)


@mcp.tool()
async def get_video_project(project_id: str) -> dict[str, object]:
    """Read and validate a YUGHO project from GitHub."""
    project = await service.get_project(project_id)
    return project.model_dump(mode="json")


@mcp.tool()
async def validate_video_project(project: VideoProject) -> dict[str, object]:
    """Validate a project before writing it to GitHub."""
    return {
        "valid": True,
        "project_id": project.project_id,
        "segments": len(project.segments),
        "renderers": sorted({segment.renderer for segment in project.segments}),
        "duration_sec": sum(
            segment.duration_sec for segment in project.segments
        ),
        "publish_enabled": project.publish.enabled,
    }


@mcp.tool()
async def start_video_render(
    project_id: str,
    profile: str = "preview",
    publish: bool = False,
    segment_id: str | None = None,
) -> dict[str, object]:
    """Dispatch a GitHub Actions render for the complete project or one segment."""
    if profile not in {"smoke", "preview", "final"}:
        raise ValueError("profile must be smoke, preview, or final")
    if segment_id and publish:
        raise ValueError("A segment preview cannot publish to YouTube.")
    return await service.start_render(
        project_id,
        profile,
        publish,
        segment_id=segment_id,
    )


@mcp.tool()
async def render_segment_preview(
    project_id: str,
    segment_id: str,
) -> dict[str, object]:
    """Render one segment as a standalone preview artifact."""
    return await service.start_render(
        project_id,
        "preview",
        False,
        segment_id=segment_id,
    )


@mcp.tool()
async def get_video_status(project_id: str) -> dict[str, object]:
    """Return the latest render/publish state and YouTube result for a project."""
    return await service.status(project_id)


@mcp.tool()
async def publish_video(
    project_id: str,
    profile: str = "final",
) -> dict[str, object]:
    """Enable the project's YouTube publication and dispatch a final render/upload."""
    if profile not in {"preview", "final"}:
        raise ValueError("profile must be preview or final")
    return await service.start_render(project_id, profile, True)


def main() -> None:
    port = int(os.getenv("PORT", "10000"))
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        stateless_http=True,
        json_response=True,
    )


if __name__ == "__main__":
    main()
