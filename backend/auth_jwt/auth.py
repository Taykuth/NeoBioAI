"""
Neo-Dock — backend/auth_jwt/auth.py
=====================================
JWT tabanlı tam kimlik doğrulama sistemi.

Akış:
  POST /auth/register → kullanıcı kaydı → {user_id, email}
  POST /auth/login    → {email, password} → {access_token, refresh_token}
  GET  /auth/me       → token → kullanıcı bilgisi
  POST /auth/refresh  → refresh_token → yeni access_token
"""

import os
import time
import uuid
import hashlib
import hmac
import json
import base64
from typing import Optional
from dataclasses import dataclass, field
from fastapi import HTTPException, Header, status, Depends, APIRouter
from pydantic import BaseModel

# ─── Yapılandırma ─────────────────────────────────────────
SECRET_KEY  = os.environ.get("JWT_SECRET", "neodock-dev-secret-change-in-prod")
ACCESS_EXP  = 15 * 60          # 15 dakika (saniye)
REFRESH_EXP = 7 * 24 * 3600   # 7 gün


# ─── In-memory kullanıcı deposu ───────────────────────────
@dataclass
class User:
    user_id:       str
    email:         str
    password_hash: str
    tier:          str   = "free"      # free | pro
    created_at:    float = field(default_factory=time.time)
    request_count: int   = 0


_users:          dict[str, User] = {}
_refresh_tokens: dict[str, str]  = {}   # jti → user_id

# Demo kullanıcı
_demo = User(
    user_id="demo-001",
    email="demo@neodock.dev",
    password_hash=hashlib.sha256(b"demo1234").hexdigest(),
    tier="pro",
)
_users["demo@neodock.dev"] = _demo


# ─── JWT (saf Python — bağımlılıksız) ─────────────────────

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * pad)


def _sign(payload: dict, expiry: int) -> str:
    header  = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = {**payload, "exp": int(time.time()) + expiry, "iat": int(time.time())}
    body    = _b64url(json.dumps(payload).encode())
    msg     = f"{header}.{body}".encode()
    sig     = _b64url(hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"


def _verify(token: str) -> Optional[dict]:
    try:
        header, body, sig = token.split(".")
        msg      = f"{header}.{body}".encode()
        expected = _b64url(hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64url_decode(body))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# ─── Pydantic modeller ────────────────────────────────────

class RegisterRequest(BaseModel):
    email:    str
    password: str


class LoginRequest(BaseModel):
    email:    str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "Bearer"
    expires_in:    int = ACCESS_EXP


# ─── Yardımcılar ──────────────────────────────────────────

def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _make_tokens(user: User) -> dict:
    access     = _sign({"sub": user.user_id, "email": user.email,
                         "tier": user.tier, "type": "access"}, ACCESS_EXP)
    refresh_id = str(uuid.uuid4())
    refresh    = _sign({"sub": user.user_id, "jti": refresh_id,
                         "type": "refresh"}, REFRESH_EXP)
    _refresh_tokens[refresh_id] = user.user_id
    return {"access_token": access, "refresh_token": refresh,
            "token_type": "Bearer", "expires_in": ACCESS_EXP}


# ─── FastAPI Dependency ───────────────────────────────────

def get_current_user(authorization: Optional[str] = Header(default=None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization: Bearer <token> gerekli",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token   = authorization[7:]
    payload = _verify(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Geçersiz veya süresi dolmuş token")
    user = next((u for u in _users.values() if u.user_id == payload["sub"]), None)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Kullanıcı bulunamadı")
    user.request_count += 1
    return user


def optional_user(authorization: Optional[str] = Header(default=None)) -> Optional[User]:
    try:
        return get_current_user(authorization)
    except HTTPException:
        return None


# ─── Router ───────────────────────────────────────────────

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", summary="Yeni kullanıcı kaydı")
def register(req: RegisterRequest):
    if req.email in _users:
        raise HTTPException(status_code=409, detail="Bu e-posta zaten kayıtlı")
    if len(req.password) < 8:
        raise HTTPException(status_code=422, detail="Şifre en az 8 karakter olmalı")
    user = User(
        user_id=str(uuid.uuid4())[:8],
        email=req.email,
        password_hash=_hash_pw(req.password),
    )
    _users[req.email] = user
    return {"user_id": user.user_id, "email": user.email, "tier": user.tier}


@router.post("/login", response_model=TokenResponse, summary="Giriş yap, JWT al")
def login(req: LoginRequest):
    user = _users.get(req.email)
    if not user or user.password_hash != _hash_pw(req.password):
        raise HTTPException(status_code=401, detail="E-posta veya şifre hatalı")
    return _make_tokens(user)


@router.post("/refresh", summary="Access token yenile")
def refresh_token(body: RefreshRequest):
    payload = _verify(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Geçersiz refresh token")
    jti = payload.get("jti", "")
    uid = _refresh_tokens.get(jti)
    if not uid:
        raise HTTPException(status_code=401, detail="Token iptal edilmiş")
    user = next((u for u in _users.values() if u.user_id == uid), None)
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    del _refresh_tokens[jti]
    return _make_tokens(user)


@router.get("/me", summary="Mevcut kullanıcı bilgisi")
def me(user: User = Depends(get_current_user)):
    return {
        "user_id":       user.user_id,
        "email":         user.email,
        "tier":          user.tier,
        "request_count": user.request_count,
        "created_at":    user.created_at,
    }
