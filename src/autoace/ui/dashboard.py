"""Simple production Streamlit dashboard for the P6 hybrid pipeline."""

from __future__ import annotations

import io
import os
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from autoace.batch import AudioBatch, export_csv, export_json
from autoace.environment import capture_environment
from autoace.evaluation.experiments import write_json_artifact
from autoace.inference.gemini_audio import OpenRouterAudioObserver
from autoace.pipeline import analyze_p6_with_stats
from autoace.security import safe_extract_zip

AUDIO_FILE_TYPES = (
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
)
AUDIO_SUFFIXES = {f".{extension}" for extension in AUDIO_FILE_TYPES}


def _secret(st: Any, name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value
    try:
        secret = st.secrets.get(name)
    except Exception:
        return None
    return str(secret) if secret else None


def _remote_cost(stats: dict[str, object]) -> float:
    remote = stats.get("remote")
    return float(remote.get("actual_cost_usd", 0.0)) if isinstance(remote, dict) else 0.0


def _input_duration(stats: dict[str, object]) -> float:
    return float(cast(float, stats["input_duration_seconds"]))


def run() -> None:
    import streamlit as st

    st.set_page_config(
        page_title="AutoAce Call Analysis",
        page_icon="🎧",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.title("AutoAce Call Analysis")
    st.caption("Production P6 hybrid · local specialists + Gemini audio")

    with st.sidebar:
        st.subheader("How it works")
        st.write(
            "P6 combines local audio measurements and Whisper semantics with one "
            "cost-capped remote audio observation."
        )
        st.info("Uploaded audio is sent to OpenRouter. Files are processed one at a time.")
        st.caption("Supported: MP4, OGG, WAV, MP3, FLAC, M4A, AAC, OPUS, WEBM and WMA.")

    expected_password = _secret(st, "AUTOACE_DASHBOARD_PASSWORD")
    if not expected_password:
        st.error("Deployment is missing AUTOACE_DASHBOARD_PASSWORD.")
        st.stop()
    password = st.text_input("Access password", type="password", placeholder="Enter password")
    if password != expected_password:
        st.stop()

    api_key = _secret(st, "OPENROUTER_API_KEY")
    if not api_key:
        st.error("Deployment is missing OPENROUTER_API_KEY.")
        st.stop()

    st.subheader("Analyze calls")
    uploads = st.file_uploader(
        "Choose individual audio files or one ZIP",
        type=["zip", *AUDIO_FILE_TYPES],
        accept_multiple_files=True,
        help="A ZIP may contain supported audio files at its root. A labels file is optional.",
    )
    if not uploads:
        st.info("Upload one or more calls to begin.")
        return
    if not st.button("Analyze with P6", type="primary", use_container_width=True):
        return

    run_started = time.perf_counter()
    run_timestamp = datetime.now(UTC)
    with tempfile.TemporaryDirectory(prefix="autoace-") as temporary:
        root = Path(temporary)
        input_root = root / "input"
        zip_uploads = [upload for upload in uploads if upload.name.lower().endswith(".zip")]
        if zip_uploads and len(uploads) != 1:
            st.error("Upload either one ZIP or individual files, not both.")
            return

        if zip_uploads:
            extracted = safe_extract_zip(io.BytesIO(uploads[0].getvalue()), input_root)
            audio_files = [
                file for file in extracted if file.suffix.lower() in AUDIO_SUFFIXES
            ]
            ignored = len(extracted) - len(audio_files)
            if ignored:
                st.caption(f"Ignored {ignored} non-audio file(s) in the ZIP.")
        else:
            input_root.mkdir(parents=True, exist_ok=True)
            audio_files = []
            seen: set[str] = set()
            for upload in uploads:
                filename = Path(upload.name).name
                if (
                    not filename
                    or filename != upload.name
                    or filename in seen
                    or Path(filename).suffix.lower() not in AUDIO_SUFFIXES
                ):
                    st.error(f"Invalid or duplicate audio filename: {upload.name}")
                    return
                seen.add(filename)
                target = input_root / filename
                target.write_bytes(upload.getvalue())
                audio_files.append(target)
        if not audio_files:
            st.error("No supported audio files were found.")
            return

        max_files = int(os.environ.get("AUTOACE_MAX_FILES_PER_RUN", "25"))
        if len(audio_files) > max_files:
            st.error(f"This deployment accepts at most {max_files} files per run.")
            return

        budget_usd = float(os.environ.get("AUTOACE_OPENROUTER_BUDGET_USD", "0.10"))
        observer = OpenRouterAudioObserver(budget_usd=budget_usd, api_key=api_key)
        batch = AudioBatch(root)
        for file in audio_files:
            batch.add(file.name)

        run_files: list[dict[str, object]] = []
        progress = st.progress(0.0, text="Preparing analysis…")
        for index, file in enumerate(audio_files, start=1):
            batch.mark_processing(file.name)
            file_started = time.perf_counter()
            progress.progress(
                (index - 1) / len(audio_files),
                text=f"Analyzing {file.name} ({index}/{len(audio_files)})",
            )
            try:
                analysis, stats = analyze_p6_with_stats(file, observer)
                payload: dict[str, object] = {
                    "analysis": analysis.model_dump(),
                    "stats": stats,
                }
                batch.mark_complete(file.name, payload)
                run_files.append({"name": file.name, "status": "complete", **payload})
            except Exception as error:
                batch.mark_failed(file.name, str(error))
                run_files.append(
                    {
                        "name": file.name,
                        "status": "failed",
                        "error": str(error)[:500],
                        "elapsed_seconds": time.perf_counter() - file_started,
                    }
                )
        progress.progress(1.0, text="Analysis complete")

        completed_rows = [item for item in run_files if item["status"] == "complete"]
        total_minutes = sum(
            _input_duration(cast(dict[str, object], item["stats"])) / 60
            for item in completed_rows
        )
        total_cost = sum(
            _remote_cost(cast(dict[str, object], item["stats"]))
            for item in completed_rows
        )
        metric_columns = st.columns(4)
        metric_columns[0].metric("Completed", batch.completed)
        metric_columns[1].metric("Failed", batch.failed)
        metric_columns[2].metric("Audio minutes", f"{total_minutes:.2f}")
        metric_columns[3].metric("Inference cost", f"${total_cost:.5f}")

        if completed_rows:
            st.subheader("Results")
            table_rows = [
                {
                    "file": item["name"],
                    **cast(dict[str, object], item["analysis"]),
                }
                for item in completed_rows
            ]
            st.dataframe(table_rows, use_container_width=True, hide_index=True)
        if batch.failed:
            st.warning(f"{batch.failed} file(s) failed. Open technical details below.")

        with st.expander("Technical details"):
            st.json(batch.items)
            if total_minutes:
                st.caption(
                    f"Observed external inference cost: "
                    f"${total_cost / total_minutes:.6f} per audio minute."
                )

        download_columns = st.columns(2)
        download_columns[0].download_button(
            "Download JSON",
            export_json(batch),
            "autoace-results.json",
            "application/json",
            use_container_width=True,
        )
        download_columns[1].download_button(
            "Download CSV",
            export_csv(batch),
            "autoace-results.csv",
            "text/csv",
            use_container_width=True,
        )

        run_id = f"p6-{run_timestamp.strftime('%Y%m%dT%H%M%S%fZ')}-{uuid4().hex[:8]}"
        run_stats = {
            "run_id": run_id,
            "pipeline": "P6",
            "experiment": "E11",
            "started_at_utc": run_timestamp.isoformat(),
            "elapsed_seconds": time.perf_counter() - run_started,
            "file_count": len(audio_files),
            "completed_count": batch.completed,
            "failed_count": batch.failed,
            "total_audio_minutes": total_minutes,
            "total_external_cost_usd": total_cost,
            "cost_per_audio_minute_usd": (
                total_cost / total_minutes if total_minutes else 0.0
            ),
            "peak_rss_mb": max(
                (
                    float(
                        cast(
                            float,
                            cast(dict[str, object], item["stats"])["peak_rss_mb"],
                        )
                    )
                    for item in completed_rows
                ),
                default=0.0,
            ),
            "environment": capture_environment(Path("uv.lock")),
            "files": run_files,
        }
        artifact_path = write_json_artifact(
            run_stats,
            Path("artifacts/dashboard_runs") / f"{run_id}.json",
        )
        st.success("P6 analysis finished.")
        st.caption(f"Run evidence recorded at {artifact_path}.")
