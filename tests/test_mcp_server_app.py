import asyncio
import importlib

import httpx


def test_mcp_health_endpoint_is_public_and_reports_ready(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_REPO", "owner/repo")
    monkeypatch.setenv("MCP_PUBLIC_URL", "https://test.example/mcp")
    monkeypatch.setenv("MCP_AUTH_ISSUER", "https://issuer.example/")
    monkeypatch.setenv("MCP_AUTH_AUDIENCE", "yugho-mcp")
    monkeypatch.setenv(
        "MCP_AUTH_JWKS_URL",
        "https://issuer.example/.well-known/jwks.json",
    )
    monkeypatch.delenv("MCP_ALLOW_ANONYMOUS", raising=False)

    server_module = importlib.import_module("yugho_video.mcp_server.server")
    server_module = importlib.reload(server_module)

    async def request() -> None:
        transport = httpx.ASGITransport(app=server_module.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="https://test.example",
        ) as client:
            response = await client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "YUGHO Video MCP"}

    asyncio.run(request())
