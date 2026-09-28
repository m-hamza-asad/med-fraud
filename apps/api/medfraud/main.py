from __future__ import annotations

import io
import hashlib
import json
import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from xlsxwriter import Workbook

from . import __version__
from .auth import COOKIE_NAME, create_session, current_user, digest_token, require_admin, verify_csrf, verify_password
from .database import SessionLocal, get_db
from .analytics import percentile, provider_graph, robust_summary
from .evaluators import EvaluationContext, evaluate_rule, parse_facts
from .imports import PROFILES, checksum, commit_preview, map_synthetic_uae_rows, parse_rows, preview_payload, safe_filename, validate_rows
from .migrations import run_migrations
from .models import (AuditEvent, CanonicalFact, Claim, ConfigurationVersion, DatasetProfile, EvaluationRun, ImportBatch,
                     ImportIssue, ImportPreview, MappingProfile, RuleEvaluation, RuleParameterDefinition, RuleRecord,
                     SessionToken, ThresholdRecommendation, ThresholdSimulation, User)
from .registry import REGISTRY
from .rule_contracts import CONTRACTS

app = FastAPI(title="Shahai Medical Payment Integrity", version=__version__, docs_url="/api/docs", openapi_url="/api/openapi.json")
EVALUATOR_VERSION = "canonical-evidence-v2-2026-09-28"
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; object-src 'none'"
    if request.url.path.startswith("/api/v1/auth"):
        response.headers["Cache-Control"] = "no-store"
    return response


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class ConfigBody(BaseModel):
    parameter: str = Field(default="threshold", max_length=128)
    value: float = Field(ge=0, le=1000000)
    unit: str = Field(default="score", max_length=32)
    effective_at: datetime
    label: str = Field(default="Prospective local configuration", max_length=128)
    source: str = Field(default="Administrator decision", max_length=255)


class EvaluationBody(BaseModel):
    batch_id: int
    analysis_date: date


def rule_dict(rule: RuleRecord) -> dict:
    item = json.loads(rule.metadata_json)
    return {**item, "rule_id": rule.rule_id, "scope_state": rule.scope_state,
            "operational_state": rule.operational_state, "reason_code": rule.reason_code}


@app.on_event("startup")
def startup() -> None:
    run_migrations()
    from .database import engine
    with Session(engine) as db:
        for interrupted in db.scalars(select(EvaluationRun).where(EvaluationRun.status.in_(["QUEUED", "RUNNING"]))):
            interrupted.status = "FAILED"
            interrupted.coverage = "Partial"
            progress = json.loads(interrupted.progress_json or "{}")
            progress["error"] = "Application stopped before the evaluation completed; start a new run."
            interrupted.progress_json = json.dumps(progress)
            interrupted.completed_at = datetime.utcnow()
        for item in REGISTRY:
            if not db.get(RuleRecord, item["rule_id"]):
                db.add(RuleRecord(rule_id=item["rule_id"], scenario_id=item["scenario_id"], name=item["rule_name"],
                                  type_expression=item["type_expression"], stage=item["canonical_stage"] or item["stage_label"],
                                  scope_state=item["scope_state"], operational_state=item["operational_state"],
                                  version=item["version"], reason_code=item["reason_code"], metadata_json=json.dumps(item)))
        db.flush()
        for contract in CONTRACTS.values():
            for parameter in contract.parameters:
                exists = db.scalar(select(RuleParameterDefinition.id).where(
                    RuleParameterDefinition.rule_id == contract.rule_id,
                    RuleParameterDefinition.parameter_key == parameter.key,
                    RuleParameterDefinition.version == 1,
                ))
                if not exists:
                    db.add(RuleParameterDefinition(
                        rule_id=contract.rule_id, parameter_key=parameter.key, display_label=parameter.label,
                        description=parameter.description, parameter_type=parameter.parameter_type, unit=parameter.unit,
                        provenance_class=parameter.provenance, edit_authority=parameter.edit_authority,
                        default_value_json=json.dumps(parameter.default),
                        bounds_json=json.dumps({"minimum": parameter.minimum, "maximum": parameter.maximum,
                                                "allowed_values": parameter.allowed_values}), scope=parameter.scope,
                        required=parameter.required, recommendation_eligible=parameter.recommendation_eligible,
                        source="Authoritative catalogue contract", rationale=contract.trigger_criterion,
                    ))
        db.commit()


@app.get("/api/v1/health")
def health(db: Session = Depends(get_db)) -> dict:
    counts = {state: db.scalar(select(func.count()).select_from(RuleRecord).where(RuleRecord.scope_state == state)) for state in ("EXECUTABLE", "DEFERRED_DOCUMENT", "EXCLUDED_MODEL")}
    ready = counts == {"EXECUTABLE": 149, "DEFERRED_DOCUMENT": 12, "EXCLUDED_MODEL": 3}
    return {"status": "ready" if ready else "degraded", "version": __version__, "database": "ready", "migration": "metadata-v1", "registry": counts, "bind": "127.0.0.1"}


@app.post("/api/v1/auth/login")
def login(body: LoginBody, response: Response, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.username == body.username))
    if not user or not verify_password(user.password_hash, body.password):
        db.add(AuditEvent(event_type="AUTH_LOGIN_FAILED", target_type="user", target_id=body.username[:64]))
        db.commit()
        raise HTTPException(401, "Invalid username or password")
    csrf = create_session(db, user, response)
    db.add(AuditEvent(event_type="AUTH_LOGIN_SUCCEEDED", actor_user_id=user.id,
                      target_type="session", target_id=user.username,
                      detail_json=json.dumps({"role": user.role})))
    db.commit()
    return {"username": user.username, "role": user.role, "csrf_token": csrf}


@app.post("/api/v1/auth/logout", dependencies=[Depends(verify_csrf)])
def logout(request: Request, response: Response, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    raw = request.cookies.get(COOKIE_NAME, "")
    token = db.scalar(select(SessionToken).where(SessionToken.token_hash == digest_token(raw)))
    if token:
        db.delete(token)
    db.add(AuditEvent(event_type="AUTH_LOGOUT", actor_user_id=user.id, target_type="session"))
    db.commit()
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@app.get("/api/v1/auth/session")
def session(user: User = Depends(current_user)) -> dict:
    return {"username": user.username, "role": user.role}


@app.get("/api/v1/rules")
def rules(q: str | None = None, scope_state: str | None = None, db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    stmt = select(RuleRecord).order_by(RuleRecord.rule_id)
    if scope_state:
        stmt = stmt.where(RuleRecord.scope_state == scope_state)
    items = [rule_dict(row) for row in db.scalars(stmt)]
    if q:
        needle = q.casefold()
        items = [x for x in items if needle in (x["rule_id"] + " " + x["rule_name"]).casefold()]
    return {"items": items, "total": len(items), "catalogue": {"total": 164, "executable": 149, "deferred": 12, "excluded": 3}}


@app.get("/api/v1/rules/{rule_id}")
def rule_detail(rule_id: str, db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    rule = db.get(RuleRecord, rule_id)
    if not rule:
        raise HTTPException(404, "Rule not found")
    item = rule_dict(rule)
    contract = CONTRACTS.get(rule_id)
    configurations = list(db.scalars(select(ConfigurationVersion).where(ConfigurationVersion.rule_id == rule_id).order_by(ConfigurationVersion.version.desc())))
    now = datetime.utcnow()
    current = [row for row in configurations if row.valid_from <= now and (row.valid_to is None or row.valid_to > now)]
    return {"catalogue": item, "contract": contract.to_dict() if contract else None,
            "current_configuration": [{"parameter": row.parameter, "value": json.loads(row.value_json),
                "unit": row.unit, "version": row.version, "valid_from": row.valid_from,
                "label": row.label, "source": row.source} for row in current],
            "configuration_history": [{"parameter": row.parameter, "value": json.loads(row.value_json), "unit": row.unit,
                                       "version": row.version, "valid_from": row.valid_from, "valid_to": row.valid_to,
                                       "label": row.label, "source": row.source} for row in configurations],
            "readiness": "DEFERRED" if rule.scope_state != "EXECUTABLE" else "READY_WHEN_INPUTS_AVAILABLE"}


@app.get("/api/v1/rules/{rule_id}/parameters")
def rule_parameters(rule_id: str, db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    contract = CONTRACTS.get(rule_id)
    if not contract: raise HTTPException(409, "Rule has no executable parameter contract")
    history = list(db.scalars(select(ConfigurationVersion).where(ConfigurationVersion.rule_id == rule_id).order_by(ConfigurationVersion.parameter, ConfigurationVersion.version)))
    return {"items": [parameter.__dict__ for parameter in contract.parameters],
            "effective_versions": [{"parameter": row.parameter, "value": json.loads(row.value_json), "version": row.version,
                                    "valid_from": row.valid_from, "valid_to": row.valid_to} for row in history]}


@app.get("/api/v1/rules/{rule_id}/distribution")
def rule_distribution(rule_id: str, db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    contract = CONTRACTS.get(rule_id)
    if not contract: raise HTTPException(409, "Rule has no executable distribution")
    run = db.scalar(select(EvaluationRun).where(
        EvaluationRun.status.in_(["COMPLETED", "COMPLETED_WITH_ERRORS"]),
    ).order_by(EvaluationRun.id.desc()).limit(1))
    profile = _field_decision_profile(db, contract.required_fields[0], run.batch_id if run else None)
    return {"rule_id": rule_id, "field": contract.required_fields[0], **profile}


def _field_decision_profile(db: Session, field_name: str, batch_id: int | None = None) -> dict:
    total_stmt = select(func.count()).select_from(Claim)
    if batch_id is not None:
        total_stmt = total_stmt.where(Claim.import_batch_id == batch_id)
    total_claims = db.scalar(total_stmt) or 0
    fact_stmt = select(CanonicalFact).where(CanonicalFact.field_name == field_name)
    if batch_id is not None:
        fact_stmt = fact_stmt.join(Claim, Claim.id == CanonicalFact.claim_id).where(Claim.import_batch_id == batch_id)
    rows = list(db.scalars(fact_stmt))
    direct_columns = {"claim.service_date": Claim.service_date, "claim.submitted_amount": Claim.submitted_amount,
                      "claim.net_amount": Claim.net_amount, "claim.paid_amount": Claim.paid_amount}
    direct_values: list[object] = []
    if not rows and field_name in direct_columns:
        direct_stmt = select(direct_columns[field_name])
        if batch_id is not None:
            direct_stmt = direct_stmt.where(Claim.import_batch_id == batch_id)
        direct_values = list(db.scalars(direct_stmt))
    numeric: list[Decimal] = []
    categorical: dict[str, int] = {}
    values: list[object] = direct_values or [
        row.value_number if row.value_number is not None else row.value_date if row.value_date is not None else row.value_bool if row.value_bool is not None else row.value_text
        for row in rows]
    for value in values:
        if value is None:
            continue
        try:
            if not isinstance(value, (date, bool)):
                numeric.append(Decimal(str(value)))
                continue
        except (ValueError, TypeError, InvalidOperation):
            pass
        key = value.isoformat() if isinstance(value, date) else str(value)
        categorical[key] = categorical.get(key, 0) + 1
    covered_claims = len(direct_values) if direct_values else len({row.claim_id for row in rows if row.claim_id is not None})
    summary = robust_summary(numeric)
    histogram: list[dict] = []
    if numeric:
        low, high = min(numeric), max(numeric)
        if low == high:
            histogram = [{"lower": str(low), "upper": str(high), "count": len(numeric)}]
        else:
            width = (high - low) / Decimal("10")
            counts = [0] * 10
            for value in numeric:
                index = min(9, int((value - low) / width))
                counts[index] += 1
            histogram = [{"lower": str(low + width * index), "upper": str(low + width * (index + 1)), "count": count}
                         for index, count in enumerate(counts)]
    top_values = [{"value": value, "count": count} for value, count in
                  sorted(categorical.items(), key=lambda item: (-item[1], item[0]))[:10]]
    return {"population": len(numeric) if numeric else sum(categorical.values()),
            "covered_claims": covered_claims, "total_claims": total_claims,
            "coverage_rate": covered_claims / total_claims if total_claims else 0,
            "data_type": "numeric" if numeric else "categorical_or_date" if categorical else "unavailable",
            "summary": {key: str(value) if isinstance(value, Decimal) else value for key, value in summary.items()},
            "histogram": histogram, "top_values": top_values,
            "support": "sufficient" if max(len(numeric), sum(categorical.values())) >= 20 else "insufficient"}


@app.get("/api/v1/rules/{rule_id}/decision-support")
def rule_decision_support(rule_id: str, db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    contract = CONTRACTS.get(rule_id)
    if not contract:
        raise HTTPException(409, "Rule is outside executable decision support")
    run = db.scalar(select(EvaluationRun).where(
        EvaluationRun.status.in_(["COMPLETED", "COMPLETED_WITH_ERRORS"]),
    ).order_by(EvaluationRun.id.desc()).limit(1))
    fields = [{"field": field_name, **_field_decision_profile(db, field_name, run.batch_id if run else None)}
              for field_name in contract.required_fields]
    joint_eligible = 0
    if run is not None:
        batch_claims = list(db.scalars(select(Claim).where(
            Claim.import_batch_id == run.batch_id, Claim.service_date <= run.analysis_date,
        ).order_by(Claim.member_token, Claim.service_date, Claim.id)))
        linked_readmissions = _linked_readmission_claims(batch_claims)
        for claim in batch_claims:
            facts = parse_facts(claim.facts_json)
            facts.setdefault("claim", {}).update({"service_date": claim.service_date.isoformat(),
                "submitted_amount": str(claim.submitted_amount), "net_amount": str(claim.net_amount),
                "paid_amount": str(claim.paid_amount), "source_claim_id": claim.source_claim_id})
            if contract.rule_id == "CLN-05-R02":
                facts.setdefault("history", {}).pop("readmission_gap_days", None)
                linked = linked_readmissions.get(claim.id)
                if linked:
                    facts["history"]["readmission_gap_days"] = (
                        _encounter_date(claim, "admission_date") - _encounter_date(linked, "discharge_date")).days
            values = []
            for field_name in contract.required_fields:
                cursor: object = facts
                for part in field_name.split("."):
                    cursor = cursor.get(part) if isinstance(cursor, dict) else None
                values.append(cursor)
            joint_eligible += all(value is not None for value in values)
    history = list(db.scalars(select(ConfigurationVersion).where(ConfigurationVersion.rule_id == rule_id)
                              .order_by(ConfigurationVersion.version.desc()).limit(20)))
    available = sum(item["covered_claims"] > 0 for item in fields)
    return {"rule_id": rule_id, "population": contract.population,
            "required_field_count": len(fields), "available_field_count": available,
            "readiness": "READY" if joint_eligible >= 20 else "PARTIAL" if joint_eligible else "UNAVAILABLE",
            "joint_eligible_claims": joint_eligible,
            "fields": fields,
            "snapshot": None if run is None else {"run_id": run.id, "batch_id": run.batch_id,
                "analysis_date": run.analysis_date, "completed_at": run.completed_at,
                "note": "Simulation uses this immutable run population. Field distributions describe the currently loaded local data."},
            "configuration_history": [{"parameter": row.parameter, "value": json.loads(row.value_json),
                "unit": row.unit, "version": row.version, "valid_from": row.valid_from,
                "valid_to": row.valid_to, "label": row.label, "source": row.source} for row in history],
            "guidance": "Distribution charts describe the mapped local data; they do not establish policy or prove fraud."}


@app.post("/api/v1/configuration/{rule_id}", dependencies=[Depends(verify_csrf)])
def configure(rule_id: str, body: ConfigBody, db: Session = Depends(get_db), user: User = Depends(require_admin)) -> dict:
    rule = db.get(RuleRecord, rule_id)
    if not rule:
        raise HTTPException(404, "Rule not found")
    if rule.scope_state != "EXECUTABLE":
        raise HTTPException(409, "Excluded and deferred rules cannot be configured")
    if len(body.source.strip()) < 10 or body.source.strip() == "Administrator decision":
        raise HTTPException(422, "A specific decision rationale or approved source is required")
    definition = db.scalar(select(RuleParameterDefinition).where(
        RuleParameterDefinition.rule_id == rule_id, RuleParameterDefinition.parameter_key == body.parameter,
    ).order_by(RuleParameterDefinition.version.desc()))
    if not definition:
        raise HTTPException(422, "Unknown parameter for this rule")
    if definition.edit_authority != "ADMIN_EDITABLE":
        raise HTTPException(409, "This governed or technical parameter cannot be edited locally")
    bounds = json.loads(definition.bounds_json)
    if ((bounds.get("minimum") is not None and body.value < bounds["minimum"]) or
            (bounds.get("maximum") is not None and body.value > bounds["maximum"])):
        raise HTTPException(422, "Value is outside the governed parameter bounds")
    if body.unit != definition.unit:
        raise HTTPException(422, f"Unit must be {definition.unit}")
    effective_at = body.effective_at.replace(tzinfo=None) if body.effective_at.tzinfo else body.effective_at
    if effective_at <= datetime.utcnow():
        raise HTTPException(422, "Effective date must be in the future")
    current = db.scalar(select(ConfigurationVersion).where(ConfigurationVersion.rule_id == rule_id,
        ConfigurationVersion.parameter == body.parameter, ConfigurationVersion.valid_to.is_(None)).order_by(ConfigurationVersion.version.desc()))
    latest = db.scalar(select(ConfigurationVersion).where(ConfigurationVersion.rule_id == rule_id,
        ConfigurationVersion.parameter == body.parameter).order_by(ConfigurationVersion.version.desc()).limit(1))
    if latest and effective_at <= latest.valid_from:
        raise HTTPException(422, f"Effective date must be after the latest scheduled version ({latest.valid_from.isoformat()})")
    next_version = (latest.version + 1) if latest else 1
    previous = None if current is None else {"version": current.version, "value": json.loads(current.value_json),
        "valid_from": current.valid_from.isoformat(), "valid_to": current.valid_to.isoformat() if current.valid_to else None}
    if current:
        current.valid_to = effective_at
    row = ConfigurationVersion(rule_id=rule_id, parameter=body.parameter, value_json=json.dumps(body.value), unit=body.unit,
                               valid_from=effective_at, version=next_version, changed_by=user.id,
                               label=body.label, source=body.source)
    db.add(row)
    db.add(AuditEvent(event_type="CONFIGURATION_CHANGED", actor_user_id=user.id, target_type="rule", target_id=rule_id,
        detail_json=json.dumps({"parameter": body.parameter, "before": previous,
            "after": {"version": next_version, "value": body.value, "unit": body.unit,
                      "effective_at": effective_at.isoformat()}, "rationale": body.source})))
    db.commit()
    return {"rule_id": rule_id, "parameter": body.parameter, "version": next_version, "effective_at": body.effective_at}


@app.post("/api/v1/rules/{rule_id}/simulate", dependencies=[Depends(verify_csrf)])
def simulate_configuration(rule_id: str, body: ConfigBody, db: Session = Depends(get_db), user: User = Depends(require_admin)) -> dict:
    contract = CONTRACTS.get(rule_id)
    if not contract:
        raise HTTPException(409, "Only executable rules can be simulated")
    parameter = next((item for item in contract.parameters if item.key == body.parameter), None)
    if parameter is None:
        raise HTTPException(404, "Parameter not found")
    if parameter.minimum is not None and body.value < parameter.minimum or parameter.maximum is not None and body.value > parameter.maximum:
        raise HTTPException(422, f"Candidate must be between {parameter.minimum} and {parameter.maximum}")
    run = db.scalar(select(EvaluationRun).where(
        EvaluationRun.status.in_(["COMPLETED", "COMPLETED_WITH_ERRORS"]),
    ).order_by(EvaluationRun.id.desc()).limit(1))
    if run is None:
        raise HTTPException(409, "Run an evaluation before simulating a configuration change")
    claims_for_run = list(db.scalars(select(Claim).where(
        Claim.import_batch_id == run.batch_id, Claim.service_date <= run.analysis_date,
    ).order_by(Claim.member_token, Claim.service_date, Claim.id)))
    linked_readmissions = _linked_readmission_claims(claims_for_run)
    baseline_config = {item.key: item.default for item in contract.parameters if item.default is not None}
    for configured in json.loads(run.configuration_snapshot or "[]"):
        if configured.get("rule_id") == rule_id:
            baseline_config[configured["parameter"]] = configured["value"]
    candidate_config = {**baseline_config, body.parameter: body.value}
    baseline_ids: set[int] = set()
    candidate_ids: set[int] = set()
    unavailable = 0
    for claim in claims_for_run:
        facts = parse_facts(claim.facts_json)
        history = facts.setdefault("history", {})
        history.pop("readmission_gap_days", None)
        linked = linked_readmissions.get(claim.id)
        if linked is not None:
            current_admission = _encounter_date(claim, "admission_date")
            prior_discharge = _encounter_date(linked, "discharge_date")
            history["readmission_gap_days"] = (current_admission - prior_discharge).days
        facts.setdefault("claim", {}).update({"source_claim_id": claim.source_claim_id,
            "service_date": claim.service_date.isoformat(), "submitted_amount": str(claim.submitted_amount),
            "net_amount": str(claim.net_amount), "paid_amount": str(claim.paid_amount)})
        available = frozenset(set(facts.get("available_datasets", [])) | {"claim_header"})
        context = {"analysis_date": run.analysis_date,
            "history_start": date(run.analysis_date.year - 5, run.analysis_date.month, min(run.analysis_date.day, 28)),
            "facts": facts, "available_datasets": available}
        baseline = evaluate_rule(contract, EvaluationContext(**context, configuration=baseline_config))
        candidate = evaluate_rule(contract, EvaluationContext(**context, configuration=candidate_config))
        if baseline.triggered:
            baseline_ids.add(claim.id)
        if candidate.triggered:
            candidate_ids.add(claim.id)
        if candidate.status in {"DISABLED_MISSING_DATA", "INSUFFICIENT_DATA", "ERROR"}:
            unavailable += 1
    added = candidate_ids - baseline_ids
    removed = baseline_ids - candidate_ids
    persisted_ids = set(db.scalars(select(RuleEvaluation.claim_id).where(
        RuleEvaluation.run_id == run.id, RuleEvaluation.rule_id == rule_id,
        RuleEvaluation.triggered.is_(True), RuleEvaluation.claim_id.is_not(None))))
    persisted_count = db.scalar(select(func.count(RuleEvaluation.id)).where(
        RuleEvaluation.run_id == run.id, RuleEvaluation.rule_id == rule_id)) or 0
    if persisted_count and persisted_ids != baseline_ids:
        raise HTTPException(409, "The current evaluator no longer reproduces the selected run baseline; create a new evaluation run before simulation")
    candidate_claims = {claim.id: claim for claim in claims_for_run if claim.id in candidate_ids}
    result = {"candidate_value": body.value, "decision_threshold": str(body.value),
              "simulation_kind": "production_evaluator_replay", "population": len(claims_for_run),
              "baseline_triggered": len(baseline_ids), "would_trigger": len(candidate_ids),
              "added_claims": len(added), "removed_claims": len(removed),
              "trigger_rate": len(candidate_ids) / len(claims_for_run) if claims_for_run else None,
              "unavailable_claims": unavailable, "analysis_date": run.analysis_date,
              "batch_id": run.batch_id, "baseline_run_id": run.id,
              "example_claims": [{"id": claim.id, "claim_id": claim.source_claim_id,
                                  "service_date": claim.service_date, "net_amount": claim.net_amount}
                                 for claim in list(candidate_claims.values())[:5]],
              "support": "sufficient" if len(claims_for_run) - unavailable >= 20 else "insufficient",
              "warnings": [] if len(claims_for_run) - unavailable >= 20 else
                  ["Fewer than 20 claims produced a result; do not use this simulation to set policy."],
              "baseline_reconciled": bool(persisted_count), "mutated_configuration": False}
    row = ThresholdSimulation(rule_id=rule_id, proposed_configuration_json=body.model_dump_json(),
                              dataset_snapshot_hash=f"batch-{run.batch_id}-run-{run.id}",
                              result_json=json.dumps(result, default=str),
                              status="COMPLETE" if claims_for_run else "INSUFFICIENT_DATA", created_by=user.id)
    db.add(row); db.commit()
    return {"simulation_id": row.id, **result}


@app.post("/api/v1/rules/{rule_id}/recommendations/{parameter_key}", dependencies=[Depends(verify_csrf)])
def recommend_configuration(rule_id: str, parameter_key: str, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    contract = CONTRACTS.get(rule_id)
    if not contract:
        raise HTTPException(409, "Only executable rules have parameter guidance")
    parameter = next((item for item in contract.parameters if item.key == parameter_key), None)
    if not parameter:
        raise HTTPException(404, "Parameter not found")
    if parameter.provenance == "POLICY_REFERENCE":
        return {"status": "UNAVAILABLE", "suggested_value": None, "support": "not_applicable",
                "method": "governed reference required", "warnings": ["Utilization data cannot infer policy, tariff, licence, or benefit terms."]}
    if not parameter.recommendation_eligible:
        return {"status": "NOT_ELIGIBLE", "suggested_value": None, "support": "not_applicable",
                "method": "administrator or governed source required",
                "warnings": ["This parameter is not eligible for an empirical recommendation. Review its bounds, source, and the supporting field distributions before entering a value."]}
    run = db.scalar(select(EvaluationRun).where(
        EvaluationRun.status.in_(["COMPLETED", "COMPLETED_WITH_ERRORS"]),
    ).order_by(EvaluationRun.id.desc()).limit(1))
    if run is None:
        raise HTTPException(409, "Run an evaluation before generating dataset guidance")
    values: list[Decimal] = []
    calibration_cutoff = run.analysis_date
    population_claims = list(db.scalars(select(Claim).where(
        Claim.import_batch_id == run.batch_id, Claim.service_date < calibration_cutoff,
    ).order_by(Claim.member_token, Claim.service_date, Claim.id)))
    linked_readmissions = _linked_readmission_claims(population_claims)
    for claim in population_claims:
        facts = parse_facts(claim.facts_json)
        if contract.primitive == "date_window":
            history = facts.setdefault("history", {})
            history.pop("readmission_gap_days", None)
            linked = linked_readmissions.get(claim.id)
            if linked is not None:
                history["readmission_gap_days"] = (claim.service_date - linked.service_date).days
        cursor: object = facts
        for part in contract.required_fields[0].split("."):
            cursor = cursor.get(part) if isinstance(cursor, dict) else None
        try:
            if cursor is not None: values.append(Decimal(str(cursor)))
        except Exception:
            continue
    summary = robust_summary(values); support = "sufficient" if len(values) >= 20 else "insufficient"
    probability = float(parameter.default) if parameter.parameter_type == "percentile" and parameter.default is not None else .95
    supporting_threshold = percentile(values, probability) if support == "sufficient" else None
    if parameter.parameter_type == "percentile":
        suggestion = Decimal(str(parameter.default if parameter.default is not None else probability)) if support == "sufficient" else None
        method = f"percentile control selection with observed p={probability} boundary"
    elif parameter.key == "minimum_support":
        suggestion = Decimal(str(parameter.default or 20)) if support == "sufficient" else None
        method = "minimum support floor retained after population sufficiency check"
    else:
        suggestion = supporting_threshold
        method = f"leakage-controlled historical percentile p={probability}"
    warnings = [] if support == "sufficient" else ["Minimum support of 20 mapped observations is not met; no value is recommended."]
    payload = {"status": "AVAILABLE" if suggestion is not None else "INSUFFICIENT_DATA",
               "suggested_value": str(suggestion) if suggestion is not None else None, "support": support,
               "method": method, "supporting_threshold": str(supporting_threshold) if supporting_threshold is not None else None,
               "population": {"records": len(values), "period_end_exclusive": calibration_cutoff.isoformat(),
                              "batch_id": run.batch_id, "run_id": run.id,
                              "leakage_control": "Only claims in the simulation batch before the run analysis date."},
               "distribution": {key: str(value) if isinstance(value, Decimal) else value for key, value in summary.items()},
               "warnings": warnings, "impact": "Run a non-mutating simulation before saving."}
    row = ThresholdRecommendation(rule_id=rule_id, parameter_key=parameter_key,
        dataset_snapshot_hash=f"batch-{run.batch_id}-run-{run.id}-{len(values)}", method=payload["method"],
        suggested_value_json=json.dumps(payload["suggested_value"]), range_json=json.dumps({"minimum": parameter.minimum, "maximum": parameter.maximum}),
        population_json=json.dumps(payload["population"]), distribution_json=json.dumps(payload["distribution"]),
        impact_json=json.dumps({"guidance": payload["impact"]}), support_level=support,
        warnings_json=json.dumps(warnings), feature_version="canonical-v1", code_version=__version__)
    db.add(row); db.commit()
    return {"recommendation_id": row.id, **payload}


@app.post("/api/v1/imports/validate")
async def validate_import(profile: str = Form(...), analysis_date: date = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    if profile not in PROFILES:
        raise HTTPException(422, "Unknown import profile")
    data = await file.read()
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(413, "File exceeds 50 MB")
    name = safe_filename(file.filename or "upload")
    file_checksum = checksum(data)
    existing = db.scalar(select(ImportBatch).where(ImportBatch.checksum == file_checksum))
    if existing:
        return {"duplicate": True, "batch_id": existing.id, "status": existing.status,
                "row_count": existing.row_count, "error_count": existing.error_count,
                "warning_count": existing.warning_count, "issues": [],
                "message": "This exact file already exists; no rows were duplicated."}
    try:
        parsed = parse_rows(name, data)
        mapping_issues: list[dict] = []
        if profile == "synthetic_uae":
            parsed, mapping_issues = map_synthetic_uae_rows(parsed)
            for issue in mapping_issues: issue.update({"file": name, "sheet": None})
        normalized, issues = validate_rows(parsed, name, analysis_date)
        issues = mapping_issues + issues
    except (ValueError, UnicodeDecodeError) as exc:
        normalized, issues = [], [{"severity": "error", "file": name, "sheet": None, "column_name": None, "row_number": None, "code": "PARSE_ERROR", "message": str(exc), "guidance": "Use an unencrypted .csv or .xlsx template without macros."}]
    batch = ImportBatch(checksum=file_checksum, filename=name, profile=profile, status="VALIDATED" if not any(x["severity"] == "error" for x in issues) else "INVALID", row_count=len(normalized), error_count=sum(x["severity"] == "error" for x in issues), warning_count=sum(x["severity"] == "warning" for x in issues), created_by=user.id)
    db.add(batch); db.flush()
    for item in issues:
        db.add(ImportIssue(batch_id=batch.id, **item))
    if batch.status == "VALIDATED":
        mapping = None
        if profile == "synthetic_uae":
            mapping = db.scalar(select(MappingProfile).where(MappingProfile.name == "synthetic_uae_v1"))
            if mapping is None:
                mapping = MappingProfile(name="synthetic_uae_v1", source_profile=profile, schema_hash=file_checksum[:32], confirmed=True,
                    created_by=user.id, mapping_json=json.dumps({"claim_id": "source_claim_id", "patient_id": "member_token",
                    "hospital_id": "provider_token", "tpa": "network_id", "date_of_admission": "service_date",
                    "claim_amount_requested_aed": "submitted_amount", "claim_amount_approved_aed": "net_amount",
                    "labels": "held_out_not_evaluator_inputs"}))
                db.add(mapping); db.flush()
        db.add(ImportPreview(batch_id=batch.id, analysis_date=analysis_date, normalized_rows_json=preview_payload(normalized),
                             mapping_profile_id=mapping.id if mapping else None))
        service_dates = [row["service_date"] for row in normalized]
        db.add(DatasetProfile(import_batch_id=batch.id, dataset_name=name, snapshot_hash=file_checksum,
            source_profile=profile, safety_status="SYNTHETIC_FIXTURE_ONLY" if profile == "synthetic_uae" else "TOKENIZED_LOCAL_DATA_EXPECTED",
            mapping_status="CONFIRMED_SYNTHETIC_MAPPING" if profile == "synthetic_uae" else "PROFILE_SELECTED",
            row_count=len(normalized), period_start=min(service_dates) if service_dates else None,
            period_end=max(service_dates) if service_dates else None,
            summary_json=json.dumps({"currency": "AED", "labels_used_for_evaluation": False}),
            limitations_json=json.dumps(["Synthetic engineering data; not evidence of fraud performance."] if profile == "synthetic_uae" else [])))
    db.add(AuditEvent(event_type="IMPORT_VALIDATED", actor_user_id=user.id, target_type="batch", target_id=str(batch.id), detail_json=json.dumps({"status": batch.status, "rows": batch.row_count})))
    db.commit()
    issue_summary: dict[str, int] = {}
    for issue in issues:
        issue_summary[issue["code"]] = issue_summary.get(issue["code"], 0) + 1
    mapping_summary = ({"Claim ID": "claim_id", "Member token": "patient_id",
        "Provider token": "hospital_id", "Network / TPA": "tpa",
        "Service date": "date_of_admission", "Submitted amount (AED)": "claim_amount_requested_aed",
        "Net amount (AED)": "claim_amount_approved_aed"} if profile == "synthetic_uae" else
        {"Canonical fields": "File columns must match the selected canonical template"})
    return {"duplicate": False, "batch_id": batch.id, "status": batch.status,
        "row_count": batch.row_count, "error_count": batch.error_count,
        "warning_count": batch.warning_count, "issues": issues, "issue_summary": issue_summary,
        "preview_rows": normalized[:10], "mapping_summary": mapping_summary,
        "period": {"start": min((row["service_date"] for row in normalized), default=None),
                   "end": max((row["service_date"] for row in normalized), default=None)},
        "currency": "AED"}


@app.post("/api/v1/imports/{batch_id}/commit", dependencies=[Depends(verify_csrf)])
def commit_import(batch_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    batch = db.get(ImportBatch, batch_id)
    if not batch:
        raise HTTPException(404, "Import batch not found")
    try:
        created = commit_preview(db, batch)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    db.add(AuditEvent(event_type="IMPORT_COMMITTED", actor_user_id=user.id, target_type="batch",
                      target_id=str(batch.id), detail_json=json.dumps({"rows": created})))
    db.commit()
    return {"batch_id": batch.id, "status": batch.status, "row_count": batch.row_count, "created": created}


@app.get("/api/v1/imports")
def imports(db: Session = Depends(get_db), _user: User = Depends(current_user)) -> list[dict]:
    rows = db.scalars(select(ImportBatch).order_by(ImportBatch.created_at.desc()).limit(100))
    result = []
    for batch in rows:
        latest_run = db.scalar(select(EvaluationRun).where(EvaluationRun.batch_id == batch.id).order_by(EvaluationRun.id.desc()).limit(1))
        preview = db.scalar(select(ImportPreview).where(ImportPreview.batch_id == batch.id))
        result.append({"id": batch.id, "filename": batch.filename, "profile": batch.profile,
            "status": batch.status, "row_count": batch.row_count, "errors": batch.error_count,
            "warnings": batch.warning_count, "created_at": batch.created_at,
            "analysis_date": preview.analysis_date if preview else None,
            "evaluation": None if latest_run is None else {"id": latest_run.id, "status": latest_run.status,
                "coverage": latest_run.coverage, "progress": json.loads(latest_run.progress_json or "{}")}})
    return result


def _encounter_date(claim: Claim, field: str) -> date | None:
    value = parse_facts(claim.facts_json).get("encounter", {}).get(field)
    try:
        return date.fromisoformat(str(value)) if value else None
    except ValueError:
        return None


def _linked_readmission_claims(claims_in_date_order: list[Claim]) -> dict[int, Claim]:
    """Link only time-correct earlier claims for the same member and primary diagnosis."""
    linked: dict[int, Claim] = {}
    latest_by_member_diagnosis: dict[tuple[str, str], Claim] = {}
    for claim in claims_in_date_order:
        facts = parse_facts(claim.facts_json)
        diagnosis_code = str(facts.get("diagnosis", {}).get("primary_code") or "").strip()
        if not diagnosis_code:
            continue
        key = (claim.member_token, diagnosis_code)
        current_admission = _encounter_date(claim, "admission_date")
        prior_claim = latest_by_member_diagnosis.get(key)
        prior_discharge = _encounter_date(prior_claim, "discharge_date") if prior_claim else None
        if prior_claim is not None and current_admission is not None and prior_discharge is not None and prior_discharge < current_admission:
            linked[claim.id] = prior_claim
        latest_by_member_diagnosis[key] = claim
    return linked


def _execute_evaluation(run_id: int) -> None:
    """Evaluate a committed batch in bounded transactions and persist visible progress."""
    try:
        with SessionLocal() as db:
            run = db.get(EvaluationRun, run_id)
            if run is None:
                return
            batch = db.get(ImportBatch, run.batch_id)
            if batch is None:
                raise ValueError("Evaluation batch is unavailable")
            run.status = "RUNNING"
            db.commit()
            rules_by_id = {x.rule_id: rule_dict(x) for x in db.scalars(
                select(RuleRecord).where(RuleRecord.scope_state == "EXECUTABLE").order_by(RuleRecord.rule_id))}
            configured = json.loads(run.configuration_snapshot)
            config_by_rule: dict[str, dict[str, object]] = {}
            version_by_rule: dict[str, dict[str, int]] = {}
            for item in configured:
                config_by_rule.setdefault(item["rule_id"], {})[item["parameter"]] = item["value"]
                version_by_rule.setdefault(item["rule_id"], {})[item["parameter"]] = item["version"]
            total_claims = db.scalar(select(func.count()).select_from(Claim).where(
                Claim.import_batch_id == batch.id, Claim.service_date <= run.analysis_date)) or 0
            history_rows = list(db.scalars(select(Claim).where(
                Claim.import_batch_id == batch.id, Claim.service_date <= run.analysis_date,
            ).order_by(Claim.member_token, Claim.service_date, Claim.id)))
            linked_readmissions = _linked_readmission_claims(history_rows)
            processed = failures = disabled = triggered = 0
            last_claim_id = 0
            while True:
                claim_chunk = list(db.scalars(select(Claim).where(
                    Claim.import_batch_id == batch.id, Claim.service_date <= run.analysis_date,
                    Claim.id > last_claim_id).order_by(Claim.id).limit(100)))
                if not claim_chunk:
                    break
                for claim in claim_chunk:
                    facts = parse_facts(claim.facts_json)
                    history = facts.setdefault("history", {})
                    history.pop("readmission_gap_days", None)
                    linked_readmission = linked_readmissions.get(claim.id)
                    if linked_readmission is not None:
                        current_admission = _encounter_date(claim, "admission_date")
                        prior_discharge = _encounter_date(linked_readmission, "discharge_date")
                        history["readmission_gap_days"] = (current_admission - prior_discharge).days
                        history["readmission_evidence"] = "derived_from_linked_claims_with_matching_primary_diagnosis"
                    facts.setdefault("claim", {}).update({"source_claim_id": claim.source_claim_id,
                        "service_date": claim.service_date.isoformat(), "submitted_amount": str(claim.submitted_amount),
                        "net_amount": str(claim.net_amount), "paid_amount": str(claim.paid_amount)})
                    available_claim = set(facts.get("available_datasets", [])) | {"claim_header"}
                    for rule in rules_by_id.values():
                        try:
                            contract = CONTRACTS[rule["rule_id"]]
                            rule_config = {p.key: p.default for p in contract.parameters if p.default is not None}
                            rule_config.update(config_by_rule.get(rule["rule_id"], {}))
                            evidence_records = [{"dataset": "claim_header", "record_id": claim.source_claim_id,
                                                 "claim_id": claim.id}]
                            if contract.rule_id == "CLN-05-R02" and linked_readmission is not None:
                                evidence_records.append({"dataset": "claim_history",
                                    "record_id": linked_readmission.source_claim_id,
                                    "claim_id": linked_readmission.id,
                                    "service_date": linked_readmission.service_date.isoformat(),
                                    "relationship": "earlier claim with matching member and primary diagnosis"})
                            result = evaluate_rule(contract, EvaluationContext(
                                analysis_date=run.analysis_date,
                                history_start=date(run.analysis_date.year - 5, run.analysis_date.month, min(run.analysis_date.day, 28)),
                                facts=facts, available_datasets=frozenset(available_claim), configuration=rule_config,
                                configuration_versions=version_by_rule.get(rule["rule_id"], {}),
                                reference_versions={dataset: batch.checksum[:12] for dataset in available_claim},
                                evidence_records=tuple(evidence_records),
                            ))
                            disabled += result.status in {"DISABLED_MISSING_DATA", "INSUFFICIENT_DATA"}
                            triggered += result.triggered
                            db.add(RuleEvaluation(run_id=run.id, claim_id=claim.id, rule_id=rule["rule_id"],
                                status=result.status, triggered=result.triggered, reason_code=rule["reason_code"],
                                evidence_json=json.dumps(result.evidence), disposition=result.disposition,
                                score=result.score, exposure=result.exposure))
                        except Exception as exc:
                            failures += 1
                            db.add(RuleEvaluation(run_id=run.id, claim_id=claim.id, rule_id=rule["rule_id"],
                                status="ERROR", reason_code=rule["reason_code"], error_category=type(exc).__name__,
                                evidence_json=json.dumps({"safe_message": "Evaluator failed"})))
                    processed += 1
                    last_claim_id = claim.id
                run.progress_json = json.dumps({"claims_processed": processed, "claims_total": total_claims,
                    "rules": len(rules_by_id), "triggered": triggered, "disabled": disabled, "errors": failures})
                db.commit()
            insufficient = db.scalar(select(func.count(RuleEvaluation.id)).where(
                RuleEvaluation.run_id == run.id, RuleEvaluation.status == "INSUFFICIENT_DATA")) or 0
            run.coverage = "Partial" if disabled or failures or insufficient else "Complete"
            run.status = "COMPLETED_WITH_ERRORS" if failures else "COMPLETED"
            run.progress_json = json.dumps({"claims_processed": processed, "claims_total": total_claims,
                "claims": processed, "rules": len(rules_by_id), "triggered": triggered,
                "disabled": disabled, "insufficient": insufficient, "errors": failures,
                "evaluator_version": EVALUATOR_VERSION})
            run.completed_at = datetime.utcnow()
            db.add(AuditEvent(event_type="EVALUATION_COMPLETED", actor_user_id=run.created_by,
                target_type="run", target_id=str(run.id), detail_json=run.progress_json))
            db.commit()
    except Exception as exc:
        with SessionLocal() as db:
            run = db.get(EvaluationRun, run_id)
            if run is not None:
                run.status = "FAILED"
                progress = json.loads(run.progress_json or "{}")
                progress.update({"error": "Evaluation stopped unexpectedly", "error_category": type(exc).__name__})
                run.progress_json = json.dumps(progress)
                run.completed_at = datetime.utcnow()
                db.commit()


@app.post("/api/v1/evaluations", dependencies=[Depends(verify_csrf)], status_code=202)
def run_evaluation(body: EvaluationBody, background_tasks: BackgroundTasks,
                   db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    batch = db.get(ImportBatch, body.batch_id)
    if not batch or batch.status != "COMMITTED":
        raise HTTPException(409, "A committed import batch is required")
    active = db.scalar(select(EvaluationRun).where(EvaluationRun.batch_id == batch.id,
        EvaluationRun.status.in_(["QUEUED", "RUNNING"])).order_by(EvaluationRun.id.desc()))
    if active:
        return {"id": active.id, "status": active.status, "coverage": active.coverage,
                **json.loads(active.progress_json or "{}")}
    at = datetime.combine(body.analysis_date, datetime.max.time())
    config_rows = list(db.scalars(select(ConfigurationVersion).where(
        ConfigurationVersion.valid_from <= at,
        (ConfigurationVersion.valid_to.is_(None)) | (ConfigurationVersion.valid_to > at),
    )))
    config = [{"rule_id": x.rule_id, "parameter": x.parameter, "value": json.loads(x.value_json),
               "version": x.version} for x in config_rows]
    total_claims = db.scalar(select(func.count()).select_from(Claim).where(
        Claim.import_batch_id == batch.id, Claim.service_date <= body.analysis_date)) or 0
    run = EvaluationRun(batch_id=batch.id, analysis_date=body.analysis_date, status="QUEUED", coverage="Pending",
        configuration_snapshot=json.dumps(config), created_by=user.id,
        progress_json=json.dumps({"claims_processed": 0, "claims_total": total_claims, "rules": 149,
                                  "triggered": 0, "disabled": 0, "insufficient": 0, "errors": 0,
                                  "evaluator_version": EVALUATOR_VERSION}))
    db.add(run); db.flush()
    db.add(AuditEvent(event_type="EVALUATION_QUEUED", actor_user_id=user.id, target_type="run",
        target_id=str(run.id), detail_json=json.dumps({"batch_id": batch.id, "claims": total_claims})))
    db.commit()
    background_tasks.add_task(_execute_evaluation, run.id)
    return {"id": run.id, "status": run.status, "coverage": run.coverage, **json.loads(run.progress_json)}


@app.get("/api/v1/evaluations")
def evaluations(db: Session = Depends(get_db), _user: User = Depends(current_user)) -> list[dict]:
    rows = db.scalars(select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(100))
    return [{"id": x.id, "batch_id": x.batch_id, "analysis_date": x.analysis_date, "status": x.status,
             "coverage": x.coverage, "progress": json.loads(x.progress_json), "created_at": x.created_at,
             "completed_at": x.completed_at} for x in rows]


@app.get("/api/v1/evaluations/{run_id}")
def evaluation_detail(run_id: int, db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    run = db.get(EvaluationRun, run_id)
    if not run: raise HTTPException(404, "Evaluation run not found")
    counts = db.execute(select(RuleEvaluation.status, func.count()).where(RuleEvaluation.run_id == run_id).group_by(RuleEvaluation.status)).all()
    batch = db.get(ImportBatch, run.batch_id)
    triggered_claims = db.scalar(select(func.count(func.distinct(RuleEvaluation.claim_id))).where(
        RuleEvaluation.run_id == run_id, RuleEvaluation.triggered.is_(True))) or 0
    assessed_claims = db.scalar(select(func.count(func.distinct(RuleEvaluation.claim_id))).where(
        RuleEvaluation.run_id == run_id, RuleEvaluation.claim_id.is_not(None))) or 0
    unavailable_by_rule = db.execute(select(RuleEvaluation.rule_id, func.count()).where(
        RuleEvaluation.run_id == run_id,
        RuleEvaluation.status.in_(["DISABLED_MISSING_DATA", "INSUFFICIENT_DATA", "ERROR"]),
    ).group_by(RuleEvaluation.rule_id).order_by(func.count().desc()).limit(10)).all()
    return {"id": run.id, "batch_id": run.batch_id, "batch_filename": batch.filename if batch else None,
            "analysis_date": run.analysis_date, "status": run.status,
            "coverage": run.coverage, "configuration_snapshot": json.loads(run.configuration_snapshot),
            "progress": json.loads(run.progress_json), "status_counts": dict(counts),
            "distinct_counts": {"assessed_claims": assessed_claims, "flagged_claims": triggered_claims,
                                "controls": 149,
                                "rule_claim_checks": sum(count for _, count in counts)},
            "top_unavailable_controls": [{"rule_id": rule_id, "checks": count}
                                         for rule_id, count in unavailable_by_rule],
            "created_at": run.created_at, "completed_at": run.completed_at,
            "configuration_version_count": len(json.loads(run.configuration_snapshot))}


def _latest_completed_runs(db: Session) -> dict[int, int]:
    result: dict[int, int] = {}
    for batch_id in db.scalars(select(Claim.import_batch_id).distinct()):
        latest = db.scalar(select(EvaluationRun.id).where(
            EvaluationRun.batch_id == batch_id,
            EvaluationRun.status.in_(["COMPLETED", "COMPLETED_WITH_ERRORS"]),
        ).order_by(EvaluationRun.id.desc()).limit(1))
        if latest is not None:
            result[batch_id] = latest
    return result


def _evaluation_claim_sets(db: Session, run_ids: set[int], rule_id: str | None = None) -> tuple[set[int], set[int], set[int]]:
    if not run_ids:
        return set(), set(), set()
    base = [RuleEvaluation.run_id.in_(run_ids), RuleEvaluation.claim_id.is_not(None)]
    assessed = set(db.scalars(select(RuleEvaluation.claim_id).where(*base).distinct()))
    flagged_filters = [*base, RuleEvaluation.triggered.is_(True)]
    if rule_id:
        flagged_filters.append(RuleEvaluation.rule_id == rule_id)
    flagged = set(db.scalars(select(RuleEvaluation.claim_id).where(*flagged_filters).distinct()))
    partial = set(db.scalars(select(RuleEvaluation.claim_id).where(
        *base, RuleEvaluation.status.in_(["DISABLED_MISSING_DATA", "INSUFFICIENT_DATA", "ERROR"]),
    ).distinct()))
    return assessed, flagged, partial


@app.get("/api/v1/claims")
def claims(run_id: int | None = None, page: int = 1, page_size: int = 50,
           q: str | None = None, decision: str | None = None, coverage: str | None = None,
           rule_id: str | None = None, provider: str | None = None, batch_id: int | None = None,
           date_from: date | None = None, date_to: date | None = None,
           sort: str = "service_date", direction: str = "desc",
           db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    latest_by_batch = _latest_completed_runs(db) if run_id is None else {}
    relevant_runs = {run_id} if run_id is not None else set(latest_by_batch.values())
    assessed_ids, flagged_ids, partial_ids = _evaluation_claim_sets(db, relevant_runs, rule_id)
    stmt = select(Claim)
    if batch_id is not None:
        stmt = stmt.where(Claim.import_batch_id == batch_id)
    if provider:
        stmt = stmt.where(Claim.provider_token == provider)
    if date_from:
        stmt = stmt.where(Claim.service_date >= date_from)
    if date_to:
        stmt = stmt.where(Claim.service_date <= date_to)
    rows = list(db.scalars(stmt))
    needle = (q or "").strip().casefold()
    if needle:
        rows = [row for row in rows if needle in " ".join((row.source_claim_id, row.member_token,
            row.provider_token, row.network_id or "", row.claim_type)).casefold()]
    if rule_id:
        rows = [row for row in rows if row.id in flagged_ids]
    normalized_decision = (decision or "").casefold()
    if normalized_decision == "flagged":
        rows = [row for row in rows if row.id in flagged_ids]
    elif normalized_decision in {"no_flag", "no flag detected"}:
        rows = [row for row in rows if row.id in assessed_ids and row.id not in flagged_ids]
    elif normalized_decision in {"unevaluated", "not evaluated"}:
        rows = [row for row in rows if row.id not in assessed_ids]
    normalized_coverage = (coverage or "").casefold()
    if normalized_coverage == "partial":
        rows = [row for row in rows if row.id in partial_ids]
    elif normalized_coverage == "complete":
        rows = [row for row in rows if row.id in assessed_ids and row.id not in partial_ids]
    elif normalized_coverage in {"unevaluated", "not evaluated"}:
        rows = [row for row in rows if row.id not in assessed_ids]
    sort_key = {
        "claim_id": lambda row: row.source_claim_id.casefold(),
        "provider": lambda row: row.provider_token.casefold(),
        "net_amount": lambda row: Decimal(row.net_amount),
        "service_date": lambda row: (row.service_date, row.id),
    }.get(sort, lambda row: (row.service_date, row.id))
    rows.sort(key=sort_key, reverse=direction.casefold() != "asc")
    total = len(rows)
    page_size = max(1, min(page_size, 200)); page = max(1, page)
    rows = rows[(page - 1) * page_size:page * page_size]
    evaluations_by_claim: dict[int, list[RuleEvaluation]] = {}
    claim_ids = [row.id for row in rows]
    if claim_ids and relevant_runs:
        for evaluation in db.scalars(select(RuleEvaluation).where(
            RuleEvaluation.claim_id.in_(claim_ids), RuleEvaluation.run_id.in_(relevant_runs))):
            evaluations_by_claim.setdefault(evaluation.claim_id, []).append(evaluation)
    items = []
    for row in rows:
        selected_run = run_id if run_id is not None else latest_by_batch.get(row.import_batch_id)
        evals = evaluations_by_claim.get(row.id, []) if selected_run else []
        fired = [x for x in evals if x.triggered]
        disabled = [x for x in evals if x.status in {"DISABLED_MISSING_DATA", "INSUFFICIENT_DATA", "ERROR"}]
        assessed = bool(evals)
        primary_rule = db.get(RuleRecord, fired[0].rule_id) if fired else None
        items.append({"id": row.id, "claim_id": row.source_claim_id, "member": row.member_token,
            "provider": row.provider_token, "network_id": row.network_id, "claim_type": row.claim_type,
            "service_date": row.service_date, "submitted_amount": row.submitted_amount,
            "net_amount": row.net_amount, "paid_amount": row.paid_amount,
            "decision": "Flagged" if fired else "No flag detected" if assessed else "Not evaluated",
            "coverage": "Partial" if disabled else "Complete" if assessed else "Not evaluated",
            "primary_reason": primary_rule.name if primary_rule else "No review reason triggered" if assessed else "Run evaluation for this batch",
            "triggered_rules": len(fired), "evaluation_run_id": selected_run})
    return {"items": items, "page": page, "page_size": page_size, "total": total,
            "scope": {"run_id": run_id, "batch_id": batch_id, "query": q, "decision": decision,
                      "coverage": coverage, "rule_id": rule_id, "provider": provider,
                      "date_from": date_from, "date_to": date_to, "sort": sort, "direction": direction},
            "available": {"providers": list(db.scalars(select(Claim.provider_token).distinct().order_by(Claim.provider_token))),
                          "batches": [{"id": item.id, "filename": item.filename} for item in db.scalars(
                              select(ImportBatch).where(ImportBatch.status == "COMMITTED").order_by(ImportBatch.id.desc()))]}}


DISPOSITION_LABELS = {
    "PREPAY_REVIEW": "Review before payment",
    "POSTPAY_AUDIT": "Review after payment",
    "REPRICE": "Check payment calculation",
    "MONITOR_ONLY": "Monitor and verify",
    "REFER_SIU": "Consider specialist investigation",
    "PEND_DOCUMENTS": "Request supporting documents",
}


def _plain_field_name(path: str) -> str:
    return path.split(".")[-1].replace("_", " ").capitalize()


def _evaluation_presentation(evaluation: RuleEvaluation, contract, evidence: dict,
                             linked_claim: Claim | None = None) -> dict:
    observed = evidence.get("observed")
    expected = evidence.get("expected")
    unit = "days" if contract.primitive == "date_window" else next(
        (parameter.unit for parameter in contract.parameters if parameter.unit), None)
    observed_text = f"{observed} {unit}" if observed is not None and unit else str(observed if observed is not None else "Unavailable")
    expected_text = f"{expected} {unit}" if expected is not None and unit else str(expected if expected is not None else "Unavailable")
    limitations = []
    if evidence.get("exclusions_unavailable"):
        limitations.append("Some legitimate exceptions could not be checked from the available data.")
    is_readmission = contract.rule_id == "CLN-05-R02"
    if is_readmission:
        comparison = f"{observed_text} is inside the configured {expected}-day review window."
        headline = f"Possible {contract.name.lower()} within the review window"
        why = (f"The linked earlier claim was {observed_text} before this claim, which is inside the "
               f"configured {expected}-day review window.") if linked_claim else (
               f"The imported source reports a gap of {observed_text}, inside the configured "
               f"{expected}-day review window, but the earlier claim is not linked in this dataset.")
        if linked_claim is None:
            limitations.append("The earlier encounter needed to verify this timing signal is not linked; confirm it before acting.")
    else:
        operator = evidence.get("operator") or "compared with"
        comparison = f"{observed_text} {operator} {expected_text}."
        headline = contract.name
        why = f"The observed {_plain_field_name(contract.required_fields[0]).lower()} was {observed_text}; the review boundary was {expected_text}."
    return {
        "headline": headline,
        "why_flagged": why,
        "comparison": comparison,
        "observed_label": _plain_field_name(contract.required_fields[0]),
        "observed_display": observed_text,
        "expected_label": "Configured review boundary",
        "expected_display": expected_text,
        "action": DISPOSITION_LABELS.get(evaluation.disposition, evaluation.disposition.replace("_", " ").title()),
        "limitations": limitations,
        "requires_linked_record": is_readmission,
        "linked_claim": None if linked_claim is None else {
            "id": linked_claim.id, "claim_id": linked_claim.source_claim_id,
            "service_date": linked_claim.service_date, "provider": linked_claim.provider_token,
            "net_amount": linked_claim.net_amount,
        },
        "technical_reference": {"rule_id": evaluation.rule_id, "reason_code": evaluation.reason_code},
    }


@app.get("/api/v1/overview")
def overview(db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    """Return population-wide decision counts without treating unassessed claims as clean."""
    total_claims, total_amount = db.execute(select(
        func.count(Claim.id), func.coalesce(func.sum(Claim.net_amount), 0),
    )).one()
    latest_by_batch = _latest_completed_runs(db)
    latest_run_ids = list(latest_by_batch.values())

    assessed = flagged = partial = 0
    priority: list[dict] = []
    if latest_run_ids:
        assessed = db.scalar(select(func.count(func.distinct(RuleEvaluation.claim_id))).where(
            RuleEvaluation.run_id.in_(latest_run_ids), RuleEvaluation.claim_id.is_not(None),
        )) or 0
        flagged = db.scalar(select(func.count(func.distinct(RuleEvaluation.claim_id))).where(
            RuleEvaluation.run_id.in_(latest_run_ids), RuleEvaluation.triggered.is_(True),
        )) or 0
        partial = db.scalar(select(func.count(func.distinct(RuleEvaluation.claim_id))).where(
            RuleEvaluation.run_id.in_(latest_run_ids),
            RuleEvaluation.status.in_(["DISABLED_MISSING_DATA", "INSUFFICIENT_DATA", "ERROR"]),
        )) or 0
        priority_rows = db.scalars(select(Claim).join(
            RuleEvaluation, RuleEvaluation.claim_id == Claim.id,
        ).where(
            RuleEvaluation.run_id.in_(latest_run_ids), RuleEvaluation.triggered.is_(True),
        ).distinct().order_by(Claim.service_date.desc(), Claim.id.desc()).limit(5)).all()
        for claim in priority_rows:
            reason_ids = list(db.scalars(select(RuleEvaluation.rule_id).where(
                RuleEvaluation.run_id.in_(latest_run_ids),
                RuleEvaluation.claim_id == claim.id,
                RuleEvaluation.triggered.is_(True),
            )))
            reasons = [db.get(RuleRecord, rule_id).name for rule_id in reason_ids if db.get(RuleRecord, rule_id)]
            claim_partial = db.scalar(select(func.count(RuleEvaluation.id)).where(
                RuleEvaluation.run_id.in_(latest_run_ids),
                RuleEvaluation.claim_id == claim.id,
                RuleEvaluation.status.in_(["DISABLED_MISSING_DATA", "INSUFFICIENT_DATA", "ERROR"]),
            )) or 0
            priority.append({
                "id": claim.id, "claim_id": claim.source_claim_id, "member": claim.member_token,
                "provider": claim.provider_token, "network_id": claim.network_id,
                "claim_type": claim.claim_type, "service_date": claim.service_date,
                "submitted_amount": claim.submitted_amount, "net_amount": claim.net_amount,
                "paid_amount": claim.paid_amount, "decision": "Flagged",
                "coverage": "Partial" if claim_partial else "Complete",
                "primary_reason": min(reasons, default="Triggered control"),
                "triggered_rules": len(reason_ids),
            })
    assessed_ids, flagged_ids, partial_ids = _evaluation_claim_sets(db, set(latest_run_ids))
    assessed_amount = db.scalar(select(func.coalesce(func.sum(Claim.net_amount), 0)).where(Claim.id.in_(assessed_ids))) if assessed_ids else 0
    flagged_amount = db.scalar(select(func.coalesce(func.sum(Claim.net_amount), 0)).where(Claim.id.in_(flagged_ids))) if flagged_ids else 0
    runs = list(db.scalars(select(EvaluationRun).where(EvaluationRun.id.in_(latest_run_ids)).order_by(EvaluationRun.id.desc()))) if latest_run_ids else []
    return {
        "total_claims": total_claims,
        "total_amount": total_amount,
        "assessed_claims": assessed,
        "flagged_claims": flagged,
        "no_flag_claims": max(0, assessed - flagged),
        "unevaluated_claims": max(0, total_claims - assessed),
        "partial_claims": partial,
        "assessed_amount": assessed_amount,
        "flagged_amount": flagged_amount,
        "provenance": [{"run_id": run.id, "batch_id": run.batch_id, "analysis_date": run.analysis_date,
                        "coverage": run.coverage, "status": run.status, "completed_at": run.completed_at}
                       for run in runs],
        "readiness": "ENGINEERING_READY_ON_SYNTHETIC_DATA",
        "priority_claims": priority,
    }


@app.get("/api/v1/claims/{claim_id}")
def claim_detail(claim_id: int, db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    claim = db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(404, "Claim not found")
    run = db.scalar(select(EvaluationRun).where(EvaluationRun.batch_id == claim.import_batch_id,
        EvaluationRun.status.in_(["COMPLETED", "COMPLETED_WITH_ERRORS"])).order_by(EvaluationRun.id.desc()).limit(1))
    evals = list(db.scalars(select(RuleEvaluation).where(RuleEvaluation.claim_id == claim_id,
        RuleEvaluation.run_id == run.id).order_by(RuleEvaluation.triggered.desc(), RuleEvaluation.rule_id))) if run else []
    fact_rows = list(db.scalars(select(CanonicalFact).where(CanonicalFact.claim_id == claim_id)))
    fact_values: dict[str, object] = {}
    for fact in fact_rows:
        value = fact.value_number if fact.value_number is not None else fact.value_date if fact.value_date is not None else fact.value_text
        fact_values[fact.field_name] = value
    evaluations = []
    for evaluation in evals:
        evidence = json.loads(evaluation.evidence_json or "{}")
        contract = CONTRACTS.get(evaluation.rule_id)
        presentation = None
        if contract is not None:
            linked_claim = None
            if evaluation.triggered and contract.rule_id == "CLN-05-R02":
                linked_record = next((record for record in evidence.get("evidence_records", [])
                                      if record.get("relationship") and record.get("claim_id")), None)
                linked_claim = db.get(Claim, linked_record["claim_id"]) if linked_record else None
            presentation = _evaluation_presentation(evaluation, contract, evidence, linked_claim)
        evaluations.append({"rule_id": evaluation.rule_id, "status": evaluation.status,
            "triggered": evaluation.triggered, "reason_code": evaluation.reason_code,
            "disposition": evaluation.disposition, "score": evaluation.score,
            "exposure": evaluation.exposure, "evidence": evidence, "presentation": presentation})
    disabled_count = sum(item.status in {"DISABLED_MISSING_DATA", "INSUFFICIENT_DATA", "ERROR"} for item in evals)
    assessed_count = sum(item.status in {"TRIGGERED", "PASSED", "NOT_APPLICABLE"} for item in evals)
    limited = bool(disabled_count or any(item.status in {"ERROR", "INSUFFICIENT_DATA"} for item in evals))
    return {"claim": {"id": claim.id, "claim_id": claim.source_claim_id, "member": claim.member_token,
        "provider": claim.provider_token, "network_id": claim.network_id, "service_date": claim.service_date,
        "amounts": {"submitted": claim.submitted_amount, "net": claim.net_amount, "paid": claim.paid_amount},
        "source_profile": claim.source_profile, "version_id": claim.version_id,
        "context": {"admission_date": fact_values.get("encounter.admission_date"),
            "discharge_date": fact_values.get("encounter.discharge_date"),
            "diagnosis_code": fact_values.get("diagnosis.primary_code"),
            "diagnosis_description": fact_values.get("diagnosis.description")}},
        "evaluation_state": "ASSESSED" if run else "NOT_EVALUATED", "evaluation_run_id": run.id if run else None,
        "coverage_summary": {"catalogue_controls": 149, "controls_with_results": assessed_count,
            "controls_unavailable": disabled_count, "limited": limited,
            "message": (f"Limited assessment: {assessed_count} of 149 controls produced a result; "
                        f"{disabled_count} could not run with the available data.") if run and limited else
                       "All executable controls produced a result." if run else "This claim has not been evaluated."},
        "evaluations": evaluations}


@app.get("/api/v1/claims/{claim_id}/analysis")
def claim_analysis(claim_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    return claim_detail(claim_id, db, user)


@app.get("/api/v1/providers")
def providers(db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    rows = db.execute(select(Claim.provider_token, func.count(Claim.id), func.sum(Claim.net_amount)).group_by(Claim.provider_token).order_by(func.sum(Claim.net_amount).desc())).all()
    amounts = [Decimal(a or 0) for _, _, a in rows]
    summary = robust_summary(amounts)
    latest_runs = set(_latest_completed_runs(db).values())
    assessed_ids, flagged_ids, partial_ids = _evaluation_claim_sets(db, latest_runs)
    claims_by_provider: dict[str, list[Claim]] = {}
    for claim in db.scalars(select(Claim)):
        claims_by_provider.setdefault(claim.provider_token, []).append(claim)
    return {"items": [{"provider": p, "claims": n, "associated_amount": a,
                        "assessed_claims": sum(claim.id in assessed_ids for claim in claims_by_provider.get(p, [])),
                        "flagged_claims": sum(claim.id in flagged_ids for claim in claims_by_provider.get(p, [])),
                        "limited_claims": sum(claim.id in partial_ids for claim in claims_by_provider.get(p, [])),
                        "peer_level_used": "all mapped providers — exploratory fallback", "peer_size": len(rows),
                        "peer_median": summary["median"], "support": "exploratory" if len(rows) >= 20 else "insufficient",
                        "limitation": "Specialty, provider type and geography are not available for a clinically comparable peer group. This broad comparison is exploratory only."}
                       for p, n, a in rows],
            "methodology": "Provider totals use committed claims. Assessment counts use the latest completed run for each batch. Broad all-provider comparisons are not clinical benchmarks."}


@app.get("/api/v1/providers/{provider_token}")
def provider_detail(provider_token: str, db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    claims = list(db.scalars(select(Claim).where(Claim.provider_token == provider_token).order_by(Claim.service_date)))
    if not claims:
        raise HTTPException(404, "Provider not found")
    all_rows = db.execute(select(Claim.provider_token, func.count(Claim.id), func.sum(Claim.net_amount)).group_by(Claim.provider_token)).all()
    amounts = [Decimal(value or 0) for _, _, value in all_rows]
    summary = robust_summary(amounts)
    latest_runs = set(_latest_completed_runs(db).values())
    assessed_ids, flagged_ids, partial_ids = _evaluation_claim_sets(db, latest_runs)
    monthly: dict[str, dict[str, object]] = {}
    for claim in claims:
        key = claim.service_date.strftime("%Y-%m")
        item = monthly.setdefault(key, {"period": key, "claims": 0, "assessed": 0, "flagged": 0,
                                       "limited": 0, "amount": Decimal("0")})
        item["claims"] += 1; item["amount"] += Decimal(claim.net_amount)
        item["assessed"] += claim.id in assessed_ids; item["flagged"] += claim.id in flagged_ids
        item["limited"] += claim.id in partial_ids
    provider_total = sum((Decimal(row.net_amount) for row in claims), Decimal("0"))
    peer_median = summary["median"]
    return {"provider": provider_token, "metrics": {"claims": len(claims),
            "associated_amount": str(sum((Decimal(row.net_amount) for row in claims), Decimal("0"))),
            "average_claim": str(sum((Decimal(row.net_amount) for row in claims), Decimal("0")) / len(claims)),
            "assessed_claims": sum(row.id in assessed_ids for row in claims),
            "flagged_claims": sum(row.id in flagged_ids for row in claims),
            "limited_claims": sum(row.id in partial_ids for row in claims)},
            "peer": {"level_used": "all mapped providers — exploratory fallback", "size": len(all_rows),
                     "median_associated_amount": str(summary["median"]) if summary["median"] is not None else None,
                     "difference_from_median": str(provider_total - peer_median) if peer_median is not None else None,
                     "support": "exploratory" if len(all_rows) >= 20 else "insufficient",
                     "limitation": "This fallback mixes providers without matching specialty, type or geography. It is directional context, not a comparable clinical benchmark."},
            "trend": [{**item, "amount": str(item["amount"])} for item in monthly.values()],
            "contributing_claims": [{"id": row.id, "claim_id": row.source_claim_id, "service_date": row.service_date,
                                     "amount": row.net_amount, "network_id": row.network_id,
                                     "assessment": "Review needed" if row.id in flagged_ids else "No signal in runnable controls" if row.id in assessed_ids else "Not evaluated",
                                     "coverage": "Limited" if row.id in partial_ids else "Complete" if row.id in assessed_ids else "Not evaluated"}
                                    for row in reversed(claims)],
            "methodology": "Counts and trends use committed claims; assessment states use the latest completed run for each batch."}


@app.get("/api/v1/providers/{provider_token}/claims")
def provider_claims(provider_token: str, db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    rows = list(db.scalars(select(Claim).where(Claim.provider_token == provider_token).order_by(Claim.service_date.desc())))
    return {"items": [{"id": row.id, "claim_id": row.source_claim_id, "service_date": row.service_date,
                       "net_amount": row.net_amount, "network_id": row.network_id} for row in rows], "total": len(rows)}


@app.get("/api/v1/networks")
def networks(db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    rows = db.execute(select(Claim.network_id, func.count(func.distinct(Claim.id)), func.sum(Claim.net_amount),
        func.count(func.distinct(Claim.provider_token)), func.count(func.distinct(Claim.member_token)),
        func.min(Claim.service_date), func.max(Claim.service_date))
        .where(Claim.network_id.is_not(None)).group_by(Claim.network_id)).all()
    items = []
    for n, c, a, providers, members, period_start, period_end in rows:
        network_claims = list(db.scalars(select(Claim).where(Claim.network_id == n)))
        metrics = provider_graph(network_claims, n)["metrics"]
        items.append({"network_id": n, "distinct_claims": c, "distinct_associated_amount": a,
                      "providers": providers, "members": members, "period_start": period_start,
                      "period_end": period_end, "shared_members": metrics["multi_provider_members"],
                      "review_reason": "Members with claims from multiple providers and high-volume provider–member links"})
    return {"items": items, "methodology": "Administrative boundaries come only from supplied network IDs; relationships are observed claims, not inferred coordination."}


@app.get("/api/v1/networks/{network_id}")
def network_detail(network_id: str, db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    claims = list(db.scalars(select(Claim).where(Claim.network_id == network_id)))
    if not claims:
        raise HTTPException(404, "Explicit network not found")
    graph = provider_graph(claims, network_id)
    claims_by_id = {claim.id: claim for claim in claims}
    for edge in graph["edges"]:
        edge["claim_evidence"] = [{"id": claims_by_id[claim_id].id,
            "claim_id": claims_by_id[claim_id].source_claim_id,
            "service_date": claims_by_id[claim_id].service_date,
            "net_amount": claims_by_id[claim_id].net_amount,
            "provider": claims_by_id[claim_id].provider_token,
            "member": claims_by_id[claim_id].member_token}
            for claim_id in edge["claim_ids"] if claim_id in claims_by_id]
    graph["display_summary"] = {"nodes_shown": len(graph["nodes"]), "nodes_total": graph["metrics"]["total_node_count"],
        "edges_shown": len(graph["edges"]), "edges_total": graph["metrics"]["total_edge_count"],
        "selection_method": "highest claim-count provider-member links"}
    return graph


@app.get("/api/v1/networks/{network_id}/graph")
def network_graph(network_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    return network_detail(network_id, db, user)


@app.get("/api/v1/networks/{network_id}/export.csv")
def network_export(network_id: str, db: Session = Depends(get_db), _user: User = Depends(current_user)):
    claims = list(db.scalars(select(Claim).where(Claim.network_id == network_id)))
    if not claims:
        raise HTTPException(404, "Explicit network not found")
    graph = provider_graph(claims, network_id, max_nodes=10**9, max_edges=10**9)
    generated = datetime.utcnow().isoformat() + "Z"
    fields = ["network_id", "provider", "member", "source_claim_id", "service_date",
              "claim_amount", "relationship_claim_count", "relationship_associated_amount",
              "generated_at_utc", "interpretation_boundary"]
    stream = io.StringIO()
    writer = __import__("csv").DictWriter(stream, fieldnames=fields); writer.writeheader()
    for edge in graph["edges"]:
        for claim_id in edge["claim_ids"]:
            claim = db.get(Claim, claim_id)
            if claim is None:
                continue
            row = {"network_id": network_id, "provider": claim.provider_token,
                   "member": claim.member_token, "source_claim_id": claim.source_claim_id,
                   "service_date": str(claim.service_date), "claim_amount": str(claim.net_amount),
                   "relationship_claim_count": edge["claim_count"],
                   "relationship_associated_amount": edge["associated_amount"],
                   "generated_at_utc": generated,
                   "interpretation_boundary": "Observed administrative claim link; not evidence of coordination or wrongdoing."}
            writer.writerow({key: "'" + value if isinstance(value, str) and value[:1] in "=+-@" else value for key, value in row.items()})
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=network-{network_id}.csv"})


@app.get("/api/v1/data/readiness")
def data_readiness(db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    datasets = set(db.scalars(select(CanonicalFact.dataset).distinct()))
    ready = sum(set(contract.required_datasets) <= datasets for contract in CONTRACTS.values())
    partial = sum(bool(set(contract.required_datasets) & datasets) and not set(contract.required_datasets) <= datasets for contract in CONTRACTS.values())
    return {"available_datasets": sorted(datasets), "rules_ready": ready, "rules_partial": partial,
            "rules_disabled_missing_data": 149 - ready, "catalogue": {"total": 164, "executable": 149, "deferred": 12, "excluded": 3}}


@app.get("/api/v1/data/profile")
def data_profile(db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    total, earliest, latest, providers_count, members_count = db.execute(select(func.count(Claim.id), func.min(Claim.service_date), func.max(Claim.service_date), func.count(func.distinct(Claim.provider_token)), func.count(func.distinct(Claim.member_token)))).one()
    latest_profile = db.scalar(select(DatasetProfile).order_by(DatasetProfile.created_at.desc(), DatasetProfile.id.desc()).limit(1))
    return {"claims": total, "period_start": earliest, "period_end": latest, "providers": providers_count,
            "members": members_count,
            "safety_status": latest_profile.safety_status if latest_profile else "TOKENIZED_LOCAL_DATA_EXPECTED",
            "mapping_status": latest_profile.mapping_status if latest_profile else "UNCONFIRMED",
            "dataset_name": latest_profile.dataset_name if latest_profile else None,
            "limitations": json.loads(latest_profile.limitations_json) if latest_profile else []}


@app.get("/api/v1/audit")
def audit(db: Session = Depends(get_db), _user: User = Depends(current_user)) -> list[dict]:
    rows = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(250))
    result = []
    for item in rows:
        actor = db.get(User, item.actor_user_id) if item.actor_user_id else None
        result.append({"id": item.id, "event_type": item.event_type,
            "actor": actor.username if actor else "System", "actor_role": actor.role if actor else None,
            "target_type": item.target_type, "target_id": item.target_id,
            "details": json.loads(item.detail_json or "{}"), "created_at": item.created_at})
    return result


@app.get("/api/v1/audit/events")
def audit_events(page: int = 1, page_size: int = 50, event_type: str | None = None,
                 actor: str | None = None, db: Session = Depends(get_db),
                 _user: User = Depends(current_user)) -> dict:
    stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc())
    if event_type:
        stmt = stmt.where(AuditEvent.event_type == event_type)
    rows = list(db.scalars(stmt))
    if actor:
        actor_ids = set(db.scalars(select(User.id).where(func.lower(User.username).contains(actor.casefold()))))
        rows = [row for row in rows if row.actor_user_id in actor_ids]
    total = len(rows); page = max(1, page); page_size = max(1, min(page_size, 100))
    items = []
    for item in rows[(page - 1) * page_size:page * page_size]:
        user = db.get(User, item.actor_user_id) if item.actor_user_id else None
        items.append({"id": item.id, "event_type": item.event_type,
            "actor": user.username if user else "System", "actor_role": user.role if user else None,
            "target_type": item.target_type, "target_id": item.target_id,
            "details": json.loads(item.detail_json or "{}"), "created_at": item.created_at,
            "outcome": "Failed" if "FAILED" in item.event_type else "Recorded"})
    event_types = list(db.scalars(select(AuditEvent.event_type).distinct().order_by(AuditEvent.event_type)))
    return {"items": items, "total": total, "page": page, "page_size": page_size,
            "event_types": event_types, "retention_note": "This view is paginated; records are not limited to the visible page."}


def export_rows(db: Session, batch_id: int | None = None, run_id: int | None = None,
                decision: str | None = None, coverage: str | None = None,
                provider: str | None = None, q: str | None = None,
                date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    latest_by_batch: dict[int, int] = {}
    for source_batch_id in db.scalars(select(Claim.import_batch_id).distinct()):
        latest = db.scalar(select(EvaluationRun.id).where(
            EvaluationRun.batch_id == source_batch_id,
            EvaluationRun.status.in_(["COMPLETED", "COMPLETED_WITH_ERRORS"]),
        ).order_by(EvaluationRun.id.desc()).limit(1))
        if latest is not None:
            latest_by_batch[source_batch_id] = latest
    rows: list[dict] = []
    claim_stmt = select(Claim).order_by(Claim.service_date)
    if batch_id is not None:
        claim_stmt = claim_stmt.where(Claim.import_batch_id == batch_id)
    if provider:
        claim_stmt = claim_stmt.where(Claim.provider_token == provider)
    if date_from:
        claim_stmt = claim_stmt.where(Claim.service_date >= date_from)
    if date_to:
        claim_stmt = claim_stmt.where(Claim.service_date <= date_to)
    for claim in db.scalars(claim_stmt):
        needle = (q or "").strip().casefold()
        if needle and needle not in " ".join((claim.source_claim_id, claim.member_token,
                claim.provider_token, claim.network_id or "", claim.claim_type)).casefold():
            continue
        latest_run = run_id if run_id is not None else latest_by_batch.get(claim.import_batch_id)
        evaluations = list(db.scalars(select(RuleEvaluation).where(
            RuleEvaluation.claim_id == claim.id, RuleEvaluation.run_id == latest_run,
        ))) if latest_run else []
        fired = [row for row in evaluations if row.triggered]
        disabled = [row for row in evaluations if row.status in {"DISABLED_MISSING_DATA", "INSUFFICIENT_DATA", "ERROR"}]
        evidence = [json.loads(row.evidence_json or "{}") for row in fired]
        assessment = "Flagged" if fired else "No flag detected" if evaluations else "Not evaluated"
        if decision and assessment.casefold().replace(" ", "_") != decision.casefold().replace(" ", "_"):
            continue
        coverage_label = "Partial" if disabled else "Complete" if evaluations else "Not evaluated"
        if coverage and coverage_label.casefold() != coverage.casefold().replace("unevaluated", "not evaluated"):
            continue
        rows.append({"claim_id": claim.source_claim_id, "service_date": str(claim.service_date),
                     "member_token": claim.member_token, "provider_token": claim.provider_token,
                     "network_id": claim.network_id or "", "submitted_amount": str(claim.submitted_amount),
                     "net_amount": str(claim.net_amount), "paid_amount": str(claim.paid_amount),
                     "assessment": assessment,
                     "coverage": coverage_label,
                     "triggered_rules": ";".join(sorted(row.rule_id for row in fired)),
                     "dispositions": ";".join(sorted({row.disposition for row in fired})),
                     "observed_vs_expected": ";".join(f"{item.get('observed', '—')} {item.get('operator', '')} {item.get('expected', '—')}" for item in evidence),
                     "next_verification": ";".join(dict.fromkeys(str(item.get("next_verification", "")) for item in evidence if item.get("next_verification"))),
                     "configuration_versions": json.dumps({row.rule_id: json.loads(row.evidence_json or "{}").get("configuration_versions", {}) for row in fired}),
                     "estimated_exposure": str(sum((Decimal(row.exposure) for row in fired), Decimal("0"))),
                     "evaluation_run_id": latest_run or ""})
    return rows


@app.get("/api/v1/reports/preview")
def report_preview(batch_id: int | None = None, run_id: int | None = None,
                   decision: str | None = None, coverage: str | None = None,
                   provider: str | None = None, q: str | None = None,
                   date_from: date | None = None, date_to: date | None = None,
                   db: Session = Depends(get_db),
                   _user: User = Depends(current_user)) -> dict:
    if run_id is not None:
        run = db.get(EvaluationRun, run_id)
        if run is None:
            raise HTTPException(404, "Evaluation run not found")
        if batch_id is not None and run.batch_id != batch_id:
            raise HTTPException(422, "The selected run does not belong to the selected batch")
        batch_id = run.batch_id
    rows = export_rows(db, batch_id, run_id, decision, coverage, provider, q, date_from, date_to)
    return {"total_claims": len(rows), "assessed_claims": sum(row["assessment"] != "Not evaluated" for row in rows),
            "flagged_claims": sum(row["assessment"] == "Flagged" for row in rows),
            "unevaluated_claims": sum(row["assessment"] == "Not evaluated" for row in rows),
            "partial_claims": sum(row["coverage"] == "Partial" for row in rows),
            "scope": {"batch_id": batch_id, "run_id": run_id, "decision": decision,
                      "coverage": coverage, "provider": provider, "query": q,
                      "date_from": date_from, "date_to": date_to,
                      "description": "Selected batch/run population" if batch_id or run_id else "All local batches; latest completed run per batch"},
            "available_batches": [{"id": item.id, "filename": item.filename} for item in db.scalars(
                select(ImportBatch).where(ImportBatch.status == "COMMITTED").order_by(ImportBatch.id.desc()))],
            "available_runs": [{"id": item.id, "batch_id": item.batch_id, "analysis_date": item.analysis_date,
                                "status": item.status} for item in db.scalars(select(EvaluationRun).where(
                                    EvaluationRun.status.in_(["COMPLETED", "COMPLETED_WITH_ERRORS"])
                                ).order_by(EvaluationRun.id.desc()).limit(100))]}


@app.get("/api/v1/reports/{format}")
def report(format: str, batch_id: int | None = None, run_id: int | None = None,
           decision: str | None = None, coverage: str | None = None,
           provider: str | None = None, q: str | None = None,
           date_from: date | None = None, date_to: date | None = None,
           db: Session = Depends(get_db), user: User = Depends(current_user)):
    if run_id is not None:
        selected_run = db.get(EvaluationRun, run_id)
        if selected_run is None:
            raise HTTPException(404, "Evaluation run not found")
        if batch_id is not None and selected_run.batch_id != batch_id:
            raise HTTPException(422, "The selected run does not belong to the selected batch")
        batch_id = selected_run.batch_id
    rows = export_rows(db, batch_id, run_id, decision, coverage, provider, q, date_from, date_to); stamp = datetime.utcnow().isoformat() + "Z"
    scope = (f"batch {batch_id or 'all'}; run {run_id or 'latest completed per batch'}; "
             f"decision {decision or 'all'}; coverage {coverage or 'all'}; "
             f"provider {provider or 'all'}; query {q or 'none'}; "
             f"dates {date_from or 'start'} to {date_to or 'end'}")
    selected_run_ids = sorted({int(row["evaluation_run_id"]) for row in rows if row["evaluation_run_id"]})
    if run_id is not None and run_id not in selected_run_ids:
        selected_run_ids.append(run_id)
    run_snapshots = []
    for selected_run_id in selected_run_ids:
        snapshot_run = db.get(EvaluationRun, selected_run_id)
        if snapshot_run is None:
            continue
        snapshot = snapshot_run.configuration_snapshot or "[]"
        run_snapshots.append({"run_id": selected_run_id, "batch_id": snapshot_run.batch_id,
            "analysis_date": str(snapshot_run.analysis_date), "configuration_snapshot": json.loads(snapshot),
            "configuration_snapshot_hash": hashlib.sha256(snapshot.encode("utf-8")).hexdigest()})
    snapshot_hashes = ";".join(f"run-{item['run_id']}:{item['configuration_snapshot_hash']}" for item in run_snapshots)
    snapshot_manifest_hash = hashlib.sha256(json.dumps(run_snapshots, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()
    rows = [{**row, "record_type": "claim", "generated_at_utc": stamp, "exported_by_role": user.role,
             "export_scope": scope,
             "catalogue_scope": "164 total; 149 executable; 12 deferred; 3 excluded",
             "run_configuration_snapshot_hashes": snapshot_hashes,
             "run_configuration_manifest_hash": snapshot_manifest_hash} for row in rows]
    db.add(AuditEvent(event_type="REPORT_EXPORTED", actor_user_id=user.id, target_type="report", target_id=format,
        detail_json=json.dumps({"scope": scope, "row_count": len(rows), "batch_id": batch_id,
                                "run_id": run_id, "decision": decision, "coverage": coverage,
                                "provider": provider, "query": q,
                                "date_from": str(date_from) if date_from else None,
                                "date_to": str(date_to) if date_to else None}))); db.commit()
    if format == "csv":
        import csv
        empty_fields = ["record_type", "claim_id", "assessment", "coverage", "evaluation_run_id", "generated_at_utc",
                        "exported_by_role", "export_scope", "catalogue_scope", "run_configuration_snapshot_hashes",
                        "run_configuration_manifest_hash"]
        csv_rows = rows or [{"record_type": "metadata", "claim_id": "", "assessment": "", "coverage": "",
            "evaluation_run_id": run_id or "", "generated_at_utc": stamp, "exported_by_role": user.role,
            "export_scope": scope, "catalogue_scope": "164 total; 149 executable; 12 deferred; 3 excluded",
            "run_configuration_snapshot_hashes": snapshot_hashes,
            "run_configuration_manifest_hash": snapshot_manifest_hash}]
        stream = io.StringIO(); writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]) if csv_rows else empty_fields); writer.writeheader()
        for row in csv_rows:
            writer.writerow({k: ("'" + v if isinstance(v, str) and v[:1] in "=+-@" else v) for k, v in row.items()})
        return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=claims.csv"})
    if format == "xlsx":
        output = io.BytesIO(); book = Workbook(output, {"in_memory": True}); sheet = book.add_worksheet("Claims"); meta = book.add_worksheet("Metadata"); configs = book.add_worksheet("Configuration history"); snapshots = book.add_worksheet("Run snapshots")
        headers = list(rows[0]) if rows else ["claim_id", "assessment", "coverage", "evaluation_run_id",
                                             "generated_at_utc", "exported_by_role", "export_scope", "catalogue_scope"]
        for col, value in enumerate(headers): sheet.write(0, col, value)
        for r, row in enumerate(rows, 1):
            for c, key in enumerate(headers): sheet.write(r, c, row[key])
        for r, pair in enumerate((("Generated", stamp), ("User role", user.role),
            ("Scope", scope), ("Run configuration manifest SHA-256", snapshot_manifest_hash),
            ("Disclaimer", "Decision support only; a signal is not a fraud finding."),
            ("Catalogue", "164 total; 149 executable; 12 deferred; 3 excluded"))): meta.write_row(r, 0, pair)
        configs.write_row(0, 0, ["rule_id", "parameter", "value", "version", "valid_from", "source"])
        for r, item in enumerate(db.scalars(select(ConfigurationVersion).order_by(ConfigurationVersion.rule_id, ConfigurationVersion.parameter, ConfigurationVersion.version)), 1):
            configs.write_row(r, 0, [item.rule_id, item.parameter, item.value_json, item.version, str(item.valid_from), item.source])
        snapshots.write_row(0, 0, ["run_id", "batch_id", "analysis_date", "configuration_snapshot_hash", "configuration_snapshot_json"])
        for r, item in enumerate(run_snapshots, 1):
            snapshots.write_row(r, 0, [item["run_id"], item["batch_id"], item["analysis_date"],
                item["configuration_snapshot_hash"], json.dumps(item["configuration_snapshot"], sort_keys=True)])
        book.close(); output.seek(0)
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=claims.xlsx"})
    if format == "pdf":
        flagged = sum(row["assessment"] == "Flagged" for row in rows); partial = sum(row["coverage"] == "Partial" for row in rows)
        unevaluated = sum(row["assessment"] == "Not evaluated" for row in rows)
        exposure = sum((Decimal(row["estimated_exposure"]) for row in rows), Decimal("0"))
        output = io.BytesIO(); pdf = Canvas(output, pagesize=A4); pdf.setTitle("Medical Payment Integrity Summary"); pdf.drawString(48, 800, "Medical Payment Integrity Summary"); pdf.drawString(48, 778, f"Generated: {stamp} by role {user.role}"); pdf.drawString(48, 756, f"Claims: {len(rows)}  |  Flagged: {flagged}  |  Unevaluated: {unevaluated}"); pdf.drawString(48, 734, f"Partial coverage: {partial}  |  Rule-estimated amount: AED {exposure}"); pdf.drawString(48, 712, f"Scope: {scope[:92]}"); pdf.drawString(48, 690, "Catalogue: 149 executable; 12 deferred; 3 model-excluded"); pdf.drawString(48, 668, "Run configuration manifest SHA-256:"); pdf.drawString(48, 652, snapshot_manifest_hash); pdf.drawString(48, 630, "Decision support only. Amounts are not confirmed loss or recoverable value."); pdf.save(); output.seek(0)
        return StreamingResponse(output, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=summary.pdf"})
    raise HTTPException(404, "Supported formats: csv, xlsx, pdf")
