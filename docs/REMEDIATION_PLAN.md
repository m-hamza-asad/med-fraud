# Remediation Plan

Authoritative specification: `CLAUDE_FOLLOWUP_PROMPT.md`. The product remains local-only and preserves the exact catalogue split: 164 total, 149 structured executable, 12 deferred document/text, and 3 excluded model controls.

## Milestone 1 — Audit, safety gate, and migration baseline

- Preserve the current working tree and back up the active SQLite database.
- Record the current defects, dataset state, source-to-canonical mapping boundary, and schema migration approach.
- Add versioned, idempotent migrations that preserve existing users, claims, imports, evaluations, and audit history.
- Validation: `pytest tests/backend/test_migrations.py tests/backend/test_registry.py`; SQLite integrity/schema checks.
- Exit: no real dataset is read without the safety gate; migration succeeds on both a clean database and a copy of the current database.

## Milestone 2 — Canonical data, preview/commit, and rule contracts

- Normalize claim lines, diagnoses, encounters, coverage, authorizations, remittances, prescriptions, providers, network membership, and lineage while retaining source keys and payload lineage.
- Split import profiling/validation preview from explicit transactional commit and persist reusable mapping profiles.
- Give every catalogue control a complete detail contract; every executable control gets explicit required fields, typed parameters, provenance, formula/evaluator, missing-data behavior, disposition, and evidence contract.
- Validation: registry/contract tests; clean/invalid/duplicate/partial import tests; preview-no-mutation and atomic-commit tests.
- Exit: 164/149/12/3 invariants hold; no executable rule depends on `signals.{rule_id}`; 149 contracts are concrete and schema-valid.

## Milestone 3 — Typed configuration and threshold guidance

- Add typed parameter definitions, effective-dated configuration versions, immutable evaluation snapshots, recommendations, and non-mutating simulations.
- Implement robust percentile, median/MAD, IQR, minimum-support, empirical-Bayes/Wilson rate, time-window, graph-distribution, and capacity-impact methods where provenance permits.
- Keep policy/reference parameters unavailable when authoritative inputs are absent; never infer them from utilization.
- Validation: permission, range, effective-date, snapshot immutability, reproducibility, sparse-data, anti-leakage, and simulation reconciliation tests.
- Exit: Admin can simulate and save prospective editable parameters; Analyst writes are rejected; recommendations show method, period, population, support, warnings, and impact.

## Milestone 4 — Real evaluators and analyst claim workspace

- Implement reusable deterministic primitives and concrete rule contracts for all 149 executable controls over normalized canonical facts/history/references.
- Emit typed observed-versus-expected evidence, exclusions checked/unavailable, amount semantics, next verification, and version provenance.
- Implement reproducible evidence-domain aggregation without turning objective payment failures into intent findings.
- Replace raw-JSON evidence with readable claim analysis, source tables, coverage, and assessment guidance.
- Validation: positive, negative, boundary, missing-input, exclusion, and effective-date cases for all 149; claim/API/UI integration tests.
- Exit: zero passthrough/constant evaluators; standard synthetic runs have no evaluator errors and never treat missing data as pass.

## Milestone 5 — Provider intelligence and network graph

- Build provider feature snapshots, peer groups/backoff, trends, intervals, contributing-claim links, and data-support states.
- Derive typed provider relationships and graph metrics with explicit network boundaries, materiality/minimum-support controls, provenance, exclusions, and deduplicated associated value.
- Implement interactive filtering/focus/evidence and a keyboard-accessible node/edge table.
- Validation: peer/shrinkage/change tests; known-small-graph metric tests; graph-to-claim evidence and distinct-exposure tests; provider/network UI tests.
- Exit: provider metrics reconcile to claims; sparse peers abstain; graph evidence is explainable and accessible.

## Milestone 6 — Reports, complete UI, and release verification

- Upgrade CSV/Excel/PDF to include assessment, rule evidence, thresholds/references, provider/network context, coverage, and configuration versions.
- Complete rule detail/threshold lab, dataset readiness, run detail, claim, provider, and network workflows.
- Run backend, frontend, E2E, accessibility, visual, migration, export-reconciliation, security, backup/restore, and performance checks; repair failures.
- Validation: `scripts/test.ps1`, browser E2E suite, accessibility scan, visual matrix, export reconciliation, `scripts/benchmark.py`, backup/restore sequence.
- Exit: all required synthetic engineering checks pass and documentation matches measured evidence.

## Milestone 7 — Readiness closure

- Update implementation status, decisions, traceability, architecture, dictionary, methodology, network, user, testing, demo, security, and acceptance documents.
- If the real dataset remains absent, publish `ENGINEERING_READY_ON_SYNTHETIC_DATA` only after all engineering criteria pass. Real-data mapping, calibration, and holdout acceptance remain pending.
- If any engineering criterion is failing, publish `NOT_READY` and keep the failure visible.

