"""Opaque revocable sessions, Argon2 passwords and owner isolation.

Local mode accepts loopback only and sees only unowned legacy projects.
Remote mode requires HTTPS and authenticated ownership; no public signup.
"""

import hashlib
import hmac
import os
import secrets
from datetime import timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pwdlib import PasswordHash
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from .database import LoginAttemptRow, LoginSessionRow, SessionLocal, UserRow, utcnow
from .schemas import AccessSession
from .security import cors_origins

router = APIRouter(prefix="/api/v1/auth", tags=["Acesso"])
passwords = PasswordHash.recommended()
COOKIE = "eletroprojeto_session"
_dummy_hash = passwords.hash(secrets.token_urlsafe(32))


def mode():
    value = os.getenv("AUTH_MODE", "local")
    if value not in ("local", "remote"):
        raise HTTPException(503, "Configuração de acesso inválida.")
    return value


def auth_session():
    with SessionLocal() as session:
        yield session


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def require_https(request):
    if request.url.scheme != "https":
        raise HTTPException(400, "Acesso remoto exige HTTPS.")


def origin_check(request):
    origin = request.headers.get("origin")
    if origin not in cors_origins(
        os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    ):
        raise HTTPException(403, "Origem não autorizada.")


def current_session(request, session):
    raw = request.cookies.get(COOKIE, "")
    login = session.get(LoginSessionRow, token_hash(raw)) if raw else None
    user = session.get(UserRow, login.user_id) if login else None
    if not login or not user or not user.active or aware(login.expires_at) <= utcnow():
        raise HTTPException(401, "Entre na sua conta para continuar.")
    return login, user


def authenticate_request(request: Request):
    if request.url.path in ("/api/v1/health", "/api/v1/auth/login", "/api/v1/auth/session"):
        return
    if mode() == "local":
        if not request.client or request.client.host not in (
            "127.0.0.1",
            "::1",
            "localhost",
            "testclient",
        ):
            raise HTTPException(403, "Modo local permite somente acesso neste computador.")
        request.state.owner_id = None
        return
    require_https(request)
    with SessionLocal() as session:
        login, user = current_session(request, session)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin_check(request)
            if not hmac.compare_digest(request.headers.get("x-csrf-token", ""), login.csrf):
                raise HTTPException(403, "Proteção da sessão inválida. Entre novamente.")
        request.state.owner_id = user.id


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1, max_length=1024)


@router.get("/session", response_model=AccessSession)
def session_info(request: Request, session=Depends(auth_session)):
    access_mode = mode()
    if access_mode == "local":
        if not request.client or request.client.host not in (
            "127.0.0.1",
            "::1",
            "localhost",
            "testclient",
        ):
            raise HTTPException(403, "Acesso local apenas.")
        return {"mode": "local", "authenticated": True, "username": None, "csrf": None}
    require_https(request)
    try:
        login, user = current_session(request, session)
        return {
            "mode": "remote",
            "authenticated": True,
            "username": user.username,
            "csrf": login.csrf,
        }
    except HTTPException as error:
        if error.status_code != 401:
            raise
        return {"mode": "remote", "authenticated": False, "username": None, "csrf": None}


@router.post("/login", response_model=AccessSession)
def login(data: Credentials, request: Request, response: Response, session=Depends(auth_session)):
    if mode() != "remote":
        raise HTTPException(409, "Contas são usadas no modo remoto.")
    require_https(request)
    origin_check(request)
    username = data.username.strip().casefold()
    now = utcnow()
    # Persisted per-account throttle also applies to nonexistent accounts.
    key = token_hash(username)
    attempt = session.get(LoginAttemptRow, key)
    if (
        attempt
        and aware(attempt.window_start) + timedelta(minutes=15) > now
        and attempt.failures >= 5
    ):
        raise HTTPException(429, "Muitas tentativas. Aguarde 15 minutos.")
    user = session.scalar(select(UserRow).where(UserRow.username == username))
    valid = passwords.verify(data.password, user.password_hash if user else _dummy_hash)
    if not user or not user.active or not valid:
        if attempt is None:
            attempt = LoginAttemptRow(key=key, failures=0, window_start=now)
            session.add(attempt)
        if aware(attempt.window_start) + timedelta(minutes=15) <= now:
            attempt.window_start, attempt.failures = now, 0
        attempt.failures += 1
        session.commit()
        raise HTTPException(401, "Usuário ou senha inválidos.")
    if attempt:
        session.delete(attempt)
    previous = request.cookies.get(COOKIE)
    if previous:
        old = session.get(LoginSessionRow, token_hash(previous))
        if old:
            session.delete(old)
    raw, csrf = secrets.token_urlsafe(48), secrets.token_hex(32)
    session.add(
        LoginSessionRow(
            token_hash=token_hash(raw),
            user_id=user.id,
            csrf=csrf,
            expires_at=now + timedelta(hours=8),
        )
    )
    session.commit()
    response.set_cookie(
        COOKIE, raw, secure=True, httponly=True, samesite="strict", max_age=28800, path="/api/v1"
    )
    return {"mode": "remote", "authenticated": True, "username": user.username, "csrf": csrf}


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, session=Depends(auth_session)):
    raw = request.cookies.get(COOKIE)
    row = session.get(LoginSessionRow, token_hash(raw)) if raw else None
    if row:
        session.delete(row)
        session.commit()
    response.delete_cookie(COOKIE, path="/api/v1", secure=True, httponly=True, samesite="strict")
