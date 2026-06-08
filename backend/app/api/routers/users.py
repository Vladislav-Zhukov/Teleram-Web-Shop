import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_redis, require_bot_user_secret
from app.db.models.order import Order
from app.db.models.user import User
from app.repositories.users import UsersRepo
from app.schemas.user import TelegramBindByCodeIn, TelegramIdIn, UserOut
from app.settings import settings

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return user


@router.post("/bind-telegram")
async def bind_telegram(data: TelegramIdIn, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await UsersRepo(db).bind_telegram(user.id, data.telegram_id)
    await db.commit()
    return {"ok": True}


@router.post("/telegram/link")
async def create_telegram_link(user=Depends(get_current_user), redis=Depends(get_redis)):
    if redis is None:
        raise HTTPException(status_code=500, detail="REDIS_REQUIRED")

    code = secrets.token_urlsafe(16)
    key = f"tg:link:{code}".encode("utf-8")

    ttl = int(getattr(settings, "TELEGRAM_LINK_TTL_SECONDS", 600))
    await redis.setex(key, ttl, str(user.id).encode("utf-8"))
    return {"code": code, "expires_in": ttl}


@router.post("/telegram/bind-by-code")
async def bind_telegram_by_code(
    data: TelegramBindByCodeIn,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    _: object = Depends(require_bot_user_secret),
):
    if redis is None:
        raise HTTPException(status_code=500, detail="REDIS_REQUIRED")

    key = f"tg:link:{data.code}".encode("utf-8")
    user_id_bytes = await redis.get(key)
    if not user_id_bytes:
        raise HTTPException(status_code=400, detail="INVALID_OR_EXPIRED_CODE")

    website_user_id = int(user_id_bytes.decode("utf-8"))
    await redis.delete(key)

    repo = UsersRepo(db)
    existing = await repo.get_by_telegram_id(data.telegram_id)
    if existing and existing.id != website_user_id:
        await db.execute(update(Order).where(Order.user_id == existing.id).values(user_id=website_user_id))
        await repo.delete_by_id(existing.id)

    await repo.bind_telegram(website_user_id, data.telegram_id)
    await db.commit()
    return {"ok": True}


@router.post("/telegram/unlink")
async def unlink_telegram(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not getattr(user, "telegram_id", None):
        raise HTTPException(status_code=400, detail="TELEGRAM_NOT_LINKED")

    await db.execute(update(User).where(User.id == user.id).values(telegram_id=None))
    await db.commit()
    return {"ok": True}


@router.get("/telegram/status-by-telegram-id")
async def telegram_status_by_telegram_id(
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_bot_user_secret),
):
    user = await UsersRepo(db).get_by_telegram_id(int(telegram_id))
    return {
        "linked": bool(user),
        "user_id": user.id if user else None,
        "email": user.email if user else None,
    }


@router.post("/telegram/unlink-by-telegram-id")
async def unlink_by_telegram_id(
    data: TelegramIdIn,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_bot_user_secret),
):
    user = await UsersRepo(db).get_by_telegram_id(data.telegram_id)
    if user is None:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")

    await db.execute(update(User).where(User.id == user.id).values(telegram_id=None))
    await db.commit()
    return {"ok": True}
