from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from bot.database.main import Database
from bot.database.models.main import Goods
from bot.keyboards import back, simple_buttons
from bot.i18n import localize

router = Router()


class SearchStates(StatesGroup):
    waiting_search_query = State()


@router.callback_query(F.data == "search_products")
async def search_products_prompt(call: CallbackQuery, state: FSMContext):
    """
    Prompt the user to enter a search query.
    """
    await call.message.edit_text(
        localize("search.prompt"),
        reply_markup=back("back_to_menu"),
    )
    await state.set_state(SearchStates.waiting_search_query)


@router.message(SearchStates.waiting_search_query)
async def process_search_query(message: Message, state: FSMContext):
    """
    Search goods by name and description using ILIKE and display results.
    """
    query = message.text.strip()
    if not query:
        await message.answer(
            localize("search.prompt"),
            reply_markup=back("back_to_menu"),
        )
        return

    # Escape SQL LIKE wildcards to prevent wildcard injection
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"

    with Database().session() as session:
        results = (
            session.query(Goods)
            .filter(
                Goods.name.ilike(pattern, escape="\\") | Goods.description.ilike(pattern, escape="\\")
            )
            .all()
        )

    if not results:
        await message.answer(
            localize("search.no_results"),
            reply_markup=back("back_to_menu"),
        )
        await state.clear()
        return

    buttons = [
        (
            item.name,
            f"item_{item.name}_{item.category_name}_goods-page_{item.category_name}_0",
        )
        for item in results
    ]
    buttons.append((localize("btn.back"), "back_to_menu"))

    await message.answer(
        localize("search.results_title", query=query),
        reply_markup=simple_buttons(buttons),
    )
    await state.clear()
