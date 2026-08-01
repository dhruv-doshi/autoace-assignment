# Tasks: Experiment-First Call Audio Analysis

**Feature**: `001-call-audio-analysis`  
**Implementation agent**: GPT-5.6 Luna or another coding agent  
**Source of truth**: `spec.md`, `plan.md`, and
`docs/audio_pipeline_experiment_plan.md`

## Execution Rules

- Execute tasks in numeric order unless `[P]` explicitly permits independent
  work after the same prerequisites.
- Use the project-local Python 3.12 `.venv` for every Python command.
- Write the listed tests before the implementation they verify and observe the
  expected failure.
- Never send real audio remotely before privacy and spend gates pass.
- Never run a paid experiment without a configured user-approved research cap.
- Mark a task complete only after its acceptance evidence is recorded in
  `docs/implementation-log.md`.
- A blocked experiment is recorded as blocked with a reason; it is not silently
  skipped or fabricated.

## Phase 1: Reproducible Environment

- [x] T001 Create `.gitignore` with `.venv/`, secrets, temporary audio, caches,
  downloaded model binaries, and generated experiment artifacts excluded
- [x] T002 Create Python 3.12 `.venv` using `python3.12 -m venv .venv` and record
  the command in `README.md`
- [x] T003 Activate `.venv`, upgrade pip inside it, and verify `python` and
  `pip` resolve under `.venv` in `scripts/verify_environment.py`
- [x] T004 Create the single-project structure from `plan.md` under
  `src/autoace/`, `tests/`, `configs/`, `models/`, `scripts/`, and `release/`
- [x] T005 Define minimal core, experiment-extra, and development dependencies
  in `pyproject.toml` without full TensorFlow or GPU packages
- [x] T006 Generate and commit the reproducible dependency lock/constraints
  artifact from inside `.venv`
- [x] T007 [P] Configure pytest, Hypothesis, coverage, formatter, linter, type
  checker, and fixed seeds in `pyproject.toml`
- [x] T008 [P] Implement environment/version capture for Python, lock hash,
  FFmpeg, OS, CPU, and native runtimes in `src/autoace/environment.py`
- [x] T009 [P] Create `docs/implementation-log.md` with task, command, evidence,
  decision, and artifact-hash fields
- [x] T010 Run an environment smoke test from a clean `.venv` and record the
  result in `docs/implementation-log.md`

**Gate A**: No later Python task runs outside `.venv`.

## Phase 2: Exact Contracts and Safe Batch Input

- [x] T011 [P] [US2] Write failing tests for every legal/illegal result enum,
  exact keys, finite confidence, and noise invariants in
  `tests/contract/test_result_contract.py`
- [x] T012 [P] [US1] Write failing CSV/manifest tests for quoting, duplicates,
  unmatched files, missing columns, and empty hidden labels in
  `tests/contract/test_manifest_contract.py`
- [x] T013 [P] [US5] Write failing JSON Schema tests for experiment and release
  manifests in `tests/contract/test_experiment_contracts.py`
- [x] T014 [US2] Implement Pydantic public-result and evidence models in
  `src/autoace/contracts.py`
- [x] T015 [US5] Implement experiment and release-manifest models in
  `src/autoace/contracts.py`
- [x] T016 [P] [US1] Write archive adversarial tests for traversal, symlinks,
  decompression bombs, duplicate basenames, hidden files, and unsupported media
  in `tests/unit/test_batch_security.py`
- [x] T017 [US1] Implement safe temporary directories and ZIP/folder extraction
  in `src/autoace/security.py`
- [x] T018 [US1] Implement manifest parsing, filename matching, file count/size,
  media allowlist, and validation report in `src/autoace/batch.py`
- [x] T019 [P] [US1] Write mixed valid/corrupt per-file isolation tests in
  `tests/integration/test_batch_isolation.py`
- [x] T020 [US1] Implement Batch/AudioItem states, progress counters, redacted
  errors, and cleanup in `src/autoace/domain.py` and `src/autoace/batch.py`
- [x] T021 [US1] Implement filename-preserving JSON/CSV exports in
  `src/autoace/batch.py`
- [x] T022 Run the contract and safe-batch suite and record schema versions

**Gate B**: Exact public output and hostile batch handling pass before models.

## Phase 3: Audio and Evaluation Foundation

- [x] T023 [P] [US2] Write ffprobe, decode, resample, source-hash, and provenance
  tests in `tests/unit/test_decode.py`
- [x] T024 [US2] Implement original full-band preservation and mono 16 kHz
  derivation in `src/autoace/audio/decode.py`
- [x] T025 [US4] Register the three supplied files as `smoke_only` with hashes
  and expected contracts in `tests/fixtures/smoke/manifest.json`
- [x] T026 [US4] Write the assignment-aligned customer-role and field-boundary
  annotation guide in `docs/annotation-guide.md`
- [x] T027 [P] [US4] Write tests preventing call/speaker group leakage, smoke
  fixture training, and premature holdout access in
  `tests/evaluation/test_dataset_splits.py`
- [x] T028 [US4] Implement the versioned dataset registry and grouped
  development/calibration/holdout splits in
  `src/autoace/evaluation/datasets.py`
- [x] T029 [P] [US5] Implement tone/enum/boolean metrics, normalized noise-type
  scoring, paired bootstrap intervals, Brier score, and ECE in
  `src/autoace/evaluation/metrics.py`
- [x] T030 [P] [US5] Implement immutable P0–P8 candidate definitions and E00–E13
  experiment definitions in `src/autoace/evaluation/registry.py`
- [x] T031 [US5] Create versioned candidate and experiment configuration files
  in `configs/experiments/`
- [x] T032 [US5] Freeze the macro-average selection rule, tone co-primary,
  protected-field list, and material-regression margin in
  `configs/evaluation.json`
- [x] T033 [P] [US3] Implement wall time, real-time factor, baseline/peak RSS,
  completion, and subprocess metrics in `src/autoace/evaluation/profiling.py`
- [x] T034 [US5] Implement experiment execution and append-only artifact writing
  in `src/autoace/evaluation/experiments.py`

**Gate C**: Representative labels and grouped splits are required for accuracy
selection. Without them, continue only with mechanics and smoke validation.

## Phase 4: P0 Deterministic Baseline / E00

- [x] T035 [P] [US2] Write generated-audio tests for silence, level, clipping,
  static, impulses, bandwidth, dropouts, dual-mono, and independent stereo in
  `tests/unit/test_dsp.py`
- [x] T036 [US2] Implement levels, robust noise floor/SNR proxy, clipping, DC,
  crest, spectral, bandwidth, transient, dropout, and channel features in
  `src/autoace/audio/dsp.py`
- [x] T037 [P] [US2] Verify Silero VAD source, MIT license, revision, and
  artifact SHA-256 in `models/manifest.json`
- [x] T038 [P] [US2] Write VAD, speech-ratio, boundary, and injected internal
  silence tests in `tests/unit/test_vad.py`
- [x] T039 [US2] Implement bounded Silero ONNX inference and duration-aware
  internal-silence evidence in `src/autoace/audio/vad.py`
- [x] T040 [US2] Implement transparent P0 field policies in
  `src/autoace/inference/fusion.py` and `configs/fusion/p0.json`
- [x] T041 [US5] Run E00 on smoke data and the grouped development data when
  available via `scripts/evaluate.py`
- [x] T042 [US3] Profile E00 on the target-like 2 GB CPU environment via
  `scripts/profile_memory.py`
- [x] T043 [US5] Save E00 metrics, limitations, peak RSS, real-time factor, and
  hashes as a schema-valid ExperimentRun

**Gate D**: P0 is the zero-API lower bound; do not hide its semantic and overlap
limitations.

## Phase 5: P1 Local Acoustic Specialists / E01–E04

- [ ] T044 [P] [US2] Verify DNSMOS code/model license, revision, source, and
  artifact hashes in `models/manifest.json`
- [ ] T045 [P] [US2] Write DNSMOS SIG/BAK/OVRL validity, chunking, and failure
  tests in `tests/unit/test_quality_model.py`
- [ ] T046 [US2] Implement sequential DNSMOS P.835 ONNX inference in
  `src/autoace/audio/quality.py`
- [ ] T047 [P] [US2] Verify YAMNet TFLite provenance, license, revision, class
  map, and artifact hashes in `models/manifest.json`
- [ ] T048 [P] [US2] Write YAMNet temporal-event, speech/background, and failure
  tests in `tests/unit/test_event_model.py`
- [ ] T049 [US2] Implement YAMNet with TFLite/MediaPipe and no full TensorFlow
  runtime in `src/autoace/audio/events.py`
- [ ] T050 [P] [US2] Evaluate official pyannote overlap access/terms and any
  proposed conversion provenance/parity; record the decision in
  `docs/model-licenses.md`
- [ ] T051 [P] [US2] Write mono, dual-mono, genuine-stereo, brief-crosstalk, and
  overlap-model tests in `tests/unit/test_overlap.py`
- [ ] T052 [US2] Implement the eligible local overlap challenger with isolated
  loading in `src/autoace/audio/overlap.py`, or record E03 blocked if gates fail
- [ ] T053 [US5] Run E01 P0+DNSMOS and record the isolated field ablation
- [ ] T054 [US5] Run E02 P0+YAMNet and record the isolated field ablation
- [ ] T055 [US5] Run E03 P0+overlap model or a schema-valid blocked result
- [ ] T056 [US5] Run E04 using only accepted E01–E03 components; reject any
  combination with peak RSS >=1.8 GB or material field regression

**Gate E**: P1 contains only licensed local specialists with positive measured
contribution and acceptable memory/latency.

## Phase 6: P2/P3 Local Emotion and Semantics / E05–E08

- [ ] T057 [P] [US2] Verify SpeechBrain IEMOCAP model revision, Apache-2.0
  license, label map, artifact hashes, and runtime dependencies in
  `docs/model-licenses.md`
- [ ] T058 [P] [US2] Verify emotion2vec model/code licenses, revision, artifact
  hashes, and representation semantics; block production use if unclear
- [ ] T059 [P] [US2] Write customer-role, label-mapping, missing-speech,
  multilingual, and sequential-loading tests in `tests/unit/test_emotion.py`
- [ ] T060 [US2] Implement isolated SpeechBrain emotion evidence in
  `src/autoace/audio/emotion.py`
- [ ] T061 [US2] Implement isolated emotion2vec embeddings only if license and
  2 GB preflight pass; otherwise write the blocked ExperimentRun path
- [ ] T062 [US2] Implement regularized out-of-fold local emotion mapping without
  fitting the three smoke calls in `src/autoace/inference/local_semantics.py`
- [ ] T063 [US5] Run E05 SpeechBrain and E06 emotion2vec separately and retain
  only evidence with a credible tone/intensity gain
- [ ] T064 [P] [US2] Verify Whisper/whisper.cpp/faster-whisper code and model
  licenses, revisions, tiny/base hashes, and CPU INT8 support
- [ ] T065 [P] [US2] Write ASR decoding, language, timestamp, role uncertainty,
  empty speech, and memory-isolation tests in `tests/unit/test_asr.py`
- [ ] T066 [US2] Implement a tiny/base ASR adapter with subprocess isolation in
  `src/autoace/audio/asr.py`
- [ ] T067 [US2] Implement customer-aware transcript and prosody features plus a
  transparent/regularized semantic baseline in
  `src/autoace/inference/local_semantics.py`
- [ ] T068 [US5] Run E07 Whisper tiny and record tone/intensity gain, WER proxy,
  role failures, real-time factor, and peak RSS
- [ ] T069 [US5] Run E08 Whisper base under identical conditions and compare it
  with E07
- [ ] T070 [US5] Freeze the best zero-API P0–P3 pipeline and document why every
  rejected local component was removed

**Gate F**: A fully local winner remains eligible. Local models are not retained
merely to avoid API use.

## Phase 7: Paid-Observation Cache, Cost, and Privacy

- [x] T071 [P] [US3] Write Decimal-based cost tests for price snapshots, audio
  duration, short clips, hidden-thinking reserve, design/hard limits, and price
  changes in `tests/unit/test_cost.py`
- [x] T072 [P] [US5] Write cache-key, integrity, hit/miss, quarantine, and
  identical-paid-request tests in `tests/unit/test_observation_cache.py`
- [x] T073 [US5] Implement content-addressed paid-observation caching in
  `src/autoace/inference/observation_cache.py`
- [x] T074 [US3] Implement versioned prices, batch allowance, p99 reserve,
  preflight routing, and usage reconciliation in
  `src/autoace/inference/cost.py`
- [x] T075 [P] [US3] Write research-cap tests for missing approval, missing cap,
  projected overspend, actual overspend, and cached requests in
  `tests/unit/test_research_budget.py`
- [x] T076 [US3] Implement explicit research approval and total-spend ledger in
  `src/autoace/inference/cost.py`
- [ ] T077 [P] [US3] Write remote inline/upload cleanup, redacted logging,
  malformed output, timeout, 503, and no-standard-fallback tests in
  `tests/integration/test_remote_privacy.py`
- [x] T078 [US3] Add paid project, endpoint, region, retention/data controls,
  secrets, and approval configuration to `src/autoace/config.py`
- [ ] T079 [US3] Implement bounded Flex retries, immediate file deletion,
  deletion verification, and redacted telemetry in
  `src/autoace/inference/gemini_audio.py`
- [x] T080 [US4] Create versioned price and privacy approval schemas/configs in
  `configs/pricing/` and `release/privacy-approval.example.json`
- [ ] T081 [US3] Revalidate current Gemini model IDs, prices, audio tokenization,
  thinking billing, Flex behavior, and data terms; record dated sources
- [ ] T082 Run all cache/cost/privacy tests and stop paid work unless every hard
  gate passes and the user has configured approval

**Gate G**: Paid requests are impossible without privacy approval, research cap,
per-route cost compliance, and cache lookup.

## Phase 8: P4/P5 Gemini Baselines / E09–E10

- [ ] T083 [P] [US2] Design and hash the compact P4 customer-role/audio evidence
  prompt in `configs/prompts/gemini-3.5-audio.md`
- [ ] T084 [P] [US2] Write mocked structured-output, role, timestamps,
  ambiguity, no-customer-speech, and invalid-response tests in
  `tests/unit/test_gemini_audio.py`
- [ ] T085 [US2] Implement stable Gemini 3.5 Flash-Lite Flex observation in
  `src/autoace/inference/gemini_audio.py`
- [ ] T086 [US5] Run E09 P4 on a small approved development subset, using cache
  and the research ledger
- [ ] T087 [US3] Measure P4 p50/p95/p99 input, visible output, thinking, latency,
  and spend by duration bucket
- [ ] T088 [US2] Implement P5 field-specific fusion in
  `src/autoace/inference/fusion.py` and `configs/fusion/p5.json`
- [ ] T089 [US5] Run E10 P5 against E09 and the best local candidate with paired
  field intervals
- [ ] T090 [US3] Validate short-clip grouping versus independent observation;
  enable it only without material attribution regression
- [ ] T091 [US3] Freeze the measured Gemini usage reserve in
  `configs/pricing/gemini-usage-reserve.json`
- [ ] T092 [US3] Profile P4/P5 end to end on the 2 GB target and validate the
  release design cost <=$0.0024/minute
- [ ] T093 [US5] Promote the better eligible P4/P5 candidate without assuming
  either beats the local winner

**Gate H**: The best eligible local and Gemini-3.5 candidates are measured on
the same data and metrics.

## Phase 9: P6/P7/P8 Accuracy Challengers / E11–E13

- [ ] T094 [US2] Construct P6 from the best P5 path plus only previously
  accepted local specialists in `configs/experiments/p6.json`
- [ ] T095 [US5] Run E11 and measure whether each local specialist still adds
  incremental value in the Gemini hybrid
- [ ] T096 [P] [US2] Design and hash the compact evidence-only Gemini 3.6 batch
  prompt in `configs/prompts/gemini-3.6-adjudicator.md`
- [ ] T097 [P] [US3] Write P7 batch-size, short-clip skip, allowance, cache,
  malformed response, 503, and P5/P6 fallback tests in
  `tests/unit/test_adjudicator.py`
- [ ] T098 [US2] Implement optional text-only Gemini 3.6 Flex adjudication in
  `src/autoace/inference/adjudicator.py`
- [ ] T099 [US3] Integrate P7 optional-stage cost routing so it cannot block or
  invalidate the pre-adjudication result
- [ ] T100 [US5] Run E12 and compare P7 with the best P5/P6 candidate using
  paired intervals and protected-field regression gates
- [ ] T101 [US3] Measure P7 generated/thinking overhead by batch-duration bucket
  and disable it when the design allowance is insufficient
- [ ] T102 [US5] Run E13 full-audio Gemini 3.6 only on an approved bounded subset
  when research and per-route cost preflight pass; otherwise record blocked
- [ ] T103 [US5] Use E13 only as an upper-bound comparison and never promote P8
  if any production duration bucket can exceed the hard ceiling

**Gate I**: P6–P8 are optional challengers. Failure or ineligibility leaves the
best prior candidate intact.

## Phase 10: Final Selection, Fusion, and Confidence

- [ ] T104 [US5] Generate the P0–P8/E00–E13 comparison report with blocked,
  failed, rejected, and eligible states in
  `src/autoace/evaluation/reports.py`
- [ ] T105 [US5] Select the highest-scoring eligible candidate using the frozen
  rule, tone co-primary, paired intervals, and protected-field margin
- [ ] T106 [P] [US2] Write confidence leakage, OOD, missing-role, disagreement,
  missing-component, and provisional-state tests in
  `tests/evaluation/test_confidence.py`
- [ ] T107 [US2] Generate out-of-fold field margins, agreement, quality, role,
  OOD, and route features in `src/autoace/inference/confidence.py`
- [ ] T108 [US2] Compare regularized logistic/Platt and isotonic calibration
  under sample-size-aware grouped folds
- [ ] T109 [US2] Implement field and overall confidence calibration, or the
  conservative provisional path, in `src/autoace/inference/confidence.py`
- [ ] T110 [US4] Produce Brier, ECE, reliability, and sample-size limitation
  reports
- [ ] T111 Freeze the winning candidate, preprocessing, models, prompts, fusion,
  thresholds, cost reserves, and confidence configuration
- [ ] T112 Re-run development/calibration reproducibility from hashes before
  opening the final holdout

**Gate J**: Architecture selection is frozen before UI polish and holdout.

## Phase 11: Minimal Streamlit Product

- [ ] T113 [P] [US1] Write authentication, upload, validation, start, progress,
  retry, result, error, and export journey tests in
  `tests/integration/test_dashboard.py`
- [ ] T114 [US1] Implement secret-backed authentication in
  `src/autoace/ui/dashboard.py`
- [ ] T115 [US1] Implement ZIP/folder upload and manifest validation summary in
  `src/autoace/ui/dashboard.py`
- [ ] T116 [US1] Connect the frozen winner through one sequential batch worker
  in `src/autoace/ui/dashboard.py`
- [ ] T117 [US1] Implement queued/processing/complete/failed progress and
  filename-specific redacted errors
- [ ] T118 [US1] Implement compact results and filename-preserving JSON/CSV
  downloads
- [ ] T119 [US1] Keep `app.py` a thin Streamlit entry point with no database,
  broker, separate frontend, GPU, or model-selection logic
- [ ] T120 [US3] Enforce temporary cleanup and remote cache/privacy policy in the
  end-to-end application
- [ ] T121 [US3] Run a mixed batch under a 2 GB memory limit and verify progress,
  isolation, cost, cleanup, and exports
- [ ] T122 [US1] Conduct an operator walkthrough using only `quickstart.md`

**Gate K**: The dashboard exposes the winner; it does not choose or retune it.

## Phase 12: Holdout, Release, and Hosting

- [ ] T123 [US2] Open the untouched holdout once and generate final per-field
  metrics, confusion matrices, intervals, calibration, and failure analysis
- [ ] T124 [US3] Generate final cost by duration bucket, latency/RTF, peak RSS,
  cache effectiveness, and completion-rate reports
- [ ] T125 [US4] Generate `release/manifest.json` against
  `contracts/release-manifest.schema.json`
- [ ] T126 [US4] Include every accepted/rejected model revision, license,
  artifact hash, `.venv` lock hash, native runtime, prompt, and configuration
- [ ] T127 [P] [US4] Write `README.md`, deployment/operations documentation, and
  `docs/technical-memo.md`
- [ ] T128 [US4] Implement `scripts/verify_release.py` and reproduce the frozen
  result from the release manifest in a clean `.venv`
- [ ] T129 [US3] Complete every item in `checklists/model-quality.md`
- [ ] T130 [US4] Complete requirements traceability and confirm every FR has a
  test/task/evidence link
- [ ] T131 [US1] Deploy one Streamlit process to the approved 2 GB CPU host with
  secrets outside source control
- [ ] T132 [US1] Verify authenticated hosted upload-to-download behavior using a
  non-confidential release fixture
- [ ] T133 [US3] Block release on any failed contract, accuracy, cost, memory,
  privacy, license, reproducibility, cleanup, or reliability gate

## Dependency Summary

```text
Phase 1 .venv
    -> Phase 2 contracts/batch
    -> Phase 3 evaluation foundation
    -> Phase 4 P0/E00
       -> Phase 5 P1/E01-E04
       -> Phase 6 P2-P3/E05-E08
    -> Phase 7 cost/privacy/cache approval
       -> Phase 8 P4-P5/E09-E10
       -> Phase 9 P6-P8/E11-E13
    -> Phase 10 winner/confidence freeze
    -> Phase 11 Streamlit
    -> Phase 12 holdout/release/hosting
```

Local phases can proceed without paid-service approval. Accuracy selection
cannot complete without representative labels. Paid phases cannot proceed
without privacy and research-budget approval. Missing approval produces
schema-valid blocked experiment records, not invented results.
