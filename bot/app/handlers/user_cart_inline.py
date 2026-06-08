from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.callbacks.cart import CartCb
from app.store.cart import get_cart
from app.handlers.user_catalog import render_catalog
from app.handlers.user_cart import render_cart

router = Router()

def decode_in_stock(v: int) -> bool | None:
    if v == 1:
        return True
    if v == 0:
        return False
    return None

@router.callback_query(CartCb.filter((F.a.in_({"inc", "dec", "noop"})) & (F.src == "cat")))
async def cart_inc_dec_in_catalog(cb: CallbackQuery, callback_data: CartCb):
    await cb.answer(cache_time=0)

    if callback_data.a == "noop":
        return

    cart = get_cart(cb.from_user.id)
    pid = int(callback_data.pid)

    if callback_data.a == "inc":
        cart.add(pid, 1)
    else:
        cart.add(pid, -1)

    await render_catalog(
        cb,
        page=int(callback_data.page),
        in_stock=decode_in_stock(int(callback_data.in_stock)),
    )

@router.callback_query(CartCb.filter((F.a == "open") & (F.src == "cat")))
async def open_cart_from_catalog(cb: CallbackQuery):
    await cb.answer()
    await render_cart(cb)