# Copy-ready Codex implementation prompt

Paste the complete prompt below into a new Codex task whose working directory is the `Med Fraud` folder.

---

## Role

You are the principal product engineer responsible for delivering a complete, polished, locally hosted medical claims fraud, waste, abuse, and payment-integrity detection proof of concept. Own the outcome end to end: architecture, data design, implementation, test data, automated tests, visual quality, local packaging, documentation, and final verification.

Work directly in the current `Med Fraud` folder. The finished product must run locally in a browser on Windows and require no external database, paid service, cloud account, or internet connection during normal use.

## Goal

Build the application described by these local sources:

1. `PRODUCT_PLAN.md` — approved product and technical plan.
2. `uae-medical-claims-fwa-developer-specification.md` — authoritative fraud-control catalogue and behavioral specification.
3. `model-classified-rules-detailed-guide.md` — authoritative identification of model-classified controls and their boundaries.
4. The adjacent `Design-System` folder at `C:\Users\Yoga 9\OneDrive\Desktop\Shahai\Design-System` — authoritative Shahai visual and interaction system.

The outcome is a working product, not a proposal, wireframe, partial scaffold, static mockup, or collection of disconnected demos.

## Instruction priority

Apply instructions in this order:

1. Safety and permission constraints of the Codex environment.
2. This implementation prompt and explicit user requirements.
3. `PRODUCT_PLAN.md`.
4. The fraud developer specification and model-classified guide.
5. The Design-System authority hierarchy: `locked-decisions.md`, canonical tokens, product/foundation/visualization guidance, governance, then historical evidence.
6. Existing repository conventions that do not conflict with the above.

If two local sources conflict, document the conflict in `docs/DECISIONS.md`, follow the higher-priority source, and continue. Ask the user only when the decision would materially change product scope or cause an irreversible/external action. Resolve ordinary technical choices autonomously.

## Required operating behavior

- Begin by reading all four source areas completely enough to implement them correctly. Read any `AGENTS.md` or repository instructions before editing.
- Inspect the available local Node.js and Python runtimes and choose compatible stable dependencies.
- Create and maintain `IMPLEMENTATION_STATUS.md` from the first development step. It must list phases, current status, completed checks, remaining failures, and exact commands used.
- Create `docs/DECISIONS.md` for material implementation decisions and assumptions.
- Create `docs/RULE_TRACEABILITY.md` and a machine-readable `docs/rule-traceability.csv` mapping all 164 catalogue controls to type, execution status, evaluator, required datasets, tests, UI visibility, and reason code.
- Work autonomously through implementation, integration, test failures, visual QA, and documentation. Do not stop after planning or scaffolding.
- If collaboration/subagent tools are available, use them for bounded independent work such as import schemas, UI verification, and rule-pack implementation when parallelism will improve speed or quality. The primary agent remains responsible for integration, conflict resolution, and final verification.
- Preserve user files. Do not delete or overwrite the supplied catalogue, guide, plan, or Design-System source.
- Use version control if already available. If the folder is not a repository, do not make repository initialization a blocker.
- Never claim a check passed unless you ran it and captured the result.
- Keep dependencies free for local use and record their licences in `docs/THIRD_PARTY.md`.

## Non-negotiable product scope

### Users and authorization

Implement two predefined local accounts:

- `admin`: full operational access plus rule state, threshold, weight, and reference/configuration editing.
- `analyst`: all operational actions except modifying thresholds, weights, rule state, reference policy, or models.

Seed usernames, but configure initial passwords during setup or first launch. Store salted password hashes only. Enforce role permissions in the API. Hiding an interface control is insufficient authorization.

### Deployment and storage

- Local browser application.
- Default bind address `127.0.0.1`.
- One active user at a time is sufficient.
- Embedded SQLite database.
- Local generated reports and optional retained uploads.
- No external database, SaaS, telemetry, third-party analytics, or paid API.
- Provide Windows PowerShell scripts for setup, start, stop where necessary, test, demo reset, backup, and restore.

### Input and history

- Accept `.xlsx` and `.csv` claim/reference uploads.
- Provide Abu Dhabi/Shafafiya-aligned, Dubai/eClaimLink-aligned, and canonical template packs.
- Support all domains: outpatient, inpatient, dental, pharmacy, laboratory, medical devices/supplies, and the remaining catalogue specialties.
- Accumulate historical records locally.
- Evaluate against the five-year rolling service-date window ending at a user-selected analysis date.
- Use explicit `network_id` or effective-dated network membership; do not infer the network boundary.
- Treat member/provider identifiers as tokenized opaque values.

### Results

- High-level claim decision: `Flagged` or `No flag detected`.
- Always pair it with evaluation coverage: `Complete` or `Partial`.
- Show a primary reason at summary level.
- Drill-down shows all triggered rules, evidence, threshold, disposition, rule/configuration versions, exclusions considered, related claims, provider signals, network signals, and disabled rules.
- Never display “not fraudulent” as the clean state.
- Never present a signal as confirmed fraud or gross flagged value as confirmed savings.

### Rules

The catalogue contains 164 atomic controls across 39 scenarios.

- Exactly three controls are excluded because their declared type contains `M`:
  - `CLN-01-R02`
  - `ANL-01-R03`
  - `ANL-01-R04`
- Exactly 161 non-model controls remain in the roadmap.
- Exactly 12 text/document-dependent controls are deferred from execution:
  - `ENT-06-R02`
  - `PAY-05-R02`
  - `PAY-09-R01`
  - `CLN-01-R03`
  - `CLN-08-R03`
  - `DOC-01-R02`
  - `DOC-01-R03`
  - `DOC-01-R04`
  - `DOC-02-R01`
  - `DOC-02-R02`
  - `DOC-02-R03`
  - `DOC-02-R04`
- The first complete structured POC target is exactly 149 executable non-model, non-text controls.
- `DOC-01-R01` and structured document-presence/metadata checks may execute when their metadata exists.
- Every one of the 164 controls must appear in the rule registry and traceability output. None may be silently omitted.
- A structured evaluator must exist for every one of the 149 executable controls, even when a particular import cannot run it because an optional dataset is absent.
- Missing required data results in `Disabled — missing data`, not pass, fail, zero score, or silent omission.
- Deferred text controls report `Deferred — document capability`.
- The three model controls report `Excluded — model rule`.

### Configuration

- Thresholds and weights are editable by Admin only.
- Ship conservative synthetic POC defaults with unit, allowed range, scope, rationale, source, and the label `POC default — not approved policy`.
- Parameter changes create a new effective-dated version.
- Changes apply only to evaluations created afterward.
- Existing results retain the original rule and parameter snapshot.
- Do not automatically reevaluate history after a configuration change.
- Statistical/network rules must have minimum-volume and minimum-peer protections.

### Reports

Implement:

- On-screen dashboards and detail views.
- Filtered CSV exports.
- Multi-sheet Excel exports.
- Printable PDF batch, claim, provider, network, rule-coverage, and data-quality reports.
- Export metadata: generated time, analysis period, filters, user role, configuration/rule versions, coverage limitations, and decision-support disclaimer.

## Architecture target

Use the following architecture unless inspection reveals a concrete compatibility problem. Record any substitution and its reason in `docs/DECISIONS.md`.

### Front end

- React.
- TypeScript with strict mode.
- Vite.
- Accessible routing, forms, tables, dialogs, and charts.
- A maintained table solution is acceptable, but do not use a heavy paid/proprietary grid.
- Use a locally available/open-source chart library and provide accessible table equivalents.

### Back end

- Python.
- FastAPI.
- Pydantic schemas.
- SQLAlchemy or SQLModel-style repository layer.
- SQLite migrations with a supported migration mechanism.
- Polars or Pandas-compatible local analytics for tabular computation.
- NetworkX or an equivalent free local graph library for deterministic network features.
- openpyxl or XlsxWriter-compatible Excel handling.
- A free local PDF generation library such as ReportLab.

### Application modules

Separate at least these concerns:

- authentication and sessions;
- authorization;
- database and migrations;
- canonical domain models;
- import profiles and field mapping;
- validation and data-quality reporting;
- claim lineage and episode construction;
- rule registry and configuration versions;
- hard/expert/statistical/network evaluators;
- feature and peer-baseline computation;
- signal storage and correlation;
- claim/provider/network query services;
- exports;
- audit log;
- backup/restore;
- synthetic data generation.

Avoid a single monolithic evaluator file. Organize evaluators by scenario family and reuse well-tested primitives for dates, lookbacks, effective-dated joins, peer calculations, arithmetic tolerances, code equivalence, graph measures, and evidence formatting.

## Expected repository shape

Create a coherent structure equivalent to:

```text
Med Fraud/
├─ apps/
│  ├─ web/
│  └─ api/
├─ packages/
│  ├─ design-tokens/
│  ├─ import-schemas/
│  └─ rule-contracts/
├─ rules/
│  ├─ registry/
│  ├─ fixtures/
│  └─ README.md
├─ data/
│  ├─ templates/
│  ├─ demo/
│  └─ local/
├─ docs/
├─ scripts/
├─ tests/
├─ PRODUCT_PLAN.md
├─ IMPLEMENTATION_STATUS.md
└─ README.md
```

Adapt the exact folders when toolchain conventions justify it, but preserve clear boundaries and all required artifacts.

## Canonical data model

Implement effective-dated canonical entities for at least:

- member;
- coverage period;
- benefit rule/version and accumulators;
- provider and facility;
- provider licence/status/privilege periods;
- provider network membership;
- claim header;
- claim line/activity;
- diagnosis;
- encounter;
- observation/result/order metadata;
- authorization and authorization line;
- claim version/lineage;
- remittance/payment/denial/adjustment;
- prescription/dispense;
- tariff/contract/package/DRG rules;
- referral/ordering relationship;
- adjudicator/override event;
- refund/credit/recovery/COB/TPL data;
- policy/enrollment event;
- provider capacity/staff/equipment/inventory;
- member attendance/confirmation/complaint metadata;
- import batch and issue;
- rule/version/parameter;
- evaluation run;
- rule evaluation;
- signal/correlated result;
- audit event.

Requirements:

- Preserve source profile, source vocabulary, original source keys, and parsed values.
- Use append-only or versioned behavior for claim corrections, cancellations, resubmissions, and effective-dated reference facts.
- Store `valid_from`, `valid_to`, `recorded_at`, `source`, and `version_id` where temporally relevant.
- Use service-time as-of joins unless a rule explicitly requires submission time.
- Normalize timestamps consistently while retaining source-local representation.
- Protect monetary calculations from binary floating-point errors; use fixed decimal behavior and explicit rounding.
- Enforce foreign keys and indexes for the expected query paths.
- Make import replay idempotent through file checksum, source keys, and deterministic upsert/version behavior.

## Import templates and validation

Create three user-downloadable template packages:

1. Shafafiya-aligned `.xlsx`.
2. eClaimLink-aligned `.xlsx`.
3. Canonical multi-CSV package.

Each Excel template must contain:

- `README` sheet;
- one sheet per supported dataset;
- field name, source meaning, canonical mapping, type, required/optional state, example, allowed values, and rule families enabled;
- jurisdiction notes and version metadata;
- no macros.

Validation must detect and report:

- missing sheets/files or columns;
- wrong types and unparseable dates/numbers;
- duplicate source keys;
- broken parent/child relationships;
- invalid effective-date intervals;
- future dates outside allowed meaning;
- claims older than the selected five-year window;
- unknown code systems/versions;
- inconsistent currency/amount equations;
- missing identifiers required for a requested rule pack;
- mismatched jurisdiction profile;
- duplicate file/batch checksum.

Provide blocking errors and non-blocking warnings with file, sheet, column, row, code, plain-language message, and correction guidance. Preview validation before commit. Commit must be transactional: either all valid intended rows are committed according to the chosen policy or no partial hidden state is left.

## Rule engine contract

Create a typed, validated rule contract with at least:

- `rule_id`;
- `scenario_id`;
- `name`;
- `version`;
- `status` (`shadow`, `active`, `retired`, `deferred`, `excluded`);
- `type`;
- `stage`;
- `population`;
- required datasets/fields;
- expression/evaluator name;
- parameters with types, units, bounds, defaults, and scope;
- exclusions;
- missing-data behavior;
- base score/weight;
- disposition;
- reason code and reason template;
- evidence fields;
- effective dates;
- source/rationale;
- owner placeholder;
- POC-policy warning.

At application startup and in CI/tests:

- validate registry schema;
- assert 164 unique rule IDs;
- assert the catalogue ID set equals the registry ID set;
- assert three model exclusions match the specified IDs;
- assert 12 deferred text IDs match the specified list;
- assert 149 structured executable controls;
- assert every executable rule maps to an evaluator and tests;
- fail startup clearly if registry integrity is broken.

## Rule implementation requirements

Implement the supplied catalogue by family:

- `ENT`: eligibility, identity, licence, provider identity/activity, place of service, telehealth.
- `PAY`: duplicates, unbundling, code/units/time, authorization, modifier/edit bypass, tariff, patient share, resubmission, disguised non-covered services, COB/TPL, adjudication manipulation, reversal/refund/remittance.
- `CLN`: upcoding, diagnosis/severity, incompatibility, repeat/excess, LOS/readmission, phantom billing, capacity, laboratory/pathology/genetics.
- `PHR`: prescription/authorization/dispense, refill, specialty product spikes, steering, devices/supplies.
- `DOC`: structured document-presence metadata only in this release; text-based entries deferred.
- `NET`: referral, reciprocity, collusion/shared identifiers, provider-member patterns, broker/employer groups.
- `ANL`: transparent robust peer composite and self-history change point only; exclude the two `M` rules.
- `POL`: eligibility/roster, retroactive events, fact conflicts, early tenure, employer/broker clusters.

For each executable rule:

- implement the exact population and trigger semantics in the catalogue;
- make the configurable quantity explicit;
- implement listed exclusions where structured data permits;
- define deterministic missing/null behavior;
- create evidence in original business units;
- preserve reference/configuration versions;
- use the allowed disposition;
- avoid claiming intent;
- link contributing claim/member/provider/network records;
- support idempotent replay;
- add positive, clean negative, boundary, missing-input, effective-date, and exclusion fixtures;
- add correction/cancellation/resubmission fixtures when applicable.

Do not implement rule entries as unconditional placeholders returning “not triggered.” A rule counts as executable only if its tests demonstrate both triggering and non-triggering behavior from realistic inputs.

## Statistical and network implementation

### Peer analytics

Use the catalogue hierarchy:

```text
activity/code family
→ specialty
→ encounter/facility type
→ payment/contract family
→ geography
→ provider size/volume band
```

- Use robust percentiles or median/MAD for skewed values.
- Use empirical-Bayes shrinkage for rates where applicable.
- Enforce configurable minimum provider claim counts and peer entity counts.
- Back off sparse peers to the parent group and record `peer_level_used`.
- Show numerator, denominator, raw value, shrunk value/interval where used, peer median/percentile, threshold, and period.
- Never use protected identifiers as features.

### Change detection

- Use a transparent CUSUM, EWMA, or equivalent non-model method.
- Require minimum history periods.
- Record pre-change level, post-change level, change date, confidence/strength, and exclusions for known operational changes.

### Graph/network analytics

- `network_id` defines boundaries.
- Use typed nodes and typed, time-bounded edges.
- Implement the catalogue's required concentration, reciprocity, component, density, community, shared-identifier, circulation, and centrality primitives where applicable.
- Compute within comparable node types and relevant periods.
- Never auto-merge on a low-confidence/fuzzy shared identifier.
- Count each claim and associated amount once in network exposure.
- Graph results require an accessible tabular representation and evidence links.

## Scoring, decisions, and correlation

Implement the hybrid practice in `PRODUCT_PLAN.md` and catalogue:

- Hard objective failures may create a direct flag with their permitted disposition.
- Expert rules create review-oriented flags.
- Statistical/network signals trigger only after data-quality, minimum-volume, and configured threshold checks.
- No statistical/network signal alone may automatically assert confirmed fraud, reject a claim, or sanction a provider.
- Preserve shadow signals while visually distinguishing them from active flags.
- Cap repeated evidence from the same underlying fact rather than summing it repeatedly.
- Select the primary reason deterministically by disposition severity, evidence strength, exposure, then rule ID.
- Store all priority components and compute a reproducible transparent score consistent with the catalogue formula.
- Correlate claim lineage, episode, provider/scenario period, pharmacy/product, network snapshot, and distribution cohort with deterministic fingerprints.
- This correlation is presentation grouping, not case-management workflow.

Exposure rules:

- line edit: `max(0, submitted_payable - correctly_repriced_payable)`;
- duplicate: lower duplicate paid/requested amount after valid patient share;
- provider/network: distinct associated value unless exposure can be deterministically established;
- label gross/associated amount separately from estimated exposure and savings.

## API surface

Implement versioned local API routes equivalent to:

- `/auth`: login, logout, session, role.
- `/imports`: templates, upload, validate, commit, history, issues.
- `/evaluations`: create, progress, summary, coverage, failures.
- `/claims`: list, filters, detail, lines, signals, lineage, episode.
- `/providers`: list, filters, detail, metrics, signals, trends.
- `/networks`: list, filters, detail, graph, metrics, signals.
- `/rules`: registry, versions, required inputs, status.
- `/configuration`: effective-dated parameters and reference data.
- `/reports`: CSV, Excel, PDF generation/status/download.
- `/audit`: read-only events.
- `/health`: process, database, migration, registry, and version readiness.

Use typed request/response schemas, pagination, stable error shapes, explicit status codes, and OpenAPI documentation. Validate permissions at the service/API boundary.

## Interface requirements

Build all screens in `PRODUCT_PLAN.md`:

1. Sign in.
2. Overview dashboard.
3. Upload and validation wizard.
4. Claims list.
5. Claim detail.
6. Providers list and detail.
7. Networks list and detail/graph.
8. Rules and configuration.
9. Imports and data quality.
10. Reports.
11. Audit log.

### Tables

Claims, providers, networks, rules, imports, and audit views are flagship data tables. Implement the relevant features:

- search;
- filters;
- sorting;
- pagination;
- selection;
- row actions;
- expandable rows;
- status text/icon;
- loading, empty, partial, and error states;
- pinned columns where necessary;
- comfortable and compact density modes;
- right-aligned/tabular numeric values;
- accessible keyboard navigation.

### Upload experience

- Profile selector.
- Template download.
- File picker and drag/drop.
- File manifest.
- Schema mapping/recognition.
- Row preview.
- Blocking errors and warnings.
- Rule-readiness impact before commit.
- Commit/evaluate actions.
- Stage and rule-count progress.

### Claim detail

Lead with decision, reason, disposition, priority, amount/exposure, coverage, and analysis period. Then show triggered rules, all evaluation statuses, claim facts, diagnoses, encounter, authorization, remittance, lineage, episode timeline, provider/network connections, and exports.

### Provider detail

Show volume/value, flag rate, exposure/associated value, rule families, trends, peer group and level used, percentile/interval, specialty/facility/network, and contributing claims.

### Network detail

Show explicit membership, provider/pharmacy/member nodes, typed relationships, concentration/reciprocity, trends, associated value, triggered rules, graph filters, direct evidence, and a table equivalent.

## Shahai design-system requirements

Read and follow the Design-System authority hierarchy. At minimum inspect:

- `README.md`;
- `locked-decisions.md`;
- `tokens/README.md`;
- `tokens/mediums/product.json`;
- all relevant semantic, primitive, component, and data-visualization token files;
- `products/principles.md`;
- `products/layout-surfaces.md`;
- `products/navigation.md`;
- `products/data-dense-ui.md`;
- `products/forms-inputs.md`;
- `products/states-feedback.md`;
- relevant foundations, visualization, accessibility, anti-pattern, and validation guidance.

Implementation invariants:

- Dark-first, theme-ready experience.
- Poppins for working UI; Radnika Next only for the wordmark.
- Use the canonical token values rather than visually guessed replacements.
- Preserve token names or a documented mapping in `packages/design-tokens`.
- Structural navy and restrained cream use.
- Controlled soft geometry from the approved radius scale.
- Semantic status colors from the theme-specific tokens.
- Never communicate status with color alone.
- Use clear statement/detail separation.
- Allocate dashboard space by decision importance.
- Avoid decorative, oversized KPI-card grids.
- Use the approved data-visualization palette with direct labels where applicable.
- Include accessible chart table equivalents.
- Use real content and long-value stress tests.
- Where a component detail is unresolved, choose the smallest conventional accessible behavior consistent with tokens and record it in `docs/DECISIONS.md`; do not invent a new Shahai motif or token family.

Copy or transform only the token/font assets needed for the product. Do not modify the source Design-System repository.

## Synthetic data and demonstration

Create deterministic synthetic UAE-style data with fictional, tokenized entities. Include at least:

1. A clean five-year baseline spanning Abu Dhabi and Dubai and every claim domain.
2. A suspicious-pattern dataset that triggers representative controls across every scenario family, including duplicates, coverage, authorization, code/unit/time, unbundling, tariff/share, resubmission, provider outliers, pharmacy/device issues, capacity, referral/network reciprocity, payment/refund, adjudicator, and policy/enrollment patterns.
3. A partial-data dataset that demonstrates disabled rules and partial coverage.

Create an expected-results manifest with:

- rule ID;
- triggering claim/entity IDs;
- expected reason code;
- expected disposition;
- expected evidence keys;
- expected active/shadow/disabled state.

Provide a one-command demo reset/seed and a concise `docs/DEMO_SCRIPT.md` that walks through login, import, evaluation, claim drill-down, provider view, network view, threshold update, future-only behavior, and exports.

## Testing requirements

### Backend/unit

- Rule registry integrity/count tests.
- Rule evaluator fixtures for all 149 executable controls.
- Canonical schema and effective-date tests.
- Money/rounding/time-zone tests.
- Import-validation and transactional-commit tests.
- Five-year window tests.
- Lineage/episode/idempotency tests.
- Scoring/correlation/deduplication tests.
- Permission and password/session tests.
- Provider peer/shrinkage/backoff tests.
- Graph metric and distinct-exposure tests.
- CSV/Excel/PDF content reconciliation tests.
- Backup/restore tests against temporary demo databases.

### Frontend/unit/integration

- Sign-in and role-aware navigation.
- Admin editable vs. Analyst read-only configuration.
- Upload validation states.
- Table filters/sorting/pagination/density.
- Claim/provider/network drill-down.
- Complete vs. partial coverage.
- Loading, empty, warning, error, and completed-with-errors states.
- Export initiation and failure display.
- Accessible names, focus, keyboard behavior, and status redundancy.

### End to end

Automate at least these browser workflows:

1. Admin login → demo import → evaluation → flagged claim → evidence drill-down.
2. Analyst login → upload/evaluate/export → configuration write rejected.
3. Admin threshold change → old result unchanged → new evaluation uses new version.
4. Partial-data upload → disabled-rule counts shown → no false complete coverage.
5. Provider outlier → peer evidence → contributing claims.
6. Explicit network → suspicious relationship → graph and table evidence.
7. CSV, Excel, and PDF totals reconcile with selected filters.
8. Invalid import → row-specific feedback → no partial commit.
9. Duplicate upload → idempotent behavior.
10. Backup → reset demo state → restore → key counts/results return.

### Visual verification

Run the app and inspect every main screen at practical desktop/laptop widths. Capture screenshots to a local QA folder. Check:

- correct Shahai tokens and typography;
- spacing/hierarchy;
- overflow and long content;
- missing values;
- large AED numbers;
- compact/comfortable tables;
- hover/focus/selected/disabled/error states;
- dark theme and light-theme readiness;
- charts, graph, and table equivalents;
- printable PDF pages.

Use the Design-System validation tests, including Skeleton, Squint, Grayscale, No-Logo, Real-Content, and Removal checks where applicable. Iterate after inspection; do not accept the first render automatically.

## Built-in success metrics

Create `docs/ACCEPTANCE_REPORT.md` and populate it from actual test/run evidence. The product is not ready until every required metric is met or a user-approved exception is recorded.

### Scope metrics

| Metric | Required result |
|---|---:|
| Catalogue rule IDs represented | 164/164 |
| Model rules excluded | Exactly 3 specified IDs |
| Deferred text controls | Exactly 12 specified IDs |
| Structured executable controls | 149/149 |
| Executable controls with registered evaluator | 149/149 |
| Executable controls with positive fixture | 149/149 |
| Executable controls with clean negative fixture | 149/149 |
| Executable controls with boundary fixture | 149/149 |
| Silent/unclassified controls | 0 |

### Functional metrics

| Metric | Required result |
|---|---:|
| Predefined users can authenticate | 2/2 |
| Analyst forbidden configuration mutations rejected by API | 100% of authorization tests |
| Upload profiles | 3/3 |
| Required dashboards/detail areas | 11/11 |
| Export types | CSV + Excel + PDF |
| Historical window | Exactly five years ending at selected date |
| Configuration version reproducibility | 100% of versioning tests |
| Duplicate import idempotency | No duplicate canonical rows or signals |
| Partial-data behavior | Missing rules disabled and disclosed |

### Quality metrics

| Metric | Required result |
|---|---:|
| Backend automated tests | 100% pass |
| Frontend automated tests | 100% pass |
| End-to-end critical workflows | 10/10 pass |
| Registry/schema validation | 100% pass |
| TypeScript type check | 0 errors |
| Lint | 0 errors; warnings documented and justified |
| Production frontend build | Pass |
| API startup and migrations | Pass from clean state |
| Accessibility automated critical violations | 0 |
| Broken local navigation routes | 0 |
| Unhandled browser console errors in E2E | 0 |
| Export reconciliation variance | AED 0.00 and count 0 |
| Graph/network duplicate exposure | 0 duplicate-counted claims |

### Data and rule accuracy metrics

| Metric | Required result |
|---|---:|
| Synthetic expected triggered results | 100% exact rule-ID match |
| Synthetic clean negatives | 0 unexpected active hard-rule flags |
| Effective-date boundary results | 100% fixture match |
| Money rounding fixtures | 100% fixture match |
| Replayed evaluation | Identical deterministic results and no duplicate signals |
| Evidence required keys | 100% present for triggered fixtures |
| Disabled due to missing inputs | 100% correctly classified |

### Performance metrics

Measure on the available target machine and record hardware/runtime versions. Required POC targets:

- Validate a 1,000-claim-line canonical workbook in no more than 15 seconds.
- Evaluate a 1,000-claim-line new batch against at least 10,000 historical lines in no more than 60 seconds.
- Load a paginated claims page in no more than 2 seconds after warm startup.
- Apply ordinary table filters in no more than 500 ms perceived time.
- Generate a typical filtered CSV in no more than 5 seconds.
- Generate a typical multi-sheet Excel report in no more than 15 seconds.
- Generate a typical detailed PDF report in no more than 15 seconds.
- Peak memory during the standard demo remains below 2 GB.

If the target hardware cannot meet one performance threshold after reasonable optimization, document measured evidence, root cause, and the smallest remediation. Do not hide the failure or redefine the metric silently.

### Visual/product metrics

- Every main screen inspected from an actual running build.
- No horizontal page overflow at the selected supported widths; tables may scroll within their defined workspace.
- All decisions/statuses use text or icon/shape in addition to color.
- All form errors attach to their field or exact upload row.
- Every empty state explains what the area is, why it is empty, and the next action.
- All long IDs/reasons and large values remain readable or expose a clear full-value affordance.
- Dark theme uses canonical Shahai tokens; no invented palette.
- Printable PDFs render without clipped text, overlapping elements, or blank accidental pages.

## Failure handlers and recovery behavior

Implement these product failure states and follow these development recovery rules.

### Dependency/setup failure

- Capture the exact command and error.
- Check installed Node/Python versions and lockfile compatibility.
- Prefer a compatible supported dependency/version over ad hoc global installs.
- If network access is required and blocked, request the minimum needed permission once with a precise reason.
- Keep setup idempotent; a failed run may be safely retried.
- Never claim the product runs until setup succeeds from documented clean-state steps.

### Port conflict

- Detect whether the preferred local port is occupied.
- Reuse only a healthy instance belonging to this project.
- Otherwise select a documented free fallback port and print/open the exact URL.
- Never terminate an unrelated process automatically.

### Database initialization or migration failure

- Stop startup with a precise health error.
- Preserve the current database.
- Create a timestamped backup before any repair or migration retry.
- Migrate transactionally where supported.
- Never delete a user database automatically.
- Automatic reset is allowed only for a clearly identified disposable demo database and must be logged.

### Import parse/validation failure

- Do not commit hidden partial rows.
- Keep the failed batch and issues visible in import history where safe.
- Return row/sheet/column-level messages and correction guidance.
- Permit corrected retry without duplicate data.
- If an optional dataset is absent, disable dependent rules and mark evaluation coverage partial.

### Rule evaluator exception

- Catch at the rule boundary.
- Record rule ID, evaluator version, exception category, timestamp, and safe diagnostic details.
- Mark that rule `Error` for the run; never convert the error to pass or no flag.
- Continue independent rules when data integrity permits.
- Mark the run `Completed with errors` and evaluation coverage `Partial`.
- Surface the failure in UI, exports, logs, and acceptance report.
- Before final delivery, no evaluator errors may remain in the clean or suspicious standard demo runs.

### Statistical insufficiency

- If provider volume, peer population, history, or data quality is inadequate, return `Insufficient data`/disabled status.
- Do not calculate a misleading percentile from sparse peers.
- Record the failed prerequisite and next broader peer considered.
- Do not generate an active provider/network flag solely from insufficient evidence.

### Configuration failure

- Validate type, unit, allowed range, effective date, scope, and cross-field invariants before save.
- Reject invalid saves atomically and preserve the prior active version.
- Record successful changes in the audit log with old/new values and user.
- Analyst API attempts receive a clear forbidden response and create an appropriate security audit event without exposing secrets.

### Evaluation cancellation or process interruption

- Persist stage progress and run status.
- On restart, show the interrupted run as `Interrupted` unless safe deterministic resume is implemented.
- Allow a clean retry using the same committed batch.
- Idempotent retry must not duplicate signals.

### Export failure

- Generate to a temporary file and atomically publish only after success.
- Delete or quarantine incomplete temporary outputs.
- Show actionable error context without leaking secrets.
- Keep the filtered result view intact so the user can retry.
- Validate generated workbook/PDF before returning it.

### Backup/restore failure

- Validate source/target paths and database compatibility.
- Backup current state before restore.
- Restore through a temporary copy and integrity check, then replace atomically.
- On failure, keep the original active database untouched.
- Never recursively delete broad directories.

### Frontend/API disconnect

- Show a persistent connection error and retry option.
- Preserve unsent form/upload choices in memory where practical.
- Do not show stale data as newly evaluated.
- Health checks distinguish API unavailable, database unavailable, migration failure, and registry invalid.

### Test or build failure during development

- Reproduce with the narrowest reliable command.
- Diagnose the root cause.
- Fix implementation or test data; do not weaken meaningful assertions merely to obtain green status.
- Rerun the targeted test, then the affected suite, then the full release checks.
- Update `IMPLEMENTATION_STATUS.md` with the result.
- If a failure is environment-only, provide evidence and a deterministic workaround in `docs/TROUBLESHOOTING.md`.

### Performance failure

- Profile before changing architecture.
- Add appropriate indexes, chunked parsing, bounded memory operations, cached immutable aggregates, or background progress.
- Preserve correctness and auditability.
- Re-run the same benchmark and record before/after measurements.
- If still failing, document the unmet metric; do not report success.

### Visual/accessibility failure

- Fix the component or token mapping at the shared level when possible.
- Re-run affected component tests and inspect all dependent screens.
- Do not solve contrast/status problems by introducing colors outside the design system.
- Do not remove information merely to make screenshots look cleaner.

## Security and privacy baseline

- Bind to localhost by default.
- Use secure password hashing and non-verbose login errors.
- Use HTTP-only, same-site session cookies and CSRF protection where applicable.
- Rate-limit authentication attempts locally.
- Validate file type, extension, size, workbook structure, and safe filenames.
- Never execute spreadsheet macros or formulas.
- Prevent CSV formula injection in generated exports.
- Sanitize displayed/uploaded strings.
- Apply least-privilege authorization to all writes and exports.
- Avoid secrets in source control, logs, URLs, screenshots, or reports.
- Exclude runtime data, generated reports, backups, credentials, and uploads from version control.
- Log security-relevant actions without logging passwords or full sensitive payloads.
- Treat this as tokenized-data POC protection, not compliance certification.

## Required scripts and documentation

Provide and test Windows-friendly commands/scripts equivalent to:

- `scripts/setup.ps1`
- `scripts/start.ps1`
- `scripts/test.ps1`
- `scripts/demo-reset.ps1`
- `scripts/backup.ps1`
- `scripts/restore.ps1`

Provide:

- `README.md` with exact prerequisites and first-run instructions.
- `docs/ARCHITECTURE.md`.
- `docs/DATA_DICTIONARY.md`.
- `docs/IMPORT_GUIDE.md`.
- `docs/RULE_TRACEABILITY.md` and CSV.
- `docs/CONFIGURATION_GUIDE.md`.
- `docs/USER_GUIDE.md`.
- `docs/DEMO_SCRIPT.md`.
- `docs/TESTING.md`.
- `docs/TROUBLESHOOTING.md`.
- `docs/SECURITY_AND_LIMITATIONS.md`.
- `docs/THIRD_PARTY.md`.
- `docs/DECISIONS.md`.
- `docs/ACCEPTANCE_REPORT.md`.

Documentation must match the actual commands and UI. Test the instructions from a clean disposable local state before finalizing.

## Implementation sequence and release gates

Use this sequence, but continue through all phases without waiting for routine approval.

### Gate 0 — Baseline and architecture

- Inspect sources and runtimes.
- Create status/decision/traceability artifacts.
- Scaffold the front end, API, database, migrations, tests, and scripts.
- Integrate Shahai tokens.
- Implement authentication shell.

Pass when both roles sign in, the API health check passes, clean migrations run, the app shell renders from canonical tokens, and setup/start/test commands work.

### Gate 1 — Canonical data and imports

- Implement domain schema.
- Implement three upload profiles/templates.
- Implement validation, preview, transactional commit, import history, checksum/idempotency, and five-year selection.
- Implement synthetic generator baseline.

Pass when clean, invalid, duplicate, jurisdiction-specific, and partial-data fixture imports behave exactly as specified.

### Gate 2 — Rule platform and claim-level evaluation

- Implement registry/config versions.
- Implement reusable evaluation primitives.
- Implement structured ingest/prepay claim rules.
- Implement evidence, scoring, reason selection, claim list/detail, and claim exports.

Pass when registry counts are exact, relevant rule fixtures pass, permissions are enforced, and an end-to-end claim evaluation is explainable and reproducible.

### Gate 3 — Historical/provider analytics

- Implement lineage/episodes.
- Implement daily/monthly historical features, peer service, robust/shrunk statistics, and change detection.
- Implement provider screens and exports.

Pass when provider fixtures trigger expected IDs, sparse peers abstain correctly, results link to contributing claims, and replay is deterministic.

### Gate 4 — Network/pharmacy/policy/payment analytics

- Implement typed graph primitives and remaining structured rule packs.
- Implement network screens and accessible graph/table evidence.
- Implement pharmacy, device, payer/override/refund, enrollment, employer/broker capabilities.

Pass when expected network/policy/payment fixtures match, legitimate exclusions work, and claim amounts are never double counted.

### Gate 5 — Full scope, reporting, and polish

- Finish all 149 executable evaluators and fixtures.
- Finish dashboards, data-quality/rule-coverage views, reports, audit, backup/restore, and demo flows.
- Complete accessibility, visual, performance, and failure-state QA.

Pass only when all built-in success metrics meet their targets and the acceptance report contains commands/results/evidence.

## Stop rules

Do not stop because the task is large, because a first version looks plausible, or because the main happy path works. Continue until the product meets the definition of done.

Stop and ask the user only when:

- required access or permission cannot be obtained after using all safe in-scope alternatives;
- a missing business choice would materially change the agreed product;
- a destructive or irreversible action outside disposable generated/demo state is required;
- a licensing restriction prevents lawful implementation and no equivalent free dependency exists; or
- a source contradiction cannot be resolved by the stated priority order.

If blocked, provide the exact blocker, completed work, evidence, safe alternatives tried, and the smallest user decision required. Do not replace implementation with another plan.

## Final definition of done

Before responding that the product is ready, verify all of the following:

- Local setup succeeds from documented steps.
- Local start launches a usable browser app.
- Both accounts and roles work.
- All 164 controls appear in traceability.
- The three exact model controls are excluded.
- The 12 exact text controls are deferred.
- All 149 structured controls have real evaluators and required fixtures.
- Shafafiya, eClaimLink, and canonical templates import.
- Five-year historical evaluation works.
- Claim, provider, and network decisions are explainable.
- Missing data yields partial coverage, never a false clean pass.
- Admin configuration is effective-dated and prospective.
- Analyst changes are denied by the API.
- CSV, Excel, and PDF reports work and reconcile.
- Synthetic clean, suspicious, and partial datasets work.
- Backup and restore work.
- Automated backend, frontend, E2E, registry, type, lint, and build checks pass.
- Performance metrics are measured and pass or have an explicitly user-approved exception.
- Main screens and PDFs have been visually inspected and corrected.
- Acceptance, traceability, user, setup, and troubleshooting documents reflect reality.
- No runtime secret, database, upload, report, or backup is accidentally tracked.
- No unresolved evaluator exception exists in standard demo runs.

## Final response format

Lead with whether the product is ready. Then provide:

1. What was built.
2. Exact setup and launch commands.
3. Demo usernames and how initial passwords are configured.
4. Automated test/build results with counts.
5. Rule coverage counts: 164 total, 3 excluded model, 12 deferred text, 149 executable.
6. Performance measurements.
7. Visual QA completed.
8. Paths to the acceptance report, traceability matrix, templates, demo script, and troubleshooting guide.
9. Any remaining blocker or user-approved exception.

If any required metric is unmet, state `Not ready` and continue working unless a true stop condition applies. Never use “ready” for a scaffold, mockup, incomplete rule set, unverified build, or product with hidden test failures.

Start now. Inspect the sources, create the implementation status and traceability baselines, then build and verify the complete product.

