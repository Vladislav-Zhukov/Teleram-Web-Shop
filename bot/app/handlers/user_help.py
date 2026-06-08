from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "❓ Помощь")
async def help_btn(m: Message):
    await m.answer(
        "❓ Помощь\n\n"
        "🛍 Каталог - посмотреть товары\n"
        "🛒 Корзина - посмотреть корзину\n"
        "📦 Мои заказы - ваши заказы и статусы\n\n"
    )