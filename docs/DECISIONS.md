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

## D-004 — Catalogue incompleteness and interim evaluator boundary

- **Date:** 2026-09-15
- **Status:** Blocking final readiness
- **Decision:** Do not invent regulator/payment-policy semantics missing from the supplied catalogue. The interim evaluator accepts explicit structured booleans keyed by control ID, records the raw catalogue predicate and exclusions/configuration prose, treats absent facts as Not applicable, and treats absent family datasets as Disabled — missing data.
- **Evidence:** The catalogue audit verified all 164 rows but found that all lack explicit population, inputs, reason code, and evidence fields; only nine name a concrete `cfg.*` parameter; 48 have no canonical disposition and 42 imply multiple dispositions. `PAY-04-R01` also conflicts with its example contract.
- **Consequence:** The platform and scope registry can be verified, but 149 catalogue-semantic evaluators cannot honestly be called complete without a business-owned field/policy pack. This is disclosed throughout documentation and acceptance evidence.

## D-005 — Stage normalization

- **Date:** 2026-09-15
- **Status:** Accepted with visible source preservation
- **Decision:** Preserve original stage labels and normalize `PREPAY` to `PREPAY_SYNC`, `ASYNC`/`PREPAY_ASYNC` to `PREPAY_ASYNC`, `DAILY` to `POSTPAY_DAILY`, `WEEKLY` to `NETWORK_WEEKLY`, and `MONTHLY` to `MODEL_MONTHLY` only as scheduling metadata. Preserve `QUARTERLY` raw because the source defines no canonical mapping.

## D-006 — App-local responsive choices

- **Date:** 2026-09-15
- **Status:** Accepted pending design-system approval
- **Decision:** Use a 248 px analytical sidebar, 760 px mobile navigation breakpoint, and 38 px primary controls. Tables scroll within their workspace and retain identity/decision columns.
- **Reason:** Sidebar width, breakpoints, and minimum touch target remain unresolved in the Design System. These conventional app-local values use the canonical tokens and are explicitly not new system tokens.
