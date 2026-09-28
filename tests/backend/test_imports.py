from datetime import date

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from medfraud.database import Base
from medfraud.imports import BLOCKED_LOGIC_FIELDS, SYNTHETIC_LABEL_FIELDS, commit_preview, map_synthetic_uae_rows, preview_payload, validate_rows
from medfraud.models import CanonicalFact, Claim, ImportBatch, ImportPreview, User


def row(**changes):
    base = {"source_claim_id": "C-1", "member_token": "M-1", "provider_token": "P-1", "claim_type": "outpatient", "service_date": "2026-09-01", "submitted_amount": "100.00", "net_amount": "90.00", "paid_amount": "80.00", "facts_json": "{}"}
    return {**base, **changes}


def test_five_year_boundaries_and_money():
    normalized, issues = validate_rows([row(service_date="2021-09-15")], "x.csv", date(2026, 9, 15))
    assert normalized and not [x for x in issues if x["severity"] == "error"]
    _, issues = validate_rows([row(service_date="2020-09-14")], "x.csv", date(2026, 9, 15))
    assert [x for x in issues if x["code"] == "OUTSIDE_WINDOW"]


def test_invalid_amount_is_blocking():
    normalized, issues = validate_rows([row(net_amount="101.00")], "x.csv", date(2026, 9, 15))
    assert not normalized
    assert [x for x in issues if x["severity"] == "error"]


def test_synthetic_uae_mapping_is_day_first_aed_and_holds_labels_out():
    source = {"claim_id": "C1", "patient_id": "M1", "hospital_id": "P1", "date_of_admission": "02/01/2023",
              "date_of_discharge": "05/01/2023", "date_of_claim": "10/01/2023", "length_of_stay_days": "3",
              "claim_amount_requested_aed": "120", "claim_amount_approved_aed": "100", "tpa": "TPA A",
              "days_since_policy_start": "9", "fraud_label": "1", "fraud_type": "test", "fraud_confidence": ".9",
              "ground_truth_source": "synthetic"}
    mapped, issues = map_synthetic_uae_rows([source])
    assert not issues and len(mapped) == 1
    claim = mapped[0]; facts = __import__("json").loads(claim["facts_json"])
    assert claim["service_date"] == "2023-01-02"
    assert claim["submitted_amount"] == "120" and claim["net_amount"] == "100" and claim["paid_amount"] == "0"
    assert claim["network_id"] == "TPA A" and facts["coverage"]["valid_from"] == "2023-01-01"
    assert facts["mapping"]["currency"] == "AED"
    assert not (SYNTHETIC_LABEL_FIELDS & set(facts))


def test_synthetic_approved_above_requested_is_preserved_as_anomaly_warning():
    synthetic = row(submitted_amount="100", net_amount="110", facts_json='{"mapping":{"profile":"synthetic_uae_v1"}}')
    normalized, issues = validate_rows([synthetic], "synthetic.csv", date(2026, 9, 15))
    assert len(normalized) == 1
    assert [item for item in issues if item["code"] == "APPROVED_EXCEEDS_REQUESTED"]
    assert not [item for item in issues if item["severity"] == "error"]


def test_preview_does_not_create_claims_and_commit_is_atomic_and_idempotent():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    normalized, issues = validate_rows(
        [row(facts_json='{"diagnosis":{"primary":"A01"},"signals":{"PAY-01-R01":true},"fraud_label":1}')],
        "safe.csv", date(2026, 9, 15),
    )
    assert not issues
    with Session(engine) as db:
        user = User(username="owner", password_hash="x", role="Admin")
        db.add(user); db.flush()
        batch = ImportBatch(checksum="a" * 64, filename="safe.csv", profile="canonical", status="VALIDATED",
                            row_count=1, error_count=0, warning_count=0, created_by=user.id)
        db.add(batch); db.flush()
        db.add(ImportPreview(batch_id=batch.id, analysis_date=date(2026, 9, 15), normalized_rows_json=preview_payload(normalized)))
        db.commit()
        assert db.scalar(select(func.count()).select_from(Claim)) == 0
        assert commit_preview(db, batch) == 1
        db.commit()
        assert db.scalar(select(func.count()).select_from(Claim)) == 1
        assert db.scalar(select(func.count()).select_from(CanonicalFact)) > 0
        claim = db.scalar(select(Claim))
        assert claim is not None
        assert not (BLOCKED_LOGIC_FIELDS & set(__import__("json").loads(claim.facts_json)))
        assert commit_preview(db, batch) == 0
        assert db.scalar(select(func.count()).select_from(Claim)) == 1

