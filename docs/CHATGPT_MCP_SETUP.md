# ChatGPT MCP OAuth setup

The server implements the MCP resource-server half of OAuth. A separate OAuth/OIDC provider must issue the access token.

## 1. Create an OAuth/OIDC API

Use a provider with standards-compliant authorization-server discovery and JWKS metadata, such as Auth0, Okta or Microsoft Entra ID.

Create an API/resource for the MCP endpoint and a scope such as mcp:write.

The access token needs iss, sub, aud, exp and scope/scp claims.

## 2. Configure Render

Set:

MCP_PUBLIC_URL=https://YOUR_RENDER_HOST/mcp
MCP_AUTH_ISSUER=https://YOUR_ISSUER
MCP_AUTH_AUDIENCE=YOUR_API_AUDIENCE
MCP_AUTH_JWKS_URL=https://YOUR_ISSUER/.well-known/jwks.json
MCP_AUTH_REQUIRED_SCOPES=mcp:write

Do not set MCP_ALLOW_ANONYMOUS=true in production.

## 3. Connect ChatGPT

In a ChatGPT workspace that supports full custom MCP apps, create a custom app in Developer Mode, point it to the MCP URL, select OAuth, complete provider authorization, scan the tools, and test a preview render before enabling publication.

ChatGPT custom-app availability and write-action support are controlled by the current workspace plan and administrator settings.

## 4. YouTube authentication

ChatGPT OAuth protects the MCP connection. It does not authenticate your YouTube channel.

Create Google OAuth credentials for the YouTube Data API and store these only as GitHub Actions secrets:

YOUTUBE_CLIENT_ID
YOUTUBE_CLIENT_SECRET
YOUTUBE_REFRESH_TOKEN

## 5. Local development

For local MCP testing only:

MCP_ALLOW_ANONYMOUS=true

Never expose an anonymous write-enabled MCP server publicly.
