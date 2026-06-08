from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Awaitable, Any
from app.api_client.base import ApiError

class ErrorMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, dict], Awaitable[Any]], event: TelegramObject, data: dict):
        try:
            return await handler(event, data)
        except ApiError as e:
            text = "Ошибка."
            if e.error == "OUT_OF_STOCK":
                text = "❌ Товара нет в наличии."
            elif e.error in ("AUTH_REQUIRED", "INVALID_TOKEN"):
                text = "🔐 Нужно войти на сайте (нет/протух токен)."
            if hasattr(event, "answer"):
                await event.answer(text)
            return
