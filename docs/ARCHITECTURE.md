# Architecture

The local browser UI is React/TypeScript/Vite. It calls a versioned FastAPI service on localhost. SQLAlchemy stores immutable import batches, versioned claim facts, rule/configuration snapshots, evaluations, sessions, and audit events in SQLite. openpyxl/XlsxWriter and ReportLab generate local files; NetworkX and pandas are reserved for transparent graph/peer primitives.

Boundaries are organized under `apps/web`, `apps/api/medfraud`, `data`, `rules`, `scripts`, and `tests`. Model and document-content execution are intentionally absent. The registry holds 164 controls; only the 149 structured non-model rows may dispatch.

The evaluation boundary is contract-driven. Each of 149 executable controls declares a subject, population, datasets, canonical fields, primitive, typed parameters, exclusions, missing-data behavior, evidence contract, disposition, and impact method. The reusable primitives evaluate normalized facts and versioned configuration; supplied rule booleans and synthetic outcome labels are removed at import and parse boundaries. Missing data is `DISABLED_MISSING_DATA`, sparse peers are `INSUFFICIENT_DATA`, and a structured legitimate exclusion is `NOT_APPLICABLE`.

Validation persists only an `ImportPreview`; an explicit CSRF-protected commit transaction creates claims and flattened `CanonicalFact` lineage. Additive schema revisions preserve prior claims, users, evaluations, and audit events. Provider analytics expose support-aware fallback peers. Network graphs stay inside supplied `network_id` boundaries and retain claim IDs on every displayed edge.

