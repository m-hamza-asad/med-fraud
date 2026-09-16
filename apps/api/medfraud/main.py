from __future__ import annotations

import io
import json
import secrets
from datetime import date, datetime
from decimal import Decimal

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
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
from .database import Base, engine, get_db
from .evaluators import evaluate_catalogue_rule, parse_facts
from .imports import PROFILES, checksum, parse_rows, safe_filename, validate_rows
from .models import (AuditEvent, Claim, ConfigurationVersion, EvaluationRun, ImportBatch,
                     ImportIssue, RuleEvaluation, RuleRecord, SessionToken, User)
from .registry import REGISTRY

app = FastAPI(title="Shahai Medical Payment Integrity", version=__version__, docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class ConfigBody(BaseModel):
    value: float = Field(ge=0, le=1000000)
    unit: str = Field(default="score", max_length=32)
    effective_at: datetime


class EvaluationBody(BaseModel):
    batch_id: int
    analysis_date: date


def rule_dict(rule: RuleRecord) -> dict:
    item = json.loads(rule.metadata_json)
    return {**item, "rule_id": rule.rule_id, "scope_state": rule.scope_state,
            "operational_state": rule.operational_state, "reason_code": rule.reason_code}


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        for item in REGISTRY:
            if not db.get(RuleRecord, item["rule_id"]):
                db.add(RuleRecord(rule_id=item["rule_id"], scenario_id=item["scenario_id"], name=item["rule_name"],
                                  type_expression=item["type_expression"], stage=item["canonical_stage"] or item["stage_label"],
                                  scope_state=item["scope_state"], operational_state=item["operational_state"],
                                  version=item["version"], reason_code=item["reason_code"], metadata_json=json.dumps(item)))
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


@app.post("/api/v1/configuration/{rule_id}", dependencies=[Depends(verify_csrf)])
def configure(rule_id: str, body: ConfigBody, db: Session = Depends(get_db), user: User = Depends(require_admin)) -> dict:
    rule = db.get(RuleRecord, rule_id)
    if not rule:
        raise HTTPException(404, "Rule not found")
    if rule.scope_state != "EXECUTABLE":
        raise HTTPException(409, "Excluded and deferred rules cannot be configured")
    current = db.scalar(select(ConfigurationVersion).where(ConfigurationVersion.rule_id == rule_id, ConfigurationVersion.valid_to.is_(None)).order_by(ConfigurationVersion.version.desc()))
    next_version = (current.version + 1) if current else 1
    if current:
        current.valid_to = body.effective_at
    row = ConfigurationVersion(rule_id=rule_id, parameter="threshold", value_json=json.dumps(body.value), unit=body.unit, valid_from=body.effective_at, version=next_version, changed_by=user.id)
    db.add(row)
    db.add(AuditEvent(event_type="CONFIGURATION_CHANGED", actor_user_id=user.id, target_type="rule", target_id=rule_id, detail_json=json.dumps({"version": next_version})))
    db.commit()
    return {"rule_id": rule_id, "version": next_version, "effective_at": body.effective_at}


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
        return {"duplicate": True, "batch_id": existing.id, "status": existing.status, "issues": []}
    try:
        parsed = parse_rows(name, data)
        normalized, issues = validate_rows(parsed, name, analysis_date)
    except (ValueError, UnicodeDecodeError) as exc:
        normalized, issues = [], [{"severity": "error", "file": name, "sheet": None, "column_name": None, "row_number": None, "code": "PARSE_ERROR", "message": str(exc), "guidance": "Use an unencrypted .csv or .xlsx template without macros."}]
    batch = ImportBatch(checksum=file_checksum, filename=name, profile=profile, status="VALIDATED" if not any(x["severity"] == "error" for x in issues) else "INVALID", row_count=len(normalized), error_count=sum(x["severity"] == "error" for x in issues), warning_count=sum(x["severity"] == "warning" for x in issues), created_by=user.id)
    db.add(batch); db.flush()
    for item in issues:
        db.add(ImportIssue(batch_id=batch.id, **item))
    if batch.status == "VALIDATED":
        for raw in normalized:
            db.add(Claim(source_profile=profile, source_claim_id=raw["source_claim_id"], member_token=str(raw["member_token"]), provider_token=str(raw["provider_token"]), network_id=str(raw.get("network_id") or "") or None, claim_type=str(raw["claim_type"]), service_date=raw["service_date"], submitted_amount=raw["submitted_amount"], net_amount=raw["net_amount"], paid_amount=raw["paid_amount"], facts_json=raw["facts_json"], original_json=json.dumps({k: str(v) for k, v in raw.items()}), valid_from=raw["valid_from"], import_batch_id=batch.id))
        batch.status = "COMMITTED"
    db.add(AuditEvent(event_type="IMPORT_VALIDATED", actor_user_id=user.id, target_type="batch", target_id=str(batch.id), detail_json=json.dumps({"status": batch.status, "rows": batch.row_count})))
    db.commit()
    return {"duplicate": False, "batch_id": batch.id, "status": batch.status, "row_count": batch.row_count, "issues": issues}


@app.get("/api/v1/imports")
def imports(db: Session = Depends(get_db), _user: User = Depends(current_user)) -> list[dict]:
    rows = db.scalars(select(ImportBatch).order_by(ImportBatch.created_at.desc()).limit(100))
    return [{"id": x.id, "filename": x.filename, "profile": x.profile, "status": x.status, "row_count": x.row_count, "errors": x.error_count, "warnings": x.warning_count, "created_at": x.created_at} for x in rows]


@app.post("/api/v1/evaluations")
def run_evaluation(body: EvaluationBody, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    batch = db.get(ImportBatch, body.batch_id)
    if not batch or batch.status != "COMMITTED":
        raise HTTPException(409, "A committed import batch is required")
    rules_by_id = {x.rule_id: rule_dict(x) for x in db.scalars(select(RuleRecord).where(RuleRecord.scope_state == "EXECUTABLE"))}
    config = [{"rule_id": x.rule_id, "parameter": x.parameter, "value": json.loads(x.value_json), "version": x.version} for x in db.scalars(select(ConfigurationVersion).where(ConfigurationVersion.valid_from <= datetime.combine(body.analysis_date, datetime.max.time()), ConfigurationVersion.valid_to.is_(None)))]
    run = EvaluationRun(batch_id=batch.id, analysis_date=body.analysis_date, status="RUNNING", coverage="Complete", configuration_snapshot=json.dumps(config), created_by=user.id)
    db.add(run); db.flush()
    available = {"claim_line", "diagnosis"}
    claims = list(db.scalars(select(Claim).where(Claim.import_batch_id == batch.id)))
    failures = disabled = triggered = 0
    for claim in claims:
        facts = parse_facts(claim.facts_json)
        available_claim = available | set(facts.get("available_datasets", []))
        for rule in rules_by_id.values():
            try:
                result = evaluate_catalogue_rule(rule, facts, available_claim)
                disabled += result.status == "DISABLED_MISSING_DATA"
                triggered += result.triggered
                db.add(RuleEvaluation(run_id=run.id, claim_id=claim.id, rule_id=rule["rule_id"], status=result.status, triggered=result.triggered, reason_code=rule["reason_code"], evidence_json=json.dumps(result.evidence), disposition="MONITOR_ONLY", score=result.score, exposure=result.exposure))
            except Exception as exc:
                failures += 1
                db.add(RuleEvaluation(run_id=run.id, claim_id=claim.id, rule_id=rule["rule_id"], status="ERROR", reason_code=rule["reason_code"], error_category=type(exc).__name__, evidence_json=json.dumps({"safe_message": "Evaluator failed"})))
    run.coverage = "Partial" if disabled or failures else "Complete"
    run.status = "COMPLETED_WITH_ERRORS" if failures else "COMPLETED"
    run.progress_json = json.dumps({"claims": len(claims), "rules": 149, "triggered": triggered, "disabled": disabled, "errors": failures})
    run.completed_at = datetime.utcnow()
    db.add(AuditEvent(event_type="EVALUATION_COMPLETED", actor_user_id=user.id, target_type="run", target_id=str(run.id), detail_json=run.progress_json))
    db.commit()
    return {"id": run.id, "status": run.status, "coverage": run.coverage, **json.loads(run.progress_json)}


@app.get("/api/v1/evaluations")
def evaluations(db: Session = Depends(get_db), _user: User = Depends(current_user)) -> list[dict]:
    rows = db.scalars(select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(100))
    return [{"id": x.id, "batch_id": x.batch_id, "analysis_date": x.analysis_date, "status": x.status, "coverage": x.coverage, "progress": json.loads(x.progress_json), "created_at": x.created_at} for x in rows]


@app.get("/api/v1/claims")
def claims(run_id: int | None = None, page: int = 1, page_size: int = 50, db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    if run_id is None:
        run_id = db.scalar(select(EvaluationRun.id).order_by(EvaluationRun.created_at.desc()).limit(1))
    stmt = select(Claim).order_by(Claim.service_date.desc()).offset((page - 1) * page_size).limit(min(page_size, 200))
    rows = list(db.scalars(stmt))
    items = []
    for row in rows:
        evals = list(db.scalars(select(RuleEvaluation).where(RuleEvaluation.claim_id == row.id, RuleEvaluation.run_id == run_id))) if run_id else []
        fired = [x for x in evals if x.triggered]
        disabled = [x for x in evals if x.status == "DISABLED_MISSING_DATA"]
        items.append({"id": row.id, "claim_id": row.source_claim_id, "member": row.member_token, "provider": row.provider_token, "network_id": row.network_id, "claim_type": row.claim_type, "service_date": row.service_date, "submitted_amount": row.submitted_amount, "net_amount": row.net_amount, "paid_amount": row.paid_amount, "decision": "Flagged" if fired else "No flag detected", "coverage": "Partial" if disabled else "Complete", "primary_reason": min((x.reason_code for x in fired), default="No applicable signal triggered"), "triggered_rules": len(fired)})
    return {"items": items, "page": page, "page_size": page_size, "total": db.scalar(select(func.count()).select_from(Claim))}


@app.get("/api/v1/claims/{claim_id}")
def claim_detail(claim_id: int, db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    claim = db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(404, "Claim not found")
    evals = list(db.scalars(select(RuleEvaluation).where(RuleEvaluation.claim_id == claim_id).order_by(RuleEvaluation.triggered.desc(), RuleEvaluation.rule_id)))
    return {"claim": {"id": claim.id, "claim_id": claim.source_claim_id, "member": claim.member_token, "provider": claim.provider_token, "network_id": claim.network_id, "service_date": claim.service_date, "amounts": {"submitted": claim.submitted_amount, "net": claim.net_amount, "paid": claim.paid_amount}, "source_profile": claim.source_profile, "version_id": claim.version_id}, "evaluations": [{"rule_id": x.rule_id, "status": x.status, "triggered": x.triggered, "reason_code": x.reason_code, "disposition": x.disposition, "score": x.score, "exposure": x.exposure, "evidence": json.loads(x.evidence_json)} for x in evals]}


@app.get("/api/v1/providers")
def providers(db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    rows = db.execute(select(Claim.provider_token, func.count(Claim.id), func.sum(Claim.net_amount)).group_by(Claim.provider_token).order_by(func.sum(Claim.net_amount).desc())).all()
    return {"items": [{"provider": p, "claims": n, "associated_amount": a, "peer_level_used": "specialty → encounter → payment → geography → volume"} for p, n, a in rows]}


@app.get("/api/v1/networks")
def networks(db: Session = Depends(get_db), _user: User = Depends(current_user)) -> dict:
    rows = db.execute(select(Claim.network_id, func.count(func.distinct(Claim.id)), func.sum(Claim.net_amount)).where(Claim.network_id.is_not(None)).group_by(Claim.network_id)).all()
    return {"items": [{"network_id": n, "distinct_claims": c, "distinct_associated_amount": a} for n, c, a in rows]}


@app.get("/api/v1/audit")
def audit(db: Session = Depends(get_db), _user: User = Depends(current_user)) -> list[dict]:
    rows = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(250))
    return [{"id": x.id, "event_type": x.event_type, "actor_user_id": x.actor_user_id, "target_type": x.target_type, "target_id": x.target_id, "created_at": x.created_at} for x in rows]


def export_rows(db: Session) -> list[dict]:
    return [{"claim_id": x.source_claim_id, "service_date": str(x.service_date), "member_token": x.member_token, "provider_token": x.provider_token, "network_id": x.network_id or "", "submitted_amount": str(x.submitted_amount), "net_amount": str(x.net_amount), "paid_amount": str(x.paid_amount)} for x in db.scalars(select(Claim).order_by(Claim.service_date))]


@app.get("/api/v1/reports/{format}")
def report(format: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = export_rows(db); stamp = datetime.utcnow().isoformat() + "Z"
    db.add(AuditEvent(event_type="REPORT_EXPORTED", actor_user_id=user.id, target_type="report", target_id=format)); db.commit()
    if format == "csv":
        import csv
        stream = io.StringIO(); writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ["claim_id"]); writer.writeheader()
        for row in rows:
            writer.writerow({k: ("'" + v if isinstance(v, str) and v[:1] in "=+-@" else v) for k, v in row.items()})
        return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=claims.csv"})
    if format == "xlsx":
        output = io.BytesIO(); book = Workbook(output, {"in_memory": True}); sheet = book.add_worksheet("Claims"); meta = book.add_worksheet("Metadata")
        headers = list(rows[0]) if rows else ["claim_id"]
        for col, value in enumerate(headers): sheet.write(0, col, value)
        for r, row in enumerate(rows, 1):
            for c, key in enumerate(headers): sheet.write(r, c, row[key])
        for r, pair in enumerate((("Generated", stamp), ("User role", user.role), ("Disclaimer", "Decision support only; a signal is not a fraud finding."), ("Catalogue", "164 total; 149 executable; 12 deferred; 3 excluded"))): meta.write_row(r, 0, pair)
        book.close(); output.seek(0)
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=claims.xlsx"})
    if format == "pdf":
        output = io.BytesIO(); pdf = Canvas(output, pagesize=A4); pdf.setTitle("Medical Payment Integrity Summary"); pdf.drawString(48, 800, "Medical Payment Integrity Summary"); pdf.drawString(48, 778, f"Generated: {stamp}"); pdf.drawString(48, 756, f"Claims: {len(rows)}"); pdf.drawString(48, 734, "Coverage: 149 executable; 12 deferred; 3 model-excluded"); pdf.drawString(48, 700, "Decision support only; a signal is not a fraud finding."); pdf.save(); output.seek(0)
        return StreamingResponse(output, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=summary.pdf"})
    raise HTTPException(404, "Supported formats: csv, xlsx, pdf")
