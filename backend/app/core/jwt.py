from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.settings import settings

def _now() -> datetime:
    return datetime.now(timezone.utc)

def create_access_token(user_id: int) -> str:
    exp = _now() + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    payload = {"sub": str(user_id), "type": "access", "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def create_refresh_token(user_id: int, jti: str) -> str:
    exp = _now() + timedelta(days=settings.REFRESH_TOKEN_DAYS)
    payload = {"sub": str(user_id), "type": "refresh", "jti": jti, "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError:
        raise ValueError("INVALID_TOKEN")
    if payload.get("type") != "access":
        raise ValueError("INVALID_TOKEN_TYPE")
    return payload

def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError:
        raise ValueError("INVALID_REFRESH")
    if payload.get("type") != "refresh":
        raise ValueError("INVALID_TOKEN_TYPE")
    return payload

def refresh_expires_at() -> datetime:
    return _now() + timedelta(days=settings.REFRESH_TOKEN_DAYS)
