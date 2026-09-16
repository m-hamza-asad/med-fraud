# Architecture

The local browser UI is React/TypeScript/Vite. It calls a versioned FastAPI service on localhost. SQLAlchemy stores immutable import batches, versioned claim facts, rule/configuration snapshots, evaluations, sessions, and audit events in SQLite. openpyxl/XlsxWriter and ReportLab generate local files; NetworkX and pandas are reserved for transparent graph/peer primitives.

Boundaries are organized under `apps/web`, `apps/api/medfraud`, `data`, `rules`, `scripts`, and `tests`. Model and document-content execution are intentionally absent. The registry holds 164 controls; only the 149 structured non-model rows may dispatch.

The current implementation has an important constraint: because the source catalogue omits rule-level populations, required fields, evidence fields, canonical reason codes, and resolved dispositions for most controls, structured imports may provide explicit `facts_json.signals.<rule_id>` booleans. Absence is `NOT_APPLICABLE`, and missing family datasets are `DISABLED_MISSING_DATA`; neither is treated as pass. This is deterministic scaffolding, not an approved rule-policy substitute.

