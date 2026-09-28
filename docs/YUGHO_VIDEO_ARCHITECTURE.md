# YUGHO Video Architecture

## Runtime boundaries

1. Upstream renderer: src/whiteboard_skill/ is the forked renderer package.
2. YUGHO engine adapters: src/yugho_video/engines/ provides stable renderer interfaces.
3. Production runtime: src/yugho_video/video_platform/ renders segments, audio, captions, composition and publishing.
4. MCP control plane: src/yugho_video/mcp_server/ exposes ChatGPT-facing tools.
5. Execution backend: .github/workflows/yugho-video-engine.yml runs production jobs on GitHub Actions.
6. Publishing: YouTube Data API runs inside the same ephemeral GitHub Actions job.

## Segment architecture

ChatGPT chooses semantic segment types and renderer backends. The entire project is rendered in one Actions job, while individual segments can be rendered independently for preview iteration.

Example:

hook -> whiteboard
problem -> whiteboard
data_explainer -> future motion-canvas
math -> future manim
character -> whiteboard
cta -> future motion-canvas

Adding a renderer means implementing one adapter and registering it. The MCP contract does not change.

## Intended ChatGPT flow

Create a video about X
  -> research/script/story plan handled by ChatGPT
  -> create_video_project
  -> start_video_render or publish_video
  -> GitHub Actions
  -> get_video_status
  -> final YouTube result

## Authentication

The MCP is an OAuth 2.1 resource server. It validates access tokens from an external OAuth/OIDC authorization server using JWKS.

Required runtime variables:

MCP_PUBLIC_URL
MCP_AUTH_ISSUER
MCP_AUTH_AUDIENCE
MCP_AUTH_JWKS_URL
MCP_AUTH_REQUIRED_SCOPES

The repository does not own user passwords or implement an end-user login page.

## Secrets

GitHub token lives in the Render environment.
YouTube OAuth credentials live only in GitHub Actions repository secrets.
OAuth provider client configuration is handled by the provider/ChatGPT app configuration.
No secret belongs in git.
