from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from .database import Base, engine
from .models import SchemaMigration


@dataclass(frozen=True)
class Migration:
    version: str
    description: str


MIGRATIONS = (
    Migration("0001", "legacy foundation schema"),
    Migration("0002", "normalized facts, rule parameters, recommendations, and graph analytics"),
)


def run_migrations() -> list[str]:
    """Apply additive, idempotent schema migrations without deleting existing rows."""
    Base.metadata.create_all(engine)
    applied_now: list[str] = []
    with Session(engine) as db:
        existing = set(db.scalars(select(SchemaMigration.version)))
        for migration in MIGRATIONS:
            if migration.version not in existing:
                db.add(SchemaMigration(version=migration.version, description=migration.description))
                applied_now.append(migration.version)
        db.commit()
    return applied_now


def schema_inventory() -> dict[str, list[str]]:
    inspector = inspect(engine)
    return {
        table: sorted(column["name"] for column in inspector.get_columns(table))
        for table in sorted(inspector.get_table_names())
    }

