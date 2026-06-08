import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_or_bot_secret, get_db, get_redis
from app.repositories.products import ProductsRepo
from app.schemas.product import ProductCreate, ProductImageOut, ProductOut, ProductPageOut, ProductUpdate
from app.services.products import ProductsService
from app.settings import settings

router = APIRouter(prefix="/products", tags=["products"])
logger = logging.getLogger(__name__)

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _image_url(rel_path: str) -> str:
    return f"{settings.MEDIA_URL_PREFIX.rstrip('/')}/{rel_path.replace(os.sep, '/').lstrip('/')}"


async def _store_product_image(product_id: int, file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(status_code=400, detail="NO_FILE")

    content_type = file.content_type or ""
    if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="BAD_CONTENT_TYPE")

    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="BAD_EXT")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="EMPTY_FILE")
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="IMAGE_TOO_LARGE")

    name = f"{uuid.uuid4().hex}.{ext}"
    rel_path = f"products/{product_id}/{name}"
    abs_path = Path(settings.MEDIA_DIR) / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_bytes(content)
    return rel_path


@router.get("/", response_model=ProductPageOut)
async def list_products(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None, min_length=1, max_length=100),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    in_stock: bool | None = Query(None),
):
    return await ProductsService(db).list_page(
        limit=limit,
        offset=offset,
        search=search,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        redis=redis,
        cache_ttl_seconds=settings.PRODUCTS_CACHE_TTL_SECONDS,
    )


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    return await ProductsService(db).get_out(product_id)


@router.post("/", response_model=ProductOut)
async def create_product(
    data: ProductCreate,
    _: object = Depends(admin_or_bot_secret),
    db: AsyncSession = Depends(get_db),
):
    product = await ProductsService(db).create(data.name, data.description, data.price, data.stock)
    return await ProductsService(db).get_out(product.id)


@router.patch("/{product_id}")
async def update_product(
    product_id: int,
    data: ProductUpdate,
    actor: object = Depends(admin_or_bot_secret),
    db: AsyncSession = Depends(get_db),
):
    payload = {key: value for key, value in data.model_dump().items() if value is not None}
    performed_by = getattr(actor, "id", None)
    await ProductsService(db).update(product_id, payload, performed_by=performed_by)
    return {"ok": True}


@router.get("/{product_id}/images", response_model=list[ProductImageOut])
async def list_images(product_id: int, db: AsyncSession = Depends(get_db)):
    return await ProductsService(db).list_images(product_id)


@router.post("/{product_id}/images", response_model=ProductImageOut)
async def upload_image(
    product_id: int,
    make_primary: bool = Query(False),
    _: object = Depends(admin_or_bot_secret),
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
):
    service = ProductsService(db)
    await service.get(product_id)
    rel_path = await _store_product_image(product_id, file)

    try:
        image = await service.add_image(product_id, rel_path, make_primary=make_primary)
    except IntegrityError:
        await db.rollback()
        Path(settings.MEDIA_DIR, rel_path).unlink(missing_ok=True)
        raise HTTPException(status_code=409, detail="IMAGE_CONFLICT")
    except Exception:
        await db.rollback()
        Path(settings.MEDIA_DIR, rel_path).unlink(missing_ok=True)
        logger.exception("Failed to save product image metadata")
        raise

    return {"id": image.id, "url": _image_url(rel_path), "is_primary": image.is_primary}


@router.patch("/{product_id}/images/{image_id}/primary")
async def set_primary_image(
    product_id: int,
    image_id: int,
    _: object = Depends(admin_or_bot_secret),
    db: AsyncSession = Depends(get_db),
):
    await ProductsService(db).set_primary(product_id, image_id)
    return {"ok": True}


@router.delete("/{product_id}/images/{image_id}")
async def delete_image(
    product_id: int,
    image_id: int,
    _: object = Depends(admin_or_bot_secret),
    db: AsyncSession = Depends(get_db),
):
    rel_path = await ProductsService(db).delete_image(product_id, image_id)
    Path(settings.MEDIA_DIR, rel_path).unlink(missing_ok=True)
    return {"ok": True}


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    _: object = Depends(admin_or_bot_secret),
    db: AsyncSession = Depends(get_db),
):
    ok = await ProductsRepo(db).delete(product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="PRODUCT_USED_IN_ORDERS")
    return {"ok": True}
