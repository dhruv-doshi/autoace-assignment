"""Optional CPU ASR boundary for Whisper tiny/base experiments."""

from __future__ import annotations

from pathlib import Path


class LocalAsrModel:
    def __init__(self, model_path: Path, model_size: str) -> None:
        if model_size not in {"tiny", "base"}:
            raise ValueError("only tiny and base local ASR challengers are allowed")
        if not model_path.exists():
            raise RuntimeError(f"ASR artifact unavailable: {model_path}")
        self.model_path = model_path
        self.model_size = model_size

    def transcribe(self, audio_path: Path) -> dict[str, object]:
        """Transcribe one file with the pinned CPU Faster-Whisper artifact."""
        try:
            from faster_whisper import WhisperModel
        except ImportError as error:  # pragma: no cover - optional dependency path
            raise RuntimeError("faster-whisper is required for local ASR") from error
        model_root = self.model_path if self.model_path.is_dir() else self.model_path.parent
        model = WhisperModel(str(model_root), device="cpu", compute_type="int8")
        segments, info = model.transcribe(str(audio_path), beam_size=1, vad_filter=False)
        segment_rows = [
            {
                "start_seconds": float(segment.start),
                "end_seconds": float(segment.end),
                "text": segment.text.strip(),
            }
            for segment in segments
        ]
        return {
            "language": str(info.language),
            "duration_seconds": float(info.duration),
            "text": " ".join(row["text"] for row in segment_rows),
            "segments": segment_rows,
            "backend": "faster_whisper_cpu_int8",
            "model_size": self.model_size,
        }
