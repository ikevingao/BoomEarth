"""Unified factory for instantiating local and cloud TTS narrators."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from boomearth.audio.cloud_tts import CloudTTSNarrator, CloudTTSRouting
from boomearth.audio.indextts2 import IndexTTS2Narrator, TTSRouting

NarratorInstance = Union[IndexTTS2Narrator, CloudTTSNarrator]


def load_narrator(route_path: Path, root: Path | None = None) -> NarratorInstance:
    """Instantiate the appropriate narrator from a tts-routing.json config file."""
    if not route_path.is_file():
        raise FileNotFoundError(f"TTS routing file not found: {route_path}")

    try:
        payload = json.loads(route_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to read TTS routing configuration from {route_path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("TTS routing config must be a JSON object")

    provider = str(payload.get("provider", "")).strip()

    if provider == "indextts2-local":
        route = TTSRouting.load(route_path)
        return IndexTTS2Narrator(route)
    elif provider in ("edge-tts", "dashscope-cosyvoice", "cloud-tts"):
        cloud_route = CloudTTSRouting.load(route_path)
        return CloudTTSNarrator(cloud_route, root=root)
    else:
        raise ValueError(f"Unknown or unsupported TTS provider in routing config: '{provider}'")
