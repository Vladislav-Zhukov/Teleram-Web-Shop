from aiogram.filters.callback_data import CallbackData

class CatalogCb(CallbackData, prefix="cat"):
    a: str
    page: int = 0
    pid: int = 0
    in_stock: int = -1  # -1 = None, 0 = False, 1 = True