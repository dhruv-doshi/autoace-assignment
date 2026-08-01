# AutoAce Annotation Guide (Implementation Draft)

Annotators label the customer’s primary expressed tone, not the agent or a
background television/voice. Each output field is judged independently.

## Required decisions

- `emotional_tone`: neutral, satisfied, frustrated, upset, or distressed.
- `emotional_intensity`: low, medium, or high for the customer tone.
- `background_noise_present`: meaningful non-speech sound audible behind the
  conversation.
- `background_noise_type`: concise dominant sound; empty only when absent.
- `background_noise_severity`: effect on understanding, not mere presence.
- `audio_quality`: technical quality independent of emotion/noise labels.
- `speaker_overlap_present`: simultaneous speech affecting analysis.
- `long_silence_present`: unusually long call dead air, with duration noted.

## Adjudication rules

Annotators record uncertain speaker role and disagreement reason. Loudness alone
cannot select negative emotion. Audible noise does not imply impaired quality.
Mono/dual-mono channel coincidence does not prove overlap. Disagreements are
adjudicated and the original labels are retained for agreement reporting.

The guide must be expanded with real examples and boundary cases before final
calibration or holdout evaluation.
