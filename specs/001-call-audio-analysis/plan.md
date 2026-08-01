# Implementation Plan: Cost-Bounded Call Audio Analysis

**Branch**: `001-call-audio-analysis` | **Date**: 2026-08-01 | **Spec**:
[spec.md](spec.md)

**Input**: Feature specification from
`/specs/001-call-audio-analysis/spec.md`

## Summary

Use an experiment-first program to select the best eligible pipeline, then
build one authenticated Streamlit application that processes batches
sequentially on a 2 GB CPU host. Accuracy comes from field-specific evidence,
not a predetermined all-purpose model:

1. FFmpeg plus NumPy/SciPy and Silero VAD derive reliable, inexpensive
   signal-level evidence from both original full-band and mono 16 kHz audio.
2. Small ONNX/TFLite challengers (DNSMOS P.835 for quality and YAMNet for
   acoustic events) are retained only if blinded ablations improve their target
   fields while peak RSS remains below 1.8 GB.
3. Local overlap, emotion, and tiny/base Whisper ASR challengers test whether a
   zero-API or locally enriched route can compete within the same memory limit.
4. One paid, approved Gemini 3.5 Flash-Lite Flex full-audio request supplies
   customer-role, semantic, paralinguistic, noise-type, and mono-overlap
   evidence in compact structured form.
5. A field-specific fusion layer resolves deterministic and model evidence.
6. Gemini 3.6 Flash Flex may adjudicate only compact text evidence across a
   cost-efficient batch. It never receives audio by default and ships disabled
   unless it produces a statistically credible locked-validation gain.

P0–P8 and E00–E13 are compared on identical grouped data. The 3.5 audio plus
local-computation path is the primary cost/accuracy hypothesis, not a
preselected winner. The 3.6 text adjudicator is an accuracy option, not a
dependency. No GPU, local generative model, database, queue, or custom frontend
is planned.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Streamlit, Pydantic v2, `google-genai`, NumPy, SciPy,
SoundFile, ONNX Runtime CPU, Silero VAD ONNX, FFmpeg/ffprobe; experimental
extras isolate MediaPipe/TFLite YAMNet, DNSMOS P.835 ONNX, pyannote overlap,
SpeechBrain/emotion2vec, and whisper.cpp or faster-whisper tiny/base

**Storage**: Ephemeral per-batch files, content-addressed paid-observation cache,
and append-only JSONL experiment/cost artifacts; no database

**Testing**: pytest, Hypothesis for contracts/invariants, JSON Schema
validation, golden audio fixtures, grouped evaluation scripts, memory and cost
profiling

**Target Platform**: Linux CPU container or VM, 2 GB RAM, no GPU; one Streamlit
process with bounded sequential workers

**Project Type**: Single Python web application with an offline evaluation CLI
sharing the same pipeline

**Performance Goals**: Peak RSS below 1.8 GB; valid batches progress without
global failure; report real-time factor rather than promise an unmeasured
latency; remote spend target <= USD 0.0024/audio-minute and hard ceiling
<= USD 0.003/audio-minute

**Constraints**: Project-local Python 3.12 `.venv`; confidential production
calls; approved paid remote endpoint only; no silent standard-tier fallback;
exact nine-field output; independent field decisions; three visible calls
cannot train or validate generalization

**Scale/Scope**: Evaluation-sized ZIP/folder batches on one host, sequential
audio processing, one simple dashboard, CSV/JSON export

## Architecture and Decision Flow

```text
authenticated upload
        |
safe archive + manifest validation
        |
ffprobe + hash + duration ledger
        |
        +--> original full-band DSP -----------+
        |    quality/noise/channel evidence    |
        |                                      v
        +--> mono 16 kHz -> Silero VAD --> field evidence
        |                  silence/speech      |
        |                                      |
        +--> optional DNSMOS/YAMNet challengers+
        |
experiment router --------------------------------------+
  | P0 deterministic                                   |
  | P1 local specialists                               |
  | P2 local emotion                                   |
  | P3 local ASR + classical semantics                 |
  | P4 Gemini 3.5 audio (privacy + cost preflight)     |
  | P5 Gemini 3.5 + deterministic                      |
  | P6 Gemini 3.5 + accepted local specialists         |
  | P7 optional batched Gemini 3.6 text adjudication   |
  | P8 bounded Gemini 3.6 full-audio upper bound       |
  +----------------------------------------------------+
        |
field-specific fusion + confidence calibration
        |
exact schema validation -> UI + CSV/JSON
```

### Field ownership

| Output | Primary evidence | Corroborating evidence | Prohibited shortcut |
|---|---|---|---|
| Tone | Gemini customer-role semantic + paralinguistic observation | pitch/energy/tempo summaries, optional text adjudication | loudness alone |
| Intensity | semantic escalation + prosodic strength over customer turns | temporal persistence and model agreement | raw RMS threshold |
| Noise present/type | Gemini audio event observation | YAMNet candidate, non-speech spectral evidence | poor quality alone |
| Noise severity | interference with speech + estimated SNR/noise occupancy | DNSMOS BAK, Gemini observation | presence implies severity |
| Audio quality | clipping/dropout/bandwidth/echo/level evidence | DNSMOS SIG/OVRL, Gemini observation | noise present implies impaired |
| Overlap | Gemini temporal speaker observation for mono/dual-mono | independent-channel VAD only for verified true stereo | channel coincidence on dual-mono |
| Long silence | Silero VAD internal gaps and duration-aware threshold | Gemini timestamps only for ambiguity | transcript punctuation |
| Confidence | held-out correctness calibrator over field margins, agreement, OOD and quality | conservative aggregation | raw model self-rating |

## Cost Controller

Prices are a versioned 2026-08-01 planning snapshot and MUST be revalidated
before implementation and release.

| Service | Flex input | Flex output + thinking | Planned use |
|---|---:|---:|---|
| Gemini 3.5 Flash-Lite | $0.15/M tokens | $1.25/M tokens | one full-audio structured observation |
| Gemini 3.6 Flash | $0.75/M tokens | $3.75/M tokens | optional batched text-only adjudication |

Gemini audio is budgeted at 32 input tokens/second. For each batch:

```text
contract_limit = total_audio_minutes * 0.003
design_limit   = total_audio_minutes * 0.0024

projected_cost =
  sum((counted_or_estimated_input_tokens * versioned_input_rate)
      + (validated_p99_output_and_thinking_tokens * versioned_output_rate))
```

The controller performs a local duration estimate before upload and, where the
API supports the request shape, token counting before generation. Hidden
thinking is not assumed to be controlled by the visible-output limit, so the
reserve comes from a measured p99 plus a safety factor. Actual usage metadata
is recorded after every request.

The optional 3.6 stage runs only when the remaining design allowance covers the
entire evidence batch. Flex 503/timeout responses receive bounded retries; they
never trigger an unapproved standard-tier request. Very short clips are grouped
for the 3.5 request only if blinded tests show no cross-file accuracy loss.
Otherwise the cost controller evaluates the allowance across the submitted
batch and disables optional work first. Identical paid observations are cached
by source, model, prompt, schema, and configuration hashes. Paid experiments
also require a separately approved total research-spend cap.

### Supplied-batch planning example

The three supplied files total 237.841 seconds (3.964 minutes). This example
uses deliberately explicit reserves rather than presenting them as measured:

- Per-file 3.5 request: 180 prompt tokens and 320 output+thinking tokens.
- One three-file 3.6 text batch: 260 fixed + 220 input tokens/file and
  200 fixed + 110 output+thinking tokens/file.

| Stage | Estimated batch cost |
|---|---:|
| Three Gemini 3.5 audio observations | $0.002423 |
| One optional Gemini 3.6 text adjudication batch | $0.002678 |
| Total | $0.005101 |
| Total per audio minute | **$0.001287/min** |
| Design allowance | $0.009514 |
| Contract allowance | $0.011892 |

For one 30.946-second clip, an unbatched optional 3.6 adjudication would push
the example to roughly $0.00337/minute, so it MUST be skipped. These are
planning values; release pricing and token reserves come only from measured
usage. Hosting remains separate.

## Model-Selection Experiment

All candidates use the same frozen preprocessing, splits, metrics, and public
contract:

| Candidate | Components | Purpose |
|---|---|---|
| P0 | DSP + Silero | deterministic zero-API lower bound |
| P1 | P0 + DNSMOS + YAMNet + local overlap challengers | local acoustic specialists |
| P2 | P1 + one local emotion challenger | offline emotion evidence |
| P3 | best local path + Whisper tiny/base + classical semantics | fully local semantic challenger |
| P4 | Gemini 3.5 Flash-Lite audio only | remote audio-model baseline |
| P5 | P4 + P0 field-specific fusion | primary hybrid hypothesis |
| P6 | P5 + only accepted local specialists | maximum evidence hybrid |
| P7 | P5/P6 + batched Gemini 3.6 text | optional stronger rubric adjudication |
| P8 | Gemini 3.6 full audio on bounded subset | upper-bound experiment only |

Experiments E00–E13 isolate DNSMOS, YAMNet, overlap, SpeechBrain emotion,
emotion2vec, Whisper tiny, Whisper base, Gemini 3.5, hybrid fusion, accepted
specialists, batched 3.6 text, and bounded 3.6 audio. Exact definitions are
versioned in `configs/experiments/`.

P7 becomes default only if its locked-validation score improves credibly over
the best cheaper candidate and no protected field materially regresses. P8 is
not eligible unless measured p99 spend remains below the design target for the
actual duration distribution. Remove every component that does not earn its
memory, latency, cost, license, and accuracy.

## Evaluation and Accuracy Protocol

1. Create an annotation guide from the assignment definitions, including
   examples at field boundaries and customer-role rules.
2. Acquire a representative, human-adjudicated set. Target at least 300 calls
   spanning languages, channels, durations, emotions, noise, defects, overlap,
   and silence; if fewer are available, widen uncertainty and do not claim
   class-complete performance.
3. Double-label at least 20%, adjudicate disagreements, report inter-rater
   agreement, and freeze dataset/model cards.
4. Group by call and speaker; create development folds plus one untouched final
   holdout. Keep the three supplied files as smoke fixtures.
5. Predeclare:
   - tone: macro F1, per-class precision/recall/F1;
   - enum/boolean fields: macro F1 and balanced accuracy;
   - noise type: normalized exact match plus human semantic match on a frozen
     taxonomy mapping;
   - confidence: Brier score and expected calibration error;
   - overall selection: assignment-weighted normalized field score.
6. Use paired bootstrap confidence intervals. Require no material protected
   field regression and a credible overall gain before adding complexity.
7. Fit field calibrators on out-of-fold predictions only. Fit the final
   confidence calibrator after configuration freeze and before the untouched
   holdout. If sample size is inadequate, emit conservative provisional
   confidence and label it honestly in internal reports.
8. Stress-test channel layouts, short/long clips, quiet negative emotion, loud
   positive speech, television voices, static, clipping, packet loss, overlap,
   and long silence.

## Privacy and Operational Policy

- No real call leaves the host until AutoAce approves the endpoint and region.
- Use a paid billing project; disable optional data sharing/logging features;
  document whether zero-data-retention controls are available and required.
- Prefer inline requests within service limits. If a remote File API is needed,
  delete the file immediately in a `finally` path and verify the deletion.
- Do not log raw audio, transcripts, prompts containing call content, or remote
  responses. Log hashes, durations, versions, costs, statuses, and redacted
  errors.
- Use per-batch temporary directories, safe archive extraction, size/count
  limits, randomized internal paths, and automatic cleanup.
- Review licenses and hashes for every downloaded model artifact.

## Constitution Check

### Before Phase 0 research

| Gate | Status | Evidence |
|---|---|---|
| Measured accuracy | PASS | P0–P8, E00–E13, field metrics, ablations, holdout |
| Independent fields | PASS | Field-ownership table and prohibited shortcuts |
| Leakage prevention | PASS | call/speaker grouping; supplied calls are smoke-only |
| Privacy | PASS | approval, paid endpoint, deletion, fail-closed local route |
| Cost | PASS | design/hard gates, p99 reserves, no standard fallback |
| Minimal product | PASS | single Streamlit process, files only, no GPU/services |
| Honest confidence | PASS | held-out calibrator or explicit provisional state |

### After Phase 1 design

PASS. Contracts preserve exact output and cross-field invariants; the data model
keeps internal evidence separate from public results; the source tree keeps UI,
pipeline, evaluation, and contracts in one Python project. No constitutional
exception is requested.

## Project Structure

### Documentation

```text
specs/001-call-audio-analysis/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── traceability.md
├── LUNA_HANDOFF.md
├── tasks.md
├── checklists/
│   ├── requirements.md
│   └── model-quality.md
└── contracts/
    ├── result.schema.json
    ├── manifest.schema.json
    ├── evidence.schema.json
    ├── experiment.schema.json
    ├── release-manifest.schema.json
    └── openapi.yaml
```

### Planned source code

```text
app.py
pyproject.toml
.gitignore
src/autoace/
├── config.py
├── contracts.py
├── domain.py
├── batch.py
├── security.py
├── audio/
│   ├── decode.py
│   ├── dsp.py
│   ├── vad.py
│   ├── quality.py
│   ├── events.py
│   ├── overlap.py
│   ├── emotion.py
│   └── asr.py
├── inference/
│   ├── cost.py
│   ├── gemini_audio.py
│   ├── adjudicator.py
│   ├── fusion.py
│   ├── confidence.py
│   └── observation_cache.py
├── evaluation/
│   ├── datasets.py
│   ├── metrics.py
│   ├── experiments.py
│   ├── registry.py
│   └── reports.py
└── ui/
    └── dashboard.py
tests/
├── contract/
├── unit/
├── integration/
├── evaluation/
├── performance/
└── fixtures/
models/
└── manifest.json
configs/
├── prompts/
├── fusion/
├── experiments/
└── pricing/
scripts/
├── evaluate.py
├── profile_memory.py
└── verify_release.py
```

**Structure Decision**: A single Python project is enough. The same pure
pipeline is called by Streamlit and the offline evaluation scripts. Native model
runtimes are loaded sequentially and explicitly released between files.

## Delivery Phases

1. **Environment and contracts**: `.venv`, locks, schemas, safe batch I/O,
   FFmpeg, reproducible smoke fixtures.
2. **Evaluation foundation**: annotation guide, grouped dataset splits,
   metrics, experiment registry/cache, cost/memory harness.
3. **P0/P1 local acoustics**: DSP, Silero, DNSMOS, YAMNet, overlap ablations.
4. **P2/P3 local semantics**: emotion challengers and Whisper tiny/base
   experiments.
5. **P4/P5 remote baseline**: approved 3.5 structured audio evidence, privacy,
   deletion, cost ledger, hybrid fusion.
6. **P6/P7/P8 accuracy challengers**: accepted local specialists, optional 3.6
   text adjudication, bounded 3.6 audio upper bound.
7. **Fusion and confidence**: field-specific policies and out-of-fold
   calibration; freeze the winner.
8. **Minimal dashboard**: authentication, upload, progress, results, downloads.
9. **Release proof**: locked holdout, schema/cost/privacy/memory/latency reports,
   manifest, quickstart, hosted verification.

## Complexity Tracking

No constitutional violations. Experimental extras and the optional second
remote model are isolated behind accuracy, licensing, memory, and cost gates
and can be removed without changing the product contract or dashboard.
