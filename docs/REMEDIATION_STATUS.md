# Remediation Status

Last updated: 2026-09-28 (Asia/Dubai)

## Current state

- **Readiness:** `ENGINEERING_READY_ON_SYNTHETIC_DATA`
- **Engineering milestones:** 1–7 complete on deterministic fixtures
- **Dataset state:** `SYNTHETIC_FIXTURE_ONLY`; 20,893 fixture rows committed with a confirmed synthetic mapping
- **Catalogue:** 164 total / 149 executable / 12 deferred text-document / 3 excluded model

## Preserved user changes

The audit recorded and preserved the user-provided `CLAUDE_FOLLOWUP_PROMPT.md`, `CODEX_REMEDIATION_KICKOFF.md`, `data/demo/claims_demo_synthetic.csv`, and `docs/PROMPT_REDTEAM_REVIEW.md`. No user-supplied database rows were deleted. A verified backup exists at `data/backups/pre-remediation-20260927.sqlite3`.

## Completed remediation

1. Added versioned additive migrations and normalized facts, relations, provider features/edges, parameter definitions, recommendations, simulations, mappings/profiles, and evidence references.
2. Replaced Boolean passthrough with 149 field-driven contracts and 11 reusable deterministic primitives. Signal booleans and synthetic outcomes are quarantined.
3. Split import preview from explicit transactional commit, with canonical lineage and duplicate protection.
4. Added typed provenance-aware configuration, sparse-data-aware guidance, robust percentile/median-MAD/IQR/Wilson/empirical-Bayes utilities, non-mutating simulation, and prospective Admin versions.
5. Added readable claim evidence, support-aware provider context, maintained React Flow graph controls, accessible edge table, and claim-linked evidence.
6. Added richer reconciled reports, graph edge export, rule/provider/network/dataset/evaluation APIs, and complete operator documentation.
7. Completed synthetic release checks and updated implementation, acceptance, testing, security, architecture, configuration, data dictionary, import, and user guides.
8. Added user-started background evaluation with durable progress, honest per-batch assessment states, population-wide overview reconciliation, dataset-backed rule decision support, corrected percentile guidance/simulation, and an explainable provider-member network with ranked evidence paths.
9. Completed the governed UX remediation: evidence-linked readmission evaluation, plain-language claim explanations, explicit limited-coverage warnings, validation evidence before commit, production-evaluator simulation parity, live API health, accessible network evidence, full-population claims, provider analytics, scoped reports, and human-readable audit history.
10. Re-ran the full synthetic population with evaluator `canonical-evidence-v2-2026-09-28`: run #4 completed all 20,893 claims × 149 controls with 147 rule-claim triggers and zero evaluator errors. The formerly misidentified claim `C0020397` now correctly abstains for missing earlier history; `C0020596` links to it as the later admission with a derived 14-day discharge-to-admission gap.

## Dataset safety gate

Aggregate-safe profiling of the only candidate file reports 20,893 rows and 26 columns spanning 2023-01-01 through 2028-04-02. Batch 2 imported all 20,893 rows using the confirmed `synthetic_uae_v1` mapping; the database now contains 20,896 claims after preserving the original three demo rows, 1,343 provider tokens, 12,654 member tokens, and 564,111 canonical facts. The source is explicitly synthetic and includes outcome-like columns. Those columns are held out and are not stored as evaluator inputs. The 858 warnings comprise preserved window and approved-above-requested anomalies, not dropped rows.

## Validation evidence

| Check | Result |
|---|---|
| Full backend | 330 pass after synthetic mapping, anomaly-warning, bounded-graph, honest overview/export, evidence provenance, source-traceable network export, zero-row provenance, multi-run snapshot-manifest reconciliation, lower-bound simulation, stale-baseline rejection, and ordered configuration coverage were added. |
| 149-rule matrix | All positive, negative/boundary, missing-input, and exclusion cases pass. |
| Frontend | Unit, strict typecheck, lint, and production build pass. |
| E2E | 2 Playwright workflows pass; background demo evaluation reports 149 rules and 0 errors. |
| Accessibility/visual | Keyboard, labels, table alternative, overflow, desktop/mobile login, and graph screenshot comparisons pass. |
| Migration/import/export | Preservation, idempotency, preview-no-mutation, commit atomicity, and export reconciliation pass. |
| Performance | 10k validation 0.3130 s; 149k evaluations 19.5225 s; graph/export thresholds pass; peak 11.21 MB. |
| Security | Static gate passes; dependency installation audit reported 0 vulnerabilities. |

The final independent network/report recheck found no remaining P0 or P1 issue in its scope and returned `PASS / RELEASE-READY`. Two other final reviewer processes exhausted their account usage limit; their earlier findings were converted to regression tests and are covered by the green full suite.

## Real-data continuation

To pursue `DATASET_CALIBRATED_READY`, supply a tokenized real extract and governed references, run `python scripts/profile_dataset.py <path>`, confirm reusable mappings, then execute time-correct recommendation stability, linkage/completeness, structural-break, simulation reconciliation, and real-data acceptance checks. Until then, no fraud-performance or approved-policy claim is made.
