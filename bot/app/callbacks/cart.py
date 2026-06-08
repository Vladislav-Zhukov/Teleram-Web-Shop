from aiogram.filters.callback_data import CallbackData

class CartCb(CallbackData, prefix="cart"):
    # a: inc|dec|noop|checkout|open
    a: str
    pid: int = 0

    # context (чтобы после +/− обновлять правильный экран)
    src: str = ""        # "" | "cat"
    page: int = 0
    in_stock: int = -1   # -1 None, 0 False, 1 True
