# Model-excluded and text-deferred boundary audit

## Sources and authority

- `PRODUCT_PLAN.md` is the approved POC scope and therefore controls what may execute now.
- `model-classified-rules-detailed-guide.md` is a future implementation guide for the three `M` controls. It does not authorize their inclusion in the POC.
- The guide remains useful as a set of future gates and as evidence that an `M` result is review prioritization/research, not a fraud finding or autonomous payment decision.

## Reconciled rule accounting

The counts reconcile exactly:

| Catalogue population | Count | POC treatment |
|---|---:|---|
| All atomic controls | 164 | Always present in the read-only registry/traceability inventory |
| Any type containing `M` | 3 | Catalogued, but `Excluded — model rule`; never executable |
| Non-model controls | 161 | Complete-roadmap population |
| Non-model controls requiring narrative/document interpretation | 12 | Catalogued, but `Deferred`; never executable in the structured-data POC |
| Structured non-model controls | 149 | Executable candidates for the first POC; may be disabled for a run when inputs are missing |

The type-membership boundary is inclusive: **any** type string containing `M` is excluded, even if it also contains a currently supported type. Consequently `CLN-01-R02 (S/M)` is excluded in full; its `S` component does not make it partially executable.

The twelve deferred controls are:

`ENT-06-R02`, `PAY-05-R02`, `PAY-09-R01`, `CLN-01-R03`, `CLN-08-R03`, `DOC-01-R02`, `DOC-01-R03`, `DOC-01-R04`, `DOC-02-R01`, `DOC-02-R02`, `DOC-02-R03`, and `DOC-02-R04`.

`DOC-01-R01` is not in that set. It, and another genuinely structured presence/metadata control, may execute only when supplied document metadata is sufficient to establish the required artifact, type, timing/SLA, and linkage without reading or interpreting content.

## Exact control boundary

### Model-excluded controls

| Rule | Future behavior described by the model guide | Required POC behavior |
|---|---|---|
| `CLN-01-R02` | Encounter/code-family ordinal expected-level probabilities and residual; coding-review selection | Inventory only; no prediction, residual, tail probability, exposure, alert, or seeded expected result |
| `ANL-01-R03` | Provider/payer/month multivariate anomaly model, initially Isolation Forest, validated for lift beyond `ANL-01-R01/R02` | Inventory only; no model fit/score, anomaly percentile, model-only case, or model-derived priority |
| `ANL-01-R04` | Offline/quarterly cluster discovery producing a rule-development candidate | Inventory only; no clustering workflow, cluster membership, research candidate, or production signal |

No excluded rule may:

- be instantiated in the evaluator registry;
- enter a run queue or completed-rule progress denominator;
- emit a claim/entity/network signal;
- affect `Flagged`, primary reason, disposition, exposure, priority, correlation, dashboards, or exports;
- count as passed, failed, not-applicable, or disabled-missing-data;
- be enabled or configured by Admin; or
- be presented as `Shadow` (shadow is still execution).

The registry should expose these rules read-only with the exact status `Excluded — model rule` and a stable exclusion reason. The API must reject activation, threshold changes, evaluator dispatch, and manual scoring for them server-side. Hiding model-management UI is necessary but not sufficient.

### Text/document-deferred controls

The twelve deferred controls remain visible with the exact status `Deferred`. They must not be downgraded to `Disabled — missing data`: missing data is a per-run condition for an otherwise executable control, whereas deferral is a product-scope decision.

No deferred rule may run merely because an upload happens to include a note, narrative column, image, PDF, observation text, or document hash. The first POC has no validated attachment intake, OCR, English/Arabic extraction, semantic similarity, source-span evidence, or document-version interpretation path. Supplying raw content cannot silently expand scope.

For structured document-presence checks, absence may be evaluated only when metadata proves that the relevant artifact was expected, the allowed arrival latency/SLA has elapsed, and the claim/artifact linkage is reliable. An absent optional upload cannot be treated as an absent clinical document; otherwise the result is `Disabled — missing dataset`/partial coverage, not a trigger.

## Findings and conflicts

1. **The numeric scope is consistent, but the phrase “all non-model controls are in scope” is easy to misread.** It means 161 controls in the complete roadmap, not 161 executable controls in the first release. The first executable population is 149. Acceptance tests and UI copy should use those qualifiers.

2. **Status vocabulary is slightly inconsistent.** Section 3.1 mentions `Disabled — deferred documents`, while sections 7, 10, 20 and the delivery plan use `Deferred`/`Deferred documents`. Canonicalize the registry state to `Deferred`; reserve `Disabled — missing dataset` for run-specific missing inputs. This preserves the definition-of-done wording and prevents a scope choice from looking like a recoverable upload issue.

3. **The plan's generic Admin powers must be narrowed by eligibility.** Admin may enable/disable and configure only eligible executable controls. Admin cannot override `Excluded — model rule` or `Deferred` in the POC. This follows the plan's “no model-management screen” decision and Phase 6 gate.

4. **`Shadow` is not a safe substitute for exclusion.** The plan defaults noisy statistical rules to Shadow, but the model guide also describes Shadow as an actual prospective deployment state. All three `M` rules must stay Excluded, not Shadow. Only executable non-model statistical/network rules may be Shadow.

5. **Shared analytical foundations are allowed; model behavior is not.** Robust peer baselines, median/MAD residuals, minimum-volume handling, shrinkage/backoff, and transparent CUSUM/EWMA change detection are required for included non-model controls such as `ANL-01-R01/R02`. Their presence must not dispatch `ANL-01-R03`, fit an Isolation Forest/LOF, or imply that a model was implemented.

6. **The synthetic “upcoding patterns” requirement does not authorize `CLN-01-R02`.** Seeded upcoding can exercise included hard/expert/statistical controls (for example the simpler provider-level baseline), but the expected-results manifest must never list an `Excluded` rule as triggered.

7. **Model-guide output/disposition contracts are dormant.** Fields such as `model_version`, `raw_score`, calibrated model priority, model confidence, `SIU_LEAD` from R03, and `RULE_DEVELOPMENT_CANDIDATE` from R04 are future contracts. They must not be fabricated for inventory rows or mixed into the current signal contract.

8. **Future model requirements are stricter than the general POC scorer and must not be approximated now.** Transparent catalogue priority scoring is not a replacement for CLN-01-R02 probabilities, R03 anomaly scoring, or R04 clustering. Conversely, a high non-model composite score must not be labelled a model score.

9. **R04 is not a production detection rule even in a future model phase.** Its eventual output is an analyst-reviewed typology/rule proposal. The proposed explicit rule must be independently backtested and shadowed; cluster membership itself never becomes adverse evidence.

10. **Text deferral and model exclusion intersect at CLN-01 but remain separate.** `CLN-01-R02` uses only scoring-time structured inputs in its future design and is excluded because it is model-classified. `CLN-01-R03` depends on validated document extraction and is deferred because it is text-classified. Neither can be used as a fallback for the other.

## Implementation contracts

### Registry and persistence

Represent stable catalogue scope separately from mutable operational state. A safe shape is:

```text
scope_state: EXECUTABLE | EXCLUDED_MODEL | DEFERRED_DOCUMENT
operational_state: ACTIVE | SHADOW | DISABLED
readiness_state (per run): READY | DISABLED_MISSING_DATASET | NOT_APPLICABLE
```

Only `EXECUTABLE` rows may have a mutable operational state or enter readiness evaluation. Persist all 164 inventory rows, but create evaluation snapshots only for applicable executable rules. If the existing schema uses one status column, enforce an equivalent transition matrix and never allow transitions out of excluded/deferred states.

Record immutable catalogue metadata for excluded/deferred rows: rule ID, name, declared types, original stage, population, required inputs, scope reason, and source version. Do not require demo `cfg.*` defaults for them; the configuration-default requirement applies to executable rules.

### Evaluation and coverage

Use two reconciled views:

- **Catalogue coverage:** 164 total = 149 executable candidates + 12 deferred + 3 excluded.
- **Run coverage:** only applicable members of the 149 executable candidates are passed, triggered, not-applicable, or disabled-missing-dataset.

Excluded and deferred controls should be reported as separate fixed categories, not folded into run coverage. They do not make a claim's data coverage `Partial`; missing required data for an applicable executable rule does. This avoids every POC run appearing partial solely because deliberate future scope exists.

For `No flag detected`, disclose run coverage and disabled executable controls. Never infer a clean result from missing inputs. Excluded/deferred rules should remain visible in full rule coverage/drill-down as not executed for product-scope reasons, without implying their hypothetical outcome.

### Scoring and correlation

Filter to executable, actually triggered signals before priority computation and fingerprint correlation. Apply the plan's evidence-domain caps only to those signals. Inventory rows, excluded/deferred states, and missing-data records carry zero score and zero exposure and cannot win primary-reason ordering.

For included statistical/network controls, retain minimum-volume, data-quality, peer-backoff, explainable-business-unit, non-automatic-disposition, and distinct-associated-value safeguards. Those safeguards echo the model guide but do not transform the controls into models.

### API and UI

- `/rules` returns all 164 rows and exposes scope state distinctly from run readiness.
- Mutation endpoints validate `scope_state == EXECUTABLE`; return a deterministic conflict/validation error for the 15 non-executable rows.
- `/evaluations` validates the selected rule set before queueing and rejects any excluded/deferred ID rather than silently skipping it.
- Progress counts only dispatched executable rules; a separate catalogue summary shows excluded/deferred totals.
- Rule pages show explanatory, non-interactive status and source rationale for excluded/deferred controls; no parameter editor, enable toggle, run action, model score, or document-analysis affordance.
- Claims/providers/networks and every export use the same category/count definitions.

### Architecture/package boundary

The planned Python analytics layer may implement grouped statistics and NetworkX features for the 149 controls. The POC should not add model training/scoring modules, model artifact storage, feature-store tables, training jobs, drift jobs, clustering workflows, model dependencies solely for Isolation Forest/LOF/ordinal models, or model-management endpoints.

Design future seams without implementing future capability: keep rule contracts extensible, preserve event-time/effective-date correctness, and version feature definitions used by current statistical controls. These foundations support a separately authorized model phase without weakening the current exclusion.

The POC also should not add OCR/NLP/document-content dependencies or persist interpreted document facts. It may retain structured document metadata needed by executable presence checks. Phase 6 must introduce its own validated corpus, extraction provenance/source spans, bilingual validation where required, and qualified clinical/coding review before any deferred control changes state.

## Required tests and acceptance assertions

1. Inventory test: exactly 164 unique rules, with exactly 149 `EXECUTABLE`, 12 `DEFERRED_DOCUMENT`, and 3 `EXCLUDED_MODEL` IDs matching the approved lists.
2. Classification test: a mixed type containing `M` (notably `S/M`) resolves to `EXCLUDED_MODEL` before evaluator selection.
3. Dispatch test: no evaluator exists or is invoked for any of the 15 non-executable rules.
4. Authorization test: both Analyst and Admin are blocked server-side from changing scope state/configuration or requesting execution for those 15 rules.
5. Coverage test: excluded/deferred totals are reported separately and do not cause `Partial`; an absent required dataset for an applicable executable rule does cause `Partial`.
6. Missing-document test: absence of an upload does not trigger `DOC-01-R01`; sufficient metadata plus elapsed SLA may trigger it according to its structured rule contract.
7. Raw-content test: adding narrative/PDF/image fields does not activate or evaluate a deferred control.
8. Scoring test: excluded, deferred, missing-data, and not-applicable records cannot affect priority, primary reason, disposition, associated amount, or correlation.
9. Export reconciliation test: on-screen, CSV, Excel, and PDF counts use the same 149/12/3 taxonomy and the same per-run readiness totals.
10. Synthetic-manifest test: no expected trigger references any excluded/deferred ID.
11. Dependency/static test: the POC contains no model fitting/scoring path or OCR/NLP document-content path masquerading behind a supported rule.

## Future authorization gate

If model controls are later authorized, authorization should be explicit by rule and phase; it should not be achieved by an Admin toggle. The model guide then becomes binding: time-based and provider-held-out validation where applicable, scoring-time feature availability and versioning, simple baseline first, prospective incremental value, explanations in business units, data-quality/known-change suppressions, permitted review-only dispositions, drift/performance monitoring, reproducibility, kill switch, and rollback. No `M` control is approved for autonomous rejection; R04 remains research-only.

If document controls are later authorized, that is a separate gate. Model authorization does not authorize OCR/text controls, and document authorization does not authorize models.
