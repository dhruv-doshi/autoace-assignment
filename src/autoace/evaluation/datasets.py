"""Grouped dataset definitions and leakage-safe splits."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class GroupedRecord:
    item_id: str
    group: str
    ordinal: int
    smoke_only: bool = False


def grouped_split(
    records: list[GroupedRecord],
    *,
    seed: int = 0,
    development_fraction: float = 0.6,
    calibration_fraction: float = 0.2,
) -> dict[str, list[GroupedRecord]]:
    if any(record.smoke_only for record in records):
        raise ValueError("smoke-only records cannot enter evaluation splits")
    groups = sorted({record.group for record in records})
    if len(groups) < 3:
        raise ValueError("at least three groups are required for grouped splits")
    ordered = sorted(
        groups,
        key=lambda group: hashlib.sha256(f"{seed}:{group}".encode()).hexdigest(),
    )
    dev_count = max(1, int(len(ordered) * development_fraction))
    cal_count = max(1, int(len(ordered) * calibration_fraction))
    development_groups = set(ordered[:dev_count])
    calibration_groups = set(ordered[dev_count:dev_count + cal_count])
    holdout_groups = set(ordered[dev_count + cal_count:])
    result: dict[str, list[GroupedRecord]] = {
        "development": [],
        "calibration": [],
        "holdout": [],
    }
    for record in records:
        if record.group in development_groups:
            result["development"].append(record)
        elif record.group in calibration_groups:
            result["calibration"].append(record)
        elif record.group in holdout_groups:
            result["holdout"].append(record)
    return result
