"""Manifest validation, per-file batch state, and exports."""

from __future__ import annotations

import csv
import io
import json
import pathlib
from dataclasses import dataclass, field
from typing import TextIO


@dataclass(frozen=True)
class ManifestRow:
    name: str
    result_json: str | None = None


@dataclass(frozen=True)
class ManifestFileReport:
    missing: list[str]
    unmatched: list[str]


def parse_manifest(source: TextIO | io.StringIO) -> list[ManifestRow]:
    reader = csv.DictReader(source)
    if not reader.fieldnames or "name" not in reader.fieldnames:
        raise ValueError("manifest requires a name column")
    allowed = {"name", "result_json"}
    unexpected = set(reader.fieldnames) - allowed
    if unexpected:
        raise ValueError(f"unexpected manifest columns: {sorted(unexpected)}")
    rows: list[ManifestRow] = []
    seen: set[str] = set()
    for raw in reader:
        name = (raw.get("name") or "").strip()
        if not name or pathlib.PurePath(name).name != name or name in (".", ".."):
            raise ValueError(f"unsafe or empty manifest name: {name!r}")
        if name in seen:
            raise ValueError(f"duplicate manifest name: {name}")
        seen.add(name)
        value = raw.get("result_json")
        rows.append(ManifestRow(name=name, result_json=value or None))
    if not rows:
        raise ValueError("manifest must contain at least one row")
    return rows


def validate_manifest_files(rows: list[ManifestRow], filenames: list[str]) -> ManifestFileReport:
    expected = {row.name for row in rows}
    actual = set(filenames)
    return ManifestFileReport(
        missing=sorted(expected - actual),
        unmatched=sorted(actual - expected),
    )


@dataclass
class BatchItem:
    name: str
    status: str = "queued"
    result: dict[str, object] | None = None
    error: str | None = None


@dataclass
class AudioBatch:
    root: pathlib.Path
    items: dict[str, BatchItem] = field(default_factory=dict)

    def add(self, name: str) -> None:
        if name in self.items:
            raise ValueError(f"duplicate item: {name}")
        self.items[name] = BatchItem(name=name)

    def mark_processing(self, name: str) -> None:
        self.items[name].status = "processing"

    def mark_complete(self, name: str, result: dict[str, object]) -> None:
        self.items[name].status = "complete"
        self.items[name].result = result
        self.items[name].error = None

    def mark_failed(self, name: str, error: str) -> None:
        self.items[name].status = "failed"
        self.items[name].error = error[:500]

    @property
    def completed(self) -> int:
        return sum(item.status == "complete" for item in self.items.values())

    @property
    def failed(self) -> int:
        return sum(item.status == "failed" for item in self.items.values())

    @property
    def processing(self) -> int:
        return sum(item.status == "processing" for item in self.items.values())

    @property
    def status(self) -> str:
        if self.processing:
            return "processing"
        if self.failed and self.completed:
            return "partial"
        if self.failed and self.failed == len(self.items):
            return "failed"
        if self.completed == len(self.items) and self.items:
            return "complete"
        return "ready"


def export_json(batch: AudioBatch) -> str:
    rows = [
        {"name": item.name, "result": item.result, "error": item.error}
        for item in batch.items.values()
    ]
    return json.dumps(
        rows,
        indent=2,
        sort_keys=True,
    )


def export_csv(batch: AudioBatch) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["name", "result_json"])
    writer.writeheader()
    for item in batch.items.values():
        result = item.result or {}
        analysis = result.get("analysis") if isinstance(result, dict) else None
        writer.writerow(
            {
                "name": item.name,
                "result_json": json.dumps(analysis) if isinstance(analysis, dict) else "",
            }
        )
    return output.getvalue()
