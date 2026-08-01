# Model, Cost, and Privacy Release Checklist

Use this checklist for every promoted candidate. An unchecked hard gate blocks
release.

## Data and Labels

- [ ] Label guide resolves customer role and every boundary in the assignment
- [ ] Calls and speakers are grouped before splitting
- [ ] Untouched final holdout is sealed
- [ ] At least 20% of the representative set is independently double-labelled
- [ ] Inter-rater agreement and adjudication are reported
- [ ] Supplied three calls are smoke fixtures only
- [ ] Duration, channel, class, language, and defect distributions are reported

## Candidate Selection

- [ ] P0 computation-only / E00 is measured
- [ ] P1 local acoustic specialists / E01–E04 are measured or blocked with evidence
- [ ] P2 local emotion / E05–E06 is measured or blocked with evidence
- [ ] P3 local ASR / E07–E08 is measured or blocked with evidence
- [ ] P4/P5 Gemini 3.5 / E09–E10 is measured or blocked with evidence
- [ ] P6/P7 hybrids / E11–E12 are measured or blocked with evidence
- [ ] P8 full-audio 3.6 / E13 is treated as an upper-bound challenger
- [ ] Each DSP feature family and lightweight model has an ablation
- [ ] No retained component has a non-positive validated contribution
- [ ] Per-field confusion matrices and confidence intervals are reported
- [ ] Selected candidate has no material protected-field regression

## Field Integrity

- [ ] Emotion is based on customer evidence, not agent/background speech
- [ ] Loudness alone cannot select tone
- [ ] Noise and quality are independently decided
- [ ] Original full-band audio drives high-frequency defect/noise evidence
- [ ] Dual-mono is detected and cannot trigger channel-overlap logic
- [ ] Silence threshold is frozen and boundary-tested
- [ ] Noise type normalization does not collapse distinct scored categories

## Confidence

- [ ] Calibration uses held-out or out-of-fold correctness
- [ ] Brier score, ECE, and reliability bins are reported
- [ ] Model self-confidence is not returned directly
- [ ] OOD, missing-role, disagreement, and quality signals lower confidence
- [ ] Insufficient sample size causes a provisional, not calibrated, claim

## Cost

- [ ] Prices and audio token rate are revalidated and versioned
- [ ] Fixed prompt and generation/thinking overhead are duration-aware
- [ ] p50/p95/p99 usage is measured by duration bucket
- [ ] Release workload spend is <= $0.0024/audio-minute
- [ ] Every legal route is hard-blocked above $0.003/audio-minute
- [ ] A lone short clip and mixed-duration batch are tested
- [ ] Optional 3.6 is skipped when allowance is insufficient
- [ ] Flex failure never silently selects standard pricing
- [ ] Actual usage reconciles with the projected ledger
- [ ] Identical paid requests are served from the integrity-checked cache
- [ ] A total research-spend cap was explicitly approved and enforced
- [ ] Experiment spend and production per-minute cost are reported separately

## Privacy and Supply Chain

- [ ] AutoAce approved the exact endpoint, project, region, and retention terms
- [ ] Paid service configuration and data-sharing controls are documented
- [ ] Remote uploads are deleted in success and failure paths
- [ ] Logs contain no audio, transcript, prompt content, or call rationale
- [ ] Temporary local audio is deleted after its retention window
- [ ] Model licenses, revisions, sources, and SHA-256 hashes are recorded
- [ ] Converted local artifacts have provenance and parity evidence
- [ ] Gated/custom model access terms are approved

## Deployment and Reliability

- [ ] All Python commands run from the project-local `.venv`
- [ ] A clean `.venv` reproduces the locked environment
- [ ] Peak RSS is below 1.8 GB on a 2 GB CPU host
- [ ] No GPU, database, broker, or separate frontend is required
- [ ] Native models are loaded/released sequentially
- [ ] Per-file failures do not abort a batch
- [ ] Contract, archive safety, cleanup, retry, and export tests pass
- [ ] Release manifest reproduces the selected configuration
