from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
import html
import re
from decimal import Decimal
from urllib.parse import quote_plus

from bot.database import Database
from bot.database.models.main import Order, OrderItem, CustomerInfo, ShoppingCart
from bot.database.methods import reserve_inventory, get_cart_items, calculate_cart_total
from bot.keyboards import back, simple_buttons
from bot.i18n import localize
from bot.config import EnvKeys
from bot.states import OrderStates
from bot.states.payment_state import PromptPayStates
from bot.logger_mesh import logger
from bot.payments.bitcoin import get_available_bitcoin_address, mark_bitcoin_address_used
from bot.export import log_order_creation, sync_customer_to_csv
from bot.utils import generate_unique_order_code, get_telegram_username
from bot.monitoring import get_metrics

router = Router()


# ---------------------------------------------------------------------------
# Helper: extract lat/lng from Google Maps URLs
# ---------------------------------------------------------------------------
_MAPS_COORD_PATTERNS = [
    re.compile(r'@(-?\d+\.\d+),(-?\d+\.\d+)'),           # maps/@lat,lng
    re.compile(r'q=(-?\d+\.\d+),(-?\d+\.\d+)'),           # maps?q=lat,lng
    re.compile(r'll=(-?\d+\.\d+),(-?\d+\.\d+)'),          # ll=lat,lng
    re.compile(r'/(-?\d+\.\d+),(-?\d+\.\d+)'),            # generic /lat,lng in path
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
    kb = simple_buttons([
        (localize("btn.location_method.gps"), "loc_method_gps"),
        (localize("btn.location_method.live_gps"), "loc_method_live_gps"),
        (localize("btn.location_method.google_link"), "loc_method_google_link"),
        (localize("btn.location_method.type_address"), "loc_method_type_address"),
    ], per_row=1)
    if edit and hasattr(target, 'edit_text'):
        await target.edit_text(text, reply_markup=kb)
    else:
        await target.answer(text, reply_markup=kb)
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
            [KeyboardButton(text=localize("btn.back"))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    # LOGIC-21 fix: Don't send duplicate text — just delete old inline message
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        localize("order.delivery.gps_prompt"),
        reply_markup=location_kb
    )
    await state.set_state(OrderStates.waiting_location)


@router.callback_query(F.data == "loc_method_live_gps", OrderStates.waiting_location_method)
async def loc_method_live_gps(call: CallbackQuery, state: FSMContext):
    """User chose to share live location"""
    await call.answer()
    await call.message.edit_text(
        localize("order.delivery.live_gps_prompt"),
        reply_markup=back("view_cart")
    )
    await state.set_state(OrderStates.waiting_live_location)


@router.callback_query(F.data == "loc_method_google_link", OrderStates.waiting_location_method)
async def loc_method_google_link(call: CallbackQuery, state: FSMContext):
    """User chose to paste a Google Maps link"""
    await call.answer()
    await call.message.edit_text(
        localize("order.delivery.google_link_prompt"),
        reply_markup=back("view_cart")
    )
    await state.set_state(OrderStates.waiting_google_maps_link)


@router.callback_query(F.data == "loc_method_type_address", OrderStates.waiting_location_method)
async def loc_method_type_address(call: CallbackQuery, state: FSMContext):
    """User chose to type an address"""
    await call.answer()
    await call.message.edit_text(
        localize("order.delivery.address_prompt"),
        reply_markup=back("view_cart")
    )
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
        latitude=lat, longitude=lng,
        google_maps_link=maps_link,
        delivery_address=maps_link,
    )

    await message.answer(
        localize("order.delivery.location_saved"),
        reply_markup=ReplyKeyboardRemove()
    )

    # Proceed to delivery type
    await ask_delivery_type(message, state)


@router.message(OrderStates.waiting_location)
async def location_not_shared(message: Message, state: FSMContext):
    """User sent text instead of location — nudge them or go back"""
    if message.text and message.text.strip() == localize("btn.back"):
        await message.answer(
            localize("order.delivery.location_method_prompt"),
            reply_markup=ReplyKeyboardRemove()
        )
        await show_location_method_choice(message, state)
        return

    await message.answer(
        localize("order.delivery.gps_hint"),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=localize("btn.share_location"), request_location=True)],
                [KeyboardButton(text=localize("btn.back"))]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
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
        latitude=lat, longitude=lng,
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
    await message.answer(
        localize("order.delivery.live_gps_hint"),
        reply_markup=back("view_cart")
    )


# ---------------------------------------------------------------------------
# Option 2: Google Maps link
# ---------------------------------------------------------------------------

@router.message(OrderStates.waiting_google_maps_link)
async def process_google_maps_link(message: Message, state: FSMContext):
    """Parse coordinates from a Google Maps link"""
    text = (message.text or "").strip()

    # Basic URL validation
    if not text or not any(domain in text.lower() for domain in ["google.com/maps", "maps.google", "goo.gl/maps", "maps.app.goo.gl"]):
        await message.answer(
            localize("order.delivery.google_link_invalid"),
            reply_markup=back("view_cart")
        )
        return

    coords = _extract_coords_from_url(text)
    if coords:
        lat, lng = coords
        maps_link = f"https://www.google.com/maps?q={lat},{lng}"
        await state.update_data(
            latitude=lat, longitude=lng,
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
        await message.answer(
            localize("order.delivery.address_invalid"),
            reply_markup=back("view_cart")
        )
        return

    # Save to state
    await state.update_data(delivery_address=delivery_address)

    # Generate Google Maps search link for the address
    search_url = f"https://www.google.com/maps/search/{quote_plus(delivery_address)}"
    await state.update_data(google_maps_link=search_url)

    # Ask user to confirm the address
    await message.answer(
        localize("order.delivery.address_confirm_prompt",
                 address=html.escape(delivery_address),
                 maps_link=search_url),
        reply_markup=simple_buttons([
            (localize("btn.address_confirm_yes"), "address_confirm_yes"),
            (localize("btn.address_confirm_retry"), "address_confirm_retry"),
        ], per_row=1),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    await state.set_state(OrderStates.waiting_address_confirm)


@router.callback_query(F.data == "address_confirm_yes", OrderStates.waiting_address_confirm)
async def address_confirmed(call: CallbackQuery, state: FSMContext):
    """User confirmed the searched address"""
    await call.answer()
    await call.message.edit_text(localize("order.delivery.location_saved"))
    await ask_delivery_type(call.message, state)


@router.callback_query(F.data == "address_confirm_retry", OrderStates.waiting_address_confirm)
async def address_retry(call: CallbackQuery, state: FSMContext):
    """User wants to re-enter address"""
    await call.answer()
    await show_location_method_choice(call.message, state, edit=True)


async def ask_delivery_type(message: Message, state: FSMContext):
    """Show delivery type selection (Card 3)"""
    await message.answer(
        localize("order.delivery.type_prompt"),
        reply_markup=simple_buttons([
            (localize("btn.delivery.door"), "delivery_type_door"),
            (localize("btn.delivery.dead_drop"), "delivery_type_dead_drop"),
            (localize("btn.delivery.pickup"), "delivery_type_pickup"),
        ], per_row=1)
    )
    await state.set_state(OrderStates.waiting_delivery_type)


@router.callback_query(F.data == "delivery_type_door", OrderStates.waiting_delivery_type)
async def delivery_type_door(call: CallbackQuery, state: FSMContext):
    """User selected door delivery"""
    await call.answer()
    await state.update_data(delivery_type="door")
    # LOGIC-21 fix: Don't send duplicate text
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        localize("order.delivery.phone_prompt"),
        reply_markup=back("view_cart")
    )
    await state.set_state(OrderStates.waiting_phone_number)


@router.callback_query(F.data == "delivery_type_dead_drop", OrderStates.waiting_delivery_type)
async def delivery_type_dead_drop(call: CallbackQuery, state: FSMContext):
    """User selected dead drop — collect instructions"""
    await call.answer()
    await state.update_data(delivery_type="dead_drop")
    await call.message.edit_text(
        localize("order.delivery.drop_instructions_prompt"),
    )
    await state.set_state(OrderStates.waiting_drop_instructions)


@router.callback_query(F.data == "delivery_type_pickup", OrderStates.waiting_delivery_type)
async def delivery_type_pickup(call: CallbackQuery, state: FSMContext):
    """User selected self-pickup — skip address/location details"""
    await call.answer()
    await state.update_data(delivery_type="pickup")
    # LOGIC-21 fix: Don't send duplicate text
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        localize("order.delivery.phone_prompt"),
        reply_markup=back("view_cart")
    )
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
            keyboard=[[KeyboardButton(
                text=localize("btn.share_drop_location"),
                request_location=True
            )]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
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
        reply_markup=simple_buttons([
            (localize("btn.skip_drop_media"), "skip_drop_media")
        ], per_row=1)
    )
    await state.set_state(OrderStates.waiting_drop_media)


async def _accumulate_drop_media(message: Message, state: FSMContext, file_id: str, media_type: str):
    """Shared helper: accumulate a media file for the dead drop location."""
    data = await state.get_data()
    media_list = data.get('drop_media', [])
    media_list.append({"file_id": file_id, "type": media_type})
    await state.update_data(drop_media=media_list)

    await message.answer(
        localize("order.delivery.drop_media_saved", count=len(media_list)),
        reply_markup=simple_buttons([
            (localize("btn.drop_media_done"), "done_drop_media"),
            (localize("btn.skip_drop_media"), "skip_drop_media"),
        ], per_row=1)
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
    await call.message.edit_text(localize("order.delivery.phone_prompt"))
    await call.message.answer(
        localize("order.delivery.phone_prompt"),
        reply_markup=back("view_cart")
    )
    await state.set_state(OrderStates.waiting_phone_number)


@router.callback_query(F.data == "skip_drop_media", OrderStates.waiting_drop_media)
async def skip_drop_media(call: CallbackQuery, state: FSMContext):
    """User skipped drop location media"""
    await call.answer()
    await call.message.edit_text(localize("order.delivery.phone_prompt"))
    await call.message.answer(
        localize("order.delivery.phone_prompt"),
        reply_markup=back("view_cart")
    )
    await state.set_state(OrderStates.waiting_phone_number)


# --- Legacy single-photo handlers (kept for backward compat) ---

@router.message(OrderStates.waiting_drop_photo, F.photo)
async def process_drop_photo(message: Message, state: FSMContext):
    """Save photo of drop location (legacy single-photo flow)"""
    photo_file_id = message.photo[-1].file_id
    await state.update_data(drop_location_photo=photo_file_id)

    await message.answer(localize("order.delivery.drop_photo_saved"))
    await message.answer(
        localize("order.delivery.phone_prompt"),
        reply_markup=back("view_cart")
    )
    await state.set_state(OrderStates.waiting_phone_number)


@router.callback_query(F.data == "skip_drop_photo", OrderStates.waiting_drop_photo)
async def skip_drop_photo(call: CallbackQuery, state: FSMContext):
    """User skipped drop location photo (legacy flow)"""
    await call.answer()
    await call.message.edit_text(localize("order.delivery.phone_prompt"))
    await call.message.answer(
        localize("order.delivery.phone_prompt"),
        reply_markup=back("view_cart")
    )
    await state.set_state(OrderStates.waiting_phone_number)


@router.message(OrderStates.waiting_phone_number)
async def process_phone_number(message: Message, state: FSMContext):
    """
    Collect phone number from user
    """
    phone_number = message.text.strip()

    if len(phone_number) < 8:
        await message.answer(
            localize("order.delivery.phone_invalid"),
            reply_markup=back("view_cart")
        )
        return

    # Save to state
    await state.update_data(phone_number=phone_number)

    # Ask for delivery note (optional)
    await message.answer(
        localize("order.delivery.note_prompt"),
        reply_markup=simple_buttons([(localize("btn.skip"), "skip_delivery_note"), (localize("btn.back"), "view_cart")],
                                    per_row=2)
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
    await call.message.delete()
    await check_and_ask_about_bonus(call.message, state, user_id=call.from_user.id, from_callback=True)


async def check_and_ask_about_bonus(message: Message, state: FSMContext, user_id: int = None,
                                    from_callback: bool = False):
    """
    Check if user has referral bonus and ask if they want to apply it to the order
    """
    if user_id is None:
        user_id = message.from_user.id

    # Get user's bonus balance from CustomerInfo
    with Database().session() as session:
        customer_info = session.query(CustomerInfo).filter_by(telegram_id=user_id).first()

        if customer_info and customer_info.bonus_balance and customer_info.bonus_balance > 0:
            bonus_balance = customer_info.bonus_balance

            # Calculate cart total to show in message
            total_amount = await calculate_cart_total(user_id)

            # Save bonus_balance in state for later use
            await state.update_data(available_bonus=float(bonus_balance))

            text = (
                    localize("order.bonus.available", bonus_balance=bonus_balance) +
                    localize("order.bonus.order_total_label", amount=total_amount,
                             currency=EnvKeys.PAY_CURRENCY) + "\n\n" +
                    localize("order.bonus.apply_question") + f"\n" +
                    localize("order.bonus.choose_amount_hint", max_amount=min(bonus_balance, total_amount))
            )

            await message.answer(
                text,
                reply_markup=simple_buttons([
                    (localize("btn.apply_bonus_yes"), "apply_bonus_yes"),
                    (localize("btn.apply_bonus_no"), "apply_bonus_no")
                ], per_row=2)
            )
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
    available_bonus = Decimal(str(data.get('available_bonus', 0)))

    total_amount = await calculate_cart_total(call.from_user.id)
    max_applicable = min(available_bonus, Decimal(str(total_amount)))

    await call.message.edit_text(
        localize("order.bonus.enter_amount_title") + "\n\n" +
        localize("order.bonus.available_label", amount=available_bonus) + "\n" +
        localize("order.bonus.order_total_label", amount=total_amount, currency=EnvKeys.PAY_CURRENCY) + "\n" +
        localize("order.bonus.max_applicable_label", amount=max_applicable) + "\n\n" +
        localize("order.bonus.enter_amount", max_applicable=max_applicable),
        reply_markup=simple_buttons([
            (localize("btn.use_all_bonus", amount=max_applicable), f"use_all_bonus_{max_applicable}"),
            (localize("btn.cancel"), "apply_bonus_no")
        ], per_row=2)
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

    await state.update_data(bonus_applied=float(bonus_amount))
    await call.message.delete()
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
        available_bonus = Decimal(str(data.get('available_bonus', 0)))
        total_amount = await calculate_cart_total(message.from_user.id)
        max_applicable = min(available_bonus, Decimal(str(total_amount)))

        if bonus_amount > max_applicable:
            await message.answer(
                localize("order.bonus.amount_too_high", max_applicable=max_applicable)
            )
            return

        # Valid amount - save and proceed
        await state.update_data(bonus_applied=float(bonus_amount))
        await finalize_order_and_payment(message, state, user_id=message.from_user.id)

    except (ValueError, TypeError):
        await message.answer(localize("order.bonus.invalid_amount"))


@router.callback_query(F.data == "apply_bonus_no")
async def apply_bonus_no_handler(call: CallbackQuery, state: FSMContext):
    """
    User doesn't want to apply bonus
    """
    await state.update_data(bonus_applied=0)
    await call.message.delete()
    await finalize_order_and_payment(call.message, state, user_id=call.from_user.id, from_callback=True)


async def show_payment_method_selection(message: Message, state: FSMContext, user_id: int = None):
    """
    Show payment method selection (Bitcoin or Cash)
    """
    if user_id is None:
        user_id = message.from_user.id

    # Get cart total
    cart_total = await calculate_cart_total(user_id)
    data = await state.get_data()
    bonus_applied = Decimal(str(data.get('bonus_applied', 0)))
    final_amount = cart_total - bonus_applied

    # Get localized strings
    text = localize("order.payment_method.choose")

    summary_text = (
            localize("order.summary.title") +
            localize("order.summary.cart_total", cart_total=cart_total) + "\n"
    )

    if bonus_applied > 0:
        summary_text += localize("order.summary.bonus_applied", bonus_applied=bonus_applied) + "\n"
        summary_text += f"<b>" + localize("order.summary.final_amount", final_amount=final_amount) + "</b>\n\n"
    else:
        summary_text += localize("order.summary.total_label", amount=final_amount,
                                 currency=EnvKeys.PAY_CURRENCY) + "\n\n"

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

    await message.answer(
        summary_text,
        reply_markup=simple_buttons(payment_buttons, per_row=1)
    )

    await state.set_state(OrderStates.waiting_payment_method)


@router.callback_query(F.data == "payment_method_bitcoin", OrderStates.waiting_payment_method)
async def payment_method_bitcoin_handler(call: CallbackQuery, state: FSMContext):
    """
    User selected Bitcoin payment
    """
    await call.answer()
    await state.update_data(payment_method='bitcoin')

    # Track payment method selection
    metrics = get_metrics()
    if metrics:
        metrics.track_event("payment_bitcoin_initiated", call.from_user.id)
        metrics.track_conversion("customer_journey", "payment_initiated", call.from_user.id)

    # Proceed to Bitcoin payment
    await process_bitcoin_payment_new_message(call.message, state, user_id=call.from_user.id)


@router.callback_query(F.data == "payment_method_cash", OrderStates.waiting_payment_method)
async def payment_method_cash_handler(call: CallbackQuery, state: FSMContext):
    """
    User selected Cash payment
    """
    await call.answer()
    await state.update_data(payment_method='cash')

    # Track payment method selection
    metrics = get_metrics()
    if metrics:
        metrics.track_event("payment_cash_initiated", call.from_user.id)
        metrics.track_conversion("customer_journey", "payment_initiated", call.from_user.id)

    # Proceed to Cash payment
    await process_cash_payment_new_message(call.message, state, user_id=call.from_user.id)


@router.callback_query(F.data == "payment_method_promptpay", OrderStates.waiting_payment_method)
async def payment_method_promptpay_handler(call: CallbackQuery, state: FSMContext):
    """
    User selected PromptPay payment (Card 1)
    """
    await call.answer()
    await state.update_data(payment_method='promptpay')

    metrics = get_metrics()
    if metrics:
        metrics.track_event("payment_promptpay_initiated", call.from_user.id)
        metrics.track_conversion("customer_journey", "payment_initiated", call.from_user.id)

    await process_promptpay_payment(call.message, state, user_id=call.from_user.id)


async def finalize_order_and_payment(message: Message, state: FSMContext, user_id: int = None,
                                     from_callback: bool = False):
    """
    Save customer info and proceed to payment method selection
    """
    if user_id is None:
        user_id = message.from_user.id

    # Get real username from Telegram API
    username = await get_telegram_username(user_id, message.bot)

    # Get data from state
    data = await state.get_data()
    delivery_address = data.get('delivery_address')
    phone_number = data.get('phone_number')
    delivery_note = data.get('delivery_note', '')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    google_maps_link = data.get('google_maps_link')

    # Save/update customer info
    try:
        with Database().session() as session:
            customer_info = session.query(CustomerInfo).filter_by(
                telegram_id=user_id
            ).first()

            if customer_info:
                # Log changes
                from bot.export.custom_logging import log_customer_info_change

                if customer_info.delivery_address != delivery_address:
                    log_customer_info_change(
                        user_id, username, "ADDRESS",
                        customer_info.delivery_address, delivery_address
                    )
                    customer_info.delivery_address = delivery_address

                if customer_info.phone_number != phone_number:
                    log_customer_info_change(
                        user_id, username, "PHONE",
                        customer_info.phone_number, phone_number
                    )
                    customer_info.phone_number = phone_number

                if customer_info.delivery_note != delivery_note:
                    log_customer_info_change(
                        user_id, username, "DELIVERY_NOTE",
                        customer_info.delivery_note, delivery_address
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
                    delivery_note=delivery_note
                )
                # Set GPS if provided
                if latitude is not None and longitude is not None:
                    customer_info.latitude = latitude
                    customer_info.longitude = longitude
                session.add(customer_info)

            session.commit()

    except Exception as e:
        logger.error(f"Error saving customer info: {e}")
        await message.answer(
            localize("order.delivery.info_save_error"),
            reply_markup=back("view_cart")
        )
        return

    # Show payment method selection
    await show_payment_method_selection(message, state, user_id=user_id)


async def process_bitcoin_payment(call: CallbackQuery, state: FSMContext):
    """
    Process Bitcoin payment from callback query
    """
    user_id = call.from_user.id

    # Get real username from Telegram API
    username = await get_telegram_username(user_id, call.bot)

    # Get cart items
    cart_items = await get_cart_items(user_id)

    if not cart_items:
        await call.answer(localize("cart.empty_alert"), show_alert=True)
        return

    # Calculate total
    total_amount = await calculate_cart_total(user_id)

    # Get Bitcoin address
    btc_address = get_available_bitcoin_address()

    if not btc_address:
        await call.message.edit_text(
            localize("order.payment.system_unavailable"),
            reply_markup=back("back_to_menu")
        )
        return

    # Dead drop fields from FSM state
    fsm_data = await state.get_data()
    dd_type = fsm_data.get('delivery_type', 'door')
    dd_instructions = fsm_data.get('drop_instructions')
    dd_lat = fsm_data.get('drop_latitude')
    dd_lng = fsm_data.get('drop_longitude')
    dd_media = fsm_data.get('drop_media')

    # Get customer info
    with Database().session() as session:
        customer_info = session.query(CustomerInfo).filter_by(
            telegram_id=user_id
        ).first()

        if not customer_info:
            await call.answer(localize("order.payment.customer_not_found"), show_alert=True)
            return

        # Create one order for entire cart
        try:
            items_summary = []

            # Create the main order
            order = Order(
                buyer_id=user_id,
                total_price=Decimal(str(total_amount)),
                payment_method="bitcoin",
                delivery_address=customer_info.delivery_address,
                phone_number=customer_info.phone_number,
                delivery_note=customer_info.delivery_note or "",
                bitcoin_address=btc_address,
                order_status="pending",
                latitude=customer_info.latitude,
                longitude=customer_info.longitude,
                google_maps_link=f"https://www.google.com/maps?q={customer_info.latitude},{customer_info.longitude}" if customer_info.latitude else None,
                delivery_type=dd_type,
                drop_instructions=dd_instructions,
                drop_latitude=dd_lat,
                drop_longitude=dd_lng,
                drop_media=dd_media,
            )
            session.add(order)
            session.flush()  # Get the order ID

            # Generate unique order code
            order.order_code = generate_unique_order_code(session)

            # Process each cart item and create OrderItems (Physical Goods - No ItemValues)
            items_to_reserve = []
            for cart_item in cart_items:
                item_name = cart_item['item_name']
                quantity = cart_item['quantity']
                price = cart_item['price']

                # Create OrderItem (no item_values field for physical goods)
                order_item = OrderItem(
                    order_id=order.id,
                    item_name=item_name,
                    price=Decimal(str(price)),
                    quantity=quantity,
                    selected_modifiers=cart_item.get('selected_modifiers')
                )
                session.add(order_item)

                # Add to reservation list
                items_to_reserve.append({
                    'item_name': item_name,
                    'quantity': quantity
                })

                items_summary.append(f"{item_name} x{quantity} = {cart_item['total']} {EnvKeys.PAY_CURRENCY}")

            # Reserve inventory for 15 minutes
            success, msg = reserve_inventory(order.id, items_to_reserve, session)
            if not success:
                session.rollback()
                await call.message.edit_text(
                    localize("order.inventory.unable_to_reserve", unavailable_items=msg),
                    reply_markup=back("view_cart")
                )
                return

            # Mark Bitcoin address as used with this order
            mark_bitcoin_address_used(btc_address, user_id, username, order.id, session=session,
                                      order_code=order.order_code)

            # Log order creation
            log_order_creation(
                order_id=order.id,
                buyer_id=user_id,
                buyer_username=username,
                items_summary="\n".join(items_summary),
                total_price=float(total_amount),
                payment_method="bitcoin",
                delivery_address=customer_info.delivery_address,
                phone_number=customer_info.phone_number,
                bitcoin_address=btc_address,
                order_code=order.order_code
            )

            # Clear cart
            session.query(ShoppingCart).filter_by(user_id=user_id).delete()

            session.commit()

            # Send payment instructions to user
            payment_text = (
                    localize("order.payment.bitcoin.title") + "\n\n" +
                    localize("order.payment.bitcoin.order_code", code=order.order_code) + "\n" +
                    localize("order.payment.bitcoin.total_amount", amount=total_amount,
                             currency=EnvKeys.PAY_CURRENCY) + "\n\n" +
                    localize("order.payment.bitcoin.items_title") + "\n" +
                    f"{chr(10).join(items_summary)}\n\n" +
                    localize("order.payment.bitcoin.delivery_title") + "\n"
                                                                       f"📍 Address: {customer_info.delivery_address}\n"
                                                                       f"📞 Phone: {customer_info.phone_number}\n"
            )

            if customer_info.delivery_note:
                payment_text += f"📝 Note: {customer_info.delivery_note}\n"

            payment_text += (
                    "\n" + localize("order.payment.bitcoin.address_title") + "\n"
                                                                             f"<code>{btc_address}</code>\n\n" +
                    localize("order.payment.bitcoin.important_title") + "\n" +
                    localize("order.payment.bitcoin.send_exact") + "\n" +
                    localize("order.payment.bitcoin.one_time_address") + "\n" +
                    localize("order.payment.bitcoin.admin_confirm") + "\n\n" +
                    localize("order.payment.bitcoin.need_help")
            )

            await call.message.edit_text(
                payment_text,
                reply_markup=back("back_to_menu")
            )

            # Notify admin
            await notify_admin_new_order(
                call.bot, order.order_code, user_id, username,
                "\n".join(items_summary), total_amount, btc_address,
                customer_info.delivery_address, customer_info.phone_number,
                customer_info.delivery_note or ""
            )

            # Sync customer CSV
            sync_customer_to_csv(user_id, username)

            await state.clear()

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating orders: {e}")
            await call.message.edit_text(
                localize("order.payment.creation_error"),
                reply_markup=back("view_cart")
            )
            return


async def process_bitcoin_payment_new_message(message: Message, state: FSMContext, user_id: int = None):
    """
    Process Bitcoin payment by sending a new message
    """
    if user_id is None:
        user_id = message.from_user.id

    # Get real username from Telegram API
    username = await get_telegram_username(user_id, message.bot)

    # Get cart items
    cart_items = await get_cart_items(user_id)

    if not cart_items:
        await message.answer(localize("cart.empty_alert"), reply_markup=back("shop"))
        return

    # Calculate total
    total_amount = await calculate_cart_total(user_id)

    # Get state data (bonus + dead drop fields)
    data = await state.get_data()
    bonus_applied = Decimal(str(data.get('bonus_applied', 0)))
    dd_type = data.get('delivery_type', 'door')
    dd_instructions = data.get('drop_instructions')
    dd_lat = data.get('drop_latitude')
    dd_lng = data.get('drop_longitude')
    dd_media = data.get('drop_media')

    # Calculate final amount after bonus
    final_amount = total_amount - bonus_applied

    # Get Bitcoin address
    btc_address = get_available_bitcoin_address()

    if not btc_address:
        await message.answer(
            localize("order.payment.system_unavailable"),
            reply_markup=back("back_to_menu")
        )
        return

    # Get customer info
    with Database().session() as session:
        customer_info = session.query(CustomerInfo).filter_by(
            telegram_id=user_id
        ).first()

        if not customer_info:
            await message.answer(
                localize("order.payment.customer_not_found"),
                reply_markup=back("view_cart")
            )
            return

        # Deduct bonus from customer's bonus_balance if applied
        if bonus_applied > 0:
            if customer_info.bonus_balance < bonus_applied:
                await message.answer(
                    localize("order.bonus.insufficient"),
                    reply_markup=back("view_cart")
                )
                return
            customer_info.bonus_balance -= bonus_applied

        # Create one order for entire cart
        try:
            items_summary = []

            # Create the main order
            order = Order(
                buyer_id=user_id,
                total_price=Decimal(str(total_amount)),
                bonus_applied=bonus_applied,
                payment_method="bitcoin",
                delivery_address=customer_info.delivery_address,
                phone_number=customer_info.phone_number,
                delivery_note=customer_info.delivery_note or "",
                bitcoin_address=btc_address,
                order_status="pending",
                latitude=customer_info.latitude,
                longitude=customer_info.longitude,
                google_maps_link=f"https://www.google.com/maps?q={customer_info.latitude},{customer_info.longitude}" if customer_info.latitude else None,
                delivery_type=dd_type,
                drop_instructions=dd_instructions,
                drop_latitude=dd_lat,
                drop_longitude=dd_lng,
                drop_media=dd_media,
            )
            session.add(order)
            session.flush()  # Get the order ID

            # Generate unique order code
            order.order_code = generate_unique_order_code(session)

            # Process each cart item and create OrderItems
            items_to_reserve = []
            for cart_item in cart_items:
                item_name = cart_item['item_name']
                quantity = cart_item['quantity']
                price = cart_item['price']

                # Create OrderItem (without item_values - physical goods)
                order_item = OrderItem(
                    order_id=order.id,
                    item_name=item_name,
                    price=Decimal(str(price)),
                    quantity=quantity,
                    selected_modifiers=cart_item.get('selected_modifiers')
                )
                session.add(order_item)

                items_summary.append(f"{item_name} x{quantity} = {cart_item['total']} {EnvKeys.PAY_CURRENCY}")

                # Prepare for inventory reservation
                items_to_reserve.append({
                    'item_name': item_name,
                    'quantity': quantity
                })

            # Reserve inventory for this order (extended timeout for bitcoin - 7 days)
            success, reserve_message = reserve_inventory(order.id, items_to_reserve, payment_method='bitcoin',
                                                         session=session)
            if not success:
                session.rollback()
                await message.answer(
                    localize("order.inventory.unable_to_reserve", unavailable_items=reserve_message),
                    reply_markup=back("view_cart")
                )
                return

            # Mark Bitcoin address as used with this order
            mark_bitcoin_address_used(btc_address, user_id, username, order.id, session=session,
                                      order_code=order.order_code)

            # Log order creation
            log_order_creation(
                order_id=order.id,
                buyer_id=user_id,
                buyer_username=username,
                items_summary="\n".join(items_summary),
                total_price=float(total_amount),
                payment_method="bitcoin",
                delivery_address=customer_info.delivery_address,
                phone_number=customer_info.phone_number,
                bitcoin_address=btc_address,
                order_code=order.order_code
            )

            # Clear cart
            session.query(ShoppingCart).filter_by(user_id=user_id).delete()

            session.commit()

            # Track order creation metrics
            metrics = get_metrics()
            if metrics:
                metrics.track_event("order_created", user_id, {
                    "order_code": order.order_code,
                    "payment_method": "bitcoin",
                    "total": float(total_amount),
                    "bonus_applied": float(bonus_applied)
                })
                # Track inventory reservation
                for item in items_to_reserve:
                    metrics.track_event("inventory_reserved", user_id, {
                        "item": item['item_name'],
                        "quantity": item['quantity'],
                        "order_code": order.order_code
                    })
                # Track bonus usage if applied
                if bonus_applied > 0:
                    metrics.track_event("payment_bonus_applied", user_id, {
                        "bonus_amount": float(bonus_applied),
                        "order_code": order.order_code
                    })

            # Send payment instructions to user
            payment_text = (
                    localize("order.payment.bitcoin.title") + "\n\n" +
                    localize("order.payment.bitcoin.order_code", code=order.order_code) + "\n" +
                    localize("order.payment.subtotal_label", amount=total_amount, currency=EnvKeys.PAY_CURRENCY) + "\n"
            )

            if bonus_applied > 0:
                payment_text += (
                        localize("order.payment.bonus_applied_label", amount=bonus_applied,
                                 currency=EnvKeys.PAY_CURRENCY) + "\n" +
                        localize("order.payment.final_amount_label", amount=final_amount,
                                 currency=EnvKeys.PAY_CURRENCY) + "\n\n"
                )
            else:
                payment_text += localize("order.payment.total_amount_label", amount=total_amount,
                                         currency=EnvKeys.PAY_CURRENCY) + "\n\n"

            payment_text += (
                    localize("order.payment.bitcoin.items_title") + "\n"
                                                                    f"{chr(10).join(items_summary)}\n\n" +
                    localize("order.payment.bitcoin.delivery_title") + "\n"
                                                                       f"📍 Address: {customer_info.delivery_address}\n"
                                                                       f"📞 Phone: {customer_info.phone_number}\n"
            )

            if customer_info.delivery_note:
                payment_text += f"📝 Note: {customer_info.delivery_note}\n"

            payment_text += (
                    "\n" + localize("order.payment.bitcoin.address_title") + "\n"
                                                                             f"<code>{btc_address}</code>\n\n" +
                    localize("order.payment.bitcoin.important_title") + "\n" +
                    localize("order.payment.bitcoin.send_exact") + "\n" +
                    localize("order.payment.bitcoin.one_time_address") + "\n" +
                    localize("order.payment.bitcoin.admin_confirm") + "\n\n" +
                    localize("order.payment.bitcoin.need_help")
            )

            await message.answer(
                payment_text,
                reply_markup=back("back_to_menu")
            )

            # Notify admin
            await notify_admin_new_order(
                message.bot, order.order_code, user_id, username,
                "\n".join(items_summary), total_amount, btc_address,
                customer_info.delivery_address, customer_info.phone_number,
                customer_info.delivery_note or "", bonus_applied, final_amount
            )

            # Sync customer CSV
            sync_customer_to_csv(user_id, username)

            await state.clear()

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating orders: {e}")
            await message.answer(
                localize("order.payment.error_general"),
                reply_markup=back("view_cart")
            )
            return


async def process_cash_payment_new_message(message: Message, state: FSMContext, user_id: int = None):
    """
    Process Cash on Delivery payment by sending a new message
    """
    if user_id is None:
        user_id = message.from_user.id

    # Get real username from Telegram API
    username = await get_telegram_username(user_id, message.bot)

    # Get cart items
    cart_items = await get_cart_items(user_id)

    if not cart_items:
        await message.answer(localize("cart.empty_alert"), reply_markup=back("shop"))
        return

    # Calculate total
    total_amount = await calculate_cart_total(user_id)

    # Get state data (bonus + dead drop fields)
    data = await state.get_data()
    bonus_applied = Decimal(str(data.get('bonus_applied', 0)))
    dd_type = data.get('delivery_type', 'door')
    dd_instructions = data.get('drop_instructions')
    dd_lat = data.get('drop_latitude')
    dd_lng = data.get('drop_longitude')
    dd_media = data.get('drop_media')

    # Calculate final amount after bonus
    final_amount = total_amount - bonus_applied

    # Get customer info
    with Database().session() as session:
        customer_info = session.query(CustomerInfo).filter_by(
            telegram_id=user_id
        ).first()

        if not customer_info:
            await message.answer(
                localize("order.payment.customer_not_found"),
                reply_markup=back("view_cart")
            )
            return

        # Deduct bonus from customer's bonus_balance if applied
        if bonus_applied > 0:
            if customer_info.bonus_balance < bonus_applied:
                await message.answer(
                    localize("order.bonus.insufficient"),
                    reply_markup=back("view_cart")
                )
                return
            customer_info.bonus_balance -= bonus_applied

        # Create one order for entire cart
        try:
            items_summary = []

            # Create the main order (cash payment - no Bitcoin address)
            order = Order(
                buyer_id=user_id,
                total_price=Decimal(str(total_amount)),
                bonus_applied=bonus_applied,
                payment_method="cash",
                delivery_address=customer_info.delivery_address,
                phone_number=customer_info.phone_number,
                delivery_note=customer_info.delivery_note or "",
                bitcoin_address=None,  # No Bitcoin address for cash
                order_status="pending",
                latitude=customer_info.latitude,
                longitude=customer_info.longitude,
                google_maps_link=f"https://www.google.com/maps?q={customer_info.latitude},{customer_info.longitude}" if customer_info.latitude else None,
                delivery_type=dd_type,
                drop_instructions=dd_instructions,
                drop_latitude=dd_lat,
                drop_longitude=dd_lng,
                drop_media=dd_media,
            )
            session.add(order)
            session.flush()  # Get the order ID

            # Generate unique order code
            order.order_code = generate_unique_order_code(session)

            # Process each cart item and create OrderItems
            items_to_reserve = []
            for cart_item in cart_items:
                item_name = cart_item['item_name']
                quantity = cart_item['quantity']
                price = cart_item['price']

                # Create OrderItem (without item_values - physical goods)
                order_item = OrderItem(
                    order_id=order.id,
                    item_name=item_name,
                    price=Decimal(str(price)),
                    quantity=quantity,
                    selected_modifiers=cart_item.get('selected_modifiers')
                )
                session.add(order_item)

                items_summary.append(f"{item_name} x{quantity} = {cart_item['total']} {EnvKeys.PAY_CURRENCY}")

                # Prepare for inventory reservation
                items_to_reserve.append({
                    'item_name': item_name,
                    'quantity': quantity
                })

            # Reserve inventory for this order (configurable timeout for cash - default 24 hours)
            success, reserve_message = reserve_inventory(order.id, items_to_reserve, payment_method='cash',
                                                         session=session)
            if not success:
                session.rollback()
                await message.answer(
                    localize("order.inventory.unable_to_reserve", unavailable_items=reserve_message),
                    reply_markup=back("view_cart")
                )
                return

            # Log order creation
            log_order_creation(
                order_id=order.id,
                buyer_id=user_id,
                buyer_username=username,
                items_summary="\n".join(items_summary),
                total_price=float(total_amount),
                payment_method="cash",
                delivery_address=customer_info.delivery_address,
                phone_number=customer_info.phone_number,
                bitcoin_address=None,
                order_code=order.order_code
            )

            # Clear cart
            session.query(ShoppingCart).filter_by(user_id=user_id).delete()

            session.commit()

            # Track order creation metrics
            metrics = get_metrics()
            if metrics:
                metrics.track_event("order_created", user_id, {
                    "order_code": order.order_code,
                    "payment_method": "cash",
                    "total": float(total_amount),
                    "bonus_applied": float(bonus_applied)
                })
                # Track inventory reservation
                for item in items_to_reserve:
                    metrics.track_event("inventory_reserved", user_id, {
                        "item": item['item_name'],
                        "quantity": item['quantity'],
                        "order_code": order.order_code
                    })
                # Track bonus usage if applied
                if bonus_applied > 0:
                    metrics.track_event("payment_bonus_applied", user_id, {
                        "bonus_amount": float(bonus_applied),
                        "order_code": order.order_code
                    })

            cash_instructions = (
                    localize("order.payment.cash.title") + "\n\n" +
                    localize("order.payment.cash.created", code=order.order_code) + "\n\n" +
                    localize("order.payment.cash.items_title") + "\n" + chr(10).join(items_summary) + "\n\n" + localize(
                "order.payment.cash.total", amount=float(total_amount)) + "\n\n" +
                    localize("order.payment.cash.after_confirm") + "\n" +
                    localize("order.payment.cash.payment_to_courier") + "\n\n" +
                    localize("order.payment.cash.important") + "\n" +
                    localize("order.payment.cash.admin_contact")
            )

            # Send payment instructions to user
            payment_text = (
                    f"{cash_instructions}\n\n" +
                    localize("order.payment.order_label", code=order.order_code) + "\n" +
                    localize("order.payment.subtotal_label", amount=total_amount, currency=EnvKeys.PAY_CURRENCY) + "\n"
            )

            if bonus_applied > 0:
                payment_text += (
                        localize("order.payment.bonus_applied_label", amount=bonus_applied,
                                 currency=EnvKeys.PAY_CURRENCY) + "\n" +
                        localize("order.payment.cash.amount_with_bonus", amount=final_amount,
                                 currency=EnvKeys.PAY_CURRENCY) + "\n\n"
                )
            else:
                payment_text += localize("order.payment.cash.total_label", amount=total_amount,
                                         currency=EnvKeys.PAY_CURRENCY) + "\n\n"

            payment_text += (
                    localize("order.payment.bitcoin.items_title") + "\n"
                                                                    f"{chr(10).join(items_summary)}\n\n" +
                    localize("order.payment.bitcoin.delivery_title") + "\n"
                                                                       f"📍 Address: {customer_info.delivery_address}\n"
                                                                       f"📞 Phone: {customer_info.phone_number}\n"
            )

            if customer_info.delivery_note:
                payment_text += f"📝 Note: {customer_info.delivery_note}\n"

            payment_text += (
                    "\n" + localize("order.info.view_status_hint")
            )

            await message.answer(
                payment_text,
                reply_markup=back("back_to_menu")
            )

            # Notify admin about new cash order
            await notify_admin_new_cash_order(
                message.bot, order.order_code, user_id, username,
                "\n".join(items_summary), total_amount,
                customer_info.delivery_address, customer_info.phone_number,
                customer_info.delivery_note or "", bonus_applied, final_amount
            )

            # Sync customer CSV
            sync_customer_to_csv(user_id, username)

            await state.clear()

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating cash order: {e}")
            await message.answer(
                localize("order.payment.error_general"),
                reply_markup=back("view_cart")
            )
            return


async def process_promptpay_payment(message: Message, state: FSMContext, user_id: int = None):
    """
    Process PromptPay payment: generate QR, create order, ask for receipt (Card 1)
    """
    from bot.payments.promptpay import generate_promptpay_qr

    if user_id is None:
        user_id = message.from_user.id

    username = await get_telegram_username(user_id, message.bot)
    cart_items = await get_cart_items(user_id)

    if not cart_items:
        await message.answer(localize("cart.empty_alert"), reply_markup=back("shop"))
        return

    total_amount = await calculate_cart_total(user_id)
    data = await state.get_data()
    bonus_applied = Decimal(str(data.get('bonus_applied', 0)))
    dd_type = data.get('delivery_type', 'door')
    dd_instructions = data.get('drop_instructions')
    dd_lat = data.get('drop_latitude')
    dd_lng = data.get('drop_longitude')
    dd_media = data.get('drop_media')
    final_amount = total_amount - bonus_applied

    with Database().session() as session:
        customer_info = session.query(CustomerInfo).filter_by(telegram_id=user_id).first()
        if not customer_info:
            await message.answer(localize("order.payment.customer_not_found"), reply_markup=back("view_cart"))
            return

        if bonus_applied > 0:
            if customer_info.bonus_balance < bonus_applied:
                await message.answer(localize("order.bonus.insufficient"), reply_markup=back("view_cart"))
                return
            customer_info.bonus_balance -= bonus_applied

        try:
            items_summary = []
            order = Order(
                buyer_id=user_id,
                total_price=Decimal(str(total_amount)),
                bonus_applied=bonus_applied,
                payment_method="promptpay",
                delivery_address=customer_info.delivery_address,
                phone_number=customer_info.phone_number,
                delivery_note=customer_info.delivery_note or "",
                order_status="pending",
                latitude=customer_info.latitude,
                longitude=customer_info.longitude,
                google_maps_link=f"https://www.google.com/maps?q={customer_info.latitude},{customer_info.longitude}" if customer_info.latitude else None,
                delivery_type=dd_type,
                drop_instructions=dd_instructions,
                drop_latitude=dd_lat,
                drop_longitude=dd_lng,
                drop_media=dd_media,
            )
            session.add(order)
            session.flush()

            order.order_code = generate_unique_order_code(session)

            items_to_reserve = []
            for cart_item in cart_items:
                item_name = cart_item['item_name']
                quantity = cart_item['quantity']
                price = cart_item['price']

                order_item = OrderItem(
                    order_id=order.id,
                    item_name=item_name,
                    price=Decimal(str(price)),
                    quantity=quantity,
                    selected_modifiers=cart_item.get('selected_modifiers')
                )
                session.add(order_item)
                items_summary.append(f"{item_name} x{quantity} = {cart_item['total']} {EnvKeys.PAY_CURRENCY}")
                items_to_reserve.append({'item_name': item_name, 'quantity': quantity})

            success, reserve_message = reserve_inventory(order.id, items_to_reserve, payment_method='promptpay',
                                                          session=session)
            if not success:
                session.rollback()
                await message.answer(
                    localize("order.inventory.unable_to_reserve", unavailable_items=reserve_message),
                    reply_markup=back("view_cart")
                )
                return

            log_order_creation(
                order_id=order.id, buyer_id=user_id, buyer_username=username,
                items_summary="\n".join(items_summary), total_price=float(total_amount),
                payment_method="promptpay", delivery_address=customer_info.delivery_address,
                phone_number=customer_info.phone_number, bitcoin_address=None,
                order_code=order.order_code
            )

            session.query(ShoppingCart).filter_by(user_id=user_id).delete()
            session.commit()

            # Generate QR code — DB setting overrides env var
            from bot.handlers.admin.settings_management import get_promptpay_id as _get_pp_id
            promptpay_id = _get_pp_id()
            try:
                qr_bytes = generate_promptpay_qr(promptpay_id, final_amount)

                from aiogram.types import BufferedInputFile
                qr_file = BufferedInputFile(qr_bytes, filename=f"promptpay_{order.order_code}.png")

                caption = (
                    localize("order.payment.promptpay.title") + "\n\n" +
                    localize("order.payment.promptpay.scan") + "\n" +
                    f"<b>{EnvKeys.PAY_CURRENCY} {final_amount}</b>\n" +
                    f"Order: <code>{order.order_code}</code>"
                )

                await message.answer_photo(photo=qr_file, caption=caption)
            except Exception as qr_error:
                logger.error(f"QR generation failed: {qr_error}")
                await message.answer(
                    localize("order.payment.promptpay.title") + "\n\n" +
                    f"PromptPay ID: <code>{promptpay_id}</code>\n" +
                    f"Amount: <b>{final_amount} {EnvKeys.PAY_CURRENCY}</b>\n" +
                    f"Order: <code>{order.order_code}</code>"
                )

            # Ask user to upload receipt
            await message.answer(
                localize("order.payment.promptpay.upload_receipt"),
                reply_markup=back("back_to_menu")
            )

            # Save order_id in state for receipt association
            await state.update_data(promptpay_order_id=order.id, promptpay_order_code=order.order_code)
            await state.set_state(PromptPayStates.waiting_receipt_photo)

            # Notify admin
            await notify_admin_new_cash_order(
                message.bot, order.order_code, user_id, username,
                "\n".join(items_summary), total_amount,
                customer_info.delivery_address, customer_info.phone_number,
                customer_info.delivery_note or "", bonus_applied, final_amount
            )

            sync_customer_to_csv(user_id, username)

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating PromptPay order: {e}")
            await message.answer(localize("order.payment.error_general"), reply_markup=back("view_cart"))
            return


@router.message(PromptPayStates.waiting_receipt_photo, F.photo)
async def process_receipt_photo(message: Message, state: FSMContext):
    """User uploaded payment receipt photo (Card 1) — with optional auto-verification"""
    photo_file_id = message.photo[-1].file_id
    data = await state.get_data()
    order_id = data.get('promptpay_order_id')

    if order_id:
        with Database().session() as session:
            order = session.query(Order).filter_by(id=order_id).first()
            if order:
                order.payment_receipt_photo = photo_file_id
                session.commit()

                # Attempt auto-verification via bank APIs
                verify_result = None
                if EnvKeys.SLIP_AUTO_VERIFY == "1":
                    try:
                        from bot.payments.slip_verify import verify_slip, VerifyStatus

                        # Download the photo from Telegram
                        file_obj = await message.bot.get_file(photo_file_id)
                        photo_bytes_io = await message.bot.download_file(file_obj.file_path)
                        slip_image = photo_bytes_io.read()

                        # Calculate expected amount (total - bonus)
                        expected_amount = order.total_price - (order.bonus_applied or Decimal('0'))

                        from bot.handlers.admin.settings_management import get_promptpay_name as _get_pp_name
                        verify_result = await verify_slip(
                            slip_image=slip_image,
                            expected_amount=expected_amount,
                            expected_receiver=_get_pp_name() or None,
                        )

                        # Save verification result to order
                        import datetime as dt
                        order.slip_verify_status = verify_result.status.value
                        order.slip_verify_bank = verify_result.provider.value if verify_result.provider else None
                        order.slip_transaction_id = verify_result.transaction_id
                        order.slip_verified_amount = verify_result.amount
                        order.slip_sender_name = verify_result.sender_name
                        order.slip_receiver_name = verify_result.receiver_name
                        order.slip_verified_at = dt.datetime.now(dt.timezone.utc)

                        if verify_result.status == VerifyStatus.VERIFIED:
                            # Auto-confirm the payment
                            order.payment_verified_at = dt.datetime.now(dt.timezone.utc)
                            order.payment_verified_by = 0  # 0 = auto-verified by API
                            order.order_status = "confirmed"
                            logger.info(
                                "Order %s auto-verified via %s (txn: %s)",
                                order.order_code, verify_result.provider.value, verify_result.transaction_id,
                            )

                        session.commit()

                    except Exception as e:
                        logger.error(f"Slip auto-verification error for order {order.order_code}: {e}")

                # Build admin notification caption
                admin_caption = (
                    f"💳 <b>PromptPay Receipt</b>\n"
                    f"Order: <code>{order.order_code}</code>\n"
                    f"Amount: {order.total_price} {EnvKeys.PAY_CURRENCY}\n"
                    f"From: {message.from_user.id}"
                )

                if verify_result:
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


async def notify_admin_new_order(bot, order_code: str, buyer_id: int, buyer_username: str,
                                 items_summary: str, total_amount: Decimal, btc_address: str,
                                 delivery_address: str, phone_number: str, delivery_note: str,
                                 bonus_applied: Decimal = Decimal('0'), final_amount: Decimal = None):
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
                localize("admin.order.new_bitcoin_order") + "\n\n" +
                localize("admin.order.order_label", code=html.escape(order_code)) + "\n" +
                localize("admin.order.customer_label", username=html.escape(buyer_username), id=buyer_id) + "\n" +
                localize("admin.order.subtotal_label", amount=html.escape(str(total_amount)),
                         currency=html.escape(EnvKeys.PAY_CURRENCY)) + "\n"
        )

        if bonus_applied > 0:
            admin_text += (
                    localize("admin.order.bonus_applied_label", amount=html.escape(str(bonus_applied))) + "\n" +
                    localize("admin.order.amount_to_receive_label", amount=html.escape(str(final_amount)),
                             currency=html.escape(EnvKeys.PAY_CURRENCY)) + "\n\n"
            )
        else:
            admin_text += f"<b>Total: ${html.escape(str(total_amount))} {html.escape(EnvKeys.PAY_CURRENCY)}</b>\n\n"

        admin_text += (
                localize("order.payment.bitcoin.items_title") + "\n"
                                                                f"{html.escape(items_summary)}\n\n" +
                localize("order.payment.bitcoin.delivery_title") + "\n"
                                                                   f"📍 Address: {html.escape(delivery_address)}\n"
                                                                   f"📞 Phone: {html.escape(phone_number)}\n"
        )

        if delivery_note:
            admin_text += f"📝 Note: {html.escape(delivery_note)}\n"

        admin_text += (
                f"\n<b>Payment:</b>\n" +
                localize("admin.order.bitcoin_address_label", address=html.escape(btc_address)) + "\n\n" +
                localize("admin.order.awaiting_payment_status")
        )

        await bot.send_message(
            int(owner_id),
            admin_text
        )

    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")


async def notify_admin_new_cash_order(bot, order_code: str, buyer_id: int, buyer_username: str,
                                      items_summary: str, total_amount: Decimal,
                                      delivery_address: str, phone_number: str, delivery_note: str,
                                      bonus_applied: Decimal = Decimal('0'), final_amount: Decimal = None):
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
                localize("admin.order.new_cash_order") + "\n\n" +
                localize("admin.order.order_label", code=html.escape(order_code)) + "\n" +
                localize("admin.order.customer_label", username=html.escape(buyer_username), id=buyer_id) + "\n" +
                localize("admin.order.payment_method_label", method=localize("admin.order.payment_cash")) + "\n" +
                localize("admin.order.subtotal_label", amount=html.escape(str(total_amount)),
                         currency=html.escape(EnvKeys.PAY_CURRENCY)) + "\n"
        )

        if bonus_applied > 0:
            admin_text += (
                    localize("admin.order.bonus_applied_label", amount=html.escape(str(bonus_applied))) + "\n" +
                    localize("admin.order.amount_to_collect_label", amount=html.escape(str(final_amount)),
                             currency=html.escape(
                                 EnvKeys.PAY_CURRENCY)) + "\n\n"
            )
        else:
            admin_text += f"<b>Amount to Collect: ${html.escape(str(total_amount))} {html.escape(EnvKeys.PAY_CURRENCY)}</b>\n\n"

        admin_text += (
                localize("order.payment.bitcoin.items_title") + "\n"
                                                                f"{html.escape(items_summary)}\n\n" +
                localize("order.payment.bitcoin.delivery_title") + "\n"
                                                                   f"📍 Address: {html.escape(delivery_address)}\n"
                                                                   f"📞 Phone: {html.escape(phone_number)}\n"
        )

        if delivery_note:
            admin_text += f"📝 Note: {html.escape(delivery_note)}\n"

        admin_text += (
                "\n" + localize("admin.order.action_required_title") + "\n" +
                localize("admin.order.use_cli_confirm", code=html.escape(order_code)))

        await bot.send_message(
            int(owner_id),
            admin_text
        )

    except Exception as e:
        logger.error(f"Failed to send admin notification for cash order: {e}")
