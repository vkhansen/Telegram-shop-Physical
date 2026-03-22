from aiogram.filters.state import State, StatesGroup


class ShopStates(StatesGroup):
    """
    FSM states for the shopping section (personal purchases list).
    """
    selecting_brand = State()
    selecting_branch = State()
    viewing_goods = State()
    viewing_bought_items = State()
    viewing_categories = State()
