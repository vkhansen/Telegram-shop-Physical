from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StatesGroup, State
from sqlalchemy import func

from bot.database import Database
from bot.database.models.main import Review, Order, OrderItem, Goods
from bot.i18n import localize
from bot.keyboards import back, simple_buttons
from bot.config import EnvKeys

router = Router()


class ReviewStates(StatesGroup):
    waiting_comment = State()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def get_item_rating(item_name: str) -> tuple[float | None, int]:
    """Return (average_rating, review_count) for the given item name.

    Returns ``(None, 0)`` when there are no reviews yet.
    """
    with Database().session() as session:
        row = session.query(
            func.avg(Review.rating),
            func.count(Review.id),
        ).filter(Review.item_name == item_name).one()

        avg_rating = round(float(row[0]), 1) if row[0] is not None else None
        count = row[1]
    return avg_rating, count


# ---------------------------------------------------------------------------
# 1. Prompt the user to leave a review for a delivered order
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("review_prompt_"))
async def review_prompt(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split("review_prompt_")[1])

    with Database().session() as session:
        # Check the order exists and belongs to the user
        order = session.query(Order).filter(
            Order.id == order_id,
            Order.buyer_id == call.from_user.id,
        ).first()

        if order is None:
            await call.answer()
            return

        # Check if user already reviewed this order
        existing = session.query(Review).filter(
            Review.order_id == order_id,
            Review.user_id == call.from_user.id,
        ).first()

    if existing:
        await call.message.edit_text(
            localize("review.already_reviewed"),
            reply_markup=back("my_orders"),
        )
        await call.answer()
        return

    # Build star-rating buttons (1-5)
    buttons = [
        ("⭐" * i, f"review_rate_{order_id}_{i}")
        for i in range(1, 6)
    ]

    await call.message.edit_text(
        localize("review.rate_title"),
        reply_markup=simple_buttons(buttons, per_row=5),
    )
    await call.answer()


# ---------------------------------------------------------------------------
# 2. Save rating, then ask for an optional comment
# ---------------------------------------------------------------------------

@router.callback_query(F.data.regexp(r"^review_rate_\d+_\d+$"))
async def review_rate(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    # review_rate_{order_id}_{rating}
    order_id = int(parts[2])
    rating = int(parts[3])

    if rating < 1 or rating > 5:
        await call.answer()
        return

    with Database().session() as session:
        order = session.query(Order).filter(
            Order.id == order_id,
            Order.buyer_id == call.from_user.id,
        ).first()

        if order is None:
            await call.answer()
            return

        # Prevent duplicate reviews
        existing = session.query(Review).filter(
            Review.order_id == order_id,
            Review.user_id == call.from_user.id,
        ).first()

        if existing:
            await call.message.edit_text(
                localize("review.already_reviewed"),
                reply_markup=back("my_orders"),
            )
            await call.answer()
            return

        # Determine item_name from the first order item
        order_item = session.query(OrderItem).filter(
            OrderItem.order_id == order_id,
        ).first()
        item_name = order_item.item_name if order_item else None

    # Persist rating info in FSM so we can attach a comment later
    await state.update_data(
        review_order_id=order_id,
        review_rating=rating,
        review_item_name=item_name,
    )

    # Ask for optional comment
    buttons = [(localize("review.skip_comment"), "review_skip_comment")]
    await call.message.edit_text(
        localize("review.comment_prompt"),
        reply_markup=simple_buttons(buttons),
    )
    await state.set_state(ReviewStates.waiting_comment)
    await call.answer()


# ---------------------------------------------------------------------------
# 3a. User sends a text comment
# ---------------------------------------------------------------------------

@router.message(ReviewStates.waiting_comment, F.text)
async def review_save_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("review_order_id")
    rating = data.get("review_rating")
    item_name = data.get("review_item_name")

    if order_id is None or rating is None:
        await state.clear()
        return

    comment = message.text.strip()

    with Database().session() as session:
        review = Review(
            order_id=order_id,
            user_id=message.from_user.id,
            rating=rating,
            comment=comment,
            item_name=item_name,
        )
        session.add(review)
        session.commit()

    await state.clear()
    await message.answer(
        localize("review.thanks"),
        reply_markup=back("my_orders"),
    )


# ---------------------------------------------------------------------------
# 3b. User presses "skip comment"
# ---------------------------------------------------------------------------

@router.callback_query(F.data == "review_skip_comment", ReviewStates.waiting_comment)
async def review_skip_comment(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("review_order_id")
    rating = data.get("review_rating")
    item_name = data.get("review_item_name")

    if order_id is None or rating is None:
        await state.clear()
        await call.answer()
        return

    with Database().session() as session:
        review = Review(
            order_id=order_id,
            user_id=call.from_user.id,
            rating=rating,
            item_name=item_name,
        )
        session.add(review)
        session.commit()

    await state.clear()
    await call.message.edit_text(
        localize("review.thanks"),
        reply_markup=back("my_orders"),
    )
    await call.answer()


# ---------------------------------------------------------------------------
# 4. View reviews for a product
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("view_reviews_"))
async def view_reviews(call: CallbackQuery, state: FSMContext):
    item_name = call.data.split("view_reviews_", 1)[1]

    avg_rating, count = get_item_rating(item_name)

    if count == 0:
        await call.message.edit_text(
            localize("review.no_reviews"),
            reply_markup=back("menu"),
        )
        await call.answer()
        return

    # Fetch recent reviews (latest 10)
    with Database().session() as session:
        recent_reviews = (
            session.query(Review)
            .filter(Review.item_name == item_name)
            .order_by(Review.created_at.desc())
            .limit(10)
            .all()
        )

        lines = [
            localize("review.item_rating", item=item_name, avg=avg_rating, count=count),
            "",
        ]

        for r in recent_reviews:
            stars = "⭐" * r.rating
            line = f"{stars}"
            if r.comment:
                line += f" — {r.comment}"
            lines.append(line)

    await call.message.edit_text(
        "\n".join(lines),
        reply_markup=back("menu"),
    )
    await call.answer()
