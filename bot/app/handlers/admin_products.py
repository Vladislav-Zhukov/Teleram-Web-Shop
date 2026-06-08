from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.filters.is_admin import IsAdmin
from app.states.admin_product import AddProductSG
from app.api_client.base import ApiClient, ApiError
from app.api_client.products import ProductsAPI

router = Router()

@router.message(IsAdmin(), F.text == "➕ Добавить товар")
async def add_start(m: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AddProductSG.name)
    await m.answer("Введите название товара:")

@router.message(IsAdmin(), AddProductSG.name)
async def add_name(m: Message, state: FSMContext):
    await state.update_data(name=m.text.strip())
    await state.set_state(AddProductSG.stock)
    await m.answer("Введите количество (stock):")

@router.message(IsAdmin(), AddProductSG.stock)
async def add_stock(m: Message, state: FSMContext):
    await state.update_data(stock=int(m.text))
    await state.set_state(AddProductSG.price)
    await m.answer("Введите цену:")

@router.message(IsAdmin(), AddProductSG.price)
async def add_price(m: Message, state: FSMContext):
    await state.update_data(price=float(m.text.replace(",", ".")))
    await state.set_state(AddProductSG.description)
    await m.answer("Введите описание:")

@router.message(IsAdmin(), AddProductSG.description)
async def add_description(m: Message, state: FSMContext):
    await state.update_data(description=m.text.strip())
    await state.set_state(AddProductSG.photo)
    await m.answer("Отправьте фото или '-' чтобы пропустить")

@router.message(IsAdmin(), AddProductSG.photo)
async def add_photo_and_create(m: Message, state: FSMContext):
    data = await state.get_data()
    c = ApiClient()
    try:
        created = await ProductsAPI(c).create(
            name=data["name"],
            description=data["description"],
            price=data["price"],
            stock=data["stock"],
        )

        if m.photo:
            file = m.photo[-1]
            tg_file = await m.bot.get_file(file.file_id)
            downloaded = await m.bot.download_file(tg_file.file_path)
            content = downloaded.read()

            await ProductsAPI(c).upload_image(
                product_id=int(created["id"]),
                filename="photo.jpg",
                content=content,
                make_primary=True,
            )

        await m.answer(f"Товар создан: #{created['id']}")
    except ApiError as e:
        await m.answer(f"Ошибка API: {e.error}")
    finally:
        await c.close()
        await state.clear()
