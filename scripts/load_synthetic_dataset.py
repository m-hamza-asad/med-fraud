from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from medfraud.database import engine
from medfraud.imports import checksum, commit_preview, map_synthetic_uae_rows, parse_rows, preview_payload, validate_rows
from medfraud.migrations import run_migrations
from medfraud.models import AuditEvent, DatasetProfile, ImportBatch, ImportIssue, ImportPreview, MappingProfile, User


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "demo" / "claims_demo_synthetic.csv"
ANALYSIS_DATE = date(2028, 4, 2)


def main() -> None:
    run_migrations()
    data = SOURCE.read_bytes(); digest = checksum(data)
    parsed = parse_rows(SOURCE.name, data); mapped, mapping_issues = map_synthetic_uae_rows(parsed)
    normalized, validation_issues = validate_rows(mapped, SOURCE.name, ANALYSIS_DATE)
    issues = mapping_issues + validation_issues
    errors = [item for item in issues if item["severity"] == "error"]
    if errors: raise SystemExit(f"Synthetic mapping blocked by {len(errors)} error(s): {errors[0]['message']}")
    with Session(engine) as db:
        existing = db.scalar(select(ImportBatch).where(ImportBatch.checksum == digest))
        if existing:
            print(json.dumps({"status": existing.status, "batch_id": existing.id, "rows": existing.row_count, "duplicate": True}))
            return
        admin = db.scalar(select(User).where(User.username == "admin"))
        if admin is None: raise SystemExit("Admin user is missing; run scripts/setup.ps1 first.")
        mapping = db.scalar(select(MappingProfile).where(MappingProfile.name == "synthetic_uae_v1"))
        if mapping is None:
            mapping = MappingProfile(name="synthetic_uae_v1", source_profile="synthetic_uae", schema_hash=digest[:32], confirmed=True,
                created_by=admin.id, mapping_json=json.dumps({"claim_id": "source_claim_id", "patient_id": "member_token",
                "hospital_id": "provider_token", "tpa": "network_id", "date_of_admission": "service_date",
                "claim_amount_requested_aed": "submitted_amount", "claim_amount_approved_aed": "net_amount",
                "labels": "held_out_not_evaluator_inputs"}))
            db.add(mapping); db.flush()
        batch = ImportBatch(checksum=digest, filename=SOURCE.name, profile="synthetic_uae", status="VALIDATED",
            row_count=len(normalized), error_count=0, warning_count=sum(item["severity"] == "warning" for item in issues), created_by=admin.id)
        db.add(batch); db.flush()
        for issue in issues:
            issue.update({"file": SOURCE.name, "sheet": None})
            db.add(ImportIssue(batch_id=batch.id, **issue))
        db.add(ImportPreview(batch_id=batch.id, analysis_date=ANALYSIS_DATE,
            normalized_rows_json=preview_payload(normalized), mapping_profile_id=mapping.id))
        service_dates = [row["service_date"] for row in normalized]
        db.add(DatasetProfile(import_batch_id=batch.id, dataset_name=SOURCE.name, snapshot_hash=digest,
            source_profile="synthetic_uae", safety_status="SYNTHETIC_FIXTURE_ONLY", mapping_status="CONFIRMED_SYNTHETIC_MAPPING",
            row_count=len(normalized), period_start=min(service_dates), period_end=max(service_dates),
            summary_json=json.dumps({"currency": "AED", "labels_used_for_evaluation": False}),
            limitations_json=json.dumps(["Synthetic engineering data; not evidence of fraud performance."])))
        db.flush(); created = commit_preview(db, batch)
        db.add(AuditEvent(event_type="SYNTHETIC_DATASET_COMMITTED", actor_user_id=admin.id, target_type="batch",
            target_id=str(batch.id), detail_json=json.dumps({"rows": created, "mapping": "synthetic_uae_v1", "labels_held_out": True})))
        db.commit()
        print(json.dumps({"status": batch.status, "batch_id": batch.id, "rows": created, "warnings": batch.warning_count,
                          "analysis_date": ANALYSIS_DATE.isoformat(), "labels_used_for_evaluation": False}))


if __name__ == "__main__": main()
