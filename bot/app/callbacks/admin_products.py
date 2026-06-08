from aiogram.filters.callback_data import CallbackData

class AdminProdCb(CallbackData, prefix="ap"):
    a: str               # list|pick|field|nav
    pid: int = 0
    page: int = 0
    mode: str | None = None
    field: str | None = None
    dir: str | None = None