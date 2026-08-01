"""Production P6 hybrid call-audio analysis pipeline."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import cast

import psutil

from autoace.audio.asr import LocalAsrModel
from autoace.audio.decode import decode_mono_16k, decode_stereo_16k, probe_audio
from autoace.audio.dsp import channel_correlation, summarize_audio
from autoace.audio.events import acoustic_event_proxy
from autoace.audio.overlap import channel_layout_evidence, spectral_overlap_proxy
from autoace.audio.quality import quality_proxy
from autoace.audio.vad import energy_vad
from autoace.contracts import CallAnalysisResult
from autoace.inference.gemini_audio import OpenRouterAudioObserver
from autoace.models import ensure_whisper_model

DEFAULT_ASR_MODEL = Path("models/faster-whisper/tiny")


def _semantic_tone(text: str) -> tuple[str, str, dict[str, object]]:
    normalized = text.lower()
    upset_terms = ("angry", "upset", "terrible", "ridiculous", "complaint")
    frustrated_terms = ("frustrated", "problem", "issue", "cancel", "waiting")
    satisfied_terms = ("thank", "great", "appreciate", "perfect", "wonderful")
    upset_hits = [term for term in upset_terms if term in normalized]
    frustrated_hits = [term for term in frustrated_terms if term in normalized]
    satisfied_hits = [term for term in satisfied_terms if term in normalized]
    repeated_hello_count = normalized.count("hello")
    if upset_hits or repeated_hello_count >= 3:
        tone = "upset"
        intensity = "high" if repeated_hello_count >= 3 or len(upset_hits) > 1 else "medium"
    elif frustrated_hits:
        tone = "frustrated"
        intensity = "medium"
    elif satisfied_hits:
        tone = "satisfied"
        intensity = "medium"
    else:
        tone = "neutral"
        intensity = "low"
    return tone, intensity, {
        "backend": "whisper_lexical_rules",
        "upset_terms": upset_hits,
        "frustrated_terms": frustrated_hits,
        "satisfied_terms": satisfied_hits,
        "repeated_hello_count": repeated_hello_count,
    }


def _local_evidence(path: Path) -> tuple[CallAnalysisResult, dict[str, object]]:
    metadata = probe_audio(path)
    decoded = decode_mono_16k(path)
    features = summarize_audio(decoded.samples, decoded.sample_rate_hz)
    vad_result = energy_vad(decoded.samples, decoded.sample_rate_hz)
    events = acoustic_event_proxy(features)
    quality = quality_proxy(features)

    channels, stereo_sample_rate = decode_stereo_16k(path)
    correlation = channel_correlation(channels)
    layout = channel_layout_evidence(channels, channel_correlation=correlation)
    overlap = spectral_overlap_proxy(channels, stereo_sample_rate)

    loud = features["dbfs"] > -20.0
    dynamic = features["crest_factor"] >= 12.0
    noisy = features["spectral_flatness"] >= 0.28
    high_intensity = loud and features["spectral_flatness"] < 0.25
    prosody_intensity = (
        "high" if high_intensity else "medium" if dynamic or noisy else "low"
    )

    model_path = Path(os.environ.get("AUTOACE_WHISPER_MODEL_PATH", str(DEFAULT_ASR_MODEL)))
    model_path = ensure_whisper_model(model_path)
    transcript = LocalAsrModel(model_path, "tiny").transcribe(path)
    tone, lexical_intensity, semantics = _semantic_tone(cast(str, transcript["text"]))
    intensity = "high" if lexical_intensity == "high" else prosody_intensity

    noise_present = bool(events["background_noise_present"])
    noise_type = str(events["background_noise_type"]) if noise_present else ""
    noise_severity = str(events["background_noise_severity"]) if noise_present else "none"
    long_silence = vad_result.longest_silence_seconds >= 8.0
    result = CallAnalysisResult.model_validate(
        {
            "emotional_tone": tone,
            "emotional_intensity": intensity,
            "background_noise_present": noise_present,
            "background_noise_type": noise_type,
            "background_noise_severity": noise_severity,
            "audio_quality": quality["audio_quality"],
            "speaker_overlap_present": overlap["speaker_overlap_present"],
            "long_silence_present": long_silence,
            "confidence": 0.55,
        }
    )
    stats: dict[str, object] = {
        "input_bytes": path.stat().st_size,
        "input_duration_seconds": metadata.duration_seconds,
        "input_codec": metadata.codec_name,
        "input_sample_rate_hz": metadata.sample_rate_hz,
        "input_channels": metadata.channels,
        "input_channel_layout": metadata.channel_layout,
        "decoded_sample_rate_hz": decoded.sample_rate_hz,
        "decoded_samples": int(decoded.samples.size),
        "dsp": features,
        "vad": {
            "speech_ratio": vad_result.speech_ratio,
            "longest_silence_seconds": vad_result.longest_silence_seconds,
            "backend": vad_result.backend,
        },
        "noise_evidence": events,
        "quality_evidence": quality,
        "channel_evidence": {
            **layout,
            **overlap,
            "sample_rate_hz": stereo_sample_rate,
            "channel_correlation": correlation,
        },
        "prosody_evidence": {
            "backend": "dsp_proxy",
            "loud": loud,
            "dynamic": dynamic,
            "noisy": noisy,
            "high_intensity": high_intensity,
            "mapped_intensity": prosody_intensity,
        },
        "transcript": transcript,
        "semantic_evidence": {
            **semantics,
            "lexical_intensity": lexical_intensity,
            "final_intensity": intensity,
        },
    }
    return result, stats


def _fuse_p6(
    remote: CallAnalysisResult, local: CallAnalysisResult
) -> tuple[CallAnalysisResult, dict[str, object]]:
    update: dict[str, object] = {
        "audio_quality": local.audio_quality,
        "long_silence_present": local.long_silence_present,
    }
    owners: dict[str, object] = {
        "audio_quality": "local_dsp",
        "long_silence_present": "local_vad",
        "emotional_tone": "remote_audio",
        "emotional_intensity": "remote_audio",
        "background_noise": "remote_audio",
        "speaker_overlap_present": "remote_audio",
    }
    if local.background_noise_present:
        update.update(
            {
                "background_noise_present": True,
                "background_noise_type": local.background_noise_type,
                "background_noise_severity": local.background_noise_severity,
            }
        )
        owners["background_noise"] = "local_dsp_signature"
    if local.speaker_overlap_present:
        update["speaker_overlap_present"] = True
        owners["speaker_overlap_present"] = "local_spectral_polyphony"
    if (
        remote.emotional_intensity == "low"
        and local.emotional_intensity in {"medium", "high"}
    ):
        update["emotional_intensity"] = local.emotional_intensity
        owners["emotional_intensity"] = "local_prosody"
    if remote.emotional_tone == "neutral" and local.emotional_tone != "neutral":
        update["emotional_tone"] = local.emotional_tone
        update["emotional_intensity"] = local.emotional_intensity
        owners["emotional_tone"] = "local_whisper_semantics"
        owners["emotional_intensity"] = "local_whisper_semantics"
    return remote.model_copy(update=update), owners


def analyze_p6_with_stats(
    path: Path,
    observer: OpenRouterAudioObserver,
) -> tuple[CallAnalysisResult, dict[str, object]]:
    """Run the sole production pipeline and return result plus operational evidence."""

    process = psutil.Process(os.getpid())
    before_rss = process.memory_info().rss
    started = time.perf_counter()
    local_result, stats = _local_evidence(path)
    remote_response = observer.observe(
        path, audio_seconds=cast(float, stats["input_duration_seconds"])
    )
    remote_result = CallAnalysisResult.model_validate(remote_response["observation"])
    result, owners = _fuse_p6(remote_result, local_result)
    stats.update(
        {
            "pipeline": "P6",
            "pipeline_revision": "p6-production-v1",
            "remote": remote_response,
            "field_owners": owners,
            "elapsed_seconds": time.perf_counter() - started,
            "peak_rss_mb": max(before_rss, process.memory_info().rss) / (1024 * 1024),
        }
    )
    return result, stats
