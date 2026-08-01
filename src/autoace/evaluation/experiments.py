"""Persist immutable experiment artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from autoace.contracts import ExperimentRun


def write_experiment(run: ExperimentRun, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{run.run_id}.json"
    if path.exists():
        raise FileExistsError(f"experiment artifact already exists: {path}")
    path.write_text(json.dumps(run.model_dump(mode="json"), indent=2, sort_keys=True) + "\n")
    return path


def write_json_artifact(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"artifact already exists: {path}")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path
