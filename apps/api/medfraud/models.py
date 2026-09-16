from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(16), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SessionToken(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    csrf_token: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ImportBatch(Base):
    __tablename__ = "import_batches"
    id: Mapped[int] = mapped_column(primary_key=True)
    checksum: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    profile: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class ImportIssue(Base):
    __tablename__ = "import_issues"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id", ondelete="CASCADE"), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    file: Mapped[str] = mapped_column(String(255))
    sheet: Mapped[str | None] = mapped_column(String(128))
    column_name: Mapped[str | None] = mapped_column(String(128))
    row_number: Mapped[int | None] = mapped_column(Integer)
    code: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    guidance: Mapped[str] = mapped_column(Text)


class Claim(Base):
    __tablename__ = "claims"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_profile: Mapped[str] = mapped_column(String(32), index=True)
    source_claim_id: Mapped[str] = mapped_column(String(128), index=True)
    version_id: Mapped[str] = mapped_column(String(64), default="v1")
    member_token: Mapped[str] = mapped_column(String(128), index=True)
    provider_token: Mapped[str] = mapped_column(String(128), index=True)
    network_id: Mapped[str | None] = mapped_column(String(128), index=True)
    claim_type: Mapped[str] = mapped_column(String(32), index=True)
    service_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    submitted_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    facts_json: Mapped[str] = mapped_column(Text, default="{}")
    original_json: Mapped[str] = mapped_column(Text, default="{}")
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    source: Mapped[str] = mapped_column(String(128), default="upload")
    import_batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"), index=True)
    __table_args__ = (Index("ix_claim_source_version", "source_profile", "source_claim_id", "version_id", unique=True),)


class ClaimLine(Base):
    __tablename__ = "claim_lines"
    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True)
    source_line_id: Mapped[str] = mapped_column(String(128))
    activity_code: Mapped[str] = mapped_column(String(64), index=True)
    code_system: Mapped[str] = mapped_column(String(32), default="LOCAL")
    units: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=1)
    submitted_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    patient_share: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    service_start: Mapped[datetime | None] = mapped_column(DateTime)
    service_end: Mapped[datetime | None] = mapped_column(DateTime)
    facts_json: Mapped[str] = mapped_column(Text, default="{}")
    __table_args__ = (Index("ix_claim_line_source", "claim_id", "source_line_id", unique=True),)


class RuleRecord(Base):
    __tablename__ = "rules"
    rule_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    scenario_id: Mapped[str] = mapped_column(String(16), index=True)
    name: Mapped[str] = mapped_column(String(255))
    type_expression: Mapped[str] = mapped_column(String(32))
    stage: Mapped[str] = mapped_column(String(32), index=True)
    scope_state: Mapped[str] = mapped_column(String(32), index=True)
    operational_state: Mapped[str | None] = mapped_column(String(16), index=True)
    version: Mapped[str] = mapped_column(String(16), default="1.0")
    reason_code: Mapped[str] = mapped_column(String(64), unique=True)
    metadata_json: Mapped[str] = mapped_column(Text)


class ConfigurationVersion(Base):
    __tablename__ = "configuration_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("rules.rule_id"), index=True)
    parameter: Mapped[str] = mapped_column(String(128))
    value_json: Mapped[str] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String(32), default="score")
    valid_from: Mapped[datetime] = mapped_column(DateTime, index=True)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime)
    version: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(128), default="POC default — not approved policy")
    source: Mapped[str] = mapped_column(String(255), default="Synthetic POC assumption")
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"), index=True)
    analysis_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    coverage: Mapped[str] = mapped_column(String(16), index=True)
    configuration_snapshot: Mapped[str] = mapped_column(Text)
    progress_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class RuleEvaluation(Base):
    __tablename__ = "rule_evaluations"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True)
    claim_id: Mapped[int | None] = mapped_column(ForeignKey("claims.id"), index=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("rules.rule_id"), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    triggered: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    reason_code: Mapped[str] = mapped_column(String(64))
    evidence_json: Mapped[str] = mapped_column(Text, default="{}")
    disposition: Mapped[str] = mapped_column(String(32), default="MONITOR_ONLY")
    score: Mapped[Decimal] = mapped_column(Numeric(8, 3), default=0)
    exposure: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    error_category: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    __table_args__ = (Index("ix_eval_unique", "run_id", "claim_id", "rule_id", unique=True),)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    target_type: Mapped[str] = mapped_column(String(64))
    target_id: Mapped[str | None] = mapped_column(String(128))
    detail_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

