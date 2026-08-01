"""Optional local emotion-model boundaries with no unvalidated mapping."""

from __future__ import annotations

from pathlib import Path


class LocalEmotionModel:
    def __init__(self, model_path: Path, *, license_name: str) -> None:
        if not model_path.is_file():
            raise RuntimeError(f"local emotion artifact unavailable: {model_path}")
        if not license_name.strip():
            raise RuntimeError("local emotion license must be recorded")
        self.model_path = model_path
        self.license_name = license_name

    def predict(self, _samples: object, _sample_rate_hz: int) -> dict[str, object]:
        raise NotImplementedError(
            "local emotion inference requires a validated domain mapping and artifact"
        )
