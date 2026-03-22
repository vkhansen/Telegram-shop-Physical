from aiogram.filters.state import State, StatesGroup


class GoodsFSM(StatesGroup):
    """FSM for position (goods) and items management scenarios."""
    waiting_item_name_delete = State()
    waiting_item_name_show = State()


class AddItemFSM(StatesGroup):
    """
    FSM for step-by-step creation of a menu item:
    0) item type (product/prepared), 1) name, 2) description, 3) photo(s),
    4) price, 5) category, 6) stock, 7) prep time, 8) allergens,
    9) availability, 10) daily limit, 11) modifiers (interactive or JSON).
    """
    waiting_item_type = State()  # product (packaged) or prepared (made-to-order)
    waiting_item_name = State()
    waiting_item_description = State()
    waiting_item_image = State()         # Photo upload (multiple) or skip
    waiting_item_price = State()
    waiting_category = State()
    waiting_stock_quantity = State()
    waiting_prep_time = State()          # Minutes or skip
    waiting_allergens = State()          # Multi-select or skip
    waiting_availability = State()       # "HH:MM-HH:MM" or skip
    waiting_daily_limit = State()        # Integer or skip
    waiting_modifiers_json = State()     # Card 8: optional modifier schema
    # Interactive modifier builder states
    waiting_modifier_group_name = State()
    waiting_modifier_group_type = State()
    waiting_modifier_option_label = State()
    waiting_modifier_option_price = State()


class ModifierSelectionFSM(StatesGroup):
    """FSM for selecting modifiers when adding item to cart (Card 8)."""
    selecting_modifiers = State()


class UpdateItemFSM(StatesGroup):
    """
    FSM for updating an item:
    1) Manage stock quantity for an existing position.
    2) Full update (name, description, price).
    """
    # Manage stock for an item
    waiting_item_name_for_stock_mgmt = State()
    waiting_stock_action = State()
    waiting_stock_quantity = State()

    # Full update
    waiting_item_name_for_update = State()
    waiting_item_new_name = State()
    waiting_item_description = State()
    waiting_item_price = State()

