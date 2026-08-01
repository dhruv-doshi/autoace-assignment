# GPT-5.6 Luna Implementation Handoff

## Mission

Implement feature `001-call-audio-analysis` task by task. GPT-5.6 Luna is the
coding agent only. Luna must not be added to the application, runtime
dependencies, inference pipeline, cost model, UI, or documentation as a
production service.

## Authority and Scope

Authorized:

- create and modify repository code/config/tests/docs required by the current
  task;
- run local tests, static checks, smoke fixtures, and non-destructive profilers;
- download a local model only after the task's license/provenance gate and any
  required user approval;
- call a paid provider only after explicit privacy and research-spend approval.

Not authorized:

- send confidential audio to an unapproved service;
- spend against an API without a configured approved cap;
- install project Python packages globally;
- open the final holdout early;
- weaken cost, privacy, license, memory, or contract gates;
- mark blocked work complete or fabricate experiment results;
- add a GPU, database, broker, custom frontend, or distributed architecture
  without a measured requirement and plan amendment.

## Required Read Order

Before T001, read completely:

1. `docs/audio_pipeline_experiment_plan.md`
2. `.specify/memory/constitution.md`
3. `specs/001-call-audio-analysis/spec.md`
4. `specs/001-call-audio-analysis/plan.md`
5. `specs/001-call-audio-analysis/research.md`
6. `specs/001-call-audio-analysis/data-model.md`
7. every file under `specs/001-call-audio-analysis/contracts/`
8. `specs/001-call-audio-analysis/tasks.md`
9. both checklists under `specs/001-call-audio-analysis/checklists/`

## Task Loop

For each task:

1. Confirm all preceding dependencies and phase gates.
2. Activate `.venv`; if it does not exist, only T001–T003 may create it.
3. Inspect existing user changes and preserve unrelated work.
4. Write the named test first when the task specifies a test.
5. Run the narrow test and confirm it fails for the intended reason.
6. Implement only the current task's scope.
7. Run the narrow test, related phase tests, and static checks.
8. Record commands, outputs, decisions, hashes, costs, and blockers in
   `docs/implementation-log.md`.
9. Mark the task checkbox complete only when acceptance evidence exists.
10. Stop at each phase gate and summarize status before proceeding.

Do not batch-mark tasks complete.

## Virtual Environment Contract

Use:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Before every Python command group, verify:

```bash
python -c "import pathlib,sys; p=pathlib.Path(sys.executable).resolve(); assert '.venv' in p.parts, p"
```

Never run bare global `pip`. Use `python -m pip` after activation.

## Experiment Integrity

- P0–P8 are candidates; E00–E13 are immutable experiment definitions.
- All candidates share the same source audio, preprocessing revision, grouped
  splits, metrics, and public contract.
- The three supplied calls are `smoke_only`; their labels cannot fit prompts,
  thresholds, classifiers, fusion, or calibration.
- Public datasets may preselect a component but cannot replace domain
  evaluation on representative calls.
- Open the final holdout only after T111–T112 freeze the complete pipeline.
- Every ExperimentRun validates against `contracts/experiment.schema.json`.

## Paid Request Protocol

Before any remote request, all must be true:

- endpoint/project/region/retention approval exists;
- current provider/model/pricing record exists;
- research budget is explicitly approved and configured;
- exact request passes per-route cost preflight;
- cache lookup has missed with an integrity-valid key;
- request contains only approved audio/data;
- cleanup and redacted logging are active.

After the request:

- record provider usage and reconcile actual spend;
- delete and verify any remote file upload;
- persist only the approved structured observation and operational metadata;
- never log audio, transcript, prompt content, or call-derived rationale.

Flex failure may receive bounded retries. It must never silently switch to a
more expensive tier.

## Model Admission Protocol

For Silero, DNSMOS, YAMNet, pyannote, SpeechBrain, emotion2vec, and Whisper:

1. Record separate code and weight licenses.
2. Pin source/revision and SHA-256.
3. Record gating/access conditions.
4. Verify converted artifact parity when applicable.
5. Load sequentially or in a disposable subprocess.
6. Measure isolated field contribution, latency, and peak RSS.
7. Reject the model if contribution is non-positive, protected fields regress,
   terms are unclear, or peak process RSS reaches 1.8 GB.

Do not install full TensorFlow for YAMNet in production.

## Stop and Request User Input When

- representative labelled data is needed but unavailable;
- a real-call remote privacy decision is missing;
- API credentials or research-budget approval are missing;
- a gated/custom model license is unclear;
- the final holdout would be opened;
- a destructive operation or architecture expansion becomes necessary;
- two source-of-truth documents materially conflict.

A missing precondition creates a `blocked` experiment record where defined; it
does not authorize guessing.

## Expected Checkpoint Reports

At every Gate A–K, report:

- completed task IDs;
- tests/static checks run;
- current candidate/experiment artifacts;
- accuracy metrics and intervals when valid;
- peak RSS and real-time factor;
- API cache hits/misses and actual spend;
- rejected/blocked components and reasons;
- remaining approvals or data requirements.

## Completion Definition

Implementation is complete only when:

- T001–T133 are complete or legitimately inapplicable/blocked with recorded
  evidence;
- the winning candidate passes every hard gate;
- the holdout report and release manifest are reproducible;
- one authenticated Streamlit process runs on a 2 GB CPU host;
- hosted batch upload, progress, per-file isolation, and downloads work;
- no production route can knowingly exceed `$0.003/audio-minute`;
- the model-quality and requirements checklists are complete.

## Suggested First Instruction to Luna

> Read the complete Luna handoff and all sources in its required read order.
> Execute only T001. Preserve existing work, use `apply_patch` for file edits,
> record evidence in the implementation log, and stop after reporting T001's
> result. Do not implement later tasks yet.
