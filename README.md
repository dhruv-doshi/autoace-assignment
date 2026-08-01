# AutoAce call-audio analysis

AutoAce is a Streamlit application that analyzes customer-service calls with the
single selected production candidate, **P6**. P6 combines one cost-capped Gemini
audio observation through OpenRouter with local DSP, overlap, prosody, and
Faster-Whisper semantic evidence.

The executable product on `main` and `prod` contains only P6. The complete
P0–P8 research implementation is preserved on `archive/all-pipelines`. All
experiment results and the selection rationale remain versioned on the
production branches.

## Run locally

Requirements: Python 3.12 and FFmpeg.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python scripts/download_models.py

export AUTOACE_DASHBOARD_PASSWORD="choose-a-strong-password"
export OPENROUTER_API_KEY="your-openrouter-key"
streamlit run app.py
```

The dashboard accepts individual MP4, OGG, WAV, MP3, FLAC, M4A, AAC, OPUS,
WEBM, and WMA files, or one root-level ZIP containing those formats.

## Validate

```bash
source .venv/bin/activate
pytest -q
ruff check src tests scripts
mypy src tests scripts
```

## Deploy

The repository includes:

- a production `Dockerfile`;
- a Render Blueprint targeting the 2 GB Standard instance;
- Streamlit Community Cloud dependency files;
- health checks and bounded runtime configuration;
- pinned model bootstrap with SHA-256 verification.

See [deployment.md](docs/deployment.md) for secrets, platform choices, costs,
and release steps. See [experiments.md](docs/experiments.md) for the complete
pipeline record and limitations.
