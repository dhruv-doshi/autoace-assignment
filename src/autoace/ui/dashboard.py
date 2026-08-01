"""Minimal Streamlit UI for the local P0 baseline."""

from __future__ import annotations

import io
import os
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from autoace.batch import (
    AudioBatch,
    export_csv,
    export_json,
    parse_manifest,
    validate_manifest_files,
)
from autoace.environment import capture_environment
from autoace.evaluation.experiments import write_json_artifact
from autoace.inference.gemini_audio import OpenRouterAudioObserver
from autoace.pipeline import (
    analyze_p0_with_stats,
    analyze_p1_with_stats,
    analyze_p2_with_stats,
    analyze_p3_with_stats,
    analyze_p4_with_stats,
    analyze_p5_with_stats,
    analyze_p6_with_stats,
    analyze_p7_with_stats,
)
from autoace.security import safe_extract_zip

AUDIO_FILE_TYPES = [
    "mp4",
    "ogg",
    "wav",
    "mp3",
    "flac",
    "m4a",
    "aac",
    "opus",
    "webm",
    "wma",
]


def run() -> None:
    import streamlit as st

    st.set_page_config(page_title="AutoAce Call Analysis", layout="wide")
    st.title("AutoAce Call Analysis")
    st.caption("P0 local CPU baseline — experiment winner not selected yet")
    expected_password = os.environ.get("AUTOACE_DASHBOARD_PASSWORD")
    if not expected_password:
        st.error("AUTOACE_DASHBOARD_PASSWORD is not configured.")
        return
    password = st.text_input("Password", type="password")
    if password != expected_password:
        st.stop()
    uploads = st.file_uploader(
        "Upload an evaluation ZIP or individual audio files",
        type=["zip", *AUDIO_FILE_TYPES],
        accept_multiple_files=True,
        help=(
            "ZIP uploads must include a root-level labels.csv. Individual files "
            "can be analyzed without a manifest."
        ),
    )
    if not uploads:
        return
    pipeline = st.selectbox(
        "Pipeline",
        options=(
            "P0 — deterministic local",
            "P1 — local acoustic evidence",
            "P2 — local prosody evidence",
            "P3 — local Whisper semantics",
            "P4 — Gemini audio",
            "P5 — Gemini audio + P0 fusion",
            "P6 — Gemini + local specialists",
            "P7 — Gemini text adjudication",
        ),
        help="P4–P7 use OpenRouter and require OPENROUTER_API_KEY.",
    )
    if pipeline[:2] in {"P4", "P5", "P6", "P7"}:
        st.warning("This pipeline sends uploaded audio to OpenRouter for analysis.")
    if not st.button(f"Run {pipeline}"):
        return
    run_started = time.perf_counter()
    run_timestamp = datetime.now(UTC)
    with tempfile.TemporaryDirectory(prefix="autoace-") as temporary:
        root = Path(temporary)
        input_root = root / "input"
        zip_uploads = [upload for upload in uploads if upload.name.lower().endswith(".zip")]
        if zip_uploads and len(uploads) != 1:
            st.error("Upload either one evaluation ZIP or individual audio files, not both.")
            return

        if zip_uploads:
            files = safe_extract_zip(io.BytesIO(uploads[0].getvalue()), input_root)
            manifest_path = next(
                (file for file in files if file.name.lower() == "labels.csv"), None
            )
            if manifest_path is None:
                st.error("ZIP must contain a root-level labels.csv manifest.")
                return
            with manifest_path.open(newline="") as manifest_file:
                manifest_rows = parse_manifest(manifest_file)
            audio_files = [file for file in files if file.name != manifest_path.name]
            report = validate_manifest_files(manifest_rows, [file.name for file in audio_files])
            if report.missing or report.unmatched:
                st.error(
                    f"Manifest mismatch. Missing={report.missing}; unmatched={report.unmatched}"
                )
                return
        else:
            input_root.mkdir(parents=True, exist_ok=True)
            audio_files = []
            for upload in uploads:
                filename = Path(upload.name).name
                if not filename or filename != upload.name:
                    st.error(f"Invalid upload filename: {upload.name}")
                    return
                target = input_root / filename
                target.write_bytes(upload.getvalue())
                audio_files.append(target)

        batch = AudioBatch(root)
        run_files: list[dict[str, object]] = []
        remote_observer = (
            OpenRouterAudioObserver(budget_usd=0.05 if pipeline.startswith("P7") else 0.10)
            if pipeline[:2] in {"P4", "P5", "P6", "P7"}
            else None
        )
        text_observer = (
            OpenRouterAudioObserver(
                model="google/gemini-3.6-flash", budget_usd=0.05, max_output_tokens=1024
            )
            if pipeline.startswith("P7")
            else None
        )
        for file in audio_files:
            batch.add(file.name)
        progress = st.progress(0.0)
        for index, file in enumerate(audio_files, start=1):
            batch.mark_processing(file.name)
            file_started = time.perf_counter()
            try:
                if pipeline.startswith("P4"):
                    assert remote_observer is not None
                    analysis, stats = analyze_p4_with_stats(file, remote_observer)
                elif pipeline.startswith("P5"):
                    assert remote_observer is not None
                    analysis, stats = analyze_p5_with_stats(file, remote_observer)
                elif pipeline.startswith("P6"):
                    assert remote_observer is not None
                    analysis, stats = analyze_p6_with_stats(file, remote_observer)
                elif pipeline.startswith("P7"):
                    assert remote_observer is not None and text_observer is not None
                    analysis, stats = analyze_p7_with_stats(
                        file, remote_observer, text_observer
                    )
                elif pipeline.startswith("P3"):
                    analysis, stats = analyze_p3_with_stats(file)
                elif pipeline.startswith("P2"):
                    analysis, stats = analyze_p2_with_stats(file)
                elif pipeline.startswith("P1"):
                    analysis, stats = analyze_p1_with_stats(file)
                else:
                    analysis, stats = analyze_p0_with_stats(file)
                payload: dict[str, object] = {"analysis": analysis.model_dump(), "stats": stats}
                batch.mark_complete(file.name, payload)
                run_files.append({"name": file.name, "status": "complete", **payload})
            except Exception as error:  # isolate one malformed file
                batch.mark_failed(file.name, str(error))
                run_files.append(
                    {
                        "name": file.name,
                        "status": "failed",
                        "error": str(error)[:500],
                        "elapsed_seconds": time.perf_counter() - file_started,
                    }
                )
            progress.progress(index / len(audio_files))
        st.json(batch.items)
        st.download_button("Download JSON", export_json(batch), "results.json", "application/json")
        st.download_button("Download CSV", export_csv(batch), "results.csv", "text/csv")

        run_id = (
            f"{pipeline[:2].lower()}-{run_timestamp.strftime('%Y%m%dT%H%M%S%fZ')}-"
            f"{uuid4().hex[:8]}"
        )
        run_stats = {
            "run_id": run_id,
            "pipeline": pipeline[:2],
            "experiment": (
                "E01" if pipeline.startswith("P1")
                else "E05" if pipeline.startswith("P2")
                else "E07" if pipeline.startswith("P3")
                else "E09" if pipeline.startswith("P4")
                else "E10" if pipeline.startswith("P5")
                else "E11" if pipeline.startswith("P6")
                else "E12" if pipeline.startswith("P7")
                else "E00"
            ),
            "started_at_utc": run_timestamp.isoformat(),
            "elapsed_seconds": time.perf_counter() - run_started,
            "file_count": len(audio_files),
            "completed_count": batch.completed,
            "failed_count": batch.failed,
            "peak_rss_mb": max(
                (
                    float(cast(float, cast(dict[str, object], item["stats"])["peak_rss_mb"]))
                    for item in run_files
                    if "stats" in item
                ),
                default=0.0,
            ),
            "environment": capture_environment(Path("uv.lock")),
            "files": run_files,
        }
        artifact_path = write_json_artifact(
            run_stats,
            Path("artifacts/dashboard_runs") / f"{run_stats['run_id']}.json",
        )
        st.caption(f"Recorded run stats: {artifact_path}")
