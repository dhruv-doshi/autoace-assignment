from __future__ import annotations

from pathlib import Path

from autoace.batch import AudioBatch


def test_one_item_failure_does_not_abort_batch(tmp_path: Path) -> None:
    batch = AudioBatch(tmp_path)
    batch.add("good.wav")
    batch.add("bad.wav")
    batch.mark_complete("good.wav", {"ok": True})
    batch.mark_failed("bad.wav", "decode failed")
    assert batch.completed == 1
    assert batch.failed == 1
    assert batch.status == "partial"
