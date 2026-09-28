import asyncio
import csv
import io
import json
from datetime import date, datetime
from decimal import Decimal

from pypdf import PdfReader
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from medfraud.database import Base
from medfraud.main import export_rows, network_export, report
from medfraud.models import Claim, EvaluationRun, ImportBatch, RuleEvaluation, RuleRecord, User


def test_export_reconciles_assessment_coverage_and_exposure():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="a", password_hash="x", role="admin"); db.add(user); db.flush()
        batch = ImportBatch(checksum="b" * 64, filename="x.csv", profile="canonical", status="COMMITTED",
                            row_count=1, created_by=user.id); db.add(batch); db.flush()
        claim = Claim(source_profile="canonical", source_claim_id="C-1", member_token="M-1", provider_token="P-1",
                      claim_type="outpatient", service_date=date(2026, 1, 1), submitted_amount=100,
                      net_amount=90, paid_amount=80, facts_json="{}", original_json="{}", valid_from=date(2026, 1, 1),
                      import_batch_id=batch.id); db.add(claim)
        rule = RuleRecord(rule_id="PAY-06-R02", scenario_id="PAY-06", name="Arithmetic", type_expression="H",
                          stage="PREPAY", scope_state="EXECUTABLE", operational_state="Live", reason_code="RC-1",
                          metadata_json="{}"); db.add(rule); db.flush()
        run = EvaluationRun(batch_id=batch.id, analysis_date=date(2026, 9, 27), status="COMPLETED", coverage="Complete",
                            configuration_snapshot="[]", created_by=user.id, created_at=datetime(2026, 9, 27)); db.add(run); db.flush()
        db.add(RuleEvaluation(run_id=run.id, claim_id=claim.id, rule_id=rule.rule_id, status="TRIGGERED", triggered=True,
                              reason_code=rule.reason_code, evidence_json="{}", disposition="REPRICE", score=1,
                              exposure=Decimal("10.00")))
        db.commit()
        rows = export_rows(db)
        assert rows[0]["assessment"] == "Flagged"
        assert rows[0]["estimated_exposure"] == "10.00"
        assert rows[0]["triggered_rules"] == "PAY-06-R02"


def test_export_does_not_label_unevaluated_claim_clean():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        batch = ImportBatch(checksum="waiting", filename="waiting.csv", profile="canonical",
                            status="COMMITTED", row_count=1, created_by=1)
        db.add(batch)
        db.flush()
        db.add(Claim(source_profile="canonical", source_claim_id="waiting-1", version_id="v1",
                     member_token="member", provider_token="provider", claim_type="professional",
                     service_date=date(2026, 1, 1), submitted_amount=Decimal("50"),
                     net_amount=Decimal("50"), paid_amount=Decimal("0"), facts_json="{}",
                     original_json="{}", valid_from=date(2026, 1, 1), source="test",
                     import_batch_id=batch.id))
        db.commit()

        rows = export_rows(db)

        assert rows[0]["assessment"] == "Not evaluated"
        assert rows[0]["coverage"] == "Not evaluated"
        assert rows[0]["evaluation_run_id"] == ""


def _response_bytes(response) -> bytes:
    async def collect() -> bytes:
        chunks = []
        async for chunk in response.body_iterator:
            chunks.append(chunk.encode() if isinstance(chunk, str) else chunk)
        return b"".join(chunks)
    return asyncio.run(collect())


def test_zero_row_csv_contains_actual_provenance_values():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="a", password_hash="x", role="admin"); db.add(user); db.commit()
        response = report("csv", decision="Flagged", db=db, user=user)
        rows = list(csv.DictReader(io.StringIO(_response_bytes(response).decode())))
        assert rows[0]["record_type"] == "metadata"
        assert rows[0]["exported_by_role"] == "admin"
        assert "decision Flagged" in rows[0]["export_scope"]
        assert rows[0]["catalogue_scope"] == "164 total; 149 executable; 12 deferred; 3 excluded"


def test_network_export_uses_source_claim_evidence_and_boundary():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="a", password_hash="x", role="analyst"); db.add(user); db.flush()
        batch = ImportBatch(checksum="network", filename="network.csv", profile="canonical",
                            status="COMMITTED", row_count=1, created_by=user.id); db.add(batch); db.flush()
        db.add(Claim(source_profile="canonical", source_claim_id="SOURCE-C-1", member_token="M-1",
            provider_token="P-1", network_id="N-1", claim_type="outpatient", service_date=date(2026, 1, 1),
            submitted_amount=100, net_amount=90, paid_amount=80, facts_json="{}", original_json="{}",
            valid_from=date(2026, 1, 1), import_batch_id=batch.id)); db.commit()
        response = network_export("N-1", db=db, _user=user)
        rows = list(csv.DictReader(io.StringIO(_response_bytes(response).decode())))
        assert rows[0]["source_claim_id"] == "SOURCE-C-1"
        assert rows[0]["network_id"] == "N-1"
        assert rows[0]["generated_at_utc"].endswith("Z")
        assert "not evidence" in rows[0]["interpretation_boundary"]


def test_multi_run_pdf_carries_the_same_complete_snapshot_manifest_as_csv():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="a", password_hash="x", role="admin"); db.add(user); db.flush()
        for index in (1, 2):
            batch = ImportBatch(checksum=f"batch-{index}", filename=f"batch-{index}.csv", profile="canonical",
                                status="COMMITTED", row_count=1, created_by=user.id)
            db.add(batch); db.flush()
            db.add(Claim(source_profile="canonical", source_claim_id=f"C-{index}", member_token=f"M-{index}",
                provider_token=f"P-{index}", claim_type="outpatient", service_date=date(2026, 1, index),
                submitted_amount=100, net_amount=90, paid_amount=80, facts_json="{}", original_json="{}",
                valid_from=date(2026, 1, index), import_batch_id=batch.id))
            db.add(EvaluationRun(batch_id=batch.id, analysis_date=date(2026, 2, 1), status="COMPLETED",
                coverage="Partial", configuration_snapshot=json.dumps([{"rule_id": f"R-{index}", "value": index}]),
                progress_json="{}", created_by=user.id))
        db.commit()
        csv_response = report("csv", db=db, user=user)
        csv_rows = list(csv.DictReader(io.StringIO(_response_bytes(csv_response).decode())))
        manifest = csv_rows[0]["run_configuration_manifest_hash"]
        assert len(manifest) == 64
        pdf_response = report("pdf", db=db, user=user)
        pdf_text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(_response_bytes(pdf_response))).pages)
        assert manifest in pdf_text
