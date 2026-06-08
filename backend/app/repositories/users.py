from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.db.models.user import User

class UsersRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        res = await self.db.execute(select(User).where(User.id == user_id))
        return res.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        res = await self.db.execute(select(User).where(User.email == email))
        return res.scalar_one_or_none()

    async def get_by_telegram_id(self, tg_id: int) -> User | None:
        res = await self.db.execute(select(User).where(User.telegram_id == tg_id))
        return res.scalar_one_or_none()

    async def create(self, email: str, password_hash: str, is_admin: bool = False) -> User:
        user = User(email=email, password_hash=password_hash, is_admin=is_admin)
        self.db.add(user)
        await self.db.flush()
        return user

    async def bind_telegram(self, user_id: int, tg_id: int) -> None:
        await self.db.execute(update(User).where(User.id == user_id).values(telegram_id=tg_id))

    async def create_telegram_guest(self, tg_id: int) -> User:
        email = f"tg_{tg_id}@telegram.local"
        user = User(email=email, password_hash="!", is_admin=False, telegram_id=tg_id)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete_by_id(self, user_id: int) -> None:
        await self.db.execute(delete(User).where(User.id == user_id))
