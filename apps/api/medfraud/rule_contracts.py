from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from .registry import REGISTRY


PROVENANCE_CLASSES = {
    "POLICY_REFERENCE",
    "EMPIRICAL_DISTRIBUTION",
    "OPERATIONAL_CAPACITY",
    "TECHNICAL_INVARIANT",
    "USER_DEFINED",
}


@dataclass(frozen=True)
class ParameterContract:
    key: str
    label: str
    description: str
    parameter_type: str
    unit: str | None
    default: Any
    minimum: float | int | None
    maximum: float | int | None
    allowed_values: tuple[str, ...]
    provenance: str
    edit_authority: str
    recommendation_eligible: bool
    required: bool = True
    scope: str = "global"


@dataclass(frozen=True)
class RuleContract:
    rule_id: str
    scenario_id: str
    name: str
    description: str
    scheme_explanation: str
    subject: str
    population: str
    required_datasets: tuple[str, ...]
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    primitive: str
    formula: str
    trigger_criterion: str
    parameters: tuple[ParameterContract, ...]
    exclusions: tuple[str, ...]
    missing_data_behavior: str
    disposition: str
    evidence_strength: str
    evidence_fields: tuple[str, ...]
    comparison_fields: tuple[str, ...]
    impact_method: str
    reason_template: str
    data_readiness: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SCENARIO_DATASETS: dict[str, tuple[str, ...]] = {
    "ENT-01": ("claim_header", "coverage_period", "benefit_rule"),
    "ENT-02": ("claim_header", "member", "encounter", "claim_history"),
    "ENT-03": ("claim_line", "provider", "provider_status"),
    "ENT-04": ("claim_line", "provider", "encounter", "claim_history"),
    "ENT-05": ("claim_header", "claim_line", "encounter", "provider_status"),
    "ENT-06": ("claim_line", "encounter", "provider", "provider_network"),
    "PAY-01": ("claim_header", "claim_line", "claim_history", "claim_version"),
    "PAY-02": ("claim_line", "claim_history", "package_reference"),
    "PAY-03": ("claim_line", "code_reference", "encounter"),
    "PAY-04": ("claim_line", "authorization", "authorization_line"),
    "PAY-05": ("claim_line", "code_reference", "observation"),
    "PAY-06": ("claim_header", "claim_line", "tariff_reference"),
    "PAY-07": ("claim_header", "claim_line", "benefit_rule", "remittance"),
    "PAY-08": ("claim_header", "claim_line", "claim_version", "remittance"),
    "PAY-09": ("claim_line", "diagnosis", "code_reference"),
    "PAY-10": ("claim_header", "coverage_period", "remittance"),
    "PAY-11": ("claim_header", "remittance", "adjudicator_event"),
    "PAY-12": ("claim_header", "remittance", "recovery_event"),
    "CLN-01": ("claim_line", "diagnosis", "encounter", "provider_features"),
    "CLN-02": ("claim_line", "diagnosis", "encounter", "provider_features"),
    "CLN-03": ("claim_line", "diagnosis", "encounter", "code_reference"),
    "CLN-04": ("claim_line", "claim_history", "observation", "provider_features"),
    "CLN-05": ("claim_header", "encounter", "diagnosis", "claim_history"),
    "CLN-06": ("claim_line", "encounter", "observation", "provider_features"),
    "CLN-07": ("claim_line", "encounter", "provider_capacity", "provider_features"),
    "CLN-08": ("claim_line", "diagnosis", "observation", "provider_network"),
    "PHR-01": ("claim_line", "prescription", "authorization", "dispense"),
    "PHR-02": ("claim_line", "prescription", "dispense", "claim_history"),
    "PHR-03": ("claim_line", "prescription", "diagnosis", "provider_features"),
    "PHR-04": ("prescription", "dispense", "provider_network", "provider_features"),
    "PHR-05": ("claim_line", "authorization", "device_inventory", "encounter"),
    "DOC-01": ("claim_line", "document_metadata"),
    "DOC-02": ("claim_line", "document_metadata"),
    "NET-01": ("claim_header", "provider_network", "provider_relationship"),
    "NET-02": ("claim_header", "provider_network", "provider_relationship"),
    "NET-03": ("claim_header", "provider_network", "provider_relationship"),
    "NET-04": ("claim_header", "policy_enrollment", "provider_relationship"),
    "ANL-01": ("claim_history", "provider_features", "peer_baseline"),
    "POL-01": ("claim_header", "coverage_period", "policy_enrollment"),
}


SUBJECT_BY_FAMILY = {
    "ENT": "claim",
    "PAY": "claim_line",
    "CLN": "claim_line",
    "PHR": "pharmacy_product",
    "DOC": "claim",
    "NET": "network",
    "ANL": "provider",
    "POL": "policy_member",
}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")


def _disposition(raw: str, type_expression: str) -> str:
    text = raw.casefold()
    if "return" in text:
        return "RETURN"
    if "reprice" in text and "pend" not in text:
        return "REPRICE"
    if "reject" in text and "pend" not in text and type_expression == "H":
        return "REJECT"
    if "pend" in text or "prepay" in text or "clinical review" in text or "coding review" in text:
        return "PREPAY_PEND"
    if "siu" in text or "high-priority" in text or "escalate" in text:
        return "SIU_LEAD"
    if "education" in text:
        return "PROVIDER_EDUCATION"
    if any(word in text for word in ("audit", "recovery", "case", "sample", "review")):
        return "POSTPAY_AUDIT"
    return "MONITOR_ONLY"


def _exclusions(requirements: str) -> tuple[str, ...]:
    text = requirements.casefold()
    keys: list[str] = []
    for needle, key in (
        ("emergency", "emergency_exception"),
        ("newborn", "newborn_exception"),
        ("transfer", "transfer_exception"),
        ("ownership", "known_ownership"),
        ("corporate", "known_corporate_relationship"),
        ("narrow network", "narrow_network"),
        ("centre", "centre_of_excellence"),
        ("partial fill", "partial_fill"),
        ("chronic", "chronic_care_pathway"),
        ("rare disease", "rare_disease_pathway"),
        ("approved", "approved_exception"),
        ("data latency", "source_latency"),
        ("campaign", "known_campaign"),
        ("contract", "known_contract_change"),
        ("merger", "known_ownership_change"),
    ):
        if needle in text and key not in keys:
            keys.append(key)
    return tuple(keys or ["approved_exception"])


def _primitive(item: dict[str, Any]) -> str:
    overrides = {
        "ENT-01-R01": "effective_date_range",
        "PAY-04-R02": "effective_date_range",
        "PAY-06-R02": "arithmetic_balance",
        "PAY-07-R02": "arithmetic_balance",
        "PAY-10-R02": "arithmetic_balance",
    }
    if item["rule_id"] in overrides:
        return overrides[item["rule_id"]]
    name = item["rule_name"].casefold()
    trigger = item["trigger_semantics_raw"].casefold()
    combined = f"{name} {trigger}"
    if item["scenario_id"] == "PAY-01" or "duplicate" in combined or "reuse" in name:
        return "duplicate_count"
    if "arithmetic" in combined:
        return "arithmetic_balance"
    if any(word in combined for word in ("after service", "post-mortem", "inside", "window", "interval", "refill overlap", "readmission")):
        return "date_window"
    if any(word in combined for word in ("missing", "absent", "lacks", "no qualified", "no result", "no meaningful")):
        return "required_presence"
    if any(word in combined for word in ("mismatch", "conflict", "invalid", "inactive", "prohibited", "not covered", "violation", "incompatibility")):
        return "reference_match"
    if any(t in item["types"] for t in ("N",)):
        return "graph_threshold"
    if any(t in item["types"] for t in ("S",)):
        if any(word in combined for word in ("change", "shift", "spike", "burst", "rapid", "discontinuity")):
            return "change_threshold"
        return "peer_threshold"
    if any(word in combined for word in ("exceed", "excess", "maximum", "above", "outside", "overlap", "concurrent")):
        return "numeric_threshold"
    return "compound_reference"


def _fields(item: dict[str, Any], primitive: str) -> tuple[str, ...]:
    dataset = SCENARIO_DATASETS[item["scenario_id"]][0]
    metric = _slug(item["rule_name"])
    overrides: dict[str, tuple[str, ...]] = {
        "ENT-01-R01": ("claim.service_date", "coverage.valid_from", "coverage.valid_to"),
        "ENT-01-R02": ("benefit.covered",),
        "ENT-01-R03": ("benefit.paid_or_authorized_ytd", "claim.requested_payable", "benefit.limit"),
        "ENT-01-R04": ("provider.network_id", "coverage.network_id", "referral.present"),
        "ENT-02-R02": ("encounter.service_start", "member.confirmed_death_date"),
        "ENT-02-R03": ("member.overlapping_encounter_count", "member.travel_speed_kph"),
        "PAY-01-R01": ("claim_line.exact_match_count",),
        "PAY-01-R02": ("claim_line.near_match_count", "claim_line.match_age_days"),
        "PAY-01-R03": ("episode.component_match_count",),
        "PAY-01-R04": ("claim.cross_payer_paid_match_count",),
        "PAY-03-R03": ("claim_line.units", "policy.maximum_units"),
        "PAY-03-R04": ("claim_line.units", "claim_line.service_minutes", "policy.minutes_per_unit"),
        "PAY-04-R01": ("authorization.required", "authorization.present"),
        "PAY-04-R02": ("claim.service_date", "authorization.valid_from", "authorization.valid_to", "authorization.status"),
        "PAY-04-R04": ("authorization.consumed_units", "claim_line.units", "authorization.approved_units"),
        "PAY-06-R01": ("claim_line.submitted_unit_price", "tariff.allowed_unit_price"),
        "PAY-06-R02": ("claim.gross_amount", "claim.valid_discount", "claim.patient_share", "claim.net_amount"),
        "PAY-07-R01": ("claim.patient_share", "benefit.expected_patient_share"),
        "PAY-07-R02": ("claim.gross_amount", "claim.valid_discount", "claim.patient_share", "claim.net_amount"),
        "PAY-10-R02": ("claim.total_payer_payments", "claim.patient_liability", "tariff.allowable_charge"),
        "CLN-04-R01": ("history.days_since_equivalent_service", "policy.minimum_repeat_days"),
        "CLN-05-R01": ("encounter.length_of_stay_days", "peer.expected_los_low", "peer.expected_los_high"),
        "CLN-05-R02": ("history.readmission_gap_days",),
        "PHR-02-R01": ("prescription.remaining_supply_days",),
        "PHR-03-R01": ("prescription.claimed_dose", "policy.minimum_dose", "policy.maximum_dose"),
        "NET-01-R01": ("graph.top_recipient_share", "graph.hhi", "graph.edge_count"),
        "NET-01-R02": ("graph.reciprocity", "graph.opportunity_count"),
        "NET-02-R02": ("graph.density", "graph.external_flow_ratio", "graph.node_count"),
        "ANL-01-R01": ("provider.robust_peer_composite", "peer.entity_count"),
        "ANL-01-R02": ("provider.current_period_value", "provider.baseline_value", "provider.history_periods"),
    }
    if item["rule_id"] in overrides:
        return overrides[item["rule_id"]]
    if primitive == "required_presence":
        return (f"{dataset}.{metric}_present",)
    if primitive == "reference_match":
        return (f"{dataset}.{metric}_observed", f"reference.{metric}_expected")
    if primitive == "arithmetic_balance":
        return ("claim.amount_component_a", "claim.amount_component_b", "claim.amount_expected_total")
    if primitive == "date_window":
        return (f"{dataset}.{metric}_days",)
    if primitive == "duplicate_count":
        return (f"{dataset}.{metric}_match_count",)
    if primitive == "graph_threshold":
        return (f"graph.{metric}", "graph.support_count")
    if primitive in {"peer_threshold", "change_threshold"}:
        return (f"features.{metric}", "peer.entity_count", "features.denominator")
    if primitive == "numeric_threshold":
        return (f"{dataset}.{metric}",)
    return (f"{dataset}.{metric}_observed", f"reference.{metric}_expected")


def _parameter(key: str, item: dict[str, Any], primitive: str) -> ParameterContract:
    key_l = key.casefold()
    if key_l in {"window", "readmit_days", "allowed_overlap_days", "reporting_tolerance"}:
        return ParameterContract(key, key.replace("_", " ").title(), "Effective comparison window.", "duration", "days", 30, 0, 3650, (), "USER_DEFINED", "ADMIN_EDITABLE", False)
    if key_l in {"max_attempts", "max_concurrency", "minimum_support"}:
        return ParameterContract(key, key.replace("_", " ").title(), "Minimum or maximum count used by the trigger.", "integer", "count", 3 if key_l != "minimum_support" else 20, 1, 100000, (), "EMPIRICAL_DISTRIBUTION" if key_l == "minimum_support" else "USER_DEFINED", "ADMIN_EDITABLE", key_l == "minimum_support")
    if key_l == "max_speed":
        return ParameterContract(key, "Maximum plausible travel speed", "Operational plausibility threshold; not a fraud probability.", "decimal", "km/h", 180, 1, 1000, (), "USER_DEFINED", "ADMIN_EDITABLE", False)
    if key_l == "trigger_percentile":
        return ParameterContract(key, "Trigger percentile", "Peer-relative alert boundary.", "percentile", "percentile", 0.95, 0.5, 0.9999, (), "EMPIRICAL_DISTRIBUTION", "ADMIN_EDITABLE", True)
    if key_l == "tolerance":
        return ParameterContract(key, "Arithmetic tolerance", "Fixed rounding tolerance for exact arithmetic.", "currency", "AED", 0.01, 0, 1, (), "TECHNICAL_INVARIANT", "LOCKED", False)
    if key_l == "reference_value":
        return ParameterContract(key, "Governed reference", "Effective policy, code, tariff, licence, benefit, or contract reference.", "expression_component", None, None, None, None, (), "POLICY_REFERENCE", "GOVERNED_REFERENCE", False)
    if key_l == "threshold":
        return ParameterContract(key, "Trigger value", "Value compared with the observed canonical metric.", "decimal", "source unit", None, None, None, (), "USER_DEFINED", "ADMIN_EDITABLE", False)
    return ParameterContract(key, key.replace("_", " ").title(), "Catalogue-declared trigger parameter.", "decimal", "source unit", None, None, None, (), "USER_DEFINED", "ADMIN_EDITABLE", False)


def _parameters(item: dict[str, Any], primitive: str) -> tuple[ParameterContract, ...]:
    keys = list(item.get("parameters_explicit") or [])
    if primitive in {"peer_threshold", "change_threshold", "graph_threshold"}:
        keys.extend(["trigger_percentile", "minimum_support"])
    elif primitive == "arithmetic_balance":
        keys.append("tolerance")
    elif primitive in {"reference_match", "compound_reference", "effective_date_range", "required_presence"}:
        keys.append("reference_value")
    elif primitive in {"numeric_threshold", "date_window", "duplicate_count"} and not keys:
        keys.append("threshold")
    deduped = tuple(dict.fromkeys(keys))
    return tuple(_parameter(key, item, primitive) for key in deduped)


def build_contract(item: dict[str, Any]) -> RuleContract:
    family = item["scenario_id"].split("-")[0]
    primitive = _primitive(item)
    fields = _fields(item, primitive)
    params = _parameters(item, primitive)
    types = set(item["types"])
    strength = "objective" if types == {"H"} else "strong" if "H" in types else "supporting"
    impact = (
        "reprice_difference"
        if primitive == "arithmetic_balance" or "REPRICE" in item["disposition"]["raw"].upper()
        else "distinct_associated_amount"
    )
    return RuleContract(
        rule_id=item["rule_id"],
        scenario_id=item["scenario_id"],
        name=item["rule_name"],
        description=f"Evaluates {item['rule_name'].casefold()} from canonical source and reference facts.",
        scheme_explanation=f"This control tests whether {item['trigger_semantics_raw'].strip('`')}.",
        subject=SUBJECT_BY_FAMILY[family],
        population=f"Applicable {SUBJECT_BY_FAMILY[family]} records with {', '.join(SCENARIO_DATASETS[item['scenario_id']])}.",
        required_datasets=SCENARIO_DATASETS[item["scenario_id"]],
        required_fields=fields,
        optional_fields=tuple(f"exclusion.{key}" for key in _exclusions(item["requirements_raw"])),
        primitive=primitive,
        formula=f"{primitive}({', '.join(fields)})",
        trigger_criterion=item["trigger_semantics_raw"],
        parameters=params,
        exclusions=_exclusions(item["requirements_raw"]),
        missing_data_behavior="DISABLED_MISSING_DATA; never interpreted as passed",
        disposition=_disposition(item["disposition"]["raw"], item["type_expression"]),
        evidence_strength=strength,
        evidence_fields=fields,
        comparison_fields=tuple(field for field in fields if field.startswith(("peer.", "reference.", "policy.", "tariff."))),
        impact_method=impact,
        reason_template=f"{item['rule_name']}: observed {{observed}} compared with {{expected}}.",
        data_readiness="READY_WHEN_INPUTS_AVAILABLE",
    )


CONTRACTS: dict[str, RuleContract] = {
    item["rule_id"]: build_contract(item)
    for item in REGISTRY
    if item["scope_state"] == "EXECUTABLE"
}


def validate_contracts() -> None:
    if len(CONTRACTS) != 149:
        raise RuntimeError("Rule contract integrity failure: expected 149 executable contracts")
    allowed_primitives = {
        "effective_date_range",
        "date_window",
        "required_presence",
        "reference_match",
        "duplicate_count",
        "arithmetic_balance",
        "numeric_threshold",
        "peer_threshold",
        "change_threshold",
        "graph_threshold",
        "compound_reference",
    }
    for contract in CONTRACTS.values():
        if contract.primitive not in allowed_primitives or not contract.required_fields:
            raise RuntimeError(f"Incomplete contract: {contract.rule_id}")
        if not contract.parameters:
            raise RuntimeError(f"Executable contract has no trigger definition: {contract.rule_id}")
        for parameter in contract.parameters:
            if parameter.provenance not in PROVENANCE_CLASSES:
                raise RuntimeError(f"Invalid provenance: {contract.rule_id}/{parameter.key}")


validate_contracts()

