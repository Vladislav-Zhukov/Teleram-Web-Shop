from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.db.models.product import Product


class OrdersRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, order_id: int) -> Order | None:
        res = await self.db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.user),
                selectinload(Order.items).selectinload(OrderItem.product).selectinload(Product.images),
            )
        )
        return res.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[Order]:
        res = await self.db.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
            )
            .order_by(Order.id.desc())
        )
        # user endpoint doesn't need images/user; keep lighter
        return list(res.scalars().all())

    async def create(self, o: Order) -> Order:
        self.db.add(o)
        await self.db.flush()
        return o

    async def list_page(
        self,
        *,
        limit: int,
        offset: int,
        status: str | None = None,
        user_id: int | None = None,
    ) -> tuple[list[Order], int]:
        q = select(Order).options(
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product).selectinload(Product.images),
        )
        if status:
            q = q.where(Order.status == status)
        if user_id is not None:
            q = q.where(Order.user_id == user_id)

        count_q = select(func.count()).select_from(q.subquery())
        total_res = await self.db.execute(count_q)
        total = int(total_res.scalar_one())

        q = q.order_by(Order.id.desc()).limit(limit).offset(offset)
        res = await self.db.execute(q)
        return list(res.scalars().all()), total
