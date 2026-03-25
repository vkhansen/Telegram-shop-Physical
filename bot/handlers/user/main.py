from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums.chat_type import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from urllib.parse import urlparse
import datetime

from bot.database.methods import (
    select_max_role_id, create_user, check_role,
    select_user_items, check_user_cached,
    get_reference_bonus_percent
)
from bot.database import Database
from bot.database.models.main import CustomerInfo, User
from bot.handlers.other import check_sub_channel
from bot.keyboards import main_menu, back, profile_keyboard, check_sub, language_picker_keyboard
from bot.config import EnvKeys
from bot.i18n import localize, set_request_locale, get_user_locale
from bot.i18n.strings import LANGUAGE_PICKER_MESSAGE, LANGUAGE_CHANGED_MESSAGES, AVAILABLE_LOCALES
from bot.logger_mesh import logger

router = Router()


async def show_main_menu(message: Message, state: FSMContext):
    """
    Show the main menu to the user

    Args:
        message: Message object
        state: FSM context
    """
    user_id = message.from_user.id

    # Parse channel username safely from ENV
    channel_url = EnvKeys.CHANNEL_URL or ""
    parsed = urlparse(channel_url)
    channel_username = (
                           parsed.path.lstrip('/')
                           if parsed.path else channel_url.replace("https://t.me/", "").replace("t.me/", "").lstrip('@')
                       ) or None

    role_data = check_role(user_id)

    # Optional subscription check
    try:
        if channel_username:
            chat_member = await message.bot.get_chat_member(chat_id=f'@{channel_username}', user_id=user_id)
            if not await check_sub_channel(chat_member):
                markup = check_sub(channel_username)
                await message.answer(localize("subscribe.prompt"), reply_markup=markup)
                return
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        # Ignore channel errors (private channel, wrong link, etc.)
        logger.warning(f"Channel subscription check failed for user {user_id}: {e}")

    markup = main_menu(role=role_data, channel=channel_username, helper=EnvKeys.HELPER_ID)
    await message.answer(localize("menu.title"), reply_markup=markup)
    await state.clear()


@router.message(F.text.startswith('/start'))
async def start(message: Message, state: FSMContext):
    """
    Handle /start:
    - If new user → show language picker first → then reference code
    - If existing user without locale → show language picker → then menu
    - If existing user with locale → show main menu
    """
    if message.chat.type != ChatType.PRIVATE:
        return

    user_id = message.from_user.id
    await state.clear()

    # Check if user already exists
    existing_user = await check_user_cached(user_id)

    if existing_user:
        # Check if user has selected a language yet
        user_locale = get_user_locale(user_id)
        if user_locale:
            set_request_locale(user_locale)
            await show_main_menu(message, state)
            await message.delete()
            return
        else:
            # Existing user but no language — show picker
            await message.answer(
                LANGUAGE_PICKER_MESSAGE,
                reply_markup=language_picker_keyboard()
            )
            await state.update_data(after_language="menu")
            return

    # New user — show language picker first (Card 14)
    # Save referral info in state for after language selection
    referral_text = message.text[7:] if len(message.text) > 7 else ""
    await state.update_data(
        after_language="register",
        referral_text=referral_text
    )
    await message.answer(
        LANGUAGE_PICKER_MESSAGE,
        reply_markup=language_picker_keyboard()
    )


@router.callback_query(F.data.startswith("set_locale_"))
async def set_locale_callback(call: CallbackQuery, state: FSMContext):
    """
    Handle language selection from the flag picker.
    Saves locale to user record, then continues the appropriate flow.
    """
    locale_code = call.data.replace("set_locale_", "")
    user_id = call.from_user.id

    if locale_code not in AVAILABLE_LOCALES:
        await call.answer(localize("errors.invalid_language"))
        return

    await call.answer()

    # Set locale for this request
    set_request_locale(locale_code)

    # Get state data to determine what to do next
    data = await state.get_data()
    after_language = data.get("after_language", "menu")

    # Save locale to database
    with Database().session() as session:
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if user:
            user.locale = locale_code
            session.commit()

    # Send confirmation in the selected language
    confirm_msg = LANGUAGE_CHANGED_MESSAGES.get(locale_code, f"✅ Language set to {locale_code}")

    if after_language == "register":
        # New user — continue to registration flow
        referral_text = data.get("referral_text", "")

        # Check if reference codes are enabled
        from bot.database.models.main import BotSettings
        with Database().session() as session:
            setting = session.query(BotSettings).filter_by(setting_key='reference_codes_enabled').first()
            refcodes_enabled = setting and setting.setting_value.lower() == 'true' if setting else True

        if not refcodes_enabled or str(user_id) == EnvKeys.OWNER_ID:
            owner_max_role = select_max_role_id()
            referral_id = referral_text if referral_text and referral_text != str(user_id) else None
            user_role = owner_max_role if str(user_id) == EnvKeys.OWNER_ID else 1

            create_user(
                telegram_id=int(user_id),
                registration_date=datetime.datetime.now(),
                referral_id=int(referral_id) if referral_id and referral_id.isdigit() else None,
                role=user_role,
                locale=locale_code
            )

            await call.message.edit_text(confirm_msg)

            # Show PDPA privacy notice before main menu (Card: Privacy)
            await state.update_data(after_privacy="register")
            from bot.handlers.user.privacy_handler import show_privacy_notice
            await show_privacy_notice(call.message, state)
            return

        # Reference codes enabled — save locale temporarily and prompt for code
        await state.update_data(selected_locale=locale_code)
        await call.message.edit_text(confirm_msg)

        from bot.handlers.user.reference_code_handler import prompt_reference_code
        await prompt_reference_code(call.message, state)

    elif after_language == "language_change":
        # User just changing language via /language
        await call.message.edit_text(confirm_msg)
        await show_main_menu(call.message, state)

    else:
        # Existing user picking language for first time
        await call.message.edit_text(confirm_msg)
        await show_main_menu(call.message, state)


@router.message(F.text == "/language")
async def language_command(message: Message, state: FSMContext):
    """
    /language command — show language picker anytime.
    """
    if message.chat.type != ChatType.PRIVATE:
        return

    await state.clear()
    await state.update_data(after_language="language_change")
    await message.answer(
        LANGUAGE_PICKER_MESSAGE,
        reply_markup=language_picker_keyboard()
    )


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback_handler(call: CallbackQuery, state: FSMContext):
    """
    Return user to the main menu.
    """
    user_id = call.from_user.id
    user = await check_user_cached(user_id)
    if not user:
        create_user(
            telegram_id=user_id,
            registration_date=datetime.datetime.now(),
            referral_id=None,
            role=1
        )
        user = await check_user_cached(user_id)

    role_id = user.get('role_id')

    channel_url = EnvKeys.CHANNEL_URL or ""
    parsed = urlparse(channel_url)
    channel_username = (
                           parsed.path.lstrip('/')
                           if parsed.path else channel_url.replace("https://t.me/", "").replace("t.me/", "").lstrip('@')
                       ) or None

    markup = main_menu(role=role_id, channel=channel_username, helper=EnvKeys.HELPER_ID)
    await call.message.edit_text(localize("menu.title"), reply_markup=markup)
    await state.clear()


@router.callback_query(F.data == "rules")
async def rules_callback_handler(call: CallbackQuery, state: FSMContext):
    """
    Show rules text if provided in ENV.
    """
    rules_data = EnvKeys.RULES
    if rules_data:
        await call.message.edit_text(rules_data, reply_markup=back("back_to_menu"))
    else:
        await call.answer(localize("rules.not_set"))
    await state.clear()


@router.callback_query(F.data == "profile")
async def profile_callback_handler(call: CallbackQuery, state: FSMContext):
    """
    Send profile info (balance, purchases count, id, etc.).
    """
    user_id = call.from_user.id
    tg_user = call.from_user
    user_info = await check_user_cached(user_id)

    items = select_user_items(user_id)
    referral = int(get_reference_bonus_percent())

    # Get referral bonus balance from CustomerInfo
    with Database().session() as session:
        customer_info = session.query(CustomerInfo).filter_by(telegram_id=user_id).first()
        bonus_balance = customer_info.bonus_balance if customer_info and customer_info.bonus_balance else 0

    markup = profile_keyboard(referral, items)
    text = (
        f"{localize('profile.caption', name=tg_user.first_name, id=user_id)}\n"
        f"{localize('profile.id', id=user_id)}\n"
        f"{localize('profile.bonus_balance', bonus_balance=bonus_balance)}\n"
        f"{localize('profile.purchased_count', count=items)}"
    )
    await call.message.edit_text(text, reply_markup=markup, parse_mode='HTML')
    await state.clear()


@router.callback_query(F.data == "sub_channel_done")
async def check_sub_to_channel(call: CallbackQuery, state: FSMContext):
    """
    Re-check channel subscription after user clicks "Check".
    """
    user_id = call.from_user.id
    chat = EnvKeys.CHANNEL_URL or ""
    parsed_url = urlparse(chat)
    channel_username = (
                           parsed_url.path.lstrip('/')
                           if parsed_url.path else chat.replace("https://t.me/", "").replace("t.me/", "").lstrip('@')
                       ) or None
    helper = EnvKeys.HELPER_ID

    if channel_username:
        chat_member = await call.bot.get_chat_member(chat_id='@' + channel_username, user_id=user_id)
        if await check_sub_channel(chat_member):
            user = await check_user_cached(user_id)
            role_id = user.get('role_id')
            markup = main_menu(role_id, channel_username, helper)
            await call.message.edit_text(localize("menu.title"), reply_markup=markup)
            await state.clear()
            return

    await call.answer(localize("errors.not_subscribed"))
