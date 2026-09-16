from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import hash_password
from .database import Base, engine
from .models import User


def initialize(admin_password: str, analyst_password: str) -> None:
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        for username, password, role in (("admin", admin_password, "admin"), ("analyst", analyst_password, "analyst")):
            user = db.scalar(select(User).where(User.username == username))
            if user:
                user.password_hash = hash_password(password)
            else:
                db.add(User(username=username, password_hash=hash_password(password), role=role))
        db.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init"); init.add_argument("--admin-password", required=True); init.add_argument("--analyst-password", required=True)
    args = parser.parse_args()
    if args.command == "init":
        initialize(args.admin_password, args.analyst_password)
        print(json.dumps({"status": "initialized", "users": ["admin", "analyst"]}))


if __name__ == "__main__":
    main()

