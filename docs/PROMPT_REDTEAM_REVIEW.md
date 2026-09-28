# Red-team review — Codex remediation prompt

**Reviewed artifact:** `CLAUDE_FOLLOWUP_PROMPT.md` (legacy filename; content retargeted to Codex)  
**Review date:** 27 September 2026  
**Outcome:** Revised before execution

## Executive finding

The original follow-up prompt correctly identified the application's central defects, but it could still produce misleading calibration, stall when the real dataset was absent, or allow Codex to overclaim readiness. The revised prompt now distinguishes engineering readiness from dataset-calibrated readiness, prevents same-population calibration claims, constrains editable parameters by provenance, defines evidence aggregation, strengthens graph false-positive controls, and externalizes long-run state through milestone/status files.

## Findings and corrections

| Severity | Weakness | Exploit/failure mode | Correction made |
|---|---|---|---|
| Critical | Real dataset was implicitly required for final readiness | Codex could stall indefinitely or invent real-data findings | Added `ENGINEERING_READY_ON_SYNTHETIC_DATA` and `DATASET_CALIBRATED_READY` states with separate gates |
| Critical | Calibration and impact evaluation could use the same observations | Thresholds could look effective because they were optimized and judged in-sample | Added time-separated calibration/holdout, rolling-origin backtesting, and mandatory in-sample labelling |
| Critical | Existing fraud could contaminate the baseline | High abusive utilization could become the “normal” threshold | Added sensitivity analysis, extreme-entity handling disclosure, leave-one-out peer safeguards, and contamination failure handling |
| Critical | No labelled-outcome boundary | Codex could claim accuracy or false-positive rates from system flags or synthetic labels | Prohibited real-world performance claims without reviewed outcomes; defined what may be measured instead |
| High | Every parameter appeared freely editable | Admin could override technical invariants or policy references as arbitrary numbers | Added parameter edit authority for invariants, governed references, empirical, operational, and user-defined values |
| High | Overall suspicion aggregation was under-specified | Multiple correlated rules could inflate a claim into “high suspicion” | Added independent evidence domains, within-domain caps, reproducible formula/version, contradictory-evidence and exclusion handling |
| High | Recommendation “confidence” could be mistaken for fraud probability | Users could interpret a stable threshold as 90%-style fraud confidence | Defined it as data-support/stability and required the UI label `Data support` |
| High | Provider graph could visually imply collusion from legitimate concentration | Ownership, narrow networks, geography, or centres of excellence could look suspicious | Added opportunity normalization, known-relationship exclusions, minimum support/materiality, provenance, and prospective suppressions |
| High | Dataset may contain unexpected identifiers or free text | Sensitive data could appear in logs, screenshots, documentation, or external services | Added a dataset safety gate, stop behavior, untrusted-content handling, masking, and external-upload prohibition |
| High | Prompt could count placeholder evaluators as complete | An evaluator could always return not applicable while satisfying a registry mapping | Retained and strengthened the ban on signal passthrough, constant outputs, placeholders, and untested evaluators |
| Medium | Missing dataset fields could be treated as product failure | Engineering work could stop even when architecture and fixtures were possible | Added a two-track workflow and explicit `DATASET_PENDING` handling |
| Medium | Graph size had no operational boundary | Browser could freeze on dense provider networks | Added server-side filtering/aggregation and a benchmark target of 500 visible nodes/2,000 edges |
| Medium | User usefulness was described but not tested | Pages might contain more data without helping analysts reach evidence | Added analyst task-success checks for threshold explanation, exclusions, missing data, graph-to-claim paths, and role behavior |
| Medium | Performance was not bounded | Product could be functionally correct but unusable for thousands of claims | Added claim, evaluation, list, graph, report, and memory benchmarks |
| Medium | The prompt was very long as a single chat message | Codex could dilute or lose instructions during long execution | Kept the full spec in-repo and added a concise kickoff prompt plus durable plan/status files |
| Medium | No explicit non-goals | Codex could expand into models, NLP, case management, cloud, or unrelated redesign | Added a non-goals section |
| Medium | Milestone process lacked durable execution files | Long-run work could drift or repeat decisions | Required `REMEDIATION_PLAN.md`, `REMEDIATION_STATUS.md`, continuous verification, and decision logging |

## Residual risks

The prompt cannot solve missing business inputs by itself. These remain intentionally visible:

- Many hard/expert rules require effective UAE payer, benefit, contract, tariff, coding, licensing, authorization, and clinical-policy references. Utilization data cannot safely substitute for them.
- A claims dataset without reviewed outcomes can validate rule computation and alert stability, but not real-world fraud accuracy.
- Some of the 149 structured evaluators may be runtime-disabled on the supplied dataset because required domains are absent. Their code paths must still be tested with deterministic fixtures.
- Graph relationships are only as reliable as entity resolution, timestamps, provider identifiers, and known legitimate relationship data.
- A polished POC is not a production clinical, legal, compliance, or autonomous adjudication system.

## Recommended execution method

Send Codex the concise `CODEX_REMEDIATION_KICKOFF.md` prompt from the workspace. It directs Codex to treat the full remediation specification as durable source material, create a milestone plan/status log, implement, verify, repair failures, and report the correct readiness tier.

