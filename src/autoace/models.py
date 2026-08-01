"""Pinned production-model bootstrap and integrity verification."""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path

WHISPER_REPOSITORY = "Systran/faster-whisper-tiny"
WHISPER_REVISION = "d90ca5fe260221311c53c58e660288d3deb8d356"
WHISPER_MODEL_SHA256 = "dcb76c6586fc06cbdac6dd21f14cfd129cc4cdd9dce19bf4ffa62e59cbe6e6d1"
WHISPER_FILES = ("config.json", "model.bin", "tokenizer.json", "vocabulary.txt")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache(maxsize=4)
def ensure_whisper_model(target: Path) -> Path:
    """Ensure the pinned model exists and reject any hash mismatch."""

    model_file = target / "model.bin"
    if model_file.is_file() and _sha256(model_file) == WHISPER_MODEL_SHA256:
        return target
    try:
        from huggingface_hub import snapshot_download
    except ImportError as error:  # pragma: no cover - dependency contract
        raise RuntimeError("huggingface-hub is required to bootstrap the ASR model") from error
    target.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=WHISPER_REPOSITORY,
        revision=WHISPER_REVISION,
        local_dir=target,
        allow_patterns=list(WHISPER_FILES),
    )
    if not model_file.is_file() or _sha256(model_file) != WHISPER_MODEL_SHA256:
        raise RuntimeError("downloaded Whisper model failed SHA-256 verification")
    return target
