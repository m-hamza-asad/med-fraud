# Data Dictionary

Core persisted entities are `users`, `sessions`, `import_batches`, `import_issues`, `claims`, `claim_lines`, `rules`, `configuration_versions`, `evaluation_runs`, `rule_evaluations`, and `audit_events`.

Claims preserve profile, source key, source JSON, parsed structured facts, service date, tokenized member/provider/network identifiers, fixed-decimal amounts, validity, recorded time, version, and batch lineage. Template sheets expose the broader canonical dataset boundary: diagnoses, encounters, members, providers, coverage, provider networks, authorizations, remittances, prescriptions, document metadata, and policy enrollment.

Dates are ISO `YYYY-MM-DD`. Money is decimal with two stored fractional digits. Identifiers are opaque strings and must already be tokenized.

