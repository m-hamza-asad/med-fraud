# Independent UX Red-Team Review

Date: 2026-09-28  
Verdict at review start: **NOT USER-READY**

Three independent reviewers examined every route from the perspective of a non-technical payment-integrity analyst or administrator. The review covered rendered behavior, frontend and API contracts, accessibility, export provenance, and the active synthetic database.

## Release-blocking findings

1. **Claim explanations were not evidence-traceable.** The example `C0020397` displayed an imported 14-day readmission scalar but linked only the current claim. No earlier claim exists 14 days before it in the local data. A source indicator must not be presented as a verified readmission.
2. **Limited assessment could resemble a clean or complete result.** Claim and batch screens did not make it obvious that only a small subset of 149 controls produced results.
3. **Upload preview hid validation evidence.** Detailed issues returned by the API, including 858 warnings in the synthetic batch, were not visible before commit.
4. **Rule simulation could disagree with production evaluation.** It used a generic greater-than comparison, including for lower-bound rules such as readmission-window checks.
5. **Network accessibility claims exceeded the implementation.** The list promised an accessible edge table, but detail offered only the canvas graph.
6. **Report provenance claims differed across CSV, Excel and PDF.** The UI did not identify the selected batch/run/population or preview record counts.
7. **The “Local API connected” indicator was static.** It could claim connectivity while the API was unavailable.

## Screen-by-screen findings

| Screen | Primary usability risk | Required outcome |
|---|---|---|
| Login | No actionable local credential recovery | Explain where credentials came from and provide the exact local recovery route without defaults |
| Overview | Mixed evaluated/unevaluated value and weak run provenance | Reconciled populations, evaluated/flagged value, selected batch/run/date and synthetic-data warning |
| Claims | Search only covered the current page; technical reasons | Server-side search/filter/sort; plain reason with technical ID secondary; coverage counts |
| Claim detail | Codes and unitless numbers; no linked evidence | Plain-language why/comparison/limitations/action; linked records; honest limited-coverage warning |
| Providers | Broad all-provider fallback called sufficient | Label exploratory fallback, show comparability limitations and assessed/flagged/limited counts |
| Provider detail | Unlabelled per-claim bars and no claim table | Time aggregation, accessible table, explicit peer delta and linked contributing claims |
| Networks | Technical cards with insufficient context | Show scale, timeframe, shared-member reason and a task-led review CTA |
| Network detail | Unexplained HHI, broken node-only filters, no table | Plain concentration explanation, useful relationship filters, exact subset disclosure and accessible evidence table |
| Upload | No issue/mapping/row preview before commit | Five-step source/date/validate/evidence/commit workflow with warnings and mappings |
| Batch evaluation | Green completion despite limited coverage | Distinct assessed/flagged claims, trigger-event definition, missing-data causes and run detail |
| Rules catalogue | Machine terminology dominates | Plain purpose, stage, readiness, outcome and current-setting summary with useful filters |
| Rule detail | Raw paths/formulae primary; unsafe simulation/save flow | Plain purpose and trigger direction, coherent snapshot, faithful simulation, current value and history |
| Reports | No scope preview or consistent provenance | Choose population, preview counts, generate with consistent run/configuration metadata |
| Audit | Raw event codes and IDs; hidden details | Human action sentence, actor, target, outcome, before/after/version, filters and pagination |
| Shell/mobile | Static health, lost parent navigation, weak drawer behavior | Live health, breadcrumbs/route focus, nested active state, skip link and keyboard-safe drawer |

## Language standard

- Use **Review needed**, not an unexplained “signal” code, as the primary label.
- Use **No signal in the controls that could run** when coverage is limited.
- Describe value as **claim value associated with the review reason—not confirmed loss or recoverable value**.
- Translate dispositions such as `POSTPAY_AUDIT` to **Review after payment**.
- Keep rule IDs, reason codes, canonical fields and formulas behind progressive disclosure.
- Never state that an event occurred unless its supporting records are linked and time-correct.

## Comprehension exit test

A first-time analyst must be able to answer, without opening the rule catalogue:

1. Why does this item need review?
2. What exact records and comparison support it?
3. What could not be checked?
4. What does the monetary value mean—and not mean?
5. What should I do next?

