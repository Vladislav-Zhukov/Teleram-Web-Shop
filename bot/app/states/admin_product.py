from aiogram.fsm.state import StatesGroup, State

class AddProductSG(StatesGroup):
    name = State()
    stock = State()
    price = State()
    description = State()
    photo = State()

class EditProductSG(StatesGroup):
    value = State()

class DeleteProductSG(StatesGroup):
    confirm = State()