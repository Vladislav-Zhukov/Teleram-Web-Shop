from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models.refresh_token import RefreshToken

class TokensRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, token: RefreshToken) -> None:
        self.db.add(token)
        await self.db.flush()

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        res = await self.db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
        return res.scalar_one_or_none()

    async def revoke(self, jti: str) -> None:
        await self.db.execute(update(RefreshToken).where(RefreshToken.jti == jti).values(revoked=True))
