# Audio Classification Experiment Plan

**Status**: Approved; translated into Spec Kit feature 001  
**Date**: 2026-08-01  
**Canonical for the next step**: Yes  
**Implementation agent**: GPT-5.6 Luna may implement the approved Spec Kit
tasks later. Luna is not an application dependency or inference model.

> This is the approved architecture source. The regenerated
> `specs/001-call-audio-analysis/` package is the executable implementation
> handoff. If the two conflict, stop and resolve the conflict before coding.

## 1. Goal

Find the most accurate production pipeline for all nine assignment outputs
without assuming that an LLM, an offline model, or a deterministic method is
best for every field.

The winner must:

- stay at or below USD 0.003 of external inference cost per audio minute;
- target USD 0.0024/minute to leave a 20% safety margin;
- run on one 2 GB RAM CPU host with peak RSS below 1.8 GB;
- require no GPU;
- use one simple Streamlit application;
- preserve confidential-call controls;
- produce exactly the required output contract;
- demonstrate accuracy on representative unseen calls.

Hosting is accounted for separately from external inference.

## 2. Fixed Engineering Constraints

### Python environment

Use Python 3.12 and a project-local virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Rules:

- All Python commands, tests, experiments, downloads, and Streamlit execution
  run inside `.venv`.
- Never install project packages globally.
- Add `.venv/` to `.gitignore`.
- Pin direct dependencies and create a reproducible lock/constraints file.
- Record Python, FFmpeg, operating-system, CPU, and model artifact versions.
- Model binaries live outside `.venv` under a versioned `models/` manifest.

### Runtime

- One file is processed at a time by default.
- Load heavyweight local models sequentially, not simultaneously.
- Prefer ONNX, TFLite, CTranslate2, or whisper.cpp over full training
  frameworks in production.
- A disposable subprocess may isolate each heavyweight model so memory is
  definitely released between stages.
- Full TensorFlow is prohibited from the production environment unless a
  measured result proves it indispensable and the 1.8 GB gate still passes.
- Raw and full-band audio remains available for noise and quality analysis;
  create a separate mono 16 kHz derivative for speech models.

## 3. Shared Processing and Evidence

Every candidate receives the same immutable source audio and preprocessing
revision.

### Deterministic evidence

Compute:

- duration, codec, sample rate, channel layout, and channel correlation;
- RMS/dBFS distribution, noise-floor and SNR proxies;
- clipping ratio, DC offset, crest factor, low-volume and saturation flags;
- spectral centroid, rolloff, flatness, bandwidth, and zero-crossing rate;
- transient/static, dropout, packet-loss/robotic, echo, and muffling proxies;
- speech ratio, pause distribution, and longest internal silence;
- customer-only pitch, energy, tempo, and variation where speaker attribution
  is reliable.

These measurements may decide technical fields but may not directly convert
loudness into emotion.

### Lightweight shared models

- **Silero VAD ONNX**: speech regions and silence. It is small and MIT-licensed.
- **DNSMOS P.835 ONNX challenger**: speech, background, and overall quality
  evidence.
- **YAMNet TFLite challenger**: acoustic-event candidates. Use the lightweight
  runtime; do not install full TensorFlow merely for YAMNet.
- **Local overlap challenger**: evaluate the official/gated pyannote
  overlapped-speech detector or a pinned lightweight conversion only after
  provenance, license, and parity checks.

No lightweight model is automatically part of the final system. Each must earn
inclusion through an isolated field-level ablation.

## 4. Candidate Pipelines

All candidates return the same internal evidence schema and exact public output
schema.

### P0 — Deterministic baseline

Components:

- FFmpeg/ffprobe;
- DSP features;
- Silero VAD;
- transparent field rules.

Purpose:

- zero-external-cost lower bound;
- reliable silence and obvious technical-quality baseline;
- validation of contracts, metrics, and batch execution.

Expected weakness: semantic emotion, customer role, open-text noise naming, and
overlap in mono/dual-mono audio.

### P1 — Lightweight local specialists

Components:

- P0;
- DNSMOS P.835;
- YAMNet TFLite;
- local overlap challenger.

Purpose: determine how far specialized acoustic models can go with no API.

Each specialist is tested individually and together. A specialist is removed if
it does not improve its target field, increases another field's error, violates
licensing, or pushes peak RSS to 1.8 GB.

### P2 — Local emotion representation

Components:

- P1;
- one local speech-emotion challenger at a time;
- small calibrated field classifier or transparent mapping.

Initial challengers:

1. SpeechBrain wav2vec2 IEMOCAP emotion model.
2. emotion2vec base embeddings plus a regularized shallow classifier, only if
   its model license is approved.

Limitations that must be tested:

- IEMOCAP labels do not match the five assignment labels;
- acted/public emotion data differs from production calls;
- emotion2vec base is a representation model, not a ready-made assignment
  classifier;
- agent or television speech may be mistaken for the customer;
- English-only and multilingual behavior may differ.

These models may become supporting evidence even if they are not good enough to
own the tone decision.

### P3 — Local ASR plus classical semantic model

Components:

- best local acoustic pipeline from P0–P2;
- whisper.cpp or faster-whisper tiny/base on CPU, INT8 where supported;
- customer-role-aware transcript segmentation where reliable;
- regularized text/prosody classifier or lexicon baseline.

Run tiny and base as separate experiments. The official whisper.cpp estimates
approximately 273 MB for tiny and 388 MB for base, making both plausible on a
2 GB host when loaded sequentially.

Purpose: test whether local transcript semantics improve tone and intensity
enough to justify latency and role-attribution risk.

Do not retain ASR if Gemini audio already supplies more accurate semantics and
ASR has no measurable incremental contribution.

### P4 — Gemini 3.5 audio-only

Components:

- one paid, approved Gemini 3.5 Flash-Lite Flex full-audio request;
- compact structured observation;
- exact schema normalization.

Purpose: isolate the model's raw ability on customer role, semantic emotion,
paralinguistics, noise naming, and mono overlap.

The model does not receive supplied labels and does not return public
confidence directly.

### P5 — Gemini 3.5 plus deterministic computation

Components:

- P4;
- P0 deterministic evidence;
- field-specific fusion.

Expected role:

- Gemini leads semantic tone, role attribution, open-text noise type, and
  mono/dual-mono overlap;
- deterministic evidence leads silence and strong technical defects;
- both contribute independently to noise presence/severity and intensity.

This is the primary low-cost hybrid candidate.

### P6 — Gemini 3.5 plus accepted local specialists

Components:

- P5;
- only the DNSMOS, YAMNet, overlap, emotion, or ASR components whose previous
  ablations showed an incremental field gain;
- field-specific calibrated fusion.

Purpose: test whether offline specialists correct Gemini errors without adding
unnecessary latency and memory.

### P7 — Optional Gemini 3.6 text adjudication

Components:

- P5 or P6;
- compact per-file evidence sent as text to Gemini 3.6 Flash Flex;
- multiple files in one adjudication batch.

Rules:

- no audio is sent to 3.6 by default;
- the stage is optional and cost-preflighted;
- failure returns the already valid P5/P6 result;
- it ships only if locked evaluation proves a credible accuracy gain;
- it is skipped when short-batch overhead would exceed the design allowance.

### P8 — Full-audio Gemini 3.6 upper bound

This is an experiment, not a presumed production candidate. Run it only on a
bounded validation subset when the experiment budget permits.

Purpose: measure the maximum benefit of stronger full-audio inference and
decide whether P7 captures most of that benefit at lower cost.

It is ineligible for production if any duration bucket violates the external
cost gate.

## 5. Experiment Matrix

Run components incrementally so every cost and accuracy change is attributable.

| ID | Pipeline | External cost | Main question |
|---|---|---:|---|
| E00 | P0 | $0 | deterministic lower bound |
| E01 | P0 + DNSMOS | $0 | quality/noise severity gain? |
| E02 | P0 + YAMNet | $0 | noise presence/type gain? |
| E03 | P0 + overlap model | $0 | mono-overlap gain? |
| E04 | best E01–E03 combined | $0 | complementary or redundant? |
| E05 | E04 + SpeechBrain SER | $0 | tone/intensity gain? |
| E06 | E04 + emotion2vec | $0 | better emotion representation? |
| E07 | E04 + Whisper tiny | $0 | transcript semantics worth it? |
| E08 | E04 + Whisper base | $0 | base improves enough over tiny? |
| E09 | P4 Gemini 3.5 alone | API | raw audio-model baseline |
| E10 | P5 Gemini 3.5 + P0 | API | core hybrid gain |
| E11 | P6 accepted specialists | API | local correction gain |
| E12 | P7 batched 3.6 text | API | stronger rubric mapping gain? |
| E13 | P8 3.6 full audio subset | API | upper bound only |

Additional prompt, threshold, or model variants are allowed only when
pre-registered. Do not repeatedly tune against the final holdout.

## 6. Evaluation Data

The three supplied calls are smoke fixtures only. They verify decoding,
contracts, and obvious regression; they cannot select a pipeline.

### Required representative set

Preferred target: at least 300 human-adjudicated production calls. If that is
not available:

- use the largest approved set available;
- report uncertainty rather than overclaim performance;
- use public data only for component preselection;
- reserve real production calls for final domain evaluation.

The set should cover:

- all emotion labels and boundary cases;
- quiet negative and loud positive speech;
- customer/agent role ambiguity;
- television and other background speech;
- music, traffic, office chatter, wind, typing, mechanical noise, and static;
- clear, clipped, muffled, low-volume, echoing, and packet-loss audio;
- no overlap, brief crosstalk, and meaningful overlap;
- short, medium, and long internal silence;
- mono, genuine stereo, and dual-mono;
- expected languages, accents, codecs, and call durations.

Double-label at least 20%, adjudicate disagreements, and report inter-rater
agreement. Split by call and speaker before any feature, prompt, threshold, or
calibrator is fitted.

### Splits

- Development folds: grouped cross-validation for component and fusion work.
- Calibration split: untouched by model fitting.
- Final holdout: opened once after pipeline and thresholds are frozen.
- Supplied three calls: separate smoke-only partition.

## 7. Metrics and Selection

### Output metrics

- Emotional tone: macro F1, accuracy, per-class precision/recall/F1.
- Emotional intensity: macro F1 and balanced accuracy.
- Boolean fields: F1, precision, recall, and balanced accuracy.
- Enum fields: macro F1 and confusion matrix.
- Noise type: normalized exact match plus blinded semantic match under a frozen
  taxonomy.
- Confidence: Brier score, expected calibration error, and reliability bins.

### Operational metrics

- external cost per audio minute by duration bucket;
- p50/p95/p99 API tokens, thinking tokens, and latency;
- local real-time factor;
- baseline and peak RSS;
- per-file failure/completion rate;
- remote cleanup and retry success.

### Selection rule

Hard gates apply first:

1. exact schema and cross-field invariants;
2. external cost <= USD 0.003/minute for every legal production route;
3. release target <= USD 0.0024/minute on the representative distribution;
4. peak RSS <1.8 GB;
5. approved privacy and model licenses;
6. per-file failure isolation and reproducibility.

Among eligible candidates:

- choose the highest macro-average of predeclared per-field scores;
- treat emotional-tone macro F1 as a co-primary metric;
- reject a candidate that materially harms a protected field even when its
  average rises;
- use paired bootstrap confidence intervals;
- prefer the simpler/cheaper candidate when gains are within measurement
  uncertainty.

Freeze the exact metric aggregation and material-regression threshold before
running E09–E13.

## 8. Fusion and Confidence

Do not use one generic majority vote.

Create one decision path per field:

- emotion: customer-attributed semantic and paralinguistic evidence;
- intensity: semantic escalation, persistence, and customer prosody;
- noise: audio event plus non-speech spectral evidence;
- quality: clipping, dropouts, bandwidth, echo, DNSMOS, and intelligibility;
- overlap: local overlap model or Gemini temporal evidence, depending on
  channel layout;
- silence: VAD timing rule.

When sufficient labels exist, fit regularized shallow calibrators using
out-of-fold predictions. Otherwise use frozen transparent policies.

Public confidence is calibrated probability of overall correctness, not a
model's self-reported certainty. If the dataset is too small, mark it
internally as provisional and report that limitation.

## 9. External Model Cost Control

Local models have zero external per-minute cost; their CPU work is included in
hosting.

Current planning assumptions:

- Gemini audio: 32 input tokens/second.
- Gemini 3.5 Flash-Lite Flex: $0.15/M input and $1.25/M
  output-plus-thinking tokens.
- Gemini 3.6 Flash Flex: $0.75/M input and $3.75/M
  output-plus-thinking tokens.

The previous three-file example produced:

| Production route | Planning estimate |
|---|---:|
| Gemini 3.5 full audio only | about $0.000611/audio-minute |
| Gemini 3.5 audio + optional batched 3.6 text | about $0.001287/audio-minute |
| Internal operating limit | $0.002400/audio-minute |
| Contract ceiling | $0.003000/audio-minute |

These are not release guarantees. The implementation must:

- revalidate prices and model IDs;
- count or conservatively estimate input before generation;
- reserve measured p99 output and hidden-thinking usage;
- capture actual provider usage;
- compute allowance from total eligible audio duration;
- disable optional stages first;
- never fall back silently from Flex to a more expensive tier;
- reject a route that cannot prove compliance.

### Experiment-spend control

Production cost and one-time research cost are different. Multiple API
experiments necessarily analyze some clips more than once.

Control research spend by:

- caching immutable remote observations by source hash, model, prompt, schema,
  and configuration;
- never repeating an identical paid request;
- starting with a small development subset;
- promoting only promising variants to the full development set;
- requiring explicit approval for a configurable total research budget;
- recording the cost of every experiment.

A sensible initial research cap is USD 10. It is not authorized spend merely
because it appears in this plan; execution requires user approval and API
credentials.

## 10. Privacy and Licensing

- No production call leaves the host without approval for the exact provider,
  billing project, endpoint, region, and retention controls.
- Use paid service configuration; disable optional data sharing.
- Prefer inline audio. Delete remote file uploads immediately in success and
  failure paths.
- Do not log audio, transcripts, prompt content, or call-derived rationales.
- Store only hashes, versions, usage, costs, statuses, and redacted errors in
  operational logs.
- Pin and hash every local model artifact.
- Record code and model licenses separately.
- Treat gated model access or unclear custom licenses as a release blocker.

## 11. Minimal Product After Model Selection

Build the dashboard only after the experiment winner is frozen.

One Streamlit process provides:

- secret-backed login;
- folder or safe ZIP upload;
- CSV manifest validation;
- start control;
- simple per-file progress;
- per-file results and redacted errors;
- filename-preserving CSV and JSON downloads.

No React application, database, distributed queue, Kubernetes cluster, or GPU
service is planned.

Expected base hosting is one 1-vCPU/2-GB Linux VM. Benchmark shared-CPU latency
before release; increase CPU only if measured throughput is unacceptable.

## 12. Execution Phases

### Phase A — Reproducible foundation

1. Create `.venv` and dependency lock.
2. Implement exact contracts and safe batch handling.
3. Implement audio probing/decoding and experiment registry.
4. Create grouped dataset splits and metrics.
5. Build cost, latency, and peak-RSS measurement.

### Phase B — Local evidence

1. Implement P0.
2. Run E00.
3. Add and ablate DNSMOS, YAMNet, and overlap.
4. Test local emotion challengers.
5. Test Whisper tiny/base and semantic features.
6. Freeze the best zero-API pipeline.

### Phase C — Gemini and hybrid evidence

1. Obtain privacy and spend approval.
2. Run E09 Gemini 3.5 alone.
3. Run E10 computation hybrid.
4. Add only proven local specialists for E11.
5. Measure and freeze token reserves by duration bucket.

### Phase D — Strong-model experiment

1. Run batched text-only 3.6 adjudication E12.
2. Optionally run a bounded full-audio 3.6 upper-bound E13.
3. Select the highest-scoring eligible pipeline.

### Phase E — Calibration and holdout

1. Freeze preprocessing, prompts, models, fusion, and thresholds.
2. Fit confidence without leakage.
3. Open the final holdout once.
4. Produce field, calibration, cost, latency, memory, and failure reports.

### Phase F — Product and release

1. Implement the minimal Streamlit workflow.
2. Run the winner under a 2 GB memory limit.
3. Generate the immutable release manifest.
4. Deploy to the approved 2 GB CPU host.
5. Verify authenticated upload-to-download behavior.

## 13. Preconditions for Paid Experiments and Release

Execution decisions still requiring explicit approval or evidence:

1. Confirm whether a representative labelled AutoAce set can be provided.
2. Confirm whether paid Gemini use is allowed for confidential calls.
3. Approve a maximum one-time experiment API budget before paid requests run.
4. Revalidate provider pricing, model IDs, terms, and local model licenses.

The implementation package is `specs/001-call-audio-analysis/`, including the
Luna task-by-task handoff. Application code still does not exist.

## 14. Primary Technical References

- Gemini audio:
  https://ai.google.dev/gemini-api/docs/audio
- Gemini pricing:
  https://ai.google.dev/gemini-api/docs/pricing
- Gemini Flex inference:
  https://ai.google.dev/gemini-api/docs/flex-inference
- Silero VAD:
  https://github.com/snakers4/silero-vad
- DNSMOS:
  https://github.com/microsoft/DNS-Challenge
- YAMNet:
  https://github.com/tensorflow/models/tree/master/research/audioset/yamnet
- Whisper model card:
  https://github.com/openai/whisper/blob/main/model-card.md
- whisper.cpp:
  https://github.com/ggml-org/whisper.cpp
- SpeechBrain IEMOCAP emotion model:
  https://huggingface.co/speechbrain/emotion-recognition-wav2vec2-IEMOCAP
- emotion2vec:
  https://huggingface.co/emotion2vec/emotion2vec_base
- pyannote overlap detection:
  https://huggingface.co/pyannote/overlapped-speech-detection
