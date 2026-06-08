from app.api_client.base import ApiClient

class OrdersAPI:
    def __init__(self, c: ApiClient):
        self.c = c

    async def my(self):
        return await self.c.get("/orders/my")

    async def admin_page(self, limit: int = 10, offset: int = 0, status: str | None = None):
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return await self.c.get(
            "/orders/",
            params=params,
            headers=self.c.bot_admin_headers(),
        )

    async def admin_set_status(self, order_id: int, status: str):
        return await self.c.patch(
            f"/orders/{order_id}/status",
            json={"status": status},
            headers=self.c.bot_admin_headers(),
        )

    async def create(self, access_token: str, items: list[dict]):
        return await self.c.post(
            "/orders/",
            json={"items": items},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    async def create_telegram(self, telegram_id: int, items: list[dict]):
        return await self.c.post(
            "/orders/telegram",
            json={"telegram_id": telegram_id, "items": items},
            headers=self.c.bot_user_headers(),
        )

    async def my_telegram(self, telegram_id: int):
        return await self.c.get(
            "/orders/telegram/my",
            params={"telegram_id": telegram_id},
            headers=self.c.bot_user_headers(),
        )
