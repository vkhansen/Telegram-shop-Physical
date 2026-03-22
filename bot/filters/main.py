from dataclasses import dataclass, field

from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.methods import check_role_cached


@dataclass
class HasPermissionFilter(BaseFilter):
    """
    Filter for the presence of a certain permission for the user (bit mask).
    """
    permission: int

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id
        # check_role_cached(user_id) returns int (bitmask of rights) or None
        user_permissions: int = await check_role_cached(user_id) or 0
        return (user_permissions & self.permission) == self.permission


@dataclass
class BrandPermissionFilter(BaseFilter):
    """
    Filter that checks if user can manage the brand currently in FSM state.
    Passes for SUPERADMIN or brand staff with owner/admin role.
    """
    require_role: list[str] = field(default_factory=lambda: ['owner', 'admin'])

    async def __call__(self, event: Message | CallbackQuery, state: FSMContext) -> bool:
        from bot.database.methods.read import can_manage_brand, is_superadmin

        user_id = event.from_user.id

        # Superadmin always passes
        if is_superadmin(user_id):
            return True

        # Get brand_id from FSM state
        data = await state.get_data()
        brand_id = data.get('current_brand_id')
        if not brand_id:
            return False

        return can_manage_brand(user_id, brand_id)
