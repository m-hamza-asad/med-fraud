# Wasiq Code Review

Reviewed on 2026-09-27: `../Wasiq - med_fraud/fwa-engine-uae`.

## Useful patterns adopted

- An explicit source adapter instead of treating the synthetic CSV as canonical input.
- Deterministic day-first date parsing and a reusable confirmed mapping profile.
- Strict isolation of synthetic labels from operational evaluator inputs.
- TPA-derived administrative network boundaries with visible provenance.
- Bounded graph rendering while retaining full-population counts and associated value.
- Aggregate-safe dataset profiling, immutable lineage, and explicit limitations.

## Useful future ideas

- Raw-row hashes for source-to-canonical reconciliation.
- Field-level missingness and population-status dashboards.
- Hierarchical provider peer fallback with robust statistics and empirical-Bayes shrinkage.
- Effective-dated, typed graph edges distinguishing observed from inferred relationships.

## Deliberately not copied

- Source-currency conversion: the user directed that the fixture amounts be labelled AED, so no historical INR-to-AED conversion was applied.
- Synthetic fraud labels, confidence values, supervised metrics, or model claims: these remain outside production evaluation and calibration.
- Any code whose semantics depend on fields absent from the local product contract. Ideas were adapted to this repository rather than copied wholesale.
