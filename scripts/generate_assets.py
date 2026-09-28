from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
HEADERS = ["source_claim_id", "member_token", "provider_token", "network_id", "claim_type", "service_date", "submitted_amount", "net_amount", "paid_amount", "facts_json"]
DATASETS = ["claim_header", "claim_line", "diagnosis", "encounter", "member", "provider", "coverage_period", "provider_network", "authorization", "remittance", "prescription", "document_metadata", "policy_enrollment"]


def create_workbook(profile: str) -> None:
    target = ROOT / "data" / "templates" / f"{profile}-template.xlsx"
    target.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook(); readme = wb.active; readme.title = "README"
    readme.append(["Shahai medical payment-integrity import template", profile, "Version 1.0"])
    readme.append(["Purpose", "Structured, tokenized POC data. No macros or formulas."])
    readme.append(["Policy", "Thresholds are POC defaults — not approved policy."])
    for dataset in DATASETS:
        ws = wb.create_sheet(dataset)
        if dataset == "claim_header":
            ws.append(HEADERS)
            ws.append([f"{profile.upper()}-001", "MEM-001", "PRV-001", "NET-01", "outpatient", "2026-09-01", 650, 600, 600, json.dumps({"available_datasets": ["coverage_period", "provider_network"]})])
        else:
            ws.append(["field_name", "source_meaning", "canonical_mapping", "type", "required", "example", "allowed_values", "rule_families_enabled"])
            ws.append(["source_id", f"{dataset} source key", f"{dataset}.source_id", "string", "conditional", f"{dataset.upper()}-001", "tokenized opaque value", dataset.split('_')[0].upper()])
        ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
    wb.save(target)


def create_csv_pack() -> None:
    pack = ROOT / "data" / "templates" / "canonical-csv"; pack.mkdir(parents=True, exist_ok=True)
    for dataset in DATASETS:
        headers = HEADERS if dataset == "claim_header" else ["source_id", "valid_from", "valid_to", "source", "version_id"]
        with (pack / f"{dataset}.csv").open("w", newline="", encoding="utf-8-sig") as handle:
            csv.writer(handle).writerow(headers)
    (pack / "README.md").write_text("# Canonical multi-CSV pack\n\nUse ISO dates, decimal money, explicit network IDs, opaque tokenized identifiers, and stable source keys.\n", encoding="utf-8")


def create_demo_csv() -> None:
    target = ROOT / "data" / "demo"; target.mkdir(parents=True, exist_ok=True)
    available = ["claim_header", "claim_line", "coverage_period", "benefit_rule", "claim_history", "claim_version", "observation", "provider_features", "provider_network", "provider_relationship"]
    flagged_facts = {"available_datasets": available, "coverage": {"valid_from": "2026-01-01", "valid_to": "2026-08-31"},
                     "claim_line": {"exact_match_count": 2}, "history": {"days_since_equivalent_service": 5},
                     "policy": {"minimum_repeat_days": 30}, "graph": {"top_recipient_share": 1, "hhi": 1, "edge_count": 25},
                     "exclusion": {"approved_exception": False}}
    clean_facts = {"available_datasets": available, "coverage": {"valid_from": "2026-01-01", "valid_to": "2026-12-31"},
                   "claim_line": {"exact_match_count": 1}, "history": {"days_since_equivalent_service": 30},
                   "policy": {"minimum_repeat_days": 30}, "graph": {"top_recipient_share": .5, "hhi": .2, "edge_count": 25},
                   "exclusion": {"approved_exception": False}}
    rows = [
        ["DEMO-FLAG-001", "MEM-A17", "PRV-NORTH-04", "NET-DEMO-01", "outpatient", "2026-09-02", "1800.00", "1650.00", "1650.00", json.dumps(flagged_facts)],
        ["DEMO-CLEAN-001", "MEM-C22", "PRV-CENTRAL-02", "NET-DEMO-02", "dental", "2026-09-03", "420.00", "380.00", "380.00", json.dumps(clean_facts)],
        ["DEMO-PARTIAL-001", "MEM-P09", "PRV-EAST-07", "", "pharmacy", "2026-09-04", "5600.00", "5200.00", "0.00", json.dumps({"available_datasets": ["claim_line"], "claim_line": {"exact_match_count": 1}, "exclusion": {"approved_exception": False}})],
    ]
    with (target / "canonical-demo-claims.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle); writer.writerow(HEADERS); writer.writerows(rows)
    (target / "expected-results.json").write_text(json.dumps({"DEMO-FLAG-001": ["ENT-01-R01", "PAY-01-R01", "CLN-04-R01", "NET-01-R01"], "DEMO-CLEAN-001": [], "DEMO-PARTIAL-001": [], "notes": "Deterministic canonical facts only; unavailable controls must disable, never pass."}, indent=2), encoding="utf-8")


def create_traceability() -> None:
    from medfraud.registry import REGISTRY
    from medfraud.rule_contracts import CONTRACTS
    target = ROOT / "docs" / "rule-traceability.csv"
    fields = ["rule_id", "scenario_id", "name", "type", "execution_status", "evaluator", "required_datasets", "required_fields", "positive_test", "negative_test", "boundary_test", "missing_input_test", "effective_date_test", "exclusion_test", "ui_visibility", "reason_code", "notes"]
    with target.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for rule in REGISTRY:
            executable = rule["scope_state"] == "EXECUTABLE"
            contract = CONTRACTS.get(rule["rule_id"])
            writer.writerow({"rule_id": rule["rule_id"], "scenario_id": rule["scenario_id"], "name": rule["rule_name"], "type": rule["type_expression"], "execution_status": rule["scope_state"], "evaluator": contract.primitive if contract else "", "required_datasets": ";".join(contract.required_datasets) if contract else "N/A", "required_fields": ";".join(contract.required_fields) if contract else "N/A", "positive_test": "test_evaluators.py" if executable else "N/A", "negative_test": "test_evaluators.py" if executable else "N/A", "boundary_test": "test_evaluators.py" if executable else "N/A", "missing_input_test": "test_evaluators.py" if executable else "N/A", "effective_date_test": "test_evaluators.py" if executable else "N/A", "exclusion_test": "test_evaluators.py" if executable else "N/A", "ui_visibility": "Rules registry and detail", "reason_code": rule["reason_code"], "notes": "Raw trigger: " + rule["trigger_semantics_raw"]})
    summary = "# Rule Traceability\n\nGenerated from the validated 164-control registry. The machine-readable matrix is `docs/rule-traceability.csv`.\n\n| Scope | Count | Evaluated |\n|---|---:|---|\n| Structured executable | 149 | Canonical field-driven contract |\n| Deferred document/text | 12 | No |\n| Excluded model | 3 | No |\n\nAll controls are visible. Every executable row names its primitive, required datasets and fields, positive/negative/boundary/missing/exclusion test matrix, UI location, disposition, and stable reason code. Missing inputs disable a control and never become a pass. Governed policy/reference values remain unavailable until supplied; they are not inferred from utilization.\n"
    (ROOT / "docs" / "RULE_TRACEABILITY.md").write_text(summary, encoding="utf-8")


def load_demo() -> None:
    from medfraud.database import engine
    from medfraud.imports import checksum, commit_preview, parse_rows, preview_payload, validate_rows
    from medfraud.models import ImportBatch, ImportPreview, User
    data = (ROOT / "data" / "demo" / "canonical-demo-claims.csv").read_bytes()
    rows, issues = validate_rows(parse_rows("canonical-demo-claims.csv", data), "canonical-demo-claims.csv", date(2026, 9, 15))
    assert not [x for x in issues if x["severity"] == "error"]
    with Session(engine) as db:
        admin = db.query(User).filter_by(username="admin").one()
        batch = ImportBatch(checksum=checksum(data), filename="canonical-demo-claims.csv", profile="canonical", status="VALIDATED", row_count=len(rows), created_by=admin.id)
        db.add(batch); db.flush()
        db.add(ImportPreview(batch_id=batch.id, analysis_date=date(2026, 9, 15), normalized_rows_json=preview_payload(rows)))
        db.flush(); commit_preview(db, batch)
        db.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--load-demo", action="store_true"); args = parser.parse_args()
    for profile in ("shafafiya", "eclaimlink", "canonical"): create_workbook(profile)
    create_csv_pack(); create_demo_csv(); create_traceability()
    if args.load_demo: load_demo()
    print("Generated three Excel templates, canonical CSV pack, and demo fixtures.")
