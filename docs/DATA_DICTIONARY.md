# Data Dictionary

Core persisted entities are `users`, `sessions`, `schema_migrations`, `import_batches`, `import_issues`, `import_previews`, `dataset_profiles`, `mapping_profiles`, `claims`, `claim_lines`, `canonical_providers`, `canonical_facts`, `canonical_relations`, `rules`, `rule_parameter_definitions`, `configuration_versions`, `threshold_recommendations`, `threshold_simulations`, `evaluation_runs`, `rule_evaluations`, `rule_evidence_references`, `provider_feature_snapshots`, `provider_relationships`, and `audit_events`.

Claims preserve profile, source key, source JSON, parsed structured facts, service date, tokenized member/provider/network identifiers, fixed-decimal amounts, validity, recorded time, version, and batch lineage. `canonical_facts` makes each evaluator input queryable by entity, dataset, field, typed value, effective period, source key, source, and version. `canonical_relations` stores typed, directed/undirected relationships with weight, associated amount, validity, provenance, and evidence. Preview rows are separate from committed operational claims.

Dates are ISO `YYYY-MM-DD`. Money is decimal with two stored fractional digits. Identifiers are opaque strings and must already be tokenized.

