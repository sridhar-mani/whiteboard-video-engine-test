RENDERERS = {
    "whiteboard": {
        "description": "Hand-drawn progressive stroke animation with a moving hand.",
        "best_for": [
            "whiteboard explanations",
            "character doodles",
            "hand-drawn diagrams",
            "highlight/reveal scenes",
        ],
    },
    "motion-canvas": {
        "description": "Planned vector/kinetic renderer adapter.",
        "best_for": [
            "intros",
            "kinetic typography",
            "charts",
            "data explainers",
            "transitions",
        ],
    },
    "manim": {
        "description": "Planned precision explainer adapter.",
        "best_for": ["math", "scientific diagrams", "precise transformations"],
    },
    "handanim": {
        "description": "Planned procedural sketch animation adapter.",
        "best_for": ["handwritten effects", "procedural doodles", "organic motion"],
    },
}


SEGMENT_KINDS = {
    "hook": "Fast attention-grabbing opening.",
    "intro": "Branded introduction or premise setup.",
    "whiteboard_explanation": "Progressive hand-drawn explanation.",
    "animated_doodle": "Character-driven hand-drawn story beat.",
    "diagram": "Hand-drawn or vector systems/flow diagram.",
    "data_explainer": "Charts, comparisons, statistics, and numerical explanation.",
    "story": "Narrative sequence built from one or more visual beats.",
    "quote": "Quote or statement emphasis.",
    "broll": "Reserved slot for future media/B-roll backend.",
    "transition": "Short visual bridge between major sections.",
    "cta": "Call-to-action or end-card section.",
    "outro": "Closing/branded end sequence.",
}


def list_renderers() -> list[dict[str, object]]:
    return [{"id": key, **value} for key, value in RENDERERS.items()]


def list_segment_kinds() -> list[dict[str, str]]:
    return [{"id": key, "description": value} for key, value in SEGMENT_KINDS.items()]
