from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from medfraud.evaluators import EvaluationContext, evaluate_rule, parse_facts
from medfraud.rule_contracts import CONTRACTS, RuleContract


def _set(data: dict, path: str, value: object) -> None:
    target = data
    parts = path.split(".")
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value


def _configuration(contract: RuleContract) -> dict[str, object]:
    thresholds: dict[str, object] = {
        "duplicate_count": 1,
        "date_window": 30,
        "change_threshold": Decimal("1.5"),
        "numeric_threshold": 50,
        "peer_threshold": 50,
        "graph_threshold": 50,
    }
    values: dict[str, object] = {"threshold": thresholds.get(contract.primitive, 50)}
    for parameter in contract.parameters:
        if parameter.default is not None:
            values[parameter.key] = parameter.default
        elif parameter.key == "reference_value":
            values[parameter.key] = "expected"
        elif parameter.parameter_type == "integer":
            values[parameter.key] = 20
        elif parameter.key != "threshold":
            values[parameter.key] = 50
    return values


def _facts(contract: RuleContract, mode: str) -> dict:
    facts: dict = {"claim": {"net_amount": "100.00"}, "exclusion": {key: False for key in contract.exclusions}}
    fields = contract.required_fields
    primitive = contract.primitive
    if primitive == "effective_date_range":
        values = (
            ("2026-01-03", "2026-01-01", "2026-01-02")
            if mode == "positive"
            else ("2026-01-02", "2026-01-01", "2026-01-02")
        )
    elif primitive == "required_presence":
        values = (False if mode == "positive" else True,)
    elif primitive in {"reference_match", "compound_reference"}:
        values = tuple("observed" if index == 0 and mode == "positive" else "expected" for index in range(len(fields)))
    elif primitive == "duplicate_count":
        values = (2 if mode == "positive" else 1,)
    elif primitive == "arithmetic_balance":
        if contract.rule_id in {"PAY-06-R02", "PAY-07-R02"}:
            values = (100, 10, 10, 70 if mode == "positive" else 80)
        else:
            values = (50, 50, 90 if mode == "positive" else 100)
    elif primitive == "date_window":
        values = (10 if mode == "positive" and contract.rule_id in {"CLN-04-R01", "CLN-05-R02", "PHR-02-R01"} else 60 if mode == "positive" else 30,)
    elif primitive == "change_threshold":
        values = (200 if mode == "positive" else 150, 100, 100)
    elif primitive in {"peer_threshold", "graph_threshold"}:
        values = (100 if mode == "positive" else 50, *([100] * (len(fields) - 1)))
    else:
        values = (100 if mode == "positive" else 50, *([50] * (len(fields) - 1)))
    for index, field in enumerate(fields):
        _set(facts, field, values[min(index, len(values) - 1)])
    return facts


def _context(contract: RuleContract, facts: dict, configuration: dict | None = None) -> EvaluationContext:
    return EvaluationContext(
        analysis_date=date(2026, 9, 27),
        history_start=date(2021, 9, 27),
        facts=facts,
        available_datasets=frozenset(contract.required_datasets),
        configuration=configuration or _configuration(contract),
        configuration_versions={key: 1 for key in _configuration(contract)},
        reference_versions={dataset: "fixture-v1" for dataset in contract.required_datasets},
    )


@pytest.mark.parametrize("contract", CONTRACTS.values(), ids=lambda item: item.rule_id)
def test_all_executable_contracts_positive_negative_boundary_and_missing(contract: RuleContract) -> None:
    positive = evaluate_rule(contract, _context(contract, _facts(contract, "positive")))
    negative = evaluate_rule(contract, _context(contract, _facts(contract, "negative")))
    missing = evaluate_rule(
        contract,
        EvaluationContext(date(2026, 9, 27), date(2021, 9, 27), {}, frozenset()),
    )
    assert positive.status == "TRIGGERED", (contract.rule_id, positive.evidence)
    assert positive.triggered
    assert negative.status == "PASSED", (contract.rule_id, negative.evidence)
    assert not negative.triggered
    assert missing.status == "DISABLED_MISSING_DATA"
    assert positive.evidence["observed"] is not None
    assert positive.evidence["expected"] is not None
    assert positive.evidence["formula"] == contract.formula
    assert positive.evidence["configuration_versions"]
    assert positive.evidence["reference_versions"]


@pytest.mark.parametrize("contract", CONTRACTS.values(), ids=lambda item: item.rule_id)
def test_all_executable_contracts_respect_structured_exclusion(contract: RuleContract) -> None:
    facts = _facts(contract, "positive")
    _set(facts, f"exclusion.{contract.exclusions[0]}", True)
    result = evaluate_rule(contract, _context(contract, facts))
    assert result.status == "NOT_APPLICABLE"
    assert contract.exclusions[0] in result.evidence["active_exclusions"]


def test_signal_boolean_and_synthetic_label_are_removed_from_legacy_payload() -> None:
    parsed = parse_facts('{"signals":{"PAY-01-R01":true},"fraud_label":1,"fraud_confidence":0.99,"claim":{"net_amount":100}}')
    assert "signals" not in parsed
    assert "fraud_label" not in parsed
    assert "fraud_confidence" not in parsed
    assert parsed["claim"]["net_amount"] == 100


def test_objective_reprice_exposure_uses_calculated_variance() -> None:
    contract = CONTRACTS["PAY-06-R02"]
    result = evaluate_rule(contract, _context(contract, _facts(contract, "positive")))
    assert result.exposure == Decimal("10")

