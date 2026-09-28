from __future__ import annotations

import csv
import io
import json
import time
import tracemalloc
from datetime import date
from decimal import Decimal

from reportlab.pdfgen.canvas import Canvas
from xlsxwriter import Workbook

from medfraud.evaluators import EvaluationContext, evaluate_rule
from medfraud.imports import validate_rows
from medfraud.rule_contracts import CONTRACTS, RuleContract


def set_path(data: dict, path: str, value: object) -> None:
    target = data
    parts = path.split(".")
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value


def fixture(contract: RuleContract) -> tuple[dict, dict]:
    facts: dict = {"claim": {"net_amount": "100"}, "exclusion": {key: False for key in contract.exclusions}}
    count = len(contract.required_fields); primitive = contract.primitive
    if primitive == "effective_date_range": values = ("2026-09-01", "2026-01-01", "2026-08-01", "active")
    elif primitive == "required_presence": values = (False,)
    elif primitive in {"reference_match", "compound_reference"}: values = ("observed", *(["expected"] * max(1, count - 1)))
    elif primitive == "duplicate_count": values = (2,)
    elif primitive == "arithmetic_balance": values = (100, 10, 10, 70) if count >= 4 else (50, 50, 90)
    elif primitive == "date_window": values = (10 if contract.rule_id in {"CLN-04-R01", "CLN-05-R02", "PHR-02-R01"} else 60,)
    elif primitive == "change_threshold": values = (200, 100, 100)
    elif primitive in {"peer_threshold", "graph_threshold"}: values = (100, *([100] * (count - 1)))
    else: values = (100, *([50] * (count - 1)))
    for index, field in enumerate(contract.required_fields):
        set_path(facts, field, values[min(index, len(values) - 1)])
    thresholds = {"duplicate_count": 1, "date_window": 30, "change_threshold": Decimal("1.5")}
    config = {item.key: item.default for item in contract.parameters if item.default is not None}
    config["threshold"] = thresholds.get(primitive, 50)
    return facts, config


analysis_date = date(2026, 9, 15)
rows = [{"source_claim_id": f"BENCH-{i:05}", "member_token": f"M-{i % 500:04}", "provider_token": f"P-{i % 50:03}",
         "network_id": f"N-{i % 5}", "claim_type": "outpatient", "service_date": "2026-09-01",
         "submitted_amount": "100.00", "net_amount": "90.00", "paid_amount": "80.00", "facts_json": "{}"} for i in range(10000)]
tracemalloc.start()
started = time.perf_counter(); normalized, issues = validate_rows(rows, "benchmark.csv", analysis_date); validation = time.perf_counter() - started
assert len(normalized) == 10000 and not [x for x in issues if x["severity"] == "error"]

started = time.perf_counter(); triggered = 0
for _ in range(1000):
    for contract in CONTRACTS.values():
        facts, config = fixture(contract)
        result = evaluate_rule(contract, EvaluationContext(analysis_date, date(2021, 9, 15), facts,
            frozenset(contract.required_datasets), config))
        assert result.status != "ERROR"; triggered += int(result.triggered)
evaluation = time.perf_counter() - started

graph_payload = {"nodes": [{"id": f"P-{i}"} for i in range(500)],
                 "edges": [{"source": f"P-{i % 500}", "target": f"P-{(i * 7 + 1) % 500}"} for i in range(2000)]}
started = time.perf_counter(); json.dumps(graph_payload); graph_seconds = time.perf_counter() - started

export_rows = normalized[:1000]
started = time.perf_counter(); stream = io.StringIO(); writer = csv.DictWriter(stream, fieldnames=list(export_rows[0])); writer.writeheader(); writer.writerows(export_rows); csv_seconds = time.perf_counter() - started
started = time.perf_counter(); output = io.BytesIO(); book = Workbook(output, {"in_memory": True}); sheet = book.add_worksheet("Claims")
for r, row in enumerate(export_rows): sheet.write_row(r, 0, [str(row[key]) for key in list(row)[:9]])
book.close(); xlsx_seconds = time.perf_counter() - started
started = time.perf_counter(); output = io.BytesIO(); pdf = Canvas(output); pdf.drawString(48, 800, f"Benchmark claims: {len(export_rows)}"); pdf.save(); pdf_seconds = time.perf_counter() - started
_, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()

print(json.dumps({"profile_validate_lines": 10000, "validation_seconds": round(validation, 4), "history_lines": 10000,
    "new_batch_lines": 1000, "structured_contract_evaluations": 149000, "triggered_fixture_results": triggered,
    "evaluation_seconds": round(evaluation, 4), "graph_nodes": 500, "graph_edges": 2000,
    "graph_serialization_seconds": round(graph_seconds, 4), "csv_export_seconds": round(csv_seconds, 4),
    "xlsx_export_seconds": round(xlsx_seconds, 4), "pdf_export_seconds": round(pdf_seconds, 4),
    "peak_memory_mb": round(peak / 1024 / 1024, 2),
    "note": "Deterministic canonical engineering fixtures; no supplied signals, synthetic scores, or fraud-performance claims."}, indent=2))
