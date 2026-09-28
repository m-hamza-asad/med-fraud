import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from medfraud.database import Base
from medfraud.main import ConfigBody, _evaluation_presentation, _linked_readmission_claims, configure, simulate_configuration
from medfraud.models import (Claim, ConfigurationVersion, EvaluationRun, ImportBatch,
                             RuleEvaluation, RuleParameterDefinition, RuleRecord, User)
from medfraud.rule_contracts import CONTRACTS


def _claim(claim_id: int, source_id: str, service_date: date, diagnosis: str) -> Claim:
    return Claim(
        id=claim_id, source_profile="synthetic_uae", source_claim_id=source_id,
        member_token="member-1", provider_token="provider-1", claim_type="inpatient",
        service_date=service_date, submitted_amount=Decimal("100"), net_amount=Decimal("90"),
        paid_amount=Decimal("90"), facts_json=json.dumps({"diagnosis": {"primary_code": diagnosis},
            "encounter": {"admission_date": service_date.isoformat(),
                          "discharge_date": (service_date + timedelta(days=2)).isoformat()}}),
        original_json="{}", valid_from=service_date, source="test", import_batch_id=1,
    )


def test_readmission_link_requires_an_earlier_matching_diagnosis() -> None:
    same_day = _claim(1, "same-day", date(2026, 1, 1), "A01")
    duplicate = _claim(2, "duplicate", date(2026, 1, 1), "A01")
    unrelated = _claim(3, "unrelated", date(2026, 1, 10), "B02")
    later_match = _claim(4, "later-match", date(2026, 1, 20), "A01")

    links = _linked_readmission_claims([same_day, duplicate, unrelated, later_match])

    assert 2 not in links
    assert 3 not in links
    assert links[4].source_claim_id == "duplicate"


def test_plain_readmission_explanation_discloses_unlinked_source_indicator() -> None:
    evaluation = RuleEvaluation(
        run_id=1, claim_id=1, rule_id="CLN-05-R02", status="TRIGGERED", triggered=True,
        reason_code="CLN_05_R02_SIGNAL", evidence_json="{}", disposition="POSTPAY_AUDIT",
        score=Decimal("1"), exposure=Decimal("0"),
    )
    evidence = {"observed": "14", "expected": "30", "operator": "<",
                "exclusions_unavailable": ["approved_exception"]}

    result = _evaluation_presentation(evaluation, CONTRACTS[evaluation.rule_id], evidence)

    assert result["headline"] == "Possible same/related readmission within the review window"
    assert result["comparison"] == "14 days is inside the configured 30-day review window."
    assert result["action"] == "Review after payment"
    assert result["linked_claim"] is None
    assert any("not linked" in limitation for limitation in result["limitations"])


def test_lower_bound_simulation_replays_production_comparison_direction() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="admin", password_hash="x", role="admin")
        db.add(user); db.flush()
        batch = ImportBatch(checksum="simulation", filename="claims.csv", profile="canonical",
                            status="COMMITTED", row_count=2, created_by=user.id)
        db.add(batch); db.flush()
        available = ["claim_header", "encounter", "diagnosis", "claim_history"]
        first = _claim(1, "first", date(2026, 1, 1), "A01")
        second = _claim(2, "second", date(2026, 1, 11), "A01")
        for claim in (first, second):
            claim.import_batch_id = batch.id
            facts = json.loads(claim.facts_json)
            facts["available_datasets"] = available
            claim.facts_json = json.dumps(facts)
            db.add(claim)
        run = EvaluationRun(batch_id=batch.id, analysis_date=date(2026, 2, 1), status="COMPLETED",
                            coverage="Partial", configuration_snapshot="[]", progress_json="{}",
                            created_by=user.id)
        db.add(run); db.commit()

        result = simulate_configuration("CLN-05-R02", ConfigBody(
            parameter="readmit_days", value=5, unit="days",
            effective_at=datetime(2026, 2, 2, tzinfo=timezone.utc),
            source="Approved simulation test rationale",
        ), db=db, user=user)

        assert result["baseline_triggered"] == 1
        assert result["would_trigger"] == 0
        assert result["removed_claims"] == 1
        assert result["added_claims"] == 0


def test_simulation_rejects_a_stale_persisted_baseline() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="admin", password_hash="x", role="admin")
        db.add(user); db.flush()
        batch = ImportBatch(checksum="stale-simulation", filename="claims.csv", profile="canonical",
                            status="COMMITTED", row_count=2, created_by=user.id)
        db.add(batch); db.flush()
        for claim in (_claim(1, "first", date(2026, 1, 1), "A01"),
                      _claim(2, "second", date(2026, 1, 11), "A01")):
            claim.import_batch_id = batch.id
            facts = json.loads(claim.facts_json)
            facts["available_datasets"] = ["claim_header", "encounter", "diagnosis", "claim_history"]
            claim.facts_json = json.dumps(facts)
            db.add(claim)
        run = EvaluationRun(batch_id=batch.id, analysis_date=date(2026, 2, 1), status="COMPLETED",
                            coverage="Complete", configuration_snapshot="[]", progress_json="{}",
                            created_by=user.id)
        db.add(run); db.flush()
        db.add(RuleEvaluation(run_id=run.id, claim_id=1, rule_id="CLN-05-R02", status="TRIGGERED",
                              triggered=True, reason_code="CLN_05_R02_SIGNAL", evidence_json="{}",
                              disposition="POSTPAY_AUDIT", score=1, exposure=0))
        db.commit()

        with pytest.raises(HTTPException) as caught:
            simulate_configuration("CLN-05-R02", ConfigBody(
                parameter="readmit_days", value=5, unit="days",
                effective_at=datetime(2026, 2, 2, tzinfo=timezone.utc),
            ), db=db, user=user)
        assert caught.value.status_code == 409
        assert "no longer reproduces" in caught.value.detail


def test_configuration_versions_must_be_scheduled_in_order() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(username="admin", password_hash="x", role="admin")
        rule = RuleRecord(rule_id="TEST-R01", scenario_id="TEST", name="Test rule",
                          type_expression="H", stage="POSTPAY", scope_state="EXECUTABLE",
                          operational_state="Live", reason_code="TEST_SIGNAL", metadata_json="{}")
        definition = RuleParameterDefinition(rule_id=rule.rule_id, parameter_key="threshold",
            display_label="Threshold", description="Test threshold", parameter_type="number", unit="count",
            bounds_json=json.dumps({"minimum": 0, "maximum": 100}), provenance_class="LOCAL_CONFIG",
            edit_authority="ADMIN_EDITABLE", default_value_json="10", version=1,
            source="Test definition", rationale="Test-only governed parameter")
        db.add_all([user, rule, definition]); db.flush()
        latest_at = datetime.utcnow() + timedelta(days=10)
        db.add(ConfigurationVersion(rule_id=rule.rule_id, parameter="threshold", value_json="10",
            unit="count", valid_from=latest_at, version=1, changed_by=user.id,
            label="First", source="Approved first configuration"))
        db.commit()

        with pytest.raises(HTTPException) as caught:
            configure(rule.rule_id, ConfigBody(parameter="threshold", value=20, unit="count",
                effective_at=latest_at - timedelta(days=1), source="Approved later decision"), db=db, user=user)
        assert caught.value.status_code == 422
        assert "latest scheduled version" in caught.value.detail
