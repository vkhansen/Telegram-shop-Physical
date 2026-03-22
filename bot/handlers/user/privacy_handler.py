"""
PDPA-compliant Privacy Notice handler.

- Shows privacy notice card on first interaction (new users) or via /privacy command.
- Records user acceptance with timestamp for audit trail.
- Provides link to full privacy policy page.
"""

import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums.chat_type import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import EnvKeys
from bot.database import Database
from bot.database.models.main import User
from bot.i18n import localize

router = Router()


def privacy_notice_keyboard():
    """
    Inline keyboard for the privacy notice card.
    Button 1: Link to full policy (URL button, if configured)
    Button 2: Accept & Continue (callback)
    """
    kb = InlineKeyboardBuilder()

    policy_url = EnvKeys.PRIVACY_POLICY_URL
    if policy_url:
        kb.button(text=localize("privacy.btn_full_policy"), url=policy_url)

    kb.button(text=localize("privacy.btn_accept"), callback_data="privacy_accept")
    kb.adjust(1)
    return kb.as_markup()


def get_privacy_notice_text() -> str:
    """Build the privacy notice text with configured company/email."""
    company = EnvKeys.PRIVACY_COMPANY_NAME or "—"
    email = EnvKeys.PRIVACY_CONTACT_EMAIL or "/contact"
    return localize("privacy.notice", company=company, email=email)


async def show_privacy_notice(message: Message, state: FSMContext):
    """
    Send the privacy notice card to the user.
    Called during registration flow or via /privacy command.
    """
    text = get_privacy_notice_text()
    await message.answer(text, reply_markup=privacy_notice_keyboard(), parse_mode="HTML")


@router.message(F.text == "/privacy")
async def privacy_command(message: Message, state: FSMContext):
    """
    /privacy command — show privacy notice anytime.
    """
    if message.chat.type != ChatType.PRIVATE:
        return

    text = get_privacy_notice_text()
    await message.answer(text, reply_markup=privacy_notice_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "privacy_accept")
async def privacy_accept_callback(call: CallbackQuery, state: FSMContext):
    """
    Handle privacy policy acceptance.
    Records timestamp in database for PDPA compliance audit trail.
    """
    user_id = call.from_user.id
    await call.answer()

    now = datetime.datetime.now(datetime.timezone.utc)

    with Database().session() as session:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if user:
            if user.privacy_accepted_at:
                await call.message.edit_text(localize("privacy.already_accepted"))
                return
            user.privacy_accepted_at = now
            session.commit()

    await call.message.edit_text(localize("privacy.accepted"))

    # Check if this was during registration flow
    data = await state.get_data()
    if data.get("after_privacy") == "register":
        # Continue to main menu after privacy acceptance
        from bot.handlers.user.main import show_main_menu
        await show_main_menu(call.message, state)


@router.callback_query(F.data == "privacy_view")
async def privacy_view_callback(call: CallbackQuery, state: FSMContext):
    """
    Show privacy notice from profile/menu.
    """
    await call.answer()
    text = get_privacy_notice_text()
    await call.message.edit_text(text, reply_markup=privacy_notice_keyboard(), parse_mode="HTML")
