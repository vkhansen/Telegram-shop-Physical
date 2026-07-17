import os
from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.database.methods import check_role
from bot.database.models.main import Permission
from bot.keyboards import back, reference_code_admin_keyboard
from bot.keyboards.inline import InlineKeyboardBuilder
from bot.monitoring import get_metrics
from bot.referrals import create_reference_code
from bot.referrals.invite_card_sheet import export_branded_sheet, list_brands_for_admin
from bot.referrals.invite_cards import (
    assign_invite_cards_bulk,
    create_invite_card_batch,
    format_invite_card_registry,
    list_invite_cards,
    qr_png_bytes,
    telegram_start_link,
)
from bot.states.user_state import ReferenceCodeStates

router = Router()


@router.callback_query(F.data == "admin_refcode_management")
async def admin_refcode_menu(call: CallbackQuery, state: FSMContext):
    """
    Show reference code management menu (admin only)

    Args:
        call: Callback query
        state: FSM context
    """
    # Check admin permission
    user_role = check_role(call.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await call.answer("❌ Access denied", show_alert=True)
        return

    await call.message.edit_text(
        "🔑 <b>Reference Code Management</b>\n\n"
        "Manage reference codes for shop access control.\n\n"
        "Admin codes can have custom expiry and usage limits.\n\n"
        "🃏 <b>Physical invite cards</b> (numbered, QR + name stub):\n"
        "Use CLI to print a batch, write the guest name on the stub, "
        "tear the QR half and hand it over.",
        reply_markup=reference_code_admin_keyboard(),
        parse_mode="HTML",
    )
    await state.clear()


@router.callback_query(F.data == "admin_invite_cards_help")
async def admin_invite_cards_help(call: CallbackQuery, state: FSMContext):
    """How to print numbered tear-off invite cards with QR deep links."""
    user_role = check_role(call.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await call.answer("❌ Access denied", show_alert=True)
        return

    bot_user = os.getenv("BOT_USERNAME") or "(set BOT_USERNAME)"
    await call.message.edit_text(
        "🃏 <b>Physical invite cards</b>\n\n"
        "Each card has two halves:\n"
        "• <b>QR half</b> — guest keeps; scan opens Telegram with unique code\n"
        "• <b>Stub half</b> — you keep; write their name, card number matches\n\n"
        "<b>1. Branded A4 PDF (in bot)</b>\n"
        "Reference codes → <b>Brand PDF sheet (A4)</b> → pick brand → count.\n"
        "Creates codes in DB + sends a business-card PDF (LaTeX template / reportlab).\n\n"
        "<b>2. CLI batch</b>\n"
        f"<code>python bot_cli.py invite-cards generate --count 20 "
        f"--bot-username {bot_user}</code>\n"
        f"<code>python bot_cli.py invite-cards sheet --brand your-brand-slug</code>\n\n"
        "<b>3. Hand out</b>\n"
        "Write name on stub → tear QR half → give QR to guest.\n\n"
        "Guest scan → bot starts with code → access unlocked automatically.\n\n"
        "<b>4. After distribution — link stub name to DB</b>\n"
        "Each card has a unique <b>index #</b> on both halves + a unique <b>code</b>.\n"
        "Use <b>Card registry</b> or <b>Assign stub name</b>:\n"
        "<code>7 Ali</code> or multi-line bulk assign.",
        reply_markup=back("admin_refcode_management"),
        parse_mode="HTML",
    )
    await state.clear()


@router.callback_query(F.data == "admin_invite_registry")
async def admin_invite_registry(call: CallbackQuery, state: FSMContext):
    """Show card_number ↔ code ↔ recipient_name registry."""
    user_role = check_role(call.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await call.answer("❌ Access denied", show_alert=True)
        return

    cards = list_invite_cards(limit=80)
    text = format_invite_card_registry(cards, title="Invite card registry (# ↔ code ↔ name)")
    # Telegram message length cap
    if len(text) > 3900:
        text = text[:3900] + "\n…"
    kb = InlineKeyboardBuilder()
    kb.button(text="✍️ Assign stub name", callback_data="admin_invite_assign")
    kb.button(text="📄 Unassigned only", callback_data="admin_invite_registry_open")
    kb.button(text="✅ Assigned only", callback_data="admin_invite_registry_given")
    kb.button(text="🔙 Back", callback_data="admin_refcode_management")
    kb.adjust(1)
    await call.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await state.clear()


@router.callback_query(F.data == "admin_invite_registry_open")
async def admin_invite_registry_open(call: CallbackQuery, state: FSMContext):
    user_role = check_role(call.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await call.answer("❌ Access denied", show_alert=True)
        return
    cards = list_invite_cards(only_unassigned=True, limit=80)
    text = format_invite_card_registry(cards, title="Unassigned stubs (no name yet)")
    if len(text) > 3900:
        text = text[:3900] + "\n…"
    await call.message.edit_text(
        text,
        reply_markup=back("admin_invite_registry"),
        parse_mode="HTML",
    )
    await state.clear()


@router.callback_query(F.data == "admin_invite_registry_given")
async def admin_invite_registry_given(call: CallbackQuery, state: FSMContext):
    user_role = check_role(call.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await call.answer("❌ Access denied", show_alert=True)
        return
    cards = list_invite_cards(only_assigned=True, limit=80)
    text = format_invite_card_registry(cards, title="Assigned stubs (name on card)")
    if len(text) > 3900:
        text = text[:3900] + "\n…"
    await call.message.edit_text(
        text,
        reply_markup=back("admin_invite_registry"),
        parse_mode="HTML",
    )
    await state.clear()


@router.callback_query(F.data == "admin_invite_assign")
async def admin_invite_assign_start(call: CallbackQuery, state: FSMContext):
    """Collect stub names after cards are handed out."""
    user_role = check_role(call.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await call.answer("❌ Access denied", show_alert=True)
        return

    await call.message.edit_text(
        "✍️ <b>Assign stub names</b>\n\n"
        "After you write a name on the stub and give the QR half away, "
        "link that name to the database using the <b>card index</b> "
        "(same # on both halves).\n\n"
        "Send one line per card:\n"
        "<code>7 Ali</code>\n"
        "<code>#12: Sara</code>\n"
        "<code>15=John Doe</code>\n"
        "or by code: <code>ABCDEFGH Mai</code>\n\n"
        "You can paste several lines at once.",
        reply_markup=back("admin_refcode_management"),
        parse_mode="HTML",
    )
    await state.set_state(ReferenceCodeStates.waiting_assign_names)


@router.message(ReferenceCodeStates.waiting_assign_names)
async def admin_invite_assign_process(message: Message, state: FSMContext):
    user_role = check_role(message.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await message.answer("❌ Access denied")
        await state.clear()
        return

    results = assign_invite_cards_bulk(message.text or "")
    if not results:
        await message.answer("No lines to assign. Example: <code>7 Ali</code>", parse_mode="HTML")
        return

    ok_n = sum(1 for ok, _, _ in results if ok)
    lines = []
    for ok, msg, _ in results:
        lines.append(("✅ " if ok else "❌ ") + msg)
    body = "\n".join(lines)
    if len(body) > 3500:
        body = body[:3500] + "\n…"
    await message.answer(
        f"Assigned {ok_n}/{len(results)}:\n\n{body}",
        reply_markup=reference_code_admin_keyboard(),
        parse_mode="HTML",
    )
    await state.clear()


@router.callback_query(F.data == "admin_invite_sheet_start")
async def admin_invite_sheet_start(call: CallbackQuery, state: FSMContext):
    """Pick brand for A4 branded invite PDF sheet."""
    user_role = check_role(call.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await call.answer("❌ Access denied", show_alert=True)
        return

    brands = list_brands_for_admin()
    if not brands:
        await call.message.edit_text(
            "❌ No active brands found. Create a brand first (white-label / multi-brand setup).",
            reply_markup=back("admin_refcode_management"),
        )
        return

    kb = InlineKeyboardBuilder()
    for b in brands:
        kb.button(text=f"{b['name']} ({b['slug']})", callback_data=f"admin_sheet_brand_{b['id']}")
    kb.button(text="🔙 Back", callback_data="admin_refcode_management")
    kb.adjust(1)

    await call.message.edit_text(
        "📄 <b>Brand invite PDF (A4)</b>\n\n"
        "Select a brand — name, colours, and tagline come from the brand profile.\n"
        "Then choose how many new invite codes to generate (already saved in DB) "
        "and print as a business-card sheet.",
        reply_markup=kb.as_markup(),
        parse_mode="HTML",
    )
    await state.clear()


@router.callback_query(F.data.startswith("admin_sheet_brand_"))
async def admin_sheet_brand_picked(call: CallbackQuery, state: FSMContext):
    user_role = check_role(call.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await call.answer("❌ Access denied", show_alert=True)
        return

    brand_id = int(call.data.replace("admin_sheet_brand_", ""))
    await state.update_data(sheet_brand_id=brand_id)
    await call.message.edit_text(
        "📄 How many invite cards on this sheet?\n\n"
        "Send a number <b>1–40</b> (10 cards per A4 page).\n"
        "Codes are created in the database first, then the PDF is built.",
        reply_markup=back("admin_invite_sheet_start"),
        parse_mode="HTML",
    )
    await state.set_state(ReferenceCodeStates.waiting_sheet_count)


@router.message(ReferenceCodeStates.waiting_sheet_count)
async def admin_sheet_count_and_build(message: Message, state: FSMContext):
    user_role = check_role(message.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await message.answer("❌ Access denied")
        await state.clear()
        return

    try:
        count = int((message.text or "").strip())
    except ValueError:
        await message.answer("Please send a number between 1 and 40.")
        return
    if count < 1 or count > 40:
        await message.answer("Count must be between 1 and 40.")
        return

    data = await state.get_data()
    brand_id = data.get("sheet_brand_id")
    if not brand_id:
        await message.answer("Brand missing — start again.", reply_markup=reference_code_admin_keyboard())
        await state.clear()
        return

    await message.answer(f"⏳ Generating {count} codes + branded A4 PDF…")

    bot_user = os.getenv("BOT_USERNAME")
    if not bot_user:
        try:
            me = await message.bot.get_me()
            bot_user = me.username
        except Exception:
            bot_user = None
    if not bot_user:
        await message.answer(
            "❌ Set BOT_USERNAME in .env or ensure the bot has a username.",
            reply_markup=reference_code_admin_keyboard(),
        )
        await state.clear()
        return

    try:
        cards = create_invite_card_batch(
            count=count,
            created_by=message.from_user.id,
            created_by_username=message.from_user.username or f"admin_{message.from_user.id}",
            bot_username=bot_user,
            max_uses=1,
            brand_id=int(brand_id),
        )
        result = export_branded_sheet(
            brand=int(brand_id),
            cards=cards,
            batch_id=cards[0].batch_id,
            bot_username=bot_user,
            output_dir=f"data/invite_cards/{cards[0].batch_id}_sheet",
        )
        pdf_path = Path(result["pdf"])
        pdf_bytes = pdf_path.read_bytes()
        # Short registry snippet so admin can match # to code when writing stubs
        reg = format_invite_card_registry(cards, title=f"Registry batch {cards[0].batch_id}")
        if len(reg) > 900:
            reg = reg[:900] + "\n…"
        await message.answer_document(
            BufferedInputFile(pdf_bytes, filename=f"invite_sheet_{result['brand']}_{cards[0].batch_id}.pdf"),
            caption=(
                f"✅ <b>{result['brand_name']}</b> invite sheet\n"
                f"🃏 {result['count']} cards · batch <code>{result['batch_id']}</code>\n"
                f"🛠 engine: {result['engine']}\n"
                f"Each card index <b>#</b> is stored with its <b>code</b> in the DB.\n"
                f"After hand-out: <b>Assign stub name</b> with <code>7 Ali</code>."
            ),
            parse_mode="HTML",
        )
        await message.answer(reg, parse_mode="HTML")
        # also offer .tex for true LaTeX workflows
        tex_path = Path(result["tex"])
        if tex_path.is_file():
            await message.answer_document(
                BufferedInputFile(tex_path.read_bytes(), filename=tex_path.name),
                caption="📐 LaTeX source (template-driven). Compile with pdflatex if you prefer.",
            )
    except Exception as e:
        await message.answer(f"❌ Failed to build sheet: {e!s}", reply_markup=reference_code_admin_keyboard())
        await state.clear()
        return

    await message.answer("Done.", reply_markup=reference_code_admin_keyboard())
    await state.clear()


@router.callback_query(F.data == "admin_create_refcode")
async def admin_create_refcode_start(call: CallbackQuery, state: FSMContext):
    """
    Start reference code creation process

    Args:
        call: Callback query
        state: FSM context
    """
    # Check admin permission
    user_role = check_role(call.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await call.answer("❌ Access denied", show_alert=True)
        return

    await call.message.edit_text(
        "➕ <b>Create Reference Code</b>\n\n"
        "Enter the expiration time in hours:\n"
        "• Send <code>0</code> for no expiry\n"
        "• Send <code>24</code> for 24 hours\n"
        "• Send <code>168</code> for 1 week\n\n"
        "Or click Back to cancel.",
        reply_markup=back("admin_refcode_management"),
        parse_mode="HTML",
    )
    await state.set_state(ReferenceCodeStates.waiting_refcode_expires)


@router.message(ReferenceCodeStates.waiting_refcode_expires)
async def admin_create_refcode_expires(message: Message, state: FSMContext):
    """
    Process expiration hours input

    Args:
        message: Message with expiration hours
        state: FSM context
    """
    # SEC-06 fix: Permission check on FSM state handler
    user_role = check_role(message.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await message.answer("❌ Access denied")
        await state.clear()
        return
    try:
        expires_hours = int(message.text)
        if expires_hours < 0:
            await message.answer("❌ Hours must be positive or 0 (no expiry)")
            return

        await state.update_data(expires_hours=expires_hours)

        await message.answer(
            "👥 <b>Maximum Uses</b>\n\n"
            "Enter the maximum number of uses:\n"
            "• Send <code>0</code> for unlimited\n"
            "• Send <code>1</code> for single use\n"
            "• Send <code>10</code> for 10 uses\n\n"
            "Or click Back to cancel.",
            reply_markup=back("admin_refcode_management"),
            parse_mode="HTML",
        )
        await state.set_state(ReferenceCodeStates.waiting_refcode_max_uses)

    except ValueError:
        await message.answer("❌ Please enter a valid number")


@router.message(ReferenceCodeStates.waiting_refcode_max_uses)
async def admin_create_refcode_max_uses(message: Message, state: FSMContext):
    """
    Process max uses input

    Args:
        message: Message with max uses
        state: FSM context
    """
    # SEC-06 fix: Permission check on FSM state handler
    user_role = check_role(message.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await message.answer("❌ Access denied")
        await state.clear()
        return
    try:
        max_uses = int(message.text)
        if max_uses < 0:
            await message.answer("❌ Max uses must be positive or 0 (unlimited)")
            return

        await state.update_data(max_uses=max_uses)

        await message.answer(
            "📝 <b>Optional Note</b>\n\n"
            "Enter an optional note for this code (e.g., 'VIP customers', 'Marketing campaign'):\n\n"
            "• Send note text\n"
            "• Or send <code>skip</code> to skip\n\n"
            "Or click Back to cancel.",
            reply_markup=back("admin_refcode_management"),
            parse_mode="HTML",
        )
        await state.set_state(ReferenceCodeStates.waiting_refcode_note)

    except ValueError:
        await message.answer("❌ Please enter a valid number")


@router.message(ReferenceCodeStates.waiting_refcode_note)
async def admin_create_refcode_note(message: Message, state: FSMContext):
    """
    Process note and create the reference code

    Args:
        message: Message with note
        state: FSM context
    """
    # SEC-06 fix: Permission check on FSM state handler
    user_role = check_role(message.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await message.answer("❌ Access denied")
        await state.clear()
        return
    note = None if message.text.lower() == "skip" else message.text
    user_id = message.from_user.id
    username = message.from_user.username or f"admin_{user_id}"

    # Get stored data
    data = await state.get_data()
    expires_hours = data.get("expires_hours", 0)
    max_uses = data.get("max_uses", 0)

    try:
        code = create_reference_code(
            created_by=user_id,
            created_by_username=username,
            is_admin_code=True,
            expires_in_hours=expires_hours if expires_hours > 0 else None,
            max_uses=max_uses if max_uses > 0 else None,
            note=note,
        )

        # Track admin referral code creation
        metrics = get_metrics()
        if metrics:
            metrics.track_event(
                "admin_referral_code_created",
                user_id,
                {"code": code, "expires_hours": expires_hours, "max_uses": max_uses, "has_note": bool(note)},
            )

        expires_text = f"{expires_hours} hours" if expires_hours > 0 else "Never"
        max_uses_text = str(max_uses) if max_uses > 0 else "Unlimited"

        deep_link = None
        bot_user = os.getenv("BOT_USERNAME")
        if not bot_user:
            try:
                me = await message.bot.get_me()
                bot_user = me.username
            except Exception:
                bot_user = None
        if bot_user:
            try:
                deep_link = telegram_start_link(code, bot_user)
            except ValueError:
                deep_link = None

        text = (
            f"✅ <b>Reference Code Created!</b>\n\n"
            f"🔑 Code: <code>{code}</code>\n\n"
            f"⏰ Expires in: {expires_text}\n"
            f"👤 Max uses: {max_uses_text}\n"
            f"📝 Note: {note or 'None'}\n\n"
        )
        if deep_link:
            text += f"🔗 Deep link (for QR / invite card):\n<code>{deep_link}</code>\n\n"
        text += "Share the code or QR so guests open the bot with access."

        await message.answer(text, reply_markup=reference_code_admin_keyboard(), parse_mode="HTML")

        if deep_link:
            png = qr_png_bytes(deep_link)
            await message.answer_photo(
                BufferedInputFile(png, filename=f"invite_{code}.png"),
                caption=f"🃏 QR for code <code>{code}</code>\nPrint or send this half of the invite card.",
                parse_mode="HTML",
            )
    except Exception as e:
        await message.answer(f"❌ Error creating code: {e!s}", reply_markup=reference_code_admin_keyboard())

    await state.clear()


@router.callback_query(F.data == "admin_list_refcodes")
async def admin_list_refcodes(call: CallbackQuery, state: FSMContext):
    """
    List all reference codes

    Args:
        call: Callback query
        state: FSM context
    """
    # Check admin permission
    user_role = check_role(call.from_user.id)
    if not (user_role & (Permission.SHOP_MANAGE | Permission.ADMINS_MANAGE)):
        await call.answer("❌ Access denied", show_alert=True)
        return

    from bot.database.main import Database
    from bot.database.models.main import ReferenceCode

    with Database().session() as session:
        codes = session.query(ReferenceCode).order_by(ReferenceCode.created_at.desc()).limit(20).all()

        if not codes:
            await call.message.edit_text("ℹ️ No reference codes found.", reply_markup=back("admin_refcode_management"))
            return

        text = "📋 <b>Reference Codes</b> (Latest 20)\n\n"

        for code in codes:
            status = "✅" if code.is_active else "❌"
            code_type = "👑 Admin" if code.is_admin_code else "👤 User"
            max_uses = str(code.max_uses) if code.max_uses else "∞"
            expires = code.expires_at.strftime("%Y-%m-%d %H:%M") if code.expires_at else "Never"

            text += (
                f"{status} <code>{code.code}</code> {code_type}\n"
                f"   Uses: {code.current_uses}/{max_uses} | Expires: {expires}\n"
            )
            if code.note:
                text += f"   Note: {code.note}\n"
            text += "\n"

        # Build keyboard with disable options
        kb = InlineKeyboardBuilder()
        kb.button(text="🔙 Back", callback_data="admin_refcode_management")
        kb.adjust(1)

        await call.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")

    await state.clear()
