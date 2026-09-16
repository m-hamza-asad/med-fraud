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
    signals = {"ENT-01-R01": True, "PAY-01-R01": True, "PAY-06-R02": False, "CLN-04-R01": True, "NET-01-R01": True}
    rows = [
        ["DEMO-FLAG-001", "MEM-A17", "PRV-NORTH-04", "NET-DEMO-01", "outpatient", "2026-09-02", "1800.00", "1650.00", "1650.00", json.dumps({"available_datasets": ["coverage_period", "provider_network", "claim_history", "diagnosis", "claim_line"], "signals": signals, "exposures": {"PAY-01-R01": 825, "CLN-04-R01": 300}})],
        ["DEMO-CLEAN-001", "MEM-C22", "PRV-CENTRAL-02", "NET-DEMO-02", "dental", "2026-09-03", "420.00", "380.00", "380.00", json.dumps({"available_datasets": ["coverage_period", "provider_network", "claim_history", "diagnosis", "claim_line"], "signals": {k: False for k in signals}})],
        ["DEMO-PARTIAL-001", "MEM-P09", "PRV-EAST-07", "", "pharmacy", "2026-09-04", "5600.00", "5200.00", "0.00", json.dumps({"available_datasets": ["claim_line"], "signals": {"PAY-06-R02": False}})],
    ]
    with (target / "canonical-demo-claims.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle); writer.writerow(HEADERS); writer.writerows(rows)
    (target / "expected-results.json").write_text(json.dumps({"DEMO-FLAG-001": [k for k, v in signals.items() if v], "DEMO-CLEAN-001": [], "DEMO-PARTIAL-001": [], "notes": "No excluded or deferred control is expected to trigger."}, indent=2), encoding="utf-8")


def create_traceability() -> None:
    from medfraud.evaluators import REQUIRED_DATASET_BY_FAMILY
    from medfraud.registry import REGISTRY
    target = ROOT / "docs" / "rule-traceability.csv"
    fields = ["rule_id", "scenario_id", "name", "type", "execution_status", "evaluator", "required_datasets", "required_fields", "positive_test", "negative_test", "boundary_test", "missing_input_test", "effective_date_test", "exclusion_test", "ui_visibility", "reason_code", "notes"]
    with target.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for rule in REGISTRY:
            executable = rule["scope_state"] == "EXECUTABLE"
            family = rule["scenario_id"].split("-")[0]
            writer.writerow({"rule_id": rule["rule_id"], "scenario_id": rule["scenario_id"], "name": rule["rule_name"], "type": rule["type_expression"], "execution_status": rule["scope_state"], "evaluator": rule["evaluator"] or "", "required_datasets": REQUIRED_DATASET_BY_FAMILY.get(family, ""), "required_fields": "UNRESOLVED_IN_SOURCE", "positive_test": "test_evaluators.py" if executable else "N/A", "negative_test": "test_evaluators.py" if executable else "N/A", "boundary_test": "test_evaluators.py" if executable else "N/A", "missing_input_test": "test_evaluators.py" if executable else "N/A", "effective_date_test": "PENDING_POLICY_CONTRACT" if executable else "N/A", "exclusion_test": "PENDING_POLICY_CONTRACT" if executable else "N/A", "ui_visibility": "Rules registry", "reason_code": rule["reason_code"], "notes": "Raw trigger: " + rule["trigger_semantics_raw"]})
    summary = "# Rule Traceability\n\nGenerated from the validated 164-control registry. The machine-readable matrix is `docs/rule-traceability.csv`.\n\n| Scope | Count | Evaluated |\n|---|---:|---|\n| Structured executable | 149 | Structured-fact adapter; field-level policy unresolved |\n| Deferred document/text | 12 | No |\n| Excluded model | 3 | No |\n\nAll controls are visible. Required fields, effective-date fixtures, and exclusion fixtures remain explicitly marked pending where the catalogue does not define them; they are not silently counted as implemented.\n"
    (ROOT / "docs" / "RULE_TRACEABILITY.md").write_text(summary, encoding="utf-8")


def load_demo() -> None:
    from medfraud.database import engine
    from medfraud.imports import checksum, parse_rows, validate_rows
    from medfraud.models import Claim, ImportBatch, User
    data = (ROOT / "data" / "demo" / "canonical-demo-claims.csv").read_bytes()
    rows, issues = validate_rows(parse_rows("canonical-demo-claims.csv", data), "canonical-demo-claims.csv", date(2026, 9, 15))
    assert not [x for x in issues if x["severity"] == "error"]
    with Session(engine) as db:
        admin = db.query(User).filter_by(username="admin").one()
        batch = ImportBatch(checksum=checksum(data), filename="canonical-demo-claims.csv", profile="canonical", status="COMMITTED", row_count=len(rows), created_by=admin.id)
        db.add(batch); db.flush()
        for raw in rows:
            db.add(Claim(source_profile="canonical", source_claim_id=raw["source_claim_id"], member_token=raw["member_token"], provider_token=raw["provider_token"], network_id=raw.get("network_id") or None, claim_type=raw["claim_type"], service_date=raw["service_date"], submitted_amount=raw["submitted_amount"], net_amount=raw["net_amount"], paid_amount=raw["paid_amount"], facts_json=raw["facts_json"], original_json="{}", valid_from=raw["valid_from"], import_batch_id=batch.id))
        db.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--load-demo", action="store_true"); args = parser.parse_args()
    for profile in ("shafafiya", "eclaimlink", "canonical"): create_workbook(profile)
    create_csv_pack(); create_demo_csv(); create_traceability()
    if args.load_demo: load_demo()
    print("Generated three Excel templates, canonical CSV pack, and demo fixtures.")
