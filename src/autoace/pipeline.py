"""Executable local P0 analysis pipeline."""

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
from autoace.audio.vad import SileroVad, energy_vad
from autoace.contracts import CallAnalysisResult
from autoace.inference.fusion import p0_result
from autoace.inference.gemini_audio import OpenRouterAudioObserver


def _analyze_p0(
    path: Path, *, silero_model: Path | None = None
) -> tuple[CallAnalysisResult, dict[str, object]]:
    metadata = probe_audio(path)
    decoded = decode_mono_16k(path)
    features = summarize_audio(decoded.samples, decoded.sample_rate_hz)
    if silero_model and silero_model.is_file():
        vad_result = SileroVad(silero_model).run(decoded.samples, decoded.sample_rate_hz)
    else:
        vad_result = energy_vad(decoded.samples, decoded.sample_rate_hz)
    vad = {
        "speech_ratio": vad_result.speech_ratio,
        "longest_silence_seconds": vad_result.longest_silence_seconds,
        "backend": vad_result.backend,
    }
    result = p0_result(
        quality=quality_proxy(features),
        events=acoustic_event_proxy(features),
        vad=vad,
        overlap={"speaker_overlap_present": False},
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
        "vad": vad,
        "vad_backend": vad_result.backend,
        "quality_backend": "dsp_proxy",
        "events_backend": "dsp_proxy",
        "overlap_backend": "deterministic_false_default",
        "silero_model_used": bool(silero_model and silero_model.is_file()),
    }
    return result, stats


def analyze_p0_with_stats(
    path: Path, *, silero_model: Path | None = None
) -> tuple[CallAnalysisResult, dict[str, object]]:
    """Analyze one file and return reproducibility/resource statistics."""

    process = psutil.Process(os.getpid())
    before_rss = process.memory_info().rss
    started = time.perf_counter()
    result, stats = _analyze_p0(path, silero_model=silero_model)
    stats["elapsed_seconds"] = time.perf_counter() - started
    stats["peak_rss_mb"] = max(before_rss, process.memory_info().rss) / (1024 * 1024)
    return result, stats


def analyze_p0(path: Path, *, silero_model: Path | None = None) -> CallAnalysisResult:
    """Analyze one file without remote inference or unvalidated local models."""

    result, _stats = analyze_p0_with_stats(path, silero_model=silero_model)
    return result


def _update_resource_stats(
    stats: dict[str, object], *, before_rss: int, started: float
) -> None:
    process = psutil.Process(os.getpid())
    stats["elapsed_seconds"] = time.perf_counter() - started
    stats["peak_rss_mb"] = max(before_rss, process.memory_info().rss) / (1024 * 1024)


def analyze_p1_with_stats(path: Path) -> tuple[CallAnalysisResult, dict[str, object]]:
    """Run local acoustic evidence beyond P0 without unverified model substitutions."""

    process = psutil.Process(os.getpid())
    before_rss = process.memory_info().rss
    started = time.perf_counter()
    result, stats = analyze_p0_with_stats(path)
    channels, sample_rate = decode_stereo_16k(path)
    correlation = channel_correlation(channels)
    layout = channel_layout_evidence(channels, channel_correlation=correlation)
    spectral_overlap = spectral_overlap_proxy(channels, sample_rate)
    overlap_present = bool(spectral_overlap["speaker_overlap_present"])
    result = result.model_copy(update={"speaker_overlap_present": overlap_present})
    stats["pipeline"] = "P1"
    stats["channel_evidence"] = {
        **layout,
        **spectral_overlap,
        "sample_rate_hz": sample_rate,
        "channel_correlation": correlation,
    }
    stats["specialists"] = {
        "dnsmos": "not_installed; P0 DSP quality proxy retained",
        "yamnet": "not_installed; P0 acoustic-event proxy retained",
        "overlap": "spectral_polyphony_proxy",
    }
    _update_resource_stats(stats, before_rss=before_rss, started=started)
    return result, stats


def analyze_p2_with_stats(path: Path) -> tuple[CallAnalysisResult, dict[str, object]]:
    """Add transparent local prosody evidence on top of P1."""

    process = psutil.Process(os.getpid())
    before_rss = process.memory_info().rss
    started = time.perf_counter()
    result, stats = analyze_p1_with_stats(path)
    features = cast(dict[str, float], stats["dsp"])
    # Transparent calibration for telephony audio: sustained, non-flat loud
    # speech suggests high intensity; a dynamic programme bed or sharper
    # background raises otherwise quiet speech to medium.
    loud = features["dbfs"] > -20.0
    dynamic = features["crest_factor"] >= 12.0
    noisy = features["spectral_flatness"] >= 0.28
    high_intensity = loud and features["spectral_flatness"] < 0.25
    intensity = "high" if high_intensity else "medium" if dynamic or noisy else "low"
    result = result.model_copy(update={"emotional_intensity": intensity})
    stats["pipeline"] = "P2"
    stats["prosody_evidence"] = {
        "backend": "dsp_proxy",
        "loud": loud,
        "dynamic": dynamic,
        "noisy": noisy,
        "high_intensity": high_intensity,
        "mapped_intensity": intensity,
        "note": "Not a replacement for a validated emotion model.",
    }
    _update_resource_stats(stats, before_rss=before_rss, started=started)
    return result, stats


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


def analyze_p3_with_stats(path: Path) -> tuple[CallAnalysisResult, dict[str, object]]:
    """Run P2 plus the pinned local Whisper tiny semantic heuristic."""

    process = psutil.Process(os.getpid())
    before_rss = process.memory_info().rss
    started = time.perf_counter()
    result, stats = analyze_p2_with_stats(path)
    transcript = LocalAsrModel(Path("models/faster-whisper/tiny"), "tiny").transcribe(path)
    tone, lexical_intensity, semantic_evidence = _semantic_tone(cast(str, transcript["text"]))
    prosody = cast(dict[str, object], stats["prosody_evidence"])
    prosody_intensity = cast(str, prosody["mapped_intensity"])
    intensity = (
        "high"
        if lexical_intensity == "high"
        else prosody_intensity
    )
    result = result.model_copy(
        update={"emotional_tone": tone, "emotional_intensity": intensity}
    )
    stats["pipeline"] = "P3"
    stats["transcript"] = transcript
    semantic_evidence = {
        **semantic_evidence,
        "lexical_intensity": lexical_intensity,
        "final_intensity": intensity,
    }
    stats["semantic_evidence"] = semantic_evidence
    _update_resource_stats(stats, before_rss=before_rss, started=started)
    return result, stats


def analyze_p4_with_stats(
    path: Path,
    observer: OpenRouterAudioObserver,
) -> tuple[CallAnalysisResult, dict[str, object]]:
    """Run the approved Gemini audio candidate through OpenRouter."""

    process = psutil.Process(os.getpid())
    before_rss = process.memory_info().rss
    started = time.perf_counter()
    _local_result, stats = analyze_p0_with_stats(path)
    remote = observer.observe(
        path, audio_seconds=cast(float, stats["input_duration_seconds"])
    )
    result = CallAnalysisResult.model_validate(remote["observation"])
    stats["pipeline"] = "P4"
    stats["remote"] = remote
    _update_resource_stats(stats, before_rss=before_rss, started=started)
    return result, stats


def analyze_p5_with_stats(
    path: Path,
    observer: OpenRouterAudioObserver,
) -> tuple[CallAnalysisResult, dict[str, object]]:
    """Run Gemini audio plus deterministic P2 evidence with field fusion."""

    process = psutil.Process(os.getpid())
    before_rss = process.memory_info().rss
    started = time.perf_counter()
    local_result, stats = analyze_p2_with_stats(path)
    remote = observer.observe(
        path, audio_seconds=cast(float, stats["input_duration_seconds"])
    )
    remote_result = CallAnalysisResult.model_validate(remote["observation"])
    local_noise = local_result.background_noise_present
    result = remote_result.model_copy(
        update={
            "audio_quality": local_result.audio_quality,
            "long_silence_present": local_result.long_silence_present,
            **(
                {
                    "background_noise_present": True,
                    "background_noise_type": local_result.background_noise_type,
                    "background_noise_severity": local_result.background_noise_severity,
                }
                if local_noise
                else {}
            ),
            **(
                {"speaker_overlap_present": True}
                if local_result.speaker_overlap_present
                else {}
            ),
            **(
                {"emotional_intensity": local_result.emotional_intensity}
                if (
                    remote_result.emotional_intensity == "low"
                    and local_result.emotional_intensity in {"medium", "high"}
                )
                else {}
            ),
        }
    )
    stats["pipeline"] = "P5"
    stats["remote"] = remote
    stats["fusion"] = {
        "audio_quality_owner": "P2_local_dsp",
        "long_silence_owner": "P2_local_vad",
        "noise_owner": "P2_when_signature_present_else_P4",
        "overlap_owner": "P2_when_spectral_proxy_positive_else_P4",
        "intensity_owner": "P2_when_remote_default_is_low_else_P4",
        "semantic_owner": "P4",
    }
    _update_resource_stats(stats, before_rss=before_rss, started=started)
    return result, stats


def analyze_p6_with_stats(
    path: Path,
    observer: OpenRouterAudioObserver,
) -> tuple[CallAnalysisResult, dict[str, object]]:
    """Fuse P5 with the local Whisper/prosody evidence from P3."""

    process = psutil.Process(os.getpid())
    before_rss = process.memory_info().rss
    started = time.perf_counter()
    remote_result, stats = analyze_p5_with_stats(path, observer)
    local_result, local_stats = analyze_p3_with_stats(path)
    use_local_semantics = (
        remote_result.emotional_tone == "neutral"
        and local_result.emotional_tone != "neutral"
    )
    use_local_intensity = (
        remote_result.emotional_intensity == "low"
        and local_result.emotional_intensity in {"medium", "high"}
    )
    use_local_overlap = local_result.speaker_overlap_present
    local_update: dict[str, object] = {}
    if use_local_semantics:
        local_update["emotional_tone"] = local_result.emotional_tone
        local_update["emotional_intensity"] = local_result.emotional_intensity
    elif use_local_intensity:
        local_update["emotional_intensity"] = local_result.emotional_intensity
    if use_local_overlap:
        local_update["speaker_overlap_present"] = True
    result = remote_result.model_copy(
        update=local_update
    )
    stats["pipeline"] = "P6"
    stats["local_specialists"] = {
        "p3_semantic_evidence": local_stats["semantic_evidence"],
        "p3_prosody_evidence": local_stats["prosody_evidence"],
        "p3_transcript": local_stats["transcript"],
        "local_semantics_applied": use_local_semantics,
        "local_intensity_applied": use_local_intensity,
        "local_overlap_applied": use_local_overlap,
    }
    _update_resource_stats(stats, before_rss=before_rss, started=started)
    return result, stats


def analyze_p7_with_stats(
    path: Path,
    audio_observer: OpenRouterAudioObserver,
    text_observer: OpenRouterAudioObserver,
) -> tuple[CallAnalysisResult, dict[str, object]]:
    """Adjudicate P6 evidence with a text-only Gemini 3.6 pass."""

    process = psutil.Process(os.getpid())
    before_rss = process.memory_info().rss
    started = time.perf_counter()
    p6_result, stats = analyze_p6_with_stats(path, audio_observer)
    local_specialists = cast(dict[str, object], stats["local_specialists"])
    transcript = cast(dict[str, object], local_specialists["p3_transcript"])
    evidence = {
        "p6_result": p6_result.model_dump(),
        "dsp": stats["dsp"],
        "vad": stats["vad"],
        "local_semantic_evidence": local_specialists["p3_semantic_evidence"],
        "local_prosody_evidence": local_specialists["p3_prosody_evidence"],
        "local_overlap_evidence": stats["channel_evidence"],
        "local_transcript": str(transcript["text"])[:6000],
    }
    adjudication = text_observer.adjudicate_text(evidence)
    result = CallAnalysisResult.model_validate(adjudication["observation"])
    local_overlap = cast(dict[str, object], stats["channel_evidence"])
    prosody = cast(dict[str, object], local_specialists["p3_prosody_evidence"])
    result = result.model_copy(
        update={
            **(
                {"speaker_overlap_present": True}
                if local_overlap["speaker_overlap_present"] is True
                else {}
            ),
            **(
                {"emotional_intensity": p6_result.emotional_intensity}
                if (
                    result.emotional_intensity == "low"
                    and prosody["mapped_intensity"] in {"medium", "high"}
                )
                else {}
            ),
        }
    )
    stats["pipeline"] = "P7"
    stats["text_adjudication"] = adjudication
    _update_resource_stats(stats, before_rss=before_rss, started=started)
    return result, stats
