"""Cloud TTS routing and narration implementation for BoomEarth.

Supports DashScope CosyVoice and Edge-TTS providers with unified output contracts.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from dotenv import dotenv_values

from boomearth.audio.indextts2 import AudioProbe, VoiceManifest


class CloudTTSValidationError(ValueError):
    """Raised when cloud narration inputs or environment do not validate."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            while block := source.read(1024 * 1024):
                digest.update(block)
    except OSError as exc:
        raise CloudTTSValidationError("audio file is unavailable") from exc
    return digest.hexdigest()


def _write_durable_json(
    path: Path,
    payload: Mapping[str, Any],
    *,
    indent: int | None = None,
) -> None:
    encoded = (json.dumps(payload, ensure_ascii=False, indent=indent) + "\n").encode("utf-8")
    with path.open("w", encoding="utf-8") as destination:
        destination.write(json.dumps(payload, ensure_ascii=False, indent=indent) + "\n")


@dataclass(frozen=True)
class CloudTTSRouting:
    provider: str
    model: str
    voice_id: str
    playback_speed: float = 1.12
    used_fallback: bool = False
    reference_audio_path: Path | None = None
    reference_audio_sha256: str = ""

    @classmethod
    def load(cls, path: Path) -> "CloudTTSRouting":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("unable to load TTS routing") from exc

        if not isinstance(payload, dict):
            raise ValueError("TTS routing must be a JSON object")

        provider = str(payload.get("provider", "")).strip()
        if provider not in ("edge-tts", "dashscope-cosyvoice", "cloud-tts"):
            raise ValueError(f"unsupported cloud provider: {provider}")

        model = str(payload.get("model", "azure-neural" if provider == "edge-tts" else "cosyvoice-v1"))
        voice_id = str(payload.get("voice_id", "zh-CN-YunxiNeural" if provider == "edge-tts" else "longxiaochun"))
        playback_speed = float(payload.get("playback_speed", 1.12))
        used_fallback = bool(payload.get("used_fallback", False))

        ref_path_raw = payload.get("reference_audio_path")
        ref_path = Path(str(ref_path_raw)) if ref_path_raw else None
        ref_sha256 = str(payload.get("reference_audio_sha256", ""))

        return cls(
            provider=provider,
            model=model,
            voice_id=voice_id,
            playback_speed=playback_speed,
            used_fallback=used_fallback,
            reference_audio_path=ref_path,
            reference_audio_sha256=ref_sha256,
        )


class CloudTTSNarrator:
    """Narrator that uses cloud APIs (Edge-TTS or DashScope CosyVoice) to render speech."""

    def __init__(self, route: CloudTTSRouting, root: Path | None = None) -> None:
        self.route = route
        self.root = root or Path.cwd()

    def validate_environment(self) -> None:
        if shutil.which("ffmpeg") is None:
            raise CloudTTSValidationError("ffmpeg executable is required but not found in PATH")
        if shutil.which("ffprobe") is None:
            raise CloudTTSValidationError("ffprobe executable is required but not found in PATH")

        if self.route.provider == "dashscope-cosyvoice":
            key = os.environ.get("DASHSCOPE_API_KEY")
            if not key:
                env_file = self.root / ".env"
                if env_file.is_file():
                    key = dotenv_values(env_file).get("DASHSCOPE_API_KEY")
            if not key or not str(key).strip():
                raise CloudTTSValidationError("DASHSCOPE_API_KEY is required for dashscope-cosyvoice")

    def _synthesize_segment_edge_tts(self, text: str, output_path: Path) -> None:
        import edge_tts

        async def _run() -> None:
            communicate = edge_tts.Communicate(text=text, voice=self.route.voice_id)
            await communicate.save(str(output_path))

        try:
            asyncio.run(_run())
        except Exception as exc:
            raise CloudTTSValidationError(f"edge-tts synthesis failed: {exc}") from exc

    def _synthesize_segment_dashscope(self, text: str, output_path: Path) -> None:
        import dashscope
        from dashscope.audio.tts import SpeechSynthesizer

        key = os.environ.get("DASHSCOPE_API_KEY")
        if not key:
            env_file = self.root / ".env"
            if env_file.is_file():
                key = dotenv_values(env_file).get("DASHSCOPE_API_KEY")

        dashscope.api_key = key
        try:
            result = SpeechSynthesizer.call(
                model=self.route.model,
                text=text,
                voice=self.route.voice_id,
                format="wav",
            )
            if result.get_audio_data() is not None:
                with open(output_path, "wb") as f:
                    f.write(result.get_audio_data())
            else:
                raise CloudTTSValidationError(f"DashScope TTS error: {result}")
        except Exception as exc:
            raise CloudTTSValidationError(f"dashscope cosyvoice synthesis failed: {exc}") from exc

    def _parse_batch(self, batch_file: Path) -> list[dict[str, Any]]:
        if not batch_file.is_file():
            raise CloudTTSValidationError(f"batch file not found: {batch_file}")

        segments = []
        text_content = batch_file.read_text(encoding="utf-8").strip()
        if not text_content:
            raise CloudTTSValidationError("batch file is empty")

        for line_num, line in enumerate(text_content.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if isinstance(data, dict):
                    segments.append(data)
                elif isinstance(data, str):
                    segments.append({"text": data, "silence_after_ms": 0})
            except json.JSONDecodeError:
                # Plain text line fallback
                segments.append({"text": line, "silence_after_ms": 0})

        if not segments:
            raise CloudTTSValidationError("no valid segments parsed from batch file")
        return segments

    def render(self, batch_file: Path, output_wav: Path, manifest_path: Path) -> VoiceManifest:
        self.validate_environment()
        segments_data = self._parse_batch(batch_file)

        raw_audit_wav = output_wav.with_name(f"{output_wav.stem}.raw.wav")
        output_wav.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        temp_dir = Path(tempfile.mkdtemp(prefix=f"boomearth_cloud_tts_{uuid.uuid4().hex[:8]}_"))
        try:
            segment_wavs: list[Path] = []
            for idx, seg in enumerate(segments_data, start=1):
                raw_text = seg.get("tts_text") or seg.get("text") or ""
                if not raw_text.strip():
                    continue

                seg_raw = temp_dir / f"seg_{idx:04d}_raw.audio"
                if self.route.provider == "dashscope-cosyvoice":
                    self._synthesize_segment_dashscope(raw_text, seg_raw)
                else:
                    self._synthesize_segment_edge_tts(raw_text, seg_raw)

                # Convert to standard 16-bit PCM wav
                seg_pcm = temp_dir / f"seg_{idx:04d}.wav"
                silence_ms = int(seg.get("silence_after_ms", 0))

                cmd = ["ffmpeg", "-y", "-i", str(seg_raw), "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le"]
                if silence_ms > 0:
                    silence_sec = silence_ms / 1000.0
                    cmd.extend(["-af", f"apad=pad_dur={silence_sec:.3f}"])
                cmd.append(str(seg_pcm))

                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                if res.returncode != 0 or not seg_pcm.is_file():
                    raise CloudTTSValidationError(f"failed to normalize segment {idx} with ffmpeg")
                segment_wavs.append(seg_pcm)

            if not segment_wavs:
                raise CloudTTSValidationError("no audio generated for any segment")

            # Concat all segments into raw audit WAV
            concat_list_file = temp_dir / "concat_list.txt"
            concat_list_file.write_text(
                "\n".join(f"file '{p.resolve().as_posix()}'" for p in segment_wavs) + "\n",
                encoding="utf-8",
            )

            raw_combined = temp_dir / "raw_combined.wav"
            concat_cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list_file),
                "-c:a",
                "pcm_s16le",
                str(raw_combined),
            ]
            res = subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            if res.returncode != 0 or not raw_combined.is_file():
                raise CloudTTSValidationError("failed to concatenate audio segments")

            # Apply speed adjustment (atempo) to create final output WAV
            speed = float(self.route.playback_speed)
            final_temp = temp_dir / "final_speed.wav"

            if abs(speed - 1.0) > 1e-4:
                tempo_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(raw_combined),
                    "-filter:a",
                    f"atempo={speed:.4f}",
                    "-c:a",
                    "pcm_s16le",
                    str(final_temp),
                ]
                res = subprocess.run(tempo_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                if res.returncode != 0 or not final_temp.is_file():
                    raise CloudTTSValidationError("failed to apply playback speed filter")
            else:
                shutil.copy2(raw_combined, final_temp)

            # Move to final destinations
            shutil.copy2(final_temp, output_wav)
            shutil.copy2(raw_combined, raw_audit_wav)

            # Generate VoiceManifest
            manifest = VoiceManifest(
                provider=self.route.provider,
                voice_id=self.route.voice_id,
                model=self.route.model,
                reference_audio_path=str(self.route.reference_audio_path) if self.route.reference_audio_path else "",
                reference_audio_sha256=self.route.reference_audio_sha256,
                output_path=str(output_wav.resolve(strict=False)),
                output_sha256=_sha256(output_wav),
                segment_contract_path=str(batch_file.resolve(strict=False)),
                segment_contract_sha256=_sha256(batch_file),
                segment_count=len(segment_wavs),
                playback_speed=self.route.playback_speed,
                pronunciation_contract_path="",
                pronunciation_contract_sha256="",
                used_fallback=self.route.used_fallback,
            )

            _write_durable_json(manifest_path, manifest.to_dict(), indent=2)
            return manifest
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def probe_committed_wav(self, audio_path: Path, manifest: VoiceManifest) -> AudioProbe:
        ffprobe = shutil.which("ffprobe")
        if ffprobe is None:
            raise CloudTTSValidationError("ffprobe is required")

        try:
            result = subprocess.run(
                [
                    ffprobe,
                    "-v",
                    "error",
                    "-select_streams",
                    "a:0",
                    "-show_entries",
                    "stream=codec_name,sample_rate,channels,duration",
                    "-show_entries",
                    "format=format_name,duration",
                    "-of",
                    "json",
                    str(audio_path),
                ],
                capture_output=True,
                check=False,
                text=True,
            )
            if result.returncode != 0:
                raise CloudTTSValidationError(f"ffprobe failed: {result.stderr}")

            data = json.loads(result.stdout)
            stream = data["streams"][0]
            fmt = data["format"]

            sha256_val = _sha256(audio_path)
            if sha256_val.casefold() != manifest.output_sha256.casefold():
                raise CloudTTSValidationError("output sha256 mismatch with manifest")

            duration = float(stream.get("duration") or fmt.get("duration") or 0.0)

            return AudioProbe(
                container=fmt.get("format_name", "wav"),
                codec=stream.get("codec_name", "pcm_s16le"),
                sample_rate=int(stream["sample_rate"]),
                channels=int(stream["channels"]),
                duration_seconds=duration,
                sha256=sha256_val,
            )
        except Exception as exc:
            raise CloudTTSValidationError(f"failed to probe committed WAV: {exc}") from exc
