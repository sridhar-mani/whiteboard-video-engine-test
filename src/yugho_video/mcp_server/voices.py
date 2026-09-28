from __future__ import annotations


async def list_edge_voices(locale: str | None = None) -> list[dict[str, str]]:
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("edge-tts is not installed") from exc

    voices = await edge_tts.list_voices()
    normalized_locale = locale.lower().replace("_", "-") if locale else None

    output = []
    for voice in voices:
        voice_locale = str(voice.get("Locale", ""))
        if normalized_locale and voice_locale.lower() != normalized_locale:
            continue
        output.append(
            {
                "short_name": str(voice.get("ShortName", "")),
                "name": str(voice.get("Name", "")),
                "locale": voice_locale,
                "gender": str(voice.get("Gender", "")),
            }
        )

    return sorted(
        output,
        key=lambda item: (
            item["locale"],
            item["gender"],
            item["short_name"],
        ),
    )
