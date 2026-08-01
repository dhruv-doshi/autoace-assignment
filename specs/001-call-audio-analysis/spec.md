# Feature Specification: Cost-Bounded Call Audio Analysis

**Feature Branch**: `001-call-audio-analysis`

**Created**: 2026-08-01

**Status**: Approved for task-by-task implementation

**Input**: Approved experiment-first plan in
`docs/audio_pipeline_experiment_plan.md`: compare deterministic, lightweight
offline, local ASR/emotion, Gemini, and hybrid pipelines for maximum hidden-set
accuracy under USD 0.003 per audio minute on a simple 2 GB CPU host.

## User Scenarios & Testing

### User Story 1 - Analyze an evaluation batch (Priority: P1)

An authenticated evaluator uploads a ZIP or folder containing supported audio
files and a CSV manifest, starts one batch, observes progress and per-file
errors, reviews predictions, and downloads CSV or JSON results.

**Why this priority**: This is the submission's core value and the path used by
the hidden evaluation.

**Independent Test**: Upload a batch containing the three supplied calls, one
bad file, and a matching manifest. The valid files complete independently, the
bad file reports a useful error, and both downloads validate against the public
result contract.

**Acceptance Scenarios**:

1. **Given** a valid authenticated session and matching batch, **When** analysis
   is started, **Then** every valid clip receives exactly one schema-valid
   result and the original filename is preserved.
2. **Given** an unsupported, corrupt, missing, duplicate, or unmatched file,
   **When** the batch is validated, **Then** the file is isolated and the rest
   of the eligible batch can run.
3. **Given** a running batch, **When** the evaluator views the dashboard,
   **Then** queued, processing, complete, and failed counts are visible.

---

### User Story 2 - Receive accurate, independently reasoned fields (Priority: P1)

For every eligible recording, the evaluator receives emotional tone and
intensity, noise presence/type/severity, technical quality, overlap, long
silence, and an honest overall confidence.

**Why this priority**: Hidden-set performance carries the largest evaluation
weight, and the fields are scored separately.

**Independent Test**: On a frozen, call-grouped validation set, compare each
candidate and ablation per output field; accept only the highest-scoring
configuration that passes cost, privacy, memory, and calibration gates.

**Acceptance Scenarios**:

1. **Given** clear speech with audible but non-interfering background sound,
   **When** analyzed, **Then** noise and technical quality are judged
   independently.
2. **Given** loud speech without negative semantic or paralinguistic evidence,
   **When** analyzed, **Then** loudness alone does not cause a negative tone.
3. **Given** mono or dual-mono audio, **When** overlap is analyzed, **Then**
   stereo-channel coincidence is not treated as proof of overlap.
4. **Given** insufficient validation labels, **When** confidence is produced,
   **Then** it is identified internally as provisional rather than claimed to
   be calibrated.

---

### User Story 3 - Stay inside the operating constraints (Priority: P1)

The system processes a batch on one ordinary 2 GB RAM CPU host without a GPU
and prevents remote inference from exceeding USD 0.003 per input audio minute.

**Why this priority**: Cost and deployability are hard release constraints.

**Independent Test**: Run representative short, medium, long, corrupt, and
concurrent-upload fixtures while measuring peak resident memory, remote token
usage, per-clip/batch spend, and failure routing.

**Acceptance Scenarios**:

1. **Given** a batch whose remote path is projected above its allowance,
   **When** preflight runs, **Then** optional escalation is skipped or the
   remote path fails closed; an expensive standard-tier fallback is never
   selected silently.
2. **Given** transient best-effort remote unavailability, **When** bounded
   retries are exhausted, **Then** the file reports retryable failure or uses
   an already validated eligible path without violating the budget.
3. **Given** the production dependency set and representative workload,
   **When** profiled, **Then** peak RSS stays below 1.8 GB, preserving a 200 MB
   operating margin on the 2 GB host.

---

### User Story 4 - Audit and reproduce a release (Priority: P2)

An engineer can reproduce the selected configuration, evaluation, cost report,
and prediction from pinned code, prompts, model artifacts, thresholds, and
calibration data.

**Why this priority**: Accuracy claims are not credible without leakage-free
experiments and traceable releases.

**Independent Test**: Starting from the release manifest, rerun the frozen
evaluation and confirm schema validity, matching configuration hashes, and
metrics within declared deterministic tolerances.

**Acceptance Scenarios**:

1. **Given** a release result, **When** its manifest is inspected, **Then**
   local model revisions, remote model IDs/pricing, prompt version, thresholds,
   calibration version, and source-audio hash are traceable.
2. **Given** multiple clips from one caller or call, **When** datasets are
   split, **Then** their group cannot appear in both training and validation.

---

### User Story 5 - Select the best pipeline experimentally (Priority: P1)

An engineer runs the predeclared local, Gemini, and hybrid experiment matrix
against identical grouped data and selects the most accurate candidate that
passes cost, privacy, memory, licensing, reliability, and calibration gates.

**Why this priority**: The architecture cannot be selected accurately from
general model reputation or the three visible examples.

**Independent Test**: Execute E00–E13 as eligible, verify each run records its
configuration and resource/cost evidence, and reproduce the candidate-selection
report from immutable run artifacts.

**Acceptance Scenarios**:

1. **Given** two materially different candidates, **When** they are evaluated,
   **Then** they use the same preprocessing, grouped splits, metrics, and frozen
   labels.
2. **Given** a local or remote component, **When** its ablation does not improve
   a target field beyond measurement uncertainty, **Then** it is removed from
   the production candidate.
3. **Given** an identical paid request, **When** another experiment needs the
   same observation, **Then** the cached immutable result is reused instead of
   spending again.
4. **Given** that a candidate has the best average accuracy, **When** it breaks
   a hard gate or materially harms a protected field, **Then** it is ineligible.

### Edge Cases

- Clips shorter than the minimum economical remote-request duration.
- Very long clips, silent clips, non-speech recordings, and truncated uploads.
- Mono, genuine stereo, dual-mono, and unknown channel arrangements.
- Multiple noise sources, background television speech, music with vocals, and
  agent speech mistaken for the customer.
- Quiet frustration, loud satisfaction, crying, sarcasm, code-switching, and
  domain-specific language.
- Static, clipping, echo, packet loss, low volume, muffling, and noise that is
  audible but does not impair intelligibility.
- No speech, no customer speech, uncertain speaker roles, and brief crosstalk.
- Remote timeout, 503 response, malformed structured output, or changed prices.
- Archive traversal, oversized decompression, duplicate names, and manifest
  injection.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST require authenticated access to the dashboard.
- **FR-002**: The system MUST accept a folder or ZIP containing root-level
  supported audio files and a CSV manifest with `name` and optional
  `result_json`.
- **FR-003**: The system MUST validate archive safety, manifest shape, filename
  matching, supported media, duration limits, duplicates, and file size before
  inference.
- **FR-004**: The system MUST process eligible files sequentially by default,
  show progress, and isolate per-file failures.
- **FR-005**: The public result MUST contain exactly the nine assignment fields,
  with exact enum values and cross-field invariants.
- **FR-006**: The system MUST preserve the original full-band signal for
  technical/noise analysis and separately derive a mono 16 kHz speech-analysis
  signal with recorded provenance.
- **FR-007**: The system MUST compute deterministic acoustic evidence including
  voice activity, silence spans, level/noise-floor estimates, clipping, channel
  correlation, spectral summaries, and dropout/transient indicators.
- **FR-008**: The production candidate MUST evaluate lightweight bounded-memory
  models for voice activity, audio events, and technical quality; each retained
  model MUST improve a predeclared field metric or calibration.
- **FR-009**: Emotion MUST use customer-attributed semantic and paralinguistic
  evidence; signal energy alone MUST NOT assign emotional tone.
- **FR-010**: Noise presence/type/severity and audio quality MUST have separate
  evidence and decision paths.
- **FR-011**: Overlap on mono or dual-mono audio MUST NOT be decided from channel
  activity alone. Genuine independent stereo MAY use channel evidence after a
  channel-independence test.
- **FR-012**: Long silence MUST be determined from duration-aware voice activity
  rules whose threshold is frozen from the label rubric and validation data.
- **FR-013**: An approved remote audio model MAY supply semantic,
  paralinguistic, noise, role, and overlap evidence only after privacy and cost
  preflight.
- **FR-014**: A stronger remote model MAY receive compact text evidence in
  batches, never audio by default, and MUST be disabled unless its blinded
  ablation improves the primary weighted score.
- **FR-015**: The cost controller MUST use versioned prices, measured token
  usage, a conservative fixed-overhead reserve, and batch audio duration. It
  MUST target at most USD 0.0024/minute and hard-block any projected path above
  USD 0.003/minute.
- **FR-016**: The system MUST NOT silently fall back from discounted
  best-effort inference to a more expensive service tier.
- **FR-017**: Remote audio MUST use a paid, AutoAce-approved billing project
  with documented retention/training controls; uploaded files MUST be deleted
  immediately after use and local temporary audio after the batch retention
  window.
- **FR-018**: The production deployment MUST fit on a single 2 GB RAM CPU host,
  require no GPU, and avoid a database, job broker, or separate frontend.
- **FR-019**: The system MUST export filename-preserving JSON and CSV, with
  schema-valid public results and a separate operational error report.
- **FR-020**: Confidence MUST be calibrated against held-out correctness using
  per-field evidence and disagreement. Until enough representative labels
  exist, it MUST be marked internally as provisional and excluded from
  calibration claims.
- **FR-021**: The three supplied recordings MUST be smoke/reference fixtures,
  not a training set or the basis of reported generalization.
- **FR-022**: Model selection MUST implement the approved P0–P8 candidate
  definitions and execute E00–E13 when their privacy, licensing, data, and cost
  preconditions are satisfied.
- **FR-023**: Selection MUST use call/speaker-grouped splits, a locked holdout,
  per-field metrics, macro F1 for tone, calibration error/Brier score, cost,
  latency, and peak RSS.
- **FR-024**: Every release MUST pin artifact revisions and record prompt,
  fusion, threshold, pricing, calibration, and dependency versions.
- **FR-025**: All Python setup, development, tests, experiments, and application
  execution MUST use a project-local Python 3.12 `.venv`; project dependencies
  MUST NOT be installed globally.
- **FR-026**: The experiment harness MUST cache paid observations by source
  hash, model ID, prompt/schema/configuration hashes, and provider mode, and
  MUST never repeat an identical paid request.
- **FR-027**: Paid experiments MUST require a configured total research-spend
  limit and explicit approval; exceeding or missing the limit MUST fail closed.
- **FR-028**: Local ASR, emotion, event, quality, and overlap models MUST load
  sequentially or in disposable subprocesses, and each MUST pass license,
  provenance, parity where converted, accuracy-ablation, latency, and peak-RSS
  gates.
- **FR-029**: The candidate-selection rule and material protected-field
  regression threshold MUST be frozen before remote experiments E09–E13.
- **FR-030**: Product UI work MUST not determine the model architecture and
  SHOULD begin only after the leading eligible pipeline and its resource
  envelope are established.

### Key Entities

- **Batch**: One upload and its validation, progress, aggregate duration,
  spending allowance, status, and files.
- **Audio Item**: Original filename, safe local path, hash, media metadata,
  processing status, and failure information.
- **Acoustic Evidence**: Versioned deterministic and lightweight-model
  measurements derived from an audio item.
- **Remote Observation**: Structured evidence returned by an approved remote
  model with token usage, price snapshot, request mode, and deletion receipt.
- **Prediction**: The exact public result plus internal field-level evidence,
  decision provenance, and uncertainty.
- **Evaluation Run**: Frozen dataset split, candidate configuration, metrics,
  latency, memory, cost, and pass/fail gates.
- **Candidate Definition**: Immutable P0–P8 component graph, field ownership,
  runtime requirements, and eligibility rules.
- **Observation Cache Entry**: Content-addressed reusable remote observation
  with request identity, privacy state, usage, and integrity metadata.
- **Release Manifest**: Immutable versions and hashes needed to reproduce the
  selected production candidate.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of successful outputs validate against the exact result
  schema; 100% of invalid files are isolated without aborting other files.
- **SC-002**: The selected candidate has the highest locked-validation weighted
  score among candidates that pass all hard gates; tone is reported with macro
  F1 and every other field with its predeclared metric and confidence interval.
- **SC-003**: No retained component has a non-positive validated contribution
  to its target field or calibration after accounting for measurement
  uncertainty.
- **SC-004**: Measured remote spend is at most USD 0.0024/audio-minute at the
  release workload and no legal route can exceed USD 0.003/audio-minute.
- **SC-005**: Peak RSS is below 1.8 GB on the target 2 GB CPU host, with no GPU,
  under a representative batch.
- **SC-006**: At least 95% of valid files complete without manual intervention
  under the documented service availability assumptions; failures remain
  filename-specific and retryable where appropriate.
- **SC-007**: Confidence is either demonstrably calibrated on a representative
  held-out set (reported Brier score and expected calibration error) or
  transparently designated provisional.
- **SC-008**: A fresh operator can deploy the single Streamlit application and
  complete upload-to-download verification from the quickstart without adding
  another service.
- **SC-009**: Remote test requests leave a recorded approval/configuration
  trace and uploaded remote files are deleted after each successful or failed
  request.
- **SC-010**: Every eligible E00–E13 run is reproducible from its recorded
  dataset, candidate, prompt, model, threshold, and dependency hashes.
- **SC-011**: No identical paid request is executed more than once, and total
  research spend cannot exceed its approved configured limit.
- **SC-012**: A clean checkout can create `.venv`, install the locked
  dependencies, run tests, and reproduce a smoke experiment without relying on
  globally installed Python packages.

## Assumptions

- Hosting charges are outside the inference-cost ceiling, but the chosen host
  is a conventional Linux CPU instance with 2 GB RAM and FFmpeg available.
- Calls are generally OGG/Opus, WAV, MP3, AAC/M4A, or FLAC; explicit limits are
  fixed during implementation from deployment and evaluation needs.
- Gemini model availability, pricing, and data terms are revalidated immediately
  before implementation and release; the current planning snapshot is
  2026-08-01.
- AutoAce will approve or reject the proposed paid remote endpoint before real
  customer audio is sent. Without approval, only the validated local path may
  run.
- A USD 10 initial research-spend ceiling is proposed but is not authorization;
  the executing user must explicitly approve and configure the actual limit.
- A representative human-adjudicated dataset beyond the three supplied calls is
  required for credible model selection and calibrated confidence.

## Out of Scope

- Training a large foundation model or relying on a production GPU.
- A custom React frontend, microservices, persistent database, distributed job
  queue, or Kubernetes deployment.
- Treating the three visible labels as evidence of generalization.
- Guaranteed real-time streaming; the target is dependable batch analysis.
