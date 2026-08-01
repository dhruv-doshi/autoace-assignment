from __future__ import annotations

import io

import pytest

from autoace.batch import parse_manifest, validate_manifest_files


def test_manifest_accepts_quoted_json_and_empty_hidden_labels() -> None:
    text = 'name,result_json\ncall.wav,"{\"\"emotional_tone\"\":\"\"neutral\"\"}"\nhidden.wav,\n'
    rows = parse_manifest(io.StringIO(text))
    assert rows[0].name == "call.wav"
    assert rows[0].result_json == '{"emotional_tone":"neutral"}'
    assert rows[1].result_json is None


@pytest.mark.parametrize(
    "text",
    [
        "result_json\n{}\n",
        "name,result_json\na.wav,\na.wav,\n",
        "name,result_json\n../a.wav,\n",
    ],
)
def test_manifest_rejects_invalid_rows(text: str) -> None:
    with pytest.raises(ValueError):
        parse_manifest(io.StringIO(text))


def test_manifest_file_matching_is_reported() -> None:
    text = "name,result_json\na.wav,\nb.wav,\n"
    rows = parse_manifest(io.StringIO(text))
    report = validate_manifest_files(rows, ["a.wav", "c.wav"])
    assert report.missing == ["b.wav"]
    assert report.unmatched == ["c.wav"]
