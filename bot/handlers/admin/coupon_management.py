"""
Admin Coupon Management Handler.

Provides:
- Coupon management menu (create, list active, list all)
- Multi-step coupon creation via FSM
- Toggle coupon active/inactive status
- View coupon details with usage stats
"""
import random
import string
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from aiogram import Router, F
from aiogram.filters.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database import Database
from bot.database.models.main import Coupon, CouponUsage, Permission
from bot.filters import HasPermissionFilter
from bot.i18n import localize
from bot.keyboards.inline import back, simple_buttons

router = Router()

PAGE_SIZE = 10


# ── FSM States ───────────────────────────────────────────────────────

class CouponAdminStates(StatesGroup):
    waiting_code = State()
    waiting_discount_type = State()
    waiting_discount_value = State()
    waiting_min_order = State()
    waiting_max_uses = State()
    waiting_expiry = State()


def _generate_code(length: int = 8) -> str:
    """Generate a random uppercase alphanumeric coupon code."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


def _format_coupon_line(c: Coupon) -> str:
    """Format a single coupon for list display."""
    status = "Active" if c.is_active else "Inactive"
    if c.discount_type == "percent":
        discount_str = f"{c.discount_value}%"
    else:
        discount_str = f"${c.discount_value}"
    uses_str = f"{c.current_uses}/{c.max_uses}" if c.max_uses else f"{c.current_uses}/Unlimited"
    return f"<code>{c.code}</code> - {discount_str} [{status}] ({uses_str})"


# ── Management menu ──────────────────────────────────────────────────

@router.callback_query(F.data == "coupon_management", HasPermissionFilter(permission=Permission.SHOP_MANAGE))
async def coupon_management(call: CallbackQuery, state: FSMContext):
    """Show coupon management menu."""
    await state.clear()
    actions = [
        (localize("admin.coupon.create"), "admin_create_coupon"),
        (localize("admin.coupon.list_active"), "admin_list_coupons_active"),
        (localize("admin.coupon.list_all"), "admin_list_coupons_all"),
        (localize("btn.back"), "console"),
    ]
    await call.message.edit_text(
        localize("admin.coupon.title"),
        reply_markup=simple_buttons(actions, per_row=1),
    )


# ── Coupon creation flow ─────────────────────────────────────────────

@router.callback_query(F.data == "admin_create_coupon", HasPermissionFilter(permission=Permission.SHOP_MANAGE))
async def create_coupon_start(call: CallbackQuery, state: FSMContext):
    """Step 1: Ask for coupon code."""
    await state.clear()
    await state.update_data(creator_id=call.from_user.id)
    await call.message.edit_text(
        localize("admin.coupon.enter_code"),
        reply_markup=back("coupon_management"),
    )
    await state.set_state(CouponAdminStates.waiting_code)


@router.message(CouponAdminStates.waiting_code, F.text)
async def process_coupon_code(message: Message, state: FSMContext):
    """Process coupon code input. 'random' or 'auto' generates one automatically.
    LOGIC-39 fix: Added F.text filter to prevent crash on non-text messages."""
    text = message.text.strip()

    if text.lower() in ("random", "auto"):
        code = _generate_code()
    else:
        code = text.upper()
        if len(code) > 32:
            await message.answer(localize("admin.coupon.code_too_long"))
            return
        # Check uniqueness
        with Database().session() as session:
            existing = session.query(Coupon).filter(Coupon.code == code).first()
            if existing:
                await message.answer(localize("admin.coupon.code_exists"))
                return

    await state.update_data(code=code)
    actions = [
        (localize("admin.coupon.type_percent"), "coupon_type_percent"),
        (localize("admin.coupon.type_fixed"), "coupon_type_fixed"),
        (localize("btn.back"), "coupon_management"),
    ]
    await message.answer(
        localize("admin.coupon.choose_type").format(code=code),
        reply_markup=simple_buttons(actions, per_row=2),
    )
    await state.set_state(CouponAdminStates.waiting_discount_type)


@router.callback_query(CouponAdminStates.waiting_discount_type, F.data.startswith("coupon_type_"))
async def process_discount_type(call: CallbackQuery, state: FSMContext):
    """Step 2: Choose discount type (percent or fixed)."""
    discount_type = call.data.replace("coupon_type_", "")  # 'percent' or 'fixed'
    await state.update_data(discount_type=discount_type)

    if discount_type == "percent":
        prompt = localize("admin.coupon.enter_percent_value")
    else:
        prompt = localize("admin.coupon.enter_fixed_value")

    await call.message.edit_text(
        prompt,
        reply_markup=back("coupon_management"),
    )
    await state.set_state(CouponAdminStates.waiting_discount_value)


@router.message(CouponAdminStates.waiting_discount_value, F.text)
async def process_discount_value(message: Message, state: FSMContext):
    """Step 3: Enter discount value."""
    try:
        value = Decimal(message.text.strip())
        if value <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer(localize("admin.coupon.invalid_value"))
        return

    data = await state.get_data()
    if data["discount_type"] == "percent" and value > 100:
        await message.answer(localize("admin.coupon.percent_max"))
        return

    await state.update_data(discount_value=str(value))
    await message.answer(
        localize("admin.coupon.enter_min_order"),
        reply_markup=back("coupon_management"),
    )
    await state.set_state(CouponAdminStates.waiting_min_order)


@router.message(CouponAdminStates.waiting_min_order, F.text)
async def process_min_order(message: Message, state: FSMContext):
    """Step 4: Enter minimum order amount or skip."""
    text = message.text.strip().lower()

    if text in ("skip", "0", "-"):
        min_order = Decimal("0")
    else:
        try:
            min_order = Decimal(text)
            if min_order < 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            await message.answer(localize("admin.coupon.invalid_value"))
            return

    await state.update_data(min_order=str(min_order))
    await message.answer(
        localize("admin.coupon.enter_max_uses"),
        reply_markup=back("coupon_management"),
    )
    await state.set_state(CouponAdminStates.waiting_max_uses)


@router.message(CouponAdminStates.waiting_max_uses, F.text)
async def process_max_uses(message: Message, state: FSMContext):
    """Step 5: Enter max total uses or skip for unlimited."""
    text = message.text.strip().lower()

    if text in ("skip", "-", "unlimited"):
        max_uses = None
    else:
        try:
            max_uses = int(text)
            if max_uses <= 0:
                raise ValueError
        except ValueError:
            await message.answer(localize("admin.coupon.invalid_uses"))
            return

    await state.update_data(max_uses=max_uses)
    await message.answer(
        localize("admin.coupon.enter_expiry"),
        reply_markup=back("coupon_management"),
    )
    await state.set_state(CouponAdminStates.waiting_expiry)


@router.message(CouponAdminStates.waiting_expiry, F.text)
async def process_expiry(message: Message, state: FSMContext):
    """Step 6: Enter expiry in days or skip for no expiry. Then save."""
    text = message.text.strip().lower()

    if text in ("skip", "-", "never", "0"):
        valid_until = None
    else:
        try:
            days = int(text)
            if days <= 0:
                raise ValueError
            valid_until = datetime.now(timezone.utc) + timedelta(days=days)
        except ValueError:
            await message.answer(localize("admin.coupon.invalid_expiry"))
            return

    data = await state.get_data()

    # Save to database
    with Database().session() as session:
        coupon = Coupon(
            code=data["code"],
            discount_type=data["discount_type"],
            discount_value=Decimal(data["discount_value"]),
            min_order=Decimal(data.get("min_order", "0")),
            max_uses=data.get("max_uses"),
            valid_from=datetime.now(timezone.utc),
            valid_until=valid_until,
            created_by=data.get("creator_id"),
        )
        session.add(coupon)
        session.commit()

    await state.clear()

    # Build summary
    discount_str = (
        f"{data['discount_value']}%"
        if data["discount_type"] == "percent"
        else f"${data['discount_value']}"
    )
    max_uses_str = str(data.get("max_uses")) if data.get("max_uses") else "Unlimited"
    expiry_str = valid_until.strftime("%Y-%m-%d %H:%M UTC") if valid_until else "Never"

    summary = localize("admin.coupon.created_summary").format(
        code=data["code"],
        discount=discount_str,
        min_order=data.get("min_order", "0"),
        max_uses=max_uses_str,
        expiry=expiry_str,
    )

    await message.answer(
        summary,
        reply_markup=back("coupon_management"),
    )


# ── List coupons ─────────────────────────────────────────────────────

@router.callback_query(F.data.in_({"admin_list_coupons_active", "admin_list_coupons_all"}),
                       HasPermissionFilter(permission=Permission.SHOP_MANAGE))
async def admin_list_coupons(call: CallbackQuery, state: FSMContext):
    """List coupons with usage stats."""
    active_only = call.data == "admin_list_coupons_active"

    with Database().session() as session:
        query = session.query(Coupon).order_by(Coupon.created_at.desc())
        if active_only:
            query = query.filter(Coupon.is_active.is_(True))
        coupons = query.limit(PAGE_SIZE).all()

    if not coupons:
        await call.message.edit_text(
            localize("admin.coupon.list_empty"),
            reply_markup=back("coupon_management"),
        )
        return

    lines = [localize("admin.coupon.list_header")]
    actions = []
    for c in coupons:
        lines.append(_format_coupon_line(c))
        actions.append((f"{c.code}", f"admin_view_coupon_{c.id}"))

    actions.append((localize("btn.back"), "coupon_management"))

    await call.message.edit_text(
        "\n".join(lines),
        reply_markup=simple_buttons(actions, per_row=2),
    )


# ── View coupon details ──────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_view_coupon_"), HasPermissionFilter(permission=Permission.SHOP_MANAGE))
async def admin_view_coupon(call: CallbackQuery, state: FSMContext):
    """View coupon details and usage count."""
    try:
        coupon_id = int(call.data.replace("admin_view_coupon_", ""))
    except (ValueError, TypeError):
        await call.answer("Invalid coupon", show_alert=True)
        return

    with Database().session() as session:
        coupon = session.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            await call.answer(localize("admin.coupon.not_found"), show_alert=True)
            return

        usage_count = session.query(CouponUsage).filter(CouponUsage.coupon_id == coupon_id).count()

        # Build detail text
        if coupon.discount_type == "percent":
            discount_str = f"{coupon.discount_value}%"
            if coupon.max_discount:
                discount_str += f" (max ${coupon.max_discount})"
        else:
            discount_str = f"${coupon.discount_value}"

        uses_str = f"{coupon.current_uses}/{coupon.max_uses}" if coupon.max_uses else f"{coupon.current_uses}/Unlimited"
        expiry_str = coupon.valid_until.strftime("%Y-%m-%d %H:%M UTC") if coupon.valid_until else "Never"
        status = "Active" if coupon.is_active else "Inactive"
        min_order_str = f"${coupon.min_order}" if coupon.min_order else "None"

        detail = localize("admin.coupon.detail").format(
            code=coupon.code,
            status=status,
            discount=discount_str,
            min_order=min_order_str,
            uses=uses_str,
            usage_count=usage_count,
            per_user=coupon.max_uses_per_user,
            expiry=expiry_str,
            created_at=coupon.created_at.strftime("%Y-%m-%d %H:%M UTC") if coupon.created_at else "N/A",
            note=coupon.note or "-",
        )

        toggle_label = localize("admin.coupon.deactivate") if coupon.is_active else localize("admin.coupon.activate")

    actions = [
        (toggle_label, f"admin_toggle_coupon_{coupon_id}"),
        (localize("btn.back"), "coupon_management"),
    ]

    await call.message.edit_text(
        detail,
        reply_markup=simple_buttons(actions, per_row=1),
    )


# ── Toggle coupon active status ──────────────────────────────────────

@router.callback_query(F.data.startswith("admin_toggle_coupon_"), HasPermissionFilter(permission=Permission.SHOP_MANAGE))
async def admin_toggle_coupon(call: CallbackQuery, state: FSMContext):
    """Activate or deactivate a coupon."""
    try:
        coupon_id = int(call.data.replace("admin_toggle_coupon_", ""))
    except (ValueError, TypeError):
        await call.answer("Invalid coupon", show_alert=True)
        return

    with Database().session() as session:
        coupon = session.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            await call.answer(localize("admin.coupon.not_found"), show_alert=True)
            return

        coupon.is_active = not coupon.is_active
        new_status = "active" if coupon.is_active else "inactive"
        session.commit()

    await call.answer(
        localize("admin.coupon.toggled").format(code=coupon.code, status=new_status),
        show_alert=True,
    )

    # Refresh the detail view
    call.data = f"admin_view_coupon_{coupon_id}"
    await admin_view_coupon(call, state)
