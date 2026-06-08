from aiogram.filters.callback_data import CallbackData

class MyOrdersCb(CallbackData, prefix="myo"):
    a: str          # list|open
    page: int = 0
    oid: int | None = None

class AdminOrdersCb(CallbackData, prefix="ao"):
    a: str  # list | open | set | prev | next | filter
    page: int = 0
    oid: int | None = None
    status: str | None = None        # текущий фильтр
    new_status: str | None = None    # новый статус для set
