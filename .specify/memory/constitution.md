<!--
Sync Impact Report
- Version change: 1.1.0 -> 1.2.0
- Added principles:
  - I. Measured Accuracy Before Architectural Complexity
  - II. Independent Fields, Independent Evidence
  - III. Leakage-Free and Reproducible Evaluation
  - IV. Privacy and Cost Are Hard Gates
  - V. Minimal Product Surface
  - VI. Honest Uncertainty and Failure Isolation
- Added sections:
  - Non-Negotiable Product Constraints
  - Development and Release Gates
- Template alignment:
  - .specify/templates/plan-template.md: compatible; Constitution Check is mandatory
  - .specify/templates/spec-template.md: compatible; measurable outcomes and edge cases are mandatory
  - .specify/templates/tasks-template.md: compatible; tests are mandatory for model, contract, cost, and privacy gates
  - .specify/templates/checklist-template.md: compatible
- Amendment: require experiment-first comparison of local, remote, and hybrid
  candidates; require a project-local Python virtual environment.
- Follow-up actions: none.
-->

# AutoAce Call Analysis Constitution

## Core Principles

### I. Measured Accuracy Before Architectural Complexity

Output accuracy is the primary product objective. Every model, feature, rule, or
external service MUST earn its place through a predeclared, leakage-free
evaluation on representative data. A more complex component MUST NOT be adopted
because it appears more capable in general; it MUST improve the metric for the
specific output field it serves, or improve calibration without a material
accuracy regression. If an accuracy claim cannot be measured, it is not a
release claim.
Model selection MUST include materially different computation-only, local-model,
remote-audio, and hybrid candidates. A preferred architecture MAY NOT bypass the
same frozen evaluation applied to its challengers.

### II. Independent Fields, Independent Evidence

Emotion, intensity, background-noise presence and type, noise severity, audio
quality, speaker overlap, and long silence are distinct judgements. The system
MUST preserve independent evidence and decision paths for them. Background noise
MUST NOT automatically imply poor audio quality; loudness MUST NOT determine
emotion; overlap MUST NOT be inferred from transcript punctuation; enhanced
audio MUST NOT replace the original recording when enhancement could remove
evidence. Shared representations are allowed, but field-specific selection,
calibration, and ablation are mandatory.

### III. Leakage-Free and Reproducible Evaluation

All reported model-selection results MUST use call- or speaker-grouped splits,
versioned labels, frozen preprocessing, pinned model revisions, fixed random
seeds where supported, and a retained final holdout. The three assignment calls
MUST remain reference/smoke fixtures and MUST NOT be treated as sufficient
training or cross-validation data. Synthetic data MAY strengthen controlled
acoustic conditions, but MUST NOT substitute for human-adjudicated real
conversations when evaluating emotion. Every released result MUST be traceable
to a configuration and model manifest.

### IV. Privacy and Cost Are Hard Gates

Audio MUST remain local by default. Remote inference is permitted only through
an explicitly approved enterprise endpoint with documented retention controls,
and only after a deterministic cost preflight. Variable remote-model spend MUST
remain at or below USD 0.003 per processed audio minute; infrastructure and
hosting are reported separately. A privacy or cost check that cannot prove
compliance MUST fail closed to the eligible local path rather than silently
continue remotely.

### V. Minimal Product Surface

The product surface exists to submit audio, expose progress and per-file errors,
and download valid results. It MUST remain a single, simple application and
deployment unless measured requirements prove that additional services,
databases, queues, or frontend frameworks are necessary. Engineering effort
SHOULD go to the audio pipeline, evaluation, calibration, and observability.
Every architectural addition MUST name the measured constraint it resolves.
The production candidate MUST run on a conventional 2 GB RAM CPU host and MUST
NOT require a resident GPU. Models MUST load sequentially or use bounded native
runtimes when simultaneous residency would threaten this limit.

### VI. Honest Uncertainty and Failure Isolation

The returned confidence MUST be a calibrated estimate of correctness, never a
constant or an unvalidated model self-rating. Disagreement and out-of-domain
signals MUST be retained for review. One corrupt file, unavailable optional
model, or rejected remote route MUST NOT invalidate other eligible files in a
batch. Failures MUST be explicit, structured, and reproducible; unsupported
fallbacks MUST NOT masquerade as successful analysis.

## Non-Negotiable Product Constraints

- The public result contract MUST contain exactly the assignment fields and
  legal values, including an empty noise type when no noise is present.
- Customer emotion MUST be computed from customer evidence. Agent speech,
  television speech, and other background voices MUST NOT be silently labelled
  as customer emotion.
- Original full-band audio MUST remain available to acoustic evidence paths.
  Resampled or enhanced derivatives MUST record their purpose and provenance.
- Licenses and model terms MUST be reviewed and recorded before any artifact is
  admitted to a production candidate. Non-commercial-only components are not
  eligible for the production path.
- Hosting cost is outside the USD 0.003/audio-minute ceiling by user direction,
  but measured compute throughput and estimated infrastructure cost MUST still
  be reported transparently.
- A remote foundation model MAY be used for perceptual judgements that local
  computation cannot solve reliably, but it MUST be the least expensive
  validated candidate for that field. Stronger-model escalation MUST be
  evidence-gated, cost-preflighted, and removable without breaking the batch.
- Python development, testing, experiments, and runtime MUST use the
  project-local `.venv`. Global package installation is prohibited. Dependency,
  native runtime, and model artifact versions MUST be reproducible and separate
  from the virtual environment.
- The interface MUST support authenticated access, manifest-backed batch input,
  progress, per-file isolation, and JSON/CSV download without requiring a
  distributed platform.

## Development and Release Gates

1. Write contract, cost, privacy, data-split, and model-evaluation tests before
   the corresponding production integration.
2. Establish immutable dataset groups and an annotation/adjudication protocol
   before comparative model selection.
3. Record per-field baselines, primary metrics, calibration metrics, latency,
   and cost before accepting a candidate.
4. Run ablations for every evidence family used by the final stack. A component
   with no validated contribution is removed from the default path.
5. Validate exact schema output, malformed-input behavior, error isolation,
   privacy routing, and cost refusal on an end-to-end batch.
6. Freeze revisions, thresholds, calibration artifacts, prompt versions, and
   the decision configuration before the untouched final holdout.
7. A release MUST be blocked when any hard gate fails; an exception requires a
   constitution amendment, not an undocumented waiver.
8. Execute the predeclared experiment matrix incrementally, cache identical
   paid observations, and freeze the winning eligible pipeline before building
   product-specific polish.

## Governance

This constitution supersedes conflicting plan, task, and implementation
preferences. Every planning and review cycle MUST include an explicit
Constitution Check. Amendments require a written rationale, impact analysis,
migration plan for affected artifacts, and semantic version change: MAJOR for a
principle removal or incompatible governance change, MINOR for a new principle
or materially expanded mandate, and PATCH for clarification. Compliance is
re-evaluated whenever the data rubric, external pricing, privacy terms, model
license, or production model revision changes.

**Version**: 1.2.0 | **Ratified**: 2026-07-31 | **Last Amended**: 2026-08-01
