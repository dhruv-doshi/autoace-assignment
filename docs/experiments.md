# AutoAce pipeline experiments

**Recorded:** 2026-08-01  
**Production candidate:** P6  
**Research archive branch:** `archive/all-pipelines`

This document is the production-branch record of the P0–P8 research. Raw JSON
evidence remains under `artifacts/experiments/`.

## Decision

P6 was selected as the best cost/accuracy production candidate:

- latest live three-file sweep: **95.83% average field accuracy**, **2/3 exact
  files**, **$0.000389 per audio minute**, 7.13 seconds mean wall time, and
  891.5 MB measured peak RSS;
- deterministic fusion replay using recorded provider responses: **100% field
  accuracy** and **3/3 exact files**;
- comfortably below the external-inference gate of $0.003 per audio minute;
- substantially cheaper than P7 while retaining the useful local corrections.

The replay is not a fresh provider run and must not be presented as independent
holdout evidence. The corpus has only three labeled calls and was used during
calibration. P6 is therefore a deployment candidate, not a statistically
validated accuracy claim. A larger untouched holdout remains required.

## Candidate definitions and disposition

| Pipeline | Components | Outcome |
|---|---|---|
| P0 | FFmpeg, DSP, energy/Silero VAD, rules | Zero-cost lower bound; weak semantic fields |
| P1 | P0 plus acoustic and overlap challengers | Improved overlap evidence, no semantics |
| P2 | P1 plus prosody/emotion evidence | Stronger intensity; still weak tone |
| P3 | P2 plus local Faster-Whisper semantics | Best zero-external-cost result on the tuned three-file corpus |
| P4 | Gemini 3.5 Flash-Lite audio | Low cost, but variable and no exact file in repeated live runs |
| P5 | P4 plus deterministic local fusion | Better technical/noise fields; semantic errors remained |
| P6 | P5 plus accepted local overlap, prosody and ASR specialists | Selected cost/accuracy candidate |
| P7 | P6 plus Gemini 3.6 text adjudication | Similar accuracy at materially higher cost; rejected |
| P8 | Gemini 3.6 full-audio upper bound | Repeated truncated/non-schema JSON; failed |

The executable P0–P5/P7/P8 code and historical runners are intentionally absent
from `main` and `prod`; they are preserved at commit
`c6120307cf546dcfe04522ad93278b68f173be5d` on
`archive/all-pipelines`.

## Experiment sequence

### Initial deterministic and remote sweeps

The first complete comparison showed no exact matches. In
`pipeline-sweep-20260801T061813Z.json`, average field accuracy ranged from
37.5% for P0/P1 to 50% for P7. P4–P6 cost approximately
$0.00037–$0.00040/audio-minute. P7 cost $0.00357/audio-minute and exceeded the
production gate. P8 completed zero files.

The adjacent `061742Z` run records an earlier remote attempt in which P7
completed only two files and P8 remained failed. Together these runs exposed
provider output variability and motivated deterministic field ownership.

### P4 prompt tuning

`p4-prompt-tune-20260801T062555Z.json` used calls 001 and 002 for development
and call 003 as a one-file holdout:

| Prompt | Development field accuracy |
|---|---:|
| Baseline | 56.25% |
| Rubric v1 | 50.00% |

The baseline was retained. It scored 37.5% on the one holdout call. Recorded
tuning spend was $0.0037705. The experiment explicitly warns that two
development files are insufficient to freeze a production prompt.

### Local calibration

`pipeline-sweep-20260801T063125Z.json` records the first calibrated local
rules. `pipeline-sweep-20260801T063709Z.json` records the final local sweep:

| Pipeline | Average field accuracy | Exact files | External cost/min |
|---|---:|---:|---:|
| P0 | 70.83% | 0/3 | $0 |
| P1 | 79.17% | 0/3 | $0 |
| P2 | 91.67% | 1/3 | $0 |
| P3 | 100.00% | 3/3 | $0 |

The gains came from calibrated noise signatures, a conservative silence
threshold, prosody intensity, repeated unanswered “hello” semantics, and a
spectral-polyphony overlap proxy. Because these thresholds were inspected
against the supplied labels, the 100% P3 result is a regression result, not an
unseen-data estimate.

### Repeated live remote sweeps

Remote outputs varied even at temperature zero. Recorded candidate ranges:

| Pipeline | Live field accuracy range | Exact-file range | Cost/min range |
|---|---:|---:|---:|
| P4 | 33.33–62.50% | 0/3 | $0.000396–$0.000674 |
| P5 | 37.50–87.50% | 0–1/3 | $0.000383–$0.000672 |
| P6 | 45.83–95.83% | 0–2/3 | $0.000370–$0.000690 |
| P7 | 50.00–95.83% | 0–2/3 | $0.003572–$0.008642 |

Runs `063329Z`, `063355Z`, `063409Z`, `063530Z`, and `063939Z` capture this
variation and the successive fusion improvements. The final `063939Z` live
sweep is the primary P6 deployment measurement.

### Offline fusion replay

`fusion-replay-20260801T064101Z.json` replayed recorded P4/P7 observations
through the final deterministic fusion code without another provider call:

| Pipeline | Average field accuracy | Exact files |
|---|---:|---:|
| P5 | 91.67% | 1/3 |
| P6 | 100.00% | 3/3 |
| P7 | 100.00% | 3/3 |

Replay cost was $0 because it reused prior responses. It validates fusion
behavior, not future remote-model stability.

## Artifact index

| Artifact | Purpose |
|---|---|
| `e00-smoke-call_001.json` | Original P0 smoke evidence |
| `pipeline-sweep-20260801T061742Z.json` | Early P0–P8 sweep; partial P7 and failed P8 |
| `pipeline-sweep-20260801T061813Z.json` | First complete P0–P7 comparison |
| `p4-prompt-tune-20260801T062555Z.json` | Leakage-controlled P4 prompt experiment |
| `pipeline-sweep-20260801T063125Z.json` | First calibrated P0–P3 sweep |
| `pipeline-sweep-20260801T063329Z.json` | Live P4–P7 sweep after initial fusion tuning |
| `pipeline-sweep-20260801T063355Z.json` | Isolated live P4 run |
| `pipeline-sweep-20260801T063409Z.json` | Repeated live P4–P7 variability run |
| `pipeline-sweep-20260801T063530Z.json` | Repeated live P5–P7 run |
| `pipeline-sweep-20260801T063709Z.json` | Final local P0–P3 regression sweep |
| `pipeline-sweep-20260801T063939Z.json` | Final live P5–P7 sweep and primary P6 measurement |
| `fusion-replay-20260801T064101Z.json` | Final deterministic fusion replay |

## Required next evaluation

Before describing P6 accuracy as production-validated:

1. obtain at least 50–100 newly labeled calls spanning duration, language,
   channel layout, noise, and customer emotion;
2. freeze code, thresholds, model revision, and prompt before opening the
   holdout;
3. report per-field precision/recall, exact-match confidence intervals, cost by
   duration bucket, peak RSS, and provider failure rate;
4. review OpenRouter retention, regional processing, and contractual controls
   for confidential call audio.
