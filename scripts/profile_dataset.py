from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path


SENSITIVE_HINTS = {"patient", "member", "provider", "hospital", "agent", "name", "email", "phone", "address"}
OUTCOME_HINTS = {"fraud_label", "fraud_type", "fraud_confidence", "ground_truth"}
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y")


def parse_date(value: str):
    for pattern in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), pattern).date()
        except ValueError:
            pass
    return None


def profile_csv(path: Path) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        count = 0; dates = []
        for row in reader:
            count += 1
            for key in headers:
                if "date" in key.casefold() and row.get(key):
                    parsed = parse_date(str(row[key]))
                    if parsed: dates.append(parsed)
    lowered = {column.casefold() for column in headers}
    outcome = sorted(column for column in headers if any(hint in column.casefold() for hint in OUTCOME_HINTS))
    sensitive = sorted(column for column in headers if any(hint in column.casefold() for hint in SENSITIVE_HINTS))
    synthetic = "synthetic" in path.name.casefold() or bool(outcome)
    return {"file": path.name, "snapshot_hash": digest, "row_count": count, "column_count": len(headers),
            "columns": headers, "period_start": min(dates).isoformat() if dates else None,
            "period_end": max(dates).isoformat() if dates else None,
            "sensitive_columns": sensitive, "outcome_columns": outcome,
            "safety_status": "SYNTHETIC_FIXTURE_ONLY" if synthetic else "REQUIRES_MAPPING_CONFIRMATION",
            "mapping_status": "UNCONFIRMED", "limitations": [
                "Aggregate structural profile only; source row values were not emitted.",
                "Outcome-like columns are excluded from production rule logic and calibration.",
                "Real-data readiness requires user-confirmed source-to-canonical mappings and leakage-controlled holdout checks.",
            ], "contains_required_claim_key": "claim_id" in lowered or "source_claim_id" in lowered}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("path", type=Path); args = parser.parse_args()
    if args.path.suffix.casefold() != ".csv": raise SystemExit("Only CSV aggregate profiling is supported")
    print(json.dumps(profile_csv(args.path), indent=2))
