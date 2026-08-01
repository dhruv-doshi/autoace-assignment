"""Download and verify the pinned P6 production model."""

from pathlib import Path

from autoace.models import ensure_whisper_model


def main() -> int:
    target = ensure_whisper_model(Path("models/faster-whisper/tiny"))
    print(f"verified_model={target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
