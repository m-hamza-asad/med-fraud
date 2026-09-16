from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class EvaluationResult:
    status: str
    triggered: bool
    evidence: dict[str, Any]
    score: Decimal = Decimal("0")
    exposure: Decimal = Decimal("0")


REQUIRED_DATASET_BY_FAMILY = {
    "ENT": "coverage_period",
    "PAY": "claim_line",
    "CLN": "diagnosis",
    "PHR": "prescription",
    "DOC": "document_metadata",
    "NET": "provider_network",
    "ANL": "claim_history",
    "POL": "policy_enrollment",
}


def evaluate_catalogue_rule(rule: dict, claim_facts: dict, available_datasets: set[str]) -> EvaluationResult:
    """Evaluate the rule's explicit structured fact contract.

    Imports may supply a `signals` object containing observed, source-derived booleans keyed by
    catalogue rule ID. This contract is deterministic and auditable: absence is never treated as
    false. It is intentionally constrained to structured source facts and never runs model/text rules.
    """
    family = rule["scenario_id"].split("-")[0]
    required = REQUIRED_DATASET_BY_FAMILY[family]
    if required not in available_datasets:
        return EvaluationResult("DISABLED_MISSING_DATA", False, {"missing_dataset": required})
    signals = claim_facts.get("signals", {})
    if rule["rule_id"] not in signals:
        return EvaluationResult("NOT_APPLICABLE", False, {"source_fact": "not supplied"})
    observed = signals[rule["rule_id"]]
    if not isinstance(observed, bool):
        return EvaluationResult("ERROR", False, {"error": "structured signal must be boolean"})
    exposure = Decimal(str(claim_facts.get("exposures", {}).get(rule["rule_id"], 0))).quantize(Decimal("0.01"))
    evidence = {
        "observed": observed,
        "source_fact": f"signals.{rule['rule_id']}",
        "catalogue_trigger": rule["trigger_semantics_raw"],
        "exclusions_considered": rule["requirements_raw"],
        "source_units": claim_facts.get("units", {}).get(rule["rule_id"], "boolean"),
        "rule_version": rule["version"],
    }
    return EvaluationResult("TRIGGERED" if observed else "PASSED", observed, evidence,
                            Decimal("1") if observed else Decimal("0"), exposure if observed else Decimal("0"))


def parse_facts(raw: str) -> dict:
    try:
        value = json.loads(raw or "{}")
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}

