# Implementation Decisions

This log records material choices, assumptions, and source conflicts. Supplied source files are not modified.

## D-001 — Runtime bootstrap

- **Date:** 2026-09-15
- **Status:** Accepted
- **Decision:** Use the Codex-bundled Python 3.12 runtime as the discoverable bootstrap interpreter when no system `python` or `py` launcher is available. `scripts/setup.ps1` will create a project-local virtual environment and install locked dependencies into it.
- **Reason:** The target Windows machine currently has Node.js but no Python executable on `PATH`. A project-local environment keeps runtime dependencies isolated and reproducible.
- **Consequence:** Setup documentation must state the bundled-runtime fallback and provide a clear error if neither a system nor bundled Python is present.

## D-002 — Repository initialization

- **Date:** 2026-09-15
- **Status:** Accepted
- **Decision:** Do not initialize Git automatically.
- **Reason:** The workspace is not a repository, and the implementation brief says repository initialization must not become a blocker. Creating repository history was not explicitly requested.

## D-003 — Scope-state taxonomy

- **Date:** 2026-09-15
- **Status:** Accepted
- **Decision:** Store immutable `EXECUTABLE`, `DEFERRED_DOCUMENT`, and `EXCLUDED_MODEL` scope separately from mutable Active/Shadow state and per-run readiness.
- **Reason:** This prevents missing uploads, deliberate document deferral, and model exclusion from being conflated. The exact 149/12/3 split follows the higher-priority Product Plan.

## D-004 — Catalogue incompleteness and evaluator boundary

- **Date:** 2026-09-15
- **Status:** Superseded on 2026-09-27 by the remediation contract engine
- **Decision:** Do not invent regulator/payment-policy semantics missing from the supplied catalogue. The former Boolean adapter was removed. Every executable rule now has an explicit engineering contract derived from catalogue semantics, while unavailable governed references disable evaluation and remain visibly pending payer approval.
- **Evidence:** The catalogue audit verified all 164 rows but found that all lack explicit population, inputs, reason code, and evidence fields; only nine name a concrete `cfg.*` parameter; 48 have no canonical disposition and 42 imply multiple dispositions. `PAY-04-R01` also conflicts with its example contract.
- **Consequence:** Engineering behavior can be verified on deterministic fixtures, but source mappings, policy references, empirical calibration, and performance claims cannot be approved without the real tokenized dataset and business owners.

## D-005 — Stage normalization

- **Date:** 2026-09-15
- **Status:** Accepted with visible source preservation
- **Decision:** Preserve original stage labels and normalize `PREPAY` to `PREPAY_SYNC`, `ASYNC`/`PREPAY_ASYNC` to `PREPAY_ASYNC`, `DAILY` to `POSTPAY_DAILY`, `WEEKLY` to `NETWORK_WEEKLY`, and `MONTHLY` to `MODEL_MONTHLY` only as scheduling metadata. Preserve `QUARTERLY` raw because the source defines no canonical mapping.

## D-006 — App-local responsive choices

- **Date:** 2026-09-15
- **Status:** Accepted pending design-system approval
- **Decision:** Use a 248 px analytical sidebar, 760 px mobile navigation breakpoint, and 38 px primary controls. Tables scroll within their workspace and retain identity/decision columns.
- **Reason:** Sidebar width, breakpoints, and minimum touch target remain unresolved in the Design System. These conventional app-local values use the canonical tokens and are explicitly not new system tokens.

## D-007 — Additive migration and normalized fact boundary

- **Date:** 2026-09-27
- **Status:** Accepted
- **Decision:** Preserve existing tables and rows, apply versioned additive migrations, and add queryable typed `canonical_facts` and `canonical_relations` alongside dedicated provider, configuration, recommendation, graph, and evidence tables. Flexible source payloads may remain JSON for lineage, but evaluator inputs must come from typed canonical records or deterministic aggregates over them.
- **Reason:** The remediation forbids essential production logic from remaining inside `facts_json` and requires migration without destroying user data. An additive boundary allows the current database to migrate safely while normalized imports replace the legacy adapter prospectively.
- **Evidence:** Verified backup `data/backups/pre-remediation-20260927.sqlite3`; migrations `0001` and `0002` applied; SQLite integrity is `ok`; 3 claims, 447 legacy rule evaluations, 164 rules, 2 users, and 13 audit events were preserved.

## D-008 — Real dataset remains gated

- **Date:** 2026-09-27
- **Status:** Accepted
- **Decision:** Treat `data/demo/claims_demo_synthetic.csv` only as an engineering fixture. Ignore its `fraud_label`, `fraud_type`, and `fraud_confidence` columns for production evaluation and never report them as measured performance.
- **Reason:** No real tokenized dataset is present. The file is explicitly synthetic and contains generated outcome fields; using those as production evidence would violate the measurement boundary and Boolean/synthetic-score prohibition.

## D-009 — Synthetic UAE adapter and AED label semantics

- **Date:** 2026-09-27
- **Status:** Accepted for the engineering fixture only
- **Decision:** Use the explicit `synthetic_uae_v1` mapping for the 20,893-row fixture. Rename its two source headers from `_inr` to `_aed` without changing numeric values, parse dates day-first, map hospital/patient/TPA identifiers to provider/member/network tokens, and preserve approved-above-requested cases as anomaly warnings.
- **Boundary:** This is a user-directed label correction, not an asserted FX conversion or a real-data mapping. Synthetic labels and confidence fields remain held out from claims, canonical facts, evaluators, recommendations, and performance reporting.
- **Evidence:** Batch 2 committed 20,893 rows with 858 non-blocking temporal/anomaly warnings, `CONFIRMED_SYNTHETIC_MAPPING`, and `labels_used_for_evaluation=false`.

## D-010 — Explicit evaluation state and analyst-led execution

- **Date:** 2026-09-28
- **Status:** Accepted
- **Decision:** A committed batch remains `NOT EVALUATED` until an analyst starts a run from **Upload & validation** and that run completes. Evaluation executes in a background worker with durable progress, a frozen configuration snapshot, bounded database transactions, and a visible failure state. Claims and population summaries resolve only against the latest completed run for their own batch.
- **Reason:** Importing data and evaluating controls are separate reproducible actions. Treating an imported row with no results as `No flag detected` is materially misleading, while forcing evaluation inside upload removes analyst control and makes large imports appear stalled.
- **Consequence:** Overview, claim list, and claim detail separately report flagged, no-flag, partial, and unevaluated states. Restarted interrupted runs are marked failed and can be rerun from the interface.
