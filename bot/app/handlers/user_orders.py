from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.api_client.base import ApiClient
from app.api_client.orders import OrdersAPI
from app.callbacks.orders import MyOrdersCb
from app.keyboards.user import my_orders_kb

router = Router()
PAGE_SIZE = 5


def fmt_order(o: dict) -> str:
    # OrderOut: id, status, items...
    return f'#{o["id"]} | {o.get("status")}'


@router.message(F.text.in_({"/my_orders", "📦 Мои заказы"}))
async def my_orders_cmd(m: Message):
    await render_my_orders(m, page=0)


async def render_my_orders(target: Message | CallbackQuery, page: int):
    uid = target.from_user.id
    c = ApiClient()
    try:
        items = await OrdersAPI(c).my_telegram(telegram_id=uid)  # список
    finally:
        await c.close()

    total = len(items)
    start = page * PAGE_SIZE
    chunk = items[start : start + PAGE_SIZE]
    has_prev = page > 0
    has_next = start + PAGE_SIZE < total

    text = "📦 Мои заказы:\n" + ("\n".join(fmt_order(o) for o in chunk) if chunk else "Пока заказов нет.")
    markup = my_orders_kb(page, has_prev, has_next)

    if isinstance(target, Message):
        await target.answer(text, reply_markup=markup)
    else:
        await target.message.edit_text(text, reply_markup=markup)


@router.callback_query(MyOrdersCb.filter(F.a == "list"))
async def my_orders_list(cb: CallbackQuery, callback_data: MyOrdersCb):
    await cb.answer()
    await render_my_orders(cb, page=callback_data.page)
