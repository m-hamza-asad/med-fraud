from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from medfraud.database import Base
from medfraud.models import SchemaMigration, User


def test_additive_schema_preserves_existing_rows(tmp_path: Path) -> None:
    path = tmp_path / "migration.sqlite3"
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    User.__table__.create(engine)
    with Session(engine) as db:
        db.add(User(username="preserved", password_hash="hash", role="analyst"))
        db.commit()

    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(SchemaMigration(version="0002", description="test"))
        db.commit()
        assert db.scalar(select(User.username)) == "preserved"

    with sqlite3.connect(path) as connection:
        assert connection.execute("pragma integrity_check").fetchone()[0] == "ok"
        tables = {row[0] for row in connection.execute("select name from sqlite_master where type='table'")}
    assert {"canonical_facts", "provider_relationships", "rule_parameter_definitions"} <= tables


def test_schema_creation_is_idempotent(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'clean.sqlite3').as_posix()}")
    Base.metadata.create_all(engine)
    Base.metadata.create_all(engine)
    with sqlite3.connect(tmp_path / "clean.sqlite3") as connection:
        assert connection.execute("pragma integrity_check").fetchone()[0] == "ok"

