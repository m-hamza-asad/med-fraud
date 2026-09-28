from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
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


class SchemaMigration(Base):
    __tablename__ = "schema_migrations"
    version: Mapped[str] = mapped_column(String(32), primary_key=True)
    description: Mapped[str] = mapped_column(String(255))
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class DatasetProfile(Base):
    __tablename__ = "dataset_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"), index=True)
    dataset_name: Mapped[str] = mapped_column(String(128), index=True)
    snapshot_hash: Mapped[str] = mapped_column(String(64), index=True)
    source_profile: Mapped[str] = mapped_column(String(32), index=True)
    safety_status: Mapped[str] = mapped_column(String(32), index=True)
    mapping_status: Mapped[str] = mapped_column(String(32), index=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    limitations_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class MappingProfile(Base):
    __tablename__ = "mapping_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    source_profile: Mapped[str] = mapped_column(String(32), index=True)
    schema_hash: Mapped[str] = mapped_column(String(64), index=True)
    mapping_json: Mapped[str] = mapped_column(Text)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ImportPreview(Base):
    __tablename__ = "import_previews"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id", ondelete="CASCADE"), unique=True)
    analysis_date: Mapped[date] = mapped_column(Date)
    normalized_rows_json: Mapped[str] = mapped_column(Text)
    mapping_profile_id: Mapped[int | None] = mapped_column(ForeignKey("mapping_profiles.id"))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CanonicalProvider(Base):
    __tablename__ = "canonical_providers"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider_token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    provider_type: Mapped[str | None] = mapped_column(String(64), index=True)
    specialty: Mapped[str | None] = mapped_column(String(128), index=True)
    facility_token: Mapped[str | None] = mapped_column(String(128), index=True)
    geography: Mapped[str | None] = mapped_column(String(128), index=True)
    ownership_group: Mapped[str | None] = mapped_column(String(128), index=True)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(128), default="upload")
    version_id: Mapped[str] = mapped_column(String(64), default="v1")
    attributes_json: Mapped[str] = mapped_column(Text, default="{}")


class CanonicalFact(Base):
    __tablename__ = "canonical_facts"
    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int | None] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True)
    claim_line_id: Mapped[int | None] = mapped_column(ForeignKey("claim_lines.id", ondelete="CASCADE"), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_key: Mapped[str] = mapped_column(String(128), index=True)
    dataset: Mapped[str] = mapped_column(String(64), index=True)
    field_name: Mapped[str] = mapped_column(String(128), index=True)
    value_type: Mapped[str] = mapped_column(String(16))
    value_text: Mapped[str | None] = mapped_column(Text)
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(24, 6))
    value_date: Mapped[date | None] = mapped_column(Date)
    value_bool: Mapped[bool | None] = mapped_column(Boolean)
    valid_from: Mapped[date | None] = mapped_column(Date, index=True)
    valid_to: Mapped[date | None] = mapped_column(Date, index=True)
    source_key: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(128), default="upload")
    version_id: Mapped[str] = mapped_column(String(64), default="v1")
    __table_args__ = (Index("ix_fact_lookup", "entity_type", "entity_key", "dataset", "field_name", "valid_from"),)


class CanonicalRelation(Base):
    __tablename__ = "canonical_relations"
    id: Mapped[int] = mapped_column(primary_key=True)
    relation_type: Mapped[str] = mapped_column(String(64), index=True)
    source_type: Mapped[str] = mapped_column(String(64), index=True)
    source_key: Mapped[str] = mapped_column(String(128), index=True)
    target_type: Mapped[str] = mapped_column(String(64), index=True)
    target_key: Mapped[str] = mapped_column(String(128), index=True)
    claim_id: Mapped[int | None] = mapped_column(ForeignKey("claims.id"), index=True)
    directed: Mapped[bool] = mapped_column(Boolean, default=True)
    weight: Mapped[Decimal] = mapped_column(Numeric(24, 6), default=1)
    associated_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    valid_from: Mapped[date | None] = mapped_column(Date, index=True)
    valid_to: Mapped[date | None] = mapped_column(Date)
    provenance: Mapped[str] = mapped_column(String(32), default="derived")
    evidence_json: Mapped[str] = mapped_column(Text, default="{}")
    __table_args__ = (Index("ix_relation_lookup", "relation_type", "source_key", "target_key", "valid_from"),)


class RuleParameterDefinition(Base):
    __tablename__ = "rule_parameter_definitions"
    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("rules.rule_id"), index=True)
    parameter_key: Mapped[str] = mapped_column(String(128))
    display_label: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    parameter_type: Mapped[str] = mapped_column(String(32))
    unit: Mapped[str | None] = mapped_column(String(32))
    provenance_class: Mapped[str] = mapped_column(String(32), index=True)
    edit_authority: Mapped[str] = mapped_column(String(32))
    default_value_json: Mapped[str] = mapped_column(Text)
    bounds_json: Mapped[str] = mapped_column(Text, default="{}")
    scope: Mapped[str] = mapped_column(String(32), default="global")
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    recommendation_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(255))
    rationale: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (UniqueConstraint("rule_id", "parameter_key", "version", name="uq_rule_parameter_version"),)


class ThresholdRecommendation(Base):
    __tablename__ = "threshold_recommendations"
    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("rules.rule_id"), index=True)
    parameter_key: Mapped[str] = mapped_column(String(128), index=True)
    dataset_snapshot_hash: Mapped[str] = mapped_column(String(64), index=True)
    method: Mapped[str] = mapped_column(String(64))
    suggested_value_json: Mapped[str | None] = mapped_column(Text)
    range_json: Mapped[str] = mapped_column(Text, default="{}")
    population_json: Mapped[str] = mapped_column(Text, default="{}")
    distribution_json: Mapped[str] = mapped_column(Text, default="{}")
    impact_json: Mapped[str] = mapped_column(Text, default="{}")
    support_level: Mapped[str] = mapped_column(String(16), index=True)
    warnings_json: Mapped[str] = mapped_column(Text, default="[]")
    feature_version: Mapped[str] = mapped_column(String(64))
    code_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ThresholdSimulation(Base):
    __tablename__ = "threshold_simulations"
    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("rules.rule_id"), index=True)
    proposed_configuration_json: Mapped[str] = mapped_column(Text)
    dataset_snapshot_hash: Mapped[str] = mapped_column(String(64), index=True)
    result_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), index=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ProviderFeatureSnapshot(Base):
    __tablename__ = "provider_feature_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider_token: Mapped[str] = mapped_column(String(128), index=True)
    period_start: Mapped[date] = mapped_column(Date, index=True)
    period_end: Mapped[date] = mapped_column(Date, index=True)
    feature_name: Mapped[str] = mapped_column(String(128), index=True)
    observed_value: Mapped[Decimal] = mapped_column(Numeric(24, 6))
    numerator: Mapped[Decimal | None] = mapped_column(Numeric(24, 6))
    denominator: Mapped[Decimal | None] = mapped_column(Numeric(24, 6))
    peer_group: Mapped[str] = mapped_column(String(255))
    peer_level_used: Mapped[str] = mapped_column(String(64))
    peer_size: Mapped[int] = mapped_column(Integer)
    peer_median: Mapped[Decimal | None] = mapped_column(Numeric(24, 6))
    percentile: Mapped[Decimal | None] = mapped_column(Numeric(8, 5))
    interval_low: Mapped[Decimal | None] = mapped_column(Numeric(24, 6))
    interval_high: Mapped[Decimal | None] = mapped_column(Numeric(24, 6))
    support_level: Mapped[str] = mapped_column(String(16))
    context_json: Mapped[str] = mapped_column(Text, default="{}")


class ProviderRelationship(Base):
    __tablename__ = "provider_relationships"
    id: Mapped[int] = mapped_column(primary_key=True)
    network_id: Mapped[str] = mapped_column(String(128), index=True)
    source_node_type: Mapped[str] = mapped_column(String(64))
    source_node_key: Mapped[str] = mapped_column(String(128), index=True)
    target_node_type: Mapped[str] = mapped_column(String(64))
    target_node_key: Mapped[str] = mapped_column(String(128), index=True)
    relationship_type: Mapped[str] = mapped_column(String(64), index=True)
    directed: Mapped[bool] = mapped_column(Boolean, default=False)
    claim_count: Mapped[int] = mapped_column(Integer, default=0)
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    weight: Mapped[Decimal] = mapped_column(Numeric(24, 6), default=0)
    associated_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    unexpectedness: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    period_start: Mapped[date] = mapped_column(Date, index=True)
    period_end: Mapped[date] = mapped_column(Date, index=True)
    provenance: Mapped[str] = mapped_column(String(32), default="derived")
    exclusion_json: Mapped[str] = mapped_column(Text, default="{}")
    evidence_json: Mapped[str] = mapped_column(Text, default="{}")
    __table_args__ = (UniqueConstraint("network_id", "source_node_key", "target_node_key", "relationship_type", "period_start", "period_end", name="uq_provider_relationship_snapshot"),)


class RuleEvidenceReference(Base):
    __tablename__ = "rule_evidence_references"
    id: Mapped[int] = mapped_column(primary_key=True)
    rule_evaluation_id: Mapped[int] = mapped_column(ForeignKey("rule_evaluations.id", ondelete="CASCADE"), index=True)
    dataset: Mapped[str] = mapped_column(String(64), index=True)
    record_type: Mapped[str] = mapped_column(String(64))
    record_id: Mapped[str] = mapped_column(String(128))
    relationship: Mapped[str] = mapped_column(String(64))
    display_json: Mapped[str] = mapped_column(Text, default="{}")
