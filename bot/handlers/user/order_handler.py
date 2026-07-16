import contextlib
import html
import re
from datetime import UTC
from decimal import Decimal
from urllib.parse import quote_plus

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from bot.config import EnvKeys
from bot.database import Database
from bot.database.models.main import CustomerInfo, Order
from bot.export import sync_customer_to_csv
from bot.i18n import localize
from bot.keyboards import back, simple_buttons
from bot.logger_mesh import logger
from bot.monitoring.metrics import get_metrics
from bot.services import cart as cart_svc
from bot.states import OrderStates
from bot.states.payment_state import PromptPayStates
from bot.utils import get_telegram_username
from bot.utils.constants import (
    DELIVERY_DEAD_DROP,
    DELIVERY_DOOR,
    DELIVERY_PICKUP,
    PAYMENT_BITCOIN,
    PAYMENT_CASH,
    PAYMENT_LITECOIN,
    PAYMENT_PROMPTPAY,
    PAYMENT_SOLANA,
    PAYMENT_USDT_SOL,
)
from bot.utils.message_utils import send_or_edit
from bot.utils.tracking import track_payment
from bot.utils.validators import validate_and_normalize_phone

router = Router()


# ---------------------------------------------------------------------------
# Helper: extract lat/lng from Google Maps URLs
# ---------------------------------------------------------------------------
_MAPS_COORD_PATTERNS = [
    re.compile(r"@(-?\d+\.\d+),(-?\d+\.\d+)"),  # maps/@lat,lng
    re.compile(r"q=(-?\d+\.\d+),(-?\d+\.\d+)"),  # maps?q=lat,lng
    re.compile(r"ll=(-?\d+\.\d+),(-?\d+\.\d+)"),  # ll=lat,lng
    re.compile(r"/(-?\d+\.\d+),(-?\d+\.\d+)"),  # generic /lat,lng in path
]


def _extract_coords_from_url(url: str):
    """Return (lat, lng) floats or None if no coords found."""
    for pat in _MAPS_COORD_PATTERNS:
        m = pat.search(url)
        if m:
            lat, lng = float(m.group(1)), float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return lat, lng
    return None


async def show_location_method_choice(target, state: FSMContext, *, edit: bool = False):
    """Show the 4-option location method picker."""
    text = localize("order.delivery.location_method_prompt")
    kb = simple_buttons(
        [
            (localize("btn.location_method.gps"), "loc_method_gps"),
            (localize("btn.location_method.live_gps"), "loc_method_live_gps"),
            (localize("btn.location_method.google_link"), "loc_method_google_link"),
            (localize("btn.location_method.type_address"), "loc_method_type_address"),
        ],
        per_row=1,
    )
    await send_or_edit(target, text, reply_markup=kb, edit=edit)
    await state.set_state(OrderStates.waiting_location_method)


# ---------------------------------------------------------------------------
# Step 1: Location method choice
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "loc_method_gps", OrderStates.waiting_location_method)
async def loc_method_gps(call: CallbackQuery, state: FSMContext):
    """User chose GPS via Telegram"""
    await call.answer()
    location_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=localize("btn.share_location"), request_location=True)],
            [KeyboardButton(text=localize("btn.back"))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    # LOGIC-21 fix: Don't send duplicate text — just delete old inline message
    with contextlib.suppress(Exception):
        await call.message.delete()
    await call.message.answer(localize("order.delivery.gps_prompt"), reply_markup=location_kb)
    await state.set_state(OrderStates.waiting_location)


@router.callback_query(F.data == "loc_method_live_gps", OrderStates.waiting_location_method)
async def loc_method_live_gps(call: CallbackQuery, state: FSMContext):
    """User chose to share live location"""
    await call.answer()
    await call.message.edit_text(localize("order.delivery.live_gps_prompt"), reply_markup=back("view_cart"))
    await state.set_state(OrderStates.waiting_live_location)


@router.callback_query(F.data == "loc_method_google_link", OrderStates.waiting_location_method)
async def loc_method_google_link(call: CallbackQuery, state: FSMContext):
    """User chose to paste a Google Maps link"""
    await call.answer()
    await call.message.edit_text(localize("order.delivery.google_link_prompt"), reply_markup=back("view_cart"))
    await state.set_state(OrderStates.waiting_google_maps_link)


@router.callback_query(F.data == "loc_method_type_address", OrderStates.waiting_location_method)
async def loc_method_type_address(call: CallbackQuery, state: FSMContext):
    """User chose to type an address"""
    await call.answer()
    await call.message.edit_text(localize("order.delivery.address_prompt"), reply_markup=back("view_cart"))
    await state.set_state(OrderStates.waiting_delivery_address)


# ---------------------------------------------------------------------------
# Option 1: GPS via Telegram
# ---------------------------------------------------------------------------


@router.message(OrderStates.waiting_location, F.location)
async def process_location(message: Message, state: FSMContext):
    """Process shared GPS location"""
    lat = message.location.latitude
    lng = message.location.longitude
    maps_link = f"https://www.google.com/maps?q={lat},{lng}"

    await state.update_data(
        latitude=lat,
        longitude=lng,
        google_maps_link=maps_link,
        delivery_address=maps_link,
    )

    await message.answer(localize("order.delivery.location_saved"), reply_markup=ReplyKeyboardRemove())

    # Proceed to delivery type
    await ask_delivery_type(message, state)


@router.message(OrderStates.waiting_location)
async def location_not_shared(message: Message, state: FSMContext):
    """User sent text instead of location — nudge them or go back"""
    if message.text and message.text.strip() == localize("btn.back"):
        await message.answer(localize("order.delivery.location_method_prompt"), reply_markup=ReplyKeyboardRemove())
        await show_location_method_choice(message, state)
        return

    await message.answer(
        localize("order.delivery.gps_hint"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=localize("btn.share_location"), request_location=True)],
                [KeyboardButton(text=localize("btn.back"))],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


# ---------------------------------------------------------------------------
# Option 1b: Live Location via Telegram
# ---------------------------------------------------------------------------


@router.message(OrderStates.waiting_live_location, F.location)
async def process_live_location(message: Message, state: FSMContext):
    """Process shared live location"""
    lat = message.location.latitude
    lng = message.location.longitude
    maps_link = f"https://www.google.com/maps?q={lat},{lng}"
    is_live = bool(message.location.live_period)

    await state.update_data(
        latitude=lat,
        longitude=lng,
        google_maps_link=maps_link,
        delivery_address=maps_link,
        live_location_message_id=message.message_id if is_live else None,
        live_location_shared=is_live,
    )

    if is_live:
        await message.answer(localize("order.delivery.live_gps_saved"))
    else:
        # User sent a static location instead — still accept it
        await message.answer(localize("order.delivery.location_saved"))

    await ask_delivery_type(message, state)


@router.message(OrderStates.waiting_live_location)
async def live_location_not_shared(message: Message, state: FSMContext):
    """User sent text instead of live location — remind them"""
    await message.answer(localize("order.delivery.live_gps_hint"), reply_markup=back("view_cart"))


# ---------------------------------------------------------------------------
# Option 2: Google Maps link
# ---------------------------------------------------------------------------


@router.message(OrderStates.waiting_google_maps_link)
async def process_google_maps_link(message: Message, state: FSMContext):
    """Parse coordinates from a Google Maps link"""
    text = (message.text or "").strip()

    # Basic URL validation
    if not text or not any(
        domain in text.lower() for domain in ["google.com/maps", "maps.google", "goo.gl/maps", "maps.app.goo.gl"]
    ):
        await message.answer(localize("order.delivery.google_link_invalid"), reply_markup=back("view_cart"))
        return

    coords = _extract_coords_from_url(text)
    if coords:
        lat, lng = coords
        maps_link = f"https://www.google.com/maps?q={lat},{lng}"
        await state.update_data(
            latitude=lat,
            longitude=lng,
            google_maps_link=maps_link,
            delivery_address=maps_link,
        )
        await message.answer(localize("order.delivery.location_saved"))
        await ask_delivery_type(message, state)
    else:
        # Could not extract coords — save the link as-is and ask user to confirm
        await state.update_data(
            google_maps_link=text,
            delivery_address=text,
        )
        await message.answer(localize("order.delivery.location_saved"))
        await ask_delivery_type(message, state)


# ---------------------------------------------------------------------------
# Option 3: Type an address → search & confirm
# ---------------------------------------------------------------------------


@router.message(OrderStates.waiting_delivery_address)
async def process_delivery_address(message: Message, state: FSMContext):
    """Collect delivery address from user, then ask to confirm via map link"""
    delivery_address = (message.text or "").strip()

    if len(delivery_address) < 5:
        await message.answer(localize("order.delivery.address_invalid"), reply_markup=back("view_cart"))
        return

    # Save to state
    await state.update_data(delivery_address=delivery_address)

    # Generate Google Maps search link for the address
    search_url = f"https://www.google.com/maps/search/{quote_plus(delivery_address)}"
    await state.update_data(google_maps_link=search_url)

    # Ask user to confirm the address
    await message.answer(
        localize("order.delivery.address_confirm_prompt", address=html.escape(delivery_address), maps_link=search_url),
        reply_markup=simple_buttons(
            [
                (localize("btn.address_confirm_yes"), "address_confirm_yes"),
                (localize("btn.address_confirm_retry"), "address_confirm_retry"),
            ],
            per_row=1,
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    await state.set_state(OrderStates.waiting_address_confirm)


@router.callback_query(F.data == "address_confirm_yes", OrderStates.waiting_address_confirm)
async def address_confirmed(call: CallbackQuery, state: FSMContext):
    """User confirmed the searched address"""
    await call.answer()
    await call.message.edit_text(localize("order.delivery.location_saved"))
    await ask_delivery_type(call.message, state, edit=True)


@router.callback_query(F.data == "address_confirm_retry", OrderStates.waiting_address_confirm)
async def address_retry(call: CallbackQuery, state: FSMContext):
    """User wants to re-enter address"""
    await call.answer()
    await show_location_method_choice(call.message, state, edit=True)


async def ask_delivery_type(message: Message, state: FSMContext, *, edit: bool = False):
    """Show delivery type selection (Card 3)"""
    text = localize("order.delivery.type_prompt")
    kb = simple_buttons(
        [
            (localize("btn.delivery.door"), "delivery_type_door"),
            (localize("btn.delivery.dead_drop"), "delivery_type_dead_drop"),
            (localize("btn.delivery.pickup"), "delivery_type_pickup"),
        ],
        per_row=1,
    )
    await send_or_edit(message, text, reply_markup=kb, edit=edit)
    await state.set_state(OrderStates.waiting_delivery_type)


@router.callback_query(F.data == "delivery_type_door", OrderStates.waiting_delivery_type)
async def delivery_type_door(call: CallbackQuery, state: FSMContext):
    """User selected door delivery"""
    await call.answer()
    await state.update_data(delivery_type=DELIVERY_DOOR)
    await call.message.edit_text(localize("order.delivery.phone_prompt"), reply_markup=back("view_cart"))
    await state.set_state(OrderStates.waiting_phone_number)


@router.callback_query(F.data == "delivery_type_dead_drop", OrderStates.waiting_delivery_type)
async def delivery_type_dead_drop(call: CallbackQuery, state: FSMContext):
    """User selected dead drop — collect instructions"""
    await call.answer()
    await state.update_data(delivery_type=DELIVERY_DEAD_DROP)
    await call.message.edit_text(
        localize("order.delivery.drop_instructions_prompt"),
    )
    await state.set_state(OrderStates.waiting_drop_instructions)


@router.callback_query(F.data == "delivery_type_pickup", OrderStates.waiting_delivery_type)
async def delivery_type_pickup(call: CallbackQuery, state: FSMContext):
    """User selected self-pickup — skip address/location details"""
    await call.answer()
    await state.update_data(delivery_type=DELIVERY_PICKUP)
    await call.message.edit_text(localize("order.delivery.phone_prompt"), reply_markup=back("view_cart"))
    await state.set_state(OrderStates.waiting_phone_number)


@router.message(OrderStates.waiting_drop_instructions)
async def process_drop_instructions(message: Message, state: FSMContext):
    """Collect dead drop instructions text, then ask for GPS location"""
    instructions = message.text.strip()
    await state.update_data(drop_instructions=instructions)

    # Ask for GPS location of the dead drop
    await message.answer(
        localize("order.delivery.drop_gps_prompt"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=localize("btn.share_drop_location"), request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    await state.set_state(OrderStates.waiting_drop_gps)


@router.message(OrderStates.waiting_drop_gps, F.location)
async def process_drop_gps(message: Message, state: FSMContext):
    """Save GPS coordinates for the dead drop location"""
    await state.update_data(
        drop_latitude=message.location.latitude,
        drop_longitude=message.location.longitude,
    )
    await message.answer(
        localize("order.delivery.drop_gps_saved"),
        reply_markup=ReplyKeyboardRemove(),
    )

    # Now ask for photos/videos of the drop location
    await state.update_data(drop_media=[])
    await message.answer(
        localize("order.delivery.drop_media_prompt"),
        reply_markup=simple_buttons([(localize("btn.skip_drop_media"), "skip_drop_media")], per_row=1),
    )
    await state.set_state(OrderStates.waiting_drop_media)


async def _accumulate_drop_media(message: Message, state: FSMContext, file_id: str, media_type: str):
    """Shared helper: accumulate a media file for the dead drop location."""
    data = await state.get_data()
    media_list = data.get("drop_media", [])
    media_list.append({"file_id": file_id, "type": media_type})
    await state.update_data(drop_media=media_list)

    await message.answer(
        localize("order.delivery.drop_media_saved", count=len(media_list)),
        reply_markup=simple_buttons(
            [
                (localize("btn.drop_media_done"), "done_drop_media"),
                (localize("btn.skip_drop_media"), "skip_drop_media"),
            ],
            per_row=1,
        ),
    )


@router.message(OrderStates.waiting_drop_media, F.photo)
async def process_drop_media_photo(message: Message, state: FSMContext):
    """Accumulate a photo for the dead drop location"""
    await _accumulate_drop_media(message, state, message.photo[-1].file_id, "photo")


@router.message(OrderStates.waiting_drop_media, F.video)
async def process_drop_media_video(message: Message, state: FSMContext):
    """Accumulate a video for the dead drop location"""
    await _accumulate_drop_media(message, state, message.video.file_id, "video")


@router.callback_query(F.data == "done_drop_media", OrderStates.waiting_drop_media)
async def done_drop_media(call: CallbackQuery, state: FSMContext):
    """User finished uploading drop media — proceed to phone number"""
    await call.answer()
    await call.message.edit_text(localize("order.delivery.phone_prompt"), reply_markup=back("view_cart"))
    await state.set_state(OrderStates.waiting_phone_number)


@router.callback_query(F.data == "skip_drop_media", OrderStates.waiting_drop_media)
async def skip_drop_media(call: CallbackQuery, state: FSMContext):
    """User skipped drop location media"""
    await call.answer()
    await call.message.edit_text(localize("order.delivery.phone_prompt"), reply_markup=back("view_cart"))
    await state.set_state(OrderStates.waiting_phone_number)


# --- Legacy single-photo handlers (kept for backward compat) ---


@router.message(OrderStates.waiting_drop_photo, F.photo)
async def process_drop_photo(message: Message, state: FSMContext):
    """Save photo of drop location (legacy single-photo flow)"""
    photo_file_id = message.photo[-1].file_id
    await state.update_data(drop_location_photo=photo_file_id)

    await message.answer(localize("order.delivery.drop_photo_saved"))
    await message.answer(localize("order.delivery.phone_prompt"), reply_markup=back("view_cart"))
    await state.set_state(OrderStates.waiting_phone_number)


@router.callback_query(F.data == "skip_drop_photo", OrderStates.waiting_drop_photo)
async def skip_drop_photo(call: CallbackQuery, state: FSMContext):
    """User skipped drop location photo (legacy flow)"""
    await call.answer()
    await call.message.edit_text(localize("order.delivery.phone_prompt"), reply_markup=back("view_cart"))
    await state.set_state(OrderStates.waiting_phone_number)


@router.message(OrderStates.waiting_phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    """
    Collect phone number from user
    """
    try:
        phone_number = validate_and_normalize_phone(message.text or "")
    except ValueError:
        await message.answer(localize("order.delivery.phone_invalid"), reply_markup=back("view_cart"))
        return

    # Save normalised E.164 number to state
    await state.update_data(phone_number=phone_number)

    # Ask for delivery note (optional)
    await message.answer(
        localize("order.delivery.note_prompt"),
        reply_markup=simple_buttons(
            [(localize("btn.skip"), "skip_delivery_note"), (localize("btn.back"), "view_cart")], per_row=2
        ),
    )
    await state.set_state(OrderStates.waiting_delivery_note)


@router.message(OrderStates.waiting_delivery_note)
async def process_delivery_note(message: Message, state: FSMContext):
    """
    Collect delivery note from user
    """
    delivery_note = message.text.strip()

    # Save to state
    await state.update_data(delivery_note=delivery_note)

    # Check if user has bonus balance and ask about applying it
    await check_and_ask_about_bonus(message, state, user_id=message.from_user.id)


@router.callback_query(F.data == "skip_delivery_note", OrderStates.waiting_delivery_note)
async def skip_delivery_note_handler(call: CallbackQuery, state: FSMContext):
    """
    User skipped delivery note
    """
    await state.update_data(delivery_note="")

    # Check if user has bonus balance and ask about applying it
    await check_and_ask_about_bonus(call.message, state, user_id=call.from_user.id, from_callback=True)


async def check_and_ask_about_bonus(
    message: Message, state: FSMContext, user_id: int | None = None, from_callback: bool = False
):
    """
    Check if user has referral bonus and ask if they want to apply it to the order
    """
    if user_id is None:
        user_id = message.from_user.id

    # Extract the scalar bonus balance before closing the session — never hold a DB
    # connection open across Telegram/Redis awaits.
    bonus_balance = None
    with Database().session() as session:
        customer_info = session.query(CustomerInfo).filter_by(telegram_id=user_id).first()
        if customer_info and customer_info.bonus_balance and customer_info.bonus_balance > 0:
            bonus_balance = customer_info.bonus_balance
    # Session closed here; all awaits happen outside.

    if bonus_balance is not None:
        total_res = await cart_svc.get_total(user_id)
        total_amount = total_res.data.get("total", 0) if total_res.ok else 0
        await state.update_data(available_bonus=str(bonus_balance))

        text = (
            localize("order.bonus.available", bonus_balance=bonus_balance)
            + localize("order.bonus.order_total_label", amount=total_amount, currency=EnvKeys.PAY_CURRENCY)
            + "\n\n"
            + localize("order.bonus.apply_question")
            + "\n"
            + localize("order.bonus.choose_amount_hint", max_amount=min(bonus_balance, total_amount))
        )

        kb = simple_buttons(
            [(localize("btn.apply_bonus_yes"), "apply_bonus_yes"), (localize("btn.apply_bonus_no"), "apply_bonus_no")],
            per_row=2,
        )
        await send_or_edit(message, text, reply_markup=kb, edit=from_callback)
        return

    # No bonus or zero bonus - proceed to payment
    await state.update_data(bonus_applied=0)
    await finalize_order_and_payment(message, state, user_id=user_id, from_callback=from_callback)


@router.callback_query(F.data == "apply_bonus_yes")
async def apply_bonus_yes_handler(call: CallbackQuery, state: FSMContext):
    """
    User wants to apply bonus - ask for amount
    """
    data = await state.get_data()
    available_bonus = Decimal(str(data.get("available_bonus", 0)))

    total_res = await cart_svc.get_total(call.from_user.id)
    total_amount = total_res.data.get("total", 0) if total_res.ok else 0
    max_applicable = min(available_bonus, Decimal(str(total_amount)))

    await call.message.edit_text(
        localize("order.bonus.enter_amount_title")
        + "\n\n"
        + localize("order.bonus.available_label", amount=available_bonus)
        + "\n"
        + localize("order.bonus.order_total_label", amount=total_amount, currency=EnvKeys.PAY_CURRENCY)
        + "\n"
        + localize("order.bonus.max_applicable_label", amount=max_applicable)
        + "\n\n"
        + localize("order.bonus.enter_amount", max_applicable=max_applicable),
        reply_markup=simple_buttons(
            [
                (localize("btn.use_all_bonus", amount=max_applicable), f"use_all_bonus_{max_applicable}"),
                (localize("btn.cancel"), "apply_bonus_no"),
            ],
            per_row=2,
        ),
    )
    await state.set_state(OrderStates.waiting_bonus_amount)


@router.callback_query(F.data.startswith("use_all_bonus_"))
async def use_all_bonus_handler(call: CallbackQuery, state: FSMContext):
    """
    User wants to use all available bonus
    """
    # Extract amount from callback data
    amount_str = call.data.replace("use_all_bonus_", "")
    bonus_amount = Decimal(amount_str)

    await state.update_data(bonus_applied=str(bonus_amount))
    await finalize_order_and_payment(call.message, state, user_id=call.from_user.id, from_callback=True)


@router.message(OrderStates.waiting_bonus_amount)
async def process_bonus_amount(message: Message, state: FSMContext):
    """
    Process the bonus amount entered by user
    """
    try:
        bonus_amount = Decimal(message.text.strip())

        if bonus_amount <= 0:
            await message.answer(localize("order.bonus.amount_positive_error"))
            return

        data = await state.get_data()
        available_bonus = Decimal(str(data.get("available_bonus", 0)))
        total_res = await cart_svc.get_total(message.from_user.id)
        total_amount = total_res.data.get("total", 0) if total_res.ok else 0
        max_applicable = min(available_bonus, Decimal(str(total_amount)))

        if bonus_amount > max_applicable:
            await message.answer(localize("order.bonus.amount_too_high", max_applicable=max_applicable))
            return

        # Valid amount - save and proceed
        await state.update_data(bonus_applied=str(bonus_amount))
        await finalize_order_and_payment(message, state, user_id=message.from_user.id)

    except (ValueError, TypeError):
        await message.answer(localize("order.bonus.invalid_amount"))


@router.callback_query(F.data == "apply_bonus_no")
async def apply_bonus_no_handler(call: CallbackQuery, state: FSMContext):
    """
    User doesn't want to apply bonus
    """
    await state.update_data(bonus_applied=0)
    await finalize_order_and_payment(call.message, state, user_id=call.from_user.id, from_callback=True)


async def show_payment_method_selection(
    message: Message, state: FSMContext, user_id: int | None = None, from_callback: bool = False
):
    """
    Show payment method selection (Bitcoin or Cash)
    """
    if user_id is None:
        user_id = message.from_user.id

    # Get cart total via application service (CARD-32 / CARD-40-B)
    total_res = await cart_svc.get_total(user_id)
    cart_total = total_res.data.get("total", 0) if total_res.ok else 0
    data = await state.get_data()
    bonus_applied = Decimal(str(data.get("bonus_applied", 0)))
    final_amount = Decimal(str(cart_total)) - bonus_applied

    # Get localized strings
    text = localize("order.payment_method.choose")

    summary_text = localize("order.summary.title") + localize("order.summary.cart_total", cart_total=cart_total) + "\n"

    if bonus_applied > 0:
        summary_text += localize("order.summary.bonus_applied", bonus_applied=bonus_applied) + "\n"
        summary_text += "<b>" + localize("order.summary.final_amount", final_amount=final_amount) + "</b>\n\n"
    else:
        summary_text += (
            localize("order.summary.total_label", amount=final_amount, currency=EnvKeys.PAY_CURRENCY) + "\n\n"
        )

    summary_text += text

    # Payment method buttons
    payment_buttons = [
        (localize("order.payment_method.cash"), "payment_method_cash"),
    ]

    # Add PromptPay if configured (Card 1) — check DB first, then env var
    from bot.handlers.admin.settings_management import get_promptpay_id

    if get_promptpay_id():
        payment_buttons.insert(0, (localize("order.payment_method.promptpay"), "payment_method_promptpay"))

    payment_buttons.append((localize("order.payment_method.bitcoin"), "payment_method_bitcoin"))

    # Add crypto coins if enabled (Card 18)
    if EnvKeys.CRYPTO_PAYMENTS_ENABLED:
        enabled_coins = [c.strip() for c in EnvKeys.CRYPTO_COINS_ENABLED.split(",") if c.strip()]
        from bot.utils.constants import PAYMENT_METHOD_TO_COIN

        coin_to_method = {v: k for k, v in PAYMENT_METHOD_TO_COIN.items()}
        for coin in enabled_coins:
            method = coin_to_method.get(coin)
            if method and method != "bitcoin":  # BTC already added above
                label_key = f"order.payment_method.{method}"
                payment_buttons.append((localize(label_key), f"payment_method_{method}"))

    await send_or_edit(
        message,
        summary_text,
        reply_markup=simple_buttons(payment_buttons, per_row=1),
        edit=from_callback,
    )
    await state.set_state(OrderStates.waiting_payment_method)


# ---------------------------------------------------------------------------
# Payment method handlers — one factory to bind (method_name → processor).
# ---------------------------------------------------------------------------

PAYMENT_PROCESSORS = {
    PAYMENT_BITCOIN: lambda msg, st, uid: process_bitcoin_payment_new_message(msg, st, user_id=uid),
    PAYMENT_CASH: lambda msg, st, uid: process_cash_payment_new_message(msg, st, user_id=uid),
    PAYMENT_PROMPTPAY: lambda msg, st, uid: process_promptpay_payment(msg, st, user_id=uid),
    PAYMENT_LITECOIN: lambda msg, st, uid: process_crypto_payment(msg, st, user_id=uid),
    PAYMENT_SOLANA: lambda msg, st, uid: process_crypto_payment(msg, st, user_id=uid),
    PAYMENT_USDT_SOL: lambda msg, st, uid: process_crypto_payment(msg, st, user_id=uid),
}


async def _handle_payment_method(call: CallbackQuery, state: FSMContext, method: str):
    """Common logic for every payment-method callback."""
    processor = PAYMENT_PROCESSORS.get(method)
    if not processor:
        logger.error("Unknown payment method: %s", method)
        await call.answer(localize("order.payment.error_general"), show_alert=True)
        return
    await call.answer()
    await state.update_data(payment_method=method)
    track_payment(method, call.from_user.id)
    await processor(call.message, state, call.from_user.id)


@router.callback_query(F.data == "payment_method_bitcoin", OrderStates.waiting_payment_method)
async def payment_method_bitcoin_handler(call: CallbackQuery, state: FSMContext):
    await _handle_payment_method(call, state, PAYMENT_BITCOIN)


@router.callback_query(F.data == "payment_method_cash", OrderStates.waiting_payment_method)
async def payment_method_cash_handler(call: CallbackQuery, state: FSMContext):
    await _handle_payment_method(call, state, PAYMENT_CASH)


@router.callback_query(F.data == "payment_method_promptpay", OrderStates.waiting_payment_method)
async def payment_method_promptpay_handler(call: CallbackQuery, state: FSMContext):
    await _handle_payment_method(call, state, PAYMENT_PROMPTPAY)


@router.callback_query(F.data == "payment_method_litecoin", OrderStates.waiting_payment_method)
async def payment_method_litecoin_handler(call: CallbackQuery, state: FSMContext):
    await _handle_payment_method(call, state, PAYMENT_LITECOIN)


@router.callback_query(F.data == "payment_method_solana", OrderStates.waiting_payment_method)
async def payment_method_solana_handler(call: CallbackQuery, state: FSMContext):
    await _handle_payment_method(call, state, PAYMENT_SOLANA)


@router.callback_query(F.data == "payment_method_usdt_sol", OrderStates.waiting_payment_method)
async def payment_method_usdt_sol_handler(call: CallbackQuery, state: FSMContext):
    await _handle_payment_method(call, state, PAYMENT_USDT_SOL)


# ---------------------------------------------------------------------------
# Generic crypto payment processor (Card 18) — LTC, SOL, USDT_SOL via checkout.
# BTC still uses process_bitcoin_payment_new_message (legacy BitcoinAddress pool).
# ---------------------------------------------------------------------------


async def process_crypto_payment(message: Message, state: FSMContext, *, user_id: int | None = None):
    """Generic flow for on-chain-verified crypto payments (LTC, SOL, USDT).

    CARD-32: order create / address / CryptoPayment live in ``bot.services.checkout``;
    this handler is adapter-only (price feed + I/O + FSM).
    """
    from bot.payments.chain_verify import get_verifier
    from bot.services import cart as cart_svc
    from bot.services import checkout as checkout_svc
    from bot.utils.constants import PAYMENT_METHOD_TO_COIN
    from bot.utils.tracking import track_event

    if user_id is None:
        user_id = message.from_user.id
    username = await get_telegram_username(user_id, message.bot)

    data = await state.get_data()
    payment_method = data.get("payment_method")
    coin = PAYMENT_METHOD_TO_COIN.get(payment_method)
    if not coin:
        await message.answer(localize("order.payment.error_general"), reply_markup=back("view_cart"))
        return

    verifier = get_verifier(coin)
    coin_name = verifier.coin_name()

    cart_res = await cart_svc.list_items(user_id)
    cart_items = cart_res.data.get("items") or []
    if not cart_items:
        await message.answer(localize("cart.empty_alert"), reply_markup=back("shop"))
        return

    total_amount = cart_res.data.get("total") or 0
    bonus_applied = Decimal(str(data.get("bonus_applied", 0)))
    final_amount = Decimal(str(total_amount)) - bonus_applied
    dd_type = data.get("delivery_type", DELIVERY_DOOR)
    dd_instructions = data.get("drop_instructions")
    dd_lat = data.get("drop_latitude")
    dd_lng = data.get("drop_longitude")
    dd_media = data.get("drop_media")

    # Network I/O — outside any DB session (CARD-23)
    try:
        from bot.payments.price_feed import get_crypto_amount

        crypto_amount, exchange_rate = await get_crypto_amount(coin, final_amount)
    except Exception as exc:
        logger.error("Price feed error for %s: %s", coin, exc)
        await message.answer(localize("order.payment.error_general"), reply_markup=back("view_cart"))
        return

    timeout_map = {
        "btc": EnvKeys.CRYPTO_PAYMENT_TIMEOUT_BTC,
        "ltc": EnvKeys.CRYPTO_PAYMENT_TIMEOUT_LTC,
        "sol": EnvKeys.CRYPTO_PAYMENT_TIMEOUT_SOL,
        "usdt_sol": EnvKeys.CRYPTO_PAYMENT_TIMEOUT_USDT,
    }
    timeout_minutes = timeout_map.get(coin, 60)

    order_res = checkout_svc.start_crypto_order(
        user_id,
        cart_items,
        payment_method=payment_method,
        total_amount=total_amount,
        bonus_applied=bonus_applied,
        username=username,
        delivery_type=dd_type,
        drop_instructions=dd_instructions,
        drop_latitude=dd_lat,
        drop_longitude=dd_lng,
        drop_media=dd_media,
        brand_id=data.get("current_brand_id"),
        store_id=data.get("current_store_id"),
        crypto_amount=crypto_amount,
        required_confirmations=verifier.required_confirmations(),
        timeout_minutes=timeout_minutes,
        legacy_bitcoin=False,
    )

    if not order_res.ok:
        key = order_res.error_key or "order.payment.error_general"
        if key == "cart.empty":
            await message.answer(localize("cart.empty_alert"), reply_markup=back("shop"))
        elif key == "crypto.payment.no_address":
            await message.answer(
                localize("crypto.payment.no_address", coin=coin_name),
                reply_markup=back("back_to_menu"),
            )
        elif key == "order.payment.customer_not_found":
            await message.answer(localize("order.payment.customer_not_found"), reply_markup=back("view_cart"))
        elif key == "order.bonus.insufficient":
            await message.answer(localize("order.bonus.insufficient"), reply_markup=back("view_cart"))
        elif key == "order.inventory.unable_to_reserve":
            await message.answer(
                localize(
                    "order.inventory.unable_to_reserve",
                    unavailable_items=order_res.error_detail or order_res.data.get("unavailable_items") or "",
                ),
                reply_markup=back("view_cart"),
            )
        else:
            await message.answer(localize("order.payment.error_general"), reply_markup=back("view_cart"))
        return

    order_code = order_res.data["order_code"]
    address = order_res.data.get("receive_address") or order_res.data.get("crypto_address")
    final_amount = Decimal(str(order_res.data.get("final_amount", final_amount)))
    timeout_minutes = order_res.data.get("crypto_timeout_minutes") or timeout_minutes

    track_event(
        "order_created",
        user_id,
        {
            "order_code": order_code,
            "payment_method": payment_method,
            "coin": coin,
            "total": float(total_amount),
            "bonus_applied": float(bonus_applied),
        },
    )

    payment_text = (
        localize("crypto.payment.title", coin_name=coin_name)
        + "\n\n"
        + localize("crypto.payment.order_code", code=order_code)
        + "\n"
        + localize("crypto.payment.total_fiat", amount=final_amount, currency=EnvKeys.PAY_CURRENCY)
        + "\n"
        + localize("crypto.payment.rate", coin=coin.upper(), rate=exchange_rate, currency=EnvKeys.PAY_CURRENCY)
        + "\n"
        + localize("crypto.payment.amount_due", crypto_amount=crypto_amount, coin=coin.upper())
        + "\n\n"
        + localize("crypto.payment.address", address=address)
        + "\n\n"
        + localize("crypto.payment.send_exact")
        + "\n"
        + localize("crypto.payment.one_time")
        + "\n"
        + localize("crypto.payment.auto_confirm")
        + "\n\n"
        + localize("crypto.payment.waiting", timeout=timeout_minutes)
    )

    await message.answer(payment_text, reply_markup=back("back_to_menu"))
    sync_customer_to_csv(user_id, username)
    await state.clear()


async def finalize_order_and_payment(
    message: Message, state: FSMContext, user_id: int | None = None, from_callback: bool = False
):
    """
    Save customer info and proceed to payment method selection
    """
    if user_id is None:
        user_id = message.from_user.id

    # Get real username from Telegram API
    username = await get_telegram_username(user_id, message.bot)

    # Get data from state
    data = await state.get_data()
    delivery_address = data.get("delivery_address")
    phone_number = data.get("phone_number")
    delivery_note = data.get("delivery_note", "")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    data.get("google_maps_link")

    # Save/update customer info
    try:
        with Database().session() as session:
            customer_info = session.query(CustomerInfo).filter_by(telegram_id=user_id).first()

            if customer_info:
                # Log changes
                from bot.export.custom_logging import log_customer_info_change

                if customer_info.delivery_address != delivery_address:
                    log_customer_info_change(
                        user_id, username, "ADDRESS", customer_info.delivery_address, delivery_address
                    )
                    customer_info.delivery_address = delivery_address

                if customer_info.phone_number != phone_number:
                    log_customer_info_change(user_id, username, "PHONE", customer_info.phone_number, phone_number)
                    customer_info.phone_number = phone_number

                if customer_info.delivery_note != delivery_note:
                    log_customer_info_change(
                        user_id, username, "DELIVERY_NOTE", customer_info.delivery_note, delivery_note
                    )
                    customer_info.delivery_note = delivery_note

                # Update GPS coordinates if provided (Card 2)
                if latitude is not None and longitude is not None:
                    customer_info.latitude = latitude
                    customer_info.longitude = longitude

            else:
                # Create new customer info (username stored in users table, not here)
                customer_info = CustomerInfo(
                    telegram_id=user_id,
                    phone_number=phone_number,
                    delivery_address=delivery_address,
                    delivery_note=delivery_note,
                )
                # Set GPS if provided
                if latitude is not None and longitude is not None:
                    customer_info.latitude = latitude
                    customer_info.longitude = longitude
                session.add(customer_info)

            session.commit()

    except Exception as e:
        logger.error(f"Error saving customer info: {e}")
        await message.answer(localize("order.delivery.info_save_error"), reply_markup=back("view_cart"))
        return

    # Show payment method selection
    await show_payment_method_selection(message, state, user_id=user_id, from_callback=from_callback)


async def process_bitcoin_payment(call: CallbackQuery, state: FSMContext):
    """
    Process Bitcoin payment from callback query.

    CARD-32: order create via ``checkout.start_crypto_order`` (legacy BTC pool).
    """
    from bot.services import cart as cart_svc
    from bot.services import checkout as checkout_svc

    user_id = call.from_user.id
    username = await get_telegram_username(user_id, call.bot)

    cart_res = await cart_svc.list_items(user_id)
    cart_items = cart_res.data.get("items") or []
    if not cart_items:
        await call.answer(localize("cart.empty_alert"), show_alert=True)
        return

    total_amount = cart_res.data.get("total") or 0
    fsm_data = await state.get_data()
    dd_type = fsm_data.get("delivery_type", DELIVERY_DOOR)
    dd_instructions = fsm_data.get("drop_instructions")
    dd_lat = fsm_data.get("drop_latitude")
    dd_lng = fsm_data.get("drop_longitude")
    dd_media = fsm_data.get("drop_media")

    order_res = checkout_svc.start_crypto_order(
        user_id,
        cart_items,
        payment_method=PAYMENT_BITCOIN,
        total_amount=total_amount,
        bonus_applied=0,
        username=username,
        delivery_type=dd_type,
        drop_instructions=dd_instructions,
        drop_latitude=dd_lat,
        drop_longitude=dd_lng,
        drop_media=dd_media,
        brand_id=fsm_data.get("current_brand_id"),
        store_id=fsm_data.get("current_store_id"),
        legacy_bitcoin=True,
    )

    if not order_res.ok:
        key = order_res.error_key or "order.payment.error_general"
        if key == "cart.empty":
            await call.answer(localize("cart.empty_alert"), show_alert=True)
        elif key == "order.payment.system_unavailable":
            await call.message.edit_text(
                localize("order.payment.system_unavailable"), reply_markup=back("back_to_menu")
            )
        elif key == "order.payment.customer_not_found":
            await call.answer(localize("order.payment.customer_not_found"), show_alert=True)
        elif key == "order.inventory.unable_to_reserve":
            await call.message.edit_text(
                localize(
                    "order.inventory.unable_to_reserve",
                    unavailable_items=order_res.error_detail or order_res.data.get("unavailable_items") or "",
                ),
                reply_markup=back("view_cart"),
            )
        else:
            await call.message.edit_text(localize("order.payment.creation_error"), reply_markup=back("view_cart"))
        return

    order_code = order_res.data["order_code"]
    items_summary = order_res.data.get("items_summary") or []
    btc_address = order_res.data.get("bitcoin_address") or order_res.data.get("receive_address")
    cust_address = order_res.data.get("delivery_address")
    cust_phone = order_res.data.get("phone_number")
    cust_note = order_res.data.get("delivery_note") or ""
    total_amount = Decimal(str(order_res.data.get("total_amount", total_amount)))

    payment_text = (
        localize("order.payment.bitcoin.title")
        + "\n\n"
        + localize("order.payment.bitcoin.order_code", code=order_code)
        + "\n"
        + localize("order.payment.bitcoin.total_amount", amount=total_amount, currency=EnvKeys.PAY_CURRENCY)
        + "\n\n"
        + localize("order.payment.bitcoin.items_title")
        + "\n"
        + f"{chr(10).join(items_summary)}\n\n"
        + localize("order.payment.bitcoin.delivery_title")
        + "\n"
        f"📍 Address: {cust_address}\n"
        f"📞 Phone: {cust_phone}\n"
    )

    if cust_note:
        payment_text += f"📝 Note: {cust_note}\n"

    payment_text += (
        "\n"
        + localize("order.payment.bitcoin.address_title")
        + "\n"
        + f"<code>{btc_address}</code>\n\n"
        + localize("order.payment.bitcoin.important_title")
        + "\n"
        + localize("order.payment.bitcoin.send_exact")
        + "\n"
        + localize("order.payment.bitcoin.one_time_address")
        + "\n"
        + localize("order.payment.bitcoin.admin_confirm")
        + "\n\n"
        + localize("order.payment.bitcoin.need_help")
    )

    await call.message.edit_text(payment_text, reply_markup=back("back_to_menu"))

    await notify_admin_new_order(
        call.bot,
        order_code,
        user_id,
        username,
        "\n".join(items_summary),
        total_amount,
        btc_address,
        cust_address,
        cust_phone,
        cust_note or "",
    )

    sync_customer_to_csv(user_id, username)
    await state.clear()


async def process_bitcoin_payment_new_message(message: Message, state: FSMContext, user_id: int | None = None):
    """
    Process Bitcoin payment by sending a new message.

    CARD-32: order create via ``checkout.start_crypto_order`` (legacy BTC pool).
    """
    from bot.services import cart as cart_svc
    from bot.services import checkout as checkout_svc

    if user_id is None:
        user_id = message.from_user.id

    username = await get_telegram_username(user_id, message.bot)
    cart_res = await cart_svc.list_items(user_id)
    cart_items = cart_res.data.get("items") or []

    if not cart_items:
        await message.answer(localize("cart.empty_alert"), reply_markup=back("shop"))
        return

    total_amount = cart_res.data.get("total") or 0
    data = await state.get_data()
    bonus_applied = Decimal(str(data.get("bonus_applied", 0)))
    dd_type = data.get("delivery_type", DELIVERY_DOOR)
    dd_instructions = data.get("drop_instructions")
    dd_lat = data.get("drop_latitude")
    dd_lng = data.get("drop_longitude")
    dd_media = data.get("drop_media")

    order_res = checkout_svc.start_crypto_order(
        user_id,
        cart_items,
        payment_method=PAYMENT_BITCOIN,
        total_amount=total_amount,
        bonus_applied=bonus_applied,
        username=username,
        delivery_type=dd_type,
        drop_instructions=dd_instructions,
        drop_latitude=dd_lat,
        drop_longitude=dd_lng,
        drop_media=dd_media,
        brand_id=data.get("current_brand_id"),
        store_id=data.get("current_store_id"),
        legacy_bitcoin=True,
    )

    if not order_res.ok:
        key = order_res.error_key or "order.payment.error_general"
        if key == "cart.empty":
            await message.answer(localize("cart.empty_alert"), reply_markup=back("shop"))
        elif key == "order.payment.system_unavailable":
            await message.answer(localize("order.payment.system_unavailable"), reply_markup=back("back_to_menu"))
        elif key == "order.payment.customer_not_found":
            await message.answer(localize("order.payment.customer_not_found"), reply_markup=back("view_cart"))
        elif key == "order.bonus.insufficient":
            await message.answer(localize("order.bonus.insufficient"), reply_markup=back("view_cart"))
        elif key == "order.inventory.unable_to_reserve":
            await message.answer(
                localize(
                    "order.inventory.unable_to_reserve",
                    unavailable_items=order_res.error_detail or order_res.data.get("unavailable_items") or "",
                ),
                reply_markup=back("view_cart"),
            )
        else:
            await message.answer(localize("order.payment.error_general"), reply_markup=back("view_cart"))
        return

    order_code = order_res.data["order_code"]
    items_summary = order_res.data.get("items_summary") or []
    btc_address = order_res.data.get("bitcoin_address") or order_res.data.get("receive_address")
    final_amount = Decimal(str(order_res.data.get("final_amount", total_amount)))
    total_amount = Decimal(str(order_res.data.get("total_amount", total_amount)))
    cust_address = order_res.data.get("delivery_address")
    cust_phone = order_res.data.get("phone_number")
    cust_note = order_res.data.get("delivery_note") or ""

    metrics = get_metrics()
    if metrics:
        metrics.track_event(
            "order_created",
            user_id,
            {
                "order_code": order_code,
                "payment_method": "bitcoin",
                "total": float(total_amount),
                "bonus_applied": float(bonus_applied),
            },
        )
        for cart_item in cart_items:
            metrics.track_event(
                "inventory_reserved",
                user_id,
                {
                    "item": cart_item["item_name"],
                    "quantity": cart_item["quantity"],
                    "order_code": order_code,
                },
            )
        if bonus_applied > 0:
            metrics.track_event(
                "payment_bonus_applied",
                user_id,
                {"bonus_amount": float(bonus_applied), "order_code": order_code},
            )

    payment_text = (
        localize("order.payment.bitcoin.title")
        + "\n\n"
        + localize("order.payment.bitcoin.order_code", code=order_code)
        + "\n"
        + localize("order.payment.subtotal_label", amount=total_amount, currency=EnvKeys.PAY_CURRENCY)
        + "\n"
    )

    if bonus_applied > 0:
        payment_text += (
            localize("order.payment.bonus_applied_label", amount=bonus_applied, currency=EnvKeys.PAY_CURRENCY)
            + "\n"
            + localize("order.payment.final_amount_label", amount=final_amount, currency=EnvKeys.PAY_CURRENCY)
            + "\n\n"
        )
    else:
        payment_text += (
            localize("order.payment.total_amount_label", amount=total_amount, currency=EnvKeys.PAY_CURRENCY) + "\n\n"
        )

    payment_text += (
        localize("order.payment.bitcoin.items_title")
        + "\n"
        + f"{chr(10).join(items_summary)}\n\n"
        + localize("order.payment.bitcoin.delivery_title")
        + "\n"
        + f"📍 Address: {cust_address}\n"
        + f"📞 Phone: {cust_phone}\n"
    )

    if cust_note:
        payment_text += f"📝 Note: {cust_note}\n"

    payment_text += (
        "\n"
        + localize("order.payment.bitcoin.address_title")
        + "\n"
        + f"<code>{btc_address}</code>\n\n"
        + localize("order.payment.bitcoin.important_title")
        + "\n"
        + localize("order.payment.bitcoin.send_exact")
        + "\n"
        + localize("order.payment.bitcoin.one_time_address")
        + "\n"
        + localize("order.payment.bitcoin.admin_confirm")
        + "\n\n"
        + localize("order.payment.bitcoin.need_help")
    )

    await message.answer(payment_text, reply_markup=back("back_to_menu"))

    await notify_admin_new_order(
        message.bot,
        order_code,
        user_id,
        username,
        "\n".join(items_summary),
        total_amount,
        btc_address,
        cust_address,
        cust_phone,
        cust_note or "",
        bonus_applied,
        final_amount,
    )

    sync_customer_to_csv(user_id, username)
    await state.clear()


async def process_cash_payment_new_message(message: Message, state: FSMContext, user_id: int | None = None):
    """
    Process Cash on Delivery payment by sending a new message.

    CARD-32: business order creation lives in ``bot.services.checkout``;
    this handler is a Telegram adapter only (I/O + FSM + metrics).
    """
    from bot.services import cart as cart_svc
    from bot.services import checkout as checkout_svc

    if user_id is None:
        user_id = message.from_user.id

    username = await get_telegram_username(user_id, message.bot)
    cart_res = await cart_svc.list_items(user_id)
    cart_items = cart_res.data.get("items") or []

    if not cart_items:
        await message.answer(localize("cart.empty_alert"), reply_markup=back("shop"))
        return

    total_amount = cart_res.data.get("total") or 0
    data = await state.get_data()
    bonus_applied = Decimal(str(data.get("bonus_applied", 0)))
    dd_type = data.get("delivery_type", DELIVERY_DOOR)
    dd_instructions = data.get("drop_instructions")
    dd_lat = data.get("drop_latitude")
    dd_lng = data.get("drop_longitude")
    dd_media = data.get("drop_media")

    # Application service — no Telegram types inside
    order_res = checkout_svc.start_cash_order(
        user_id,
        cart_items,
        total_amount=total_amount,
        bonus_applied=bonus_applied,
        username=username,
        delivery_type=dd_type,
        drop_instructions=dd_instructions,
        drop_latitude=dd_lat,
        drop_longitude=dd_lng,
        drop_media=dd_media,
        brand_id=data.get("current_brand_id"),
        store_id=data.get("current_store_id"),
    )

    if not order_res.ok:
        key = order_res.error_key or "order.payment.error_general"
        if key == "cart.empty":
            await message.answer(localize("cart.empty_alert"), reply_markup=back("shop"))
        elif key == "order.payment.customer_not_found":
            await message.answer(localize("order.payment.customer_not_found"), reply_markup=back("view_cart"))
        elif key == "order.bonus.insufficient":
            await message.answer(localize("order.bonus.insufficient"), reply_markup=back("view_cart"))
        elif key == "order.inventory.unable_to_reserve":
            await message.answer(
                localize(
                    "order.inventory.unable_to_reserve",
                    unavailable_items=order_res.error_detail or order_res.data.get("unavailable_items") or "",
                ),
                reply_markup=back("view_cart"),
            )
        else:
            await message.answer(localize("order.payment.error_general"), reply_markup=back("view_cart"))
        return

    order_code = order_res.data["order_code"]
    items_summary = order_res.data.get("items_summary") or []
    final_amount = Decimal(str(order_res.data.get("final_amount", total_amount)))
    total_amount = Decimal(str(order_res.data.get("total_amount", total_amount)))
    cust_address = order_res.data.get("delivery_address")
    cust_phone = order_res.data.get("phone_number")
    cust_note = order_res.data.get("delivery_note") or ""

    # Adapter-only metrics (not domain)
    metrics = get_metrics()
    if metrics:
        metrics.track_event(
            "order_created",
            user_id,
            {
                "order_code": order_code,
                "payment_method": "cash",
                "total": float(total_amount),
                "bonus_applied": float(bonus_applied),
            },
        )
        for cart_item in cart_items:
            metrics.track_event(
                "inventory_reserved",
                user_id,
                {
                    "item": cart_item["item_name"],
                    "quantity": cart_item["quantity"],
                    "order_code": order_code,
                },
            )
        if bonus_applied > 0:
            metrics.track_event(
                "payment_bonus_applied",
                user_id,
                {"bonus_amount": float(bonus_applied), "order_code": order_code},
            )

    cash_instructions = (
        localize("order.payment.cash.title")
        + "\n\n"
        + localize("order.payment.cash.created", code=order_code)
        + "\n\n"
        + localize("order.payment.cash.items_title")
        + "\n"
        + chr(10).join(items_summary)
        + "\n\n"
        + localize("order.payment.cash.total", amount=float(total_amount))
        + "\n\n"
        + localize("order.payment.cash.after_confirm")
        + "\n"
        + localize("order.payment.cash.payment_to_courier")
        + "\n\n"
        + localize("order.payment.cash.important")
        + "\n"
        + localize("order.payment.cash.admin_contact")
    )

    payment_text = (
        f"{cash_instructions}\n\n"
        + localize("order.payment.order_label", code=order_code)
        + "\n"
        + localize("order.payment.subtotal_label", amount=total_amount, currency=EnvKeys.PAY_CURRENCY)
        + "\n"
    )

    if bonus_applied > 0:
        payment_text += (
            localize("order.payment.bonus_applied_label", amount=bonus_applied, currency=EnvKeys.PAY_CURRENCY)
            + "\n"
            + localize(
                "order.payment.cash.amount_with_bonus",
                amount=final_amount,
                currency=EnvKeys.PAY_CURRENCY,
            )
            + "\n\n"
        )
    else:
        payment_text += (
            localize("order.payment.cash.total_label", amount=total_amount, currency=EnvKeys.PAY_CURRENCY) + "\n\n"
        )

    payment_text += (
        localize("order.payment.bitcoin.items_title")
        + "\n"
        + f"{chr(10).join(items_summary)}\n\n"
        + localize("order.payment.bitcoin.delivery_title")
        + "\n"
        + f"📍 Address: {cust_address}\n"
        + f"📞 Phone: {cust_phone}\n"
    )

    if cust_note:
        payment_text += f"📝 Note: {cust_note}\n"

    payment_text += "\n" + localize("order.info.view_status_hint")

    await message.answer(payment_text, reply_markup=back("back_to_menu"))

    await notify_admin_new_cash_order(
        message.bot,
        order_code,
        user_id,
        username,
        "\n".join(items_summary),
        total_amount,
        cust_address,
        cust_phone,
        cust_note or "",
        bonus_applied,
        final_amount,
    )

    sync_customer_to_csv(user_id, username)

    await state.clear()


async def process_promptpay_payment(message: Message, state: FSMContext, user_id: int | None = None):
    """
    Process PromptPay payment: create order via checkout service, show QR, ask for receipt.

    CARD-32: business order creation lives in ``bot.services.checkout``;
    this handler is a Telegram adapter only (I/O + FSM).
    """
    from aiogram.types import BufferedInputFile

    from bot.services import cart as cart_svc
    from bot.services import checkout as checkout_svc

    if user_id is None:
        user_id = message.from_user.id

    username = await get_telegram_username(user_id, message.bot)
    cart_res = await cart_svc.list_items(user_id)
    cart_items = cart_res.data.get("items") or []

    if not cart_items:
        await message.answer(localize("cart.empty_alert"), reply_markup=back("shop"))
        return

    total_amount = cart_res.data.get("total") or 0
    data = await state.get_data()
    bonus_applied = Decimal(str(data.get("bonus_applied", 0)))
    dd_type = data.get("delivery_type", DELIVERY_DOOR)
    dd_instructions = data.get("drop_instructions")
    dd_lat = data.get("drop_latitude")
    dd_lng = data.get("drop_longitude")
    dd_media = data.get("drop_media")

    # Application service — no Telegram types inside
    order_res = checkout_svc.start_promptpay_order(
        user_id,
        cart_items,
        total_amount=total_amount,
        bonus_applied=bonus_applied,
        username=username,
        delivery_type=dd_type,
        drop_instructions=dd_instructions,
        drop_latitude=dd_lat,
        drop_longitude=dd_lng,
        drop_media=dd_media,
        brand_id=data.get("current_brand_id"),
        store_id=data.get("current_store_id"),
    )

    if not order_res.ok:
        key = order_res.error_key or "order.payment.error_general"
        if key == "cart.empty":
            await message.answer(localize("cart.empty_alert"), reply_markup=back("shop"))
        elif key == "order.payment.customer_not_found":
            await message.answer(localize("order.payment.customer_not_found"), reply_markup=back("view_cart"))
        elif key == "order.bonus.insufficient":
            await message.answer(localize("order.bonus.insufficient"), reply_markup=back("view_cart"))
        elif key == "order.inventory.unable_to_reserve":
            await message.answer(
                localize(
                    "order.inventory.unable_to_reserve",
                    unavailable_items=order_res.error_detail or order_res.data.get("unavailable_items") or "",
                ),
                reply_markup=back("view_cart"),
            )
        else:
            await message.answer(localize("order.payment.error_general"), reply_markup=back("view_cart"))
        return

    order_id = order_res.data["order_id"]
    order_code = order_res.data["order_code"]
    items_summary = order_res.data.get("items_summary") or []
    final_amount = Decimal(str(order_res.data.get("final_amount", total_amount)))
    cust_address = order_res.data.get("delivery_address")
    cust_phone = order_res.data.get("phone_number")
    cust_note = order_res.data.get("delivery_note") or ""

    # QR payload via service (account resolution + optional dynamic QR bytes)
    pay = checkout_svc.build_promptpay_qr_payload(
        final_amount=final_amount,
        order_code=order_code,
        store_id=data.get("current_store_id"),
        brand_id=data.get("current_brand_id"),
    )
    caption = (
        localize("order.payment.promptpay.title")
        + "\n\n"
        + localize("order.payment.promptpay.scan")
        + "\n"
        + f"<b>{EnvKeys.PAY_CURRENCY} {final_amount}</b>\n"
        + f"Order: <code>{order_code}</code>"
    )
    try:
        if pay.data.get("qr_bytes"):
            qr_file = BufferedInputFile(pay.data["qr_bytes"], filename=f"promptpay_{order_code}.png")
            await message.answer_photo(photo=qr_file, caption=caption)
        elif pay.data.get("static_qr_file_id"):
            static_caption = caption + "\n" + localize("order.payment.promptpay.static_amount_note")
            await message.answer_photo(photo=pay.data["static_qr_file_id"], caption=static_caption)
        else:
            await message.answer(
                localize("order.payment.promptpay.title")
                + "\n\n"
                + f"Amount: <b>{final_amount} {EnvKeys.PAY_CURRENCY}</b>\n"
                + f"Order: <code>{order_code}</code>"
            )
    except Exception as qr_error:
        logger.error(f"QR delivery failed: {qr_error}")
        await message.answer(
            localize("order.payment.promptpay.title")
            + "\n\n"
            + f"PromptPay ID: <code>{pay.data.get('promptpay_id') or ''}</code>\n"
            + f"Amount: <b>{final_amount} {EnvKeys.PAY_CURRENCY}</b>\n"
            + f"Order: <code>{order_code}</code>"
        )

    # Ask user to upload receipt
    await message.answer(localize("order.payment.promptpay.upload_receipt"), reply_markup=back("back_to_menu"))

    # Save order_id in state for receipt association
    await state.update_data(promptpay_order_id=order_id, promptpay_order_code=order_code)
    await state.set_state(PromptPayStates.waiting_receipt_photo)

    # Notify admin
    await notify_admin_new_cash_order(
        message.bot,
        order_code,
        user_id,
        username,
        "\n".join(items_summary),
        total_amount,
        cust_address,
        cust_phone,
        cust_note or "",
        bonus_applied,
        final_amount,
    )

    sync_customer_to_csv(user_id, username)


@router.message(PromptPayStates.waiting_receipt_photo, F.photo)
async def process_receipt_photo(message: Message, state: FSMContext):
    """User uploaded payment receipt photo (Card 1) — with optional auto-verification"""
    photo_file_id = message.photo[-1].file_id
    data = await state.get_data()
    order_id = data.get("promptpay_order_id")

    # Phase 1 — persist the receipt photo (short session, no awaits inside)
    order_found = False
    order_code = None
    order_total = None
    order_bonus = Decimal("0")
    order_store_id = None
    order_brand_id = None
    if order_id:
        with Database().session() as session:
            order = session.query(Order).filter_by(id=order_id).first()
            if order:
                order.payment_receipt_photo = photo_file_id
                session.commit()
                order_found = True
                order_code = order.order_code
                order_total = order.total_price
                order_bonus = order.bonus_applied or Decimal("0")
                # Card 28: capture the order's store/brand so the slip is verified
                # against the SAME PromptPay account the QR routed payment to.
                order_store_id = order.store_id
                order_brand_id = order.brand_id
        # session closed before any Telegram/network I/O

    # Phase 2 — download + verify slip (network I/O, NO DB connection held)
    verify_result = None
    duplicate_detected = False
    duplicate_owner_code = None
    if order_found and EnvKeys.SLIP_AUTO_VERIFY == "1":
        try:
            from bot.payments.slip_verify import verify_slip

            # Download the photo from Telegram
            file_obj = await message.bot.get_file(photo_file_id)
            photo_bytes_io = await message.bot.download_file(file_obj.file_path)
            slip_image = photo_bytes_io.read()

            # Calculate expected amount (total - bonus)
            expected_amount = order_total - order_bonus

            # Card 28: verify the slip's receiver against the SAME account the QR
            # paid into (store → brand → global), not just the global name.
            from bot.payments.store_payment import resolve_payment_target

            target = resolve_payment_target(store_id=order_store_id, brand_id=order_brand_id)
            verify_result = await verify_slip(
                slip_image=slip_image,
                expected_amount=expected_amount,
                expected_receiver=target.promptpay_name or None,
            )
        except Exception as e:
            logger.error(f"Slip auto-verification error for order {order_code}: {e}")
            verify_result = None

        # Phase 3 — persist verification result (short session, no awaits inside)
        if verify_result is not None:
            try:
                import datetime as dt

                from bot.payments.slip_verify import VerifyStatus

                with Database().session() as session:
                    order = session.query(Order).filter_by(id=order_id).first()
                    if order:
                        order.slip_verify_bank = verify_result.provider.value if verify_result.provider else None
                        order.slip_verified_amount = verify_result.amount
                        order.slip_sender_name = verify_result.sender_name
                        order.slip_receiver_name = verify_result.receiver_name
                        order.slip_verified_at = dt.datetime.now(dt.UTC)

                        # Duplicate-slip guard (Card 24): a verified bank slip can
                        # pay for exactly one order. SlipOK/RDCW don't flag reuse
                        # server-side, so before storing the txn id / auto-confirming
                        # we check no *other* order already claimed it. This is also
                        # constraint-safe — we never copy a txn id already in use,
                        # which would otherwise trip uq_orders_slip_transaction_id.
                        txn_id = verify_result.transaction_id
                        duplicate_owner = None
                        if txn_id:
                            duplicate_owner = (
                                session.query(Order)
                                .filter(Order.slip_transaction_id == txn_id, Order.id != order.id)
                                .first()
                            )

                        if duplicate_owner is not None:
                            duplicate_detected = True
                            duplicate_owner_code = duplicate_owner.order_code or str(duplicate_owner.id)
                            order.slip_verify_status = VerifyStatus.DUPLICATE.value
                            # Do NOT store the txn id on this order or confirm it.
                            logger.warning(
                                "Duplicate slip rejected: order %s tried to reuse txn %s already claimed by order %s",
                                order_code,
                                txn_id,
                                duplicate_owner_code,
                            )
                        else:
                            order.slip_verify_status = verify_result.status.value
                            order.slip_transaction_id = txn_id
                            if verify_result.status == VerifyStatus.VERIFIED:
                                # Auto-confirm the payment
                                order.payment_verified_at = dt.datetime.now(dt.UTC)
                                order.payment_verified_by = 0  # 0 = auto-verified by API
                                order.order_status = "confirmed"
                                logger.info(
                                    "Order %s auto-verified via %s (txn: %s)",
                                    order_code,
                                    verify_result.provider.value,
                                    verify_result.transaction_id,
                                )

                        session.commit()
            except Exception as e:
                logger.error(f"Slip auto-verification error for order {order_code}: {e}")

    # Phase 4 — outbound I/O (no DB connection held)
    if order_found:
        # Build admin notification caption
        admin_caption = (
            f"💳 <b>PromptPay Receipt</b>\n"
            f"Order: <code>{order_code}</code>\n"
            f"Amount: {order_total} {EnvKeys.PAY_CURRENCY}\n"
            f"From: {message.from_user.id}"
        )

        if duplicate_detected:
            admin_caption += (
                f"\n\n🚫 <b>DUPLICATE SLIP REJECTED</b>\n"
                f"Txn: <code>{verify_result.transaction_id if verify_result else '?'}</code>\n"
                f"Already used by order <code>{duplicate_owner_code}</code>\n"
                f"This order was NOT auto-confirmed — verify manually."
            )
        elif verify_result:
            from bot.payments.slip_verify import VerifyStatus

            if verify_result.status == VerifyStatus.VERIFIED:
                admin_caption += (
                    f"\n\n✅ <b>AUTO-VERIFIED</b> via {verify_result.provider.value.upper()}\n"
                    f"Txn: <code>{verify_result.transaction_id}</code>\n"
                    f"Amount: {verify_result.amount} THB"
                )
                if verify_result.sender_name:
                    admin_caption += f"\nSender: {verify_result.sender_name}"
            elif verify_result.status == VerifyStatus.NO_API_CONFIGURED:
                admin_caption += "\n\n⏳ Manual verification required (no bank API configured)"
            else:
                admin_caption += (
                    f"\n\n⚠️ <b>VERIFY FAILED:</b> {verify_result.status.value}\n"
                    f"{verify_result.error_message or 'Check manually'}"
                )

        # Notify admin with receipt
        owner_id = EnvKeys.OWNER_ID
        if owner_id:
            try:
                await message.bot.send_photo(
                    int(owner_id),
                    photo_file_id,
                    caption=admin_caption,
                )
            except Exception as e:
                logger.error(f"Failed to forward receipt to admin: {e}")

        # Send appropriate response to user
        if duplicate_detected:
            await message.answer(
                localize("order.payment.promptpay.duplicate_slip"),
                reply_markup=back("back_to_menu"),
            )
            await state.clear()
            return

        if verify_result and verify_result.status == VerifyStatus.VERIFIED:
            await message.answer(
                localize("order.payment.promptpay.slip_verified"),
                reply_markup=back("back_to_menu"),
            )
            await state.clear()
            return

    await message.answer(localize("order.payment.promptpay.receipt_received"), reply_markup=back("back_to_menu"))
    await state.clear()


@router.message(PromptPayStates.waiting_receipt_photo)
async def process_receipt_invalid(message: Message, state: FSMContext):
    """User sent non-photo message when receipt expected"""
    await message.answer(localize("order.payment.promptpay.receipt_invalid"))


async def notify_admin_new_order(
    bot,
    order_code: str,
    buyer_id: int,
    buyer_username: str,
    items_summary: str,
    total_amount: Decimal,
    btc_address: str,
    delivery_address: str,
    phone_number: str,
    delivery_note: str,
    bonus_applied: Decimal = Decimal("0"),
    final_amount: Decimal | None = None,
):
    """
    Send notification to admin about new order
    """
    owner_id = EnvKeys.OWNER_ID

    if not owner_id:
        logger.warning("OWNER_ID not set, cannot send admin notification")
        return

    if final_amount is None:
        final_amount = total_amount

    try:
        admin_text = (
            localize("admin.order.new_bitcoin_order")
            + "\n\n"
            + localize("admin.order.order_label", code=html.escape(order_code))
            + "\n"
            + localize("admin.order.customer_label", username=html.escape(buyer_username), id=buyer_id)
            + "\n"
            + localize(
                "admin.order.subtotal_label",
                amount=html.escape(str(total_amount)),
                currency=html.escape(EnvKeys.PAY_CURRENCY),
            )
            + "\n"
        )

        if bonus_applied > 0:
            admin_text += (
                localize("admin.order.bonus_applied_label", amount=html.escape(str(bonus_applied)))
                + "\n"
                + localize(
                    "admin.order.amount_to_receive_label",
                    amount=html.escape(str(final_amount)),
                    currency=html.escape(EnvKeys.PAY_CURRENCY),
                )
                + "\n\n"
            )
        else:
            admin_text += f"<b>Total: ${html.escape(str(total_amount))} {html.escape(EnvKeys.PAY_CURRENCY)}</b>\n\n"

        admin_text += (
            localize("order.payment.bitcoin.items_title") + "\n"
            f"{html.escape(items_summary)}\n\n" + localize("order.payment.bitcoin.delivery_title") + "\n"
            f"📍 Address: {html.escape(delivery_address)}\n"
            f"📞 Phone: {html.escape(phone_number)}\n"
        )

        if delivery_note:
            admin_text += f"📝 Note: {html.escape(delivery_note)}\n"

        admin_text += (
            "\n<b>Payment:</b>\n"
            + localize("admin.order.bitcoin_address_label", address=html.escape(btc_address))
            + "\n\n"
            + localize("admin.order.awaiting_payment_status")
        )

        await bot.send_message(int(owner_id), admin_text)

    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")


async def notify_admin_new_cash_order(
    bot,
    order_code: str,
    buyer_id: int,
    buyer_username: str,
    items_summary: str,
    total_amount: Decimal,
    delivery_address: str,
    phone_number: str,
    delivery_note: str,
    bonus_applied: Decimal = Decimal("0"),
    final_amount: Decimal | None = None,
):
    """
    Send notification to admin about new cash order
    """
    owner_id = EnvKeys.OWNER_ID

    if not owner_id:
        logger.warning("OWNER_ID not set, cannot send admin notification")
        return

    if final_amount is None:
        final_amount = total_amount

    try:
        admin_text = (
            localize("admin.order.new_cash_order")
            + "\n\n"
            + localize("admin.order.order_label", code=html.escape(order_code))
            + "\n"
            + localize("admin.order.customer_label", username=html.escape(buyer_username), id=buyer_id)
            + "\n"
            + localize("admin.order.payment_method_label", method=localize("admin.order.payment_cash"))
            + "\n"
            + localize(
                "admin.order.subtotal_label",
                amount=html.escape(str(total_amount)),
                currency=html.escape(EnvKeys.PAY_CURRENCY),
            )
            + "\n"
        )

        if bonus_applied > 0:
            admin_text += (
                localize("admin.order.bonus_applied_label", amount=html.escape(str(bonus_applied)))
                + "\n"
                + localize(
                    "admin.order.amount_to_collect_label",
                    amount=html.escape(str(final_amount)),
                    currency=html.escape(EnvKeys.PAY_CURRENCY),
                )
                + "\n\n"
            )
        else:
            admin_text += (
                f"<b>Amount to Collect: ${html.escape(str(total_amount))} {html.escape(EnvKeys.PAY_CURRENCY)}</b>\n\n"
            )

        admin_text += (
            localize("order.payment.bitcoin.items_title") + "\n"
            f"{html.escape(items_summary)}\n\n" + localize("order.payment.bitcoin.delivery_title") + "\n"
            f"📍 Address: {html.escape(delivery_address)}\n"
            f"📞 Phone: {html.escape(phone_number)}\n"
        )

        if delivery_note:
            admin_text += f"📝 Note: {html.escape(delivery_note)}\n"

        admin_text += (
            "\n"
            + localize("admin.order.action_required_title")
            + "\n"
            + localize("admin.order.use_cli_confirm", code=html.escape(order_code))
        )

        await bot.send_message(int(owner_id), admin_text)

    except Exception as e:
        logger.error(f"Failed to send admin notification for cash order: {e}")
