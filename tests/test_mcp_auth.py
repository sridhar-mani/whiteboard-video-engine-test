from yugho_video.mcp_server.auth import build_auth_settings


def test_auth_derives_render_mcp_url_from_render_external_url(monkeypatch) -> None:
    monkeypatch.delenv("MCP_PUBLIC_URL", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://yugho-video-mcp.onrender.com")
    monkeypatch.setenv("MCP_AUTH_ISSUER", "https://example.auth0.com/")
    monkeypatch.setenv("MCP_AUTH_AUDIENCE", "https://yugho-mcp.example")
    monkeypatch.setenv(
        "MCP_AUTH_JWKS_URL",
        "https://example.auth0.com/.well-known/jwks.json",
    )

    pair = build_auth_settings()

    assert pair is not None
    _verifier, auth_settings = pair
    assert str(auth_settings.resource_server_url).rstrip("/") == (
        "https://yugho-video-mcp.onrender.com/mcp"
    )
