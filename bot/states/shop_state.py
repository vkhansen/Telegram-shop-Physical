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
    # Card 21: brand-switch save/delete/stay guard
    confirming_brand_switch = State()
    # Card 21: store-switch availability guard
    confirming_store_switch = State()
