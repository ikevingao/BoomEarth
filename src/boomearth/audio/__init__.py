"""Audio production adapters and unified factory for BoomEarth."""

from boomearth.audio.cloud_tts import CloudTTSNarrator, CloudTTSRouting, CloudTTSValidationError
from boomearth.audio.indextts2 import AudioProbe, IndexTTS2Narrator, IndexTTS2ValidationError, TTSRouting, VoiceManifest
from boomearth.audio.narrator_factory import load_narrator

__all__ = [
    "AudioProbe",
    "CloudTTSNarrator",
    "CloudTTSRouting",
    "CloudTTSValidationError",
    "IndexTTS2Narrator",
    "IndexTTS2ValidationError",
    "TTSRouting",
    "VoiceManifest",
    "load_narrator",
]
