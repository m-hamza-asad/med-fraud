from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


PROFILES = {"canonical", "shafafiya", "eclaimlink"}
REQUIRED = {"source_claim_id", "member_token", "provider_token", "claim_type", "service_date", "submitted_amount", "net_amount"}


def checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_filename(name: str) -> str:
    return Path(name).name.replace("\x00", "")[:255]


def _csv_rows(data: bytes) -> list[dict[str, Any]]:
    text = data.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def _xlsx_rows(data: bytes) -> list[dict[str, Any]]:
    workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=False, keep_links=False)
    if "claim_header" not in workbook.sheetnames:
        raise ValueError("Missing required sheet: claim_header")
    sheet = workbook["claim_header"]
    headers = [str(v) if v is not None else "" for v in next(sheet.iter_rows(values_only=True))]
    return [dict(zip(headers, row, strict=False)) for row in sheet.iter_rows(values_only=True)]


def parse_rows(filename: str, data: bytes) -> list[dict[str, Any]]:
    lower = filename.lower()
    if lower.endswith(".csv"):
        return _csv_rows(data)
    if lower.endswith(".xlsx"):
        return _xlsx_rows(data)
    raise ValueError("Only .csv and .xlsx files are accepted")


def validate_rows(rows: list[dict[str, Any]], filename: str, analysis_date: date) -> tuple[list[dict], list[dict]]:
    issues: list[dict] = []
    normalized: list[dict] = []
    if not rows:
        return [], [{"severity": "error", "row_number": None, "column_name": None, "code": "EMPTY_FILE", "message": "No claim rows were found", "guidance": "Add a header row and at least one claim."}]
    missing = REQUIRED - set(rows[0])
    for col in sorted(missing):
        issues.append({"severity": "error", "row_number": 1, "column_name": col, "code": "MISSING_COLUMN", "message": f"Required column '{col}' is missing", "guidance": "Use the matching downloadable template."})
    if missing:
        return [], issues
    seen: set[str] = set()
    cutoff = date(analysis_date.year - 5, analysis_date.month, min(analysis_date.day, 28))
    for offset, raw in enumerate(rows, start=2):
        try:
            service = raw["service_date"] if isinstance(raw["service_date"], date) else date.fromisoformat(str(raw["service_date"])[:10])
            submitted = Decimal(str(raw["submitted_amount"])).quantize(Decimal("0.01"))
            net = Decimal(str(raw["net_amount"])).quantize(Decimal("0.01"))
            paid = Decimal(str(raw.get("paid_amount") or 0)).quantize(Decimal("0.01"))
            source_id = str(raw["source_claim_id"]).strip()
            if source_id in seen:
                raise ValueError("duplicate source claim ID")
            seen.add(source_id)
            if service > analysis_date:
                raise ValueError("service date is after the analysis date")
            if service < cutoff:
                issues.append({"severity": "warning", "row_number": offset, "column_name": "service_date", "code": "OUTSIDE_WINDOW", "message": "Claim is older than the five-year analysis window", "guidance": "Keep for history only or choose a later analysis date."})
            if net > submitted:
                raise ValueError("net amount exceeds submitted amount")
            facts_raw = raw.get("facts_json") or "{}"
            facts = facts_raw if isinstance(facts_raw, dict) else json.loads(str(facts_raw))
            normalized.append({**raw, "source_claim_id": source_id, "service_date": service, "submitted_amount": submitted, "net_amount": net, "paid_amount": paid, "facts_json": json.dumps(facts), "valid_from": service})
        except (ValueError, TypeError, InvalidOperation, json.JSONDecodeError) as exc:
            issues.append({"severity": "error", "row_number": offset, "column_name": None, "code": "INVALID_ROW", "message": str(exc), "guidance": "Correct the row values and validate again."})
    for issue in issues:
        issue.update({"file": filename, "sheet": "claim_header" if filename.lower().endswith(".xlsx") else None})
    return normalized, issues

