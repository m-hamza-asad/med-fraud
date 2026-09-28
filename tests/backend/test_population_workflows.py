from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from medfraud.database import Base
from medfraud.main import claims, export_rows, provider_detail, report
from medfraud.models import Claim, EvaluationRun, ImportBatch, RuleEvaluation, RuleRecord, User


def seed(db: Session):
    user = User(username="analyst", password_hash="x", role="analyst")
    db.add(user); db.flush()
    batch = ImportBatch(checksum="population", filename="population.csv", profile="canonical",
                        status="COMMITTED", row_count=2, created_by=user.id)
    db.add(batch); db.flush()
    rule = RuleRecord(rule_id="TEST-R01", scenario_id="TEST", name="Plain review reason",
                      type_expression="H", stage="POSTPAY", scope_state="EXECUTABLE",
                      operational_state="Live", reason_code="TEST_SIGNAL", metadata_json="{}")
    db.add(rule)
    first = Claim(source_profile="canonical", source_claim_id="C-ALPHA", member_token="M-1",
                  provider_token="P-1", network_id="N-1", claim_type="outpatient",
                  service_date=date(2026, 1, 2), submitted_amount=100, net_amount=90,
                  paid_amount=80, facts_json="{}", original_json="{}", valid_from=date(2026, 1, 2),
                  import_batch_id=batch.id)
    second = Claim(source_profile="canonical", source_claim_id="C-BETA", member_token="M-2",
                   provider_token="P-2", network_id="N-1", claim_type="outpatient",
                   service_date=date(2026, 2, 2), submitted_amount=200, net_amount=180,
                   paid_amount=160, facts_json="{}", original_json="{}", valid_from=date(2026, 2, 2),
                   import_batch_id=batch.id)
    db.add_all([first, second]); db.flush()
    run = EvaluationRun(batch_id=batch.id, analysis_date=date(2026, 3, 1), status="COMPLETED",
                        coverage="Partial", configuration_snapshot="[]", progress_json="{}",
                        created_by=user.id, created_at=datetime(2026, 3, 1))
    db.add(run); db.flush()
    db.add_all([
        RuleEvaluation(run_id=run.id, claim_id=first.id, rule_id=rule.rule_id, status="TRIGGERED",
                       triggered=True, reason_code=rule.reason_code, evidence_json="{}",
                       disposition="POSTPAY_AUDIT", score=1, exposure=10),
        RuleEvaluation(run_id=run.id, claim_id=second.id, rule_id=rule.rule_id,
                       status="DISABLED_MISSING_DATA", triggered=False, reason_code=rule.reason_code,
                       evidence_json="{}", disposition="MONITOR_ONLY", score=0, exposure=0),
    ])
    db.commit()
    return user, batch, run, first, second


def test_claim_filters_apply_to_full_server_population():
    engine = create_engine("sqlite:///:memory:"); Base.metadata.create_all(engine)
    with Session(engine) as db:
        user, batch, _, first, _ = seed(db)
        result = claims(decision="flagged", provider="P-1", batch_id=batch.id, q="alpha",
                        page=1, page_size=50, run_id=None, coverage=None, rule_id=None,
                        date_from=None, date_to=None, sort="net_amount", direction="desc",
                        db=db, _user=user)
        assert result["total"] == 1
        assert result["items"][0]["id"] == first.id
        assert result["items"][0]["primary_reason"] == "Plain review reason"


def test_scoped_export_matches_selected_batch_and_decision():
    engine = create_engine("sqlite:///:memory:"); Base.metadata.create_all(engine)
    with Session(engine) as db:
        _, batch, run, first, _ = seed(db)
        other = ImportBatch(checksum="other", filename="other.csv", profile="canonical",
                            status="COMMITTED", row_count=1, created_by=1)
        db.add(other); db.flush()
        db.add(Claim(source_profile="canonical", source_claim_id="C-OTHER", member_token="M-3",
                     provider_token="P-3", claim_type="outpatient", service_date=date(2026, 2, 3),
                     submitted_amount=50, net_amount=40, paid_amount=30, facts_json="{}",
                     original_json="{}", valid_from=date(2026, 2, 3), import_batch_id=other.id))
        db.commit()
        assert len(export_rows(db)) == 3
        rows = export_rows(db, batch_id=batch.id, run_id=run.id, decision="Flagged", provider="P-1")
        assert [row["claim_id"] for row in rows] == [first.source_claim_id]
        assert [row["claim_id"] for row in export_rows(db, batch_id=other.id)] == ["C-OTHER"]

        user = db.query(User).first()
        with pytest.raises(HTTPException) as caught:
            report("csv", batch_id=other.id, run_id=run.id, db=db, user=user)
        assert caught.value.status_code == 422


def test_provider_detail_uses_monthly_periods_and_assessment_counts():
    engine = create_engine("sqlite:///:memory:"); Base.metadata.create_all(engine)
    with Session(engine) as db:
        user, _, _, _, _ = seed(db)
        result = provider_detail("P-1", db=db, _user=user)
        assert result["metrics"]["assessed_claims"] == 1
        assert result["metrics"]["flagged_claims"] == 1
        assert result["trend"][0]["period"] == "2026-01"
        assert "exploratory" in result["peer"]["level_used"]
