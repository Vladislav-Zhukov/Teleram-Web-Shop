import logging
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_only, get_db
from app.services.products import ProductsService
from app.settings import settings

router = APIRouter(prefix="/admin/products", tags=["admin-products"])
logger = logging.getLogger(__name__)

ALLOWED_CT = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_BYTES = 5 * 1024 * 1024


@router.post("/{product_id}/images/upload")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    make_primary: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_only),
):
    if file.content_type not in ALLOWED_CT:
        raise HTTPException(status_code=400, detail="UNSUPPORTED_IMAGE_TYPE")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="EMPTY_FILE")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="IMAGE_TOO_LARGE")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="UNSUPPORTED_IMAGE_EXT")

    await ProductsService(db).get(product_id)

    name = f"{uuid.uuid4().hex}{ext}"
    rel_path = f"products/{product_id}/{name}"
    abs_path = Path(settings.MEDIA_DIR) / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_bytes(data)

    try:
        image = await ProductsService(db).add_image(product_id=product_id, rel_path=rel_path, make_primary=make_primary)
    except Exception:
        await db.rollback()
        abs_path.unlink(missing_ok=True)
        logger.exception("Failed to save product image metadata")
        raise

    return {
        "id": image.id,
        "url": f"{settings.MEDIA_URL_PREFIX.rstrip('/')}/{rel_path}",
        "is_primary": image.is_primary,
    }


@router.patch("/{product_id}/images/{image_id}/primary")
async def set_primary_product_image(
    product_id: int,
    image_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_only),
):
    await ProductsService(db).set_primary(product_id, image_id)
    return {"ok": True}


@router.post("/{product_id}/images/{image_id}/primary", include_in_schema=False)
async def set_primary_product_image_legacy(
    product_id: int,
    image_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_only),
):
    return await set_primary_product_image(product_id, image_id, db, admin)


@router.delete("/{product_id}/images/{image_id}")
async def delete_product_image(
    product_id: int,
    image_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(admin_only),
):
    rel_path = await ProductsService(db).delete_image(product_id, image_id)
    try:
        (Path(settings.MEDIA_DIR) / rel_path).unlink(missing_ok=True)
    except Exception:
        logger.exception("Failed to delete product image file")
    return {"ok": True}
