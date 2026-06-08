from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.callbacks.cart import CartCb
from app.callbacks.checkout import CheckoutCb
from app.states.checkout import CheckoutState

from app.store.cart import get_cart
from app.handlers.user_cart import render_cart

from app.api_client.base import ApiClient
from app.api_client.orders import OrdersAPI

from aiogram.exceptions import TelegramBadRequest

router = Router()

@router.callback_query(CartCb.filter(F.a == "checkout"))
async def start_checkout(cb: CallbackQuery, state: FSMContext):
    await cb.answer()

    cart = get_cart(cb.from_user.id)
    if not cart.items:
        await render_cart(cb)
        return

    await state.set_state(CheckoutState.comment)
    await cb.message.edit_text(
        "✍️ Напиши комментарий к заказу (можно адрес/доставка). Если не нужно - отправь '-'",
    )

@router.message(CheckoutState.comment)
async def checkout_comment(m: Message, state: FSMContext):
    text = (m.text or "").strip()
    comment = "" if text == "-" else text

    await state.update_data(comment=comment)
    await state.set_state(CheckoutState.confirm)

    cart = get_cart(m.from_user.id)
    if not cart.items:
        await state.clear()
        await m.answer("🛒 Корзина пуста.")
        return

    lines = [f"• id={pid} - x{qty}" for pid, qty in cart.items.items()]
    summary = "\n".join(lines)
    if comment:
        summary += f"\n\n📝 Комментарий: {comment}"

    from app.keyboards.user import checkout_confirm_kb
    await m.answer("Подтверди заказ:\n\n" + summary, reply_markup=checkout_confirm_kb())

@router.callback_query(CheckoutCb.filter(F.a == "cancel"))
async def checkout_cancel(cb: CallbackQuery, state: FSMContext):
    await cb.answer("Отменено")
    await state.clear()
    await render_cart(cb)

@router.callback_query(CheckoutCb.filter(F.a == "confirm"))
async def checkout_confirm(cb: CallbackQuery, state: FSMContext):
    await cb.answer("Оформляю…", show_alert=False)

    cart = get_cart(cb.from_user.id)
    if not cart.items:
        await state.clear()
        await render_cart(cb)
        return

    data = await state.get_data()
    comment = (data.get("comment") or "").strip()

    items = [{"product_id": int(pid), "quantity": int(qty)} for pid, qty in cart.items.items()]

    c = ApiClient()
    try:
        res = await OrdersAPI(c).create_telegram(telegram_id=cb.from_user.id, items=items)
    finally:
        await c.close()

    cart.clear()
    await state.clear()

    text = f"✅ Заказ создан: #{res['id']} статус={res['status']}"
    try:
        await cb.message.edit_text(text)
    except TelegramBadRequest:
        await cb.message.answer(text)