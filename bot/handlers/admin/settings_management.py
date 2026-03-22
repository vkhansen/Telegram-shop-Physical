import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.database.models.main import Permission, BotSettings
from bot.database.main import Database
from bot.database.methods.read import get_reference_bonus_percent, get_bot_setting
from bot.states.user_state import SettingsFSM
from bot.keyboards.inline import back, settings_management_keyboard, timezone_selection_keyboard
from bot.filters import HasPermissionFilter
from bot.config import timezone
from bot.config.env import EnvKeys
from bot.i18n.strings import localize

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "settings_management", HasPermissionFilter(Permission.SETTINGS_MANAGE))
async def settings_menu(call: CallbackQuery, state: FSMContext):
    """
    Show settings management menu (admin/owner only).
    Displays current values for all configurable settings.
    """
    await state.clear()

    # Get current settings
    current_percent = get_reference_bonus_percent()
    current_timeout = get_bot_setting('cash_order_timeout_hours', default=24, value_type=int)
    current_timezone = timezone.get_timezone()
    promptpay_id = get_bot_setting('promptpay_id') or EnvKeys.PROMPTPAY_ID or "Not set"
    promptpay_name = get_bot_setting('promptpay_account_name') or EnvKeys.PROMPTPAY_ACCOUNT_NAME or "Not set"
    current_currency = get_bot_setting('pay_currency') or EnvKeys.PAY_CURRENCY

    await call.message.edit_text(
        f"⚙️ <b>Bot Settings</b>\n\n"
        f"<b>Current Values:</b>\n"
        f"• Referral Bonus: <b>{current_percent}%</b>\n"
        f"• Order Timeout: <b>{current_timeout} hours</b>\n"
        f"• Timezone: <b>{current_timezone}</b>\n"
        f"• PromptPay: <b>{promptpay_id}</b> ({promptpay_name})\n"
        f"• Currency: <b>{current_currency}</b>\n\n"
        f"Select a setting to modify:",
        reply_markup=settings_management_keyboard(),
        parse_mode='HTML'
    )


@router.callback_query(F.data == "setting_referral_percent", HasPermissionFilter(Permission.SETTINGS_MANAGE))
async def set_referral_percent_start(call: CallbackQuery, state: FSMContext):
    """
    Start referral percentage update flow.
    """
    current_percent = get_reference_bonus_percent()

    await call.message.edit_text(
        f"💰 <b>Update Referral Bonus Percentage</b>\n\n"
        f"Current value: <b>{current_percent}%</b>\n\n"
        f"Enter new percentage (0-100):\n"
        f"• Example: <code>5</code> (for 5%)\n"
        f"• Example: <code>10</code> (for 10%)\n"
        f"• Example: <code>0</code> (to disable referral bonuses)\n\n"
        f"<i>This percentage will be applied to all future completed orders.</i>",
        reply_markup=back("settings_management"),
        parse_mode='HTML'
    )
    await state.set_state(SettingsFSM.waiting_referral_percent)


@router.message(SettingsFSM.waiting_referral_percent, F.text)
async def process_referral_percent(message: Message, state: FSMContext):
    """
    Process and save referral percentage.
    Validates input and updates the database.
    """
    try:
        # Validate input - must be integer
        percent_value = int(message.text.strip())

        if percent_value < 0 or percent_value > 100:
            await message.answer(
                "❌ <b>Invalid input</b>\n\n"
                "Percentage must be between 0 and 100.\n"
                "Please try again:",
                reply_markup=back("settings_management"),
                parse_mode='HTML'
            )
            return

        # Update database
        with Database().session() as session:
            setting = session.query(BotSettings).filter_by(
                setting_key='reference_bonus_percent'
            ).first()

            if setting:
                setting.setting_value = str(percent_value)
            else:
                setting = BotSettings(
                    setting_key='reference_bonus_percent',
                    setting_value=str(percent_value)
                )
                session.add(setting)

            session.commit()

        # Show confirmation
        status_text = "enabled" if percent_value > 0 else "disabled"
        await message.answer(
            f"✅ <b>Referral Bonus Updated!</b>\n\n"
            f"New percentage: <b>{percent_value}%</b>\n"
            f"Status: <b>{status_text.upper()}</b>\n\n"
            f"This will apply to all future completed orders.\n"
            f"Users will receive {percent_value}% of their referral's order total as bonus balance.",
            reply_markup=settings_management_keyboard(),
            parse_mode='HTML'
        )

    except ValueError:
        await message.answer(
            "❌ <b>Invalid input</b>\n\n"
            "Please enter a valid whole number (0-100).\n"
            "Examples: 5, 10, 15, 20",
            reply_markup=back("settings_management"),
            parse_mode='HTML'
        )
        return

    await state.clear()


@router.callback_query(F.data == "setting_order_timeout", HasPermissionFilter(Permission.SETTINGS_MANAGE))
async def set_order_timeout_start(call: CallbackQuery, state: FSMContext):
    """
    Start order timeout update flow.
    """
    current_timeout = get_bot_setting('cash_order_timeout_hours', default=24, value_type=int)

    await call.message.edit_text(
        f"⏱️ <b>Update Order Timeout</b>\n\n"
        f"Current value: <b>{current_timeout} hours</b>\n\n"
        f"Enter new timeout in hours (1-168):\n"
        f"• Example: <code>24</code> (24 hours / 1 day)\n"
        f"• Example: <code>48</code> (48 hours / 2 days)\n"
        f"• Example: <code>72</code> (72 hours / 3 days)\n\n"
        f"<i>Orders will automatically expire after this time if not paid.</i>",
        reply_markup=back("settings_management"),
        parse_mode='HTML'
    )
    await state.set_state(SettingsFSM.waiting_order_timeout)


@router.message(SettingsFSM.waiting_order_timeout, F.text)
async def process_order_timeout(message: Message, state: FSMContext):
    """
    Process and save order timeout.
    Validates input and updates the database.
    """
    try:
        # Validate input - must be integer
        timeout_hours = int(message.text.strip())

        if timeout_hours < 1 or timeout_hours > 168:  # Max 1 week
            await message.answer(
                "❌ <b>Invalid input</b>\n\n"
                "Timeout must be between 1 and 168 hours (1 week).\n"
                "Please try again:",
                reply_markup=back("settings_management"),
                parse_mode='HTML'
            )
            return

        # Update database
        with Database().session() as session:
            setting = session.query(BotSettings).filter_by(
                setting_key='cash_order_timeout_hours'
            ).first()

            if setting:
                setting.setting_value = str(timeout_hours)
            else:
                setting = BotSettings(
                    setting_key='cash_order_timeout_hours',
                    setting_value=str(timeout_hours)
                )
                session.add(setting)

            session.commit()

        # Calculate days for display
        days = timeout_hours / 24
        days_text = f"{days:.1f} day(s)" if days != int(days) else f"{int(days)} day(s)"

        # Show confirmation
        await message.answer(
            f"✅ <b>Order Timeout Updated!</b>\n\n"
            f"New timeout: <b>{timeout_hours} hours</b> ({days_text})\n\n"
            f"All new orders will automatically expire after {timeout_hours} hours if not paid.\n"
            f"Reserved inventory will be released when orders expire.",
            reply_markup=settings_management_keyboard(),
            parse_mode='HTML'
        )

    except ValueError:
        await message.answer(
            "❌ <b>Invalid input</b>\n\n"
            "Please enter a valid whole number (1-168).\n"
            "Examples: 12, 24, 48, 72",
            reply_markup=back("settings_management"),
            parse_mode='HTML'
        )
        return

    await state.clear()


@router.callback_query(F.data == "setting_timezone", HasPermissionFilter(Permission.SETTINGS_MANAGE))
async def set_timezone_start(call: CallbackQuery, state: FSMContext):
    """
    Start timezone update flow with popular options.
    """
    current_tz = timezone.get_timezone()
    current_time = timezone.get_localized_time()

    await call.message.edit_text(
        f"🌍 <b>Update Timezone</b>\n\n"
        f"Current timezone: <b>{current_tz}</b>\n"
        f"Current time: <b>{current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}</b>\n\n"
        f"Select a timezone from popular options below,\n"
        f"or choose 'Enter manually' to type your own.\n\n"
        f"<i>This affects all logging timestamps.</i>",
        reply_markup=timezone_selection_keyboard(),
        parse_mode='HTML'
    )


@router.callback_query(F.data.startswith("tz_select:"), HasPermissionFilter(Permission.SETTINGS_MANAGE))
async def select_timezone_from_button(call: CallbackQuery, state: FSMContext):
    """
    Process timezone selection from inline buttons.
    """
    # Extract timezone from callback_data
    timezone_str = call.data.split(":", 1)[1]

    # Validate timezone
    if not timezone.validate_timezone(timezone_str):
        await call.answer("❌ Invalid timezone!", show_alert=True)
        return

    # Update database
    with Database().session() as session:
        setting = session.query(BotSettings).filter_by(
            setting_key='timezone'
        ).first()

        if setting:
            setting.setting_value = timezone_str
        else:
            setting = BotSettings(
                setting_key='timezone',
                setting_value=timezone_str
            )
            session.add(setting)

        session.commit()

    # Hot reload timezone
    timezone.reload_timezone()
    new_time = timezone.get_localized_time()

    # Show confirmation
    await call.message.edit_text(
        f"✅ <b>Timezone Updated!</b>\n\n"
        f"New timezone: <b>{timezone_str}</b>\n"
        f"Current time: <b>{new_time.strftime('%Y-%m-%d %H:%M:%S %Z')}</b>\n\n"
        f"All logging timestamps will now use this timezone.\n"
        f"Changes applied immediately (hot reload).",
        reply_markup=settings_management_keyboard(),
        parse_mode='HTML'
    )

    await state.clear()


@router.callback_query(F.data == "tz_manual", HasPermissionFilter(Permission.SETTINGS_MANAGE))
async def set_timezone_manual(call: CallbackQuery, state: FSMContext):
    """
    Start manual timezone input.
    """
    current_tz = timezone.get_timezone()

    await call.message.edit_text(
        f"🌍 <b>Enter Timezone Manually</b>\n\n"
        f"Current timezone: <b>{current_tz}</b>\n\n"
        f"Enter timezone in IANA format:\n"
        f"• Example: <code>UTC</code>\n"
        f"• Example: <code>Europe/Moscow</code>\n"
        f"• Example: <code>America/New_York</code>\n"
        f"• Example: <code>Asia/Tokyo</code>\n\n"
        f"📋 Full list: <a href='https://en.wikipedia.org/wiki/List_of_tz_database_time_zones'>Wikipedia</a>\n\n"
        f"<i>Timezone must be valid according to the IANA time zone database.</i>",
        reply_markup=back("settings_management"),
        parse_mode='HTML'
    )
    await state.set_state(SettingsFSM.waiting_timezone)


@router.message(SettingsFSM.waiting_timezone, F.text)
async def process_timezone_input(message: Message, state: FSMContext):
    """
    Process and validate manually entered timezone.
    """
    timezone_str = message.text.strip()

    # Validate timezone
    if not timezone.validate_timezone(timezone_str):
        await message.answer(
            f"❌ <b>Invalid Timezone</b>\n\n"
            f"'{timezone_str}' is not a valid IANA timezone.\n\n"
            f"Please use the correct format:\n"
            f"• UTC\n"
            f"• Europe/Moscow\n"
            f"• America/New_York\n"
            f"• Asia/Tokyo\n\n"
            f"Check the full list: "
            f"<a href='https://en.wikipedia.org/wiki/List_of_tz_database_time_zones'>Wikipedia</a>",
            reply_markup=back("settings_management"),
            parse_mode='HTML'
        )
        return

    # Update database
    with Database().session() as session:
        setting = session.query(BotSettings).filter_by(
            setting_key='timezone'
        ).first()

        if setting:
            setting.setting_value = timezone_str
        else:
            setting = BotSettings(
                setting_key='timezone',
                setting_value=timezone_str
            )
            session.add(setting)

        session.commit()

    # Hot reload timezone
    timezone.reload_timezone()
    new_time = timezone.get_localized_time()

    # Show confirmation
    await message.answer(
        f"✅ <b>Timezone Updated!</b>\n\n"
        f"New timezone: <b>{timezone_str}</b>\n"
        f"Current time: <b>{new_time.strftime('%Y-%m-%d %H:%M:%S %Z')}</b>\n\n"
        f"All logging timestamps will now use this timezone.\n"
        f"Changes applied immediately (hot reload).",
        reply_markup=settings_management_keyboard(),
        parse_mode='HTML'
    )

    await state.clear()


# ---------------------------------------------------------------------------
# PromptPay Recipient Account Settings
# ---------------------------------------------------------------------------

def get_promptpay_id() -> str:
    """Get PromptPay ID from DB, falling back to env var."""
    return get_bot_setting('promptpay_id') or EnvKeys.PROMPTPAY_ID or ""


def get_promptpay_name() -> str:
    """Get PromptPay account name from DB, falling back to env var."""
    return get_bot_setting('promptpay_account_name') or EnvKeys.PROMPTPAY_ACCOUNT_NAME or ""


@router.callback_query(F.data == "setting_promptpay", HasPermissionFilter(Permission.SETTINGS_MANAGE))
async def set_promptpay_start(call: CallbackQuery, state: FSMContext):
    """Show current PromptPay recipient account and offer setup options."""
    current_id = get_promptpay_id()
    current_name = get_promptpay_name()

    id_display = f"<code>{current_id}</code>" if current_id else "<i>Not configured</i>"
    name_display = f"<b>{current_name}</b>" if current_name else "<i>Not set</i>"

    await call.message.edit_text(
        f"💳 <b>PromptPay Recipient Account</b>\n\n"
        f"This is the account that receives all PromptPay payments.\n"
        f"The QR code shown to customers will direct payment here.\n\n"
        f"<b>Current Configuration:</b>\n"
        f"• PromptPay ID: {id_display}\n"
        f"• Account Name: {name_display}\n\n"
        f"Choose how to set up your account:",
        reply_markup=_promptpay_setup_keyboard(),
        parse_mode='HTML'
    )


def _promptpay_setup_keyboard():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="📷 Upload QR Code Image", callback_data="promptpay_upload_qr")
    kb.button(text="✍️ Enter ID Manually", callback_data="promptpay_manual_id")
    kb.button(text=localize("btn.back"), callback_data="settings_management")
    kb.adjust(1)
    return kb.as_markup()


# --- Option 1: Upload QR code image ---

@router.callback_query(F.data == "promptpay_upload_qr", HasPermissionFilter(Permission.SETTINGS_MANAGE))
async def promptpay_upload_qr_start(call: CallbackQuery, state: FSMContext):
    """Ask admin to upload their PromptPay QR code image."""
    await call.message.edit_text(
        "📷 <b>Upload PromptPay QR Code</b>\n\n"
        "Send a photo or screenshot of your PromptPay QR code.\n\n"
        "This can be:\n"
        "• A screenshot from your banking app (KBank, SCB, etc.)\n"
        "• A photo of your printed PromptPay QR\n"
        "• A QR image saved on your phone\n\n"
        "<i>The bot will automatically extract your PromptPay ID from the QR code.</i>",
        reply_markup=back("setting_promptpay"),
        parse_mode='HTML'
    )
    await state.set_state(SettingsFSM.waiting_promptpay_id)
    await state.update_data(promptpay_input_mode="qr_upload")


@router.message(SettingsFSM.waiting_promptpay_id, F.photo)
async def process_promptpay_qr_photo(message: Message, state: FSMContext):
    """Decode uploaded QR image and extract PromptPay ID."""
    data = await state.get_data()
    if data.get("promptpay_input_mode") != "qr_upload":
        # Photo received but we're in manual mode — ignore
        await message.answer(
            "❌ Please enter your PromptPay ID as text, not a photo.\n"
            "Or go back and choose 'Upload QR Code Image' instead.",
            reply_markup=back("setting_promptpay"),
            parse_mode='HTML'
        )
        return

    try:
        from bot.payments.promptpay import extract_promptpay_from_image

        # Download photo from Telegram
        photo_file_id = message.photo[-1].file_id
        file_obj = await message.bot.get_file(photo_file_id)
        photo_io = await message.bot.download_file(file_obj.file_path)
        image_bytes = photo_io.read()

        # Extract PromptPay info
        info = extract_promptpay_from_image(image_bytes)

        id_type_display = "phone number" if info.id_type == "phone" else "national ID"
        amount_display = f"\nDefault Amount: <b>{info.amount} THB</b>" if info.amount else ""

        await state.update_data(
            new_promptpay_id=info.promptpay_id,
            promptpay_id_type=id_type_display,
        )

        current_name = get_promptpay_name()
        name_hint = f"\nCurrent name: <b>{current_name}</b>" if current_name else ""

        await message.answer(
            f"✅ <b>QR Code Decoded Successfully!</b>\n\n"
            f"<b>Extracted Info:</b>\n"
            f"• PromptPay ID: <code>{info.promptpay_id}</code> ({id_type_display}){amount_display}\n"
            f"• Country: {info.country_code or 'TH'}\n\n"
            f"<b>Now enter the account holder name:</b>{name_hint}\n\n"
            f"Enter the name exactly as it appears on your bank account.\n"
            f"This is used to verify customer payments go to the right recipient.\n\n"
            f"• Example: <code>Somchai Jaidee</code>\n"
            f"• Example: <code>My Restaurant Co Ltd</code>",
            reply_markup=back("settings_management"),
            parse_mode='HTML'
        )
        await state.set_state(SettingsFSM.waiting_promptpay_name)

    except ImportError:
        await message.answer(
            "❌ <b>QR decoding not available</b>\n\n"
            "The <code>pyzbar</code> library is not installed.\n"
            "Install it with: <code>pip install pyzbar</code>\n\n"
            "You can still enter your PromptPay ID manually.",
            reply_markup=_promptpay_setup_keyboard(),
            parse_mode='HTML'
        )
        await state.clear()

    except ValueError as e:
        await message.answer(
            f"❌ <b>Could not read QR code</b>\n\n"
            f"{e}\n\n"
            f"Please try again with a clearer image, or enter your ID manually.",
            reply_markup=_promptpay_setup_keyboard(),
            parse_mode='HTML'
        )
        await state.clear()

    except Exception as e:
        logger.error("QR decode error: %s", e)
        await message.answer(
            "❌ <b>Error processing image</b>\n\n"
            "Could not extract PromptPay info from the image.\n"
            "Please try a different image or enter your ID manually.",
            reply_markup=_promptpay_setup_keyboard(),
            parse_mode='HTML'
        )
        await state.clear()


# --- Option 2: Manual entry ---

@router.callback_query(F.data == "promptpay_manual_id", HasPermissionFilter(Permission.SETTINGS_MANAGE))
async def promptpay_manual_start(call: CallbackQuery, state: FSMContext):
    """Start manual PromptPay ID entry."""
    await call.message.edit_text(
        "✍️ <b>Enter PromptPay ID</b>\n\n"
        "Enter your PromptPay ID:\n"
        "• Phone number (10 digits): <code>0812345678</code>\n"
        "• National ID (13 digits): <code>1234567890123</code>\n\n"
        "<i>This is the phone number or national ID registered with PromptPay at your bank.</i>",
        reply_markup=back("setting_promptpay"),
        parse_mode='HTML'
    )
    await state.set_state(SettingsFSM.waiting_promptpay_id)
    await state.update_data(promptpay_input_mode="manual")


@router.message(SettingsFSM.waiting_promptpay_id, F.text)
async def process_promptpay_id(message: Message, state: FSMContext):
    """Validate and save PromptPay ID, then ask for account name."""
    raw_id = message.text.strip().replace("-", "").replace(" ", "")

    # Validate: must be 10-digit phone or 13-digit national ID
    if len(raw_id) == 10 and raw_id.isdigit() and raw_id.startswith("0"):
        id_type = "phone number"
    elif len(raw_id) == 13 and raw_id.isdigit():
        id_type = "national ID"
    else:
        await message.answer(
            "❌ <b>Invalid PromptPay ID</b>\n\n"
            "Must be one of:\n"
            "• 10-digit phone number starting with 0 (e.g. <code>0812345678</code>)\n"
            "• 13-digit national ID (e.g. <code>1234567890123</code>)\n\n"
            "Please try again:",
            reply_markup=back("settings_management"),
            parse_mode='HTML'
        )
        return

    # Save ID to state, ask for account name next
    await state.update_data(new_promptpay_id=raw_id, promptpay_id_type=id_type)

    current_name = get_promptpay_name()
    name_hint = f"\nCurrent name: <b>{current_name}</b>" if current_name else ""

    await message.answer(
        f"✅ PromptPay ID: <code>{raw_id}</code> ({id_type})\n\n"
        f"<b>Now enter the account holder name:</b>{name_hint}\n\n"
        f"This name is used to verify that customer payments reach the correct recipient.\n"
        f"Enter the name exactly as it appears on your bank account.\n\n"
        f"• Example: <code>Somchai Jaidee</code>\n"
        f"• Example: <code>My Restaurant Co Ltd</code>",
        reply_markup=back("settings_management"),
        parse_mode='HTML'
    )
    await state.set_state(SettingsFSM.waiting_promptpay_name)


@router.message(SettingsFSM.waiting_promptpay_name, F.text)
async def process_promptpay_name(message: Message, state: FSMContext):
    """Save PromptPay account name and finalize."""
    account_name = message.text.strip()

    if len(account_name) < 2 or len(account_name) > 200:
        await message.answer(
            "❌ <b>Invalid name</b>\n\n"
            "Account name must be between 2 and 200 characters.\n"
            "Please try again:",
            reply_markup=back("settings_management"),
            parse_mode='HTML'
        )
        return

    data = await state.get_data()
    promptpay_id = data.get('new_promptpay_id', '')
    id_type = data.get('promptpay_id_type', '')

    # Save both settings to database
    with Database().session() as session:
        for key, value in [('promptpay_id', promptpay_id), ('promptpay_account_name', account_name)]:
            setting = session.query(BotSettings).filter_by(setting_key=key).first()
            if setting:
                setting.setting_value = value
            else:
                setting = BotSettings(setting_key=key, setting_value=value)
                session.add(setting)
        session.commit()

    await message.answer(
        f"✅ <b>PromptPay Account Updated!</b>\n\n"
        f"<b>PromptPay ID:</b> <code>{promptpay_id}</code> ({id_type})\n"
        f"<b>Account Name:</b> {account_name}\n\n"
        f"All new orders will generate QR codes directing payment to this account.\n"
        f"Slip verification will check that payments match this recipient.",
        reply_markup=settings_management_keyboard(),
        parse_mode='HTML'
    )
    await state.clear()


# === Currency Selection ===

SUPPORTED_CURRENCIES = [
    ("🇹🇭 THB (Thai Baht)", "THB"),
    ("🇺🇸 USD (US Dollar)", "USD"),
    ("🇪🇺 EUR (Euro)", "EUR"),
    ("🇬🇧 GBP (British Pound)", "GBP"),
    ("🇯🇵 JPY (Japanese Yen)", "JPY"),
    ("🇷🇺 RUB (Russian Ruble)", "RUB"),
    ("🇦🇪 AED (UAE Dirham)", "AED"),
    ("🇸🇦 SAR (Saudi Riyal)", "SAR"),
    ("🇮🇷 IRR (Iranian Rial)", "IRR"),
    ("🇦🇫 AFN (Afghan Afghani)", "AFN"),
    ("🇲🇾 MYR (Malaysian Ringgit)", "MYR"),
    ("🇸🇬 SGD (Singapore Dollar)", "SGD"),
    ("₿ BTC (Bitcoin)", "BTC"),
]


@router.callback_query(F.data == "setting_currency", HasPermissionFilter(Permission.SETTINGS_MANAGE))
async def set_currency_start(call: CallbackQuery, state: FSMContext):
    """Show currency selection menu."""
    from bot.keyboards.inline import simple_buttons
    current = get_bot_setting('pay_currency') or EnvKeys.PAY_CURRENCY

    buttons = [(label, f"currency_select_{code}") for label, code in SUPPORTED_CURRENCIES]
    buttons.append((localize("btn.back"), "settings_management"))

    await call.message.edit_text(
        f"💱 <b>Currency Selection</b>\n\n"
        f"Current: <b>{current}</b>\n\n"
        f"Select currency:",
        reply_markup=simple_buttons(buttons, per_row=2),
    )


@router.callback_query(F.data.startswith("currency_select_"), HasPermissionFilter(Permission.SETTINGS_MANAGE))
async def set_currency_confirm(call: CallbackQuery, state: FSMContext):
    """Save selected currency."""
    currency_code = call.data.replace("currency_select_", "")

    with Database().session() as session:
        setting = session.query(BotSettings).filter_by(setting_key='pay_currency').first()
        if setting:
            setting.setting_value = currency_code
        else:
            session.add(BotSettings(setting_key='pay_currency', setting_value=currency_code))
        session.commit()

    await call.answer(f"Currency set to {currency_code}", show_alert=True)
    await settings_menu(call, state)
