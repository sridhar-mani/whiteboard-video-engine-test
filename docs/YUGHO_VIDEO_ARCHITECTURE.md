# YUGHO Video Architecture

The repository has three layers.

## 1. Upstream renderer package

`src/whiteboard_skill/` is the forked whiteboard engine. It remains intact so upstream updates can be incorporated without coupling the rest of the platform to its internal files.

## 2. YUGHO renderer adapters

`src/yugho_video/engines/` contains stable adapters for individual rendering engines.

The whiteboard adapter calls the upstream Python renderer directly. Future adapters can target Motion Canvas, Manim, HandAnim, or other engines without changing the project schema or MCP tools.

## 3. Control and production layers

- `src/yugho_video/mcp_server/` exposes stable ChatGPT-facing MCP tools.
- `src/yugho_video/video_platform/` validates projects, renders segments, composes the master video, generates captions, and publishes to YouTube.
- `.github/workflows/yugho-video-engine.yml` provides the current execution backend.

Render hosts only the lightweight MCP control plane. GitHub Actions performs the CPU-heavy work.

The project schema deliberately chooses a renderer per segment:

```text
hook            -> motion-canvas
whiteboard      -> whiteboard
data_explainer  -> motion-canvas
character       -> whiteboard
math            -> manim
cta             -> motion-canvas
```

This makes the rendering backend replaceable without changing the ChatGPT tool interface.

## Current state

Only the whiteboard adapter is implemented initially. Adding another engine means:

1. implement a renderer adapter;
2. register it in `video_platform/renderers.py`;
3. add focused tests;
4. add any engine-specific dependencies to the GitHub workflow.

YouTube credentials are never stored in the repository.
