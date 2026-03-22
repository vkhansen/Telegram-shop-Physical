import logging
from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StatesGroup, State

from sqlalchemy import func, and_

from bot.database.main import Database
from bot.database.models.main import User, CustomerInfo, Order, Permission
from bot.filters import HasPermissionFilter
from bot.i18n import localize
from bot.keyboards.inline import back, simple_buttons
from bot.communication.broadcast_system import BroadcastManager

logger = logging.getLogger(__name__)

router = Router()


class SegmentBroadcastStates(StatesGroup):
    waiting_message = State()


SEGMENT_TYPES = {
    "high_spenders": "High Spenders (top 20%)",
    "recent_buyers": "Recent Buyers (7 days)",
    "inactive": "Inactive Users (30+ days)",
    "new_users": "New Users (7 days)",
}


@router.callback_query(F.data == "segmented_broadcast", HasPermissionFilter(permission=Permission.BROADCAST))
async def segmented_broadcast(call: CallbackQuery, state: FSMContext):
    """Show segmentation options for targeted broadcasts."""
    await state.clear()

    buttons = [
        (localize("admin.segment.all_users"), "send_message"),
        (localize("admin.segment.high_spenders"), "segment_high_spenders"),
        (localize("admin.segment.recent_buyers"), "segment_recent_buyers"),
        (localize("admin.segment.inactive"), "segment_inactive"),
        (localize("admin.segment.new_users"), "segment_new_users"),
    ]

    await call.message.edit_text(
        localize("admin.segment.title"),
        reply_markup=simple_buttons(buttons, per_row=1),
    )


def _get_segment_user_ids(segment_type: str) -> list[int]:
    """Query user IDs matching the given segment type."""
    with Database().session() as session:
        if segment_type == "high_spenders":
            # Users whose total_spendings >= 2x the average
            avg_spending = session.query(func.avg(CustomerInfo.total_spendings)).scalar() or 0
            threshold = float(avg_spending) * 2
            rows = (
                session.query(CustomerInfo.telegram_id)
                .filter(CustomerInfo.total_spendings >= threshold)
                .all()
            )
            return [int(row[0]) for row in rows]

        elif segment_type == "recent_buyers":
            # Users who placed an order in the last 7 days
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            rows = (
                session.query(Order.buyer_id)
                .filter(Order.created_at >= cutoff)
                .distinct()
                .all()
            )
            return [int(row[0]) for row in rows if row[0] is not None]

        elif segment_type == "inactive":
            # Users who have NOT placed an order in the last 30 days
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            recent_buyer_ids = (
                session.query(Order.buyer_id)
                .filter(Order.created_at >= cutoff)
                .distinct()
                .subquery()
            )
            rows = (
                session.query(User.telegram_id)
                .filter(User.telegram_id.notin_(
                    session.query(recent_buyer_ids.c.buyer_id).filter(
                        recent_buyer_ids.c.buyer_id.isnot(None)
                    )
                ))
                .all()
            )
            return [int(row[0]) for row in rows]

        elif segment_type == "new_users":
            # Users registered in the last 7 days
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            rows = (
                session.query(User.telegram_id)
                .filter(User.registration_date >= cutoff)
                .all()
            )
            return [int(row[0]) for row in rows]

        else:
            return []


@router.callback_query(
    F.data.in_([f"segment_{t}" for t in SEGMENT_TYPES]),
    HasPermissionFilter(permission=Permission.BROADCAST),
)
async def segment_selected(call: CallbackQuery, state: FSMContext):
    """Handle segment selection: query matching users and ask for broadcast message."""
    segment_type = call.data.replace("segment_", "")
    segment_label = SEGMENT_TYPES.get(segment_type, segment_type)

    user_ids = _get_segment_user_ids(segment_type)

    if not user_ids:
        await call.answer(localize("admin.segment.empty"), show_alert=True)
        return

    await state.update_data(segment_user_ids=user_ids, segment_type=segment_type)

    await call.message.edit_text(
        localize("admin.segment.count", segment=segment_label, count=len(user_ids))
        + "\n\n"
        + localize("admin.segment.message_prompt"),
        reply_markup=back("segmented_broadcast"),
    )
    await state.set_state(SegmentBroadcastStates.waiting_message)


@router.message(SegmentBroadcastStates.waiting_message, F.text)
async def process_segment_broadcast(message: Message, state: FSMContext):
    """Send the broadcast message to the selected segment."""
    data = await state.get_data()
    user_ids = data.get("segment_user_ids", [])
    segment_type = data.get("segment_type", "unknown")

    if not user_ids:
        await message.answer(
            localize("admin.segment.empty"),
            reply_markup=back("segmented_broadcast"),
        )
        await state.clear()
        return

    await message.delete()

    progress_msg = await message.answer(
        localize("admin.segment.sending", count=len(user_ids)),
        reply_markup=back("segmented_broadcast"),
    )

    try:
        broadcast_manager = BroadcastManager(
            bot=message.bot,
            batch_size=30,
            batch_delay=1.0,
        )

        stats = await broadcast_manager.broadcast(
            user_ids=user_ids,
            text=message.text,
            parse_mode="HTML",
        )

        duration = int(stats.duration) if stats.duration else 0
        await progress_msg.edit_text(
            localize(
                "admin.segment.sent",
                segment=SEGMENT_TYPES.get(segment_type, segment_type),
                total=stats.total,
                sent=stats.sent,
                failed=stats.failed,
                duration=duration,
            ),
            reply_markup=back("segmented_broadcast"),
        )

        logger.info(
            "Segmented broadcast [%s] by user %s: sent=%d, failed=%d, total=%d",
            segment_type, message.from_user.id, stats.sent, stats.failed, stats.total,
        )

    except Exception as e:
        logger.error("Segmented broadcast error: %s", e)
        await progress_msg.edit_text(
            localize("errors.invalid_data"),
            reply_markup=back("segmented_broadcast"),
        )

    await state.clear()
