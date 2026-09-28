# UX Remediation Plan

Status values: `TODO`, `IN PROGRESS`, `DONE`, `BLOCKED`.

## Milestone 1 — Decision safety and claim comprehension (`DONE`)

- Derive readmission timing only from identifiable earlier claims with the same member and primary diagnosis.
- Persist both claims as evidence; abstain when the earlier event is unavailable.
- Replace reason codes, raw dispositions and unitless comparisons with plain-language explanations.
- Show controls with results, unavailable controls, evidence limitations and a concrete review checklist.
- Label associated value as neither confirmed loss nor recovery.

Validation: backend evidence tests; claim-detail component tests; authenticated browser comprehension test.  
Exit: the five comprehension questions in the red-team review can be answered from claim detail.

## Milestone 2 — Honest import and evaluation workflow (`DONE`)

- Display accepted/rejected/warning counts, grouped issues, affected rows, mapping summary and normalized row preview before commit.
- Remove or qualify selectable source mappings that are not implemented.
- Explain analysis date and recommend it from the file period.
- Reconcile evaluation results by distinct claims, controls and rule-claim checks.
- Provide run detail, missing-data causes, failure recovery and explicit limited-assessment status.

Validation: import preview tests, duplicate-state tests, E2E warning review and batch-result reconciliation.  
Exit: every API validation issue is visible or downloadable before commit; partial completion cannot look complete.

## Milestone 3 — Safe rule decisions (`DONE`)

- Make purpose, trigger direction, current effective configuration and dataset readiness primary.
- Use one immutable batch/run/analysis-date population for graphs, guidance and simulation.
- Replay the production evaluator in simulation, including exclusions and lower-bound comparisons.
- Show baseline/candidate counts, added/removed claims, example claims and missing-data effects.
- Require explicit adoption of guidance and future-dated configuration rationale; show version history.

Validation: lower-bound simulation parity, configuration boundary tests, rule-detail E2E and accessibility.  
Exit: simulation reconciles to production evaluation and saving cannot silently overwrite or backdate a setting.

## Milestone 4 — Analyst population and provider workflows (`DONE`)

- Add server-side claim search/filter/sort with preserved pagination and scoped export.
- Split overview by full/limited/unevaluated/failed status and show run provenance.
- Downgrade broad provider peers to exploratory and disclose comparability limitations.
- Add assessed/flagged/limited provider counts, monthly trends and an accessible contributing-claims table.

Validation: API filter tests, overview reconciliation, provider-period tests and browser workflows.  
Exit: list/detail totals reconcile and no broad peer fallback is presented as clinically comparable.

## Milestone 5 — Explainable and accessible networks (`DONE`)

- Put ranked review paths before the graph and explain every ranking.
- Replace node-only filters with relationship-preserving filters.
- State exact displayed/full node and edge counts and the subset selection method.
- Use source claim IDs and provide an equivalent keyboard-accessible evidence table plus export.
- Translate HHI into a benchmarked provider-concentration explanation.

Validation: graph/table reconciliation, keyboard and screen-reader workflow, large-network visual tests.  
Exit: the graph is optional; every conclusion and supporting claim is available without the canvas.

## Milestone 6 — Reports, audit and shell trust (`DONE`)

- Add report population selection, preview, progress/errors and uniform provenance in every format.
- Render audit actors, actions, targets, outcome and change details; expose limits/pagination.
- Replace static connectivity with live health; add breadcrumbs, nested active navigation and route focus.
- Add skip navigation and a focus-trapped, Escape-close mobile drawer.

Validation: export reconciliation/provenance, audit event tests, offline health state, WCAG keyboard/mobile suite.  
Exit: UI claims exactly match exported/audited/system state.

## Final independent acceptance

Repeat the red-team review screen by screen with reviewers who did not implement the changes. Any P0 finding returns the product to `NOT USER-READY`. Synthetic-data status remains `ENGINEERING_READY_ON_SYNTHETIC_DATA` until real-data calibration is completed.
