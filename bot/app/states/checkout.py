from aiogram.fsm.state import StatesGroup, State

class CheckoutState(StatesGroup):
    comment = State()
    confirm = State()