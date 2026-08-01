# Quickstart for Implementation

This package is a plan and task handoff. It does not yet contain application
code.

## Read First

1. `docs/audio_pipeline_experiment_plan.md`
2. `.specify/memory/constitution.md`
3. `specs/001-call-audio-analysis/spec.md`
4. `specs/001-call-audio-analysis/plan.md`
5. `specs/001-call-audio-analysis/research.md`
6. `specs/001-call-audio-analysis/data-model.md`
7. `specs/001-call-audio-analysis/contracts/`
8. `specs/001-call-audio-analysis/tasks.md`
9. `specs/001-call-audio-analysis/LUNA_HANDOFF.md`

## Mandatory Python Environment

From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Every Python command must resolve inside `.venv`:

```bash
python -c "import sys; print(sys.executable)"
python -m pytest
```

The executable path must begin with the repository's `.venv`. Never install
project packages globally. FFmpeg and model binaries are native/artifact
dependencies and are recorded separately from `.venv`.

## Safe Execution Order

Run tasks in `tasks.md` from T001 onward.

1. Environment and contracts.
2. Safe batch and evaluation foundation.
3. P0 deterministic baseline.
4. P1–P3 offline model experiments.
5. Cost, cache, privacy, and spend controls.
6. P4–P8 Gemini/hybrid experiments.
7. Winner selection and confidence.
8. Minimal Streamlit application.
9. Holdout, release, and deployment.

Do not start with Streamlit. The UI must expose the frozen winning pipeline,
not influence model selection.

## Inputs Needed During Execution

### Representative labels

The three supplied calls are smoke-only. Credible candidate selection needs
grouped, human-adjudicated AutoAce calls, preferably at least 300 with coverage
across fields. If unavailable, record the limitation and do not claim
hidden-set generalization or calibrated confidence.

### Paid Gemini approval

Before E09–E13:

- approve the exact paid provider project, endpoint, region, and retention
  controls;
- configure credentials outside source control;
- approve and configure a total research-spend cap;
- revalidate model IDs, prices, audio tokenization, thinking billing, and Flex
  behavior.

Without approval, record affected experiments as `blocked`. Never upload real
calls to an unapproved service.

### Local model approval

Before each local model experiment, record:

- code and model license;
- exact source/revision;
- artifact SHA-256;
- runtime and format;
- access/gating terms;
- conversion parity, if using converted weights.

Unclear licensing blocks production eligibility.

## Experiment Commands

The exact CLI is implemented by the corresponding tasks. Its intended shape is:

```bash
python scripts/evaluate.py --experiment E00 --split development
python scripts/evaluate.py --experiment E01 --split development
python scripts/evaluate.py --experiment E09 --split development
python scripts/profile_memory.py --experiment E10 --limit-mb 1843
```

Paid experiment commands must fail before a request if privacy approval,
research cap, cache integrity, or route cost preflight is missing.

## Selection

Hard gates precede accuracy:

- exact contract;
- external route <=$0.003/audio-minute;
- release target <=$0.0024/audio-minute;
- peak RSS <1.8 GB;
- privacy and license approval;
- reproducibility and failure isolation.

Among eligible candidates, choose the best frozen macro-average with emotional
tone as a co-primary metric and no material protected-field regression.

## Release Verification

Expected final commands:

```bash
source .venv/bin/activate
python -m pytest
python scripts/evaluate.py --config configs/release.json --split holdout
python scripts/profile_memory.py --config configs/release.json --limit-mb 1843
python scripts/verify_release.py --manifest release/manifest.json
.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
```

The release is blocked until the model-quality checklist is complete.
