# Medical Claims Fraud Detection POC — Product Plan

**Status:** Approved planning baseline; development has not started  
**Prepared:** 15 September 2026  
**Primary workspace:** `Med Fraud`  
**Target:** Polished, local, browser-based proof of concept for UAE medical claims fraud, waste, abuse, and payment-integrity detection

## 1. Product vision

Build a locally hosted browser application that accepts UAE-style medical claims and supporting reference data from CSV or Excel, evaluates all in-scope non-model controls in the supplied catalogue, and presents explainable claim-, provider-, and network-level results.

The product is a decision-support and reporting tool. It identifies non-payability, inconsistency, and abnormality; it does not declare that fraud has been proven. The user-facing vocabulary must therefore distinguish `RETURN`, `REJECT`, `REPRICE`, `PREPAY_PEND`, `POSTPAY_AUDIT`, `SIU_LEAD`, `PROVIDER_EDUCATION`, and `MONITOR_ONLY` from a legal or investigative fraud finding.

## 2. Confirmed product decisions

| Area | Decision |
|---|---|
| Users | Two predefined users: Admin and Analyst |
| Admin permissions | Full access, including thresholds, weights, rule state, and reference/configuration data |
| Analyst permissions | All operational functions except changing thresholds, weights, rules, or underlying models |
| Authentication | Local authentication; no external identity provider |
| Claim intake | CSV and Excel uploads |
| Data schema | Designed from the supplied fraud-control catalogue |
| UAE coverage | Abu Dhabi Shafafiya and Dubai eClaimLink profiles |
| Claim domains | Outpatient, inpatient, dental, pharmacy, laboratory, devices/supplies, and all other catalogue domains |
| History | Evaluate against accumulated historical claims in a rolling five-year lookback ending at a selected analysis date |
| Network definition | Explicit network/group identifier supplied in source data |
| Claim result | High-level Flagged / No flag detected, with primary reason; drill-down shows all rules and evidence |
| Post-flag workflow | Detection and reporting only; no assignment, notes, or investigation case workflow |
| Rule configuration | Admin-editable thresholds and weights; initial values are clearly marked POC assumptions |
| Configuration effect | Changes apply prospectively to future evaluations only |
| Documents | PDF/image and narrative-analysis controls are deferred |
| Reporting | On-screen dashboards plus CSV, Excel, and printable PDF exports |
| Language | English only |
| Deployment | Local browser app, used by one person at a time |
| Storage | Embedded local storage only; no external database or paid service |
| Data sensitivity | Tokenized/de-identified data for the POC |
| Demo content | Synthetic UAE-style clean and suspicious claims included |
| Quality target | Polished proof of concept, not a production adjudication system |

## 3. Scope and rule accounting

The supplied developer specification contains **39 scenarios and 164 atomic controls**.

### 3.1 In scope

- All controls whose declared type does not include `M`.
- 161 non-model controls in the complete roadmap.
- 149 structured-data controls in the first executable POC release.
- Hard (`H`), expert (`E`), statistical (`S`), network (`N`), and combinations of these types.
- Claim-level, member-level, provider-level, pharmacy/product-level, policy/employer-level, and network-level evaluation.
- Rule configuration, effective dating, evidence snapshots, reason codes, and versioned results.
- A data-readiness status for every rule: `Ready`, `Disabled — missing dataset`, `Disabled — deferred documents`, or `Excluded — model rule`.

### 3.2 Explicitly excluded from execution

These three controls contain `M` and will not be deployed:

1. `CLN-01-R02` — Expected-level residual (`S/M`)
2. `ANL-01-R03` — Unsupervised incremental anomaly (`M`)
3. `ANL-01-R04` — Novel-cluster discovery (`M`)

Their catalogue entries may be visible in a read-only rule inventory with status `Excluded — model rule`, ensuring the scope decision is auditable.

### 3.3 Deferred document/text controls

The following 12 controls require document or narrative interpretation and will be planned but not executed in the structured-data POC:

- `ENT-06-R02`
- `PAY-05-R02`
- `PAY-09-R01`
- `CLN-01-R03`
- `CLN-08-R03`
- `DOC-01-R02`, `DOC-01-R03`, `DOC-01-R04`
- `DOC-02-R01`, `DOC-02-R02`, `DOC-02-R03`, `DOC-02-R04`

`DOC-01-R01` and other structured document-presence checks may execute when document metadata is supplied, without reading document content.

### 3.4 Honest coverage behavior

A missing dataset must never be interpreted as a clean result. Each claim, provider, and network result will show:

- the binary decision: `Flagged` or `No flag detected`;
- evaluation coverage: `Complete` or `Partial`;
- number of applicable, passed, triggered, disabled, and not-applicable rules;
- missing datasets that prevented evaluation; and
- the exact rule/configuration versions used.

The UI phrase “No flag detected” is preferred to “Not fraudulent.”

## 4. UAE market alignment

The POC will use one canonical internal model with two explicit import profiles rather than assuming Abu Dhabi and Dubai are field-identical.

### 4.1 Abu Dhabi profile

- Preserve Shafafiya concepts including Claim, Encounter, Activity, Observation, diagnosis, patient share, authorization/prior request, remittance, denial, resubmission, sender, and receiver.
- Preserve original source vocabulary and source IDs alongside canonical values.
- Model claim line/Activity and Observation as separate linked entities.
- Carry code-list and policy versions with effective dates.

### 4.2 Dubai profile

- Map eClaimLink claim, encounter, activity, diagnosis/POA, clinician, facility, payer, denial, remittance, referral, pharmacy, and Dubai Drug Code fields into the same canonical model.
- Maintain a separate Dubai field-mapping profile and reference-data versions.
- Do not silently coerce Dubai-specific values into Abu Dhabi semantics.

### 4.3 POC ingestion boundary

Although both UAE ecosystems use structured electronic transactions in operational practice, the agreed POC input is CSV/Excel. The templates will mirror their important concepts and identifiers. Native XML/web-service adapters are an extension point, not a POC deliverable.

Official anchors to revalidate before implementation and before any real pilot:

- [DoH Shafafiya overview](https://www.doh.gov.ae/en/shafafiya/)
- [DoH Shafafiya data schema](https://shafafiyaportal.doh.gov.ae/dictionary/DataSchema.html)
- [DoH claims and adjudication rules](https://www.doh.gov.ae/-/media/Feature/shafifya/Prices/Adjudication-Rules/DOH-Claims-and-Adjudication-Rules-V2025.ashx)
- [DHA eClaimLink information hub](https://eclaimlink.ae/default.aspx/eClaim/infohub.aspx)
- [DHA/eClaimLink public coding sets](https://www.eclaimlink.ae/NoneRegisteredCodingSets.aspx)

The app will label bundled thresholds and reference rows as demonstration assumptions, not regulator-approved payment policy.

## 5. Users and access control

### 5.1 Admin

May sign in, upload and validate data, run evaluations, view every dashboard/detail, export reports, manage local reference datasets, enable/disable eligible rules, edit thresholds and weights, select analysis dates, and inspect the audit log.

### 5.2 Analyst

May sign in, upload and validate data, run evaluations, view every dashboard/detail, filter/search/drill down, and export reports. Thresholds, weights, rule activation, and policy/reference configuration are read-only.

### 5.3 Authentication design

- Two seeded accounts: `admin` and `analyst`.
- Passwords are configured during local setup; only salted password hashes are stored.
- Session cookie is local, HTTP-only, same-site, and expires after inactivity.
- Login failures are generic and rate-limited.
- The role is enforced by the API, not only by hidden interface controls.
- No model-management screen will be present because model rules are excluded.

## 6. Core user journeys

### 6.1 Sign in

1. User opens the local URL.
2. User enters predefined account credentials.
3. App routes to the dashboard and displays the active role.

### 6.2 Load historical data

1. User chooses jurisdiction: Abu Dhabi, Dubai, or canonical template.
2. User downloads the relevant workbook/CSV template pack.
3. User uploads one or more claim/reference datasets.
4. App validates file structure, types, dates, identifiers, relationships, duplicates, and five-year eligibility.
5. User sees blocking errors, non-blocking warnings, row samples, and rule-readiness impact.
6. Valid rows are committed locally as an immutable import batch.

### 6.3 Evaluate new claims

1. User uploads a new claim batch and selects the analysis date.
2. App evaluates ingest and claim-level controls, then historical, provider, and network controls over the rolling five-year window.
3. App shows measurable progress by stage and rule family.
4. Completed batch opens to a summary of flagged claims, primary reasons, dispositions, exposure, data coverage, provider signals, and network signals.

### 6.4 Investigate a result

1. User opens a flagged claim from the results table.
2. Header shows Flagged / No flag detected, primary reason, priority, disposition, associated amount, and coverage status.
3. Drill-down lists every triggered rule, evidence values, comparable records, threshold, rule version, exceptions considered, and related provider/network signals.
4. User can inspect claim lineage, episode history, and five-year context without editing the claim.

### 6.5 Change a threshold

1. Admin opens Rules & Configuration.
2. Admin selects an editable rule parameter or weight.
3. App shows current value, unit, scope, rationale, affected rule, and demo-warning label.
4. Saving creates a new effective-dated configuration version and audit event.
5. Existing results retain their original configuration snapshot; subsequent evaluations use the new version.

### 6.6 Export

Users may export the current filtered claim/provider/network view to CSV or Excel, and generate a printable PDF summary or detailed entity report. Every export includes generation time, analysis period, filters, rule/configuration version, coverage limitations, and the “signal is not a fraud finding” disclaimer.

## 7. Information architecture and screens

### 7.1 Sign in

- Shahai wordmark treatment, product name, username/password fields, show-password affordance, validation, and local-system notice.

### 7.2 Overview dashboard

- Analysis-period selector and current data coverage.
- Flagged vs. no-flag claim counts.
- Submitted amount and estimated exposure kept visually distinct.
- Most frequent reasons and dispositions.
- Provider and network signals requiring attention.
- Trend over time and latest import status.
- Direct paths to claims, providers, networks, and data-quality issues.

### 7.3 Upload & validation

- Profile choice, template download, drag/drop or file picker, file manifest, schema mapping, preview, validation results, and commit/run controls.
- Errors attached to exact sheet/file, column, and row.
- Duplicate batch detection using file checksum plus source identifiers.

### 7.4 Claims

- Flagship table with search, filters, sorting, pagination, pinned identity/status columns, comfortable/compact density, expandable evidence rows, and export.
- Key columns: decision, primary reason, claim ID, jurisdiction, service date, member token, provider, claim type, submitted/net/paid amount, exposure, priority, coverage, and evaluated time.

### 7.5 Claim detail

- Summary, triggered rules, full rule-evaluation coverage, claim/line facts, diagnoses, encounter, authorizations, remittances, lineage, episode timeline, related provider/network signals, and export.

### 7.6 Providers

- Ranked provider table and provider detail workspace.
- Metrics: volume/value, flag rate, exposure, rule families, trend, peer group used, percentile/interval where relevant, specialties, facilities, and networks.
- Statistical signals must show original business units and comparator population.

### 7.7 Networks

- Explicit network list and detail page.
- Summary metrics, members/providers/pharmacies, internal flow, referral concentration, suspicious relationships, signal trends, and distinct associated value.
- Graph view uses typed nodes/edges, direct labels, filters, and an accompanying accessible table. Each claim amount is counted once.

### 7.8 Rules & Configuration

- Searchable registry of all 164 controls.
- Status chips for Active, Shadow, Disabled/Missing data, Deferred documents, and Excluded model.
- Type, stage, scenario, priority, population, required inputs, parameters, exclusions, disposition, reason code, and version.
- Admin-only editing for eligible parameters/weights; Analyst read-only view.

### 7.9 Imports & data quality

- Batch history, source profile, row counts, errors/warnings, data completeness, checksum, user, timestamps, and rule-readiness impact.

### 7.10 Reports

- Saved report definitions are out of scope; users generate current filtered reports.
- Claim results, provider summary, network summary, rule coverage, data quality, and configuration snapshot reports.

### 7.11 Audit log

- Sign-ins, uploads, evaluation runs, exports, and configuration/rule-state changes.
- No investigation notes or case-disposition workflow.

## 8. Data intake design

### 8.1 Delivery format

Provide three downloadable template packs:

1. Abu Dhabi/Shafafiya-aligned Excel workbook.
2. Dubai/eClaimLink-aligned Excel workbook.
3. Canonical multi-CSV ZIP layout for technical users.

Every workbook includes a `README` sheet, field descriptions, required/optional markers, types, examples, allowed values, and jurisdiction mappings.

### 8.2 Core required datasets

| Dataset | Purpose |
|---|---|
| `claim_header` | Source IDs, payer/TPA, member, provider, encounter, dates, claim type, status, and header amounts |
| `claim_line` | Activity/product code, units, prices, share, clinician roles, modifiers/indicators, authorization, and service timestamps |
| `diagnosis` | Principal/secondary/admitting diagnoses, POA, code system/version |
| `encounter` | Type, setting, facility, location, admission/discharge, start/end |
| `member` | Token, DOB/age, sex where permissible, sponsor/employer token, death metadata if available |
| `provider` | Provider/facility token, regulator ID, type, specialty, ownership/group identifiers |
| `coverage_period` | Product/payer/network and effective eligibility dates |
| `provider_network` | Explicit network/group membership and effective dates |

### 8.3 Optional rule-enabling datasets

- Benefit rules and accumulators.
- Tariffs/contracts and package/DRG inclusions.
- Provider licence, privilege, exclusion, facility operations, staff/equipment capacity, and leave periods.
- Authorizations and authorization lines.
- Claim versions/resubmissions/cancellations.
- Remittance/payment/denial/adjustment records.
- Prescription, dispense, inventory, serial/batch, and drug equivalence data.
- Observations/results/order metadata.
- Referral and ordering relationships.
- Adjudicator/override events.
- Refunds, credits, coordination-of-benefits, and third-party-liability records.
- Policy/enrollment events and broker/employer links.
- Member confirmation/attendance/complaint metadata.

Rules depending on an absent optional dataset remain disabled for that evaluation and are disclosed in coverage reporting.

### 8.4 Temporal and identity rules

- Source records are append-only; corrections create versions rather than overwriting prior facts.
- All policy/reference joins are as-of the service time unless the rule explicitly requires submission time.
- Store `valid_from`, `valid_to`, `recorded_at`, `source`, and `version_id` for effective-dated records.
- Retain original local timestamp and normalize comparison timestamps consistently.
- Enforce a rolling five-year service-date window ending at the selected analysis date.
- Tokenized identifiers remain opaque strings; the POC does not attempt to re-identify members.
- Natural/source keys plus batch hashes make re-import idempotent.

## 9. Detection and decision design

### 9.1 Rule engine

Rules are configuration-led and versioned. Each rule record includes:

- rule/scenario ID and name;
- status and version;
- type and execution stage;
- population and required inputs;
- parameter values and units;
- exclusions and missing-data behavior;
- reason code and user-facing reason template;
- evidence fields;
- score/weight and allowed disposition;
- effective dates; and
- POC rationale/source label.

Rule-specific evaluators may be code-backed, but rule metadata and editable values must not be scattered through UI or business logic.

### 9.2 Execution pipeline

```text
Upload
  → schema and relationship validation
  → canonical normalization
  → immutable batch commit
  → claim lineage and episode construction
  → INGEST controls
  → PREPAY/PREPAY_ASYNC structured controls
  → historical DAILY/MONTHLY-style provider features
  → WEEKLY-style network features
  → signal correlation and priority
  → result coverage calculation
  → dashboards and exports
```

The catalogue's operational stages are preserved as metadata. For the POC, all applicable stages may run in one user-started batch while still recording their original stage.

### 9.3 Hybrid flagging practice

- Objective hard controls may flag directly and retain their policy disposition.
- Expert controls produce review-oriented flags and never overstate certainty.
- Statistical/network controls require minimum volume, adequate data, and an Admin-configurable threshold.
- Statistical/network controls never produce an automatic fraud conclusion, rejection, or sanction.
- Multiple signals based on the same fact are capped during scoring to avoid double counting.
- A primary reason is selected by disposition severity, evidence strength, exposure, then deterministic rule ID ordering.

### 9.4 Priority and exposure

Use the transparent catalogue formula as the initial priority framework, with normalized evidence strength, exposure, independent evidence domains, history, recency, data-quality penalty, and known exceptions. Store the component breakdown so a score is reproducible.

Exposure uses rule-specific logic:

- line edit: submitted payable less correctly repriced payable;
- duplicate: lower duplicated payable/paid amount after valid share;
- provider/network pattern: distinct associated amount, clearly labelled unless confirmed exposure is computable;
- no gross flagged amount is presented as savings.

### 9.5 Case correlation without case management

Correlate signals for readable presentation using deterministic fingerprints for claim lineage, episode, provider/scenario period, pharmacy/product, network snapshot, and distribution cohort. This is result grouping only; assignment, notes, investigation status, and final disposition are out of scope.

## 10. Initial configuration strategy

- Ship conservative synthetic/demo defaults for every editable `cfg.*` parameter needed by executable rules.
- Label every assumed value `POC default — not approved policy`.
- Store unit, allowed range, scope, rationale, and effective date.
- Default potentially high-noise statistical rules to `Shadow` while still showing their output in the POC.
- Default model rules to `Excluded` and document/text rules to `Deferred`.
- Default rules that lack required uploads to `Disabled — missing data` for that run.
- Prevent nonsensical values with type/range validation.
- Preserve prior values and result snapshots; no automatic historical reevaluation.
- Provide an explicit future “re-run with current configuration” extension, but do not include it in the first build.

## 11. Provider and network analytics

### 11.1 Provider baselines

Use the catalogue hierarchy: code/activity family → specialty → encounter/facility type → payment/contract family → geography → provider size band. Use robust percentiles or median/MAD, minimum denominators, and shrinkage for rates. Sparse groups back off to a broader peer and disclose the level used.

### 11.2 Change detection

For applicable non-model rules, compute stable weekly/monthly metrics and transparent CUSUM/EWMA-style changes after minimum history. Known contract, tariff, ownership, specialty, and feed changes may be configured as exclusions.

### 11.3 Network analytics

- Explicit `network_id` defines the evaluation boundary.
- Typed nodes: provider, clinician/prescriber, pharmacy, facility, member token, employer/broker where provided.
- Typed edges: referral, ordering, rendering, dispensing, shared identifier, member flow, and payment/override relation.
- Compute concentration, reciprocal flow, components, density, and centrality only where the corresponding rule requires them.
- Fuzzy shared-identity matches remain supporting evidence; they do not automatically merge entities or create hard findings.

## 12. Reporting specification

### 12.1 On-screen

- Dashboard summaries and trends.
- Filterable claim, provider, and network tables.
- Claim and entity drill-down.
- Rule coverage and data quality.
- Visible analysis window and configuration version.

### 12.2 CSV

Flat, machine-readable current-filter export with stable column names and one row per selected grain (claim, signal, provider, or network).

### 12.3 Excel

Formatted workbook with summary, filtered entities, triggered signals, rule coverage, data-quality notes, and configuration metadata on separate sheets.

### 12.4 PDF

- Executive batch summary.
- Detailed claim report.
- Provider profile report.
- Network profile report.
- Rule coverage/configuration appendix.

PDFs are generated locally and contain a footer with timestamp, analysis period, user role, data-coverage status, and decision-support disclaimer.

## 13. Design-system application

Implementation will consume the supplied Shahai tokens as the source of exact values and follow the authority order in the design-system repository.

### 13.1 Visual direction

- Dark-first, theme-ready product experience.
- Poppins for all working interface text; Radnika Next only for the Shahai wordmark.
- Balanced Midnight surface hierarchy and structural navy.
- Cream used sparingly for deliberate emphasis, never as a general highlight color.
- Controlled soft geometry using the approved radius scale.
- Semantic status colors from the provided dark/light tokens.
- Status always includes text and/or icon/shape; never color alone.

### 13.2 Product composition

- Dense analytical workspaces for claims, providers, rules, and imports.
- Clear statement/detail separation: decision first, evidence below.
- Dashboard area allocated by decision importance instead of a generic grid of oversized KPI cards.
- Flagship tables support search, filter, sort, pagination, pinned columns, expandable rows, row actions, loading, empty/error states, and comfortable/compact density.
- Numeric values use tabular alignment and right alignment; text stays left aligned.
- Charts use the approved data-visualization palette, direct labels where practical, restrained furniture, and accessible companion tables.
- Forms prioritize error prevention, attached validation, units, allowed ranges, and visible consequences.

### 13.3 Exact token usage

- Product typography and spacing come from `tokens/mediums/product.json`.
- Dark/light surfaces come from `tokens/semantic/dark.json` and `light.json`.
- Status colors come from `tokens/semantic/status.json`.
- Interaction values come from `tokens/semantic/interaction.json`.
- Radii come from `tokens/primitives/geometry.json`.
- Chart palettes and geometry come from `tokens/data-viz/`.

Where the design system marks a component detail unresolved, use the smallest conventional, accessible choice consistent with existing tokens and record it for design review. Do not invent a new Shahai motif or token family.

## 14. Proposed technical architecture

### 14.1 Stack

| Layer | Choice | Reason |
|---|---|---|
| Front end | React + TypeScript + Vite | Fast local UI, strong table/form ecosystem, straightforward token integration |
| API | Python + FastAPI | Clear typed endpoints and strong fit for data/rule processing |
| Data access | SQLAlchemy/SQLModel-style repository layer | Keeps persistence isolated and testable |
| Local database | SQLite | Embedded, free, portable, sufficient for thousands of claims and one concurrent user |
| Analytics | Python with Polars/Pandas-compatible processing plus NetworkX | Transparent grouped/statistical and graph calculations without model services |
| Excel | openpyxl/XlsxWriter-compatible generation | Local workbook validation and export |
| PDF | ReportLab-compatible generation | Local printable reports without a paid service |
| Testing | Pytest, Vitest/React Testing Library, Playwright | Rule, API, component, and end-to-end coverage |

Exact package selection will be locked during scaffolding based on available local runtime compatibility and licences.

### 14.2 Runtime topology

```text
Local browser
    ↕ HTTP on localhost only
React application
    ↕ JSON/file upload
FastAPI service
    ├─ import/validation service
    ├─ canonical repository
    ├─ rule engine and feature builders
    ├─ provider/network analytics
    ├─ export service
    └─ authentication/audit service
         ↕
    local SQLite database + local generated-report directory
```

The default binding is `127.0.0.1`, not the LAN. A PowerShell launcher starts the API/UI and opens the local URL. No cloud connection is required for normal operation.

### 14.3 Code organization

```text
Med Fraud/
├─ apps/
│  ├─ web/                 # React/TypeScript UI
│  └─ api/                 # FastAPI application
├─ packages/
│  ├─ design-tokens/       # Consumed snapshot/adaptor of Shahai tokens
│  ├─ rule-contracts/      # Rule schemas and shared reason/disposition contracts
│  └─ import-schemas/      # Canonical, Shafafiya, and eClaimLink mappings
├─ rules/
│  ├─ registry/            # Versioned rule metadata/configuration
│  ├─ evaluators/          # Deterministic/statistical/network implementations
│  └─ fixtures/            # Positive, negative, boundary, and exception cases
├─ data/
│  ├─ templates/           # User-downloadable workbook/CSV packs
│  ├─ demo/                # Synthetic UAE-style data
│  └─ local/               # Ignored runtime database/import/report files
├─ tests/
├─ docs/
├─ scripts/
└─ PRODUCT_PLAN.md
```

## 15. Local persistence, privacy, and recovery

- SQLite database stored under a local ignored runtime directory.
- Uploaded source file retained locally only if enabled; otherwise retain checksum, import metadata, and canonical rows.
- Tokenized IDs displayed in masked form where full visibility is unnecessary.
- Password hashes, not plaintext passwords.
- Audit records are append-only through the application.
- Exports warn that they contain sensitive operational data.
- A local backup action creates a timestamped copy of the database and configuration.
- A restore script validates schema/version before replacement and preserves the current database as a recovery copy.
- No telemetry, third-party analytics, external APIs, or paid services in the POC.

This is POC-grade local protection, not a claim of compliance certification. Processing identifiable health data or deploying over a network requires a separate security/privacy review.

## 16. API and module boundaries

Initial API groups:

- `/auth`: sign in, sign out, session, role.
- `/imports`: templates, upload, validate, commit, history, issues.
- `/evaluations`: start run, progress, summary, coverage.
- `/claims`: list, detail, lines, signals, lineage, episode.
- `/providers`: list, detail, metrics, signals, trends.
- `/networks`: list, detail, metrics, graph, signals.
- `/rules`: registry, versions, inputs, parameters, state.
- `/configuration`: effective-dated values and reference data.
- `/reports`: CSV, Excel, PDF generation.
- `/audit`: read-only audit log.
- `/health`: local readiness and version.

Long-running evaluation is handled as an in-process local job with persisted progress; an external queue is unnecessary at POC volume.

## 17. Testing strategy

### 17.1 Every executable rule

At minimum:

1. Positive fixture with exact reason code.
2. Clean negative fixture.
3. Threshold/date/amount/unit boundary fixture.
4. Null and missing-input behavior.
5. Two-version effective-date fixture.
6. Correction/cancellation/resubmission behavior where applicable.
7. Approved exception fixture.
8. Idempotent replay fixture.
9. Evidence snapshot with human-readable values and source versions.

The original catalogue includes tenant-isolation testing. The single-installation POC has no multi-tenant feature, so this is replaced with jurisdiction/profile and payer-data separation tests; tenant isolation returns in any multi-organization pilot.

### 17.2 Integration tests

- Shafafiya-aligned and eClaimLink-aligned files normalize correctly.
- Invalid rows never silently enter analysis.
- Duplicate import is detected.
- Five-year window excludes older claims and future-dated claims appropriately.
- Threshold update affects only later evaluations.
- Claim corrections supersede/correlate instead of double counting.
- Provider peer baseline is reproducible.
- Network amount counts each claim once.
- Role enforcement blocks Analyst configuration writes.
- CSV, Excel, and PDF exports match the active filters and totals.

### 17.3 UI and visual QA

- Keyboard navigation and visible focus.
- Text/status does not rely on color alone.
- Contrast against supplied tokens.
- Responsive behavior at practical laptop/desktop widths.
- Real-content stress tests: long IDs/reasons, missing values, large AED values, many statuses, and thousands of rows.
- Empty, loading, partial-data, success, warning, and error states.
- Dark default and light-theme readiness.

### 17.4 POC performance targets

- Smooth filtering/pagination for thousands of claims.
- A typical thousand-claim upload validates and evaluates without blocking the browser.
- Progress is visible by stage and completed rule count.
- Reopening completed results does not re-run evaluation.
- Exact performance thresholds will be baselined on the target laptop during implementation rather than invented in the plan.

## 18. Synthetic demo dataset

Provide at least three coherent five-year datasets:

1. **Clean baseline:** normal claims across both jurisdictions and all service domains.
2. **Suspicious patterns:** seeded duplicates, coverage failures, authorization issues, upcoding patterns, excessive utilization, refill overlap, provider capacity issues, referral concentration, reciprocal networks, payment/refund anomalies, and enrollment anomalies.
3. **Partial-data batch:** deliberately missing optional datasets to demonstrate honest coverage reporting.

Each seeded pattern has an expected-results manifest listing rule IDs, affected claims/entities, expected reason, and expected disposition. Tokenized identifiers and fictional providers/members are used throughout.

## 19. Delivery sequence and gates

### Phase 0 — Foundation and design translation

Deliver repository scaffold, local launcher, design-token adapter, database migrations, shared contracts, seeded users, app shell, and automated checks.

**Exit:** both roles can sign in; the Shahai shell renders from supplied tokens; local persistence and tests run from documented commands.

### Phase 1 — Canonical data and import experience

Deliver canonical schema, UAE import profiles, workbook/CSV templates, validation engine, import preview/history, five-year filtering, and demo-data generator.

**Exit:** clean and deliberately invalid files produce deterministic commits/errors; duplicate import is safe; rule-readiness coverage is visible.

### Phase 2 — Rule engine and claim-level hard/expert controls

Deliver rule registry/versioning, evidence contract, configuration UI, ingest/prepay structured controls, claim decision logic, claim tables/detail, and claim exports.

**Exit:** every included claim-level rule has fixtures; Admin changes are prospective; Analyst writes are denied; reasons/evidence reproduce exactly.

### Phase 3 — Historical and provider analytics

Deliver lineage, episode builder, daily/monthly-style aggregates, peer grouping, shrinkage/robust statistics, change detection, provider dashboard/detail, and provider exports.

**Exit:** provider results are explainable, reproducible, minimum-volume protected, and linked to contributing claims.

### Phase 4 — Network, pharmacy, policy, and payer analytics

Deliver typed graph features, explicit-network views, pharmacy/provider relationships, policy/employer signals, internal adjudication/payment controls, network visualization, and network exports.

**Exit:** seeded network patterns trigger expected controls; legitimate group relationships/exclusions suppress expected false positives; amounts are deduplicated.

### Phase 5 — Reporting, polish, and complete structured-rule coverage

Deliver overview dashboard, CSV/Excel/PDF report suite, remaining structured non-model controls, data-quality/coverage reports, audit log, backup/restore, error states, accessibility pass, and demo script.

**Exit:** all 149 structured non-model controls are implemented or explicitly marked data-disabled in a traceability matrix; no control is silently omitted.

### Phase 6 — Deferred document capability

Future scope: attachment intake, document metadata, OCR, English/Arabic extraction as required by actual deployment, source-span evidence, and the 12 deferred text/document controls. This phase requires its own validation corpus and human clinical/coding review.

Model controls remain excluded unless the user separately authorizes them.

## 20. Definition of done for the polished POC

The POC is complete when:

- both predefined roles authenticate and authorization is enforced server-side;
- Abu Dhabi-, Dubai-, and canonical-style sample files import successfully;
- all 149 structured non-model controls exist in the rule traceability matrix and executable code path;
- each executable rule has required automated fixtures and human-readable evidence;
- controls lacking optional data visibly report `Disabled — missing data`;
- all three model controls visibly report `Excluded — model rule`;
- all 12 text/document controls visibly report `Deferred`;
- new batches use five years of accumulated history up to the chosen analysis date;
- claim results show decision plus primary reason and full drill-down;
- provider and network views link signals to contributing claims and evidence;
- Admin can change valid thresholds/weights, Analyst cannot, and changes are prospective;
- dashboard, CSV, Excel, and PDF outputs reconcile to the same filtered data;
- synthetic data demonstrates clean, suspicious, and partial-coverage behavior;
- the UI passes the Shahai design-system, accessibility, empty/error/loading, and real-content checks;
- the app runs locally without an external database, paid service, or required internet connection; and
- setup, demo, backup, restore, test, and troubleshooting instructions are documented.

## 21. Main risks and mitigations

| Risk | Mitigation |
|---|---|
| Catalogue breadth creates superficial implementations | Rule-by-rule traceability, fixtures, evidence contracts, and phased exit gates |
| Missing reference datasets produce misleading passes | Per-run readiness and partial-coverage labeling; disable rather than pass |
| Assumed thresholds are mistaken for UAE policy | Prominent POC labels, source/rationale fields, versioning, and Admin controls |
| Statistical false positives | Minimum volume, shrinkage, peer backoff, shadow status, explainable units |
| Multiple signals inflate risk/value | Evidence-domain caps and distinct-claim exposure calculations |
| Dubai/Abu Dhabi semantics are conflated | Separate input mappings and retained source vocabulary |
| Local files are lost | Backup/restore tools and recoverable database replacement |
| POC language implies confirmed fraud | Controlled outcome vocabulary and disclaimers throughout UI/exports |
| Configuration change breaks reproducibility | Immutable result snapshots and effective-dated prospective versions |
| Dense UI becomes unreadable | Shahai density modes, scan anchors, hierarchy, pinned columns, real-content QA |

## 22. Future extensions intentionally left open

- Native Shafafiya/eClaimLink XML and web-service adapters.
- Multi-user concurrent deployment and enterprise identity integration.
- Full investigation/case-management workflow.
- Document/OCR analysis and the deferred text controls.
- Model-classified controls and supervised prioritization.
- Multi-tenant isolation.
- Scheduled daily/weekly/monthly execution services.
- Production security, privacy, retention, compliance, monitoring, and disaster recovery.
- Regulator/payer-approved UAE policy packs maintained by clinical/coding owners.

