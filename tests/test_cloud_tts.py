"""Tests for Cloud TTS narrator, routing and contracts."""

import json
from pathlib import Path
import pytest

from boomearth.audio.cloud_tts import (
    CloudTTSNarrator,
    CloudTTSRouting,
    CloudTTSValidationError,
)
from boomearth.audio.narrator_factory import load_narrator


def test_cloud_tts_routing_load_edge_tts(tmp_path: Path) -> None:
    config_file = tmp_path / "tts-routing.json"
    config_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "provider": "edge-tts",
                "model": "azure-neural",
                "voice_id": "zh-CN-YunxiNeural",
                "playback_speed": 1.12,
                "used_fallback": False,
            }
        ),
        encoding="utf-8",
    )

    route = CloudTTSRouting.load(config_file)
    assert route.provider == "edge-tts"
    assert route.model == "azure-neural"
    assert route.voice_id == "zh-CN-YunxiNeural"
    assert route.playback_speed == 1.12
    assert route.used_fallback is False


def test_cloud_tts_routing_load_dashscope(tmp_path: Path) -> None:
    config_file = tmp_path / "tts-routing.json"
    config_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "provider": "dashscope-cosyvoice",
                "model": "cosyvoice-v1",
                "voice_id": "longxiaochun",
                "playback_speed": 1.12,
                "used_fallback": False,
            }
        ),
        encoding="utf-8",
    )

    route = CloudTTSRouting.load(config_file)
    assert route.provider == "dashscope-cosyvoice"
    assert route.model == "cosyvoice-v1"
    assert route.voice_id == "longxiaochun"


def test_cloud_tts_routing_invalid_provider(tmp_path: Path) -> None:
    config_file = tmp_path / "tts-routing.json"
    config_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "provider": "unsupported-provider-xyz",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported cloud provider"):
        CloudTTSRouting.load(config_file)


def test_narrator_factory_dispatcher(tmp_path: Path) -> None:
    edge_file = tmp_path / "edge_routing.json"
    edge_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "provider": "edge-tts",
                "model": "azure-neural",
                "voice_id": "zh-CN-YunxiNeural",
                "playback_speed": 1.12,
                "used_fallback": False,
            }
        ),
        encoding="utf-8",
    )

    narrator = load_narrator(edge_file)
    assert isinstance(narrator, CloudTTSNarrator)
    assert narrator.route.provider == "edge-tts"


def test_cloud_tts_dashscope_requires_key_when_validating(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    route = CloudTTSRouting(
        provider="dashscope-cosyvoice",
        model="cosyvoice-v1",
        voice_id="longxiaochun",
    )
    narrator = CloudTTSNarrator(route, root=tmp_path)
    with pytest.raises(CloudTTSValidationError, match="DASHSCOPE_API_KEY is required"):
        narrator.validate_environment()


def test_cloud_tts_render_mock_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Prepare batch file
    batch_file = tmp_path / "narration.jsonl"
    batch_file.write_text(
        json.dumps({"text": "测试第一句", "silence_after_ms": 300}) + "\n" +
        json.dumps({"text": "测试第二句", "silence_after_ms": 0}) + "\n",
        encoding="utf-8",
    )

    output_wav = tmp_path / "output" / "final.wav"
    manifest_path = tmp_path / "output" / "voice_manifest.json"

    route = CloudTTSRouting(
        provider="edge-tts",
        model="azure-neural",
        voice_id="zh-CN-YunxiNeural",
        playback_speed=1.12,
    )
    narrator = CloudTTSNarrator(route, root=tmp_path)

    # Mock synthesize method to generate silent sine wave using ffmpeg instead of network call
    def fake_synthesize(text: str, output_path: Path) -> None:
        import subprocess
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.5", "-c:a", "pcm_s16le", "-f", "wav", str(output_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )

    monkeypatch.setattr(narrator, "_synthesize_segment_edge_tts", fake_synthesize)

    manifest = narrator.render(batch_file, output_wav, manifest_path)

    assert output_wav.is_file()
    assert manifest_path.is_file()
    assert manifest.provider == "edge-tts"
    assert manifest.playback_speed == 1.12
    assert manifest.segment_count == 2
    assert manifest.output_path == str(output_wav.resolve())

    # Probe committed WAV
    probe = narrator.probe_committed_wav(output_wav, manifest)
    assert probe.codec == "pcm_s16le"
    assert probe.channels == 1
    assert probe.sample_rate == 24000
    assert probe.duration_seconds > 0


def test_check_env_cloud_mode_bypasses_indextts2_local_path_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import importlib.util
    script = Path(__file__).resolve().parents[1] / "automation" / "scripts" / "check_env.py"
    spec = importlib.util.spec_from_file_location("boomearth_check_env_cloud_test", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Prepare root with .env and yt-dlp only (no local IndexTTS2 directories created)
    root = tmp_path / "cloud_env"
    root.mkdir()
    yt_dlp = root / "yt-dlp.exe"
    yt_dlp.write_bytes(b"fake yt-dlp")

    from boomearth.config import DEFAULTS
    env_lines = [
        "TIKHUB_API_KEY=fake-tikhub",
        "DASHSCOPE_API_KEY=fake-dashscope",
        "VOLCENGINE_API_KEY=fake-volcengine",
        *(f"{k}={v}" for k, v in DEFAULTS.items()),
        f"YT_DLP_PATH={yt_dlp}",
        "TTS_PROVIDER=edge-tts",
        "TTS_VOICE=zh-CN-YunxiNeural",
    ]
    (root / ".env").write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    exit_code = module.main(root=root)
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "status=OK" in output
    assert "missing_paths" not in output


