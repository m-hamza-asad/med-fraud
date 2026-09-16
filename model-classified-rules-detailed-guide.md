# Detailed Implementation Guide for Model-Classified (`M`) Rules

**Companion to:** UAE Medical Claims Fraud, Waste and Payment-Integrity Developer Specification v3.0  
**Prepared:** 8 September 2026  
**Audience:** Product managers, data engineers, analytics/ML engineers, clinical coding teams, QA and SIU

---

## 1. Scope

The developer specification contains three atomic controls whose type includes `M`:

| Rule | Model role | Unit scored | Intended output |
|---|---|---|---|
| **CLN-01-R02 — Expected-level residual** | Predict the code level expected from the clinical/encounter context | Claim or encounter | Select claims for coding review |
| **ANL-01-R03 — Unsupervised incremental anomaly** | Find unusual combinations of entity behavior that add value beyond simpler controls | Provider/pharmacy/member-period | Monitoring or SIU lead |
| **ANL-01-R04 — Novel-cluster discovery** | Explore the population for recurring behavioral groups that may represent a new typology | Entity-period population | Candidate for a new explicit rule |

They solve different problems:

```text
CLN-01-R02 asks: “Given this encounter, what code level would normally be supported?”

ANL-01-R03 asks: “Is this entity's combined behavior unusually different from comparable entities?”

ANL-01-R04 asks: “Are several entities behaving alike in a way we have not yet encoded as a scenario?”
```

Only CLN-01-R02 is attached directly to a named billing scheme—upcoding. ANL-01-R03 is a broad detection safety net. ANL-01-R04 is research and rule discovery, not a production fraud decision.

---

## 2. Requirements shared by all `M` controls

### 2.1 What a model result means

A model result means that a claim or entity deserves attention under a defined analytical test. It does not establish that:

- the claim is incorrect;
- the service was unnecessary;
- the provider intended to deceive;
- payment should automatically be denied; or
- the entity should be reported as fraudulent.

All three rules require human or policy validation before an adverse decision.

### 2.2 Common data split

Use time-based partitions:

```text
Training period     Validation period      Test period       Prospective shadow
Jan–Dec 2024        Jan–Jun 2025           Jul–Dec 2025      Jan 2026 onward
```

The dates are illustrative. The important point is that the model must predict a later period using only earlier information. A random split can place the same provider's near-identical claims in training and testing and produce misleadingly strong performance.

Where the use case requires generalization to unseen providers, also keep entire providers out of the test set. Report both:

- performance on future claims from known providers; and
- performance on providers absent from training.

### 2.3 Common feature controls

Every feature must declare:

| Field | Meaning |
|---|---|
| `feature_name` | Stable technical name |
| `definition` | Exact numerator, denominator and filters |
| `observation_window` | Period from which the feature is calculated |
| `available_at` | Earliest timestamp at which the feature truly exists |
| `null_policy` | Missing-value treatment |
| `peer_scope` | Specialty, setting, contract or other segmentation |
| `owner` | Team responsible for correctness |
| `version` | Definition version |

Do not use fields created after the decision being predicted. Examples of leakage include final recovery amount, investigation outcome, future denials, appeal result or a diagnosis added after audit.

### 2.4 Common output contract

```yaml
rule_id: ANL-01-R03
model_version: iforest_provider_month_v1.3.0
subject_type: provider
subject_id: protected provider key
scoring_period: 2026-08
raw_score: 0.873
calibrated_priority: 91
confidence: medium
top_reasons:
  - feature: resubmission_rate
    actual: 0.182
    peer_median: 0.031
    peer_percentile: 0.992
  - feature: high_level_code_share
    actual: 0.640
    peer_median: 0.170
    peer_percentile: 0.981
data_quality_score: 0.94
financial_exposure_aed: 184000
recommended_disposition: SIU_LEAD
```

The model version must identify the training dataset cutoff, feature-set version, algorithm configuration and threshold version.

### 2.5 Common deployment states

1. **Development:** offline experimentation only.
2. **Backtest:** evaluate on a later untouched period.
3. **Shadow:** calculate results prospectively without influencing claims or investigators.
4. **Assisted review:** show results to analysts, but do not automatically change payment.
5. **Production prioritization:** use the score to order review work.
6. **Retired:** preserve reproducibility and history but stop scoring.

No `M` rule in this catalog is approved for autonomous claim rejection.

---

## 3. CLN-01-R02 — Expected-level residual

### 3.1 Plain-language definition

This rule estimates which billing level would normally be supported by the information available about an encounter. It then compares that expected level with the level actually billed.

Example: a consultation family has levels 1–5. The model estimates:

```text
Expected probabilities:
Level 1:  3%
Level 2: 18%
Level 3: 57%
Level 4: 19%
Level 5:  3%

Actual billed level: 5
```

The billed level is substantially higher than the expected distribution. The claim becomes a candidate for coding review. The model does not prove upcoding; documentation may contain facts unavailable to the model.

### 3.2 Why a model is useful

A basic provider-level rule can detect that a provider bills many high-level codes. It cannot adequately answer whether a particular high-level claim is reasonable for its patient and setting.

CLN-01-R02 can consider multiple factors together:

- diagnosis and comorbidity burden;
- member age and recent utilization;
- new versus established patient;
- emergency, outpatient or inpatient setting;
- procedures and tests associated with the encounter;
- encounter duration, when reliably available;
- referral context;
- specialty and facility type; and
- prior related encounters.

### 3.3 Prediction unit and population

Recommended initial prediction unit:

```text
one eligible encounter within one clearly ordered code family
```

Do not combine unrelated families in one target. A level-5 consultation and a high-complexity procedure are not numerically comparable simply because both contain a “5.”

Create a separate model—or a carefully designed multi-family model—for each code family with:

- an ordered complexity structure;
- adequate audited volume;
- a meaningful payment difference between levels; and
- documented coding criteria.

Exclude claims that are cancelled, reversed, incomplete, missing essential context, governed by exceptional payment rules or outside the model's supported population.

### 3.4 Target variable

The preferred target is:

```text
audited_supported_level
```

Acceptable sources, in descending order:

1. coding-audit determination after full documentation review;
2. upheld post-appeal coding determination;
3. high-confidence dual-review sample;
4. specially constructed reference set reviewed by qualified coders.

Do not train the model to reproduce the originally billed level and then call the prediction “correct.” Paid claims contain the behavior the product is trying to detect.

If audited labels are initially scarce, use a **statistical expected-level model** trained on a carefully selected low-risk reference cohort. Clearly label this as expectation modeling, not supervised fraud classification.

### 3.5 Features

Recommended first-version features:

| Group | Examples |
|---|---|
| Member context | age band, sex where clinically relevant, risk score, chronic-condition count |
| Encounter | new/established status, setting, emergency indicator, referral type, admission status |
| Clinical codes | diagnosis groups, number of diagnoses, comorbidity groups, associated procedures |
| History | related encounters in prior 30/90 days, recent admission, prior diagnostic burden |
| Provider context | specialty and facility type—not the provider's identity |
| Operational | reliable duration or time units, if available before adjudication |

Avoid provider ID as a direct predictor. Otherwise the model may learn “this provider usually bills level 5” and normalize the very behavior being investigated.

Exclude documentation-derived facts from the production model if documentation is not consistently available at scoring time. Those facts can be used separately by CLN-01-R03.

### 3.6 Model choices

Start with an ordinal logistic regression because the target has a natural order. It is relatively easy to explain and produces a probability for every level.

Benchmark it against a constrained gradient-boosted tree if nonlinear relationships appear important. Complexity is justified only if prospective review yield improves without unacceptable instability.

Do not frame the task as ordinary numeric regression without checking its consequences. Predicting level `3.4` is not itself meaningful; the output must be translated into probabilities over permitted levels.

### 3.7 Residual and trigger calculation

There are two useful trigger forms.

**Probability trigger:**

```text
P(model assigns a level at least as high as billed_level) < cfg.max_tail_probability
```

For the earlier example:

```text
P(level >= 5) = 3%
```

If the configured threshold is 5%, the claim qualifies.

**Expected-level residual:**

```text
expected_level = sum(level × predicted_probability(level))
residual = billed_level - expected_level
```

Trigger only when all conditions hold:

```text
residual >= cfg.minimum_level_difference
tail_probability <= cfg.maximum_tail_probability
incremental_payment_aed >= cfg.minimum_exposure
data_quality_score >= cfg.minimum_data_quality
```

For production, the probability trigger is generally preferable because it respects uncertainty.

### 3.8 Example

A cardiology provider bills a level-5 established-patient consultation.

```text
Model context:
- stable chronic diagnosis
- no new acute diagnosis
- no recent admission
- no high-complexity procedure
- short routine follow-up pattern

Predicted level probabilities:
L2 10%, L3 67%, L4 20%, L5 3%

Billed: L5
Expected level: 3.16
Incremental payment versus most likely level: AED 310
```

The claim is placed in a prepay coding sample. A coder may find that the note documents a legitimate complex issue absent from structured claims data. If so, the result is a model false positive or data-availability limitation—not provider misconduct.

### 3.9 Required explanation

Show:

- billed level;
- most likely expected level and full probability distribution;
- material factors increasing or decreasing expected complexity;
- comparison with the applicable specialty/setting peer group;
- estimated payment difference;
- data missing from the model; and
- a statement that documentation review is required.

### 3.10 Evaluation

Measure:

- exact-level accuracy;
- accuracy within one level;
- weighted error, penalizing larger level differences;
- probability calibration by code family;
- precision among claims selected for review;
- confirmed incremental overpayment AED per 100 reviews;
- overturn/appeal rate; and
- performance by specialty, setting, payer and facility type.

The most important operational metric is not generic accuracy. It is the yield of **higher-than-expected claims selected for review**, because lower-than-expected predictions are not the principal use case.

### 3.11 Failure conditions

Keep the rule in shadow mode if:

- audited labels are too sparse or selected only from previously suspicious claims;
- important documentation is unavailable at decision time;
- code-level criteria differ materially by payer but the model does not account for them;
- calibration fails for major specialties;
- the model mostly identifies one facility's data-quality issue; or
- the review yield does not beat CLN-01-R01's simpler provider-level sampling.

---

## 4. ANL-01-R03 — Unsupervised incremental anomaly

### 4.1 Recommended rename

Use this product-facing name:

> **Multivariate anomaly model with incremental-value validation**

“Incremental” means that the model must find useful cases beyond `ANL-01-R01` robust peer scoring and `ANL-01-R02` self-history change detection. It does not mean incremental or online model training.

### 4.2 Plain-language definition

This rule looks for entities with an unusual **combination** of behaviors. An entity can be moderately unusual on several dimensions without crossing any individual threshold.

Example:

| Feature | Provider percentile among peers |
|---|---:|
| Claims per member | 82nd |
| Average paid amount | 79th |
| Highest-level code share | 84th |
| Resubmission rate | 81st |
| Zero-patient-share rate | 78th |

No individual feature reaches a conventional 95th-percentile threshold. The joint pattern may nevertheless be extremely rare. An unsupervised model can detect that interaction.

### 4.3 Why it is unsupervised

The model is trained without a fraud/not-fraud target. It learns the shape of the observed provider population and assigns high anomaly scores to entities that are difficult to place within that shape.

This is useful during cold start, when confirmed investigation outcomes are limited. The trade-off is that unusual does not mean wrong. Specialist centres, new facilities and legitimate operational changes can be highly anomalous.

### 4.4 Scoring unit

Recommended first implementation:

```text
provider + payer + calendar month
```

Consider separate models for pharmacies, members and brokers only after provider scoring is stable. Do not mix node types in one feature matrix.

Require a minimum exposure and activity volume. Very small providers are naturally volatile and should use shrinkage, longer windows or monitor-only treatment.

### 4.5 Feature construction

Use 15–40 well-understood, scenario-aligned features rather than hundreds of raw codes. Candidate groups:

| Group | Examples |
|---|---|
| Volume | claims, members, encounters and lines per period |
| Intensity | services per episode, units per member, high-level code share |
| Financial | average paid amount, paid per member, high-cost-service share |
| Adjudication | denial, override, resubmission and approval ratios |
| Payment behavior | patient-share-zero rate, billed-to-allowed relationship |
| Mix | procedure concentration, diagnosis severity, encounter-setting mix |
| Temporal | weekend/night share, abrupt recent growth, burstiness |
| Relationships | referral/pharmacy concentration and member overlap |

First transform raw features into peer-relative residuals. A laboratory and a psychiatrist should not be compared on raw line volume.

Recommended robust transformation:

```text
robust_z(feature) =
    (provider_value - peer_median)
    / max(1.4826 × peer_MAD, configured_floor)
```

Winsorize only for numerical stability and retain the original value for explanation. Add missingness indicators rather than silently replacing all missing values with zero.

### 4.6 Baseline controls that must exist first

`ANL-01-R01` computes a transparent weighted composite of large peer residuals.

`ANL-01-R02` detects changes relative to the entity's own history using methods such as CUSUM or Bayesian changepoints.

R03 is justified only if its nonlinear/multivariate behavior identifies additional productive cases.

### 4.7 Candidate algorithms

Start with **Isolation Forest**:

- handles nonlinear combinations;
- scales reasonably well;
- does not require labelled fraud cases; and
- is usually easier to operate than a neural autoencoder.

Benchmark **Local Outlier Factor** when locally unusual behavior within dense specialty subgroups matters. Be cautious using LOF for scoring completely new records; implementation behavior differs between fitting and novelty detection.

One-Class SVM, autoencoders and other alternatives should remain experiments until they outperform the simpler models prospectively.

### 4.8 Training process

```text
1. Select completed historical months before the scoring month.
2. Apply data-quality filters and minimum-volume rules.
3. Build peer-relative features using baselines available at that time.
4. Remove known test entities and confirmed data-corruption periods.
5. Fit the candidate model.
6. Score the untouched future validation period.
7. Calibrate an operational threshold to review capacity.
8. Compare model-only results with R01 and R02.
9. Run prospectively in shadow mode.
```

Do not remove every known suspicious entity from training by default. Unsupervised healthcare data is expected to contain some misconduct. Isolation Forest can tolerate contamination, but its contamination/threshold assumptions must be tested.

### 4.9 Trigger logic

```text
qualifies =
    anomaly_percentile >= cfg.minimum_anomaly_percentile
    AND exposure_aed >= cfg.minimum_exposure
    AND data_quality_score >= cfg.minimum_data_quality
    AND activity_count >= cfg.minimum_volume

incremental =
    qualifies
    AND not already_fully_explained_by(R01, R02, active_scenario_rules)
```

“Not fully explained” does not mean suppress every overlap. If the model provides a genuinely different evidence domain, it may enrich an existing case. It should not create a second case merely because its score is high.

### 4.10 Measuring incremental value

Suppose a shadow period produces:

```text
Baseline R01/R02 alerts:             1,000
Validated findings from baseline:      120

R03 high-score entities:                300
Already detected by baseline:           250
Model-only entities reviewed:            50
Validated model-only findings:           12
```

Then:

```text
model-only precision = 12 / 50 = 24%
```

Also calculate model-only confirmed AED, review cost, stability and diversity of schemes. If the model mostly duplicates baseline alerts, it may still improve case priority, but it should not be presented as additional detection coverage.

### 4.11 Explanation

Never display only “anomaly score 0.93.” Show:

```text
Provider anomaly priority: 91/100

Main differences from comparable cardiology providers:
- Resubmission rate: 18.2%; peer median 3.1%; 99.2nd percentile
- Highest-level consultation share: 64%; peer median 17%; 98.1st percentile
- Zero patient-share rate: 43%; peer median 8%; 97.4th percentile
- Services per episode: 7.8; peer median 3.2; 96.8th percentile

Current-month claims: 184
Amount associated with unusual behavior: AED 184,000
Known operational changes: none recorded
```

Feature contribution methods may include controlled perturbation, local surrogate explanation or SHAP-compatible analysis. Always translate contributions back into original business units.

### 4.12 Evaluation

There is no conventional accuracy measurement without labels. Evaluate operationally:

- precision from blinded investigator/coding review;
- confirmed AED per reviewed entity;
- model-only precision and AED;
- overlap with existing scenarios;
- month-to-month alert persistence;
- score stability after ordinary data revisions;
- specialty and provider-size distribution;
- false-positive reasons; and
- sensitivity to feature/parameter changes.

### 4.13 Drift monitoring

Monitor:

- missingness and data-volume shifts;
- feature population stability;
- anomaly-score distribution;
- alert count by peer group;
- top-reason distribution;
- review yield; and
- model-only incremental value.

Retraining should respond to measured drift or a scheduled governance cycle. Do not retrain automatically simply because another month has arrived.

### 4.14 Production action

Default:

```text
MONITOR_ONLY
```

Allow:

```text
SIU_LEAD
```

only when there is material exposure, adequate data quality, an understandable reason profile and sufficient validation. Never use R03 alone for `REJECT` or provider sanction.

---

## 5. ANL-01-R04 — Novel-cluster discovery

### 5.1 Plain-language definition

This rule is better understood as an **analytical discovery process** than a production rule.

It groups entities with similar behavioral profiles so analysts can determine whether a recurring group represents:

- a legitimate business archetype;
- a data-quality or contract artifact;
- a known scenario that is poorly configured; or
- a genuinely new fraud/payment-integrity pattern worth converting into an explicit rule.

It does not mean “everyone in a strange cluster is fraudulent.”

### 5.2 Difference from R03

| R03 anomaly detection | R04 cluster discovery |
|---|---|
| Finds individual entities that are unusual | Finds groups of entities that behave similarly |
| Can prioritize a monitored/SIU lead | Produces research candidates |
| Runs monthly after validation | Runs quarterly or during targeted research |
| Requires incremental alert value | Requires coherent, repeatable and actionable group structure |
| Output is an entity score with reasons | Output is a cluster profile and proposed typology |

An entity can be part of a meaningful cluster without being an outlier. For example, twelve clinics may share a new resubmission-and-coding strategy; together they form a recognizable group even if none is individually extreme.

### 5.3 Population and feature matrix

Use one node type and a stable observation window, such as:

```text
provider + trailing six months
```

Use peer-relative features similar to R03, but retain features that help characterize behavioral archetypes:

- code-family distribution;
- patient/diagnosis mix;
- claim and payment characteristics;
- resubmission/denial behavior;
- patient-share behavior;
- temporal patterns;
- referral/pharmacy concentration; and
- service-setting mix.

High-dimensional raw code vectors should be grouped clinically or reduced carefully. Otherwise clusters may reflect minor coding vocabulary differences instead of meaningful behavior.

### 5.4 Algorithm choices

Candidate methods serve different purposes:

- **Hierarchical or k-means clustering:** useful for broad, stable behavioral archetypes after careful scaling; requires choosing the number of clusters.
- **Gaussian mixture model:** useful when entities may belong probabilistically to overlapping behavioral groups.
- **DBSCAN/HDBSCAN-style density clustering:** useful for finding dense groups and leaving sparse entities unassigned; sensitive to distance, scaling and density variation.

Do not select an algorithm solely because it gives the highest silhouette score. The selected result must be stable and interpretable to claims/SIU users.

### 5.5 Discovery workflow

```text
1. Define the business population and research question.
2. Freeze the feature definitions and observation window.
3. Robust-scale peer-relative features.
4. Run multiple clustering seeds/configurations.
5. Measure stability across samples and adjacent periods.
6. Produce plain-language profiles for every material cluster.
7. Ask coding, clinical, SIU and data-quality reviewers to classify clusters.
8. Inspect representative claims and estimate exposure.
9. Reject clusters explained by contracts, specialties, facilities or data defects.
10. For a credible new pattern, write an explicit scenario/rule proposal.
11. Backtest that proposed rule independently.
12. Deploy the new rule in shadow mode—not the research cluster itself.
```

### 5.6 Cluster profile output

Example:

```yaml
discovery_run_id: provider_cluster_2026_q2_v2
cluster_id: C17
entity_count: 12
stability_score: 0.82
estimated_associated_paid_aed: 4200000
distinguishing_features:
  - repeated_resubmission_rate: 4.8x peer median
  - diagnosis_changed_after_denial: 6.1x peer median
  - highest_level_code_share: 2.7x peer median
  - common_billing_vendor: true
known_explanation: none confirmed
analyst_assessment: candidate coordinated resubmission typology
recommended_next_step: draft PAY-08 subrule and conduct targeted audit
```

The amount is “associated paid value,” not confirmed exposure or savings.

### 5.7 Example of conversion into a rule

Discovery finds a stable group of clinics with this sequence:

```text
1. Submit moderate-level consultation.
2. Receive a specific denial.
3. Resubmit with a more severe diagnosis and enabling indicator.
4. Receive payment.
5. Use the same mutation sequence across many members.
```

The cluster itself should not be productionized. Instead, analysts define a new PAY-08 rule:

```text
IF original denial_code IN configured_edit_family
AND resubmission changes diagnosis_severity upward
AND enabling_indicator is newly added
AND payment changes from zero to positive
AND pattern repeats for provider >= configured_count
THEN create PAY-08 provider case
```

That rule is explainable, testable and governed. This conversion is the intended value of R04.

### 5.8 Evaluation

Evaluate clusters using:

- stability across resamples and adjacent periods;
- separation and compactness as secondary diagnostics;
- understandable distinguishing features;
- material entity count and associated value;
- analyst agreement that the pattern is coherent;
- proportion explained by known legitimate factors;
- audit yield from representative samples; and
- ability to convert the finding into a deterministic, statistical, network or document rule.

A mathematically clean cluster with no operational interpretation has no product value.

### 5.9 Production action

R04 must produce:

```text
RULE_DEVELOPMENT_CANDIDATE
```

It must not directly produce:

```text
REJECT
PREPAY_PEND
PROVIDER_SANCTION
FRAUD_CONFIRMED
```

Analysts may open a controlled research case to inspect representative claims, but the cluster membership alone must not become adverse evidence.

---

## 6. Implementation order

Implement the three controls in this order:

1. **Build transparent foundations:** peer grouping, robust statistics and ANL-01-R01/R02.
2. **CLN-01-R02:** only for one well-defined code family with a credible audited reference set.
3. **ANL-01-R03:** start with provider-month Isolation Forest in shadow mode and measure model-only lift.
4. **ANL-01-R04:** introduce as a quarterly analyst workflow after features and peer definitions are stable.

Do not build all three simultaneously. They depend on the same feature governance, review outcomes and time-correct data, and instability in those foundations will be mistaken for model insight.

---

## 7. Developer acceptance checklist

An `M` rule is not complete until all answers are “yes”:

- Is the business question stated without model terminology?
- Is the scored population and exclusion logic explicit?
- Were all features available at the actual scoring time?
- Are peer groups and minimum volumes defined?
- Is the training cutoff and time-based test period recorded?
- Is the simple non-model baseline implemented?
- Does the model demonstrate prospective value beyond that baseline?
- Can every result be explained in original business units?
- Are data-quality and known-change suppressions implemented?
- Is the output limited to the permitted non-automatic disposition?
- Are review outcomes captured using the standard taxonomy?
- Are performance, drift, alert volume and incremental value monitored?
- Can the exact historical result be reproduced from stored versions?
- Is there a kill switch and rollback path?

---

## 8. Summary

`CLN-01-R02` is a **claim-level expected coding model**. `ANL-01-R03` is an **entity-level anomaly detector that must prove additional operational value**. `ANL-01-R04` is an **offline discovery process used to design future explicit rules**.

The safest product principle is:

> Models identify where to look. Versioned payment, coding and clinical policies determine what is payable. Qualified reviewers determine whether the evidence supports error, waste, abuse or suspected fraud.
