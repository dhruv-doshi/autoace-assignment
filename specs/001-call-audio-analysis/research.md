# Research and Architecture Decision Record

**Date**: 2026-08-01  
**Decision scope**: Highest defensible output accuracy under USD 0.003/audio
minute and a 2 GB CPU host

## Recovered Session Context

The older session did not ultimately propose a “Gemini 3.5” production design.
It progressed from CPU-only Whisper/Silero/YAMNet/DSP ideas to a hybrid using
full-audio Gemini 3.6 Flash plus local deterministic acoustics. The useful idea
was multimodal audio reasoning plus computation. Its original cost estimate was
too optimistic for short clips because fixed prompt/output/thinking overhead
was divided by a full minute, and it treated overlap rules too casually for
dual-mono recordings.

This plan keeps the useful hybrid principle, moves full-audio inference to the
much cheaper Gemini 3.5 Flash-Lite Flex, and limits Gemini 3.6 to optional
batched text adjudication.

## Evidence from the Assignment

The three supplied files are OGG/Opus, 48 kHz stereo:

| File | Duration | Label highlights |
|---|---:|---|
| call_001.ogg | 30.946 s | upset/high; no noise; clear; no overlap |
| call_002.ogg | 34.967 s | neutral/medium; TV/medium; clear; overlap |
| call_003.ogg | 171.928 s | satisfied/medium; sharp static/medium; clear; overlap |

These labels demonstrate why one score cannot drive every field: the two noisy
calls are still labelled `clear`, and overlap appears with very different noise
types. The files are useful smoke tests but statistically incapable of
selecting or calibrating a model.

## Decisions

### ADR-001: Do not host a generative model

**Decision**: No local LLM/audio foundation model and no GPU.

**Reason**: A 2 GB CPU host cannot provide competitive multimodal inference
with practical latency. Quantization does not fix semantic/audio capability,
memory residency, or engineering risk. Hosting a model also turns fixed hosting
into a much larger operational cost.

### ADR-002: Use Gemini 3.5 Flash-Lite Flex for audio observation

**Decision**: Make one compact structured full-audio observation per eligible
clip or validated short-clip microbatch.

**Reason**: It handles audio, speaker/emotion/sound tasks, structured output,
and minimal thinking at a large price margin under the ceiling. The model is
used where computation is weakest: semantic tone, customer role, noise naming,
and overlap in mono mixtures.

**Controls**: Pin the stable model ID; use `minimal` thinking; compact JSON
schema; record actual audio/input/output/thinking usage; no model-generated
public confidence; no automatic standard-tier fallback.

### ADR-003: Use Gemini 3.6 only as a text-only challenger

**Decision**: Batch compact 3.5 observations and local evidence for optional
3.6 adjudication. Do not send audio to 3.6 by default.

**Reason**: Stronger reasoning can improve exact rubric mapping while avoiding
3.6 audio-token cost. Batching amortizes its fixed overhead. It remains
removable if it does not improve locked-validation accuracy or cannot meet the
duration-specific cost gate.

### ADR-004: Keep deterministic evidence on the original signal

**Decision**: FFmpeg/ffprobe plus NumPy/SciPy calculate duration, channel
correlation, levels, robust noise floor/SNR proxy, clipping, DC offset, crest
factor, spectral centroid/rolloff/flatness, zero crossing, bandwidth,
transients, dropouts, and speech/pause summaries.

**Reason**: These are cheap, reproducible, interpretable, and often more
reliable than a language model for technical defects. Original full-band audio
is required because a 16 kHz derivative can erase high-frequency noise/static.

### ADR-005: Use Silero VAD for speech and silence

**Decision**: Use the small ONNX VAD on mono 16 kHz audio.

**Reason**: It is lightweight, CPU-friendly, and suitable for speech segments
and internal silence. The silence decision remains a validated duration-aware
rule, not a model guess.

### ADR-006: Treat every offline specialist as a challenger, not an assumption

**Decision**: Evaluate DNSMOS P.835 ONNX for SIG/BAK/OVRL quality evidence and
YAMNet TFLite/MediaPipe for 521-class acoustic-event evidence. Never install
full TensorFlow on the production host. Separately evaluate a lightweight
pyannote overlap detector, SpeechBrain/emotion2vec emotion evidence, and
Whisper tiny/base semantics.

**Reason**: Each may add useful independent evidence, but public task/domain
mismatch is substantial. They ship only after license, provenance, parity where
converted, artifact, ablation, latency, and 1.8 GB RSS gates.

### ADR-007: Experiment with local ASR without preselecting it

**Decision**: Compare whisper.cpp or faster-whisper tiny and base as P3
challengers, running one model at a time inside the 2 GB envelope.

**Reason**: Tiny/base are plausible sequential CPU models and could enable a
fully local semantic baseline. They also add latency, transcription and
speaker-role errors, and maintenance. ASR is retained only if its
speaker-attributed transcript produces an incremental predeclared accuracy
gain over the cheaper local path or corrects the Gemini hybrid.

### ADR-008: Compare local emotion evidence without fitting the three examples

**Decision**: Compare SpeechBrain wav2vec2 IEMOCAP and emotion2vec base
representations one at a time. DSP prosody may support intensity, OOD, and
confidence. Any five-label classifier or mapping requires representative
grouped data and out-of-fold fitting.

**Reason**: Public emotion datasets have domain, channel, acting, language, and
label-taxonomy mismatch. A tiny visible set would overfit and contaminate model
selection. IEMOCAP's label set does not match the assignment. emotion2vec base
is a representation model and its custom model license requires review. A
regularized shallow classifier becomes eligible only after proper
human-adjudicated data exists.

### ADR-009: Field-specific fusion, not majority voting

**Decision**: Each field receives a separate policy/calibrator. Strong
deterministic evidence may override technical fields; semantic emotion remains
model-led; overlap remains model-led on mono/dual-mono.

**Reason**: Models are not equally competent on all fields. Majority voting can
amplify correlated errors and violate independence.

### ADR-010: Confidence is learned correctness probability

**Decision**: Build out-of-fold features from field margins, evidence
agreement, audio quality, role certainty, OOD indicators, and route status.
Calibrate per-field probabilities and aggregate them against observed overall
correctness.

**Reason**: A raw model self-rating or constant `0.82` is not confidence.
Isotonic regression needs sufficient samples; regularized logistic/Platt
scaling is preferred when data is limited. Without enough labels, confidence
is conservative and explicitly provisional.

### ADR-011: Cache paid observations and cap research spend

**Decision**: Address a remote observation by the hashes of the audio, model,
prompt, structured-output schema, and inference configuration. An identical
request reuses the immutable encrypted/local cache. Every paid experiment
requires a configured total research-spend limit and explicit approval.

**Reason**: E09–E13 intentionally compare paid routes. Production
per-audio-minute cost and one-time research spend are different, but neither
should be uncontrolled or repeated unnecessarily.

### ADR-012: Use a project-local Python virtual environment

**Decision**: Python 3.12 `.venv` is mandatory for development, experiments,
tests, and the application. Local model binaries remain in a separate versioned
artifact directory.

**Reason**: Global packages make results irreproducible and blur application
dependencies with system tools. Separating `.venv`, FFmpeg, and model artifacts
also makes the release manifest auditable.

## Alternatives Considered

| Pipeline | Accuracy hypothesis | Variable cost | 2 GB fit | Role |
|---|---|---:|---:|---|
| P0 DSP/Silero | weak for semantics/mono overlap | $0 | yes | lower bound |
| P1 local specialists | stronger acoustics | $0 | validate sequentially | challenger |
| P2 local emotion | domain-sensitive | $0 | validate sequentially | challenger |
| P3 local ASR/semantics | semantic gain with role risk | $0 | tiny/base plausible | challenger |
| P4 Gemini 3.5 audio | strong multimodal baseline | low | yes | remote baseline |
| P5 3.5 + computation | strong expected balance | low | yes | primary hypothesis |
| P6 P5 + accepted specialists | possible corrections | low | validate sequentially | challenger |
| P7 P5/P6 + 3.6 text | stronger rubric mapping | batch dependent | yes | challenger |
| P8 3.6 full audio | potential upper bound | short-clip risk | yes | bounded experiment |
| Self-hosted generative model | uncertain | hosting/GPU | no | rejected |

## Cost Findings

- Gemini audio input is documented at 32 tokens/second (1,920/minute).
- 2026-08-01 Flex planning prices:
  - Gemini 3.5 Flash-Lite: $0.15/M input, $1.25/M output+thinking.
  - Gemini 3.6 Flash: $0.75/M input, $3.75/M output+thinking.
- Flex is best-effort and may return 503. It is suitable for batch evaluation
  with bounded retries, but not a reason to use a costlier automatic fallback.
- Thinking tokens are billed even when hidden. `max_output_tokens` must not be
  treated as proof of a hard total-generation cap. Release cost gates use
  observed p99 usage and actual usage metadata.
- One 3.6 full-audio minute can approach or exceed the ceiling when prompt and
  generation overhead are included. One 3.5 audio minute leaves enough room
  for local computation and selectively batched text adjudication.
- Multiple paid experiments are one-time research spend, not one production
  route. Cache identical observations and require explicit approval for the
  configurable research cap; USD 10 is the proposed initial cap, not
  authorization.

## Privacy Findings

Paid Gemini services state that submitted content is not used to improve Google
products, but this alone is not equivalent to zero retention. File API uploads
may persist for a documented window unless deleted. The production design
therefore requires AutoAce approval, paid-project configuration, review of
abuse/data logging and regional controls, immediate file deletion, and local
redacted logs. If the policy requires stronger contractual or zero-retention
controls, use the approved enterprise/Vertex route or stay local.

## Primary References

- Gemini 3.6 Flash model:
  https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash
- Gemini model selection and 3.5 Flash-Lite:
  https://ai.google.dev/gemini-api/docs/latest-model
- Gemini pricing:
  https://ai.google.dev/gemini-api/docs/pricing
- Flex inference:
  https://ai.google.dev/gemini-api/docs/flex-inference
- Audio input and tokenization:
  https://ai.google.dev/gemini-api/docs/audio
- Structured output:
  https://ai.google.dev/gemini-api/docs/structured-output
- Thinking-token billing:
  https://ai.google.dev/gemini-api/docs/thinking
- Gemini data retention / zero-data-retention:
  https://ai.google.dev/gemini-api/docs/zdr
- Gemini Files API:
  https://ai.google.dev/gemini-api/docs/files
- Silero VAD:
  https://github.com/snakers4/silero-vad
- YAMNet:
  https://github.com/tensorflow/models/blob/master/research/audioset/yamnet/README.md
- MediaPipe audio classifier:
  https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/audio/AudioClassifier
- DNSMOS P.835:
  https://github.com/microsoft/DNS-Challenge
- Whisper model card:
  https://github.com/openai/whisper/blob/main/model-card.md
- whisper.cpp memory/runtime:
  https://github.com/ggml-org/whisper.cpp
- SpeechBrain IEMOCAP emotion model:
  https://huggingface.co/speechbrain/emotion-recognition-wav2vec2-IEMOCAP
- emotion2vec base:
  https://huggingface.co/emotion2vec/emotion2vec_base
- pyannote overlap detection:
  https://huggingface.co/pyannote/overlapped-speech-detection

## Open Pre-Implementation Verifications

These are gates, not unresolved architecture choices:

1. Recheck model IDs, Flex prices, thinking behavior, quotas, supported upload
   path, and data terms on the implementation/release dates.
2. Obtain AutoAce approval for the exact endpoint/project/region.
3. Verify licenses and checksums for Silero, DNSMOS, and YAMNet artifacts.
4. Measure p50/p95/p99 total generated tokens for compact schemas.
5. Confirm short-clip microbatching does not reduce file attribution accuracy.
6. Profile peak RSS and real-time factor on the actual 2 GB target.
7. Freeze the operational definition of “unusually long silence.”
8. Confirm representative labelled data, paid-experiment approval, research
   cap, and every gated/custom local model term before the affected run.
