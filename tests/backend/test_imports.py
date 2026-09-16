from datetime import date

from medfraud.imports import validate_rows


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

