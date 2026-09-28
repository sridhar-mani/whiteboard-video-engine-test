from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SpeakerTurn(BaseModel):
    speaker: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=5000)
    voice: str | None = None
    rate: str = "+0%"
    pitch: str = "+0Hz"
    volume: str = "+0%"
    pause_after_sec: float = Field(default=0.15, ge=0.0, le=5.0)


class SegmentSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
    kind: str = Field(default="whiteboard_explanation", min_length=1, max_length=80)
    renderer: str = Field(default="whiteboard", min_length=1, max_length=80)
    duration_sec: float = Field(gt=0, le=1800)
    narration: str = ""
    dialogue: list[SpeakerTurn] = Field(default_factory=list, max_length=200)
    input_path: str | None = None
    config: dict[str, object] = Field(default_factory=dict)


class AudioSpec(BaseModel):
    provider: Literal["none", "edge"] = "none"
    voice: str | None = None
    rate: str = "+0%"
    pitch: str = "+0Hz"
    volume: str = "+0%"
    speaker_voices: dict[str, str] = Field(default_factory=dict)
    background_music_path: str | None = None
    background_music_volume: float = Field(default=0.12, ge=0.0, le=1.0)
    fit_segments_to_narration: bool = True


class PublishSpec(BaseModel):
    enabled: bool = False
    privacy_status: Literal["private", "unlisted", "public"] = "private"
    publish_at: str | None = None
    category_id: str = "27"
    language: str = "en"


class VideoProject(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: str = "1.2"
    project_id: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    title: str = Field(min_length=1, max_length=100)
    topic: str = Field(min_length=1, max_length=500)
    description: str = ""
    tags: list[str] = Field(default_factory=list, max_length=30)
    segments: list[SegmentSpec] = Field(min_length=1, max_length=120)
    audio: AudioSpec = Field(default_factory=AudioSpec)
    publish: PublishSpec = Field(default_factory=PublishSpec)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        cleaned = []
        seen = set()
        for tag in value:
            normalized = tag.strip()
            if normalized and normalized.lower() not in seen:
                cleaned.append(normalized)
                seen.add(normalized.lower())
        return cleaned
