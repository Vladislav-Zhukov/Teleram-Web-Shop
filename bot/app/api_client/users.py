from app.api_client.base import ApiClient


class UsersAPI:
    def __init__(self, c: ApiClient):
        self.c = c

    async def bind_by_code(self, code: str, telegram_id: int):
        return await self.c.post(
            "/users/telegram/bind-by-code",
            json={"code": code, "telegram_id": telegram_id},
            headers=self.c.bot_user_headers(),
        )

    async def status_by_telegram_id(self, telegram_id: int):
        return await self.c.get(
            "/users/telegram/status-by-telegram-id",
            params={"telegram_id": telegram_id},
            headers=self.c.bot_user_headers(),
        )

    async def unlink_by_telegram_id(self, telegram_id: int):
        return await self.c.post(
            "/users/telegram/unlink-by-telegram-id",
            json={"telegram_id": telegram_id},
            headers=self.c.bot_user_headers(),
        )