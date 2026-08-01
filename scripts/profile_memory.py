"""Profile a smoke candidate's elapsed time and process RSS."""

from __future__ import annotations

import argparse
from pathlib import Path

from autoace.audio.decode import decode_mono_16k
from autoace.audio.dsp import summarize_audio
from autoace.audio.vad import energy_vad
from autoace.evaluation.profiling import measure


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", default="E00")
    parser.add_argument("--audio", type=Path, default=Path("assignment/call_001.ogg"))
    parser.add_argument("--limit-mb", type=float, default=1843.0)
    args = parser.parse_args()

    def run() -> dict[str, object]:
        decoded = decode_mono_16k(args.audio)
        return {
            "dsp": summarize_audio(decoded.samples, decoded.sample_rate_hz),
            "vad": energy_vad(decoded.samples, decoded.sample_rate_hz),
        }

    result = measure(run)
    print({
        "experiment": args.experiment,
        "elapsed_seconds": result.elapsed_seconds,
        "peak_rss_mb": result.peak_rss_mb,
        "memory_gate": result.peak_rss_mb < args.limit_mb,
    })
    return 0 if result.peak_rss_mb < args.limit_mb else 1


if __name__ == "__main__":
    raise SystemExit(main())
