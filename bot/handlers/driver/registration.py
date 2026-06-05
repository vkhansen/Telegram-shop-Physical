"""Driver onboarding & admin approval (Card 26, Phase A).

A user runs ``/driver`` to apply; the application lands as ``pending`` and the
owner approves/rejects it from an inline prompt. Approval promotes the user into
a real ``Driver`` record they can then bring online.
"""

import contextlib
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import EnvKeys
from bot.database.methods import (
    approve_driver,
    create_driver,
    get_driver,
    set_driver_status,
)
from bot.handlers.driver.availability import driver_menu_keyboard, driver_status_text
from bot.i18n import localize
from bot.keyboards import back
from bot.states import DriverRegistrationStates

logger = logging.getLogger(__name__)
router = Router()

VEHICLE_TYPES = ("motorbike", "car", "bicycle", "foot")


@router.message(Command("driver"))
async def driver_entry(message: Message, state: FSMContext):
    """Entry point: show the driver menu if registered, else start onboarding."""
    await state.clear()
    driver = get_driver(message.from_user.id)
    if driver:
        await message.answer(
            driver_status_text(driver),
            reply_markup=driver_menu_keyboard(driver),
        )
        return
    await message.answer(localize("driver.register.start"), reply_markup=back("menu"))
    await message.answer(localize("driver.register.ask_name"))
    await state.set_state(DriverRegistrationStates.waiting_name)


@router.message(DriverRegistrationStates.waiting_name, F.text)
async def reg_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name or len(name) > 120:
        await message.answer(localize("driver.register.invalid_name"))
        return
    await state.update_data(name=name)
    await message.answer(localize("driver.register.ask_phone"))
    await state.set_state(DriverRegistrationStates.waiting_phone)


@router.message(DriverRegistrationStates.waiting_phone, F.text)
async def reg_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if len(phone) > 50:
        await message.answer(localize("driver.register.invalid_phone"))
        return
    await state.update_data(phone=phone)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=localize(f"driver.vehicle.{v}"), callback_data=f"driver_vehicle_{v}")]
            for v in VEHICLE_TYPES
        ]
    )
    await message.answer(localize("driver.register.ask_vehicle"), reply_markup=kb)
    await state.set_state(DriverRegistrationStates.waiting_vehicle)


@router.callback_query(DriverRegistrationStates.waiting_vehicle, F.data.startswith("driver_vehicle_"))
async def reg_vehicle(call: CallbackQuery, state: FSMContext):
    vehicle = call.data.removeprefix("driver_vehicle_")
    if vehicle not in VEHICLE_TYPES:
        await call.answer(localize("driver.register.invalid_vehicle"), show_alert=True)
        return
    data = await state.get_data()
    await state.clear()

    brand_id = getattr(call, "brand_id", None) or None
    create_driver(
        telegram_id=call.from_user.id,
        name=data.get("name", call.from_user.full_name),
        brand_id=brand_id,
        phone=data.get("phone"),
        vehicle_type=vehicle,
        status="pending",
    )
    await call.message.edit_text(localize("driver.register.submitted"))
    await _notify_admins_new_application(call, data.get("name"), data.get("phone"), vehicle)
    await call.answer()


async def _notify_admins_new_application(call: CallbackQuery, name: str, phone: str, vehicle: str) -> None:
    """Ping the owner with approve/reject buttons for a new application."""
    owner_id = EnvKeys.OWNER_ID
    if not owner_id:
        return
    tg = call.from_user.id
    text = localize(
        "admin.driver.new_application",
        name=name or "—",
        phone=phone or "—",
        vehicle=localize(f"driver.vehicle.{vehicle}"),
        tg=tg,
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=localize("admin.driver.approve_btn"), callback_data=f"driver_approve_{tg}"),
                InlineKeyboardButton(text=localize("admin.driver.reject_btn"), callback_data=f"driver_reject_{tg}"),
            ]
        ]
    )
    try:
        await call.bot.send_message(int(owner_id), text, reply_markup=kb)
    except Exception:
        logger.warning("Failed to notify owner of new driver application from %s", tg)


def _is_owner(user_id: int) -> bool:
    return EnvKeys.OWNER_ID is not None and str(user_id) == str(EnvKeys.OWNER_ID)


@router.callback_query(F.data.startswith("driver_approve_"))
async def approve(call: CallbackQuery):
    if not _is_owner(call.from_user.id):
        await call.answer(localize("admin.driver.not_authorized"), show_alert=True)
        return
    tg = int(call.data.removeprefix("driver_approve_"))
    if not approve_driver(tg, approved_by=call.from_user.id):
        await call.answer(localize("admin.driver.not_found"), show_alert=True)
        return
    await call.message.edit_text(call.message.text + "\n\n" + localize("admin.driver.approved_admin"))
    with contextlib.suppress(Exception):
        await call.bot.send_message(tg, localize("driver.approved"))
    await call.answer()


@router.callback_query(F.data.startswith("driver_reject_"))
async def reject(call: CallbackQuery):
    if not _is_owner(call.from_user.id):
        await call.answer(localize("admin.driver.not_authorized"), show_alert=True)
        return
    tg = int(call.data.removeprefix("driver_reject_"))
    if not set_driver_status(tg, "rejected"):
        await call.answer(localize("admin.driver.not_found"), show_alert=True)
        return
    await call.message.edit_text(call.message.text + "\n\n" + localize("admin.driver.rejected_admin"))
    with contextlib.suppress(Exception):
        await call.bot.send_message(tg, localize("driver.rejected"))
    await call.answer()
