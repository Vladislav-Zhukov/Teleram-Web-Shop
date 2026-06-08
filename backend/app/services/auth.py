import secrets
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from datetime import datetime, timezone

from app.core.security import hash_password, verify_password
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    refresh_expires_at,
)
from app.db.models.refresh_token import RefreshToken
from app.repositories.users import UsersRepo
from app.repositories.tokens import TokensRepo
from app.settings import settings

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UsersRepo(db)
        self.tokens = TokensRepo(db)

    async def register(self, email: str, password: str):
        if await self.users.get_by_email(email):
            raise HTTPException(status_code=409, detail="EMAIL_EXISTS")
        user = await self.users.create(email=email, password_hash=hash_password(password))
        await self.db.commit()
        return user

    async def login(self, email: str, password: str):
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")

        jti = secrets.token_hex(16)
        rt = RefreshToken(user_id=user.id, jti=jti, expires_at=refresh_expires_at())
        await self.tokens.create(rt)

        access = create_access_token(user.id)
        refresh = create_refresh_token(user.id, jti)

        await self.db.commit()
        return access, refresh

    async def refresh(self, refresh_token: str, redis: Redis | None = None):
        try:
            payload = decode_refresh_token(refresh_token)
        except Exception:
            raise HTTPException(status_code=401, detail="INVALID_REFRESH")

        jti = payload.get("jti")
        user_id = int(payload.get("sub", "0"))

        # Redis fast-path revocation check
        if redis is not None and jti:
            try:
                if await redis.get(f"revoked:{jti}".encode("utf-8")):
                    raise HTTPException(status_code=401, detail="REFRESH_REVOKED")
            except HTTPException:
                raise
            except Exception:
                pass

        db_token = await self.tokens.get_by_jti(jti)
        if not db_token or db_token.revoked:
            raise HTTPException(status_code=401, detail="REFRESH_REVOKED")

        # rotate refresh token
        await self.tokens.revoke(jti)

        # Put revoked jti to Redis until token exp
        if redis is not None and jti:
            try:
                exp = payload.get("exp")
                ttl = 60 * 60 * 24 * settings.REFRESH_TOKEN_DAYS
                if isinstance(exp, (int, float)):
                    now = datetime.now(timezone.utc).timestamp()
                    ttl = max(1, int(exp - now))
                await redis.setex(f"revoked:{jti}".encode("utf-8"), ttl, b"1")
            except Exception:
                pass

        new_jti = secrets.token_hex(16)
        rt = RefreshToken(user_id=user_id, jti=new_jti, expires_at=refresh_expires_at())
        await self.tokens.create(rt)

        access = create_access_token(user_id)
        refresh = create_refresh_token(user_id, new_jti)

        await self.db.commit()
        return access, refresh

    async def logout(self, refresh_token: str, redis: Redis | None = None):
        try:
            payload = decode_refresh_token(refresh_token)
        except Exception:
            return
        jti = payload.get("jti")
        if jti:
            await self.tokens.revoke(jti)
            if redis is not None:
                try:
                    exp = payload.get("exp")
                    ttl = 60 * 60 * 24 * settings.REFRESH_TOKEN_DAYS
                    if isinstance(exp, (int, float)):
                        now = datetime.now(timezone.utc).timestamp()
                        ttl = max(1, int(exp - now))
                    await redis.setex(f"revoked:{jti}".encode("utf-8"), ttl, b"1")
                except Exception:
                    pass
            await self.db.commit()
