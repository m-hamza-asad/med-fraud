import csv
from pathlib import Path

from scripts.profile_dataset import profile_csv


def test_profile_is_aggregate_and_date_parsing_is_deterministic(tmp_path: Path):
    path = tmp_path / "fixture_synthetic.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["claim_id", "patient_id", "date_of_claim", "fraud_label"])
        writer.writeheader(); writer.writerow({"claim_id": "C-SECRET", "patient_id": "P-SECRET", "date_of_claim": "27/09/2026", "fraud_label": "1"})
    result = profile_csv(path)
    assert result["period_start"] == "2026-09-27"
    assert result["safety_status"] == "SYNTHETIC_FIXTURE_ONLY"
    assert "C-SECRET" not in str(result) and "P-SECRET" not in str(result)
