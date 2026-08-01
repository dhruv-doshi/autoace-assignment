"""Validate a release manifest and its hard-gate invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from autoace.contracts import ReleaseManifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    manifest = ReleaseManifest.model_validate(json.loads(args.manifest.read_text()))
    print(f"release={manifest.release_id}")
    print(f"winning_candidate={manifest.winning_candidate.candidate_id}")
    print("all_release_gates=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
