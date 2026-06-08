import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from app.store.cart import get_cart
from app.callbacks.cart import CartCb
from app.keyboards.user import cart_kb
from app.api_client.base import ApiClient
from app.api_client.products import ProductsAPI
from app.api_client.orders import OrdersAPI
from app.callbacks.checkout import CheckoutCb

router = Router()


async def _cart_text_and_names(cart_items: dict[int, int]) -> tuple[str, dict[int, str]]:
    if not cart_items:
        return "🛒 Корзина пуста.", {}

    names: dict[int, str] = {}
    c = ApiClient()
    try:
        api = ProductsAPI(c)
        for pid in cart_items.keys():
            try:
                p = await api.get(int(pid))
                names[int(pid)] = p.get("name") or f"#{pid}"
            except Exception:
                names[int(pid)] = f"#{pid}"
    finally:
        await c.close()

    lines = []
    total = 0.0
    for pid, qty in cart_items.items():
        pid = int(pid)
        qty = int(qty)
        lines.append(f"• {names.get(pid, f'#{pid}')} (id={pid}) - x{qty}")

    return "🛒 Корзина:\n" + "\n".join(lines), names


async def render_cart(target: Message | CallbackQuery) -> None:
    cart = get_cart(target.from_user.id)
    text, names = await _cart_text_and_names(cart.items)
    markup = cart_kb(cart.items, names) if cart.items else None

    if isinstance(target, Message):
        await target.answer(text, reply_markup=markup)
    else:
        try:
            await target.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest as e:
            # если текст не изменился - обновим только клавиатуру
            if "message is not modified" in str(e).lower():
                try:
                    await target.message.edit_reply_markup(reply_markup=markup)
                except TelegramBadRequest:
                    pass
            else:
                raise


@router.message(F.text.in_({"/cart", "🛒 Корзина"}))
async def cart_cmd(m: Message):
    await render_cart(m)

@router.callback_query(CartCb.filter(F.a == "open"))
async def cart_open(cb: CallbackQuery):
    await cb.answer()
    await render_cart(cb)


@router.callback_query(CartCb.filter(F.a.in_({"inc", "dec", "noop"}) & (F.src != "cat")))
async def cart_inc_dec(cb: CallbackQuery, callback_data: CartCb):
    await cb.answer(cache_time=0)

    if callback_data.a == "noop":
        return

    cart = get_cart(cb.from_user.id)
    pid = int(callback_data.pid)

    if callback_data.a == "inc":
        cart.add(pid, 1)
    else:
        cart.add(pid, -1)

    await render_cart(cb)

log = logging.getLogger(__name__)

@router.callback_query(CheckoutCb.filter(F.a == "start"))
async def cart_checkout(cb: CallbackQuery):
    await cb.answer("Оформляю…", show_alert=False)

    cart = get_cart(cb.from_user.id)
    if not cart.items:
        await render_cart(cb)
        return

    items = [{"product_id": int(pid), "quantity": int(qty)} for pid, qty in cart.items.items()]
    log.info("CHECKOUT: user=%s items=%s", cb.from_user.id, items)

    c = ApiClient()
    try:
        res = await OrdersAPI(c).create_telegram(
            telegram_id=cb.from_user.id,
            items=items,
        )
        log.info("CHECKOUT OK: %s", res)
    except Exception as e:
        log.exception("CHECKOUT FAILED: %s", e)
        try:
            await cb.message.edit_text(f"❌ Не удалось оформить заказ: {type(e).__name__}: {e}")
        except TelegramBadRequest:
            await cb.message.answer(f"❌ Не удалось оформить заказ: {type(e).__name__}: {e}")
        return
    finally:
        await c.close()

    cart.clear()

    text = f"✅ Заказ создан: #{res.get('id')} статус={res.get('status')}"
    try:
        await cb.message.edit_text(text)
    except TelegramBadRequest:
        await cb.message.answer(text)