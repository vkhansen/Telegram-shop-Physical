import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StatesGroup, State

from bot.database.main import Database
from bot.database.models.main import Store, Permission
from bot.filters import HasPermissionFilter
from bot.i18n import localize
from bot.keyboards.inline import back, simple_buttons

logger = logging.getLogger(__name__)

router = Router()


class StoreStates(StatesGroup):
    waiting_name = State()
    waiting_address = State()
    waiting_location = State()


@router.callback_query(F.data == "store_management", HasPermissionFilter(permission=Permission.SETTINGS_MANAGE))
async def store_management(call: CallbackQuery, state: FSMContext):
    """Show list of stores with management options."""
    await state.clear()

    with Database().session() as session:
        stores = session.query(Store).order_by(Store.created_at).all()

        buttons = []
        for store in stores:
            status = "+" if store.is_active else "-"
            default = " *" if store.is_default else ""
            label = f"[{status}] {store.name}{default}"
            buttons.append((label, f"view_store_{store.id}"))

        buttons.append((localize("admin.store.add"), "add_store"))
        buttons.append((localize("btn.back"), "settings_management"))

    await call.message.edit_text(
        localize("admin.store.title"),
        reply_markup=simple_buttons(buttons, per_row=1),
    )


# ---------------------------------------------------------------------------
# Store creation FSM
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "add_store", HasPermissionFilter(permission=Permission.SETTINGS_MANAGE))
async def add_store_start(call: CallbackQuery, state: FSMContext):
    """Begin store creation: ask for name."""
    await call.message.edit_text(
        localize("admin.store.name_prompt"),
        reply_markup=back("store_management"),
    )
    await state.set_state(StoreStates.waiting_name)


@router.message(StoreStates.waiting_name, F.text)
async def process_store_name(message: Message, state: FSMContext):
    """Save store name and ask for address."""
    name = message.text.strip()

    if not name or len(name) > 200:
        await message.answer(
            localize("admin.store.name_invalid"),
            reply_markup=back("store_management"),
        )
        return

    # Check uniqueness
    with Database().session() as session:
        existing = session.query(Store).filter_by(name=name).first()
        if existing:
            await message.answer(
                localize("admin.store.name_exists"),
                reply_markup=back("store_management"),
            )
            return

    await state.update_data(store_name=name)

    skip_buttons = [
        (localize("btn.skip"), "skip_store_address"),
    ]
    await message.answer(
        localize("admin.store.address_prompt"),
        reply_markup=simple_buttons(skip_buttons, per_row=1),
    )
    await state.set_state(StoreStates.waiting_address)


@router.callback_query(F.data == "skip_store_address", HasPermissionFilter(permission=Permission.SETTINGS_MANAGE))
async def skip_store_address(call: CallbackQuery, state: FSMContext):
    """Skip address entry and move to location."""
    await state.update_data(store_address=None)

    skip_buttons = [
        (localize("btn.skip"), "skip_store_location"),
    ]
    await call.message.edit_text(
        localize("admin.store.location_prompt"),
        reply_markup=simple_buttons(skip_buttons, per_row=1),
    )
    await state.set_state(StoreStates.waiting_location)


@router.message(StoreStates.waiting_address, F.text)
async def process_store_address(message: Message, state: FSMContext):
    """Save address and ask for GPS location."""
    await state.update_data(store_address=message.text.strip())

    skip_buttons = [
        (localize("btn.skip"), "skip_store_location"),
    ]
    await message.answer(
        localize("admin.store.location_prompt"),
        reply_markup=simple_buttons(skip_buttons, per_row=1),
    )
    await state.set_state(StoreStates.waiting_location)


@router.callback_query(F.data == "skip_store_location", HasPermissionFilter(permission=Permission.SETTINGS_MANAGE))
async def skip_store_location(call: CallbackQuery, state: FSMContext):
    """Skip location and save store."""
    await state.update_data(store_latitude=None, store_longitude=None)
    await _save_store(call.message, state)


@router.message(StoreStates.waiting_location, F.location)
async def process_store_location(message: Message, state: FSMContext):
    """Save GPS location and create the store."""
    await state.update_data(
        store_latitude=message.location.latitude,
        store_longitude=message.location.longitude,
    )
    await _save_store(message, state)


async def _save_store(message: Message, state: FSMContext):
    """Persist the new store to the database."""
    data = await state.get_data()

    name = data.get("store_name", "Unnamed")
    address = data.get("store_address")
    latitude = data.get("store_latitude")
    longitude = data.get("store_longitude")

    with Database().session() as session:
        store = Store(
            name=name,
            address=address,
            latitude=latitude,
            longitude=longitude,
        )
        session.add(store)
        session.commit()

    await message.answer(
        localize("admin.store.created", name=name),
        reply_markup=back("store_management"),
    )
    await state.clear()

    logger.info("Store created: %s", name)


# ---------------------------------------------------------------------------
# View / toggle / set default
# ---------------------------------------------------------------------------

@router.callback_query(
    F.data.regexp(r"^view_store_\d+$"),
    HasPermissionFilter(permission=Permission.SETTINGS_MANAGE),
)
async def view_store(call: CallbackQuery):
    """Show details for a single store."""
    store_id = int(call.data.split("_")[-1])

    with Database().session() as session:
        store = session.query(Store).filter_by(id=store_id).first()
        if not store:
            await call.answer(localize("admin.store.not_found"), show_alert=True)
            return

        status = localize("admin.store.active") if store.is_active else localize("admin.store.inactive")
        default_label = localize("admin.store.is_default") if store.is_default else ""

        details = (
            f"<b>{store.name}</b>{default_label}\n\n"
            f"<b>{localize('admin.store.status')}:</b> {status}\n"
        )
        if store.address:
            details += f"<b>{localize('admin.store.address')}:</b> {store.address}\n"
        if store.latitude and store.longitude:
            details += f"<b>{localize('admin.store.location')}:</b> {store.latitude}, {store.longitude}\n"
        if store.phone:
            details += f"<b>{localize('admin.store.phone')}:</b> {store.phone}\n"

        toggle_label = localize("admin.store.deactivate") if store.is_active else localize("admin.store.activate")
        buttons = [
            (toggle_label, f"toggle_store_{store.id}"),
        ]
        if not store.is_default:
            buttons.append((localize("admin.store.set_default"), f"set_default_store_{store.id}"))
        buttons.append((localize("btn.back"), "store_management"))

    await call.message.edit_text(
        details,
        reply_markup=simple_buttons(buttons, per_row=1),
        parse_mode="HTML",
    )


@router.callback_query(
    F.data.regexp(r"^toggle_store_\d+$"),
    HasPermissionFilter(permission=Permission.SETTINGS_MANAGE),
)
async def toggle_store(call: CallbackQuery):
    """Activate or deactivate a store."""
    store_id = int(call.data.split("_")[-1])

    with Database().session() as session:
        store = session.query(Store).filter_by(id=store_id).first()
        if not store:
            await call.answer(localize("admin.store.not_found"), show_alert=True)
            return

        store.is_active = not store.is_active
        new_status = store.is_active
        session.commit()

    status_text = localize("admin.store.active") if new_status else localize("admin.store.inactive")
    await call.answer(f"{status_text}", show_alert=True)

    # Refresh the view
    call.data = f"view_store_{store_id}"
    await view_store(call)


@router.callback_query(
    F.data.regexp(r"^set_default_store_\d+$"),
    HasPermissionFilter(permission=Permission.SETTINGS_MANAGE),
)
async def set_default_store(call: CallbackQuery):
    """Set a store as the default, unsetting all others."""
    store_id = int(call.data.split("_")[-1])

    with Database().session() as session:
        # Unset current defaults
        session.query(Store).filter(Store.is_default == True).update({"is_default": False})

        store = session.query(Store).filter_by(id=store_id).first()
        if not store:
            await call.answer(localize("admin.store.not_found"), show_alert=True)
            return

        store.is_default = True
        session.commit()

    await call.answer(localize("admin.store.default_set"), show_alert=True)

    # Refresh the view
    call.data = f"view_store_{store_id}"
    await view_store(call)
