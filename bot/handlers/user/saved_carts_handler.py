"""
Saved-cart restore flow (Card 21, Phase 4 completion).

When a user switches brands with a non-empty cart they can "Save & Clear", which
writes a SavedCart snapshot. This handler lets them view those snapshots from the
Profile menu and restore or discard them.

Flow:
  Profile → "🛒 Saved Carts" → list → [♻️ Restore] / [🗑 Discard] per snapshot
  Restore replaces the active cart, re-adds available items (skipping any that are
  no longer orderable), consumes the snapshot, and offers a jump to the cart.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.database.methods.create import restore_saved_cart
from bot.database.methods.delete import delete_saved_cart
from bot.database.methods.read import get_saved_carts
from bot.i18n import localize
from bot.keyboards.inline import back, saved_carts_keyboard, simple_buttons

router = Router()


async def _render_saved_carts(call: CallbackQuery, state: FSMContext):
    """Render the list of the user's saved carts (or an empty-state message)."""
    carts = get_saved_carts(call.from_user.id)
    if not carts:
        await call.message.edit_text(
            localize("saved_carts.empty"),
            reply_markup=back("profile"),
        )
        await state.set_state(None)
        return

    lines = [localize("saved_carts.title"), ""]
    for c in carts:
        store = f" · {c['store_name']}" if c["store_name"] else ""
        lines.append(
            localize(
                "saved_carts.entry",
                brand=c["brand_name"],
                store=store,
                n=c["item_count"],
                total=c["total"],
            )
        )
    await call.message.edit_text(
        "\n".join(lines),
        reply_markup=saved_carts_keyboard(carts),
    )
    await state.set_state(None)


@router.callback_query(F.data == "saved_carts")
async def saved_carts_list(call: CallbackQuery, state: FSMContext):
    """Show the user's saved-cart snapshots."""
    await _render_saved_carts(call, state)


@router.callback_query(F.data.startswith("restore_cart:"))
async def restore_cart(call: CallbackQuery, state: FSMContext):
    """Restore a saved cart into the active cart, then offer to view it."""
    saved_cart_id = int(call.data.split(":")[1])
    result = await restore_saved_cart(call.from_user.id, saved_cart_id)

    if not result.get("ok"):
        await call.answer(localize("saved_carts.not_found"), show_alert=True)
        await _render_saved_carts(call, state)
        return

    # Set brand/store context so the restored cart is browsable straight away.
    await state.update_data(
        current_brand_id=result["brand_id"],
        current_store_id=result.get("store_id"),
    )

    if result["skipped"]:
        text = localize(
            "saved_carts.restored_partial",
            restored=result["restored"],
            skipped="\n".join(f"• {name}" for name in result["skipped"]),
        )
    else:
        text = localize("saved_carts.restored", restored=result["restored"])

    await call.message.edit_text(
        text,
        reply_markup=simple_buttons(
            [
                (localize("btn.cart"), "view_cart"),
                (localize("btn.back"), "profile"),
            ]
        ),
    )


@router.callback_query(F.data.startswith("discard_saved:"))
async def discard_saved(call: CallbackQuery, state: FSMContext):
    """Discard a saved-cart snapshot and re-render the list."""
    saved_cart_id = int(call.data.split(":")[1])
    delete_saved_cart(call.from_user.id, saved_cart_id)
    await call.answer(localize("saved_carts.discarded"))
    await _render_saved_carts(call, state)
