from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.product import Product

class StockService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add(self, product_id: int, delta: int) -> Product:
        if delta == 0:
            raise HTTPException(status_code=400, detail="DELTA_ZERO")

        res = await self.db.execute(
            select(Product).where(Product.id == product_id).with_for_update()
        )
        p = res.scalar_one_or_none()
        if not p:
            raise HTTPException(status_code=404, detail="PRODUCT_NOT_FOUND")

        new_stock = p.stock + delta
        if new_stock < 0:
            raise HTTPException(status_code=409, detail="OUT_OF_STOCK")

        p.stock = new_stock
        p.sync_flags()
        await self.db.commit()
        await self.db.refresh(p)
        return p
