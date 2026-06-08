from typing import AsyncGenerator
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.core.jwt import decode_access_token
from app.repositories.users import UsersRepo
from app.core.permissions import require_admin
from app.settings import settings

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="AUTH_REQUIRED")
    token = authorization.split(" ", 1)[1]

    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="INVALID_TOKEN")

    user = await UsersRepo(db).get_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="USER_NOT_FOUND")
    return user

async def admin_only(user=Depends(get_current_user)):
    require_admin(user)
    return user


async def admin_or_bot_secret(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_bot_admin_secret: str | None = Header(default=None),
):
    """Admin access for web (JWT) OR for bot (shared secret).

    If BOT_ADMIN_SECRET is configured and request includes matching X-Bot-Admin-Secret header,
    we allow the action even without admin JWT user.
    """
    if settings.BOT_ADMIN_SECRET and x_bot_admin_secret == settings.BOT_ADMIN_SECRET:
        return {"bot": True}

    # fallback to normal admin JWT
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="AUTH_REQUIRED")
    token = authorization.split(" ", 1)[1]

    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="INVALID_TOKEN")

    user = await UsersRepo(db).get_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="USER_NOT_FOUND")

    require_admin(user)
    return user


def get_redis(request: Request):
    return getattr(request.app.state, "redis", None)


async def require_bot_user_secret(x_bot_user_secret: str | None = Header(default=None)):
    """Allow access only for our bot (guest checkout, telegram link confirm)."""
    if not settings.BOT_USER_SECRET or x_bot_user_secret != settings.BOT_USER_SECRET:
        raise HTTPException(status_code=401, detail="BOT_SECRET_REQUIRED")
    return True
