from __future__ import annotations

import os
from typing import Any

import jwt
from pydantic import AnyHttpUrl

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings


class JWTTokenVerifier(TokenVerifier):
    def __init__(
        self,
        issuer: str,
        audience: str,
        jwks_url: str,
        algorithms: tuple[str, ...] = ("RS256",),
    ) -> None:
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.jwks_url = jwks_url
        self.algorithms = algorithms
        self.jwks = jwt.PyJWKClient(jwks_url)

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            signing_key = self.jwks.get_signing_key_from_jwt(token)
            claims: dict[str, Any] = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(self.algorithms),
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iss", "sub"]},
            )
        except Exception:
            return None

        raw_scopes = claims.get("scope", claims.get("scp", []))
        if isinstance(raw_scopes, str):
            scopes = [item for item in raw_scopes.split() if item]
        elif isinstance(raw_scopes, list):
            scopes = [str(item) for item in raw_scopes]
        else:
            scopes = []

        return AccessToken(
            token=token,
            client_id=str(claims.get("azp", claims.get("client_id", "chatgpt"))),
            scopes=scopes,
            expires_at=int(claims["exp"]),
            resource=self.audience,
            subject=str(claims["sub"]),
            claims=claims,
        )


def auth_configured() -> bool:
    required = (
        os.getenv("MCP_AUTH_ISSUER"),
        os.getenv("MCP_AUTH_AUDIENCE"),
        os.getenv("MCP_AUTH_JWKS_URL"),
        os.getenv("MCP_PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL"),
    )
    return all(value and value.strip() for value in required)


def build_auth_settings() -> tuple[JWTTokenVerifier, AuthSettings] | None:
    if not auth_configured():
        return None

    issuer = os.environ["MCP_AUTH_ISSUER"].strip().rstrip("/")
    audience = os.environ["MCP_AUTH_AUDIENCE"].strip()
    jwks_url = os.environ["MCP_AUTH_JWKS_URL"].strip()
    public_url = (
        os.getenv("MCP_PUBLIC_URL")
        or os.getenv("RENDER_EXTERNAL_URL")
        or ""
    ).strip().rstrip("/")
    if not public_url:
        raise RuntimeError(
            "MCP public URL is missing. Set MCP_PUBLIC_URL or deploy on Render."
        )
    public_url = f"{public_url}/mcp" if not public_url.endswith("/mcp") else public_url
    required_scopes = [
        item.strip()
        for item in os.getenv("MCP_AUTH_REQUIRED_SCOPES", "mcp:write").split()
        if item.strip()
    ]

    verifier = JWTTokenVerifier(
        issuer=issuer,
        audience=audience,
        jwks_url=jwks_url,
    )
    settings = AuthSettings(
        issuer_url=AnyHttpUrl(issuer),
        resource_server_url=AnyHttpUrl(public_url),
        required_scopes=required_scopes,
        validate_token_resource=False,
    )
    return verifier, settings
