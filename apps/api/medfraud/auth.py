from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import AuditEvent, SessionToken, User
from .settings import settings

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
COOKIE_NAME = "medfraud_session"


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters")
    return ph.hash(password)


def verify_password(stored: str, password: str) -> bool:
    try:
        return ph.verify(stored, password)
    except VerifyMismatchError:
        return False


def digest_token(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def create_session(db: Session, user: User, response: Response) -> str:
    raw = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(24)
    db.add(SessionToken(token_hash=digest_token(raw), user_id=user.id, csrf_token=csrf,
                        expires_at=datetime.utcnow() + timedelta(hours=settings.session_hours)))
    db.add(AuditEvent(event_type="AUTH_LOGIN", actor_user_id=user.id, target_type="session"))
    db.commit()
    response.set_cookie(COOKIE_NAME, raw, httponly=True, samesite="strict", secure=False,
                        max_age=settings.session_hours * 3600, path="/")
    return csrf


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    raw = request.cookies.get(COOKIE_NAME)
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    token = db.scalar(select(SessionToken).where(SessionToken.token_hash == digest_token(raw)))
    if not token or token.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    user = db.get(User, token.user_id)
    if not user or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator role required")
    return user


def verify_csrf(request: Request, db: Session = Depends(get_db)) -> None:
    raw = request.cookies.get(COOKIE_NAME)
    supplied = request.headers.get("x-csrf-token")
    token = db.scalar(select(SessionToken).where(SessionToken.token_hash == digest_token(raw or "")))
    if not token or not supplied or not secrets.compare_digest(token.csrf_token, supplied):
        raise HTTPException(status_code=403, detail="CSRF validation failed")

