from functools import partial

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, InputMediaVideo

from bot.config import EnvKeys
from bot.database import Database
from bot.database.methods import (
    check_value,
    get_bought_item_info,
    get_item_info_cached,
    query_categories,
    query_user_bought_items,
)
from bot.database.models.main import Goods as GoodsModel
from bot.i18n import localize
from bot.keyboards import back, item_info, lazy_paginated_keyboard
from bot.states import ShopStates
from bot.utils import LazyPaginator

router = Router()


# PERF-01 fix: Cache item display data to avoid N+1 DB queries
_item_display_cache: dict[str, tuple] = {}


def _warm_item_display_cache(item_names: list[str]) -> None:
    """Batch-load display data for multiple items in a single query."""
    if not item_names:
        return
    uncached = [n for n in item_names if n not in _item_display_cache]
    if not uncached:
        return
    with Database().session() as sess:
        rows = sess.query(
            GoodsModel.name,
            GoodsModel.prep_time_minutes,
            GoodsModel.sold_out_today,
            GoodsModel.is_active,
            GoodsModel.daily_limit,
            GoodsModel.daily_sold_count,
        ).filter(GoodsModel.name.in_(uncached)).all()
        for row in rows:
            _item_display_cache[row[0]] = row[1:]


def _item_button_text(item_name: str) -> str:
    """Build display text for an item button in the items list.

    Appends prep time if available, and marks sold-out items.
    """
    g = _item_display_cache.get(item_name)
    if g is None:
        # Fallback single query if not pre-cached
        with Database().session() as sess:
            row = sess.query(
                GoodsModel.prep_time_minutes,
                GoodsModel.sold_out_today,
                GoodsModel.is_active,
                GoodsModel.daily_limit,
                GoodsModel.daily_sold_count,
            ).filter(GoodsModel.name == item_name).first()
        if not row:
            return item_name
        g = row

    prep_time, sold_out, is_active, daily_limit, daily_sold = g

    label = item_name

    # Append prep time
    if prep_time:
        label += f" ({prep_time} min)"

    # Mark sold-out
    if sold_out or (daily_limit is not None and daily_sold >= daily_limit):
        label += " \u274c"

    return label


async def show_brand_categories(call: CallbackQuery, state: FSMContext):
    """
    Show list of shop categories for the current brand with lazy loading.
    Called from store_selection.py after brand/branch is selected.
    """
    data = await state.get_data()
    brand_id = data.get('current_brand_id')
    brand_name = data.get('current_brand_name', '')

    # Create paginator with brand filter
    query_func = partial(query_categories, brand_id=brand_id) if brand_id else query_categories
    paginator = LazyPaginator(query_func, per_page=10)

    # Create keyboard
    markup = await lazy_paginated_keyboard(
        paginator=paginator,
        item_text=lambda cat: cat,
        item_callback=lambda cat: f"category_{cat}_categories-page_0",  # Include page info
        page=0,
        back_cb="switch_brand",
        nav_cb_prefix="categories-page_",
    )

    title = localize("shop.categories.title")
    if brand_name:
        title = f"{brand_name}\n\n{title}"

    await call.message.edit_text(title, reply_markup=markup)

    # Save paginator state
    await state.update_data(categories_paginator=paginator.get_state())
    await state.set_state(ShopStates.viewing_categories)


@router.callback_query(F.data.startswith('categories-page_'))
async def navigate_categories(call: CallbackQuery, state: FSMContext):
    """
    Pagination across shop categories with cache.
    """
    parts = call.data.split('_', 1)
    page = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0

    # Get saved state
    data = await state.get_data()
    paginator_state = data.get('categories_paginator')
    brand_id = data.get('current_brand_id')

    # Create paginator with cached state
    query_func = partial(query_categories, brand_id=brand_id) if brand_id else query_categories
    paginator = LazyPaginator(
        query_func,
        per_page=10,
        state=paginator_state
    )

    markup = await lazy_paginated_keyboard(
        paginator=paginator,
        item_text=lambda cat: cat,
        item_callback=lambda cat: f"category_{cat}_categories-page_{page}",  # Pass current page
        page=page,
        back_cb="switch_brand",
        nav_cb_prefix="categories-page_"
    )

    await call.message.edit_text(localize('shop.categories.title'), reply_markup=markup)

    # Update state
    await state.update_data(categories_paginator=paginator.get_state())


@router.callback_query(F.data.startswith('category_'))
async def items_list_callback_handler(call: CallbackQuery, state: FSMContext):
    """
    Show items of selected category.
    Extract category name and return page from callback_data.
    Filters out inactive items and annotates buttons with prep time / sold-out status.
    """
    # Parse callback data: category_{name}_categories-page_{page}
    callback_data = call.data[9:]  # Remove 'category_'

    if '_categories-page_' in callback_data:
        category_name, back_data = callback_data.rsplit('_categories-page_', 1)
        back_data = f"categories-page_{back_data}"
    else:
        category_name = callback_data
        back_data = "shop"

    # Create paginator for items in category (active items only)
    from bot.database.methods.lazy_queries import query_items_in_category

    query_func = partial(query_items_in_category, category_name)
    paginator = LazyPaginator(query_func, per_page=10)

    markup = await lazy_paginated_keyboard(
        paginator=paginator,
        item_text=_item_button_text,
        item_callback=lambda item: f"item_{item}_{category_name}_goods-page_{category_name}_0",
        page=0,
        back_cb=back_data,  # Use the saved page
        nav_cb_prefix=f"goods-page_{category_name}_",
    )

    await call.message.edit_text(localize("shop.goods.choose"), reply_markup=markup)

    # Save state
    await state.update_data(
        goods_paginator=paginator.get_state(),
        current_category=category_name
    )
    await state.set_state(ShopStates.viewing_goods)


@router.callback_query(F.data.startswith('goods-page_'), ShopStates.viewing_goods)
async def navigate_goods(call: CallbackQuery, state: FSMContext):
    """
    Pagination for items inside selected category.
    Format: goods-page_{category}_{page}
    """
    prefix = "goods-page_"
    tail = call.data[len(prefix):]
    category_name, current_index = tail.rsplit("_", 1)
    current_index = int(current_index)

    # Get saved state
    data = await state.get_data()
    paginator_state = data.get('goods_paginator')

    # Determine back button target
    # Try to get from state if we came from categories
    categories_page = data.get('categories_last_viewed_page', 0)
    back_data = f"categories-page_{categories_page}"

    # Create paginator
    from bot.database.methods.lazy_queries import query_items_in_category

    query_func = partial(query_items_in_category, category_name)
    paginator = LazyPaginator(query_func, per_page=10, state=paginator_state)

    markup = await lazy_paginated_keyboard(
        paginator=paginator,
        item_text=_item_button_text,
        item_callback=lambda item: f"item_{item}_{category_name}_goods-page_{category_name}_{current_index}",
        page=current_index,
        back_cb=back_data,
        nav_cb_prefix=f"goods-page_{category_name}_",
    )

    await call.message.edit_text(localize("shop.goods.choose"), reply_markup=markup)

    # Update state
    await state.update_data(goods_paginator=paginator.get_state())


@router.callback_query(F.data.startswith('item_'))
async def item_info_callback_handler(call: CallbackQuery):
    """
    Show detailed information about the item, including photo, prep time,
    allergens, calories, daily remaining, availability window, and reviews.
    Format: item_{name}_{category}_goods-page_{category}_{page}
    """
    # Parse callback data
    callback_data = call.data[5:]  # Remove 'item_'

    # Extract item name, category and back data
    if '_goods-page_' in callback_data:
        # Split by the last occurrence of _goods-page_
        item_and_cat, back_page_data = callback_data.rsplit('_goods-page_', 1)
        # Now split item_and_cat to get item name and category
        parts = item_and_cat.rsplit('_', 1)
        if len(parts) == 2:
            item_name, category = parts
        else:
            item_name = item_and_cat
            category = ""
        back_data = f"goods-page_{back_page_data}"
    else:
        item_name = callback_data
        back_data = "shop"
        category = ""

    item_info_data = await get_item_info_cached(item_name)
    if not item_info_data:
        await call.answer(localize("shop.item.not_found"), show_alert=True)
        return

    # If couldn't extract category from callback, get it from item info
    if not category:
        category = item_info_data.get('category_name', '')

    # Get detailed stock information with reservation details
    if check_value(item_name):
        quantity_line = localize("shop.item.quantity_unlimited")
    else:
        # Get inventory statistics (stock, reserved, available)
        from bot.database.methods.inventory import get_inventory_stats
        inventory_stats = get_inventory_stats(item_name)

        if inventory_stats:
            quantity_line = localize(
                "shop.item.quantity_detailed",
                total=inventory_stats['stock'],
                reserved=inventory_stats['reserved'],
                available=inventory_stats['available']
            )
        else:
            # Fallback if item not found
            quantity_line = localize("shop.item.quantity_left", count=0)

    # Build the item_info keyboard; we may add a gallery button below
    markup = item_info(item_name, back_data)

    # Build caption lines
    info_lines = [
        localize("shop.item.title", name=item_name),
        localize("shop.item.description", description=item_info_data["description"]),
        localize("shop.item.price", amount=item_info_data["price"], currency=EnvKeys.PAY_CURRENCY),
        quantity_line,
    ]

    # Item type indicator
    item_type = item_info_data.get("item_type", "prepared")
    if item_type == "product":
        info_lines.append(localize("shop.item.type_product"))
    else:
        info_lines.append(localize("shop.item.type_prepared"))

    # Prep time (primarily for prepared items)
    prep = item_info_data.get("prep_time_minutes")
    if prep:
        info_lines.append(localize("shop.item.prep_time", minutes=prep))

    # Allergens
    allergens = item_info_data.get("allergens")
    if allergens:
        info_lines.append(localize("shop.item.allergens", allergens=allergens))

    # Calories
    calories = item_info_data.get("calories")
    if calories:
        info_lines.append(localize("shop.item.calories", calories=calories))

    # Daily remaining
    daily_limit = item_info_data.get("daily_limit")
    if daily_limit:
        with Database().session() as sess:
            g = sess.query(GoodsModel).filter_by(name=item_name).first()
            if g and g.daily_sold_count is not None:
                remaining = max(0, daily_limit - g.daily_sold_count)
                info_lines.append(localize("shop.item.daily_remaining", remaining=remaining, limit=daily_limit))

    # Availability window
    avail_from = item_info_data.get("available_from")
    avail_until = item_info_data.get("available_until")
    if avail_from and avail_until:
        info_lines.append(localize("shop.item.availability", from_time=avail_from, until_time=avail_until))

    # Show available modifiers in the item description (Card 8)
    modifiers_schema = item_info_data.get("modifiers")
    if modifiers_schema and isinstance(modifiers_schema, dict):
        info_lines.append("")  # blank line separator
        for group_key, group in modifiers_schema.items():
            label = group.get("label", group_key)
            required = group.get("required", False)
            req_tag = localize("modifier.required") if required else localize("modifier.optional")
            options = group.get("options", [])
            opt_labels = []
            for opt in options:
                opt_text = opt.get("label", opt["id"])
                price = opt.get("price", 0)
                if price:
                    opt_text += f" {localize('modifier.price_extra', price=price)}"
                opt_labels.append(opt_text)
            info_lines.append(f"{label} {req_tag}: {', '.join(opt_labels)}")

    # Add review rating if reviews exist
    try:
        from bot.handlers.user.review_handler import get_item_rating
        avg_rating, review_count = get_item_rating(item_name)
        if review_count > 0:
            stars = "\u2b50" * round(avg_rating)
            info_lines.append(f"{stars} {avg_rating:.1f}/5 ({review_count})")
    except Exception:
        pass  # Reviews module not available or no reviews table yet

    caption = "\n".join(info_lines)

    # Check for gallery media and inject gallery button into markup
    media_list = item_info_data.get("media")
    if media_list and isinstance(media_list, list) and len(media_list) > 1:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        # Rebuild keyboard with gallery button
        kb = InlineKeyboardBuilder()
        kb.button(text=localize("btn.add_to_cart"), callback_data=f"add_to_cart_{item_name}")
        kb.button(
            text=localize("btn.view_gallery", count=len(media_list)),
            callback_data=f"item_gallery_{item_name}",
        )
        kb.button(text=localize("btn.back"), callback_data=back_data)
        kb.adjust(2, 1)
        markup = kb.as_markup()

    # Display with photo if available
    image_file_id = item_info_data.get("image_file_id")
    if image_file_id:
        # Can't edit a text message into a photo message - delete old and send new
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer_photo(
            photo=image_file_id,
            caption=caption,
            reply_markup=markup,
        )
    else:
        await call.message.edit_text(caption, reply_markup=markup)


@router.callback_query(F.data.startswith('item_gallery_'))
async def item_gallery_handler(call: CallbackQuery):
    """Show all photos/videos for an item as a media group (up to 10 items)."""
    item_name = call.data.replace('item_gallery_', '')

    item_info_data = await get_item_info_cached(item_name)
    if not item_info_data:
        await call.answer(localize("shop.item.not_found"), show_alert=True)
        return

    media_list = item_info_data.get("media")
    if not media_list or not isinstance(media_list, list):
        await call.answer(localize("shop.item.no_gallery"), show_alert=True)
        return

    # Build media group (Telegram allows max 10 items)
    media_group = []
    for entry in media_list[:10]:
        file_id = entry.get("file_id")
        entry_type = entry.get("type", "photo")
        entry_caption = entry.get("caption")
        if not file_id:
            continue
        if entry_type == "video":
            media_group.append(InputMediaVideo(media=file_id, caption=entry_caption))
        else:
            media_group.append(InputMediaPhoto(media=file_id, caption=entry_caption))

    if not media_group:
        await call.answer(localize("shop.item.no_gallery"), show_alert=True)
        return

    await call.message.answer_media_group(media=media_group)
    await call.answer()


@router.callback_query(F.data == "bought_items")
async def bought_items_callback_handler(call: CallbackQuery, state: FSMContext):
    """
    Show list of user's purchased items with lazy loading.
    """
    user_id = call.from_user.id

    # Create paginator for user's bought items
    query_func = partial(query_user_bought_items, user_id)
    paginator = LazyPaginator(query_func, per_page=10)

    markup = await lazy_paginated_keyboard(
        paginator=paginator,
        item_text=lambda item: item.item_name,
        item_callback=lambda item: f"bought-item:{item.id}:bought-goods-page_user_0",
        page=0,
        back_cb="profile",
        nav_cb_prefix="bought-goods-page_user_"
    )

    await call.message.edit_text(localize("purchases.title"), reply_markup=markup)

    # Save paginator state
    await state.update_data(bought_items_paginator=paginator.get_state())


@router.callback_query(F.data.startswith('bought-goods-page_'))
async def navigate_bought_items(call: CallbackQuery, state: FSMContext):
    """
    Pagination for user's purchased items with lazy loading.
    Format: 'bought-goods-page_{data}_{page}', where data = 'user' or user_id.
    """
    parts = call.data.split('_')
    if len(parts) < 3:
        await call.answer(localize("purchases.pagination.invalid"))
        return

    data_type = parts[1]
    try:
        current_index = int(parts[2])
    except ValueError:
        current_index = 0

    if data_type == 'user':
        user_id = call.from_user.id
        back_cb = 'profile'
        pre_back = f'bought-goods-page_user_{current_index}'
    else:
        user_id = int(data_type)
        back_cb = f'check-user_{data_type}'
        pre_back = f'bought-goods-page_{data_type}_{current_index}'

    # Get saved state
    data = await state.get_data()
    paginator_state = data.get('bought_items_paginator')

    # Create paginator with cached state
    query_func = partial(query_user_bought_items, user_id)
    paginator = LazyPaginator(query_func, per_page=10, state=paginator_state)

    markup = await lazy_paginated_keyboard(
        paginator=paginator,
        item_text=lambda item: item.item_name,
        item_callback=lambda item: f"bought-item:{item.id}:{pre_back}",
        page=current_index,
        back_cb=back_cb,
        nav_cb_prefix=f"bought-goods-page_{data_type}_"
    )

    await call.message.edit_text(localize("purchases.title"), reply_markup=markup)

    # Update state
    await state.update_data(bought_items_paginator=paginator.get_state())


@router.callback_query(F.data.startswith('bought-item:'))
async def bought_item_info_callback_handler(call: CallbackQuery):
    """
    Show details for a purchased item.
    """
    trash, item_id, back_data = call.data.split(':', 2)
    item = get_bought_item_info(item_id)
    if not item:
        await call.answer(localize("purchases.item.not_found"), show_alert=True)
        return

    text = "\n".join([
        localize("purchases.item.name", name=item["item_name"]),
        localize("purchases.item.price", amount=item["price"], currency=EnvKeys.PAY_CURRENCY),
        localize("purchases.item.datetime", dt=item["bought_datetime"]),
        localize("purchases.item.unique_id", uid=item["unique_id"]),
        localize("purchases.item.value", value=item["value"]),
    ])
    await call.message.edit_text(text, parse_mode='HTML', reply_markup=back(back_data))
