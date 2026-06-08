from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from app.callbacks.admin_products import AdminProdCb
from app.callbacks.orders import AdminOrdersCb  # важно для админ-заказов


ORDER_STATUSES = ["NEW", "PAID", "SHIPPED", "DELIVERED", "CANCELED"]

# -------------------------
# keyboard: Admin menu
# -------------------------

def admin_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Все товары")],
            [KeyboardButton(text="➕ Добавить товар"), KeyboardButton(text="✏️ Редактировать товар")],
            [KeyboardButton(text="🙈 Скрыть товар"), KeyboardButton(text="👁 Убрать товар из скрытого")],
            [KeyboardButton(text="🗑 Удалить товар")],
            [KeyboardButton(text="🧾 Заказы")],
        ],
        resize_keyboard=True,
    )

# -------------------------
# Products: list + nagination
# -------------------------

def admin_products_list(items: list[dict], mode: str, page: int, has_prev: bool, has_next: bool):
    """
    mode: edit | hide | delete
    """
    builder = InlineKeyboardBuilder()

    for p in items:
        builder.button(
            text=f'#{p["id"]} {p["name"]}',
            callback_data=AdminProdCb(
                a="pick",
                pid=int(p["id"]),
                page=page,
                mode=mode
            ).pack(),
        )

    builder.adjust(1)

    nav = InlineKeyboardBuilder()

    if has_prev:
        nav.button(
            text="⬅️",
            callback_data=AdminProdCb(
                a="nav",
                page=page,
                mode=mode,
                dir="prev"
            ).pack(),
        )

    nav.button(
        text=f"Стр. {page + 1}",
        callback_data=AdminProdCb(
            a="list",
            page=page,
            mode=mode
        ).pack(),
    )

    if has_next:
        nav.button(
            text="➡️",
            callback_data=AdminProdCb(
                a="nav",
                page=page,
                mode=mode,
                dir="next"
            ).pack(),
        )

    nav.adjust(3)

    for row in nav.export():
        builder.row(*row)

    return builder.as_markup()


def admin_edit_fields(pid: int, page: int, mode: str = "edit"):
    builder = InlineKeyboardBuilder()

    builder.button(text="Название", callback_data=AdminProdCb(a="field", pid=pid, page=page, field="name").pack())
    builder.button(text="Кол-во", callback_data=AdminProdCb(a="field", pid=pid, page=page, field="stock").pack())
    builder.button(text="Цена", callback_data=AdminProdCb(a="field", pid=pid, page=page, field="price").pack())
    builder.button(text="Описание", callback_data=AdminProdCb(a="field", pid=pid, page=page, field="description").pack())
    builder.button(text="Фото", callback_data=AdminProdCb(a="field", pid=pid, page=page, field="photo").pack())

    builder.button(
        text="⬅️ Назад к списку",
        callback_data=AdminProdCb(a="list", page=page, mode=mode).pack(),
    )

    builder.adjust(2)
    return builder.as_markup()


# -------------------------
# Orders (admin): list + pagination
# -------------------------

def admin_orders_kb(page: int, has_prev: bool, has_next: bool):
    b = InlineKeyboardBuilder()

    if has_prev:
        b.button(text="⬅️", callback_data=AdminOrdersCb(a="list", page=page - 1).pack())

    b.button(text=f"Стр. {page + 1}", callback_data=AdminOrdersCb(a="list", page=page).pack())

    if has_next:
        b.button(text="➡️", callback_data=AdminOrdersCb(a="list", page=page + 1).pack())

    b.adjust(3)
    return b.as_markup()


def admin_order_status_kb(order_id: int, page: int, current_status: str | None = None):
    b = InlineKeyboardBuilder()
    for status in ORDER_STATUSES:
        text = f"✅ {status}" if current_status == status else status
        b.button(text=text, callback_data=AdminOrdersCb(a="set", oid=order_id, new_status=status, page=page).pack())

    b.button(text="⬅️ Назад к списку", callback_data=AdminOrdersCb(a="list", page=page).pack())
    b.adjust(2)
    return b.as_markup()

def admin_view_back_kb(page: int):
    b = InlineKeyboardBuilder()
    b.button(
        text="⬅️ Назад к списку",
        callback_data=AdminProdCb(
            a="nav",
            page=page,
            dir="stay",
            mode="view",
        ).pack(),
    )
    return b.as_markup()


def admin_orders_list_kb(*, items: list[dict], page: int, has_prev: bool, has_next: bool, status: str):
    b = InlineKeyboardBuilder()

    # --- filter row ---
    # 1) "Все"
    b.button(
        text=("✅ Все" if status == "" else "Все"),
        callback_data=AdminOrdersCb(a="filter", page=0, status="").pack(),
    )
    # 2) statuses (в 2 строки)
    for s in ORDER_STATUSES:
        b.button(
            text=("✅ " + s if status == s else s),
            callback_data=AdminOrdersCb(a="filter", page=0, status=s).pack(),
        )
    b.adjust(3, 3)  # "Все"+"NEW"+"PAID" / "SHIPPED"+"DELIVERED"+"CANCELED"

    # --- orders list ---
    for o in items:
        oid = int(o["id"])
        st = o.get("status", "")
        total = o.get("total", None)
        label = f"#{oid} {st}"
        if total is not None:
            label += f" • {float(total):.2f}"
        b.row(
            InlineKeyboardButton(
                text=label,
                callback_data=AdminOrdersCb(a="open", oid=oid, page=page, status=status).pack(),
            )
        )

    # --- nav row ---
    nav: list[InlineKeyboardButton] = []
    if has_prev:
        nav.append(InlineKeyboardButton(
            text="⬅️",
            callback_data=AdminOrdersCb(a="prev", page=page, status=status).pack(),
        ))
    nav.append(InlineKeyboardButton(
        text=f"Стр. {page+1}",
        callback_data=AdminOrdersCb(a="list", page=page, status=status).pack(),
    ))
    if has_next:
        nav.append(InlineKeyboardButton(
            text="➡️",
            callback_data=AdminOrdersCb(a="next", page=page, status=status).pack(),
        ))
    b.row(*nav)

    return b.as_markup()


def admin_order_open_kb(*, oid: int, page: int, status: str):
    b = InlineKeyboardBuilder()

    # кнопки смены статуса
    for s in ORDER_STATUSES:
        b.button(
            text=s,
            callback_data=AdminOrdersCb(a="set", oid=oid, new_status=s, page=page, status=status).pack(),
        )
    b.adjust(3, 2)  # 3 + 2 (5 статусов)

    # назад
    b.row(
        InlineKeyboardButton(
            text="⬅️ Назад к списку",
            callback_data=AdminOrdersCb(a="list", page=page, status=status).pack(),
        )
    )
    return b.as_markup()