from __future__ import annotations

import json
from pathlib import Path

from .settings import ROOT

MODEL_IDS = {"CLN-01-R02", "ANL-01-R03", "ANL-01-R04"}
DEFERRED_IDS = {
    "ENT-06-R02", "PAY-05-R02", "PAY-09-R01", "CLN-01-R03", "CLN-08-R03",
    "DOC-01-R02", "DOC-01-R03", "DOC-01-R04", "DOC-02-R01", "DOC-02-R02",
    "DOC-02-R03", "DOC-02-R04",
}


def load_registry() -> list[dict]:
    path = ROOT / "docs" / "_work_catalogue.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    controls = []
    for item in raw["controls"]:
        rid = item["rule_id"]
        scope = "EXCLUDED_MODEL" if rid in MODEL_IDS else "DEFERRED_DOCUMENT" if rid in DEFERRED_IDS else "EXECUTABLE"
        controls.append({
            **item,
            "scope_state": scope,
            "operational_state": None if scope != "EXECUTABLE" else ("SHADOW" if any(t in item["types"] for t in ("S", "N")) else "ACTIVE"),
            "version": "1.0",
            "reason_code": f"{rid.replace('-', '_')}_SIGNAL",
            "evaluator": None if scope != "EXECUTABLE" else f"{item['scenario_id'].split('-')[0].lower()}_catalogue",
            "poc_policy_warning": "POC default — not approved policy",
        })
    validate_registry(controls)
    return controls


def validate_registry(controls: list[dict]) -> None:
    ids = [x["rule_id"] for x in controls]
    if len(ids) != 164 or len(set(ids)) != 164:
        raise RuntimeError("Registry integrity failure: expected 164 unique controls")
    excluded = {x["rule_id"] for x in controls if x["scope_state"] == "EXCLUDED_MODEL"}
    deferred = {x["rule_id"] for x in controls if x["scope_state"] == "DEFERRED_DOCUMENT"}
    executable = [x for x in controls if x["scope_state"] == "EXECUTABLE"]
    if excluded != MODEL_IDS or deferred != DEFERRED_IDS or len(executable) != 149:
        raise RuntimeError("Registry integrity failure: expected 149 executable, 12 deferred, 3 excluded")
    if any(not x["evaluator"] for x in executable):
        raise RuntimeError("Registry integrity failure: executable rule without evaluator")


REGISTRY = load_registry()

