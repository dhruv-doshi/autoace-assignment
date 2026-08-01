from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

import pytest

from autoace.batch import AudioBatch, export_csv
from autoace.security import safe_extract_zip


def make_zip(entries: list[tuple[str, bytes]]) -> io.BytesIO:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, content in entries:
            archive.writestr(name, content)
    stream.seek(0)
    return stream


def test_safe_extract_rejects_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsafe"):
        safe_extract_zip(make_zip([("../escape.wav", b"x")]), tmp_path / "out")


def test_safe_extract_rejects_nested_files(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="root"):
        safe_extract_zip(make_zip([("nested/call.wav", b"x")]), tmp_path / "out")


def test_safe_extract_writes_valid_root_files(tmp_path: Path) -> None:
    output = safe_extract_zip(make_zip([("call.wav", b"audio")]), tmp_path / "out")
    assert output == [tmp_path / "out" / "call.wav"]
    assert output[0].read_bytes() == b"audio"


def test_safe_extract_ignores_macos_metadata_and_accepts_one_wrapping_directory(
    tmp_path: Path,
) -> None:
    output = safe_extract_zip(
        make_zip(
            [
                ("__MACOSX/._call.wav", b"metadata"),
                ("evaluation_batch/call.wav", b"audio"),
            ]
        ),
        tmp_path / "out",
        allow_single_root_directory=True,
    )
    assert output == [tmp_path / "out" / "call.wav"]
    assert output[0].read_bytes() == b"audio"


def test_export_csv_contains_only_required_prediction_fields(tmp_path: Path) -> None:
    batch = AudioBatch(tmp_path)
    batch.add("call.wav")
    analysis = {"emotional_tone": "neutral", "confidence": 0.8}
    batch.mark_complete("call.wav", {"analysis": analysis, "stats": {"peak_rss_mb": 500}})

    rows = list(csv.DictReader(io.StringIO(export_csv(batch))))

    assert rows == [{"name": "call.wav", "result_json": json.dumps(analysis)}]
