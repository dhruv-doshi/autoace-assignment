from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import cast

from autoace.inference.gemini_audio import OpenRouterAudioObserver
from autoace.pipeline import analyze_p6_with_stats

FIELDS = (
    "emotional_tone",
    "emotional_intensity",
    "background_noise_present",
    "background_noise_type",
    "background_noise_severity",
    "audio_quality",
    "speaker_overlap_present",
    "long_silence_present",
)


class NeutralRemoteObserver:
    def observe(self, _path: Path, *, audio_seconds: float) -> dict[str, object]:
        return {
            "observation": {
                "emotional_tone": "neutral",
                "emotional_intensity": "low",
                "background_noise_present": False,
                "background_noise_type": "",
                "background_noise_severity": "none",
                "audio_quality": "clear",
                "speaker_overlap_present": False,
                "long_silence_present": False,
                "confidence": 0.9,
            },
            "actual_cost_usd": audio_seconds * 0.0007 / 60,
            "prompt_version": "test",
        }


def test_production_p6_matches_supplied_regression_corpus() -> None:
    with Path("assignment/labels.csv").open(newline="") as handle:
        labels = {
            row["name"]: json.loads(row["result_json"])
            for row in csv.DictReader(handle)
        }
    observer = cast(OpenRouterAudioObserver, NeutralRemoteObserver())
    for name, expected in labels.items():
        result, stats = analyze_p6_with_stats(Path("assignment") / name, observer)
        payload = result.model_dump()
        assert all(payload[field] == expected[field] for field in FIELDS)
        assert stats["pipeline"] == "P6"
        assert stats["pipeline_revision"] == "p6-production-v1"
