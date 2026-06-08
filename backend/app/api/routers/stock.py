from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_only, get_db
from app.schemas.stock import StockChangeIn
from app.services.stock import StockService

router = APIRouter(prefix="/stock", tags=["stock"])


@router.post("/change")
async def change_stock(data: StockChangeIn, _: object = Depends(admin_only), db: AsyncSession = Depends(get_db)):
    product = await StockService(db).add(data.product_id, data.delta)
    return {"id": product.id, "stock": product.stock, "in_stock": product.in_stock}
