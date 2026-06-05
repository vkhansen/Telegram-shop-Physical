from aiogram.filters.state import State, StatesGroup


class BroadcastFSM(StatesGroup):
    """FSM state for the broadcast message"""

    waiting_message = State()
