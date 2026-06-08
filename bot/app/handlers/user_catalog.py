from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.api_client.base import ApiClient, ApiError
from app.api_client.products import ProductsAPI
from app.api_client.users import UsersAPI
from app.callbacks.catalog import CatalogCb

from app.keyboards.user import user_main_menu, catalog_cart_kb
from app.keyboards.admin import admin_main_menu

from app.store.cart import get_cart
from app.settings import settings

router = Router()
PAGE_SIZE = 5


def fmt_item(p: dict) -> str:
    status = "✅" if p.get("in_stock") else "❌"
    price = p.get("price")
    stock = p.get("stock")
    name = p.get("name")
    pid = p.get("id")
    return f"{status} #{pid} {name} - {price} (stock={stock})"


async def render_catalog(target: Message | CallbackQuery, page: int, in_stock: bool | None):
    offset = page * PAGE_SIZE

    c = ApiClient()
    try:
        data = await ProductsAPI(c).list_page(
            limit=PAGE_SIZE,
            offset=offset,
            in_stock=in_stock,
        )
    finally:
        await c.close()

    items = data["items"]
    total = int(data["total"])
    has_prev = page > 0
    has_next = offset + PAGE_SIZE < total

    cart = get_cart(target.from_user.id)

    if not items:
        text = "Каталог пуст." if total == 0 else "На этой странице нет товаров."
    else:
        text = "🛍 Каталог:\n\nНажимай ➖/➕ чтобы менять количество."

    markup = catalog_cart_kb(
        items=items,
        page=page,
        has_prev=has_prev,
        has_next=has_next,
        in_stock=in_stock,
        cart_items=cart.items,
    )

    if isinstance(target, Message):
        await target.answer(text, reply_markup=markup)
    else:
        await target.message.edit_text(text, reply_markup=markup)


@router.message(F.text.startswith("/start"))
async def start(m: Message):
    uid = m.from_user.id

    # /start <payload>
    parts = (m.text or "").split(maxsplit=1)
    payload = parts[1].strip() if len(parts) > 1 else ""

    # если не привязался
    if payload:
        c = ApiClient()
        try:
            await UsersAPI(c).bind_by_code(code=payload, telegram_id=uid)
        except ApiError as e:
            await m.answer(f"❌ Не получилось привязать: {e.error}")
            return
        finally:
            await c.close()

        await m.answer("✅ Telegram привязан к аккаунту на сайте! Теперь история заказов общая.")
        if uid in settings.admins():
            await m.answer("Привет, админ 👑", reply_markup=admin_main_menu())
        else:
            await m.answer("Привет! Выбирай действие кнопками ниже 👇", reply_markup=user_main_menu())
        return

    # отображение ТГ привязки
    linked_text = ""
    c = ApiClient()
    try:
        st = await UsersAPI(c).status_by_telegram_id(uid)
        if st.get("linked"):
            linked_text = "✅ Telegram привязан."
        else:
            linked_text = "❌ Telegram не привязан. Привязать можно с сайта (кнопка «Привязать Telegram»)."
    except ApiError:
        linked_text = ""
    finally:
        await c.close()

    if uid in settings.admins():
        await m.answer("Привет, админ 👑", reply_markup=admin_main_menu())
        if linked_text:
            await m.answer(linked_text)
    else:
        await m.answer("Привет! Выбирай действие кнопками ниже 👇", reply_markup=user_main_menu())
        if linked_text:
            await m.answer(linked_text)


@router.message(F.text == "🔓 Отвязать Telegram")
async def unlink_telegram(m: Message):
    uid = m.from_user.id
    c = ApiClient()
    try:
        await UsersAPI(c).unlink_by_telegram_id(uid)
    except ApiError as e:
        await m.answer(f"❌ Не получилось отвязать: {e.error}")
        return
    finally:
        await c.close()

    await m.answer("✅ Telegram отвязан от аккаунта сайта.")


@router.message(F.text == "🛍 Каталог")
async def catalog_btn(m: Message):
    await render_catalog(m, page=0, in_stock=None)


@router.callback_query(CatalogCb.filter(F.a.in_({"open", "next", "prev"})))
async def catalog_nav(cb: CallbackQuery, callback_data: CatalogCb):
    await cb.answer()

    page = callback_data.page
    if callback_data.a == "next":
        page += 1
    elif callback_data.a == "prev":
        page -= 1

    in_stock = None
    if callback_data.in_stock == 1:
        in_stock = True
    elif callback_data.in_stock == 0:
        in_stock = False

    await render_catalog(cb, page=page, in_stock=in_stock)


@router.callback_query(CatalogCb.filter(F.a == "toggle_stock"))
async def toggle_stock(cb: CallbackQuery, callback_data: CatalogCb):
    await cb.answer()

    if callback_data.in_stock == -1:
        in_stock = True
    elif callback_data.in_stock == 1:
        in_stock = False
    else:
        in_stock = None

    await render_catalog(cb, page=callback_data.page, in_stock=in_stock)