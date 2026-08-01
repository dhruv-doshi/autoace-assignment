"""Quality evidence with an explicit deterministic fallback."""

from __future__ import annotations

from pathlib import Path


def quality_proxy(features: dict[str, float]) -> dict[str, object]:
    clipping = features.get("clipping_ratio", 0.0)
    level = features.get("dbfs", -100.0)
    flatness = features.get("spectral_flatness", 0.0)
    if clipping >= 0.01 or level > -1.0:
        quality = "severely_impaired"
    elif clipping >= 0.001 or level < -45.0 or flatness > 0.9:
        quality = "slightly_impaired"
    else:
        quality = "clear"
    return {
        "audio_quality": quality,
        "backend": "dsp_proxy",
        "dnsmos": None,
        "reason": "DNSMOS artifact not admitted; deterministic evidence only",
    }


class DnsMosModel:
    """Optional ONNX DNSMOS adapter; never silently substitutes a score."""

    def __init__(self, model_path: Path) -> None:
        if not model_path.is_file():
            raise RuntimeError(f"DNSMOS artifact unavailable: {model_path}")
        try:
            import onnxruntime as ort
        except ImportError as error:
            raise RuntimeError("onnxruntime is required for DNSMOS") from error
        self._session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])

    def predict(self, _samples: object, _sample_rate_hz: int) -> dict[str, object]:
        raise NotImplementedError(
            "DNSMOS input adapter must be validated against the pinned artifact"
        )
