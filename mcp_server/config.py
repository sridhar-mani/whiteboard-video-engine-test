from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    github_token: str
    github_repo: str
    github_workflow: str = "yugho-video-engine.yml"
    github_ref: str = "main"
    github_api_base: str = "https://api.github.com"
    mcp_name: str = "YUGHO Video MCP"

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("GITHUB_TOKEN", "").strip()
        repo = os.getenv("GITHUB_REPO", "").strip()
        if not token:
            raise RuntimeError("GITHUB_TOKEN is required")
        if not repo or "/" not in repo:
            raise RuntimeError("GITHUB_REPO must be in owner/name form")
        return cls(
            github_token=token,
            github_repo=repo,
            github_workflow=os.getenv("GITHUB_WORKFLOW", cls.github_workflow),
            github_ref=os.getenv("GITHUB_REF", cls.github_ref),
            github_api_base=os.getenv("GITHUB_API_BASE", cls.github_api_base).rstrip("/"),
            mcp_name=os.getenv("MCP_NAME", cls.mcp_name),
        )
