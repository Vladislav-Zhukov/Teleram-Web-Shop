from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import admin_or_bot_secret, get_current_user, get_db, get_redis, require_bot_user_secret
from app.repositories.orders import OrdersRepo
from app.repositories.users import UsersRepo
from app.schemas.order import (
    OrderAdminOut,
    OrderAdminPageOut,
    OrderCreate,
    OrderItemAdminOut,
    OrderOut,
    OrderStatusUpdateIn,
    TelegramOrderCreate,
)
from app.services.orders import OrdersService

router = APIRouter(prefix="/orders", tags=["orders"])


def _media_url(path: str | None) -> str | None:
    if not path:
        return None
    normalized_path = str(path).replace("\\", "/").lstrip("/")
    return f"/media/{normalized_path}"


def _order_to_admin_out(order) -> OrderAdminOut:
    total = 0.0
    items: list[OrderItemAdminOut] = []

    for item in order.items:
        unit_price = float(item.unit_price)
        line_total = unit_price * int(item.quantity)
        total += line_total
        product = item.product
        image_url = None
        if product is not None and hasattr(product, "primary_image_path"):
            image_url = _media_url(product.primary_image_path())

        items.append(
            OrderItemAdminOut(
                product_id=item.product_id,
                product_name=(product.name if product is not None else f"#{item.product_id}"),
                unit_price=unit_price,
                quantity=int(item.quantity),
                line_total=line_total,
                image_url=image_url,
            )
        )

    return OrderAdminOut(
        id=order.id,
        user_id=order.user_id,
        user_email=(order.user.email if order.user is not None else ""),
        status=order.status,
        created_at=order.created_at,
        total=total,
        items=items,
    )


def _order_to_user_out(order) -> dict:
    return {
        "id": order.id,
        "user_id": order.user_id,
        "status": order.status,
        "items": [
            {"product_id": item.product_id, "quantity": item.quantity}
            for item in order.items
        ],
    }


@router.post("/")
async def create_order(
    data: OrderCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    redis_key = None
    if idempotency_key and redis is not None:
        redis_key = f"idem:order:{user.id}:{idempotency_key}".encode("utf-8")
        existing = await redis.get(redis_key)
        if existing:
            order_id = int(existing.decode("utf-8") if isinstance(existing, bytes) else existing)
            return {"id": order_id, "idempotent": True}

    order = await OrdersService(db).create_order(user.id, [item.model_dump() for item in data.items])

    if redis_key is not None and redis is not None:
        await redis.setex(redis_key, 600, str(order.id).encode("utf-8"))

    return {"id": order.id, "status": order.status}


@router.get("/my", response_model=list[OrderOut])
async def my_orders(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    orders = await OrdersRepo(db).list_by_user(user.id)
    return [_order_to_user_out(order) for order in orders]


@router.get("/", response_model=OrderAdminPageOut)
async def list_orders(
    _: object = Depends(admin_or_bot_secret),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None, min_length=1, max_length=30),
    user_id: int | None = Query(None, ge=1),
):
    orders, total = await OrdersRepo(db).list_page(limit=limit, offset=offset, status=status, user_id=user_id)
    return {
        "items": [_order_to_admin_out(order) for order in orders],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.patch("/{order_id}/status", response_model=OrderAdminOut)
async def update_order_status(
    order_id: int,
    data: OrderStatusUpdateIn,
    actor: object = Depends(admin_or_bot_secret),
    db: AsyncSession = Depends(get_db),
):
    performed_by = getattr(actor, "id", None)
    await OrdersService(db).set_status(order_id, data.status, performed_by=performed_by)

    order = await OrdersRepo(db).get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="ORDER_NOT_FOUND")
    return _order_to_admin_out(order)


@router.post("/telegram")
async def create_order_telegram(
    data: TelegramOrderCreate,
    _: object = Depends(require_bot_user_secret),
    db: AsyncSession = Depends(get_db),
):
    users = UsersRepo(db)
    user = await users.get_by_telegram_id(data.telegram_id)
    if user is None:
        user = await users.create_telegram_guest(data.telegram_id)

    order = await OrdersService(db).create_order(user.id, [item.model_dump() for item in data.items])
    return {"id": order.id, "status": order.status}


@router.get("/telegram/my", response_model=list[OrderOut])
async def my_orders_telegram(
    telegram_id: int = Query(..., ge=1),
    _: object = Depends(require_bot_user_secret),
    db: AsyncSession = Depends(get_db),
):
    user = await UsersRepo(db).get_by_telegram_id(int(telegram_id))
    if user is None:
        return []
    orders = await OrdersRepo(db).list_by_user(user.id)
    return [_order_to_user_out(order) for order in orders]
