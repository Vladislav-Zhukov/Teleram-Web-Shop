from __future__ import annotations

import logging

import orjson
from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog
from app.db.models.product import Product
from app.db.models.product_image import ProductImage
from app.repositories.product_images import ProductImagesRepo
from app.repositories.products import ProductsRepo
from app.settings import settings

logger = logging.getLogger(__name__)


class ProductsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProductsRepo(db)
        self.images = ProductImagesRepo(db)

    def _img_url(self, path: str) -> str:
        prefix = settings.MEDIA_URL_PREFIX.rstrip("/")
        normalized_path = path.replace("\\", "/").lstrip("/")
        return f"{prefix}/{normalized_path}"

    async def _attach_images(self, product: Product) -> dict:
        images = await self.images.list_by_product(product.id)
        images_out = [
            {"id": img.id, "url": self._img_url(img.path), "is_primary": img.is_primary}
            for img in images
        ]
        primary = next((img["url"] for img in images_out if img["is_primary"]), None)
        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "stock": product.stock,
            "in_stock": product.in_stock,
            "primary_image_url": primary,
            "images": images_out,
        }

    async def list(self) -> list[dict]:
        items = await self.list_all()
        return [await self._attach_images(product) for product in items]

    async def list_page(
        self,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock: bool | None = None,
        redis: Redis | None = None,
        cache_ttl_seconds: int = 0,
    ) -> dict:
        cache_key: bytes | None = None
        if redis is not None and cache_ttl_seconds > 0:
            cache_key = (
                f"products:v2:limit={limit}:offset={offset}:search={search or ''}:"
                f"min={'' if min_price is None else min_price}:"
                f"max={'' if max_price is None else max_price}:"
                f"in_stock={'' if in_stock is None else int(in_stock)}"
            ).encode("utf-8")
            cached = await redis.get(cache_key)
            if cached:
                try:
                    return orjson.loads(cached)
                except Exception:
                    logger.exception("Failed to decode products cache")

        items, total = await self.repo.list_page(
            limit=limit,
            offset=offset,
            search=search,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
        )
        out = {
            "items": [await self._attach_images(product) for product in items],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

        if cache_key is not None and redis is not None and cache_ttl_seconds > 0:
            try:
                await redis.setex(cache_key, cache_ttl_seconds, orjson.dumps(out))
            except Exception:
                logger.exception("Failed to write products cache")

        return out

    async def list_all(self) -> list[Product]:
        return await self.repo.list_all()

    async def get(self, product_id: int) -> Product:
        product = await self.repo.get(product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return product

    async def get_out(self, product_id: int) -> dict:
        product = await self.get(product_id)
        return await self._attach_images(product)

    async def create(self, name: str, description: str, price: float, stock: int) -> Product:
        if price < 0:
            raise HTTPException(status_code=400, detail="BAD_PRICE")
        if stock < 0:
            raise HTTPException(status_code=400, detail="BAD_STOCK")

        product = Product(name=name, description=description, price=price, stock=stock)
        product.sync_flags()
        await self.repo.create(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update(self, product_id: int, data: dict, *, performed_by: int | None = None) -> None:
        if not data:
            raise HTTPException(status_code=422, detail="NO_FIELDS_TO_UPDATE")

        product = await self.get(product_id)
        old_price = float(product.price)
        old_stock = int(product.stock)

        if "price" in data and data["price"] is not None and float(data["price"]) < 0:
            raise HTTPException(status_code=400, detail="BAD_PRICE")

        if "stock" in data and data["stock"] is not None:
            stock = int(data["stock"])
            if stock < 0:
                raise HTTPException(status_code=400, detail="BAD_STOCK")
            data["stock"] = stock
            data["in_stock"] = stock > 0

        updated = await self.repo.update_fields(product_id, data)
        if not updated:
            raise HTTPException(status_code=404, detail="NOT_FOUND")

        await self.db.refresh(product)

        new_price = float(product.price)
        new_stock = int(product.stock)
        if old_price != new_price or old_stock != new_stock:
            self.db.add(
                AuditLog(
                    entity_type="product",
                    entity_id=product.id,
                    action="update_product",
                    performed_by=performed_by,
                    payload={
                        "old_price": old_price,
                        "new_price": new_price,
                        "old_stock": old_stock,
                        "new_stock": new_stock,
                    },
                )
            )

        await self.db.commit()

    async def add_image(self, product_id: int, rel_path: str, make_primary: bool = False) -> ProductImage:
        await self.get(product_id)
        existing_images = await self.images.list_by_product(product_id)
        should_make_primary = make_primary or not any(img.is_primary for img in existing_images)

        image = ProductImage(product_id=product_id, path=rel_path, is_primary=False)
        await self.images.create(image)

        if should_make_primary:
            await self.images.set_primary(product_id, image.id)

        await self.db.commit()
        await self.db.refresh(image)
        return image

    async def list_images(self, product_id: int) -> list[dict]:
        await self.get(product_id)
        images = await self.images.list_by_product(product_id)
        return [
            {"id": img.id, "url": self._img_url(img.path), "is_primary": img.is_primary}
            for img in images
        ]

    async def set_primary(self, product_id: int, image_id: int) -> None:
        await self.get(product_id)
        ok = await self.images.set_primary(product_id, image_id)
        if not ok:
            raise HTTPException(status_code=404, detail="IMAGE_NOT_FOUND")
        await self.db.commit()

    async def delete_image(self, product_id: int, image_id: int) -> str:
        await self.get(product_id)
        image = await self.images.get(image_id)
        if image is None or image.product_id != product_id:
            raise HTTPException(status_code=404, detail="IMAGE_NOT_FOUND")

        rel_path = image.path
        was_primary = bool(image.is_primary)
        ok = await self.images.delete(product_id, image_id)
        if not ok:
            raise HTTPException(status_code=404, detail="IMAGE_NOT_FOUND")

        if was_primary:
            remaining = await self.images.list_by_product(product_id)
            if remaining:
                await self.images.set_primary(product_id, remaining[0].id)

        await self.db.commit()
        return rel_path
