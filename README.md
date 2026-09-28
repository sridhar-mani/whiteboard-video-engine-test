# YUGHO Video Platform

A modular, ChatGPT-driven video production system.

Architecture:

ChatGPT -> YUGHO Video MCP (Render) -> GitHub Actions -> FFmpeg/renderers -> YouTube

Render hosts only the lightweight MCP control plane. GitHub Actions is the compute/runtime plane.

## Modular video model

A project is a sequence of semantic segments. ChatGPT can choose the visual treatment of each segment.

Segment kinds include: hook, intro, whiteboard_explanation, animated_doodle, diagram, data_explainer, story, quote, transition, cta, and outro.

Each segment carries its renderer, duration, narration, input asset and renderer-specific configuration.

## Current rendering features

- 1920x1080 final output
- full-project or single-segment preview rendering
- progressive whiteboard stroke/hand animation
- optional Edge TTS narration
- optional background music
- automatic SRT captions
- automatic thumbnail extraction
- FFmpeg final composition
- YouTube resumable upload
- YouTube thumbnail upload
- YouTube caption upload
- private/unlisted/public metadata
- scheduled publication metadata
- durable per-project result state

## MCP tools

list_available_renderers
list_video_segment_kinds
create_video_project
get_video_project
validate_video_project
start_video_render
render_segment_preview
get_video_status
publish_video

## Render deployment

render.yaml deploys the MCP control plane as a Render Web Service.

Required runtime variables:

GITHUB_TOKEN
GITHUB_REPO=sridhar-mani/whiteboard-video-engine-test
GITHUB_WORKFLOW=yugho-video-engine.yml
GITHUB_REF=main
MCP_PUBLIC_URL=https://your-render-host/mcp
MCP_AUTH_ISSUER=https://your-oidc-provider
MCP_AUTH_AUDIENCE=your-api-audience
MCP_AUTH_JWKS_URL=https://your-oidc-provider/.well-known/jwks.json
MCP_AUTH_REQUIRED_SCOPES=mcp:write

OAuth is implemented as an MCP resource-server verifier. The actual OAuth authorization server is external; see docs/CHATGPT_MCP_SETUP.md.

For local development only, MCP_ALLOW_ANONYMOUS=true can bypass OAuth. Never use that on a public write-enabled deployment.

## YouTube secrets

Store these as GitHub Actions repository secrets, never in git:

YOUTUBE_CLIENT_ID
YOUTUBE_CLIENT_SECRET
YOUTUBE_REFRESH_TOKEN

The GitHub worker exchanges the refresh token for an access token and performs the upload.

## Development

python -m pip install -e '.[dev,youtube,tts]'

MCP_ALLOW_ANONYMOUS=true GITHUB_TOKEN=... GITHUB_REPO=sridhar-mani/whiteboard-video-engine-test python -m yugho_video.mcp_server.server

HTTP MCP endpoint: http://127.0.0.1:10000/mcp

## License

The upstream whiteboard renderer remains under its original license. See LICENSE and THIRD_PARTY_NOTICES.md.
