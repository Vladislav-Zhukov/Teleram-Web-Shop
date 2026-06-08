from aiogram.filters.callback_data import CallbackData

class CheckoutCb(CallbackData, prefix="chk"):
    a: str