from __future__ import annotations

from typing import Any

CAPABILITY_CONTEXT: dict[str, Any] = {
    "system": {
        "name": "YUGHO Modular Video Platform",
        "version": "0.1.0",
        "role": "ChatGPT-facing video production control plane plus GitHub Actions execution backend",
        "output": "1920x1080 MP4, captions, thumbnail, optional YouTube publication",
    },
    "execution": {
        "control_plane": "Render web service",
        "compute_plane": "GitHub Actions public repository standard runner",
        "current_render_backend": "whiteboard",
        "future_backend_selection": "per segment",
        "storage": "Git repository project manifests + ephemeral Actions workspace",
    },
    "segment_kinds": {
        "hook": "Fast attention-grabbing opening.",
        "intro": "Branded introduction or premise setup.",
        "whiteboard_explanation": "Progressive hand-drawn explanation.",
        "animated_doodle": "Character-driven hand-drawn story beat.",
        "dialogue": "Multi-speaker conversation or debate.",
        "diagram": "Hand-drawn or vector systems/flow diagram.",
        "data_explainer": "Charts, comparisons, statistics, and numerical explanation.",
        "story": "Narrative sequence.",
        "quote": "Quote or statement emphasis.",
        "broll": "Future media/B-roll backend.",
        "transition": "Visual bridge.",
        "cta": "Call-to-action.",
        "outro": "Closing/branded ending.",
    },
    "renderers": {
        "whiteboard": {
            "status": "implemented",
            "library": "upstream whiteboard-video-engine fork wrapped as a YUGHO adapter",
            "strengths": [
                "progressive stroke reveal",
                "moving hand",
                "hand-drawn styles",
                "line-art and SVG input",
                "colour fill and block animation",
                "story/annotation support",
            ],
            "best_for": [
                "whiteboard explanation",
                "character doodle",
                "diagram",
                "story beat",
                "highlight/reveal",
            ],
        },
        "motion_canvas": {
            "status": "planned",
            "library": "Motion Canvas",
            "best_for": ["intros", "kinetic typography", "charts", "vector diagrams", "transitions"],
        },
        "manim": {
            "status": "planned",
            "library": "Manim",
            "best_for": ["math", "science", "precise transformations", "technical diagrams"],
        },
        "handanim": {
            "status": "planned",
            "library": "HandAnim",
            "best_for": ["procedural handwriting", "organic doodles", "sketch effects"],
        },
    },
    "media_editing": {
        "ffmpeg": {
            "status": "implemented",
            "role": [
                "compose segments",
                "encode H.264/AAC",
                "mux audio",
                "mix background music",
                "extract thumbnail",
                "validate media",
                "resumable-upload source preparation",
            ],
        },
        "pyav": {
            "status": "planned",
            "role": [
                "precise frame/packet/codec manipulation",
                "custom frame transforms",
                "media inspection",
            ],
            "source": "https://github.com/PyAV-Org/PyAV",
        },
        "moviepy": {
            "status": "planned",
            "role": [
                "high-level programmatic composition",
                "clip sequencing",
                "effects",
                "text/media composition",
            ],
            "source": "https://github.com/Zulko/moviepy",
        },
        "pyscenedetect": {
            "status": "planned",
            "role": [
                "source-video scene detection",
                "automatic splitting",
                "cut/fade detection",
                "input analysis",
            ],
            "source": "https://www.scenedetect.com/",
        },
        "opencv": {
            "status": "optional",
            "role": [
                "frame/image analysis",
                "computer-vision preprocessing",
                "motion/region analysis",
            ],
        },
        "imageio_ffmpeg": {
            "status": "optional",
            "role": [
                "simple FFmpeg process wrapper",
            ],
        },
    },
    "audio": {
        "edge_tts": {
            "status": "implemented",
            "features": [
                "single narrator",
                "multiple speaker turns",
                "per-speaker voices",
                "rate modulation",
                "pitch modulation",
                "volume modulation",
                "turn pauses",
            ],
        },
        "background_music": {
            "status": "implemented",
            "features": [
                "loop to video duration",
                "configurable volume",
                "mix with narration",
            ],
        },
        "future": [
            "word-level TTS alignment",
            "audio ducking",
            "SFX timeline",
            "voice acting presets",
        ],
    },
    "captions": {
        "srt": {
            "status": "implemented",
            "features": ["narration captions", "speaker-labelled dialogue captions"],
        },
        "future": [
            "word-level karaoke timing",
            "ASS styling",
            "burned-in caption themes",
        ],
    },
    "publishing": {
        "youtube": {
            "status": "implemented",
            "features": [
                "resumable MP4 upload",
                "title/description/tags/category",
                "privacy state",
                "future publish scheduling via publishAt",
                "thumbnail upload",
                "caption-track upload",
            ],
            "credentials": "GitHub Actions secrets",
        },
    },
    "security": {
        "mcp": {
            "status": "OAuth-ready",
            "model": "OAuth 2.1 resource-server token verification with issuer/audience/JWKS",
            "production": "requires external standards-compliant OAuth/OIDC authorization server",
        },
        "github": "Render environment secret",
        "youtube": "GitHub Actions repository secrets",
    },
    "design_principles": [
        "ChatGPT chooses the content plan and segment composition.",
        "The MCP exposes stable semantic tools, not infrastructure details.",
        "Rendering engines are replaceable adapters.",
        "One Actions job composes many segments to avoid workflow startup per segment.",
        "Single segments can be preview-rendered without rebuilding the whole video.",
        "No credentials are stored in the public repository.",
    ],
}


def get_full_context() -> dict[str, Any]:
    return CAPABILITY_CONTEXT


def recommend_pipeline(
    content_type: str,
    visual_goal: str,
    audio_goal: str = "single_narrator",
) -> dict[str, Any]:
    content = content_type.lower()
    visual = visual_goal.lower()
    audio = audio_goal.lower()

    renderer = "whiteboard"
    reasons = []

    if any(term in visual for term in ("kinetic", "chart", "intro", "vector", "transition")):
        renderer = "motion_canvas"
        reasons.append("Motion Canvas is the planned vector/kinetic backend.")
    elif any(term in visual for term in ("math", "science", "equation", "technical")):
        renderer = "manim"
        reasons.append("Manim is the planned precision explainer backend.")
    elif any(term in visual for term in ("handwriting", "organic", "sketch")):
        renderer = "handanim"
        reasons.append("HandAnim is the planned procedural sketch backend.")
    else:
        reasons.append("Whiteboard is the implemented renderer and is the current default.")

    editing = ["ffmpeg"]
    if content in {"source-video", "existing-video", "podcast-video"}:
        editing.extend(["pyscenedetect", "pyav"])
        reasons.append("Input-video workflows benefit from scene detection and precise media inspection.")
    if "complex" in visual or "layered" in visual:
        editing.append("moviepy")
        reasons.append("High-level composition is useful for complex layered timelines.")

    audio_stack = ["edge_tts"] if audio not in {"none", "silent"} else []
    if audio in {"dialogue", "discussion", "multi_voice"}:
        reasons.append("Use speaker turns with per-speaker voice, rate, pitch, volume, and pauses.")

    return {
        "renderer": renderer,
        "editing_stack": editing,
        "audio_stack": audio_stack,
        "reasons": reasons,
        "implementation_note": (
            "If a planned renderer is requested before its adapter is implemented, "
            "ChatGPT should either use the closest implemented backend or request implementation first."
        ),
    }
