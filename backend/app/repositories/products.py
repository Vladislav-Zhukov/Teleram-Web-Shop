from sqlalchemy import delete as sa_delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.product import Product


class ProductsRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[Product]:
        result = await self.db.execute(select(Product).order_by(Product.id.desc()))
        return list(result.scalars().all())

    async def list_page(
        self,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock: bool | None = None,
    ) -> tuple[list[Product], int]:
        query = select(Product)

        if search:
            query = query.where(Product.name.ilike(f"%{search.strip()}%"))

        if min_price is not None:
            query = query.where(Product.price >= min_price)

        if max_price is not None:
            query = query.where(Product.price <= max_price)

        if in_stock is True:
            query = query.where(Product.in_stock.is_(True), Product.stock > 0)
        elif in_stock is False:
            query = query.where((Product.in_stock.is_(False)) | (Product.stock <= 0))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = int(total_result.scalar_one())

        result = await self.db.execute(
            query.order_by(Product.id.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def get(self, product_id: int) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def create(self, product: Product) -> Product:
        self.db.add(product)
        await self.db.flush()
        return product

    async def delete(self, product_id: int) -> bool:
        result = await self.db.execute(
            sa_delete(Product).where(Product.id == product_id)
        )
        return bool(result.rowcount)

    async def update_fields(self, product_id: int, data: dict) -> bool:
        if not data:
            return False

        result = await self.db.execute(
            update(Product).where(Product.id == product_id).values(**data)
        )
        return bool(result.rowcount)
