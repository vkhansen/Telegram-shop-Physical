import json
import re
from urllib.parse import urlparse

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNotFound
from aiogram.types import CallbackQuery, Message

from bot.config import EnvKeys
from bot.database.methods import check_category_cached, check_item_cached, create_item
from bot.database.methods.inventory import add_inventory
from bot.database.models import Permission
from bot.filters import HasPermissionFilter
from bot.i18n import localize
from bot.keyboards.inline import back, simple_buttons
from bot.logger_mesh import audit_logger
from bot.states import AddItemFSM

router = Router()

COMMON_ALLERGENS = ["gluten", "dairy", "eggs", "nuts", "shellfish", "soy", "fish", "sesame"]

_TIME_RANGE_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _allergen_keyboard(selected: list[str]):
    """Build toggleable allergen multi-select keyboard."""
    buttons = []
    for allergen in COMMON_ALLERGENS:
        prefix = "[x] " if allergen in selected else ""
        label = prefix + localize(f"admin.goods.add.allergen.{allergen}")
        buttons.append((label, f"allergen_toggle:{allergen}"))
    buttons.append((localize("admin.goods.add.allergens.done"), "allergens_done"))
    return simple_buttons(buttons, per_row=2)


def _media_action_keyboard():
    """Keyboard shown after each media upload."""
    buttons = [
        (localize("admin.goods.add.photo.done"), "media_done"),
        (localize("admin.goods.add.photo.skip"), "media_skip"),
    ]
    return simple_buttons(buttons, per_row=2)


def _skip_keyboard():
    """Generic Skip button alongside Back."""
    buttons = [
        (localize("btn.skip"), "step_skip"),
        (localize("btn.back"), "goods_management"),
    ]
    return simple_buttons(buttons, per_row=2)


def _modifier_prompt_keyboard():
    """Yes / No / Paste JSON for modifier group prompt."""
    buttons = [
        (localize("admin.goods.add.modifier.add_group"), "modifier_add_group"),
        (localize("admin.goods.add.modifier.done"), "modifier_finish"),
        (localize("admin.goods.modifiers.json_btn"), "modifier_paste_json"),
    ]
    return simple_buttons(buttons, per_row=2)


def _modifier_option_keyboard():
    """Add another option or finish this group."""
    buttons = [
        (localize("admin.goods.add.modifier.add_option"), "modifier_add_option"),
        (localize("admin.goods.add.modifier.done"), "modifier_group_done"),
    ]
    return simple_buttons(buttons, per_row=2)


def _group_type_keyboard():
    """Single / Multi and Required yes/no for modifier group type."""
    buttons = [
        ("Single + Required", "mtype:single:yes"),
        ("Single + Optional", "mtype:single:no"),
        ("Multi + Required", "mtype:multi:yes"),
        ("Multi + Optional", "mtype:multi:no"),
    ]
    return simple_buttons(buttons, per_row=2)


def _make_group_key(label: str) -> str:
    """Generate a group key from a label: lowercase, underscores."""
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


# ---------------------------------------------------------------------------
# Step 0: Item Type (product vs prepared)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == 'add_item', HasPermissionFilter(permission=Permission.SHOP_MANAGE))
async def add_item_callback_handler(call: CallbackQuery, state):
    """Ask administrator to choose item type first."""
    buttons = [
        (localize("admin.goods.add.type.prepared"), "item_type_prepared"),
        (localize("admin.goods.add.type.product"), "item_type_product"),
    ]
    await call.message.edit_text(
        localize('admin.goods.add.prompt.type'),
        reply_markup=simple_buttons(buttons, per_row=1),
    )
    await state.set_state(AddItemFSM.waiting_item_type)


@router.callback_query(F.data.startswith("item_type_"), AddItemFSM.waiting_item_type)
async def item_type_selected(call: CallbackQuery, state):
    """Save item type and proceed to name."""
    item_type = call.data.replace("item_type_", "")  # 'product' or 'prepared'
    await state.update_data(item_type=item_type)
    await call.message.edit_text(
        localize('admin.goods.add.prompt.name'),
        reply_markup=back("goods_management"),
    )
    await state.set_state(AddItemFSM.waiting_item_name)


# ---------------------------------------------------------------------------
# Step 1: Name
# ---------------------------------------------------------------------------


@router.message(AddItemFSM.waiting_item_name, F.text)
async def check_item_name_for_add(message: Message, state):
    """Validate uniqueness, save name, ask for description."""
    item_name = (message.text or "").strip()
    item = await check_item_cached(item_name)
    if item:
        await message.answer(
            localize('admin.goods.add.name.exists'),
            reply_markup=back('goods_management'),
        )
        return

    await state.update_data(item_name=item_name)
    await message.answer(
        localize('admin.goods.add.prompt.description'),
        reply_markup=back('goods_management'),
    )
    await state.set_state(AddItemFSM.waiting_item_description)


# ---------------------------------------------------------------------------
# Step 2: Description
# ---------------------------------------------------------------------------

@router.message(AddItemFSM.waiting_item_description, F.text)
async def add_item_description(message: Message, state):
    """Save description, ask for photos/videos."""
    await state.update_data(item_description=(message.text or "").strip())
    await state.update_data(item_media=[])
    buttons = [
        (localize("admin.goods.add.photo.skip"), "media_skip"),
    ]
    await message.answer(
        localize('admin.goods.add.prompt.photo'),
        reply_markup=simple_buttons(buttons, per_row=1),
    )
    await state.set_state(AddItemFSM.waiting_item_image)


# ---------------------------------------------------------------------------
# Step 3: Photos / Videos
# ---------------------------------------------------------------------------

@router.message(AddItemFSM.waiting_item_image, F.photo)
async def receive_item_photo(message: Message, state):
    """Store uploaded photo and offer to send more."""
    file_id = message.photo[-1].file_id
    data = await state.get_data()
    media_list = data.get('item_media', [])
    media_list.append({"file_id": file_id, "type": "photo"})
    update = {"item_media": media_list}
    # First photo becomes the primary display image
    if not data.get('image_file_id'):
        update["image_file_id"] = file_id
    await state.update_data(**update)
    await message.answer(
        localize('admin.goods.add.photo.received') + "\n" +
        localize('admin.goods.add.photo.send_more'),
        reply_markup=_media_action_keyboard(),
    )


@router.message(AddItemFSM.waiting_item_image, F.video)
async def receive_item_video(message: Message, state):
    """Store uploaded video and offer to send more."""
    file_id = message.video.file_id
    data = await state.get_data()
    media_list = data.get('item_media', [])
    media_list.append({"file_id": file_id, "type": "video"})
    await state.update_data(item_media=media_list)
    await message.answer(
        localize('admin.goods.add.photo.received') + "\n" +
        localize('admin.goods.add.photo.send_more'),
        reply_markup=_media_action_keyboard(),
    )


# LOGIC-38 fix: Combined identical media_done and media_skip into single handler
@router.callback_query(F.data.in_({"media_done", "media_skip"}))
async def media_done_or_skip(call: CallbackQuery, state):
    """Finish or skip media collection, proceed to price."""
    await call.answer()
    await call.message.edit_text(
        localize('admin.goods.add.prompt.price', currency=EnvKeys.PAY_CURRENCY),
        reply_markup=back('goods_management'),
    )
    await state.set_state(AddItemFSM.waiting_item_price)


# ---------------------------------------------------------------------------
# Step 4: Price
# ---------------------------------------------------------------------------

@router.message(AddItemFSM.waiting_item_price, F.text)
async def add_item_price(message: Message, state):
    """Validate price, ask for category."""
    # LOGIC-22 fix: Accept decimal prices (e.g., "9.99") not just integers
    price_text = (message.text or "").strip()
    try:
        price_value = float(price_text)
        if price_value <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        await message.answer(
            localize('admin.goods.add.price.invalid'),
            reply_markup=back('goods_management'),
        )
        return

    await state.update_data(item_price=price_value)
    await message.answer(
        localize('admin.goods.add.prompt.category'),
        reply_markup=back('goods_management'),
    )
    await state.set_state(AddItemFSM.waiting_category)


# ---------------------------------------------------------------------------
# Step 5: Category
# ---------------------------------------------------------------------------

@router.message(AddItemFSM.waiting_category, F.text)
async def check_category_for_add_item(message: Message, state):
    """Category must exist; then ask for stock quantity."""
    category_name = (message.text or "").strip()
    category = await check_category_cached(category_name)
    if not category:
        await message.answer(
            localize('admin.goods.add.category.not_found'),
            reply_markup=back('goods_management'),
        )
        return

    await state.update_data(item_category=category_name)
    await message.answer(
        localize('admin.goods.add.stock.prompt'),
        reply_markup=back('goods_management'),
    )
    await state.set_state(AddItemFSM.waiting_stock_quantity)


# ---------------------------------------------------------------------------
# Step 6: Stock Quantity
# ---------------------------------------------------------------------------

@router.message(AddItemFSM.waiting_stock_quantity, F.text)
async def stock_then_ask_prep_time(message: Message, state):
    """Save stock, ask for prep time."""
    stock_text = (message.text or "").strip()
    if not stock_text.isdigit():
        await message.answer(
            localize('admin.goods.add.stock.invalid'),
            reply_markup=back('goods_management'),
        )
        return

    stock_quantity = int(stock_text)
    if stock_quantity < 0:
        await message.answer(
            localize('admin.goods.add.stock.negative'),
            reply_markup=back('goods_management'),
        )
        return

    await state.update_data(stock_quantity=stock_quantity)
    await message.answer(
        localize('admin.goods.add.prompt.prep_time'),
        reply_markup=_skip_keyboard(),
    )
    await state.set_state(AddItemFSM.waiting_prep_time)


# ---------------------------------------------------------------------------
# Step 7: Prep Time
# ---------------------------------------------------------------------------

@router.message(AddItemFSM.waiting_prep_time, F.text)
async def receive_prep_time(message: Message, state):
    """Accept prep time in minutes."""
    text = (message.text or "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer(
            localize('admin.goods.add.prompt.prep_time'),
            reply_markup=_skip_keyboard(),
        )
        return

    await state.update_data(prep_time=int(text))
    await _ask_allergens(message, state)


@router.callback_query(F.data == "step_skip", AddItemFSM.waiting_prep_time)
async def skip_prep_time(call: CallbackQuery, state):
    """Skip prep time, go to allergens."""
    await call.answer()
    await _ask_allergens(call.message, state)


async def _ask_allergens(message: Message, state):
    """Transition to allergen selection."""
    await state.update_data(selected_allergens=[])
    await message.answer(
        localize('admin.goods.add.prompt.allergens'),
        reply_markup=_allergen_keyboard([]),
    )
    await state.set_state(AddItemFSM.waiting_allergens)


# ---------------------------------------------------------------------------
# Step 8: Allergens (multi-select toggle)
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("allergen_toggle:"), AddItemFSM.waiting_allergens)
async def toggle_allergen(call: CallbackQuery, state):
    """Toggle an allergen on/off."""
    allergen = call.data.split(":", 1)[1]
    data = await state.get_data()
    selected = data.get('selected_allergens', [])
    if allergen in selected:
        selected.remove(allergen)
    else:
        selected.append(allergen)
    await state.update_data(selected_allergens=selected)
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=_allergen_keyboard(selected))


@router.callback_query(F.data == "allergens_done", AddItemFSM.waiting_allergens)
async def allergens_done(call: CallbackQuery, state):
    """Finalize allergen selection, proceed to availability window."""
    data = await state.get_data()
    selected = data.get('selected_allergens', [])
    allergens_str = ",".join(selected) if selected else None
    await state.update_data(allergens=allergens_str)
    await call.answer()
    await call.message.edit_text(
        localize('admin.goods.add.prompt.availability'),
        reply_markup=_skip_keyboard(),
    )
    await state.set_state(AddItemFSM.waiting_availability)


# ---------------------------------------------------------------------------
# Step 9: Availability Window
# ---------------------------------------------------------------------------

@router.message(AddItemFSM.waiting_availability, F.text)
async def receive_availability(message: Message, state):
    """Parse HH:MM-HH:MM availability window."""
    text = (message.text or "").strip()
    if not _TIME_RANGE_RE.match(text):
        await message.answer(
            localize('admin.goods.add.prompt.availability'),
            reply_markup=_skip_keyboard(),
        )
        return

    start, end = text.split("-")
    await state.update_data(available_from=start, available_until=end)
    await message.answer(
        localize('admin.goods.add.prompt.daily_limit'),
        reply_markup=_skip_keyboard(),
    )
    await state.set_state(AddItemFSM.waiting_daily_limit)


@router.callback_query(F.data == "step_skip", AddItemFSM.waiting_availability)
async def skip_availability(call: CallbackQuery, state):
    """Skip availability, go to daily limit."""
    await call.answer()
    await call.message.edit_text(
        localize('admin.goods.add.prompt.daily_limit'),
        reply_markup=_skip_keyboard(),
    )
    await state.set_state(AddItemFSM.waiting_daily_limit)


# ---------------------------------------------------------------------------
# Step 10: Daily Limit
# ---------------------------------------------------------------------------

@router.message(AddItemFSM.waiting_daily_limit, F.text)
async def receive_daily_limit(message: Message, state):
    """Accept daily limit as positive integer."""
    text = (message.text or "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer(
            localize('admin.goods.add.prompt.daily_limit'),
            reply_markup=_skip_keyboard(),
        )
        return

    await state.update_data(daily_limit=int(text))
    await _ask_modifiers(message, state)


@router.callback_query(F.data == "step_skip", AddItemFSM.waiting_daily_limit)
async def skip_daily_limit(call: CallbackQuery, state):
    """Skip daily limit, go to modifiers."""
    await call.answer()
    await _ask_modifiers(call.message, state)


async def _ask_modifiers(message: Message, state):
    """Prompt: add modifier group, finish, or paste JSON."""
    await state.update_data(item_modifiers={})
    await message.answer(
        localize('admin.goods.add.prompt.modifier_group'),
        reply_markup=_modifier_prompt_keyboard(),
    )


# ---------------------------------------------------------------------------
# Step 11: Interactive Modifier Builder
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "modifier_finish")
async def modifier_finish(call: CallbackQuery, state):
    """Done with modifiers, create item."""
    data = await state.get_data()
    modifiers = data.get('item_modifiers') or {}
    await state.update_data(item_modifiers=modifiers if modifiers else None)
    await call.answer()
    await _create_and_finalize_item(call.message, state, call.from_user.id)


@router.callback_query(F.data == "modifier_add_group")
async def modifier_add_group(call: CallbackQuery, state):
    """Ask for modifier group name."""
    await call.answer()
    await call.message.edit_text(
        localize('admin.goods.add.modifier.group_name'),
        reply_markup=back('goods_management'),
    )
    await state.set_state(AddItemFSM.waiting_modifier_group_name)


@router.message(AddItemFSM.waiting_modifier_group_name, F.text)
async def receive_modifier_group_name(message: Message, state):
    """Save group name, ask for type."""
    group_name = (message.text or "").strip()
    if not group_name:
        await message.answer(
            localize('admin.goods.add.modifier.group_name'),
            reply_markup=back('goods_management'),
        )
        return

    await state.update_data(
        current_group_label=group_name,
        current_group_key=_make_group_key(group_name),
        current_group_options=[],
    )
    await message.answer(
        localize('admin.goods.add.modifier.group_type'),
        reply_markup=_group_type_keyboard(),
    )
    await state.set_state(AddItemFSM.waiting_modifier_group_type)


@router.callback_query(F.data.startswith("mtype:"), AddItemFSM.waiting_modifier_group_type)
async def receive_modifier_group_type(call: CallbackQuery, state):
    """Save group type (single/multi + required), ask for first option label."""
    _, group_type, required = call.data.split(":")
    await state.update_data(
        current_group_type=group_type,
        current_group_required=(required == "yes"),
    )
    await call.answer()
    await call.message.edit_text(
        localize('admin.goods.add.modifier.option_label'),
        reply_markup=back('goods_management'),
    )
    await state.set_state(AddItemFSM.waiting_modifier_option_label)


@router.message(AddItemFSM.waiting_modifier_option_label, F.text)
async def receive_modifier_option_label(message: Message, state):
    """Save option label, ask for price."""
    label = (message.text or "").strip()
    if not label:
        await message.answer(
            localize('admin.goods.add.modifier.option_label'),
            reply_markup=back('goods_management'),
        )
        return

    await state.update_data(current_option_label=label)
    await message.answer(
        localize('admin.goods.add.modifier.option_price'),
        reply_markup=back('goods_management'),
    )
    await state.set_state(AddItemFSM.waiting_modifier_option_price)


@router.message(AddItemFSM.waiting_modifier_option_price, F.text)
async def receive_modifier_option_price(message: Message, state):
    """Save option price, offer to add more options or finish group."""
    price_text = (message.text or "").strip()
    try:
        price = int(price_text)
    except ValueError:
        await message.answer(
            localize('admin.goods.add.modifier.option_price'),
            reply_markup=back('goods_management'),
        )
        return

    data = await state.get_data()
    options = data.get('current_group_options', [])
    option_label = data.get('current_option_label', 'option')
    option_id = _make_group_key(option_label) + f"_{len(options)}"
    options.append({
        "id": option_id,
        "label": option_label,
        "price": price,
    })
    await state.update_data(current_group_options=options)
    await message.answer(
        localize('admin.goods.add.modifier.add_option'),
        reply_markup=_modifier_option_keyboard(),
    )


@router.callback_query(F.data == "modifier_add_option")
async def modifier_add_another_option(call: CallbackQuery, state):
    """Add another option to the current group."""
    await call.answer()
    await call.message.edit_text(
        localize('admin.goods.add.modifier.option_label'),
        reply_markup=back('goods_management'),
    )
    await state.set_state(AddItemFSM.waiting_modifier_option_label)


@router.callback_query(F.data == "modifier_group_done")
async def modifier_group_done(call: CallbackQuery, state):
    """Finish current group, store it, and ask about adding another."""
    data = await state.get_data()
    modifiers = data.get('item_modifiers', {})
    group_key = data.get('current_group_key', 'group')

    # Ensure unique key
    base_key = group_key
    counter = 1
    while group_key in modifiers:
        group_key = f"{base_key}_{counter}"
        counter += 1

    modifiers[group_key] = {
        "label": data.get('current_group_label', group_key),
        "type": data.get('current_group_type', 'single'),
        "required": data.get('current_group_required', False),
        "options": data.get('current_group_options', []),
    }

    # Clean up temp state keys
    await state.update_data(
        item_modifiers=modifiers,
        current_group_key=None,
        current_group_label=None,
        current_group_type=None,
        current_group_required=None,
        current_group_options=None,
        current_option_label=None,
    )

    await call.answer()
    await call.message.edit_text(
        localize('admin.goods.add.prompt.modifier_group'),
        reply_markup=_modifier_prompt_keyboard(),
    )


# ---------------------------------------------------------------------------
# Step 11b: Paste JSON (power-user alternative)
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "modifier_paste_json")
async def ask_modifiers_json(call: CallbackQuery, state):
    """Ask admin to paste modifier JSON schema."""
    await call.answer()
    await call.message.edit_text(
        localize("admin.goods.modifiers.json_prompt"),
        reply_markup=back('goods_management'),
    )
    await state.set_state(AddItemFSM.waiting_modifiers_json)


@router.message(AddItemFSM.waiting_modifiers_json, F.text)
async def receive_modifiers_json(message: Message, state):
    """Parse and validate modifier JSON, then create the item."""
    raw = (message.text or "").strip()

    try:
        modifiers = json.loads(raw)
    except json.JSONDecodeError as e:
        await message.answer(
            localize("admin.goods.modifiers.invalid_json", error=str(e)),
            reply_markup=back('goods_management'),
        )
        return

    if not isinstance(modifiers, dict):
        await message.answer(
            localize("admin.goods.modifiers.invalid_json", error="Must be a JSON object"),
            reply_markup=back('goods_management'),
        )
        return

    # Validate structure of each group
    for group_key, group in modifiers.items():
        if not isinstance(group, dict):
            await message.answer(
                localize("admin.goods.modifiers.invalid_json",
                         error=f"Group '{group_key}' must be an object"),
                reply_markup=back('goods_management'),
            )
            return
        if "options" not in group or not isinstance(group.get("options"), list):
            await message.answer(
                localize("admin.goods.modifiers.invalid_json",
                         error=f"Group '{group_key}' must have 'options' array"),
                reply_markup=back('goods_management'),
            )
            return

    # Check if we're editing an existing item's modifiers
    data = await state.get_data()
    if data.get('modifier_edit_existing'):
        item_name = data.get('modifier_item_name')
        from bot.database import Database
        from bot.database.models.main import Goods
        with Database().session() as session:
            good = session.query(Goods).filter_by(name=item_name).first()
            if good:
                good.modifiers = modifiers
                session.commit()
        await message.answer(
            f"Modifiers updated for <b>{item_name}</b>",
            reply_markup=back('goods_management'),
        )
        await state.clear()
        return

    await state.update_data(item_modifiers=modifiers)
    await _create_and_finalize_item(message, state, message.from_user.id)


# ---------------------------------------------------------------------------
# Finalize: create item, stock, channel notification, audit log
# ---------------------------------------------------------------------------

async def _create_and_finalize_item(message: Message, state, admin_id: int):
    """Create position with all fields, stock, modifiers, then notify channel."""
    data = await state.get_data()
    item_name = data.get('item_name')
    item_description = data.get('item_description')
    item_price = data.get('item_price')
    category_name = data.get('item_category')
    stock_quantity = data.get('stock_quantity', 0)
    item_modifiers = data.get('item_modifiers')

    # Create position with restaurant-specific fields
    create_item(
        item_name,
        item_description,
        item_price,
        category_name,
        image_file_id=data.get('image_file_id'),
        media=data.get('item_media'),
        prep_time_minutes=data.get('prep_time'),
        allergens=data.get('allergens'),
        daily_limit=data.get('daily_limit'),
        available_from=data.get('available_from'),
        available_until=data.get('available_until'),
        brand_id=data.get('current_brand_id'),
        item_type=data.get('item_type', 'prepared'),
    )

    # Set modifiers if provided
    if item_modifiers:
        from bot.database import Database
        from bot.database.models.main import Goods
        with Database().session() as session:
            good = session.query(Goods).filter_by(name=item_name).first()
            if good:
                good.modifiers = item_modifiers
                session.commit()

    # Add stock using inventory management system
    if stock_quantity > 0:
        from bot.database import Database as Db2
        with Db2().session() as session:
            success, msg = add_inventory(
                item_name=item_name,
                quantity=stock_quantity,
                admin_id=admin_id,
                comment="Initial stock added during product creation",
                session=session,
            )
            if not success:
                await message.answer(
                    localize('admin.goods.add.stock.error', error=msg),
                    reply_markup=back('goods_management'),
                )
                await state.clear()
                return

    modifier_note = ""
    if item_modifiers:
        groups = len(item_modifiers)
        modifier_note = f"\nModifiers: {groups} group(s) configured"

    await message.answer(
        localize('admin.goods.add.result.created_with_stock',
                 name=item_name,
                 stock=stock_quantity) + modifier_note,
        reply_markup=back('goods_management'),
    )

    # Optionally notify a channel
    channel_url = EnvKeys.CHANNEL_URL or ""
    parsed = urlparse(channel_url)
    channel_username = (
        parsed.path.lstrip('/')
        if parsed.path else channel_url.replace("https://t.me/", "").replace("t.me/", "").lstrip('@')
    ) or None
    if channel_username:
        try:
            await message.bot.send_message(
                chat_id=f"@{channel_username}",
                text=(
                    f"\U0001f381 {localize('shop.group.new_upload')}\n"
                    f"\U0001f3f7\ufe0f {localize('shop.group.item')}: <b>{item_name}</b>\n"
                    f"\U0001f4e6 {localize('shop.group.stock')}: <b>{stock_quantity}</b>"
                ),
                parse_mode='HTML',
            )
        except TelegramForbiddenError:
            await message.answer(localize("errors.channel.telegram_forbidden_error", channel=channel_username))
        except TelegramNotFound:
            await message.answer(localize("errors.channel.telegram_not_found", channel=channel_username))
        except TelegramBadRequest as e:
            await message.answer(localize("errors.channel.telegram_bad_request", e=e))

    admin_info = await message.bot.get_chat(admin_id)
    audit_logger.info(
        f'Admin {admin_id} ({admin_info.first_name}) created item "{item_name}" '
        f'with stock {stock_quantity}, modifiers={bool(item_modifiers)}, '
        f'prep_time={data.get("prep_time")}, allergens={data.get("allergens")}, '
        f'availability={data.get("available_from")}-{data.get("available_until")}, '
        f'daily_limit={data.get("daily_limit")}, media_count={len(data.get("item_media") or [])}'
    )
    await state.clear()
