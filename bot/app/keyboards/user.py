from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.callbacks.catalog import CatalogCb
from app.callbacks.cart import CartCb
from app.callbacks.orders import MyOrdersCb
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardButton
from app.callbacks.checkout import CheckoutCb


def user_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Каталог"), KeyboardButton(text="🛒 Корзина")],
            [KeyboardButton(text="📦 Мои заказы"), KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="🔓 Отвязать Telegram")],
        ],
        resize_keyboard=True,
    )

def my_orders_kb(page: int, has_prev: bool, has_next: bool):
    b = InlineKeyboardBuilder()
    if has_prev:
        b.button(text="⬅️", callback_data=MyOrdersCb(a="list", page=page-1).pack())
    b.button(text=f"Стр. {page+1}", callback_data=MyOrdersCb(a="list", page=page).pack())
    if has_next:
        b.button(text="➡️", callback_data=MyOrdersCb(a="list", page=page+1).pack())
    b.adjust(3)
    return b.as_markup()

def my_order_open_kb(order_id: int):
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ Назад", callback_data=MyOrdersCb(a="list", page=0).pack())
    return b.as_markup()


def catalog_kb(page: int, has_prev: bool, has_next: bool, in_stock: bool | None):
    b = InlineKeyboardBuilder()

    if has_prev:
        b.button(text="⬅️", callback_data=CatalogCb(a="prev", page=page-1).pack())
    b.button(text=f"Стр. {page+1}", callback_data=CatalogCb(a="open", page=page).pack())
    if has_next:
        b.button(text="➡️", callback_data=CatalogCb(a="next", page=page+1).pack())
    b.adjust(3)

    # наличие
    label = "✅ В наличии: ON" if in_stock is True else "✅ В наличии: OFF"
    b.button(text=label, callback_data=CatalogCb(a="toggle_stock", page=page).pack())

    return b.as_markup()


def catalog_items_kb(items: list[dict], page: int):
    b = InlineKeyboardBuilder()
    for p in items:
        b.button(
            text=f'#{p["id"]} {p["name"]}',
            callback_data=CatalogCb(a="item", page=page, pid=p["id"]).pack()
        )
    b.adjust(1)
    return b.as_markup()


def product_kb(product_id: int, can_add: bool):
    b = InlineKeyboardBuilder()
    if can_add:
        b.button(text="🛒 В корзину", callback_data=CartCb(a="add", pid=product_id, qty=1).pack())
    b.button(text="⬅️ Назад", callback_data=CatalogCb(a="open", page=0).pack())
    b.adjust(1)
    return b.as_markup()


def cart_kb(cart_items: dict[int, int], names: dict[int, str]):
    b = InlineKeyboardBuilder()

    for pid, qty in cart_items.items():
        pid = int(pid)
        qty = int(qty)
        title = names.get(pid, f"Товар #{pid}")

        b.row(
            InlineKeyboardButton(
                text=title,
                callback_data=CartCb(a="noop", pid=pid, src="cart").pack(),
            )
        )

        # 2) строка управления количеством
        b.row(
            InlineKeyboardButton(
                text="➖",
                callback_data=CartCb(a="dec", pid=pid, src="cart").pack(),
            ),
            InlineKeyboardButton(
                text=str(qty),
                callback_data=CartCb(a="noop", pid=pid, src="cart").pack(),
            ),
            InlineKeyboardButton(
                text="➕",
                callback_data=CartCb(a="inc", pid=pid, src="cart").pack(),
            ),
        )

    # checkout
    b.row(
        InlineKeyboardButton(
            text="✅ ОФОРМИТЬ ЗАКАЗ",
            callback_data=CheckoutCb(a="start").pack(),
        )
    )
    return b.as_markup()

def _is_available(p: dict) -> bool:
    # надёжно: если backend отдаёт и in_stock, и stock
    if p.get("in_stock") is False:
        return False
    try:
        stock = int(p.get("stock", 0))
    except Exception:
        stock = 0
    return stock > 0

def _fmt_price(p: dict) -> str:
    price = p.get("price")
    return str(price) if price is not None else "-"

def catalog_cart_kb(
    items: list[dict],
    page: int,
    has_prev: bool,
    has_next: bool,
    in_stock: bool | None,
    cart_items,
):
    b = InlineKeyboardBuilder()
    stock_flag = _pack_stock(in_stock)

    # --- NAV row ---
    nav_buttons: list[InlineKeyboardButton] = []
    if has_prev:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=CatalogCb(a="prev", page=page, in_stock=stock_flag).pack(),
            )
        )
    nav_buttons.append(
        InlineKeyboardButton(
            text=f"Стр. {page+1}",
            callback_data=CatalogCb(a="open", page=page, in_stock=stock_flag).pack(),
        )
    )
    if has_next:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=CatalogCb(a="next", page=page, in_stock=stock_flag).pack(),
            )
        )
    b.row(*nav_buttons)

    # --- toggle row ---
    label = "✅ В наличии: ON" if in_stock is True else "✅ В наличии: OFF"
    b.row(
        InlineKeyboardButton(
            text=label,
            callback_data=CatalogCb(a="toggle_stock", page=page, in_stock=stock_flag).pack(),
        )
    )

    # pid -> qty
    if isinstance(cart_items, dict):
        cart_map = {int(pid): int(qty) for pid, qty in cart_items.items()}
    else:
        cart_map = {int(pid): int(qty) for pid, qty in cart_items}

    # --- items: title row + controls row ---
    for p in items:
        pid = int(p["id"])
        qty = int(cart_map.get(pid, 0))

        available = _is_available(p)
        status = "✅" if available else "❌"
        price = _fmt_price(p)

        # 1) title row
        b.row(
            InlineKeyboardButton(
                text=f'{status} #{pid} {p["name"]} - {price}',
                callback_data=CatalogCb(a="item", page=page, pid=pid, in_stock=stock_flag).pack(),
            )
        )

        # 2) controls row
        if available:
            b.row(
                InlineKeyboardButton(
                    text="➖",
                    callback_data=CartCb(a="dec", pid=pid, src="cat", page=page, in_stock=stock_flag).pack(),
                ),
                InlineKeyboardButton(
                    text=str(qty),
                    callback_data=CartCb(a="noop", pid=pid, src="cat", page=page, in_stock=stock_flag).pack(),
                ),
                InlineKeyboardButton(
                    text="➕",
                    callback_data=CartCb(a="inc", pid=pid, src="cat", page=page, in_stock=stock_flag).pack(),
                ),
            )
        else:
            # одна кнопка вместо 3х
            b.row(
                InlineKeyboardButton(
                    text="🚫 Нет в наличии",
                    callback_data=CartCb(a="noop", pid=pid, src="cat", page=page, in_stock=stock_flag).pack(),
                )
            )

    # --- cart row ---
    total_qty = sum(cart_map.values())
    b.row(
        InlineKeyboardButton(
            text=f"🛒 Корзина ({total_qty})",
            callback_data=CartCb(a="open").pack(),
        )
    )

    return b.as_markup()


def _pack_stock(in_stock: bool | None) -> int:
    # формат: -1=None, 0=False, 1=True
    if in_stock is True:
        return 1
    if in_stock is False:
        return 0
    return -1

def checkout_confirm_kb():
    b = InlineKeyboardBuilder()
    b.button(text="✅ Подтвердить", callback_data=CheckoutCb(a="confirm").pack())
    b.button(text="❌ Отмена", callback_data=CheckoutCb(a="cancel").pack())
    b.adjust(2)
    return b.as_markup()