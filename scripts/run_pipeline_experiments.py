"""Run a labeled comparison of all declared AutoAce pipeline candidates."""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from autoace.contracts import CallAnalysisResult
from autoace.evaluation.experiments import write_json_artifact
from autoace.inference.gemini_audio import OpenRouterAudioObserver
from autoace.pipeline import (
    analyze_p0_with_stats,
    analyze_p1_with_stats,
    analyze_p2_with_stats,
    analyze_p3_with_stats,
    analyze_p4_with_stats,
    analyze_p5_with_stats,
    analyze_p6_with_stats,
    analyze_p7_with_stats,
)

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

LocalRunner = Callable[[Path], tuple[CallAnalysisResult, dict[str, object]]]


def _labels(path: Path) -> dict[str, dict[str, object]]:
    with path.open(newline="") as handle:
        return {
            row["name"]: json.loads(row["result_json"])
            for row in csv.DictReader(handle)
        }


def _remote_cost(stats: dict[str, object]) -> float:
    total = 0.0
    for key in ("remote", "text_adjudication"):
        value = stats.get(key)
        if isinstance(value, dict):
            total += float(value.get("actual_cost_usd", 0.0))
    return total


def _summarize(
    candidate_id: str,
    rows: list[dict[str, object]],
    labels: dict[str, dict[str, object]],
) -> dict[str, object]:
    completed = [row for row in rows if row["status"] == "complete"]
    field_metrics: dict[str, float] = {}
    for field in FIELDS:
        correct = 0
        for row in completed:
            analysis = cast(dict[str, object], row["analysis"])
            label = labels[cast(str, row["file"])]
            correct += analysis[field] == label[field]
        field_metrics[field] = correct / len(completed) if completed else 0.0
    exact = 0
    audio_minutes = 0.0
    total_cost = 0.0
    elapsed_seconds = 0.0
    peak_rss_mb = 0.0
    for row in completed:
        analysis = cast(dict[str, object], row["analysis"])
        label = labels[cast(str, row["file"])]
        exact += all(analysis[field] == label[field] for field in FIELDS)
        stats = cast(dict[str, object], row["stats"])
        audio_minutes += float(cast(float, stats["input_duration_seconds"])) / 60
        total_cost += float(cast(float, row["cost_usd"]))
        elapsed_seconds += float(cast(float, stats["elapsed_seconds"]))
        peak_rss_mb = max(peak_rss_mb, float(cast(float, stats["peak_rss_mb"])))
    return {
        "candidate_id": candidate_id,
        "status": "complete" if len(completed) == len(rows) else "partial_or_failed",
        "file_count": len(rows),
        "completed_count": len(completed),
        "field_accuracy": field_metrics,
        "average_field_accuracy": sum(field_metrics.values()) / len(field_metrics),
        "exact_match_rate": exact / len(completed) if completed else 0.0,
        "total_audio_minutes": audio_minutes,
        "total_cost_usd": total_cost,
        "cost_per_audio_minute_usd": total_cost / audio_minutes if audio_minutes else 0.0,
        "mean_elapsed_seconds": elapsed_seconds / len(completed) if completed else 0.0,
        "peak_rss_mb": peak_rss_mb,
        "files": rows,
    }


def _run_candidate(
    candidate_id: str,
    files: list[Path],
    labels: dict[str, dict[str, object]],
) -> dict[str, object]:
    local_runners: dict[str, LocalRunner] = {
        "P0": analyze_p0_with_stats,
        "P1": analyze_p1_with_stats,
        "P2": analyze_p2_with_stats,
        "P3": analyze_p3_with_stats,
    }
    audio_observer: OpenRouterAudioObserver | None = None
    text_observer: OpenRouterAudioObserver | None = None
    if candidate_id in {"P4", "P5", "P6", "P7"}:
        audio_observer = OpenRouterAudioObserver(budget_usd=0.05)
    if candidate_id == "P7":
        text_observer = OpenRouterAudioObserver(
            model="google/gemini-3.6-flash", budget_usd=0.05, max_output_tokens=1024
        )

    rows: list[dict[str, object]] = []
    for path in files:
        try:
            if candidate_id in local_runners:
                result, stats = local_runners[candidate_id](path)
            elif candidate_id == "P4":
                assert audio_observer is not None
                result, stats = analyze_p4_with_stats(path, audio_observer)
            elif candidate_id == "P5":
                assert audio_observer is not None
                result, stats = analyze_p5_with_stats(path, audio_observer)
            elif candidate_id == "P6":
                assert audio_observer is not None
                result, stats = analyze_p6_with_stats(path, audio_observer)
            elif candidate_id == "P7":
                assert audio_observer is not None and text_observer is not None
                result, stats = analyze_p7_with_stats(path, audio_observer, text_observer)
            else:
                raise RuntimeError(
                    "P8 is failed: Gemini 3.6 audio has not returned schema-valid JSON."
                )
            rows.append(
                {
                    "file": path.name,
                    "status": "complete",
                    "analysis": result.model_dump(),
                    "stats": stats,
                    "cost_usd": _remote_cost(stats),
                }
            )
        except Exception as error:
            rows.append({"file": path.name, "status": "failed", "error": str(error)})
    return _summarize(candidate_id, rows, labels)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("assignment"))
    parser.add_argument("--labels", type=Path, default=Path("assignment/labels.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/experiments"))
    parser.add_argument(
        "--candidates",
        nargs="+",
        choices=[f"P{index}" for index in range(9)],
        default=[f"P{index}" for index in range(9)],
    )
    args = parser.parse_args()

    labels = _labels(args.labels)
    files = sorted(args.input_dir.glob("*.ogg"))
    report = {
        "run_at_utc": datetime.now(UTC).isoformat(),
        "dataset": str(args.input_dir),
        "candidates": [
            _run_candidate(candidate_id, files, labels)
            for candidate_id in args.candidates
        ],
    }
    name = f"pipeline-sweep-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    path = write_json_artifact(report, args.output_dir / name)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
