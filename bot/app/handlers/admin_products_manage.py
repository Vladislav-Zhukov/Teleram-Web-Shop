from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.filters.is_admin import IsAdmin
from app.api_client.base import ApiClient, ApiError
from app.api_client.products import ProductsAPI
from app.callbacks.admin_products import AdminProdCb
from app.keyboards.admin import (
    admin_products_list,
    admin_edit_fields,
    admin_view_back_kb,      # Назад к списку
)
from app.states.admin_product import EditProductSG, DeleteProductSG

router = Router()

PAGE_SIZE = 10


async def _load_products_page(page: int, in_stock: bool | None = None):
    c = ApiClient()
    try:
        data = await ProductsAPI(c).list_page(
            limit=PAGE_SIZE,
            offset=page * PAGE_SIZE,
            in_stock=in_stock,   # фильтр
        )
    finally:
        await c.close()

    items = data["items"]
    total = int(data["total"])
    has_prev = page > 0
    has_next = page * PAGE_SIZE + PAGE_SIZE < total
    return items, has_prev, has_next, total


# ----- MENU -----

@router.message(IsAdmin(), F.text == "📦 Все товары")
async def admin_view_menu(m: Message, state: FSMContext):
    await state.clear()
    items, has_prev, has_next, total = await _load_products_page(0)
    if not items:
        await m.answer("Товаров нет.")
        return

    await m.answer(
        f"📦 Все товары (всего: {total})\n\nВыберите товар:",
        reply_markup=admin_products_list(items, "view", 0, has_prev, has_next),
    )


@router.message(IsAdmin(), F.text == "✏️ Редактировать товар")
async def edit_menu(m: Message, state: FSMContext):
    await state.clear()
    items, has_prev, has_next, total = await _load_products_page(0)
    if not items:
        await m.answer("Товаров нет.")
        return

    await m.answer(
        f"Выберите товар (всего: {total}):",
        reply_markup=admin_products_list(items, "edit", 0, has_prev, has_next),
    )


@router.message(IsAdmin(), F.text == "🙈 Скрыть товар")
async def hide_menu(m: Message, state: FSMContext):
    await state.clear()
    items, has_prev, has_next, total = await _load_products_page(0)
    if not items:
        await m.answer("Товаров нет.")
        return

    await m.answer(
        f"Выберите товар для скрытия (всего: {total}):",
        reply_markup=admin_products_list(items, "hide", 0, has_prev, has_next),
    )


@router.message(IsAdmin(), F.text == "👁 Убрать товар из скрытого")
async def unhide_menu(m: Message, state: FSMContext):
    await state.clear()
    items, has_prev, has_next, total = await _load_products_page(0, in_stock=False)

    if not items:
        await m.answer("Скрытых товаров нет.")
        return

    await m.answer(
        f"🙈 Скрытые товары (всего: {total})\n\nВыберите товар, чтобы показать обратно:",
        reply_markup=admin_products_list(items, "unhide", 0, has_prev, has_next),
    )


@router.message(IsAdmin(), F.text == "🗑 Удалить товар")
async def delete_menu(m: Message, state: FSMContext):
    await state.clear()
    items, has_prev, has_next, total = await _load_products_page(0)
    if not items:
        await m.answer("Товаров нет.")
        return

    await m.answer(
        f"Выберите товар для удаления (всего: {total}):",
        reply_markup=admin_products_list(items, "delete", 0, has_prev, has_next),
    )


# ----- NAVIGATION -----

@router.callback_query(IsAdmin(), AdminProdCb.filter(F.a == "nav"))
async def nav_list(cb: CallbackQuery, callback_data: AdminProdCb):
    await cb.answer()

    page = int(callback_data.page)
    direction = callback_data.dir
    mode = callback_data.mode or "view"

    if direction == "prev":
        new_page = page - 1
    elif direction == "next":
        new_page = page + 1
    else:  # stay
        new_page = page

    stock_filter: bool | None = False if mode == "unhide" else None

    items, has_prev, has_next, total = await _load_products_page(new_page, in_stock=stock_filter)

    if not items and total != 0:
        items, has_prev, has_next, _ = await _load_products_page(page, in_stock=stock_filter)
        new_page = page

    await cb.message.edit_text(
        "Скрытые товары:",
        reply_markup=admin_products_list(items, mode, new_page, has_prev, has_next),
    )


# ----- PICK PRODUCT -----

@router.callback_query(IsAdmin(), AdminProdCb.filter(F.a == "pick"))
async def pick_product(cb: CallbackQuery, callback_data: AdminProdCb, state: FSMContext):
    await cb.answer()

    pid = int(callback_data.pid)
    mode = callback_data.mode or "view"
    page = int(callback_data.page)

    if mode == "view":
        c = ApiClient()
        try:
            p = await ProductsAPI(c).get(pid)
        finally:
            await c.close()

        await cb.message.edit_text(
            f"📦 Товар #{pid}\n\n"
            f"Название: {p.get('name')}\n"
            f"Цена: {p.get('price')}\n"
            f"Склад: {p.get('stock')}\n"
            f"В наличии: {p.get('in_stock')}",
            reply_markup=admin_view_back_kb(page),
        )
        return

    if mode == "edit":
        await cb.message.edit_text(
            f"Товар #{pid}: выберите поле",
            reply_markup=admin_edit_fields(pid, page),
        )
        return

    if mode == "hide":
        c = ApiClient()
        try:
            await ProductsAPI(c).patch(pid, {"in_stock": False})
            await cb.message.answer(f"✅ Товар #{pid} скрыт.")
        except ApiError as e:
            await cb.message.answer(f"Ошибка API: {e.error}")
        finally:
            await c.close()
        return

    if mode == "unhide":
        c = ApiClient()
        try:
            await ProductsAPI(c).patch(pid, {"in_stock": True})
            await cb.message.answer(f"✅ Товар #{pid} снова показывается.")
        except ApiError as e:
            await cb.message.answer(f"Ошибка API: {e.error}")
        finally:
            await c.close()
        return

    if mode == "delete":
        await state.set_state(DeleteProductSG.confirm)
        await state.update_data(pid=pid)
        await cb.message.answer("Введите 'Удалить' для подтверждения.")
        return


# ----- EDIT VALUE -----

@router.callback_query(IsAdmin(), AdminProdCb.filter(F.a == "field"))
async def choose_field(cb: CallbackQuery, callback_data: AdminProdCb, state: FSMContext):
    await cb.answer()

    await state.set_state(EditProductSG.value)
    await state.update_data(pid=int(callback_data.pid), field=callback_data.field)

    if callback_data.field == "photo":
        await cb.message.answer("Отправьте новое фото.")
    else:
        await cb.message.answer("Введите новое значение.")


@router.message(IsAdmin(), EditProductSG.value)
async def edit_value(m: Message, state: FSMContext):
    data = await state.get_data()
    pid = int(data["pid"])
    field = data["field"]

    c = ApiClient()
    try:
        if field == "photo":
            if not m.photo:
                await m.answer("Нужно отправить фото.")
                return
            file = m.photo[-1]
            tg_file = await m.bot.get_file(file.file_id)
            downloaded = await m.bot.download_file(tg_file.file_path)
            content = downloaded.read()

            await ProductsAPI(c).upload_image(pid, "photo.jpg", content, True)

        else:
            patch = {}
            if field == "stock":
                patch["stock"] = int((m.text or "").strip())
            elif field == "price":
                patch["price"] = float((m.text or "").replace(",", ".").strip())
            elif field == "name":
                patch["name"] = (m.text or "").strip()
            elif field == "description":
                patch["description"] = (m.text or "").strip()
            elif field == "in_stock":
                patch["in_stock"] = (m.text or "").strip().lower() in {"1", "true", "да", "yes", "on"}
            else:
                await m.answer("Неизвестное поле.")
                return

            await ProductsAPI(c).patch(pid, patch)

        await m.answer("✅ Изменения сохранены.")

    except Exception:
        await m.answer("❌ Ошибка обновления.")
    finally:
        await c.close()
        await state.clear()


# ----- DELETE CONFIRM -----

@router.message(IsAdmin(), DeleteProductSG.confirm)
async def delete_confirm(m: Message, state: FSMContext):
    data = await state.get_data()
    pid = data["pid"]

    if m.text.lower() != "удалить":
        await m.answer("Удаление отменено.")
        await state.clear()
        return

    c = ApiClient()
    try:
        await ProductsAPI(c).delete_product(pid)
        await m.answer(f"✅ Товар #{pid} удалён.")

    except ApiError as e:
        # если товар используется в заказах
        if e.status == 409 and e.error == "PRODUCT_USED_IN_ORDERS":
            await m.answer(
                "⚠️ Товар нельзя удалить, т.к. он хранится в истории заказов."
            )
        else:
            await m.answer(f"❌ Ошибка API: {e.status} {e.error}")

    finally:
        await c.close()
        await state.clear()