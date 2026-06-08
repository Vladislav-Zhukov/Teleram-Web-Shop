from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from app.filters.is_admin import IsAdmin
from app.api_client.base import ApiClient, ApiError
from app.api_client.orders import OrdersAPI
from app.callbacks.orders import AdminOrdersCb
from app.keyboards.admin import admin_orders_list_kb, admin_order_open_kb

router = Router()
PAGE_SIZE = 10


def _fmt_order(o: dict) -> str:
    oid = o.get("id")
    status = o.get("status")
    user_email = o.get("user_email", "")
    created_at = o.get("created_at", "")
    total = o.get("total", 0)

    lines = [
        f"🧾 Заказ #{oid}",
        f"Статус: {status}",
        f"Покупатель: {user_email}",
        f"Создан: {created_at}",
        f"Итого: {float(total):.2f}",
        "",
        "Товары:",
    ]

    for it in o.get("items", []):
        pname = it.get("product_name") or f"#{it.get('product_id')}"
        qty = it.get("quantity")
        unit = it.get("unit_price")
        line_total = it.get("line_total")
        lines.append(f"• {pname} - x{qty} • {float(unit):.2f} = {float(line_total):.2f}")

    return "\n".join(lines)


async def _load_orders_page(page: int, status: str):
    c = ApiClient()
    try:
        data = await OrdersAPI(c).admin_page(
            limit=PAGE_SIZE,
            offset=page * PAGE_SIZE,
            status=(status or None),
        )
    finally:
        await c.close()

    items = data["items"]
    total = int(data["total"])

    has_prev = page > 0
    has_next = page * PAGE_SIZE + PAGE_SIZE < total
    return items, has_prev, has_next, total

@router.message(IsAdmin(), F.text =="🧾 Заказы")
async def admin_orders_menu(m: Message):
    page = 0
    status = ""
    items, has_prev, has_next, total = await _load_orders_page(page, status)

    text = f"🧾 Заказы (всего: {total})"
    await m.answer(
        text,
        reply_markup=admin_orders_list_kb(
            items=items,
            page=page,
            has_prev=has_prev,
            has_next=has_next,
            status=status,
        ),
    )


@router.callback_query(IsAdmin(), AdminOrdersCb.filter(F.a.in_({"list", "filter"})))
async def admin_orders_list(cb: CallbackQuery, callback_data: AdminOrdersCb):
    await cb.answer()

    status = callback_data.status or ""
    page = int(callback_data.page)

    items, has_prev, has_next, total = await _load_orders_page(page, status)
    text = f"🧾 Заказы (всего: {total})" + (f" • фильтр: {status}" if status else "")

    try:
        await cb.message.edit_text(
            text,
            reply_markup=admin_orders_list_kb(
                items=items,
                page=page,
                has_prev=has_prev,
                has_next=has_next,
                status=status,
            ),
        )
    except TelegramBadRequest:
        await cb.message.answer(
            text,
            reply_markup=admin_orders_list_kb(
                items=items,
                page=page,
                has_prev=has_prev,
                has_next=has_next,
                status=status,
            ),
        )


@router.callback_query(IsAdmin(), AdminOrdersCb.filter(F.a.in_({"prev", "next"})))
async def admin_orders_prev_next(cb: CallbackQuery, callback_data: AdminOrdersCb):
    await cb.answer()
    status = callback_data.status or ""
    page = int(callback_data.page)
    page = page - 1 if callback_data.a == "prev" else page + 1
    if page < 0:
        page = 0

    items, has_prev, has_next, total = await _load_orders_page(page, status)
    text = f"🧾 Заказы (всего: {total})" + (f" • фильтр: {status}" if status else "")

    await cb.message.edit_text(
        text,
        reply_markup=admin_orders_list_kb(
            items=items,
            page=page,
            has_prev=has_prev,
            has_next=has_next,
            status=status,
        ),
    )


@router.callback_query(IsAdmin(), AdminOrdersCb.filter(F.a == "open"))
async def admin_orders_open(cb: CallbackQuery, callback_data: AdminOrdersCb):
    await cb.answer()
    oid = int(callback_data.oid)
    page = int(callback_data.page)
    status = callback_data.status or ""

    c = ApiClient()
    try:
        # грузим первую сотню с фильтром
        data = await OrdersAPI(c).admin_page(limit=100, offset=0, status=(status or None))
    finally:
        await c.close()

    order = next((o for o in data["items"] if int(o.get("id")) == oid), None)
    if not order:
        await cb.message.answer("Заказ не найден.")
        return

    await cb.message.edit_text(
        _fmt_order(order),
        reply_markup=admin_order_open_kb(oid=oid, page=page, status=status),
    )


@router.callback_query(IsAdmin(), AdminOrdersCb.filter(F.a == "set"))
async def admin_orders_set_status(cb: CallbackQuery, callback_data: AdminOrdersCb):
    await cb.answer("Меняю статус…")

    oid = int(callback_data.oid)
    new_status = callback_data.new_status
    page = int(callback_data.page)
    status = callback_data.status or ""

    if not new_status:
        await cb.message.answer("Не передан новый статус.")
        return

    c = ApiClient()
    try:
        await OrdersAPI(c).admin_set_status(oid, new_status)
    except ApiError as e:
        await cb.message.answer(f"🚫 {e.message}")
        return
    finally:
        await c.close()

    await cb.message.answer(f"✅ Заказ #{oid}: статус -> {new_status}")

    items, has_prev, has_next, total = await _load_orders_page(page, status)
    text = f"🧾 Заказы (всего: {total})" + (f" • фильтр: {status}" if status else "")
    await cb.message.edit_text(
        text,
        reply_markup=admin_orders_list_kb(
            items=items,
            page=page,
            has_prev=has_prev,
            has_next=has_next,
            status=status,
        ),
    )