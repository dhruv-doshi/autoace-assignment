# Data Model

The public prediction stays deliberately small. All evidence, costs, and audit
records are internal artifacts and MUST NOT leak into the assignment result.

## Batch

| Field | Type | Rules |
|---|---|---|
| `batch_id` | UUID | generated server-side |
| `created_at` | timestamp | UTC |
| `status` | enum | validating, ready, processing, complete, partial, failed |
| `total_audio_seconds` | decimal | sum of eligible probed durations |
| `design_allowance_usd` | decimal | minutes × 0.0024 |
| `hard_allowance_usd` | decimal | minutes × 0.003 |
| `projected_cost_usd` | decimal | conservative preflight |
| `actual_cost_usd` | decimal | usage-ledger sum |
| `items` | AudioItem[] | one per manifest/audio entry |
| `temp_directory` | path | private randomized directory; never exported |

State transitions:

```text
validating -> ready -> processing -> complete
     |          |           |          ^
     +-> failed +-> failed  +-> partial+
```

## AudioItem

| Field | Type | Rules |
|---|---|---|
| `item_id` | UUID | internal |
| `batch_id` | UUID | parent |
| `original_name` | string | safe basename and export key |
| `sha256` | string | source identity |
| `media_type` | string | probed, not trusted extension |
| `duration_seconds` | decimal | ffprobe |
| `sample_rate_hz` | integer | positive |
| `channels` | integer | bounded supported count |
| `channel_layout` | string | mono/stereo/unknown |
| `channel_correlation` | number/null | used to detect dual-mono |
| `status` | enum | queued, processing, complete, failed, skipped |
| `error` | ItemError/null | redacted |
| `prediction` | Prediction/null | exactly one on success |

## AcousticEvidence

Versioned internal record:

- source hash and preprocessing revision;
- original/full-band and 16 kHz derivative metadata;
- VAD segments, speech ratio, longest internal non-speech span;
- RMS/dBFS distribution, robust noise floor/SNR proxy, clipping ratio, DC
  offset, crest factor;
- spectral centroid, rolloff, flatness, bandwidth, zero-crossing summaries;
- transient, dropout, packet-loss/robotic and echo proxies;
- pitch/energy/tempo summaries calculated only on eligible customer speech when
  speaker attribution is available;
- optional DNSMOS SIG/BAK/OVRL;
- optional YAMNet top acoustic events with temporal occupancy;
- quality flags, OOD flags, and per-feature validity.

Every value records units, aggregation, and unavailable reason. NaN and infinity
are forbidden at serialization boundaries.

## RemoteObservation

| Field | Type | Rules |
|---|---|---|
| `provider` | string | approved provider |
| `model_id` | string | pinned stable ID |
| `mode` | enum | audio_observer, text_adjudicator |
| `prompt_version` | string | content hash |
| `request_id` | string | provider trace ID when available |
| `observations` | object[] | per-file structured evidence |
| `input_tokens` | integer | provider usage |
| `output_tokens` | integer | provider usage |
| `thinking_tokens` | integer/null | explicit when reported |
| `price_snapshot` | string | versioned config ID |
| `cost_usd` | decimal | deterministic from usage |
| `file_deleted` | boolean/null | required true when file upload was used |
| `status` | enum | success, retryable_failure, terminal_failure |

The observation contains field candidates, concise evidence spans/timestamps,
customer-role certainty, ambiguity flags, and OOD flags. Its self-confidence is
diagnostic only.

## CandidateDefinition

Immutable description of one P0–P8 pipeline:

| Field | Meaning |
|---|---|
| `candidate_id` | P0 through P8 |
| `revision` | content hash of the definition |
| `components` | ordered local/remote/fusion stages |
| `field_ownership` | primary and corroborating evidence per public field |
| `preconditions` | data, license, privacy, cost, and model-access requirements |
| `runtime_policy` | sequential/subprocess loading, threads, and memory limit |
| `cost_policy` | allowed remote stages and priority when allowance is scarce |
| `configuration_hashes` | preprocessing, prompts, thresholds, and model configs |

Candidate definitions are configuration, not code branches. Two experiment runs
may compare candidates while sharing decoded audio and immutable observations.

## ObservationCacheEntry

| Field | Type | Rules |
|---|---|---|
| `cache_key` | SHA-256 | source + provider/model + prompt + schema + config hashes |
| `source_sha256` | SHA-256 | exact source identity |
| `request_identity` | object | no secret or raw call content |
| `observation_sha256` | SHA-256 | integrity of structured result |
| `usage` | object | input/output/thinking counts |
| `cost_usd` | decimal | immutable actual charge estimate |
| `privacy_approval_id` | string | required for real calls |
| `remote_file_deleted` | boolean/null | true when upload path used |
| `created_at` | timestamp | UTC |
| `status` | enum | complete, invalid, quarantined |

Only `complete` entries with matching hashes and current eligibility may be
reused. A price change does not invalidate the observation, but reports retain
the original price snapshot and cost.

## Prediction

The public form is defined by `contracts/result.schema.json` and contains only:

- `emotional_tone`
- `emotional_intensity`
- `background_noise_present`
- `background_noise_type`
- `background_noise_severity`
- `audio_quality`
- `speaker_overlap_present`
- `long_silence_present`
- `confidence`

Internal prediction metadata stores field candidates, chosen source/policy,
calibrated probability, disagreement, override reason, fusion version, and
contract-validation status.

Invariants:

- no noise -> type is empty and severity is none;
- noise present -> type is non-empty and severity is low/medium/high;
- confidence is finite in [0, 1];
- success requires exactly the public properties and legal enum values.

## ExperimentRun

| Field | Meaning |
|---|---|
| `run_id` | immutable experiment ID |
| `experiment_id` | E00 through E13 |
| `dataset_version` | hashes, label guide, and group split |
| `candidate_id` | P0 through P8 plus definition hash |
| `fold_or_holdout` | split identity |
| `environment` | `.venv` lock, Python, OS, CPU, FFmpeg, native runtimes |
| `field_metrics` | per-field point estimates and confidence intervals |
| `calibration_metrics` | Brier score, ECE, reliability bins |
| `cost_metrics` | total, per-minute, p50/p95/p99 by duration bucket |
| `latency_metrics` | real-time factor and request latency |
| `memory_metrics` | baseline and peak RSS |
| `failures` | counts and categorized causes |
| `gate_results` | accuracy, privacy, cost, memory, contract |
| `cache_summary` | remote hits, misses, avoided requests, and paid spend |

Valid lifecycle:

```text
declared -> eligible -> running -> complete -> accepted/rejected
                |          |
                +-> blocked+-> failed
```

An experiment is `blocked`, not failed, when it lacks data, approval, license,
model access, or research-budget authority.

## ReleaseManifest

Immutable JSON containing:

- source revision and dependency lock hash;
- `.venv` creation instructions and Python/native runtime versions;
- local model names, revisions, licenses, artifact hashes;
- remote model IDs, prompt hashes, endpoint mode, and price snapshot;
- preprocessing, feature, fusion, threshold, and calibration versions;
- dataset/split/annotation-guide versions;
- result/evidence schema versions;
- evaluation run IDs and gate results;
- winning candidate definition and rejected challenger summaries;
- build timestamp and target-platform profile.

## Retention

- Raw batch files and derivatives: private temporary storage, deleted at the end
  of the configured short batch window.
- Remote uploaded files: deleted immediately in a success/failure cleanup path.
- Predictions and experiment summaries: downloadable or retained as configured,
  but contain no raw audio.
- Operational logs: hashes and redacted metadata only; never raw audio,
  transcript, prompt content, or call-derived rationale.
