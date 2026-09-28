# Acceptance Report

**Release verdict: `ENGINEERING_READY_ON_SYNTHETIC_DATA`.** This verdict covers deterministic engineering behavior only. The real-data gate is pending.

## Scope and evaluator acceptance

- Registry and generated traceability reconcile at 164 / 149 / 12 / 3.
- `CONTRACTS` contains exactly 149 executable controls across 11 deterministic primitives.
- Every executable contract declares subject/population, datasets, fields, formula, typed parameters, provenance, exclusions, evidence, disposition, and impact method.
- The parameterized suite exercises triggered, clean negative/boundary, missing-input, and exclusion behavior for all 149. Missing data never passes; evaluator exceptions never pass.
- Tests prove supplied rule booleans and synthetic label/confidence fields are discarded.

## Product acceptance

- Preview and commit are separate; preview creates no claims; commit is transactional and retry-safe.
- Rule detail, threshold guidance, non-mutating simulation, prospective Admin save, provider detail, evaluation detail, dataset readiness/profile, claim analysis, network graph, and graph export APIs are present.
- Claims show observed/expected/operator/variance, evidence strength and records, exclusions, associated value, estimated exposure, formula/version provenance, and next verification without raw JSON.
- Provider metrics disclose peer fallback and support; sparse groups abstain. Trends and contributing claims are linked.
- React Flow provides maintained pan/zoom/fit controls, stable deterministic layout, node/edge selection, type filtering, labels, legend, and claim-linked accessible edge table. Explicit network boundaries and distinct claim amounts reconcile in tests.
- Reports include assessment, triggered rules, observed/expected summaries, coverage, dispositions, exposure, provider/network context, and configuration versions; reconciliation is tested.
- Network evidence exports use source claim IDs and carry network, timestamp, amount, and interpretation-boundary provenance. Report CSV, Excel, and PDF outputs carry immutable run-configuration snapshot hashes; Excel labels current configuration history separately.

## Executed gates

| Check | Evidence | Result |
|---|---|---|
| Full suite | `powershell -File scripts/test.ps1` | Pass: backend, compile, frontend unit, typecheck, lint, build. |
| Browser E2E | `npm --prefix apps/web run test:e2e -- --reporter=list` | 2 passed; authenticated rule/import/evaluation/network workflow and zero post-login console errors. |
| Accessibility/visual | Playwright keyboard/landmark/overflow assertions and three stored screenshots | Pass. |
| Dataset profile | `python scripts/profile_dataset.py data/demo/claims_demo_synthetic.csv` | 20,893 rows; 2023-01-01–2028-04-02; synthetic-only; mapping unconfirmed. |
| Performance | `$env:PYTHONPATH='apps\api'; python scripts/benchmark.py` | 10k validation 0.3130 s; 149k evaluations 19.5225 s; graph/export thresholds pass; peak 11.21 MB. |
| Security | `python scripts/security_check.py`; `npm audit` during install | Pass; 0 dependency vulnerabilities reported. |
| Migration/backup | migration tests; active integrity; verified backup schema check | Pass, existing aggregate counts preserved. |
| Export reconciliation | `tests/backend/test_reports.py` | Pass. |

## Corrected full-population evaluation

Synthetic run #4 completed on 2026-09-28 with evaluator `canonical-evidence-v2-2026-09-28`: 20,893 claims, 149 executable controls, 147 triggered rule-claim checks, 0 evaluator errors. Readmission evidence now uses an earlier discharge and a later admission for the same member and primary diagnosis; future claims are excluded by the run analysis date. The final backend suite contains 330 passing tests and the two Playwright workflows pass without updating baselines. The final independent network/report recheck returned `PASS / RELEASE-READY` with no open P0/P1 finding in that scope.

## Dataset-calibrated acceptance still pending

No real tokenized dataset is available. Mapping confirmation, governed payer references, real linkage/completeness, structural-break review, leakage-controlled calibration/holdout periods, simulation reconciliation, and stability analysis have not been claimed. Synthetic labels are excluded from production logic and are not used to report fraud accuracy.
