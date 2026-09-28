from __future__ import annotations

import os
from urllib.parse import urlparse

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from .auth import build_auth_settings
from .capabilities import get_full_context, recommend_pipeline
from .config import Settings
from .github import GitHubClient
from .models import VideoProject
from .render_catalog import list_renderers, list_segment_kinds
from .services import VideoControlService
from .voices import list_edge_voices


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
        "YUGHO is a modular, ChatGPT-driven video production system. "
        "Before planning a complex video, inspect get_video_system_context. "
        "Use list_available_renderers and list_video_segment_kinds to choose a "
        "segment plan. Use create_video_project, render_segment_preview, "
        "start_video_render, get_video_status and publish_video to execute it. "
        "The MCP abstracts the execution backend; GitHub Actions currently performs "
        "the heavy rendering and YouTube publishing."
    ),
}

if auth_pair is not None:
    verifier, auth_settings = auth_pair
    server_kwargs["token_verifier"] = verifier
    server_kwargs["auth"] = auth_settings

mcp = MCPServer(settings.mcp_name, **server_kwargs)


@mcp.tool()
async def get_video_system_context() -> dict[str, object]:
    """Return the complete machine-readable capability map for planning YUGHO videos."""
    return get_full_context()


@mcp.tool()
async def recommend_video_pipeline(
    content_type: str,
    visual_goal: str,
    audio_goal: str = "single_narrator",
) -> dict[str, object]:
    """Recommend a renderer/editing/audio stack from the current capability catalog."""
    return recommend_pipeline(content_type, visual_goal, audio_goal)


@mcp.tool()
async def list_available_renderers() -> list[dict[str, object]]:
    """List renderer backends and the kinds of content each backend is suited for."""
    return list_renderers()


@mcp.tool()
async def list_video_segment_kinds() -> list[dict[str, str]]:
    """List semantic segment types that ChatGPT can compose into a video."""
    return list_segment_kinds()


@mcp.tool()
async def list_audio_voices(locale: str | None = None) -> list[dict[str, str]]:
    """List currently available Edge TTS voices, optionally filtered by locale."""
    return await list_edge_voices(locale)


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
        "duration_sec": sum(segment.duration_sec for segment in project.segments),
        "publish_enabled": project.publish.enabled,
        "dialogue_segments": sum(bool(segment.dialogue) for segment in project.segments),
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


def _transport_security() -> TransportSecuritySettings | None:
    public_url = os.getenv("MCP_PUBLIC_URL", "").strip()
    if not public_url:
        return None
    hostname = urlparse(public_url).hostname
    if not hostname:
        raise RuntimeError("MCP_PUBLIC_URL must contain a valid hostname")
    return TransportSecuritySettings(
        allowed_hosts=[hostname, f"{hostname}:*"],
        allowed_origins=[],
    )


def main() -> None:
    port = int(os.getenv("PORT", "10000"))
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        stateless_http=True,
        json_response=True,
        transport_security=_transport_security(),
    )


if __name__ == "__main__":
    main()
