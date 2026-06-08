from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.product_image import ProductImage


class ProductImagesRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_product(self, product_id: int) -> list[ProductImage]:
        result = await self.db.execute(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.id)
        )
        return list(result.scalars().all())

    async def get(self, image_id: int) -> ProductImage | None:
        result = await self.db.execute(
            select(ProductImage).where(ProductImage.id == image_id)
        )
        return result.scalar_one_or_none()

    async def create(self, img: ProductImage) -> ProductImage:
        self.db.add(img)
        await self.db.flush()
        return img

    async def clear_primary(self, product_id: int) -> None:
        await self.db.execute(
            update(ProductImage)
            .where(ProductImage.product_id == product_id)
            .values(is_primary=False)
        )

    async def set_primary(self, product_id: int, image_id: int) -> bool:
        img = await self.get(image_id)
        if img is None or img.product_id != product_id:
            return False

        await self.clear_primary(product_id)
        img.is_primary = True
        await self.db.flush()
        return True

    async def delete(self, product_id: int, image_id: int) -> bool:
        result = await self.db.execute(
            delete(ProductImage).where(
                ProductImage.id == image_id,
                ProductImage.product_id == product_id,
            )
        )
        return bool(result.rowcount)
