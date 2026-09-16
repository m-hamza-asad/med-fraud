# UAE Medical Claims Fraud, Waste and Payment-Integrity Developer Specification

**Version:** 3.0  
**Prepared:** 29 August 2026  
**Status:** Build specification  
**Audience:** Product, claims operations, clinical/coding policy, data engineering, analytics, ML engineering, QA and SIU  
**Supersedes:** `uae-medical-claims-fwa-scenario-catalog.md` for implementation purposes

---

## 1. Executive verdict

The scenario-led catalog is directionally sound, but it was not yet sufficient to hand directly to a development team. It explained *what* to detect without consistently defining atomic controls, execution stage, configuration, exclusions, evidence contracts or testable outcomes.

This specification corrects that. It contains **39 scenarios and 164 atomic controls**. The controls are intentionally separated from algorithms: a scenario may have a hard edit, an expert rule, a provider-level statistic and a document model, but users receive one correlated case.

### 1.1 Coverage audit result

The earlier 31-scenario catalog covered the core provider, member, coding, pharmacy, documentation and network schemes. Eight areas needed explicit treatment and are now added:

| Added scenario | Why it matters |
|---|---|
| **ENT-06 Telehealth encounter and downstream-order integrity** | Remote-consultation schemes can generate concentrated laboratory, device or pharmacy orders without a meaningful clinical relationship. |
| **PAY-09 Disguised non-covered service or product** | UAE guidance expressly identifies misstatement of symptoms/services and billing covered codes while supplying uncovered or non-medical items. |
| **PAY-10 Coordination-of-benefits and third-party-liability overpayment** | Duplicate recovery across payers and failure to apply motor, work-injury or other liable-party rules are distinct from a same-payer duplicate. |
| **PAY-11 Internal adjudication, override and payment manipulation** | UAE's fraud definition includes payer/TPA employees and other parties; override abuse cannot be detected solely from provider claims. |
| **PAY-12 Reversal, refund, credit-balance and remittance leakage** | Payment integrity continues after initial adjudication; cancelled claims, duplicate remittances and unapplied credits create recoverable loss. |
| **CLN-08 Laboratory, pathology and genetic-testing integrity** | No-order, panel inflation, pass-through billing, absent results and high-complexity test schemes deserve explicit, service-specific controls. |
| **PHR-05 Equipment, implant, consumable and supply integrity** | Billing new/high-grade equipment while supplying used, cheaper or no equipment is explicitly recognized in UAE fraud guidance. |
| **POL-01 Enrollment, employer-group and policy manipulation** | False eligibility, retroactive member changes and suspicious early-tenure utilization are policy/distribution risks, not ordinary claim anomalies. |

No static catalog can be “complete forever.” Tariffs, coding standards, benefit designs and fraud methods change. Completeness therefore requires a quarterly typology review and a mechanism for adding rules without code deployment.

---

## 2. Product behavior and safety boundary

### 2.1 A signal is not a fraud finding

Claims data can establish non-payability, inconsistency or abnormality. It usually cannot establish intent. Each control must therefore declare one of these outcomes:

| Outcome | Use |
|---|---|
| `RETURN` | Transaction cannot be processed because required data or format is invalid. |
| `REJECT` | An objective, effective-dated coverage/payment condition fails and policy authorizes rejection. |
| `REPRICE` | Correct payable amount is computable under tariff/contract. |
| `PREPAY_PEND` | Human coding, clinical or payment review is required before payment. |
| `POSTPAY_AUDIT` | Pattern requires records, sampling or recovery review after payment. |
| `SIU_LEAD` | Coordinated or intentional conduct is plausible and should be assessed by SIU. |
| `PROVIDER_EDUCATION` | Pattern is more consistent with error or poor billing practice. |
| `MONITOR_ONLY` | Evidence is insufficient for operational intervention. |

An anomaly score, graph metric or NLP result must never be the sole basis for `REJECT`.

### 2.2 Control types

- **H — Hard:** exact validation against transaction, benefit, tariff, contract, licence or other authoritative rule.
- **E — Expert:** deterministic execution against a maintained clinical/coding policy containing expert judgment.
- **S — Statistical:** peer-relative or self-history deviation with minimum-volume and uncertainty controls.
- **N — Network:** relationship concentration, reciprocity, shared identity or community pattern.
- **T — Text/document:** structured facts extracted from notes, reports or attachments.
- **M — Model:** trained unsupervised or supervised score.

### 2.3 Execution stages

| Stage | Maximum expected latency | Typical controls |
|---|---:|---|
| `INGEST` | <1 second/file validation batch | Required fields, transaction integrity, exact duplicates |
| `PREPAY_SYNC` | <500 ms/claim after features are available | Eligibility, tariff, code, authorization and patient-share edits |
| `PREPAY_ASYNC` | Minutes | document checks, near duplicates, episode joins, clinical review routing |
| `POSTPAY_DAILY` | Daily | provider statistics, resubmission behavior, refunds and capacity |
| `NETWORK_WEEKLY` | Weekly | referral/collusion graph and broker/employer analysis |
| `MODEL_MONTHLY` | Monthly or when drift triggers | peer baselines, anomaly models, calibration and validation |

---

## 3. Canonical data contracts

### 3.1 Minimum tables

| Table | Primary key | Required content |
|---|---|---|
| `member` | `member_sk` | protected identity linkage, DOB, sex, death status/source, sponsor/employer |
| `coverage_period` | `coverage_id` | member, product, payer, effective dates, network, status |
| `benefit_rule_version` | composite | product, service family, coverage, limits, patient share, exceptions, effective dates |
| `provider` | `provider_sk` | regulator IDs, type, specialty, facility, ownership and administrative identifiers |
| `provider_status_period` | composite | licence, privilege, network and exclusion status by effective date |
| `claim_header` | `claim_sk` | source IDs, sender/receiver, payer/TPA, encounter, amounts and submission/settlement data |
| `claim_line` | `line_sk` | Activity type/code, units, amounts, clinician roles, indicator/modifier and authorization ID |
| `diagnosis` | composite | claim/encounter, code/version, type, principal/secondary, POA where applicable |
| `encounter` | `encounter_sk` | type, facility, start/end, admission/discharge and location |
| `observation` | `observation_sk` | parent Activity, type, result/value, attachment and event time |
| `authorization` | `authorization_sk` | request/response IDs, status, validity, provider/facility, approved amounts/units |
| `authorization_line` | `authorization_line_sk` | approved Activity, quantity/value, conditions and denial code |
| `claim_version` | composite | original/resubmission/correction relationship and field-level version history |
| `remittance` | `remittance_sk` | claim/line decisions, denial/adjustment, payment, reference and settlement dates |
| `prescription_dispense` | `rx_sk` | order, authorization, prescribed/approved/billed/dispensed product and quantity |
| `policy_event` | `policy_event_sk` | enrollment/add/delete/correction event, actor and timestamp |
| `review_outcome` | `review_id` | disposition, validated category, confirmed amount, rationale and appeal result |

For Abu Dhabi integrations, preserve Shafafiya transaction semantics including Claim, Encounter, Activity, Observation, PatientShare, Prior Request/Authorization, Remittance Advice, denial codes and Resubmission type. For Dubai, build a separate eClaimLink adapter against its current standard data sets, code lists, clinician/facility/payer files and denial codes; do not assume field-level identity with Shafafiya. Store the original transaction payload or immutable hash plus parsed version and retain the source-system vocabulary alongside canonical values.

### 3.2 Required temporal behavior

All joins to coverage, contract, tariff, code, licence, network, edit or model data must be **as-of joins** using service time unless the policy explicitly uses submission time. Corrections never overwrite the prior version. Store `valid_from`, `valid_to`, `recorded_at`, `source` and `version_id`.

### 3.3 Atomic control definition

Rules should be configuration, not hard-coded conditionals. Recommended contract:

```yaml
rule_id: PAY-04-R01
scenario_id: PAY-04
name: Missing mandatory authorization
version: 1.0.0
status: shadow | active | retired
type: H
stage: PREPAY_SYNC
population: claim_line where benefit_rule.authorization_required = true
inputs: [line.service_date, line.activity_code, line.provider_id, line.authorization_id]
expression: authorization_id is null and no policy_exception exists
parameters: {grace_minutes: 0}
exclusions: [emergency_exception, deemed_approval, regulator_exception]
grouping_key: [payer_id, member_sk, episode_id, scenario_id]
score: 100
disposition: PREPAY_PEND
reason_code: AUTH_MISSING
evidence_fields: [activity_code, service_date, authorization_rule_version]
owner: claims_policy
effective_from: 2026-01-01
```

Expressions may compile to SQL, Spark or a streaming rule engine, but one canonical evaluation library must define null, time-zone, rounding, currency, lookback and as-of behavior. UAE timestamps should be normalized to UTC and retained with original `Asia/Dubai` representation.

### 3.4 Signal and case contract

Every result includes `signal_id`, `rule_id`, `rule_version`, `scenario_id`, subject, event/detection time, score, confidence, exposure AED, evidence JSON, reference versions, disposition and related signals. Case correlation happens after rule execution. It must cap correlated evidence so three versions of the same fact do not triple the risk score.

### 3.5 Parameter governance

Parameters live in effective-dated tables scoped by regulator, payer, product, contract, provider type and code family. Every threshold records owner, rationale, source, approval, expected alert volume and expiry/review date. Values shown below as `cfg.*` are configuration—not universal medical facts.

---

## 4. Atomic rule catalog

**Notation:** `same_episode()` and `related_claims()` use the episode and lineage services; `peer_pct()` returns a shrunk percentile with minimum volume; `expected_*()` resolves the effective benefit, tariff or clinical-policy version. Tables use compact stage labels: `PREPAY` = `PREPAY_SYNC`, `ASYNC` = `PREPAY_ASYNC`, `DAILY` = `POSTPAY_DAILY`, `WEEKLY` = `NETWORK_WEEKLY`, and `MONTHLY`/`QUARTERLY` are scheduled analytical jobs. Unless a row says otherwise, results correlate at scenario/entity level before reaching users.

### ENT-01 — Coverage, benefit and network eligibility · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| ENT-01-R01 Coverage inactive | H / PREPAY | `service_time NOT BETWEEN coverage.valid_from AND coverage.valid_to` | Grace/newborn/emergency and retroactive-update policy | Reject/pend; show coverage interval |
| ENT-01-R02 Benefit not covered | H / PREPAY | `expected_benefit(activity_family, product).covered = false` | Mandatory benefits, approved exception, medical-tourism/self-pay route | Reject with benefit version |
| ENT-01-R03 Benefit limit exceeded | H / PREPAY | `paid_or_authorized_ytd + requested_payable > benefit_limit` | Reset period, family/member basis, reversals, pending authorizations | Reprice or pend excess only |
| ENT-01-R04 Network/referral violation | H / PREPAY | Provider/route outside effective network or required referral missing | Emergency, access-gap and regulator exceptions | Reject/pend with failed route |

### ENT-02 — Member identity misuse, card sharing and post-mortem billing · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| ENT-02-R01 Authoritative identity conflict | H / INGEST | Protected national-ID token maps to different enrolled member or DOB/sex conflicts with authoritative record | Placeholder IDs, newborns, corrected identity; names alone prohibited | Pend for identity resolution |
| ENT-02-R02 Post-mortem service | H / PREPAY | `service_start > confirmed_death_date + cfg.reporting_tolerance` | Death-source confidence; administrative claims after service permitted | Pend/reject with source confidence |
| ENT-02-R03 Member impossible presence | S / PREPAY_ASYNC | Same member has overlapping encounters or travel speed above `cfg.max_speed` | Inpatient ancillary lines, telehealth, claim date without time | Member lead with encounter pairs |
| ENT-02-R04 Card-sharing utilization pattern | S / DAILY | Incompatible concurrent geography/provider clusters or abrupt demographic-inconsistent service pattern | Chronic/rare disease pathways; require minimum independent evidence | SIU lead, never auto-reject |

### ENT-03 — Provider/facility licence, exclusion and privilege · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| ENT-03-R01 Inactive/expired licence | H / PREPAY | Rendering, ordering, dispensing or facility licence not active at service time | Role-specific licence requirement and approved grace | Reject/pend with licence period |
| ENT-03-R02 Excluded/watch-listed entity | H / PREPAY | Effective match on regulator or approved internal exclusion list | Exact ID match required for reject; fuzzy match only pends | Reject or SIU lead |
| ENT-03-R03 Hard privilege violation | H / PREPAY | Activity outside regulator/facility privilege explicitly marked prohibited | Effective privilege source and exception | Reject/pend |
| ENT-03-R04 Soft specialty mismatch | E / PREPAY_ASYNC | Activity outside curated specialty map but not legally prohibited | `cfg.specialty_map`, cross-specialty privileges, sample-based validation | Coding review, not reject |
| ENT-03-R05 Dormant/new/non-operational provider burst | S / DAILY | New/reactivated provider immediately exceeds specialty volume/value percentile or lacks expected operating footprint | Credentialing date, acquisition/merger and new contract | SIU/provider-enrollment lead |

### ENT-04 — Rendering identity and clinician activity integrity · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| ENT-04-R01 Missing/invalid rendering clinician | H / PREPAY | Service family requires rendering clinician and ID is null, facility-only, or invalid | Role requirement by activity/encounter | Return/pend |
| ENT-04-R02 Billing-rendering role conflict | H/E / PREPAY | Billing/rendering/ordering/supervising combination violates explicit role rule | Incident-to/team care and supervision policy | Pend with role conflict |
| ENT-04-R03 Concurrent clinician services | S / DAILY | Clinician has overlapping time-dependent services beyond `cfg.max_concurrency` | Team procedures, anesthesia concurrency, date-only records | Provider case with timeline |
| ENT-04-R04 Geographic or leave impossibility | S / DAILY | Clinician claims during confirmed leave/out-of-country period or impossible facility travel | Timestamp/source reliability | SIU lead if repeated |

### ENT-05 — Encounter type/place-of-service misrepresentation · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| ENT-05-R01 Facility-type incompatibility | H / PREPAY | Claimed encounter/activity requires a facility type not matching licence | Mobile/home/telehealth exceptions | Reject/pend |
| ENT-05-R02 Admission evidence conflict | H/E / PREPAY_ASYNC | Inpatient/ICU/day-case billing lacks admission, bed, discharge or required Observation trail | Data latency and transferred cases | Pend for records |
| ENT-05-R03 Related-claim setting conflict | E / DAILY | Professional and facility claims for same episode disagree on setting | Cross-facility transfer, independent practitioner | Correlated episode case |
| ENT-05-R04 Setting-shift anomaly | S / MONTHLY | Provider's better-paid setting share rises beyond changepoint and peer threshold | Contract/facility change segmentation | Postpay audit |

### ENT-06 — Telehealth encounter and downstream-order integrity · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| ENT-06-R01 Telehealth eligibility/setting failure | H / PREPAY | Telehealth code billed for ineligible service, member geography or provider privilege | Regulator/product telehealth rules | Reject/pend |
| ENT-06-R02 No meaningful clinical interaction | E/T / ASYNC | Remote order has no qualifying encounter/note or interaction duration below policy minimum | Asynchronous-care rules and emergencies | Clinical review |
| ENT-06-R03 Downstream referral concentration | S/N / WEEKLY | Telehealth provider sends share above peer threshold to one lab/pharmacy/device supplier | Corporate ownership and narrow network | Network lead |
| ENT-06-R04 Remote-order conversion spike | S / DAILY | Downstream high-cost test/drug/device conversion materially exceeds adjusted peers | Specialty, diagnosis and campaign/new-service change | Postpay/SIU lead |

### PAY-01 — Exact, near and cross-submission duplicate billing · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PAY-01-R01 Exact line duplicate | H / PREPAY | Same payer/member/provider/code/date/units/amount and no valid repeat indicator in active lineage | Replacement/cancelled line, bilateral/repeat rule | Reject later line |
| PAY-01-R02 Near duplicate | H / ASYNC | Same clinical service with changed claim ID, amount, units or code equivalent within `cfg.window` | Staged/repeat services and code-equivalence map | Pend with matched line |
| PAY-01-R03 Split-claim duplicate | H / DAILY | Component/identical service appears across claim headers for same episode | Facility/professional legitimate split | Reprice/pend episode |
| PAY-01-R04 Cross-payer duplicate | H/S / DAILY | Privacy-preserving member/service match paid by multiple payers | Only authorized data-sharing/COB data; payment status required | Recovery/coordination case |

### PAY-02 — Unbundling and inclusive/package/DRG leakage · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PAY-02-R01 Same-claim component edit | H / PREPAY | Parent and separately payable component match effective bundling edit | Permitted indicator and edit version | Reprice/reject component |
| PAY-02-R02 Cross-claim/cross-provider component | H/E / DAILY | Included component billed on related claim in global/episode window | Contractual professional/facility split | Episode reprice/pend |
| PAY-02-R03 Package completeness/zero-price lines | H / PREPAY | Required package activities absent, or included activity has non-zero charge | Documented medical omission and local claiming rule | Return/reprice |
| PAY-02-R04 DRG/inclusive leakage | H / DAILY | FFS line separately paid although included in DRG/package | Effective inclusions/exclusions, carve-outs | Recovery candidate |
| PAY-02-R05 Novel unbundling pattern | S / MONTHLY | Provider has abnormal profitable component co-occurrence not in known edit table | Minimum volume and peer adjustment | Policy-review candidate, not denial |

### PAY-03 — Code validity, demographics, units and time billing · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PAY-03-R01 Invalid/effective-date code | H / INGEST | Code absent from declared code system/version or inactive at service date | Approved unlisted-code pathway and required Observation | Return |
| PAY-03-R02 Hard demographic impossibility | H / PREPAY | Explicit age/sex restriction fails | Gender/clinical exceptions approved by policy | Reject/pend |
| PAY-03-R03 Unit maximum | H/E / PREPAY | Daily/episode units exceed administrative or clinical maximum | Repeat/laterality, dose, inpatient rules | Reprice or clinical pend |
| PAY-03-R04 Time-unit inconsistency | H/E / PREPAY | Time-derived units do not match start/end time or overlap impossible services | Rounding policy, anesthesia concurrency | Reprice/pend |

### PAY-04 — Prior-authorization compliance and scope · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PAY-04-R01 Missing required authorization | H / PREPAY | Activity requires authorization and no valid link exists | Emergency, deemed approval, response-time exception | Pend/reject |
| PAY-04-R02 Invalid timing/status | H / PREPAY | Service outside authorization validity or authorization denied/cancelled | Approved extension and urgent retrospective route | Pend/reject |
| PAY-04-R03 Code/provider/facility scope mismatch | H / PREPAY | Claim dimension not equal/equivalent to approved dimension | Equivalent-code map and approved transfer | Pend |
| PAY-04-R04 Quantity/value exhaustion | H / PREPAY | Cumulative claimed/paid plus current exceeds approved units/value | Cancelled/reversed claims and partial fills | Reprice/pend excess |
| PAY-04-R05 Authorization reuse | H/S / DAILY | Same authorization consumed by unrelated members/episodes/providers or after exhaustion | Family/shared authorization only if policy permits | SIU/prepay lead |

### PAY-05 — Modifier, indicator and edit-bypass abuse · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PAY-05-R01 Prohibited code-indicator pair | H / PREPAY | Pair absent/prohibited in effective policy table | Local indicator rules; never import foreign rules blindly | Return/reject |
| PAY-05-R02 Required support absent | E/T / ASYNC | Enabling indicator requires Observation/report/narrative and artifact is missing | Document arrival latency | Pend |
| PAY-05-R03 Provider use-rate outlier | S / MONTHLY | Indicator rate exceeds shrunk specialty peer percentile | Minimum denominator, facility/payment model | Postpay audit |
| PAY-05-R04 Post-edit migration | S / MONTHLY | Usage spikes after new edit and disproportionately converts denials to payment | Rule launch and provider education periods | Payment-integrity case |

### PAY-06 — Tariff, contract and billed-amount manipulation · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PAY-06-R01 Tariff/contract price variance | H / PREPAY | Submitted price basis differs from effective allowed price outside rounding tolerance | Negotiated carve-outs, VAT and currency policy | Reprice |
| PAY-06-R02 Gross/net/share arithmetic failure | H / INGEST | Amount relationships violate transaction or contract equation | Approved adjustments and other-insurer amounts | Return |
| PAY-06-R03 Billed amount peer outlier | S / DAILY | Code-level amount above contract-adjusted peer threshold | Case mix, units, implant carve-out | Pend only with material exposure |
| PAY-06-R04 Approved-to-billed pattern | S / MONTHLY | Persistent low approval ratio or suspiciously invariant full approval versus peers | Adjudication model and contract differences | Education, audit or PAY-11 link |

### PAY-07 — Patient-share, copay, deductible and balance billing · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PAY-07-R01 Expected-share mismatch | H / PREPAY | Submitted claim/Activity share differs from benefit calculation | Deductible accumulator, exemptions, rounding | Reprice/return |
| PAY-07-R02 Share shifted to payer | H / PREPAY | `gross - valid_discount - patient_share != net` or waived share included in net | Approved discount/hardship | Reprice |
| PAY-07-R03 Systematic zero/rounded share | S / MONTHLY | Provider zero-share or repeated-rounding rate exceeds product-adjusted peers | Zero-share benefits and regulator programs | Postpay audit |
| PAY-07-R04 Excess patient charge/balance bill | H/S / DAILY | Receipt/complaint/collection data exceeds approved patient liability | Non-covered elective items with documented consent | Member protection/provider case |

### PAY-08 — Denial-resubmission mutation and gaming · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PAY-08-R01 Missing/broken lineage | H / INGEST | Correction/resubmission lacks valid prior payer ID/type or references unrelated claim | Legacy route where permitted | Return |
| PAY-08-R02 Reimbursement-enabling field mutation | H/E / ASYNC | Denied line changes diagnosis, code, units, provider, setting or indicator without coherent correction evidence | Accepted correction matrix by denial code | Pend with field diff |
| PAY-08-R03 Repeated resubmission loop | S / DAILY | Attempts per underlying service exceed `cfg.max_attempts` or alternate variants until paid | Internal complaint/appeal route | Provider case |
| PAY-08-R04 Edit-learning success anomaly | S / MONTHLY | Provider's mutated resubmission success materially exceeds peers and concentrates on specific denial edits | Biller/vendor and policy-change adjustment | SIU/payment-integrity lead |

### PAY-09 — Disguised non-covered service or product · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PAY-09-R01 Code-description/document conflict | E/T / ASYNC | Note/order/Observation describes an uncovered service while claim uses covered code | NLP confidence and clinician review | Pend |
| PAY-09-R02 Covered-code substitution pattern | S / MONTHLY | Provider uses a payable proxy code unusually often around denied/non-covered services | Code-family and denial-history map | Postpay audit |
| PAY-09-R03 Cosmetic/alternative/non-medical disguise | E / PREPAY | Diagnosis, setting and product combination matches approved disguise-risk policy | Reconstructive/medical-necessity exceptions | Clinical pend |
| PAY-09-R04 Member/provider confirmation mismatch | S / DAILY | Member receipt/confirmation describes different item/service than billed | Confirmation reliability and consent | SIU lead |

### PAY-10 — Coordination of benefits and third-party liability · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PAY-10-R01 Other coverage not coordinated | H / PREPAY | Active primary/other coverage exists but claim submitted with wrong payer order | UAE/product COB policy | Pend/reprice |
| PAY-10-R02 Multi-payer overpayment | H / DAILY | Sum of payer payments + patient liability exceeds allowable charge | Lawful top-up and benefit coordination | Recovery case |
| PAY-10-R03 Accident/liability indicator missing | H/E / PREPAY | Diagnosis/encounter suggests road/work/third-party event but liable-party fields absent | Clinical false-positive list | Pend for coordination data |
| PAY-10-R04 Duplicate recovery after settlement | H / DAILY | Claim paid by health payer after documented third-party settlement without offset | Subrogation/recovery policy | Recovery workflow |

### PAY-11 — Internal adjudication, override and payment manipulation · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PAY-11-R01 Unauthorized/manual override | H / DAILY | Denial/edit overridden without required role, approval or reason | Emergency escalation and delegated authority | Internal-control case |
| PAY-11-R02 Adjudicator-provider concentration | S/N / MONTHLY | Employee's override/payment volume to provider materially exceeds adjusted peers | Assigned provider books and specialty | Compliance/SIU lead |
| PAY-11-R03 Post-settlement upward adjustment | H/S / DAILY | Paid amount increased after settlement without valid adjustment reason/workflow | Contract true-up and appeal decision | Internal audit case |
| PAY-11-R04 Suspicious full-pay/invariant decisions | S / MONTHLY | Adjudicator/provider pair shows unusually high approval and low variance despite comparable edits | Auto-adjudicated claims excluded | Internal audit lead |

### PAY-12 — Reversal, refund, credit-balance and remittance leakage · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PAY-12-R01 Paid cancelled/reversed claim | H / DAILY | Net payment remains after effective cancellation/reversal | Timing tolerance and netting process | Recovery |
| PAY-12-R02 Duplicate remittance/payment reference | H / DAILY | Same payable claim/line paid more than once or payment reference reused inconsistently | Split settlement and batch payments | Finance pend/recovery |
| PAY-12-R03 Unapplied provider refund/credit | H / DAILY | Received credit/refund not linked to outstanding recovery within SLA | Dispute and unapplied-cash queue | Finance exception |
| PAY-12-R04 Negative/offset manipulation | S / MONTHLY | Provider repeatedly offsets credits against unrelated claims or delays reversals versus peers | Contractual netting rules | Postpay audit |

### CLN-01 — Upcoding and code-intensity inflation · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| CLN-01-R01 High-level code share | S / MONTHLY | Highest-paid level share in code family exceeds shrunk peer percentile | Specialty, setting, case mix, minimum `n` | Provider coding case |
| CLN-01-R02 Expected-level residual | S/M / DAILY | Billed level exceeds level predicted from diagnoses, age, setting and prior utilization by `cfg.delta` | Interpretable ordinal model; no document features at scoring time if unavailable | Prepay sample |
| CLN-01-R03 Documentation-level conflict | E/T / ASYNC | Extracted work/severity/time elements do not meet policy for billed level | Validated Arabic/English extraction and human review | Coding pend |
| CLN-01-R04 Level migration changepoint | S / MONTHLY | Provider abruptly shifts to higher code levels absent case-mix/contract change | Segment known structural changes | Postpay sample audit |

**Model note:** Use an ordinal logistic/gradient-boosted model to estimate expected code level only after a transparent peer distribution is live. Train on audited-supported levels or high-confidence records, not paid claims as truth. Report actual level, expected distribution, peer rate and payment differential.

### CLN-02 — Diagnosis, comorbidity and DRG severity manipulation · P0/P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| CLN-02-R01 Payment-changing secondary diagnosis | H/E / DAILY | Removing suspect secondary diagnosis lowers DRG/payment and code lacks required supporting evidence | Current grouper and audit policy | Coding audit candidate |
| CLN-02-R02 Comorbidity prevalence outlier | S / MONTHLY | Provider's CC/MCC or local severity-code rate exceeds risk-adjusted peers | DRG, age, transfer, specialty, minimum volume | Provider case |
| CLN-02-R03 Prior-history inconsistency | E/S / DAILY | Acute/severe diagnosis materially conflicts with longitudinal history and episode evidence | New diagnoses allowed; absence is weak evidence | Prioritize record review |
| CLN-02-R04 POA/sequencing conflict | H/E / PREPAY | POA or principal/secondary sequence violates effective coding policy | Transfer and obstetric/newborn rules | Coding pend |
| CLN-02-R05 Severity-mix changepoint | S / MONTHLY | Severity index increases without corresponding procedure, LOS or referral shift | Service-line expansion segmentation | Postpay audit |

### CLN-03 — Clinical incompatibility and specialty mismatch · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| CLN-03-R01 Impossible diagnosis–procedure pair | H / PREPAY | Pair explicitly prohibited by authoritative rule | Only rules marked `hard=true` | Reject/pend |
| CLN-03-R02 Unsupported indication | E / ASYNC | No same-episode or lookback indication in curated policy | Lookback and accepted indication groups | Clinical review |
| CLN-03-R03 Procedure sequence conflict | E / DAILY | Prerequisite procedure/result absent or service occurs in impossible order | External services and data latency | Pend/audit |
| CLN-03-R04 Rare pair/specialty anomaly | S / MONTHLY | Provider's rare combinations exceed specialty peer prevalence | Minimum volume; exploratory only | Monitor/policy review |

### CLN-04 — Unnecessary, excessive or repeated services · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| CLN-04-R01 Minimum repeat interval | E / PREPAY | Same/equivalent service repeated inside policy interval without accepted indicator | Code family, clinical exception and required Observation | Clinical pend |
| CLN-04-R02 Episode frequency excess | E/S / DAILY | Count per episode/member exceeds policy maximum or risk-adjusted peer threshold | Diagnosis/care pathway and age | Pend/audit |
| CLN-04-R03 No result before repeat | E / ASYNC | Repeat diagnostic service occurs while prior result/report is absent or unchanged | Result latency, failed/inconclusive test | Review |
| CLN-04-R04 Provider utilization outlier | S / MONTHLY | Services per comparable episode/member exceed shrunk peers | Case mix, referral role and denominator | Provider case |
| CLN-04-R05 Cascade pattern | S/N / WEEKLY | Initial low-intensity encounter reliably triggers unusually large downstream test/service bundle | Specialty pathway and network structure | Postpay/network case |

### CLN-05 — Length-of-stay, admission and readmission irregularity · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| CLN-05-R01 LOS high/low residual | S / DAILY | LOS outside risk-adjusted DRG/diagnosis prediction interval | Transfers, deaths, ICU and outlier payment | Utilization review |
| CLN-05-R02 Same/related readmission | E/S / DAILY | Related admission inside `cfg.readmit_days` with payment impact | Planned/staged care, unrelated trauma | Episode review, not fraud label |
| CLN-05-R03 Discharge-readmit split | H/E / DAILY | Two stays likely constitute one continuous episode under payment policy | Transfers and genuine clinical deterioration | Reprice/pend |
| CLN-05-R04 Admission-rate outlier | S / MONTHLY | Provider admits unusually high share of comparable presentations | Severity, referral mix and observation status | Postpay audit |

### CLN-06 — Phantom billing/service not rendered · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| CLN-06-R01 Missing expected order/result trail | E / ASYNC | Billed diagnostic/therapy lacks required order, result, Observation or administration evidence | Artifact latency and service-specific requirements | Pend |
| CLN-06-R02 Closed/non-operational facility service | H/S / DAILY | Service occurs outside verified operating period or facility shows no credible operating footprint | 24-hour/emergency and outreach service | SIU lead |
| CLN-06-R03 Repeated synthetic encounter signature | S / DAILY | High rate of identical code/time/amount/note patterns across unrelated members | Standard packages and batch timestamps | Provider case |
| CLN-06-R04 Member denial/attendance mismatch | S / DAILY | Reliable member confirmation or attendance record says service not received | Contact/authentication quality and recall | High-priority SIU lead |
| CLN-06-R05 No longitudinal clinical footprint | S / MONTHLY | Claimed high-impact service lacks expected follow-up, medication, result or episode consequences versus peers | Out-of-network follow-up and data completeness | Supporting evidence only |

### CLN-07 — Provider capacity and throughput impossibility · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| CLN-07-R01 Improbable service day | E/S / DAILY | Sum of conservative service minutes/units per clinician exceeds available day capacity | Parallel/team services and documented hours | Provider timeline |
| CLN-07-R02 Facility/staff capacity | E/S / DAILY | Claimed volume exceeds rooms/equipment/licensed staff capacity plus tolerance | Missing roster produces low confidence | Audit lead |
| CLN-07-R03 Scarce-equipment concurrency | E / DAILY | Same device/resource required by overlapping services beyond capacity | Equipment inventory and turnaround | Pend/audit |
| CLN-07-R04 Capacity trend discontinuity | S / MONTHLY | Throughput jumps without staff, hours, equipment or facility change | Onboarding/data-feed changes | Provider case |

### CLN-08 — Laboratory, pathology and genetic-testing integrity · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| CLN-08-R01 No qualified order/relationship | E / PREPAY_ASYNC | Test lacks valid ordering clinician or qualifying encounter/indication | Screening programs, standing orders | Clinical pend |
| CLN-08-R02 Panel/component inflation | H/E / PREPAY | Components billed separately or panel substantially exceeds ordered tests | Reflex testing and local panel rules | Reprice/pend |
| CLN-08-R03 Absent/duplicate result | E/T / ASYNC | Paid test lacks result/report or identical result appears across unrelated patients | Result latency and normal templates | Audit/SIU lead |
| CLN-08-R04 Reference-lab/pass-through spread | S/N / MONTHLY | Billing entity adds abnormal markup or volume while test is performed by concentrated third party | Contract and permitted reference arrangements | Postpay/network case |
| CLN-08-R05 High-complexity/genetic test outlier | S / MONTHLY | Provider ordering/rendering rate, panel size or cost exceeds risk-adjusted peers | Specialty/oncology/rare-disease centres | Targeted record sample |

### PHR-01 — Prescribed, authorized, billed and dispensed mismatch · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PHR-01-R01 Product identity mismatch | H / PREPAY | Billed product differs from prescribed/authorized product and is not approved equivalent | Generic/trade equivalence and substitution policy | Pend/reject |
| PHR-01-R02 Quantity/strength/form mismatch | H/E / PREPAY | Billed quantity, strength or dosage form exceeds order/authorization | Partial fill, titration and package conversion | Reprice/pend |
| PHR-01-R03 Dispense-claim mismatch | H / DAILY | Dispensing/inventory record differs from billed product/quantity | Claim timing and reversals | Pharmacy case |
| PHR-01-R04 Non-medical/uncovered substitution | E/S / DAILY | Member/receipt/inventory evidence indicates uncovered or non-medical item supplied | Confirmation reliability | SIU lead |

### PHR-02 — Early refill, stockpiling and multi-prescriber convergence · P0

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PHR-02-R01 Refill overlap | H/E / PREPAY | Remaining supply at next fill exceeds `cfg.allowed_overlap_days` | Dose change, lost/travel override, inpatient days | Pend |
| PHR-02-R02 Therapy-duration excess | E / DAILY | Continuous fills exceed diagnosis/drug policy duration without review | Chronic therapy and specialist approval | Clinical review |
| PHR-02-R03 Multi-prescriber same-equivalent drug | E/S / DAILY | Distinct prescribers within window exceed drug/specialty threshold | Care team and provider-group identity | Member/pharmacy case |
| PHR-02-R04 Multi-pharmacy convergence | S/N / DAILY | Same member obtains overlapping equivalent drug from multiple pharmacies | Stock shortage and partial fills | SIU/clinical lead |

### PHR-03 — High-cost drug/infusion/specialty-product spike · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PHR-03-R01 Dose/weight/body-surface conflict | E / PREPAY | Claimed dose outside approved clinical range | Wastage, loading dose and rounding | Clinical pend/reprice |
| PHR-03-R02 Drug-diagnosis/step-therapy conflict | E / PREPAY | Indication or prerequisite therapy absent | Authorization overrides and rare disease | Pend |
| PHR-03-R03 Provider/pharmacy volume spike | S / MONTHLY | Risk-adjusted volume/value changepoint without patient-mix shift | New formulary/centre status | Audit |
| PHR-03-R04 Wastage/unused-vial anomaly | S / MONTHLY | Wastage units or vial rounding exceed comparable dosing peers | Single-use vial policy | Postpay sample |

### PHR-04 — Prescriber–pharmacy steering and reciprocal concentration · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PHR-04-R01 Top-pharmacy concentration | S / MONTHLY | Prescriber's share to top pharmacy exceeds geographic/specialty peers | On-site, specialty and narrow network | Network lead |
| PHR-04-R02 Reciprocal value loop | N / WEEKLY | Concentrated prescriber→pharmacy flow aligns with referrals/ownership/shared IDs | Known corporate relationships | SIU graph |
| PHR-04-R03 High-cost steering | S/N / WEEKLY | Concentration is materially stronger for profitable/high-cost drugs | Product availability | Prioritized lead |
| PHR-04-R04 Rapid relationship formation | N / WEEKLY | New prescriber-pharmacy edge rapidly becomes dominant | New site/contract launch | Monitor/SIU |

### PHR-05 — Equipment, implant, consumable and supply integrity · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| PHR-05-R01 New/used/rental/purchase mismatch | H/E / PREPAY | Billed condition or payment method conflicts with authorization, serial/inventory or contract | Refurbishment and rent-to-own policy | Reprice/pend |
| PHR-05-R02 Implant/device not linked to procedure | E / PREPAY | Device/implant lacks qualifying procedure, laterality or operative record | Replacement/spare policy | Clinical pend |
| PHR-05-R03 Supply quantity/consumption excess | E/S / DAILY | Units exceed procedure/episode norm or repeat too soon for useful life | Member growth/damage/clinical change | Reprice/audit |
| PHR-05-R04 Serial/inventory duplication | H/N / DAILY | Same serial/batch billed for multiple members or claimed stock exceeds inventory/acquisition | Bulk/non-serialized consumables | SIU lead |

### DOC-01 — Documentation-to-billing/authorization inconsistency · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| DOC-01-R01 Required document absent | H/E / ASYNC | Rule requires note/report/consent/Observation and it is missing after SLA | Document type and latency | Pend |
| DOC-01-R02 Structured fact conflict | T/E / ASYNC | Extracted diagnosis, procedure, date, quantity or setting contradicts claim/authorization | Per-field extraction precision threshold | Human review |
| DOC-01-R03 Medical-necessity support absent | T/E / ASYNC | Required indication/severity element cannot be found | Absence is not proof; use qualified reviewer | Clinical review |
| DOC-01-R04 Authorization narrative drift | T / ASYNC | Material semantic/entity mismatch between request narrative and billed event | Explain with extracted conflicting facts | Pend |

**Model note:** Prefer structured extraction plus explicit comparisons over a single semantic-similarity threshold. Measure precision/recall by language and document type; OCR confidence must flow into signal confidence.

### DOC-02 — Cloned, templated or retrospectively altered documentation · P2

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| DOC-02-R01 Cross-patient near duplicate | T / DAILY | Patient-specific content similarity exceeds threshold across unrelated members | Remove standard boilerplate before comparison | Audit sample |
| DOC-02-R02 Contradictory copied facts | T/E / DAILY | Note contains wrong patient demographics/date/laterality or impossible copied findings | Extraction confidence | High-priority review |
| DOC-02-R03 Post-denial material alteration | H/T / DAILY | Document version changes reimbursement-relevant facts after denial without addendum provenance | Valid signed addendum policy | PAY-08-linked case |
| DOC-02-R04 Template-to-complexity mismatch | T/S / MONTHLY | High-complexity services supported by unusually generic notes versus peers | Specialty and EHR template | Supporting evidence only |

### NET-01 — Referral concentration, reciprocity and downstream conversion · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| NET-01-R01 Referral concentration outlier | S / MONTHLY | Top-recipient share/HHI exceeds specialty/geographic peers | Group/network and centre-of-excellence | Network case |
| NET-01-R02 Reciprocal referral loop | N / WEEKLY | A→B and B→A edges are unusually strong relative to opportunity | Multidisciplinary teams | Graph evidence |
| NET-01-R03 High-cost conversion | S/N / WEEKLY | Referred members convert to high-cost service at abnormal rate/value | Case mix and referral indication | Prioritized audit |
| NET-01-R04 Closed downstream chain | N / WEEKLY | Referrer→lab/imaging/pharmacy chain retains members within small dense group | Ownership/narrow network | SIU lead |

### NET-02 — Collusion ring and shared-identifier linkage · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| NET-02-R01 Shared administrative identity | H/N / DAILY | Legally distinct entities share bank, phone, address, device or owner identifier | Known groups/shared services; fuzzy matches cannot be hard flags | Graph edge |
| NET-02-R02 Dense member circulation | N / WEEKLY | Community has abnormal internal member/provider edge density and low external flow | Specialty/geography/size matched communities | SIU graph |
| NET-02-R03 Synchronized billing | N/S / DAILY | Community claims share unusual time, amount, code or resubmission signatures | Batch billing systems | Supporting evidence |
| NET-02-R04 Structural-change alert | N / WEEKLY | Previously peripheral nodes rapidly become central/dense with material exposure | Merger/new contract | Monitor/SIU |

### NET-03 — Provider–member collusion and inducement · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| NET-03-R01 Repeated high-value dyad | S/N / MONTHLY | Member-provider pair has abnormal frequency/value and benefit exhaustion | Chronic/rare-disease pathways | Case evidence |
| NET-03-R02 Small closed member group | N / WEEKLY | Provider activity concentrates in tightly connected member/employer group | Clinic catchment and employer onsite care | SIU graph |
| NET-03-R03 Inducement signature | S / MONTHLY | Zero patient share, non-medical substitution or repetitive profitable services co-occur | Approved programs | High-priority lead |
| NET-03-R04 Complaint/confirmation corroboration | S / DAILY | Authenticated member evidence corroborates service/item or charge mismatch | Evidence reliability | Escalate case |

### NET-04 — Broker, agent and employer-group concentration · P2

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| NET-04-R01 Confirmed-outcome rate | S / MONTHLY | Hierarchical model shows excess validated FWA/error outcomes by originator/group | Never use raw system flags as label; control portfolio mix | Distribution review |
| NET-04-R02 Provider concentration | S/N / MONTHLY | Originator/group members disproportionately use a small provider network | Employer clinic and geography | Network case |
| NET-04-R03 Early-tenure high-risk cluster | S / MONTHLY | High-cost claims shortly after enrollment cluster by originator/group beyond morbidity expectation | Maternity/chronic continuity and guaranteed issue | Review, never individual denial |
| NET-04-R04 Shared identifiers/actors | N / WEEKLY | Broker, employer, member and provider share suspicious contact/payment/device links | Lawful data and known corporate links | SIU graph |

### ANL-01 — Multivariate anomaly and behavioral change · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| ANL-01-R01 Robust peer composite | S / MONTHLY | Weighted robust residuals across scenario-aligned features exceed calibrated threshold | Specialty/setting/size peer hierarchy | Explainable entity lead |
| ANL-01-R02 Self-history changepoint | S / MONTHLY | CUSUM/Bayesian changepoint on value, mix, frequency or denial behavior | Segment tariff/contract/ownership changes | Entity lead |
| ANL-01-R03 Unsupervised incremental anomaly | M / MONTHLY | Benchmarked model flags entity and adds lift beyond R01/R02 | Temporal validation, feature attribution, drift | Monitor/SIU only |
| ANL-01-R04 Novel-cluster discovery | M / QUARTERLY | Analyst-reviewed cluster exhibits coherent new typology and material exposure | Exploratory; no production action until converted to rule | Rule-development candidate |

**Model note:** Benchmark Isolation Forest and LOF first. One-Class SVM, autoencoder, DBSCAN and GMM remain experiments unless prospective lift, stability and explanation quality beat the baseline. Features must be computed strictly before the scored period to avoid leakage.

### POL-01 — Enrollment, employer-group and policy manipulation · P1

| Rule | Type/stage | Implementable trigger | Configuration and exclusions | Output |
|---|---|---|---|---|
| POL-01-R01 Eligibility/roster conflict | H / DAILY | Enrolled member lacks valid sponsor/employment/dependent relationship or duplicate active identity exists | Continuation, newborn and mandated coverage | Enrollment pend |
| POL-01-R02 Retroactive event after service | H/S / DAILY | Member add/change occurs after high-cost service with actor/time pattern outside policy | Approved retroactive correction/SLA | Underwriting/compliance review |
| POL-01-R03 Application/claim fact conflict | E / DAILY | Material application declaration conflicts with authoritative prior coverage/claim history where legally usable | Contestability, non-discrimination and privacy law | Human review only |
| POL-01-R04 Early-tenure utilization anomaly | S / MONTHLY | Claim pattern shortly after inception exceeds tenure/risk-adjusted expectation | Not evidence of fraud alone; maternity/chronic continuity | Monitor/distribution signal |
| POL-01-R05 Employer/broker enrollment cluster | S/N / MONTHLY | Suspicious member additions, identity links or early claims cluster by employer/originator | Portfolio size and enrollment campaign | NET-04-linked case |

---

## 5. Case correlation, scoring and financial exposure

### 5.1 Correlation rules

Signals are grouped before presentation:

- **Claim lineage:** same original claim, corrections, complaints, resubmissions, remittances and reversals.
- **Episode:** member plus clinically related encounters/Activities over the configured episode window.
- **Provider behavior:** provider plus scenario family and analysis period.
- **Pharmacy/product:** pharmacy, prescriber, product family and member/episode.
- **Network:** graph community plus analysis snapshot.
- **Distribution:** broker/agent/employer group plus policy cohort.

Use a deterministic `case_fingerprint = hash(tenant, case_type, primary_subject, scenario_family, period_bucket)` and allow merge/split with a recorded audit event. PAY-08 on a corrected claim, DOC-02 on the altered note and CLN-01 on the billed level should become one coding case.

### 5.2 Priority score

Start with a transparent score; do not train a stacker at launch:

```text
priority = 100 * sigmoid(
    1.10 * evidence_strength
  + 0.80 * log1p(exposure_aed / 1000)
  + 0.55 * independent_domain_count
  + 0.45 * validated_prior_history
  + 0.25 * recency
  - 0.60 * data_quality_penalty
  - 0.50 * known_exception_strength
)
```

Normalize inputs to `[0,1]` except exposure. Cap multiple rules using the same underlying fact at the maximum evidence strength rather than summing them. Hard-edit disposition remains determined by policy even if the priority score is low.

### 5.3 Exposure calculation

- **Line edit:** `max(0, submitted_payable - correctly_repriced_payable)`.
- **Duplicate:** lower of duplicated paid/requested amounts after valid patient share.
- **Provider pattern:** sum of sampled suspect incremental amounts, plus an explicitly labelled extrapolation interval only after audit policy permits it.
- **Network:** sum distinct paid/requested lines once; do not double count nodes.
- **Uncertain model lead:** show gross amount and “exposure not yet established,” not gross amount as savings.

---

## 6. Statistical and model implementation standards

### 6.1 Peer baselines

Peer grouping hierarchy:

```text
activity/code family
  → specialty
  → encounter/facility type
  → payment method/contract family
  → geography
  → provider size/volume band
```

Use empirical-Bayes shrinkage for rates and minimum denominators (`cfg.min_provider_claims`, `cfg.min_peer_entities`). For skewed values use median/MAD or percentiles; do not use a plain z-score unless residual diagnostics support normality. If a granular peer is sparse, back off to its parent and record `peer_level_used`.

Recommended rate estimate for provider `i`:

```text
shrunk_rate_i = (events_i + alpha_peer) / (opportunities_i + alpha_peer + beta_peer)
```

Fit `alpha_peer`, `beta_peer` from the peer population or use a hierarchical binomial model. Report the posterior interval and avoid ranking entities whose intervals are too wide.

### 6.2 Change detection

Use weekly/monthly normalized metrics with at least `cfg.min_history_periods`. Start with CUSUM, EWMA or Bayesian online/offline changepoints. Reset or add covariates for tariff, contract, facility, ownership, specialty, system migration and roster changes. Store the pre-change mean, post-change mean, change date and confidence.

### 6.3 Unsupervised anomaly models

Baseline candidates: Isolation Forest and LOF on robust-scaled, peer-residual features. Compare against the transparent robust composite in ANL-01-R01 using future-period review yield, not in-sample separation. Requirements:

- Train only on data available before the scoring period.
- Exclude direct identifiers and protected demographic attributes unless legally approved and necessary for clinical adjustment.
- Impute missingness explicitly and include missingness indicators where informative.
- Calibrate the operational threshold to review capacity and expected value.
- Produce top contributing features with original units and peer comparison.
- Monitor population stability, score distribution, alert volume and review yield.

### 6.4 Supervised propensity model

Do not build until outcome capture is stable. Target labels: `confirmed_fraud`, `confirmed_abuse_waste`, `billing_error`, `policy_exception`, `no_issue`, `unresolved`. Exclude unresolved cases from primary training and correct for investigation-selection bias using random audits or propensity weighting.

Use temporal train/validation/test splits and entity isolation where appropriate. Evaluate precision at review capacity, recall on random-audit findings, AED yield, calibration, specialty/payer stability and overturn/appeal rates. A gradient-boosted tree is a sensible first candidate; a more complex model must show prospective lift.

### 6.5 NLP/document models

Pipeline: document classification → OCR → language detection → clinical entity/negation extraction → structured comparison → evidence rendering. Evaluate by document type and Arabic, English and mixed language. Store offsets and display the exact supporting/conflicting text. No free-form generative model output should be persisted as a factual clinical finding without source spans.

### 6.6 Graph models

Use typed, time-bounded edges and materialize weekly snapshots. Compute concentration, reciprocity, connected components, community membership and centrality only within comparable node types. Community detection is exploratory until the network has material exposure and at least one interpretable edge pattern. Entity resolution must expose match fields and confidence and must not merge records automatically at low confidence.

---

## 7. Specialty and payment-method rule packs

The 39 scenarios are cross-cutting typologies. Production coverage also requires service-line packs. These are configurations and subrules of existing scenarios, not new top-level fraud categories.

| Pack | Minimum required rules |
|---|---|
| **Dental** | Tooth/surface/quadrant validity; incompatible procedures on same tooth; replacement/frequency windows; radiograph support; provider specialty; staged-treatment duplicates |
| **Optical** | Frame/lens/contact benefit periodicity; prescription-to-dispense match; lens attributes; duplicate family/member use; non-covered product substitution |
| **Maternity/newborn** | Gestational-age and delivery-date consistency; global maternity package; duplicate professional/facility billing; newborn identity/coverage linkage; mother/baby claim allocation |
| **Home care** | Staff attendance and shift overlap; member/provider concurrency; authorized hours exhaustion; credential match; impossible travel; supplies included in package |
| **Rehabilitation/physiotherapy** | Session duration overlap; authorized visits; episode frequency; progress documentation; unattended/group treatment rules |
| **Mental/behavioral health** | Time-based overlap; session frequency; provider credential; inpatient/outpatient setting; treatment-plan support; privacy-minimized evidence |
| **Ambulance/transport** | Origin/destination, distance, vehicle/service level, emergency indication, duplicate transport and encounter linkage |
| **Anesthesia/surgery** | Start/stop units, concurrent cases, base/time unit formula, assistant-surgeon eligibility, multiple-procedure reductions, implant/operative-note linkage |
| **Dialysis/infusion** | Treatment schedule, dose/weight, session attendance, drug/wastage, package inclusion, vascular-access services |
| **Laboratory/genetic testing** | Ordering relationship, indication, panel/component edit, specimen/result identity, repeat interval, reference-lab pass-through, high-complexity peer analytics |
| **Pharmacy** | Days supply, dose, generic/trade equivalence, partial fill, high-cost/controlled product, prescribed-authorized-billed-dispensed reconciliation |
| **Devices/DME/consumables** | Authorization, useful life, rental/purchase, new/used, serial/batch, procedure linkage, quantity and inventory reconciliation |
| **Inpatient/DRG/package** | Grouper version, POA, principal/secondary sequencing, severity, transfer/readmission, LOS, outlier payment and inclusions/exclusions |
| **Telehealth** | Provider/member eligibility, interaction evidence, service suitability, remote ordering and downstream concentration |

Each pack must be owned jointly by coding/clinical policy and engineering. A generic rules engine without these maintained content packs is not a complete payment-integrity product.

---

## 8. Development epics and sequencing

### Epic 0 — Foundations

1. Immutable raw transaction store and parsed canonical model.
2. Effective-dated reference/policy service.
3. Claim lineage and episode builder.
4. Rule registry, evaluator, evidence contract and versioning.
5. Signal store, case correlation and review outcome taxonomy.
6. Data-quality observability and tenant/payer configuration isolation.

### Epic 1 — P0 hard edits

Build ENT-01, ENT-03, ENT-05, PAY-01 to PAY-04, PAY-06 to PAY-09, CLN-01, CLN-02, CLN-04, CLN-06, PHR-01 and PHR-02. Start in shadow mode, compare with existing adjudication, then activate objective rules individually.

### Epic 2 — P1 provider analytics

Build peer service, provider features, change detection, CLN-03/05/07/08, PHR-03/04/05, ENT-02/04/06, PAY-10/11/12 and DOC-01. Add sample-based provider cases and exposure estimation.

### Epic 3 — Networks and distribution

Build typed graph, NET-01 to NET-04 and POL-01. Require legal/privacy approval for administrative identifiers, broker/employer analysis and cross-payer linkage.

### Epic 4 — Mature models

Build DOC-02, ANL-01-R03/R04 and supervised priority models only after random-audit and investigation outcomes are reliable.

---

## 9. Testing and release acceptance

### 9.1 Rule-level tests

Every atomic control needs, at minimum:

1. Positive fixture that triggers the exact reason code.
2. Clean negative fixture.
3. Boundary case at dates, amounts, units and thresholds.
4. Null/missing-input behavior.
5. Effective-date test using two policy versions.
6. Correction/cancellation/resubmission test.
7. Approved exception test.
8. Idempotency test: replay produces no duplicate signal.
9. Tenant isolation test.
10. Evidence snapshot asserting human-readable facts and source versions.

### 9.2 Scenario integration tests

- A corrected duplicate should close/supersede the prior signal, not create two open cases.
- A package component on another claim should correlate into the same episode.
- A denied claim mutation should display field-level differences and the final payment outcome.
- A provider peer result must remain reproducible from the stored baseline version.
- Graph cases must sum each claim once.
- Document results must link to source spans and degrade confidence when OCR quality falls.

### 9.3 Shadow and production gates

| Gate | Minimum acceptance evidence |
|---|---|
| Data readiness | ≥99.5% key linkage for claims/lines; scenario-specific completeness reported, not hidden by imputation |
| Hard edit | Policy owner sign-off; expected/observed volume; ≥99% decision reproducibility; exception coverage |
| Expert edit | Clinical/coding validation sample; documented false-positive rate and appeal route |
| Statistical rule | Prospective shadow period; minimum peer sizes; stable volume; review yield above agreed baseline |
| Model | Temporal holdout; calibration; prospective lift over simple baseline; drift and explanation tests |
| Production | Rollback, kill switch, alert-volume ceiling, audit logs and responsible owner on call |

### 9.4 Operational metrics

Track precision, confirmed AED, prevented/recovered AED, net savings after review cost, provider/member abrasion, pend turnaround, overturn/appeal rate, rule stability, alerts per reviewer, time to case disposition and random-audit miss rate. Do not report gross flagged value as savings.

---

## 10. Completeness matrix and residual boundaries

| Typology family | Covered by |
|---|---|
| Services/items not rendered | CLN-06, CLN-08, PHR-01, PHR-05 |
| Duplicate, altered or fabricated claims | PAY-01, PAY-08, DOC-02 |
| Upcoding, diagnosis inflation and DRG manipulation | CLN-01, CLN-02 |
| Unbundling/global/package leakage | PAY-02 |
| Excess units, time and impossible volume | PAY-03, ENT-04, CLN-07 |
| Non-covered service/product disguise | PAY-09, PHR-01 |
| Unnecessary/repeated care | CLN-03, CLN-04, CLN-08, PHR-02/03 |
| Licence, identity, card and credential misuse | ENT-02 to ENT-04 |
| Authorization and resubmission gaming | PAY-04, PAY-08 |
| Patient-share waiver/excess charge | PAY-07 |
| Drug substitution and pharmacy steering | PHR-01 to PHR-04 |
| Device/supply substitution or non-delivery | PHR-05 |
| Kickback/referral/collusion networks | ENT-06, PHR-04, NET-01 to NET-04 |
| Payer/TPA employee or adjudication abuse | PAY-11 |
| COB, TPL, remittance and recovery leakage | PAY-10, PAY-12 |
| Enrollment/employer/broker manipulation | NET-04, POL-01 |
| Documentation falsification/cloning | DOC-01, DOC-02 |
| New/unknown behavior | ANL-01 and quarterly typology review |

Residual boundaries are deliberate:

- This catalog does not replace cyber-fraud controls for account takeover, payment-instruction compromise or ransomware.
- It does not define underwriting legality, sanctions/AML screening, provider credentialing workflow or clinical quality measurement in full, although signals may integrate with those systems.
- It does not assume access to cross-payer, civil-registry, travel, bank, device, inventory, receipt or member-confirmation data. Controls dependent on unavailable or unlawful data remain disabled.
- Detailed emirate-, payer-, contract- and specialty-specific thresholds must be populated by approved policy owners. They cannot be safely invented by engineering.

---

## 11. Source and policy anchors

Use sources as typology and data-model anchors; the effective rule is always the current regulator/payer/contract version applicable to the service date.

### UAE

- [DoH Shafafiya overview: Claim, Encounter, Activity, Observation and Episode](https://www.doh.gov.ae/en/shafafiya)
- [DoH Shafafiya dictionary: schemas, licenses, transactions and code lists](https://www.doh.gov.ae/en/shafafiya/dictionary)
- [DoH Common Types schema: amounts, patient share, denial and authorization fields](https://shafafiyaportal.doh.gov.ae/dictionary/CommonTypes_xsd.html)
- [DoH Resubmission Type definition](https://shafafiyaportal.doh.gov.ae/dictionary/CommonTypes_xsd~s~ResubmissionType.html)
- [DoH Reporting requirements](https://www.doh.gov.ae/en/shafafiya/reporting)
- [DoH prices, tariffs and current adjudication materials](https://www.doh.gov.ae/en/shafafiya/prices)
- [DoH Claims and Adjudication Rules V2025.1](https://www.doh.gov.ae/-/media/Feature/shafifya/Prices/Adjudication-Rules/DOH-Claims-and-Adjudication-Rules-V20251.ashx)
- [DoH healthcare insurance fraud typologies in the data standard](https://shafafiyaportal.doh.gov.ae/dictionary/Standards/Datastandard/Standards.pdf)
- [DoH pharmacy substitution enforcement example](https://www.doh.gov.ae/en/news/doh-refers-a-pharmacy-to-public-prosecution-for-investigation)
- [DHA 2026 professional conduct standard](https://dha.gov.ae/uploads/012026/Standards%20for%20Code%20of%20Ethics%20and%20Professional%20Conduct%20for%20Health%20Professionals%20V1%20202613351.pdf)
- [DHA eClaimLink standard data sets and current code lists](https://www.eclaimlink.ae/Default.aspx)
- [DHA Telehealth Services Standard, including eClaimLink coding and claims requirements](https://dha.gov.ae/uploads/012023/Standards%20for%20Telehealth%20Services2023158613.pdf)

### International methodology

- [CMS Medicare Fraud & Abuse: Prevent, Detect, Report](https://www.cms.gov/outreach-and-education/medicare-learning-network-mln/mlnproducts/downloads/fraud-abuse-mln4649244.pdf)
- [CMS Healthcare Fraud Prevention Partnership white papers](https://www.cms.gov/medicare/medicaid-coordination/healthcare-fraud-prevention-partnership/white-papers)
- [CMS HFPP Genetic Testing FWA white paper](https://www.cms.gov/files/document/hfpp-genetic-testing-fwa-white-paper.pdf)
- [HHS OIG telehealth fraud overview](https://oig.hhs.gov/reports/featured/telehealth/)
- [HHS OIG compliance guidance](https://oig.hhs.gov/compliance/compliance-guidance/)
- [CMS NCCI Medically Unlikely Edits overview](https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits/medicare-ncci-medically-unlikely-edits-mues)

---

## 12. Definition of done

The catalog is complete enough to begin engineering when the team treats each atomic control as a versioned backlog item and refuses to activate it until its referenced data, policy owner, exclusions, tests, evidence and disposition are present. The first build should deliver fewer accurate, explainable controls with reliable case feedback—not all 164 controls at once.
