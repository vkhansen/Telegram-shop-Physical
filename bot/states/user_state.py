from aiogram.filters.state import StatesGroup, State


class UserMgmtStates(StatesGroup):
    """FSM for user management flow."""
    waiting_user_id_for_check = State()
    waiting_user_bonus = State()


class LanguageStates(StatesGroup):
    """FSM for language selection flow (Card 14)."""
    waiting_language = State()


class ReferenceCodeStates(StatesGroup):
    """FSM for reference code validation flow."""
    waiting_reference_code = State()
    waiting_refcode_note = State()
    waiting_refcode_expires = State()
    waiting_refcode_max_uses = State()


class OrderStates(StatesGroup):
    """FSM for order placement flow."""
    waiting_location_method = State()  # Choose: GPS / Live GPS / Google Maps link / Type address
    waiting_delivery_address = State()
    waiting_address_confirm = State()  # Confirm searched address
    waiting_google_maps_link = State()  # Paste Google Maps link
    waiting_location = State()  # GPS location sharing (Card 2)
    waiting_live_location = State()  # Live location sharing
    waiting_delivery_type = State()  # Door / Dead Drop / Pickup (Card 3)
    waiting_drop_instructions = State()  # Dead drop instructions (Card 3)
    waiting_drop_gps = State()  # Dead drop GPS location (Card 3)
    waiting_drop_media = State()  # Dead drop photos/videos — multiple (Card 3)
    waiting_drop_photo = State()  # Dead drop location photo — legacy (Card 3)
    waiting_phone_number = State()
    waiting_delivery_note = State()
    waiting_bonus_amount = State()  # For applying referral bonus to order
    waiting_payment_method = State()


class DeliveryChatStates(StatesGroup):
    """FSM for delivery chat flow (Card 13 + Card 15)."""
    chatting_with_driver = State()  # Customer is in active chat relay mode (Card 13)
    waiting_customer_gps_choice = State()  # GPS choice prompt (Card 15)


class HelpStates(StatesGroup):
    """FSM for help/support flow."""
    waiting_help_message = State()


class SupportStates(StatesGroup):
    """FSM for support ticket system."""
    choosing_type = State()        # bug_report / feedback / live_chat
    waiting_subject = State()      # Ticket subject line
    waiting_description = State()  # Detailed description
    waiting_screenshot = State()   # Optional screenshot
    live_chatting = State()        # Active live chat with maintainer


class CartStates(StatesGroup):
    """FSM for shopping cart checkout flow."""
    viewing_cart = State()
    waiting_quantity = State()


class AdminOrderStates(StatesGroup):
    """FSM for admin order management (Card 4)."""
    waiting_delivery_photo = State()


class SettingsFSM(StatesGroup):
    """FSM for bot settings management."""
    waiting_referral_percent = State()
    waiting_order_timeout = State()
    waiting_timezone = State()
    waiting_promptpay_id = State()
    waiting_promptpay_name = State()


class GrokAssistantStates(StatesGroup):
    """FSM for Grok AI admin assistant (Card 17)."""
    chatting = State()               # Main conversation loop
    awaiting_confirmation = State()  # Waiting for yes/no on mutation
    awaiting_file = State()          # Waiting for CSV/data upload
