from __future__ import annotations

from typing import Any

import httpx

from app.settings import settings


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str | None = None):
        self.status = status
        self.code = code
        self.error = code
        self.message = message or code
        super().__init__(f"Ошибка API: {status} {self.message}")


class ApiClient:
    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=settings.api_base_url,
            timeout=10.0,
        )

    async def close(self):
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        files: Any | None = None,
        headers: dict[str, str] | None = None,
    ):
        resp = await self._client.request(
            method,
            url,
            params=params,
            json=json,
            files=files,
            headers=headers,
        )

        if resp.status_code >= 400:
            await self._raise(resp)

        if not resp.content:
            return None

        try:
            return resp.json()
        except Exception:
            return resp.text

    async def _raise(self, resp: httpx.Response):
        data: Any = None
        try:
            data = resp.json()
        except Exception:
            data = None

        code = "HTTP_ERROR"
        message = None

        if isinstance(data, dict):
            code = data.get("error") or code
            message = data.get("message")

            detail = data.get("detail")
            if isinstance(detail, dict):
                code = detail.get("error") or detail.get("code") or code
                message = detail.get("message") or message
            elif isinstance(detail, str) and not message:
                code = detail
                message = detail

        raise ApiError(resp.status_code, str(code), message)

    async def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        return await self._request("GET", url, params=params, headers=headers)

    async def post(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ):
        return await self._request("POST", url, params=params, json=json, headers=headers)

    async def post_multipart(
        self,
        url: str,
        *,
        files: Any,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        return await self._request("POST", url, params=params, files=files, headers=headers)

    async def patch(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ):
        return await self._request("PATCH", url, params=params, json=json, headers=headers)

    async def delete(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        return await self._request("DELETE", url, params=params, headers=headers)

    def bot_user_headers(self) -> dict[str, str]:
        if not settings.BOT_USER_SECRET:
            raise ApiError(500, "BOT_USER_SECRET_MISSING", "Не задан BOT_USER_SECRET в настройках бота")
        return {"X-Bot-User-Secret": settings.BOT_USER_SECRET}

    def bot_admin_headers(self) -> dict[str, str]:
        if not settings.BOT_ADMIN_SECRET:
            raise ApiError(500, "BOT_ADMIN_SECRET_MISSING", "Не задан BOT_ADMIN_SECRET в настройках бота")
        return {"X-Bot-Admin-Secret": settings.BOT_ADMIN_SECRET}
