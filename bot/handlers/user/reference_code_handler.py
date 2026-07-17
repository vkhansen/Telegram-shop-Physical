import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import EnvKeys
from bot.database.methods import create_user, select_max_role_id
from bot.keyboards import back
from bot.monitoring import get_metrics
from bot.referrals.codes import create_reference_code as create_ref_code
from bot.referrals.codes import use_reference_code, validate_reference_code
from bot.referrals.invite_cards import parse_start_payload
from bot.states.user_state import ReferenceCodeStates

router = Router()


async def prompt_reference_code(message: Message, state: FSMContext):
    """
    Prompt user to enter a reference code

    Args:
        message: Message object
        state: FSM context
    """
    await message.answer(
        "🔑 Please enter your reference code to access the shop.\n\n"
        "If you don't have a reference code, please contact the administrator.\n\n"
        "💡 Or scan your invite card QR — it opens this bot with the code already filled.",
        reply_markup=back("cancel_start"),
    )
    await state.set_state(ReferenceCodeStates.waiting_reference_code)


async def try_register_with_reference_code(
    *,
    user_id: int,
    username: str | None,
    code: str,
    locale: str | None = None,
) -> tuple[bool, str]:
    """Validate + create user + mark invite/reference code used.

    Returns (success, error_message). On success error_message is empty.
    """
    code = parse_start_payload(code) if code.startswith("/start") else (code or "").strip().upper()
    if not code:
        return False, "No reference code provided"

    is_valid, error_msg, creator_id = validate_reference_code(code, user_id)
    if not is_valid:
        return False, error_msg

    owner_max_role = select_max_role_id()
    user_role = owner_max_role if str(user_id) == EnvKeys.OWNER_ID else 1
    uname = username or f"user_{user_id}"

    create_user(
        telegram_id=user_id,
        registration_date=datetime.datetime.now(),
        referral_id=creator_id,
        role=user_role,
        locale=locale,
    )

    success, error_msg, referrer_id = use_reference_code(code, user_id, uname)
    if not success:
        return False, error_msg

    metrics = get_metrics()
    if metrics:
        metrics.track_event(
            "referral_code_used",
            user_id,
            {"code": code, "referrer_id": referrer_id, "via": "deep_link_or_typed"},
        )
        metrics.track_conversion("referral_program", "code_used", user_id)

    return True, ""


@router.message(ReferenceCodeStates.waiting_reference_code)
async def process_reference_code(message: Message, state: FSMContext):
    """
    Process entered reference code

    Args:
        message: Message with reference code
        state: FSM context
    """
    code = (message.text or "").strip().upper()
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    data = await state.get_data()
    locale = data.get("selected_locale")

    success, error_msg = await try_register_with_reference_code(
        user_id=user_id,
        username=username,
        code=code,
        locale=locale,
    )

    if not success:
        await message.answer(
            f"❌ {error_msg}\n\nPlease try again or contact the administrator.",
            reply_markup=back("cancel_start"),
        )
        return

    await state.clear()

    from bot.handlers.user.main import show_main_menu

    await message.answer("✅ Welcome! Your reference code has been validated.\nYou now have access to the shop.")
    await show_main_menu(message, state)


@router.callback_query(F.data == "cancel_start")
async def cancel_start(call: CallbackQuery, state: FSMContext):
    """
    Cancel the start/registration process

    Args:
        call: Callback query
        state: FSM context
    """
    await state.clear()
    await call.message.edit_text("Registration cancelled. Send /start to try again.")


@router.callback_query(F.data == "my_refcodes")
async def show_my_refcodes(call: CallbackQuery, state: FSMContext):
    """
    Show user's generated reference codes

    Args:
        call: Callback query
        state: FSM context
    """
    from bot.referrals.codes import get_user_reference_codes

    user_id = call.from_user.id
    codes = get_user_reference_codes(user_id, include_inactive=False)

    if not codes:
        await call.message.edit_text(
            "You haven't created any reference codes yet.\n\n"
            "Users can create reference codes that are valid for 24 hours and can be used by 1 person.",
            reply_markup=back("referral_system"),
        )
        return

    text = "📋 Your Reference Codes:\n\n"

    for code_data in codes:
        code_type = "Admin" if code_data["is_admin_code"] else "User"
        status = "✅ Active" if code_data["is_active"] else "❌ Inactive"
        max_uses = code_data["max_uses"] if code_data["max_uses"] else "Unlimited"
        expires = code_data["expires_at"].strftime("%Y-%m-%d %H:%M") if code_data["expires_at"] else "Never"

        text += f"🔑 <code>{code_data['code']}</code>\n"
        text += f"   Type: {code_type}\n"
        text += f"   Uses: {code_data['current_uses']}/{max_uses}\n"
        text += f"   Expires: {expires}\n"
        text += f"   Status: {status}\n\n"

    await call.message.edit_text(text, reply_markup=back("referral_system"), parse_mode="HTML")
    await state.clear()


@router.callback_query(F.data == "create_my_refcode")
async def create_user_refcode(call: CallbackQuery, state: FSMContext):
    """
    Create a new user reference code (24h, 1 use)
    Users can only have ONE active code at a time

    Args:
        call: Callback query
        state: FSM context
    """
    user_id = call.from_user.id
    username = call.from_user.username or f"user_{user_id}"

    try:
        # Check if user already has an active code
        from bot.referrals.codes import get_user_reference_codes

        active_codes = get_user_reference_codes(user_id, include_inactive=False)

        # Filter to only user-created codes (not admin codes)
        active_user_codes = [c for c in active_codes if not c["is_admin_code"]]

        if active_user_codes:
            # User already has an active code - show it
            existing_code = active_user_codes[0]
            expires_str = (
                existing_code["expires_at"].strftime("%Y-%m-%d %H:%M") if existing_code["expires_at"] else "Never"
            )

            await call.message.edit_text(
                f"ℹ️ You already have an active reference code:\n\n"
                f"🔑 Code: <code>{existing_code['code']}</code>\n\n"
                f"⏰ Expires: {expires_str}\n"
                f"👤 Uses: {existing_code['current_uses']}/{existing_code['max_uses'] or '∞'}\n\n"
                f"💡 You can only have one active code at a time.\n"
                f"Wait for it to expire or be used before creating a new one.",
                reply_markup=back("referral_system"),
                parse_mode="HTML",
            )
            return

        code = create_ref_code(
            created_by=user_id,
            created_by_username=username,
            is_admin_code=False,  # This will auto-set 24h expiry and 1 use max
        )

        # Track referral code creation
        metrics = get_metrics()
        if metrics:
            metrics.track_event("referral_code_created", user_id, {"code": code, "is_admin": False})
            metrics.track_conversion("referral_program", "code_created", user_id)

        await call.message.edit_text(
            f"✅ Your reference code has been created!\n\n"
            f"🔑 Code: <code>{code}</code>\n\n"
            f"⏰ Valid for: 24 hours\n"
            f"👤 Can be used by: 1 person\n\n"
            f"Share this code with someone to invite them to the shop!",
            reply_markup=back("referral_system"),
            parse_mode="HTML",
        )
    except Exception as e:
        await call.message.edit_text(f"❌ Error creating reference code: {e!s}", reply_markup=back("referral_system"))

    await state.clear()
