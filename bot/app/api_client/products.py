from app.api_client.base import ApiClient


class ProductsAPI:
    def __init__(self, c: ApiClient):
        self.c = c

    async def list(self):
        return await self.c.get("/products/")

    async def list_page(
        self,
        *,
        limit: int = 5,
        offset: int = 0,
        search: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        in_stock: bool | None = None,
    ):
        params: dict[str, object] = {"limit": limit, "offset": offset}
        if search:
            params["search"] = search
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if in_stock is not None:
            params["in_stock"] = "true" if in_stock else "false"

        return await self.c.get("/products/", params=params)

    async def get(self, product_id: int):
        return await self.c.get(f"/products/{product_id}")

    async def create(self, name: str, description: str, price: float, stock: int):
        return await self.c.post(
            "/products/",
            json={"name": name, "description": description, "price": price, "stock": stock},
            headers=self.c.bot_admin_headers(),
        )

    async def patch(self, product_id: int, data: dict):
        return await self.c.patch(
            f"/products/{product_id}",
            json=data,
            headers=self.c.bot_admin_headers(),
        )

    async def admin_patch(self, product_id: int, data: dict):
        return await self.patch(product_id, data)

    async def upload_image(self, product_id: int, filename: str, content: bytes, make_primary: bool = True):
        content_type = "image/jpeg"
        lower = filename.lower()
        if lower.endswith(".png"):
            content_type = "image/png"
        elif lower.endswith(".webp"):
            content_type = "image/webp"

        files = {"file": (filename, content, content_type)}
        return await self.c.post_multipart(
            "/products/{}/images".format(product_id),
            params={"make_primary": "true" if make_primary else "false"},
            files=files,
            headers=self.c.bot_admin_headers(),
        )

    async def set_primary(self, product_id: int, image_id: int):
        return await self.c.patch(
            f"/products/{product_id}/images/{image_id}/primary",
            headers=self.c.bot_admin_headers(),
        )

    async def delete_image(self, product_id: int, image_id: int):
        return await self.c.delete(
            f"/products/{product_id}/images/{image_id}",
            headers=self.c.bot_admin_headers(),
        )

    async def delete_product(self, product_id: int):
        return await self.c.delete(
            f"/products/{product_id}",
            headers=self.c.bot_admin_headers(),
        )
