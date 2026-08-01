"""Tune one P4 prompt suffix on a development split, then score a holdout file."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from autoace.evaluation.experiments import write_json_artifact
from autoace.inference.gemini_audio import OpenRouterAudioObserver
from autoace.pipeline import analyze_p4_with_stats

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

PROMPTS = {
    "baseline": "",
    "rubric_v1": (
        "Use the stated label categories precisely. Treat repeated questioning, impatience, "
        "or agitation from the customer as upset or frustrated when audible. Use medium or high "
        "intensity only when the customer vocal delivery supports it. Detect television, music, "
        "or static as background noise when clearly audible, and mark overlap only for genuinely "
        "simultaneous speakers."
    ),
}


def _labels(path: Path) -> dict[str, dict[str, object]]:
    with path.open(newline="") as handle:
        return {
            row["name"]: json.loads(row["result_json"])
            for row in csv.DictReader(handle)
        }


def _score(prediction: dict[str, object], label: dict[str, object]) -> float:
    return sum(prediction[field] == label[field] for field in FIELDS) / len(FIELDS)


def _run(paths: list[Path], labels: dict[str, dict[str, object]], prompt: str) -> dict[str, object]:
    observer = OpenRouterAudioObserver(budget_usd=0.05, instructions=prompt)
    rows = []
    for path in paths:
        result, stats = analyze_p4_with_stats(path, observer)
        prediction = result.model_dump()
        remote = cast(dict[str, object], stats["remote"])
        rows.append(
            {
                "file": path.name,
                "prediction": prediction,
                "field_accuracy": _score(prediction, labels[path.name]),
                "cost_usd": remote["actual_cost_usd"],
            }
        )
    return {
        "mean_field_accuracy": (
            sum(float(cast(float, row["field_accuracy"])) for row in rows) / len(rows)
        ),
        "total_cost_usd": observer.spent_usd,
        "files": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("assignment"))
    parser.add_argument("--labels", type=Path, default=Path("assignment/labels.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/experiments"))
    args = parser.parse_args()
    labels = _labels(args.labels)
    development = [args.input_dir / "call_001.ogg", args.input_dir / "call_002.ogg"]
    holdout = [args.input_dir / "call_003.ogg"]

    development_results = {
        name: _run(development, labels, prompt) for name, prompt in PROMPTS.items()
    }
    selected = max(
        PROMPTS,
        key=lambda name: (development_results[name]["mean_field_accuracy"], name == "baseline"),
    )
    holdout_result = _run(holdout, labels, PROMPTS[selected])
    report = {
        "candidate_id": "P4",
        "development_files": [path.name for path in development],
        "holdout_files": [path.name for path in holdout],
        "prompt_results": development_results,
        "selected_prompt": selected,
        "holdout_result": holdout_result,
        "warning": "Two development files are insufficient to freeze a production prompt.",
    }
    name = f"p4-prompt-tune-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    path = write_json_artifact(report, args.output_dir / name)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
