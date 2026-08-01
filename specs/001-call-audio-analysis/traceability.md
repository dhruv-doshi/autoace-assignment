# Requirements Traceability

This matrix prevents implementation convenience from quietly dropping an
accuracy, cost, privacy, or product requirement.

| Requirement | Design evidence | Verification |
|---|---|---|
| FR-001 authentication | Streamlit single-app boundary | unauthorized UI/integration tests |
| FR-002 batch input | Batch entity and manifest schema | manifest contract and journey tests |
| FR-003 safe validation | security module and media probing | archive/manifest property and adversarial tests |
| FR-004 failure isolation/progress | Batch and AudioItem states | mixed valid/corrupt batch integration test |
| FR-005 exact output | result JSON schema | JSON Schema, Pydantic, CSV round-trip tests |
| FR-006 original + 16 kHz paths | decode module and evidence provenance | golden feature/provenance tests |
| FR-007 deterministic evidence | DSP decision | unit/golden audio tests |
| FR-008 lightweight models earn inclusion | candidate/ablation protocol | field gain + memory/license gates |
| FR-009 emotion independence | tone field ownership | loud-positive/quiet-negative stress set |
| FR-010 noise vs quality independence | separate fusion paths | orthogonal synthetic + real fixtures |
| FR-011 valid overlap evidence | channel-layout policy | mono, dual-mono, true-stereo tests |
| FR-012 long silence | VAD duration-aware rule | boundary and injected-silence tests |
| FR-013 approved remote audio | privacy and cost policy | approval/config/deletion tests |
| FR-014 optional strong adjudicator | candidate C gate | B-vs-C locked A/B and cost routing |
| FR-015 spend protection | cost controller | boundary, short-clip, and price-change tests |
| FR-016 no expensive fallback | route policy | Flex failure and tier-refusal tests |
| FR-017 confidential handling | temp/deletion/redacted logging policy | cleanup and log-inspection tests |
| FR-018 2 GB/simple host | single project, sequential runtime | peak RSS <1.8 GB deployment profile |
| FR-019 exports | dashboard/result boundary | filename-preserving CSV/JSON tests |
| FR-020 confidence | OOF calibration plan | Brier/ECE/reliability report or provisional flag |
| FR-021 three-call limitation | evaluation protocol | dataset registry marks smoke-only |
| FR-022 candidate comparison | P0–P8 and E00–E13 registry | experiment report |
| FR-023 grouped metrics/holdout | ExperimentRun | split leakage tests and final report |
| FR-024 release pinning | ReleaseManifest | manifest completeness/reproduction test |
| FR-025 `.venv` isolation | environment phase and Luna contract | clean-environment and executable-path tests |
| FR-026 paid observation cache | ObservationCacheEntry | cache identity/integrity/no-repeat tests |
| FR-027 research spend | cost controller | missing approval/cap and overspend tests |
| FR-028 local model admission | P1–P3 protocols | license/parity/ablation/RSS reports |
| FR-029 frozen selection | evaluation config | hash and premature-remote-run tests |
| FR-030 model before UI | delivery dependencies | task/order and frozen-winner integration tests |

## Success-Criterion Gates

| Criterion | Blocking threshold |
|---|---|
| SC-001 | 100% valid successful results; per-file failure isolation |
| SC-002 | highest eligible locked-validation score with per-field reporting |
| SC-003 | every retained optional component has measured contribution |
| SC-004 | release <= $0.0024/min; every route <= $0.003/min |
| SC-005 | peak RSS <1.8 GB on target |
| SC-006 | >=95% eligible file completion under stated assumptions |
| SC-007 | calibrated confidence or explicit provisional designation |
| SC-008 | one-process deployment and operator quickstart pass |
| SC-009 | approved paid route and verified remote-file deletion |
| SC-010 | every eligible E00–E13 run reproducible or explicitly blocked |
| SC-011 | no duplicate paid request and research cap cannot be exceeded |
| SC-012 | clean `.venv` reproduces tests and a smoke experiment |
