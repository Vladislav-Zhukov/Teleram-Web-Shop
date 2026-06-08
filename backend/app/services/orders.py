from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.order import Order
from app.db.models.order_item import OrderItem
from app.db.models.product import Product
from app.db.models.order_status_history import OrderStatusHistory
from app.db.models.audit_log import AuditLog
from app.domain.enums import OrderStatus
from app.api.errors import api_error

class OrdersService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(self, user_id: int, items: list[dict]) -> Order:
        if not items:
            raise HTTPException(status_code=400, detail="EMPTY_ORDER")

        # Lock all products involved in the order in a single query.
        product_ids = [i["product_id"] for i in items]
        res = await self.db.execute(
            select(Product).where(Product.id.in_(product_ids)).with_for_update()
        )
        products = {p.id: p for p in res.scalars().all()}
        if len(products) != len(set(product_ids)):
            raise HTTPException(status_code=404, detail="PRODUCT_NOT_FOUND")

        # Validate and decrement stock while holding row locks.
        for it in items:
            qty = int(it["quantity"])
            if qty <= 0:
                raise HTTPException(status_code=400, detail="BAD_QTY")
            p = products[it["product_id"]]
            if p.stock < qty:
                raise HTTPException(status_code=409, detail="OUT_OF_STOCK")
            p.stock -= qty
            p.sync_flags()

        order = Order(user_id=user_id, status=OrderStatus.NEW)
        self.db.add(order)
        await self.db.flush()

        for it in items:
            p = products[it["product_id"]]
            self.db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=it["product_id"],
                    quantity=it["quantity"],
                    unit_price=p.price,  # snapshot unit price at purchase time
                )
            )

        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def set_status(self, order_id: int, new_status: str, *, performed_by: int | None = None) -> Order:
        if new_status not in OrderStatus.ALL:
            raise api_error(400, "BAD_STATUS", "Неизвестный статус заказа", details={"status": new_status})

        order = await self.db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="ORDER_NOT_FOUND")

        # Basic lifecycle rules (can be extended later)
        allowed: dict[str, set[str]] = {
            OrderStatus.NEW: {OrderStatus.PAID, OrderStatus.CANCELED},
            OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELED},
            OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
            OrderStatus.DELIVERED: set(),
            OrderStatus.CANCELED: set(),
        }

        if new_status == order.status:
            return order

        if new_status not in allowed.get(order.status, set()):
            raise api_error(
                409,
                "BAD_STATUS_TRANSITION",
                "Переход запрещён правилами жизненного цикла заказа",
                details={"from": order.status, "to": new_status},
            )

        old_status = order.status
        order.status = new_status

        # Status history
        self.db.add(
            OrderStatusHistory(
                order_id=order.id,
                old_status=old_status,
                new_status=new_status,
                changed_by=performed_by,
            )
        )

        # Audit log
        self.db.add(
            AuditLog(
                entity_type="order",
                entity_id=order.id,
                action="status_change",
                performed_by=performed_by,
                payload={"old_status": old_status, "new_status": new_status},
            )
        )

        await self.db.commit()
        await self.db.refresh(order)
        return order