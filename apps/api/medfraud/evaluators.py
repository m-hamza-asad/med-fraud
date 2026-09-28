from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .rule_contracts import CONTRACTS, RuleContract


@dataclass(frozen=True)
class EvaluationContext:
    analysis_date: date
    history_start: date
    facts: dict[str, Any]
    available_datasets: frozenset[str]
    configuration: dict[str, Any] = field(default_factory=dict)
    configuration_versions: dict[str, int] = field(default_factory=dict)
    reference_versions: dict[str, str] = field(default_factory=dict)
    evidence_records: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class EvaluationResult:
    status: str
    triggered: bool
    evidence: dict[str, Any]
    score: Decimal = Decimal("0")
    exposure: Decimal = Decimal("0")
    disposition: str = "MONITOR_ONLY"


def _get(data: dict[str, Any], path: str) -> Any:
    value: Any = data
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _parameter(contract: RuleContract, context: EvaluationContext, key: str) -> Any:
    if key in context.configuration:
        return context.configuration[key]
    definition = next((item for item in contract.parameters if item.key == key), None)
    return definition.default if definition else None


def _missing_result(contract: RuleContract, missing_datasets: list[str], missing_fields: list[str]) -> EvaluationResult:
    return EvaluationResult(
        status="DISABLED_MISSING_DATA",
        triggered=False,
        evidence={
            "rule_id": contract.rule_id,
            "what_happened": "The control could not be evaluated because required canonical data is unavailable.",
            "missing_datasets": missing_datasets,
            "missing_fields": missing_fields,
            "missing_data_effect": "No clean conclusion is permitted for this control.",
            "next_verification": "Load or map the listed source data and run a new evaluation.",
        },
        disposition=contract.disposition,
    )


def _comparison(contract: RuleContract, context: EvaluationContext, values: list[Any]) -> tuple[bool, Any, Any, str, Decimal | None]:
    primitive = contract.primitive
    threshold = _parameter(contract, context, "threshold")
    if primitive == "effective_date_range":
        service, valid_from, valid_to = map(_date, values[:3])
        if not service or not valid_from or not valid_to:
            raise ValueError("effective dates must be valid ISO dates")
        return not (valid_from <= service <= valid_to), service.isoformat(), f"{valid_from.isoformat()} to {valid_to.isoformat()}", "outside", None

    if primitive == "required_presence":
        observed = values[0]
        present = observed not in (None, "", False, 0, [], {})
        return not present, observed, "required record present", "is missing", None

    if primitive in {"reference_match", "compound_reference"}:
        observed = values[0]
        expected = values[1] if len(values) > 1 else _parameter(contract, context, "reference_value")
        if expected is None:
            raise LookupError("governed reference value is unavailable")
        return observed != expected, observed, expected, "does not equal", None

    if primitive == "duplicate_count":
        observed = _decimal(values[0])
        expected = _decimal(threshold if threshold is not None else 1)
        if observed is None or expected is None:
            raise ValueError("duplicate count must be numeric")
        return observed > expected, observed, expected, ">", observed - expected

    if primitive == "arithmetic_balance":
        numbers = [_decimal(value) for value in values]
        if any(value is None for value in numbers):
            raise ValueError("arithmetic inputs must be numeric")
        assert all(value is not None for value in numbers)
        if contract.rule_id in {"PAY-06-R02", "PAY-07-R02"} and len(numbers) >= 4:
            calculated = numbers[0] - numbers[1] - numbers[2]
            expected = numbers[3]
        else:
            calculated = sum(numbers[:-1], Decimal("0"))
            expected = numbers[-1]
        tolerance = _decimal(_parameter(contract, context, "tolerance")) or Decimal("0.01")
        variance = abs(calculated - expected)
        return variance > tolerance, calculated, expected, f"absolute variance > {tolerance}", variance

    if primitive == "date_window":
        observed = _decimal(values[0])
        if observed is None and len(values) >= 2:
            left, right = _date(values[0]), _date(values[1])
            if left and right:
                observed = Decimal(str((left - right).days))
        configured = next(
            (_parameter(contract, context, key) for key in ("window", "readmit_days", "allowed_overlap_days", "reporting_tolerance", "threshold") if _parameter(contract, context, key) is not None),
            None,
        )
        expected = _decimal(configured)
        if observed is None or expected is None:
            raise LookupError("time-window configuration is unavailable")
        lower_bound_trigger = contract.rule_id in {"CLN-04-R01", "CLN-05-R02", "PHR-02-R01"}
        triggered = observed < expected if lower_bound_trigger else observed > expected
        operator = "<" if lower_bound_trigger else ">"
        return triggered, observed, expected, operator, abs(observed - expected)

    observed = _decimal(values[0])
    if observed is None:
        raise ValueError("observed metric must be numeric")

    if primitive == "change_threshold":
        baseline = _decimal(values[1]) if len(values) > 1 else None
        support_count = _decimal(values[2]) if len(values) > 2 else None
        minimum_support = _decimal(_parameter(contract, context, "minimum_support")) or Decimal("20")
        if support_count is not None and support_count < minimum_support:
            raise ArithmeticError(f"minimum support {minimum_support} not met")
        if baseline in (None, Decimal("0")):
            raise ArithmeticError("stable non-zero baseline is required")
        observed_metric = observed / baseline
    else:
        observed_metric = observed

    support = next((_decimal(value) for value in reversed(values[1:]) if _decimal(value) is not None), None)
    if primitive in {"peer_threshold", "graph_threshold"}:
        minimum_support = _decimal(_parameter(contract, context, "minimum_support")) or Decimal("20")
        if support is None or support < minimum_support:
            raise ArithmeticError(f"minimum support {minimum_support} not met")

    expected = _decimal(threshold)
    if expected is None and primitive in {"peer_threshold", "change_threshold", "graph_threshold"}:
        expected = _decimal(_parameter(contract, context, "trigger_percentile"))
    if expected is None:
        expected = _decimal(_get(context.facts, "peer.threshold_value"))
    if expected is None:
        expected = _decimal(_get(context.facts, "graph.threshold_value"))
    if expected is None:
        raise LookupError("configured or calibrated trigger value is unavailable")
    return observed_metric > expected, observed_metric, expected, ">", observed_metric - expected


def evaluate_rule(contract: RuleContract, context: EvaluationContext) -> EvaluationResult:
    missing_datasets = sorted(set(contract.required_datasets) - set(context.available_datasets))
    values = [_get(context.facts, path) for path in contract.required_fields]
    missing_fields = [path for path, value in zip(contract.required_fields, values, strict=True) if value is None]
    if missing_datasets or missing_fields:
        return _missing_result(contract, missing_datasets, missing_fields)

    checked_exclusions = [key for key in contract.exclusions if _get(context.facts, f"exclusion.{key}") is not None]
    active_exclusions = [key for key in contract.exclusions if _get(context.facts, f"exclusion.{key}") is True]
    unavailable_exclusions = [key for key in contract.exclusions if key not in checked_exclusions]
    if active_exclusions:
        return EvaluationResult(
            status="NOT_APPLICABLE",
            triggered=False,
            evidence={
                "rule_id": contract.rule_id,
                "what_happened": "A structured legitimate exclusion applies.",
                "exclusions_checked": checked_exclusions,
                "active_exclusions": active_exclusions,
                "exclusions_unavailable": unavailable_exclusions,
                "next_verification": "Verify the exclusion source and effective date.",
            },
            disposition=contract.disposition,
        )

    try:
        triggered, observed, expected, operator, variance = _comparison(contract, context, values)
    except LookupError as exc:
        return _missing_result(contract, [], [str(exc)])
    except ArithmeticError as exc:
        return EvaluationResult(
            status="INSUFFICIENT_DATA",
            triggered=False,
            evidence={
                "rule_id": contract.rule_id,
                "what_happened": "The available population is insufficient for a stable comparison.",
                "data_support": "unavailable",
                "limitation": str(exc),
                "next_verification": "Load more completed history or use an approved broader peer group.",
            },
            disposition=contract.disposition,
        )
    except (TypeError, ValueError) as exc:
        return EvaluationResult(
            status="ERROR",
            triggered=False,
            evidence={"rule_id": contract.rule_id, "safe_message": str(exc)},
            disposition=contract.disposition,
        )

    associated = _decimal(_get(context.facts, "claim.net_amount")) or Decimal("0")
    exposure = Decimal("0")
    if triggered and contract.impact_method == "reprice_difference" and variance is not None:
        exposure = max(Decimal("0"), variance)
    evidence = {
        "rule_id": contract.rule_id,
        "what_happened": contract.description,
        "trigger_explanation": contract.trigger_criterion,
        "observed": str(observed),
        "expected": str(expected),
        "operator": operator,
        "variance": str(variance) if variance is not None else None,
        "formula": contract.formula,
        "evidence_records": list(context.evidence_records),
        "exclusions_checked": checked_exclusions,
        "exclusions_unavailable": unavailable_exclusions,
        "associated_amount": str(associated),
        "estimated_exposure": str(exposure),
        "exposure_method": contract.impact_method,
        "next_verification": "Review the linked canonical records and confirm any unavailable exclusions.",
        "configuration_versions": context.configuration_versions,
        "reference_versions": context.reference_versions,
        "evidence_strength": contract.evidence_strength,
    }
    return EvaluationResult(
        status="TRIGGERED" if triggered else "PASSED",
        triggered=triggered,
        evidence=evidence,
        score=Decimal("1") if triggered else Decimal("0"),
        exposure=exposure,
        disposition=contract.disposition,
    )


def evaluate_catalogue_rule(
    rule: dict[str, Any],
    claim_facts: dict[str, Any],
    available_datasets: set[str],
    configuration: dict[str, Any] | None = None,
    *,
    analysis_date: date | None = None,
) -> EvaluationResult:
    """Compatibility entry point backed by canonical fields, never supplied rule signals."""
    contract = CONTRACTS[rule["rule_id"]]
    current_date = analysis_date or date.today()
    context = EvaluationContext(
        analysis_date=current_date,
        history_start=date(current_date.year - 5, current_date.month, min(current_date.day, 28)),
        facts=claim_facts,
        available_datasets=frozenset(available_datasets),
        configuration=configuration or {},
    )
    return evaluate_rule(contract, context)


def parse_facts(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
        if not isinstance(value, dict):
            return {}
        value.pop("signals", None)
        value.pop("fraud_label", None)
        value.pop("fraud_confidence", None)
        return value
    except json.JSONDecodeError:
        return {}

