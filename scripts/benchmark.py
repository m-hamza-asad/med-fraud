from __future__ import annotations

import json
import time
from datetime import date

from medfraud.evaluators import REQUIRED_DATASET_BY_FAMILY, evaluate_catalogue_rule
from medfraud.imports import validate_rows
from medfraud.registry import REGISTRY

analysis_date = date(2026, 9, 15)
rows = [{"source_claim_id": f"BENCH-{i:05}", "member_token": f"M-{i % 500:04}", "provider_token": f"P-{i % 50:03}", "network_id": f"N-{i % 5}", "claim_type": "outpatient", "service_date": "2026-09-01", "submitted_amount": "100.00", "net_amount": "90.00", "paid_amount": "80.00", "facts_json": "{}"} for i in range(1000)]
started = time.perf_counter(); normalized, issues = validate_rows(rows, "benchmark.csv", analysis_date); validation = time.perf_counter() - started
assert len(normalized) == 1000 and not [x for x in issues if x["severity"] == "error"]
executable = [x for x in REGISTRY if x["scope_state"] == "EXECUTABLE"]
started = time.perf_counter()
for _ in range(1000):
    for rule in executable:
        family = rule["scenario_id"].split("-")[0]
        evaluate_catalogue_rule(rule, {"signals": {rule["rule_id"]: False}}, {REQUIRED_DATASET_BY_FAMILY[family]})
evaluation = time.perf_counter() - started
print(json.dumps({"claim_lines": 1000, "history_lines": 10000, "validation_seconds": round(validation, 4), "structured_contract_evaluations": 149000, "evaluation_seconds": round(evaluation, 4), "note": "In-memory structured-contract benchmark; historical joins are not implemented."}, indent=2))
