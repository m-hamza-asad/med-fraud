from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from medfraud.database import Base
from medfraud.main import overview
from medfraud.models import Claim, EvaluationRun, ImportBatch, RuleEvaluation, User


def test_overview_keeps_claims_without_completed_run_unevaluated() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="analyst", password_hash="x", role="analyst")
        db.add(user)
        db.flush()
        batch = ImportBatch(
            checksum="overview-batch", filename="claims.csv", profile="canonical",
            status="COMMITTED", row_count=2, created_by=user.id,
        )
        db.add(batch)
        db.flush()
        for source_id, amount in (("evaluated", "100"), ("waiting", "250")):
            db.add(Claim(
                source_profile="canonical", source_claim_id=source_id,
                member_token=f"member-{source_id}", provider_token="provider-1",
                claim_type="professional", service_date=date(2026, 1, 1),
                submitted_amount=Decimal(amount), net_amount=Decimal(amount),
                paid_amount=Decimal(amount), facts_json="{}", original_json="{}",
                valid_from=date(2026, 1, 1), source="test", import_batch_id=batch.id,
            ))
        db.commit()

        result = overview(db=db, _user=user)

        assert result["total_claims"] == 2
        assert result["assessed_claims"] == 0
        assert result["no_flag_claims"] == 0
        assert result["unevaluated_claims"] == 2


def test_overview_uses_only_latest_completed_batch_run() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="analyst", password_hash="x", role="analyst")
        db.add(user)
        db.flush()
        batch = ImportBatch(
            checksum="completed-batch", filename="claims.csv", profile="canonical",
            status="COMMITTED", row_count=1, created_by=user.id,
        )
        db.add(batch)
        db.flush()
        claim = Claim(
            source_profile="canonical", source_claim_id="flagged", member_token="member-1",
            provider_token="provider-1", claim_type="professional",
            service_date=date(2026, 1, 1), submitted_amount=Decimal("100"),
            net_amount=Decimal("100"), paid_amount=Decimal("100"), facts_json="{}",
            original_json="{}", valid_from=date(2026, 1, 1), source="test",
            import_batch_id=batch.id,
        )
        db.add(claim)
        db.flush()
        run = EvaluationRun(
            batch_id=batch.id, analysis_date=date(2026, 1, 2), status="COMPLETED",
            coverage="Complete", configuration_snapshot="{}", progress_json="{}",
            created_by=user.id,
        )
        db.add(run)
        db.flush()
        db.add(RuleEvaluation(
            run_id=run.id, claim_id=claim.id, rule_id="CLN-01-R01", status="TRIGGERED",
            triggered=True, reason_code="TEST_SIGNAL", evidence_json="{}",
            disposition="MONITOR_ONLY", score=Decimal("1"), exposure=Decimal("100"),
        ))
        db.commit()

        result = overview(db=db, _user=user)

        assert result["assessed_claims"] == 1
        assert result["flagged_claims"] == 1
        assert result["no_flag_claims"] == 0
        assert result["unevaluated_claims"] == 0
        assert result["priority_claims"][0]["claim_id"] == "flagged"
