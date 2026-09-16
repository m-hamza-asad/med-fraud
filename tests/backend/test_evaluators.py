from decimal import Decimal

import pytest

from medfraud.evaluators import REQUIRED_DATASET_BY_FAMILY, evaluate_catalogue_rule
from medfraud.registry import REGISTRY


EXECUTABLE = [x for x in REGISTRY if x["scope_state"] == "EXECUTABLE"]


@pytest.mark.parametrize("rule", EXECUTABLE, ids=lambda x: x["rule_id"])
def test_positive_negative_boundary_and_missing_contract(rule):
    dataset = REQUIRED_DATASET_BY_FAMILY[rule["scenario_id"].split("-")[0]]
    positive = evaluate_catalogue_rule(rule, {"signals": {rule["rule_id"]: True}, "exposures": {rule["rule_id"]: "10.005"}}, {dataset})
    negative = evaluate_catalogue_rule(rule, {"signals": {rule["rule_id"]: False}}, {dataset})
    not_applicable = evaluate_catalogue_rule(rule, {"signals": {}}, {dataset})
    missing = evaluate_catalogue_rule(rule, {"signals": {rule["rule_id"]: True}}, set())
    assert (positive.status, positive.triggered, positive.exposure) == ("TRIGGERED", True, Decimal("10.00"))
    assert (negative.status, negative.triggered) == ("PASSED", False)
    assert not_applicable.status == "NOT_APPLICABLE"
    assert missing.status == "DISABLED_MISSING_DATA"
    assert positive.evidence["rule_version"] == "1.0"

