from aiogram.filters.state import StatesGroup, State


class BalanceStates(StatesGroup):
    """FSM states for the balance top-up flow."""
    waiting_amount = State()
    waiting_payment = State()


class PromptPayStates(StatesGroup):
    """FSM states for PromptPay payment flow (Card 1)."""
    waiting_receipt_photo = State()
