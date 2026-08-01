from __future__ import annotations

import pytest

from autoace.evaluation.datasets import GroupedRecord, grouped_split


def test_grouped_split_never_leaks_group() -> None:
    records = [GroupedRecord(f"item-{i}", f"group-{i // 2}", i) for i in range(12)]
    splits = grouped_split(records, seed=7)
    groups = {name: {record.group for record in values} for name, values in splits.items()}
    assert groups["development"].isdisjoint(groups["calibration"])
    assert groups["development"].isdisjoint(groups["holdout"])
    assert groups["calibration"].isdisjoint(groups["holdout"])


def test_smoke_records_cannot_be_used_as_training() -> None:
    records = [GroupedRecord("call_001.ogg", "smoke", 0, smoke_only=True)]
    with pytest.raises(ValueError, match="smoke"):
        grouped_split(records)
