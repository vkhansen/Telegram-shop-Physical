from aiogram import Dispatcher

from bot.handlers.admin import router as admin_router
from bot.handlers.driver import router as driver_router
from bot.handlers.other import router as other_router
from bot.handlers.user import router as user_router


def register_all_handlers(dp: Dispatcher) -> None:
    dp.include_router(admin_router)
    # Driver router goes before the user router so an approved driver's private
    # live-location edits are claimed here; non-drivers fall through (the
    # location handlers are gated by a DB filter) to the customer chat handlers.
    dp.include_router(driver_router)
    dp.include_router(other_router)
    dp.include_router(user_router)
