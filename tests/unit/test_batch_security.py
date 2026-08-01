from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

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
