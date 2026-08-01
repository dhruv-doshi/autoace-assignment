"""Simple production Streamlit dashboard for the P6 hybrid pipeline."""

from __future__ import annotations

import io
import os
import tempfile
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from autoace.batch import AudioBatch, export_csv
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
PIPELINE_DIAGRAM = Path(__file__).resolve().parents[3] / "assets" / "autoace-pipeline.svg"


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


def _format_duration(seconds: float) -> str:
    rounded_seconds = max(0, round(seconds))
    minutes, remaining_seconds = divmod(rounded_seconds, 60)
    return f"{minutes}m {remaining_seconds:02d}s"


def _render_analysis(st: Any, api_key: str) -> None:
    st.subheader("Analyze calls")
    uploads = st.file_uploader(
        "Choose individual audio files or one ZIP",
        type=["zip", *AUDIO_FILE_TYPES],
        accept_multiple_files=True,
        help=(
            "A ZIP may contain audio files at its root or inside one enclosing folder. "
            "labels.csv is not required."
        ),
    )
    if not uploads:
        st.info("Upload one or more calls to begin.")
        return
    if not st.button("Analyse the files", type="primary", use_container_width=True):
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
            try:
                extracted = safe_extract_zip(
                    io.BytesIO(uploads[0].getvalue()),
                    input_root,
                    allow_single_root_directory=True,
                )
            except (ValueError, zipfile.BadZipFile) as error:
                st.error(
                    "Could not read this ZIP file. Put the audio files at the ZIP root or "
                    f"inside one enclosing folder: {error}"
                )
                return
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
        total_seconds = sum(
            _input_duration(cast(dict[str, object], item["stats"]))
            for item in completed_rows
        )
        total_minutes = total_seconds / 60
        total_cost = sum(
            _remote_cost(cast(dict[str, object], item["stats"]))
            for item in completed_rows
        )
        metric_columns = st.columns(4)
        metric_columns[0].metric("Completed", batch.completed)
        metric_columns[1].metric("Failed", batch.failed)
        metric_columns[2].metric("Audio duration", _format_duration(total_seconds))
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

        st.download_button(
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


def _render_docs(st: Any) -> None:
    st.subheader("System documentation")
    st.image(
        str(PIPELINE_DIAGRAM),
        caption=(
            "The production hybrid pipeline combines one remote audio observation "
            "with local checks."
        ),
        use_container_width=True,
    )

    st.markdown(
        """
### Current pipeline

1. Each uploaded clip is normalized to 16 kHz mono WAV with FFmpeg.
2. Gemini 3.5 Flash-Lite receives the normalized audio through OpenRouter.
3. Local DSP, voice-activity detection, overlap/prosody checks, and Faster-Whisper
   provide independent evidence.
4. Deterministic fusion combines that evidence into the required nine-field output schema.

Audio is sent to OpenRouter for the remote observation. The local specialists run on
the dashboard host.
"""
    )

    st.markdown("### Experiment summary and selection")
    st.write(
        "P0–P8 were compared. The current pipeline was selected because it retained "
        "local corrections while staying well below the $0.003 per-audio-minute limit."
    )
    st.dataframe(
        [
            {
                "Pipeline": "P0",
                "Approach": "FFmpeg, DSP, VAD, and rules",
                "Decision": "Zero-cost baseline",
            },
            {
                "Pipeline": "P1",
                "Approach": "P0 plus acoustic and overlap challengers",
                "Decision": "No semantic evidence",
            },
            {
                "Pipeline": "P2",
                "Approach": "P1 plus prosody and emotion evidence",
                "Decision": "Tone still weak",
            },
            {
                "Pipeline": "P3",
                "Approach": "P2 plus Faster-Whisper semantics",
                "Decision": "Best local regression result",
            },
            {
                "Pipeline": "P4",
                "Approach": "Gemini audio only",
                "Decision": "Low cost but variable",
            },
            {
                "Pipeline": "P5",
                "Approach": "Gemini plus local fusion",
                "Decision": "Improved technical fields",
            },
            {
                "Pipeline": "P6",
                "Approach": "P5 plus local overlap, prosody, and ASR specialists",
                "Decision": "Selected",
            },
            {
                "Pipeline": "P7",
                "Approach": "P6 plus Gemini text adjudication",
                "Decision": "Higher cost",
            },
            {
                "Pipeline": "P8",
                "Approach": "Gemini full-audio upper bound",
                "Decision": "Non-schema/truncated responses",
            },
        ],
        use_container_width=True,
        hide_index=True,
    )

    metric_columns = st.columns(4)
    metric_columns[0].metric("Live field accuracy", "95.83%")
    metric_columns[1].metric("Exact files", "2 / 3")
    metric_columns[2].metric("External cost", "$0.000389 / min")
    metric_columns[3].metric("Mean wall time", "7.13 s")
    st.caption(
        "Final live sweep: 891.5 MB peak RSS. A deterministic replay reached 100% "
        "field accuracy and 3/3 exact files using recorded responses."
    )
    st.warning(
        "These results use the three supplied labeled calls, including calibration work. "
        "They are not an estimate of hidden-set accuracy; a new untouched holdout is required."
    )

    st.markdown("### Tuning and calibration")
    st.write(
        "No model weights were fine-tuned. The work focused on prompt and decision-rule "
        "calibration using the three supplied labeled calls."
    )
    st.markdown(
        """
- **Remote prompt tuning:** compared the baseline Gemini instruction with rubric v1.
  The baseline was retained because it achieved 56.25% development field accuracy
  versus 50.00% for rubric v1; its one-call holdout result was 37.5%.
- **Local calibration:** refined background-noise signatures, the long-silence threshold,
  prosody-based intensity, repeated-unanswered-hello semantics, and the
  spectral-polyphony overlap proxy.
- **Fusion tuning:** assigned technical-noise corrections to local evidence while retaining
  the remote audio observation for broader judgement.
"""
    )


def run() -> None:
    import streamlit as st

    st.set_page_config(
        page_title="AutoAce Call Analysis",
        page_icon="🎧",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.title("AutoAce Call Analysis")
    st.caption("Production hybrid · local specialists + Gemini audio")

    with st.sidebar:
        st.subheader("How it works")
        st.write(
            "The current pipeline combines local audio measurements and Whisper semantics "
            "with one cost-capped remote audio observation."
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

    analysis_tab, docs_tab = st.tabs(["Analyse files", "Documentation"])
    with analysis_tab:
        _render_analysis(st, api_key)
    with docs_tab:
        _render_docs(st)
