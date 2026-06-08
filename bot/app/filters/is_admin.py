from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from app.settings import settings

class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        uid = event.from_user.id
        return uid in settings.admins()
