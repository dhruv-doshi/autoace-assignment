"""Reproducible FFmpeg probing and speech-analysis derivatives."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import numpy as np
import soundfile as sf


@dataclass(frozen=True)
class AudioMetadata:
    path: Path
    duration_seconds: float
    codec_name: str
    sample_rate_hz: int
    channels: int
    channel_layout: str | None


@dataclass(frozen=True)
class DecodedAudio:
    samples: np.ndarray
    sample_rate_hz: int
    provenance: dict[str, object]


def sha256_audio(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_audio(path: Path) -> AudioMetadata:
    command = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_name,sample_rate,channels,channel_layout",
        "-of", "json", str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValueError(f"ffprobe failed for {path.name}: {result.stderr.strip()[:300]}")
    payload = json.loads(result.stdout)
    stream = next((item for item in payload.get("streams", []) if "codec_name" in item), None)
    if stream is None:
        raise ValueError(f"no audio stream found: {path.name}")
    return AudioMetadata(
        path=path,
        duration_seconds=float(payload["format"]["duration"]),
        codec_name=str(stream["codec_name"]),
        sample_rate_hz=int(stream["sample_rate"]),
        channels=int(stream["channels"]),
        channel_layout=stream.get("channel_layout"),
    )


def decode_mono_16k(path: Path) -> DecodedAudio:
    command = [
        "ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000",
        "-f", "wav", "pipe:1",
    ]
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode:
        error = result.stderr.decode(errors="replace")[:300]
        raise ValueError(f"ffmpeg decode failed for {path.name}: {error}")
    samples, sample_rate = sf.read(BytesIO(result.stdout), dtype="float32", always_2d=False)
    if samples.ndim != 1:
        samples = np.mean(samples, axis=1, dtype=np.float32)
    return DecodedAudio(
        samples=np.asarray(samples, dtype=np.float32),
        sample_rate_hz=int(sample_rate),
        provenance={
            "source_sha256": sha256_audio(path),
            "purpose": "speech_analysis",
            "resample_hz": 16000,
            "channels": 1,
            "decoder": "ffmpeg",
        },
    )


def decode_stereo_16k(path: Path) -> tuple[np.ndarray, int]:
    """Decode a two-channel derivative for transparent channel-layout evidence."""

    command = [
        "ffmpeg", "-v", "error", "-i", str(path), "-ac", "2", "-ar", "16000",
        "-f", "wav", "pipe:1",
    ]
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode:
        error = result.stderr.decode(errors="replace")[:300]
        raise ValueError(f"ffmpeg stereo decode failed for {path.name}: {error}")
    samples, sample_rate = sf.read(BytesIO(result.stdout), dtype="float32", always_2d=True)
    return np.asarray(samples, dtype=np.float32), int(sample_rate)
