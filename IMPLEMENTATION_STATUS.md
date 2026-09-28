# Implementation Status

Last updated: 2026-09-28 (Asia/Dubai)

## Release status

**ENGINEERING_READY_ON_SYNTHETIC_DATA.** The deterministic engineering gates pass. No real tokenized dataset is present, so source mappings, payer policy references, calibration, linkage quality, structural breaks, and holdout acceptance remain `DATASET_PENDING`. This is not `DATASET_CALIBRATED_READY`.

## Delivered

- Exact catalogue scope remains 164 total / 149 executable / 12 deferred document-text / 3 excluded model.
- All 149 executable controls have canonical field-driven contracts, typed parameters/provenance, exclusions, disposition, evidence, missing-data behavior, and positive/negative/boundary/missing/exclusion tests.
- Caller `signals.{rule_id}`, synthetic scores, and synthetic outcome labels are removed at intake and parse boundaries.
- Import validation is a non-mutating preview followed by explicit transactional, idempotent commit into indexed canonical facts.
- Recommendation, simulation, prospective Admin configuration, immutable run snapshots, readable claim evidence, provider peer/trend context, and React Flow network evidence are implemented.
- CSV/Excel/PDF exports include decisions, coverage, rules, observed/expected summaries, exposure, network/provider keys, and configuration provenance. Network edges have a CSV export endpoint.
- Versioned additive migrations preserve the existing database; a verified pre-remediation backup is retained locally.

## Dataset gate

Only `data/demo/claims_demo_synthetic.csv` was found. Aggregate-safe profiling reports 20,893 rows, 26 columns, date range 2023-01-01 through 2028-04-02, four outcome-like columns, `SYNTHETIC_FIXTURE_ONLY`, and `UNCONFIRMED` mapping. The future-dated range reinforces that this is not real calibration data. No row values were emitted.

## Latest verified results

| Gate | Result |
|---|---|
| Backend | 330 tests pass, including the 149-rule matrix, migrations, synthetic mapping, import atomicity, analytics, export reconciliation/provenance, multi-run manifests, time-correct readmission linkage, simulation parity, and ordered configuration versions. |
| Frontend | Unit test, strict TypeScript, ESLint, and production build pass. |
| Browser | 2 authenticated Playwright workflows pass; standard demo run has 149 rules and zero evaluator errors. |
| Accessibility | Keyboard focus, labelled graph, table alternative, landmark, status-text, and mobile overflow checks pass. |
| Visual | Desktop/mobile login and authenticated network graph snapshots pass. |
| Security | Static production-source gate passes; dependency audit reports zero vulnerabilities; CSRF/RBAC, Argon2, formula safety, and security headers are active. |
| Performance | 10,000-row validation 0.3130 s; 149,000 canonical evaluations 19.5225 s; 500-node/2,000-edge serialization 0.0093 s; CSV/XLSX/PDF generation each below 0.21 s; 11.21 MB measured Python peak. |
| Migration/backup | Additive migration and integrity tests pass; verified pre-remediation backup passes schema/integrity check. |

## Remaining real-data work

Place a tokenized, contract-approved extract outside tracked demo fixtures, run `python scripts/profile_dataset.py <path>`, confirm source-to-canonical mappings and governed references with owners, then run time-correct recommendation stability, linkage, simulation reconciliation, and holdout acceptance. Do not use the synthetic outcome columns as performance evidence.

The latest completed synthetic population run is #4. It processed 20,893 claims against 149 executable controls with zero evaluator errors under `canonical-evidence-v2-2026-09-28`. This is engineering evidence only and does not change the real-data readiness boundary.
