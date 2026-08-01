# AutoAce call-audio analysis

This repository contains the experiment-first implementation for the call-audio
analysis dashboard. The currently executable path is the deterministic P0 local
CPU baseline; it does not upload audio or make paid API calls. It is intentionally
not labelled as the final accuracy winner until representative labelled data is
available and the registered experiments pass their gates.

## Run locally

```bash
./.venv/bin/python scripts/verify_environment.py
./.venv/bin/pytest -q
./.venv/bin/streamlit run app.py
```

Set `AUTOACE_DASHBOARD_PASSWORD` before starting Streamlit. Upload a ZIP with a
root-level `labels.csv` and audio files whose names match the manifest. The UI
extracts into a temporary directory, processes files sequentially, isolates
failures, and offers JSON/CSV downloads.

## Experiments

Run the smoke baseline with:

```bash
./.venv/bin/python scripts/evaluate.py --experiment E00 --split smoke
```

Experiments requiring unavailable model artifacts, representative labels, or
explicit remote approval must be recorded as blocked, never replaced with
invented metrics:

```bash
./.venv/bin/python scripts/record_blocked_experiment.py \
  --experiment E09 \
  --reason "remote privacy approval and research budget are not configured"
```

See [the Luna handoff](specs/001-call-audio-analysis/LUNA_HANDOFF.md),
[the implementation log](docs/implementation-log.md), and the experiment plan
for the remaining gated work.
