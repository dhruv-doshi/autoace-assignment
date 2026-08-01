"""Replay recorded remote observations through the current deterministic fusion code."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from autoace.evaluation.experiments import write_json_artifact
from autoace.inference.gemini_audio import OpenRouterAudioObserver
from autoace.pipeline import analyze_p5_with_stats, analyze_p6_with_stats, analyze_p7_with_stats

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


class RecordedObserver:
    """Minimal observer that returns a prior model response without a network call."""

    def __init__(
        self, audio: dict[str, dict[str, object]], text: dict[str, dict[str, object]]
    ) -> None:
        self.audio = audio
        self.text = text

    def observe(self, path: Path, *, audio_seconds: float) -> dict[str, object]:
        del audio_seconds
        return {"observation": self.audio[path.name], "actual_cost_usd": 0.0}

    def adjudicate_text(self, evidence: dict[str, object]) -> dict[str, object]:
        transcript = str(evidence["local_transcript"])
        if "Spanish, please" in transcript:
            name = "call_002.ogg"
        elif "appointment for my car" in transcript:
            name = "call_003.ogg"
        else:
            name = "call_001.ogg"
        return {"observation": self.text[name], "actual_cost_usd": 0.0}


def _rows(report: dict[str, object], candidate: str) -> list[dict[str, object]]:
    candidates = report["candidates"]
    assert isinstance(candidates, list)
    for item in candidates:
        if isinstance(item, dict) and item.get("candidate_id") == candidate:
            rows = item["files"]
            assert isinstance(rows, list)
            return [row for row in rows if isinstance(row, dict)]
    raise ValueError(f"candidate {candidate} is absent from source artifact")


def _labels(path: Path) -> dict[str, dict[str, object]]:
    with path.open(newline="") as handle:
        return {row["name"]: json.loads(row["result_json"]) for row in csv.DictReader(handle)}


def _summary(
    candidate: str, rows: list[dict[str, object]], labels: dict[str, dict[str, object]]
) -> dict[str, object]:
    correct_by_field = {field: 0 for field in FIELDS}
    exact = 0
    for row in rows:
        analysis = row["analysis"]
        assert isinstance(analysis, dict)
        label = labels[str(row["file"])]
        for field in FIELDS:
            correct_by_field[field] += analysis[field] == label[field]
        exact += all(analysis[field] == label[field] for field in FIELDS)
    count = len(rows)
    return {
        "candidate_id": candidate,
        "file_count": count,
        "average_field_accuracy": sum(correct_by_field.values()) / (count * len(FIELDS)),
        "exact_match_rate": exact / count,
        "field_accuracy": {field: value / count for field, value in correct_by_field.items()},
        "files": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-source", type=Path, required=True)
    parser.add_argument("--text-source", type=Path, required=True)
    parser.add_argument("--labels", type=Path, default=Path("assignment/labels.csv"))
    parser.add_argument("--input-dir", type=Path, default=Path("assignment"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/experiments"))
    args = parser.parse_args()

    audio_report = json.loads(args.audio_source.read_text())
    text_report = json.loads(args.text_source.read_text())
    audio = {
        str(row["file"]): dict(cast(dict[str, object], row["analysis"]))
        for row in _rows(audio_report, "P4")
    }
    text: dict[str, dict[str, object]] = {}
    for row in _rows(text_report, "P7"):
        stats = cast(dict[str, object], row["stats"])
        adjudication = cast(dict[str, object], stats["text_adjudication"])
        text[str(row["file"])] = dict(cast(dict[str, object], adjudication["observation"]))
    labels = _labels(args.labels)
    rows_by_candidate: dict[str, list[dict[str, object]]] = {"P5": [], "P6": [], "P7": []}
    for path in sorted(args.input_dir.glob("*.ogg")):
        observer = RecordedObserver(audio, text)
        replay_observer = cast(OpenRouterAudioObserver, observer)
        results = {
            "P5": analyze_p5_with_stats(path, replay_observer),
            "P6": analyze_p6_with_stats(path, replay_observer),
            "P7": analyze_p7_with_stats(path, replay_observer, replay_observer),
        }
        for candidate, (result, stats) in results.items():
            rows_by_candidate[candidate].append(
                {
                    "file": path.name,
                    "analysis": result.model_dump(),
                    "stats": stats,
                    "replayed_remote_observations": True,
                    "replay_cost_usd": 0.0,
                }
            )
    report = {
        "run_at_utc": datetime.now(UTC).isoformat(),
        "mode": "offline_replay_no_audio_upload_or_provider_call",
        "audio_source": str(args.audio_source),
        "text_source": str(args.text_source),
        "candidates": [
            _summary(candidate, rows, labels)
            for candidate, rows in rows_by_candidate.items()
        ],
    }
    output = args.output_dir / f"fusion-replay-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    print(write_json_artifact(report, output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
