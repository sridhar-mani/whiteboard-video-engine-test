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


## Render deployment

The repository includes a Render Blueprint at `render.yaml`.

Create a Render Web Service from this repository/Blueprint with:

- Runtime: Python
- Plan: Free
- Build: `pip install -e '.[dev]'`
- Start: `yugho-video-mcp`
- Health check: `/health`

Render exposes `RENDER_EXTERNAL_URL` at runtime. The server uses it automatically to derive the protected MCP resource URL as `<external-url>/mcp`, so `MCP_PUBLIC_URL` is optional on Render. Render also supplies the hostname used by transport security.

Required Render environment values:

```
GITHUB_TOKEN=<GitHub token with repository Contents write + Actions write>
GITHUB_REPO=sridhar-mani/whiteboard-video-engine-test
GITHUB_WORKFLOW=yugho-video-engine.yml
GITHUB_REF=main

MCP_AUTH_ISSUER=https://YOUR_TENANT.auth0.com/
MCP_AUTH_AUDIENCE=https://yugho-mcp.example
MCP_AUTH_JWKS_URL=https://YOUR_TENANT.auth0.com/.well-known/jwks.json
MCP_AUTH_REQUIRED_SCOPES=mcp:write
```

`GITHUB_TOKEN`, the OAuth issuer details, and all other credentials are Render secrets; do not commit them.

### Auth0 example

In Auth0, create an API representing the YUGHO MCP resource. Use an absolute API identifier as the audience and create a custom API scope named `mcp:write`. Auth0 documents the API identifier as the token audience and supports custom API scopes. Configure the API to use RS256 so the resource server can validate the JWT against Auth0's signing keys.

For ChatGPT, create/register the OAuth application/client in the same provider and allow the callback URL presented by ChatGPT during custom-app setup. The exact callback URL belongs to the ChatGPT app configuration, not the YUGHO server.

### ChatGPT connection

Use the remote MCP endpoint:

```
https://YOUR_RENDER_HOST/mcp
```

Select OAuth during custom-app setup. The server exposes OAuth protected-resource metadata through the MCP SDK when OAuth is configured, so ChatGPT can discover the authorization server from the resource endpoint.

Do not set `MCP_ALLOW_ANONYMOUS=true` on Render.

