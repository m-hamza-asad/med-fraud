# Prompt to send to Codex

Continue the existing application in the current `Med Fraud` workspace and complete the remediation end to end.

Treat `CLAUDE_FOLLOWUP_PROMPT.md` as the authoritative remediation specification despite its legacy filename. Read it fully before editing, together with the local product plan, fraud catalogue, model-classification guide, implementation status, traceability files, current code/tests, and Shahai Design-System sources it references.

Your outcome is a working, verified analyst decision-support product. Correct the current Boolean signal passthrough, implement real dataset-driven rule evaluation, detailed rule configuration and threshold guidance, readable claim evidence, provider peer analytics, and an interactive provider-network graph. Preserve the 164 total / 149 executable / 12 deferred-text / 3 excluded-model scope exactly.

Before material implementation:

1. Inspect the working tree and preserve user changes.
2. Audit the current implementation against the remediation specification.
3. Check whether the user dataset is present and apply the dataset safety gate before profiling it.
4. Create `docs/REMEDIATION_PLAN.md` with small milestones, validation commands, and exit criteria.
5. Create `docs/REMEDIATION_STATUS.md` and keep it current throughout the run.

Then work milestone by milestone: implement, run targeted validation, fix failures, run the affected suite, update status/decisions, and continue. Do not stop at a plan, mockup, threshold table, schema, or graph placeholder. Do not use caller-supplied `signals.{rule_id}` booleans, synthetic scores, or constant/not-applicable evaluators as production rule logic.

If the real dataset is absent, complete and verify everything possible using deterministic synthetic fixtures and report `ENGINEERING_READY_ON_SYNTHETIC_DATA`; do not fabricate mappings or empirical findings. Report `DATASET_CALIBRATED_READY` only after the real dataset is safely profiled, mappings are confirmed, recommendations use time-correct leakage-controlled calibration, and real-data acceptance checks pass. Report `NOT_READY` while engineering acceptance criteria remain failing.

Run all required backend, frontend, end-to-end, accessibility, visual, migration, export-reconciliation, performance, and security checks. Never claim a check passed unless you ran it. Repair failures before moving on. Keep evaluation results and configuration snapshots reproducible and preserve user data through migrations.

Begin now with the audit, dataset-presence/safety check, and concise remediation plan, then proceed through implementation without waiting for routine approval.

