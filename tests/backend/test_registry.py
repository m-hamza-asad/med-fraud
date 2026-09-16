from medfraud.registry import DEFERRED_IDS, MODEL_IDS, REGISTRY, validate_registry


def test_registry_exact_accounting():
    validate_registry(REGISTRY)
    assert len(REGISTRY) == 164
    assert len({x["rule_id"] for x in REGISTRY}) == 164
    assert sum(x["scope_state"] == "EXECUTABLE" for x in REGISTRY) == 149
    assert {x["rule_id"] for x in REGISTRY if x["scope_state"] == "DEFERRED_DOCUMENT"} == DEFERRED_IDS
    assert {x["rule_id"] for x in REGISTRY if x["scope_state"] == "EXCLUDED_MODEL"} == MODEL_IDS


def test_only_executable_controls_have_evaluators():
    for rule in REGISTRY:
        assert bool(rule["evaluator"]) == (rule["scope_state"] == "EXECUTABLE")

