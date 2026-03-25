DEFAULT_LOCALE = "th"


# Language picker — add new languages here + their translations in TRANSLATIONS
AVAILABLE_LOCALES: dict[str, str] = {
    "th": "🇹🇭 ไทย",
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "ar": "🇸🇦 العربية",
    "fa": "🇮🇷 فارسی",
    "ps": "🇦🇫 پښتو",
    "fr": "🇫🇷 Français",
}

# The language picker message is shown in ALL languages simultaneously
# so the user can understand it regardless of current locale
LANGUAGE_PICKER_MESSAGE = (
    "🌐 Choose your language / เลือกภาษา / Выберите язык\n"
    "اختر لغتك / زبان خود را انتخاب کنید / خپله ژبه وټاکئ\n"
    "Choisissez votre langue"
)

LANGUAGE_CHANGED_MESSAGES: dict[str, str] = {
    "th": "✅ เปลี่ยนเป็นภาษาไทยแล้ว",
    "en": "✅ Language changed to English",
    "ru": "✅ Язык изменён на русский",
    "ar": "✅ تم تغيير اللغة إلى العربية",
    "fa": "✅ زبان به فارسی تغییر کرد",
    "ps": "✅ ژبه پښتو ته بدله شوه",
    "fr": "✅ Langue changée en français",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "ru": {
        # === Common Buttons ===
        "btn.shop": "🏪 Магазин",
        "btn.rules": "📜 Правила",
        "btn.profile": "👤 Профиль",
        "btn.support": "🆘 Поддержка",
        "btn.channel": "ℹ Новостной канал",
        "btn.admin_menu": "🎛 Панель администратора",
        "btn.back": "⬅️ Назад",
        "btn.close": "✖ Закрыть",
        "btn.yes": "✅ Да",
        "btn.no": "❌ Нет",
        "btn.check_subscription": "🔄 Проверить подписку",
        "btn.admin.ban_user": "🚫 Забанить пользователя",
        "btn.admin.unban_user": "✅ Разбанить пользователя",

        # === Admin Buttons (user management shortcuts) ===
        "btn.admin.promote": "⬆️ Назначить администратором",
        "btn.admin.demote": "⬇️ Снять администратора",
        "btn.admin.add_user_bonus": "🎁 Добавить реферальный бонус",

        # === Titles / Generic Texts ===
        "menu.title": "⛩️ Основное меню",
        "profile.caption": "👤 <b>Профиль</b> — <a href='tg://user?id={id}'>{name}</a>",
        "rules.not_set": "❌ Правила не были добавлены",
        "admin.users.cannot_ban_owner": "❌ Нельзя забанить владельца",
        "admin.users.ban.success": "✅ Пользователь {name} успешно забанен",
        "admin.users.ban.failed": "❌ Не удалось забанить пользователя",
        "admin.users.ban.notify": "⛔ Вы были забанены администратором",
        "admin.users.unban.success": "✅ Пользователь {name} успешно разбанен",
        "admin.users.unban.failed": "❌ Не удалось разбанить пользователя",
        "admin.users.unban.notify": "✅ Вы были разбанены администратором",

        # === Subscription Flow ===
        "subscribe.prompt": "Для начала подпишитесь на новостной канал",

        # === Profile ===
        "profile.referral_id": "👤 <b>Реферал</b> — <code>{id}</code>",
        "btn.referral": "🎲 Реферальная система",
        "btn.purchased": "🎁 Купленные товары",

        # === Profile Info Lines ===
        "profile.id": "🆔 <b>ID</b> — <code>{id}</code>",
        "profile.bonus_balance": "💰 <b>Реферальный бонус:</b> ${bonus_balance}",
        "profile.purchased_count": "🎁 <b>Куплено товаров</b> — {count} шт",
        "profile.registration_date": "🕢 <b>Дата регистрации</b> — <code>{dt}</code>",

        # === Referral ===
        "referral.title": "💚 Реферальная система",
        "referral.count": "Количество рефералов: {count}",
        "referral.description": (
            "📔 Реферальная система позволит Вам заработать деньги без всяких вложений. "
            "Необходимо всего лишь распространять свою реферальную ссылку и Вы будете получать "
            "{percent}% от суммы пополнений Ваших рефералов на Ваш баланс бота."
        ),
        "btn.view_referrals": "👥 Мои рефералы",
        "btn.view_earnings": "💰 Мои поступления",

        "referrals.list.title": "👥 Ваши рефералы:",
        "referrals.list.empty": "У вас пока нет активных рефералов",
        "referrals.item.format": "ID: {telegram_id} | Принёс: {total_earned} {currency}",

        "referral.earnings.title": "💰 Поступления от реферала <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>):",
        "referral.earnings.empty": "От данного реферала <code>{id}</code> (<a href='tg://user?id={id}'>{name}</a>) пока не было поступлений",
        "referral.earning.format": "{amount} {currency} | {date} | (с {original_amount} {currency})",
        "referral.item.info": ("💰 Поступление номер: <code>{id}</code>\n"
                               "👤 Реферал: <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>)\n"
                               "🔢 Количество: {amount} {currency}\n"
                               "🕘 Дата: <code>{date}</code>\n"
                               "💵 С пополнения на {original_amount} {currency}"),

        "referral.admin_bonus.info": ("💰 Поступление номер: <code>{id}</code>\n"
                                      "🎁 <b>Бонус от администратора</b>\n"
                                      "🔢 Количество: {amount} {currency}\n"
                                      "🕘 Дата: <code>{date}</code>"),

        "all.earnings.title": "💰 Все ваши реферальные поступления:",
        "all.earnings.empty": "У вас пока нет реферальных поступлений",
        "all.earning.format.admin": "{amount} {currency} от Админа | {date}",

        "referrals.stats.template": (
            "📊 Статистика реферальной системы:\n\n"
            "👥 Активных рефералов: {active_count}\n"
            "💰 Всего заработано: {total_earned} {currency}\n"
            "📈 Общая сумма пополнений рефералов: {total_original} {currency}\n"
            "🔢 Количество начислений: {earnings_count}"
        ),

        # === Admin: Main Menu ===
        "admin.menu.main": "⛩️ Меню администратора",
        "admin.menu.shop": "🛒 Управление магазином",
        "admin.menu.goods": "📦 Управление позициями",
        "admin.menu.categories": "📂 Управление категориями",
        "admin.menu.users": "👥 Управление пользователями",
        "admin.menu.broadcast": "📝 Рассылка",
        "admin.menu.rights": "Недостаточно прав",

        # === Admin: User Management ===
        "admin.users.prompt_enter_id": "👤 Введите id пользователя,\nчтобы посмотреть | изменить его данные",
        "admin.users.invalid_id": "⚠️ Введите корректный числовой ID пользователя.",
        "admin.users.profile_unavailable": "❌ Профиль недоступен (такого пользователя никогда не существовало)",
        "admin.users.not_found": "❌ Пользователь не найден",
        "admin.users.cannot_change_owner": "Нельзя менять роль владельца",
        "admin.users.referrals": "👥 <b>Рефералы пользователя</b> — {count}",
        "admin.users.btn.view_referrals": "👥 Рефералы пользователя",
        "admin.users.btn.view_earnings": "💰 Поступления",
        "admin.users.role": "🎛 <b>Роль</b> — {role}",
        "admin.users.set_admin.success": "✅ Роль присвоена пользователю {name}",
        "admin.users.set_admin.notify": "✅ Вам присвоена роль АДМИНИСТРАТОРА бота",
        "admin.users.remove_admin.success": "✅ Роль отозвана у пользователя {name}",
        "admin.users.remove_admin.notify": "❌ У вас отозвана роль АДМИНИСТРАТОРА бота",
        "admin.users.bonus.prompt": "Введите сумму бонуса в {currency}:",
        "admin.users.bonus.added": "✅ Реферальный бонус пользователя {name} пополнен на {amount} {currency}",
        "admin.users.bonus.added.notify": "🎁 Вам начислен реферальный бонус на {amount} {currency}",
        "admin.users.bonus.invalid": "❌ Неверная сумма. Введите число от {min_amount} до {max_amount} {currency}.",

        # === Admin: Shop Management Menu ===
        "admin.shop.menu.title": "⛩️ Меню управления магазином",
        "admin.shop.menu.statistics": "📊 Статистика",
        "admin.shop.menu.logs": "📁 Показать логи",
        "admin.shop.menu.admins": "👮 Администраторы",
        "admin.shop.menu.users": "👤 Пользователи",

        # === Admin: Categories Management ===
        "admin.categories.menu.title": "⛩️ Меню управления категориями",
        "admin.categories.add": "➕ Добавить категорию",
        "admin.categories.rename": "✏️ Переименовать категорию",
        "admin.categories.delete": "🗑 Удалить категорию",
        "admin.categories.prompt.add": "Введите название новой категории:",
        "admin.categories.prompt.delete": "Введите название категории для удаления:",
        "admin.categories.prompt.rename.old": "Введите текущее название категории, которую нужно переименовать:",
        "admin.categories.prompt.rename.new": "Введите новое имя для категории:",
        "admin.categories.add.exist": "❌ Категория не создана (такая уже существует)",
        "admin.categories.add.success": "✅ Категория создана",
        "admin.categories.delete.not_found": "❌ Категория не удалена (такой категории не существует)",
        "admin.categories.delete.success": "✅ Категория удалена",
        "admin.categories.rename.not_found": "❌ Категория не может быть обновлена (такой категории не существует)",
        "admin.categories.rename.exist": "❌ Переименование невозможно (категория с таким именем уже существует)",
        "admin.categories.rename.success": "✅ Категория \"{old}\" переименована в \"{new}\"",

        # === Admin: Goods / Items Management (Add / List / Item Info) ===
        "admin.goods.add_position": "➕ Добавить позицию",
        "admin.goods.manage_stock": "➕ Добавить товар в позицию",
        "admin.goods.update_position": "📝 Изменить позицию",
        "admin.goods.delete_position": "❌ Удалить позицию",
        "admin.goods.add.prompt.type": "Выберите тип товара:",
        "admin.goods.add.type.prepared": "🍳 Приготовление на заказ (еда, напитки)",
        "admin.goods.add.type.product": "📦 Упакованный товар (вода, снеки)",
        "admin.goods.add.prompt.name": "Введите название позиции",
        "admin.goods.add.name.exists": "❌ Позиция не может быть создана (такая позиция уже существует)",
        "admin.goods.add.prompt.description": "Введите описание для позиции:",
        "admin.goods.add.prompt.price": "Введите цену для позиции (число в {currency}):",
        "admin.goods.add.price.invalid": "⚠️ Некорректное значение цены. Введите число.",
        "admin.goods.add.prompt.category": "Введите категорию, к которой будет относиться позиция:",
        "admin.goods.add.category.not_found": "❌ Позиция не может быть создана (категория для привязки введена неверно)",
        "admin.goods.position.not_found": "❌ Товаров нет (Такой позиции не существует)",
        "admin.goods.menu.title": "⛩️ Меню управления позициями",
        "admin.goods.add.stock.prompt": "Введите количество товара для добавления",
        "admin.goods.add.stock.invalid": "⚠️ Некорректное значение количества товара. Введите число.",
        "admin.goods.add.stock.negative": "⚠️ Некорректное значение количества товара. Введите положительно число.",
        "admin.goods.add.result.created_with_stock": "✅ Позиция {item_name} создана, добавлено {stock_quantity} в количество товара.",

        # === Admin: Goods / Items Update Flow ===
        "admin.goods.update.position.invalid": "Позиция не найдена.",
        "admin.goods.update.position.exists": "Позиция с таким именем уже существует.",
        "admin.goods.update.prompt.name": "Введите название позиции",
        "admin.goods.update.not_exists": "❌ Позиция не может быть изменена (такой позиции не существует)",
        "admin.goods.update.prompt.new_name": "Введите новое имя для позиции:",
        "admin.goods.update.prompt.description": "Введите описание для позиции:",
        "admin.goods.update.success": "✅ Позиция обновлена",

        # === Admin: Goods / Items Delete Flow ===
        "admin.goods.delete.prompt.name": "Введите название позиции",
        "admin.goods.delete.position.not_found": "❌ Позиция не удалена (Такой позиции не существует)",
        "admin.goods.delete.position.success": "✅ Позиция удалена",

        # === Admin: Item Info ===
        "admin.goods.view_stock": "Посмотреть товары",

        # Admin Modifier Management (Card 8)
        "admin.goods.manage_modifiers": "🍳 Модификаторы",
        "admin.goods.modifiers.prompt": "Хотите добавить модификаторы (специи, добавки и т.д.)?",
        "admin.goods.modifiers.add_btn": "➕ Добавить модификаторы",
        "admin.goods.modifiers.skip_btn": "⏭ Пропустить",
        "admin.goods.modifiers.json_prompt": "Вставьте JSON-схему модификаторов (пример в документации):",
        "admin.goods.modifiers.invalid_json": "❌ Неверный JSON: {error}",
        "admin.goods.modifiers.select_item": "Введите название продукта для настройки модификаторов:",
        "admin.goods.modifiers.edit_instructions": "Выберите действие:",
        "admin.goods.modifiers.set_new": "📝 Задать новые",
        "admin.goods.modifiers.clear": "🗑 Удалить все",
        "admin.goods.stock.status_title": "Статус товаров:",

        # === Admin: Logs ===
        "admin.shop.logs.caption": "Логи бота",
        "admin.shop.logs.empty": "❗️ Логов пока нет",

        # === Group Notifications ===
        "shop.group.new_upload": "Залив",
        "shop.group.item": "Товар",
        "shop.group.stock": "Количество",

        # === Admin: Statistics ===
        "admin.shop.stats.template": (
            "Статистика магазина:\n"
            "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            "<b>◽ПОЛЬЗОВАТЕЛИ</b>\n"
            "◾️Пользователей за 24 часа: {today_users}\n"
            "◾️Всего администраторов: {admins}\n"
            "◾️Всего пользователей: {users}\n"
            "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            "◽<b>СРЕДСТВА</b>\n"
            "◾Продаж за 24 часа на: {today_orders} {currency}\n"
            "◾Продано товаров на: {all_orders} {currency}\n"
            "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            "◽<b>ПРОЧЕЕ</b>\n"
            "◾Товаров: {items} шт.\n"
            "◾Позиций: {goods} шт.\n"
            "◾Категорий: {categories} шт.\n"
            "◾Продано товаров: {sold_count} шт."
        ),

        # === Admin: Lists & Broadcast ===
        "admin.shop.admins.title": "👮 Администраторы бота:",
        "admin.shop.users.title": "Пользователи бота:",
        "broadcast.prompt": "Отправьте сообщение для рассылки:",
        "broadcast.creating": "📤 Начинаем рассылку...\n👥 Всего пользователей: {ids}",
        "broadcast.progress": (
            "📤 Рассылка в процессе...\n\n"
            "📊 Прогресс: {progress:.1f}%\n"
            "✅ Отправлено: {sent}/{total}\n"
            "❌ Ошибок: {failed}\n"
            "⏱ Прошло времени: {time} сек"),
        "broadcast.done": (
            "✅ Рассылка завершена!\n\n"
            "📊 Статистика:\n"
            "👥 Всего: {total}\n"
            "✅ Доставлено: {sent}\n"
            "❌ Не доставлено: {failed}\n"
            "🚫 Заблокировали бота: ~{blocked}\n"
            "📈 Успешность: {success}%\n"
            "⏱ Время: {duration} сек"
        ),
        "broadcast.cancel": "❌ Рассылка отменена",
        "broadcast.warning": "Нет активной рассылки",

        # === Brand / Store Selection ===
        "shop.brands.title": "🏪 Выберите ресторан",
        "shop.branches.title": "📍 Выберите филиал",
        "shop.no_brands": "В данный момент нет доступных ресторанов.",
        "shop.brand_unavailable": "Этот ресторан временно недоступен.",

        # === Shop Browsing (Categories / Goods / Item Page) ===
        "shop.categories.title": "🏪 Категории магазина",
        "shop.goods.choose": "🏪 Выберите нужный товар",
        "shop.item.not_found": "Товар не найден",
        "shop.item.title": "🏪 Товар {name}",
        "shop.item.description": "Описание: {description}",
        "shop.item.price": "Цена — {amount} {currency}",
        "shop.item.quantity_unlimited": "Количество — неограниченно",
        "shop.item.quantity_left": "Количество — {count} шт.",
        "shop.item.quantity_detailed": "📦 Всего на складе: {total} шт.\n🔒 Зарезервировано: {reserved} шт.\n✅ Доступно для заказа: {available} шт.",

        # === Purchases ===
        "purchases.title": "Купленные товары:",
        "purchases.pagination.invalid": "Некорректные данные пагинации",
        "purchases.item.not_found": "Покупка не найдена",
        "purchases.item.name": "<b>🧾 Товар</b>: <code>{name}</code>",
        "purchases.item.price": "<b>💵 Цена</b>: <code>{amount}</code> {currency}",
        "purchases.item.datetime": "<b>🕒 Дата покупки</b>: <code>{dt}</code>",
        "purchases.item.unique_id": "<b>🧾 Уникальный ID</b>: <code>{uid}</code>",
        "purchases.item.value": "<b>🔑 Значение</b>:\n<code>{value}</code>",

        # === Middleware ===
        "middleware.ban": "⏳ Вы временно заблокированы. Подождите {time} секунд",
        "middleware.above_limits": "⚠️ Слишком много запросов! Вы временно заблокированы.",
        "middleware.waiting": "⏳ Подождите {time} секунд перед следующим действием.",
        "middleware.security.session_outdated": "⚠️ Сессия устарела. Пожалуйста, начните заново.",
        "middleware.security.invalid_data": "❌ Недопустимые данные",
        "middleware.security.blocked": "❌ Доступ заблокирован",
        "middleware.security.not_admin": "⛔ Недостаточно прав",
        "middleware.security.banned": "⛔ <b>Вы забанены</b>\n\nПричина: {reason}",
        "middleware.security.banned_no_reason": "⛔ <b>Вы забанены</b>\n\nОбратитесь к администратору для получения дополнительной информации.",
        "middleware.security.rate_limit": "⚠️ Слишком много запросов! Пожалуйста, подождите немного.",

        # === Errors ===
        "errors.not_subscribed": "Вы не подписались",
        "errors.pagination_invalid": "Некорректные данные пагинации",
        "errors.invalid_data": "❌ Неправильные данные",
        "errors.channel.telegram_not_found": "Я не могу писать в канал. Добавьте меня админом канала для заливов @{channel} с правом публиковать сообщения.",
        "errors.channel.telegram_forbidden_error": "Канал не найден. Проверьте username канала для заливов @{channel}.",
        "errors.channel.telegram_bad_request": "Не удалось отправить в канал для заливов: {e}",
        "errors.invalid_item_name": "❌ Неверное название товара",
        "errors.invalid_language": "Неверный язык",
        "shop.error.brand_required": "Сначала выберите бренд",
        "shop.error.branch_unavailable": "Филиал недоступен",

        # === Orders ===
        "order.payment_method.choose": "💳 Выберите способ оплаты:",
        "order.payment_method.bitcoin": "💳 Bitcoin",
        "order.payment_method.litecoin": "💳 Litecoin",
        "order.payment_method.solana": "💳 SOL",
        "order.payment_method.usdt_sol": "💳 USDT (Solana)",
        "order.payment_method.cash": "💵 Оплата наличными при получении",
        "order.status.notify_order_confirmed": (
            "Заказ {order_code} подтвержден! 🎉\n\n"
            "Ваш заказ будет доставлен: {delivery_time}\n\n"
            "Товары:\n{items}\n\n"
            "Общая сумма: {total}\n\n"
            "Ожидайте доставку!"
        ),
        "order.status.notify_order_delivered": (
            "Заказ {order_code} доставлен! ✅\n\n"
            "Спасибо за покупку! Будем рады видеть вас снова! 🙏"
        ),
        "order.status.notify_order_modified": (
            "Order {order_code} modified by admin 📝\n\n"
            "Changes:\n{changes}\n\n"
            "New total: {total}"
        ),

        # === Additional Common Buttons ===
        "btn.cart": "🛒 Корзина",
        "btn.my_orders": "📦 Мои заказы",
        "btn.reference_codes": "🔑 Реферальные коды",
        "btn.settings": "⚙️ Настройки",
        "btn.referral_bonus_percent": "💰 Процент реферального бонуса",
        "btn.order_timeout": "⏱️ Таймаут заказа",
        "btn.timezone": "🌍 Часовой пояс",
        "btn.promptpay_account": "💳 Счёт PromptPay",
        "btn.currency": "💱 Валюта",
        "btn.skip": "⏭️ Пропустить",
        "btn.use_saved_info": "✅ Использовать сохраненную информацию",
        "btn.update_info": "✏️ Обновить информацию",
        "btn.back_to_cart": "◀️ Назад к корзине",
        "btn.clear_cart": "🗑️ Очистить корзину",
        "btn.proceed_checkout": "💳 Перейти к оформлению",
        "btn.remove_item": "❌ Удалить {item_name}",
        "btn.use_all_bonus": "Использовать все ${amount}",
        "btn.apply_bonus_yes": "✅ Да, применить бонус",
        "btn.apply_bonus_no": "❌ Нет, сохранить на потом",
        "btn.cancel": "❌ Отменить",
        "btn.add_to_cart": "🛒 Добавить в корзину",

        # === Cart Management ===
        "cart.add_success": "✅ {item_name} добавлен в корзину!",
        "cart.add_error": "❌ {message}",
        "cart.empty": "🛒 Ваша корзина пуста.\n\nПросмотрите магазин, чтобы добавить товары!",
        "cart.title": "🛒 <b>Ваша корзина покупок</b>\n\n",
        "cart.removed_success": "Товар удален из корзины",
        "cart.cleared_success": "✅ Корзина успешно очищена!",
        "cart.empty_alert": "Корзина пуста!",
        "cart.summary_title": "📦 <b>Сводка заказа</b>\n\n",
        "cart.saved_delivery_info": "Ваша сохраненная информация о доставке:\n\n",
        "cart.delivery_address": "📍 Адрес: {address}\n",
        "cart.delivery_phone": "📞 Телефон: {phone}\n",
        "cart.delivery_note": "📝 Примечание: {note}\n",
        "cart.use_info_question": "\n\nХотите использовать эту информацию или обновить ее?",
        "cart.no_saved_info": "❌ Сохраненная информация о доставке не найдена. Пожалуйста, введите вручную.",

        # === Order/Delivery Flow ===
        "order.delivery.address_prompt": "📍 Пожалуйста, введите ваш адрес доставки:",
        "order.delivery.address_invalid": "❌ Пожалуйста, укажите действительный адрес доставки (минимум 5 символов).",
        "order.delivery.phone_prompt": "📞 Пожалуйста, введите ваш номер телефона (с кодом страны):",
        "order.delivery.phone_invalid": "❌ Пожалуйста, укажите действительный номер телефона (минимум 8 цифр).",
        "order.delivery.note_prompt": "📝 Есть ли какие-то особые инструкции по доставке? (Необязательно)\n\nВы можете пропустить это, нажав на кнопку ниже.",
        "order.delivery.info_save_error": "❌ Ошибка сохранения информации о доставке. Пожалуйста, попробуйте еще раз.",

        # Location Method Choice
        "order.delivery.location_method_prompt": "📍 Как вы хотите указать адрес доставки?\n\nВыберите один из вариантов ниже:",
        "btn.location_method.gps": "📡 Отправить GPS через Telegram",
        "btn.location_method.live_gps": "📍 Поделиться живой геолокацией",
        "btn.location_method.google_link": "🗺 Отправить ссылку Google Maps",
        "btn.location_method.type_address": "✍️ Ввести адрес вручную",
        "order.delivery.gps_prompt": "📍 Нажмите кнопку ниже, чтобы отправить своё местоположение:",
        "order.delivery.gps_hint": "📍 Пожалуйста, используйте кнопку ниже для отправки GPS-локации, или нажмите «Назад» чтобы выбрать другой способ.",
        "order.delivery.live_gps_prompt": "📍 Чтобы поделиться живой геолокацией:\n\n1. Нажмите на скрепку 📎 внизу\n2. Выберите «Геолокация»\n3. Нажмите «Трансляция геолокации»\n4. Выберите время трансляции\n\nВодитель сможет видеть ваше местоположение в реальном времени!",
        "order.delivery.live_gps_saved": "✅ Живая геолокация получена! Водитель сможет отслеживать ваше местоположение.",
        "order.delivery.live_gps_hint": "📍 Пожалуйста, отправьте живую геолокацию через меню вложений (📎 → Геолокация → Трансляция).",
        "order.delivery.google_link_prompt": "🗺 Вставьте ссылку Google Maps с вашим местоположением.\n\nОткройте Google Maps, найдите нужное место, нажмите «Поделиться» и скопируйте ссылку сюда.",
        "order.delivery.google_link_invalid": "❌ Не удалось распознать ссылку Google Maps. Убедитесь, что ссылка начинается с google.com/maps или goo.gl/maps.",
        "order.delivery.address_confirm_prompt": "📍 Ваш адрес:\n<b>{address}</b>\n\n🔗 <a href=\"{maps_link}\">Посмотреть на карте</a>\n\nАдрес верный?",
        "btn.address_confirm_yes": "✅ Да, всё верно",
        "btn.address_confirm_retry": "✏️ Нет, ввести заново",

        # GPS Location (Card 2)
        "order.delivery.location_prompt": "📍 Хотите поделиться GPS-локацией для более точной доставки?\n\nНажмите кнопку ниже или пропустите этот шаг.",
        "order.delivery.location_saved": "✅ Локация сохранена!",
        "btn.share_location": "📍 Поделиться локацией",
        "btn.skip_location": "⏭ Пропустить",

        # Delivery Type (Card 3)
        "order.delivery.type_prompt": "🚚 Выберите тип доставки:",
        "btn.delivery.door": "🚪 Доставка к двери",
        "btn.delivery.dead_drop": "📦 Оставить в указанном месте",
        "btn.delivery.pickup": "🏪 Самовывоз",
        "order.delivery.drop_instructions_prompt": "📝 Опишите, где оставить заказ (например, 'у охранника в лобби', 'под коврик у двери 405'):",
        "order.delivery.drop_gps_prompt": "📍 Отправьте GPS-координаты места, нажав кнопку ниже:",
        "btn.share_drop_location": "📍 Отправить местоположение",
        "order.delivery.drop_gps_saved": "✅ GPS-координаты сохранены!",
        "order.delivery.drop_media_prompt": "📸 Отправьте фото или видео места (можно несколько). Нажмите «Готово», когда закончите:",
        "order.delivery.drop_media_saved": "✅ Сохранено файлов: {count}. Отправьте ещё или нажмите «Готово».",
        "btn.drop_media_done": "✅ Готово",
        "btn.skip_drop_media": "⏭ Пропустить",
        "order.delivery.drop_photo_prompt": "📸 Хотите отправить фото места? (необязательно)",
        "order.delivery.drop_photo_saved": "✅ Фото места сохранено!",
        "btn.skip_drop_photo": "⏭ Пропустить фото",

        # PromptPay (Card 1)
        "order.payment_method.promptpay": "💳 PromptPay QR",
        "order.payment.promptpay.title": "💳 <b>Оплата через PromptPay</b>",
        "order.payment.promptpay.scan": "📱 Сканируйте QR-код для оплаты:",
        "order.payment.promptpay.upload_receipt": "📸 После оплаты отправьте скриншот/фото квитанции:",
        "order.payment.promptpay.receipt_received": "✅ Квитанция получена! Ожидайте подтверждения от администратора.",
        "order.payment.promptpay.receipt_invalid": "❌ Пожалуйста, отправьте фото квитанции.",
        "order.payment.promptpay.slip_verified": "✅ Оплата подтверждена автоматически! Ваш заказ принят.",
        "admin.order.verify_payment": "✅ Подтвердить оплату",
        "admin.order.payment_verified": "✅ Оплата подтверждена",

        # Delivery Chat (Card 13)
        "order.delivery.chat_unavailable": "❌ Чат с водителем недоступен. Группа курьеров не настроена.",
        "order.delivery.chat_started": "💬 Вы можете отправить сообщение водителю. Отправьте текст, фото или локацию.\n\nОтправьте /endchat чтобы завершить чат.",
        "order.delivery.live_location_shared": "📍 Водитель поделился живой локацией! Вы можете отслеживать доставку.",
        "order.delivery.chat_no_active_delivery": "❌ У вас нет активных доставок для чата.",
        "order.delivery.chat_ended": "✅ Чат с водителем завершён.",
        "order.delivery.chat_message_sent": "✅ Сообщение отправлено водителю.",
        "order.delivery.driver_no_active_order": "⚠️ Нет активного заказа для пересылки этого сообщения.",
        "btn.chat_with_driver": "💬 Чат с водителем",

        # GPS tracking & chat session (Card 15)
        "delivery.gps.prompt": "📍 Ваш заказ {order_code} в пути!\n\nПомогите водителю найти вас быстрее — поделитесь своим местоположением:",
        "delivery.gps.btn_static": "📍 Отправить локацию",
        "delivery.gps.btn_live": "📡 Живая локация",
        "delivery.gps.btn_skip": "⏭ Пропустить",
        "delivery.gps.static_sent": "✅ Ваше местоположение отправлено водителю.",
        "delivery.gps.live_started": "📡 Живая локация включена! Водитель видит вас в реальном времени.",
        "delivery.gps.skipped": "⏭ Локация пропущена. Водитель будет использовать адрес из заказа.",
        "delivery.chat.session_closed": "⏹ Сессия чата завершена. Свяжитесь с поддержкой для помощи.",
        "delivery.chat.post_delivery_open": "✅ Доставлено! Чат остаётся открытым ещё {minutes} мин.",
        "delivery.chat.post_delivery_closed": "⏹ Окно чата после доставки закрыто.",
        "btn.end_chat": "❌ Завершить чат",

        # === Bonus/Referral Application ===
        "order.bonus.available": "💰 <b>У вас есть ${bonus_balance} в реферальных бонусах!</b>\n\n",
        "order.bonus.apply_question": "Хотите ли вы применить реферальный бонус к этому заказу?",
        "order.bonus.amount_positive_error": "❌ Пожалуйста, введите положительную сумму.",
        "order.bonus.amount_too_high": "❌ Сумма слишком велика. Максимум применимо: ${max_applicable}\nПожалуйста, введите корректную сумму:",
        "order.bonus.invalid_amount": "❌ Неверная сумма. Пожалуйста, введите число (например, 5.50):",
        "order.bonus.insufficient": "❌ Недостаточный бонусный баланс. Пожалуйста, попробуйте снова.",
        "order.bonus.enter_amount": "Введите сумму бонуса, которую вы хотите применить (максимум ${max_applicable}):\n\nИли используйте все доступные бонусы, нажав кнопку ниже.",

        # === Payment Instructions ===
        "order.payment.system_unavailable": "❌ <b>Платежная система временно недоступна</b>\n\nНет доступных Bitcoin-адресов. Пожалуйста, свяжитесь с поддержкой.",
        "order.payment.customer_not_found": "❌ Информация о клиенте не найдена. Пожалуйста, попробуйте снова.",
        "order.payment.creation_error": "❌ Ошибка создания заказов. Пожалуйста, попробуйте снова или свяжитесь с поддержкой.",

        # === Order Summary/Total ===
        "order.summary.title": "📦 <b>Сводка заказа</b>\n\n",
        "order.summary.cart_total": "Итого корзины: ${cart_total}",
        "order.summary.bonus_applied": "Применен бонус: -${bonus_applied}",
        "order.summary.final_amount": "Итоговая сумма: ${final_amount}",

        # === Inventory/Reservation ===
        "order.inventory.unable_to_reserve": "❌ <b>Не удается зарезервировать товары</b>\n\nСледующие товары недоступны в запрошенных количествах:\n\n{unavailable_items}\n\nПожалуйста, скорректируйте вашу корзину и попробуйте снова.",

        # === My Orders View ===
        "myorders.title": "📦 <b>Мои заказы</b>\n\n",
        "myorders.total": "Всего заказов: {count}",
        "myorders.active": "⏳ Активных заказов: {count}",
        "myorders.delivered": "✅ Доставлено: {count}",
        "myorders.select_category": "Выберите категорию для просмотра заказов:",
        "myorders.active_orders": "⏳ Активные заказы",
        "myorders.delivered_orders": "✅ Доставленные заказы",
        "myorders.all_orders": "📋 Все заказы",
        "myorders.no_orders_yet": "Вы еще не сделали ни одного заказа.\n\nПросмотрите магазин, чтобы начать делать покупки!",
        "myorders.browse_shop": "🛍️ Перейти в магазин",
        "myorders.back": "◀️ Назад",
        "myorders.all_title": "📋 Все заказы",
        "myorders.active_title": "⏳ Активные заказы",
        "myorders.delivered_title": "✅ Доставленные заказы",
        "myorders.invalid_filter": "Неверный фильтр",
        "myorders.not_found": "Заказы не найдены.",
        "myorders.back_to_menu": "◀️ Назад к меню заказов",
        "myorders.select_details": "Выберите заказ для просмотра деталей:",
        "myorders.order_not_found": "Заказ не найден",

        # === Order Details Display ===
        "myorders.detail.title": "📦 <b>Детали заказа #{order_code}</b>\n\n",
        "myorders.detail.status": "📊 <b>Статус:</b> {status}\n",
        "myorders.detail.subtotal": "💵 <b>Подытог:</b> ${subtotal}\n",
        "myorders.detail.bonus_applied": "🎁 <b>Применен бонус:</b> ${bonus}\n",
        "myorders.detail.final_price": "💰 <b>Итоговая цена:</b> ${total}\n",
        "myorders.detail.total_price": "💰 <b>Итоговая цена:</b> ${total}\n",
        "myorders.detail.payment_method": "💳 <b>Способ оплаты:</b> {method}\n",
        "myorders.detail.ordered": "📅 <b>Заказано:</b> {date}\n",
        "myorders.detail.delivery_time": "🚚 <b>Запланированная доставка:</b> {time}\n",
        "myorders.detail.completed": "✅ <b>Завершено:</b> {date}\n",
        "myorders.detail.items": "\n📦 <b>Товары:</b>\n{items}\n",
        "myorders.detail.delivery_info": "\n📍 <b>Информация о доставке:</b>\n{address}\n{phone}\n{note}",

        # === Help System ===
        "help.prompt": "📧 <b>Нужна помощь?</b>\n\n",
        "help.describe_issue": "Пожалуйста, опишите вашу проблему или вопрос, и он будет отправлен напрямую администратору.\n\nВведите ваше сообщение ниже:",
        "help.admin_not_configured": "❌ Извините, контакт администратора не настроен. Пожалуйста, попробуйте позже.",
        "help.admin_notification_title": "📧 <b>Новый запрос помощи</b>\n\n",
        "help.admin_notification_from": "<b>От:</b> @{username} (ID: {user_id})\n",
        "help.admin_notification_message": "<b>Сообщение:</b>\n{message}",
        "help.sent_success": "✅ {auto_message}",
        "help.sent_error": "❌ Не удалось отправить сообщение администратору: {error}\n\nПожалуйста, попробуйте позже.",
        "help.cancelled": "Запрос помощи отменен.",

        # === Admin Order Notifications ===
        "admin.goods.add.stock.error": "❌ Ошибка при добавлении начального запаса: {error}",
        "admin.goods.stock.add_success": "✅ Добавлено {quantity} единиц к \"{item}\"",
        "admin.goods.stock.add_units": "➕ Добавить единицы",
        "admin.goods.stock.current_status": "Текущий статус",
        "admin.goods.stock.error": "❌ Ошибка управления запасами: {error}",
        "admin.goods.stock.insufficient": "❌ Недостаточно запасов. Доступно только {available} единиц.",
        "admin.goods.stock.invalid_quantity": "⚠️ Неверное количество. Введите целое число.",
        "admin.goods.stock.management_title": "Управление запасами: {item}",
        "admin.goods.stock.negative_quantity": "⚠️ Количество не может быть отрицательным.",
        "admin.goods.stock.no_products": "❌ В магазине пока нет товаров",
        "admin.goods.stock.prompt.add_units": "Введите количество единиц для добавления:",
        "admin.goods.stock.prompt.item_name": "Введите название товара для управления запасами:",
        "admin.goods.stock.prompt.remove_units": "Введите количество единиц для удаления:",
        "admin.goods.stock.prompt.set_exact": "Введите точное количество запасов:",
        "admin.goods.stock.redirect_message": "ℹ️ Управление запасами теперь доступно через меню «Управление запасами»",
        "admin.goods.stock.remove_success": "✅ Удалено {quantity} единиц из \"{item}\"",
        "admin.goods.stock.remove_units": "➖ Удалить единицы",
        "admin.goods.stock.select_action": "Выберите действие",
        "admin.goods.stock.set_exact": "⚖️ Установить точное количество",
        "admin.goods.stock.set_success": "✅ Запас для \"{item}\" установлен на {quantity} единиц",
        "admin.order.action_required_title": "⏳ <b>Требуется действие:</b>",
        "admin.order.address_label": "Адрес: {address}",
        "admin.order.amount_to_collect_label": "<b>Сумма к получению: ${amount} {currency}</b>",
        "admin.order.amount_to_receive_label": "<b>Сумма к получению: ${amount} {currency}</b>",
        "admin.order.awaiting_payment_status": "⏳ Ожидание подтверждения оплаты...",
        "admin.order.bitcoin_address_label": "Bitcoin адрес: <code>{address}</code>",
        "admin.order.bonus_applied_label": "Применён бонус: <b>-${amount}</b>",
        "admin.order.customer_label": "Покупатель: {username} (ID: {id})",
        "admin.order.delivery_info_title": "<b>Информация о доставке:</b>",
        "admin.order.items_title": "<b>Товары:</b>",
        "admin.order.new_bitcoin_order": "🔔 <b>Новый BITCOIN заказ получен</b>",
        "admin.order.new_cash_order": "🔔 <b>Новый НАЛИЧНЫЙ заказ получен</b> 💵",
        "admin.order.note_label": "Примечание: {note}",
        "admin.order.order_label": "Заказ: <b>{code}</b>",
        "admin.order.payment_cash": "Наличными при доставке",
        "admin.order.payment_method_label": "Способ оплаты: <b>{method}</b>",
        "admin.order.phone_label": "Телефон: {phone}",
        "admin.order.subtotal_label": "Подытог: <b>${amount} {currency}</b>",
        "admin.order.use_cli_confirm": "Используйте CLI для подтверждения заказа и установки времени доставки:\n<code>python bot_cli.py order --order-code {code} --status-confirmed --delivery-time \"YYYY-MM-DD HH:MM\"</code>",
        "btn.admin.back_to_panel": "🔙 Назад в панель администратора",
        "btn.admin.create_refcode": "➕ Создать реферальный код",
        "btn.admin.list_refcodes": "📋 Список всех кодов",
        "btn.back_to_orders": "◀️ Назад к заказам",
        "btn.create_reference_code": "➕ Создать реферальный код",
        "btn.my_reference_codes": "🔑 Мои реферальные коды",
        "btn.need_help": "❓ Нужна помощь?",
        "cart.item.price_format": "  Цена: {price} {currency} × {quantity}",
        "cart.item.subtotal_format": "  Подытог: {subtotal} {currency}",
        "cart.item.modifiers": "  Модификаторы: {modifiers}",
        "cart.total_format": "<b>Итого: {total} {currency}</b>",
        "cart.add_cancelled": "Добавление отменено",
        "modifier.select_title": "Выберите {label}:",
        "modifier.selected": "Выбрано: {choice}",
        "modifier.required": "(обязательно)",
        "modifier.optional": "(необязательно)",
        "modifier.done": "Готово",
        "modifier.price_extra": "+{price}",
        "modifier.cancelled": "Выбор модификаторов отменён.",
        "help.pending_order.contact_support": "Используйте команду /help для связи с поддержкой.",
        "help.pending_order.issues_title": "<b>Возникли проблемы?</b>",
        "help.pending_order.status": "Ваш заказ в настоящее время ожидает оплаты.",
        "help.pending_order.step1": "1. Отправьте точную сумму на указанный Bitcoin адрес",
        "help.pending_order.step2": "2. Дождитесь подтверждения в блокчейне (обычно 10-60 минут)",
        "help.pending_order.step3": "3. Администратор подтвердит оплату и назначит время доставки",
        "help.pending_order.step4": "4. Ваши товары будут доставлены курьером.",
        "help.pending_order.title": "❓ <b>Нужна помощь с заказом?</b>",
        "help.pending_order.what_to_do_title": "<b>Что делать:</b>",
        "myorders.detail.bitcoin_address_label": "Bitcoin адрес:",
        "myorders.detail.bitcoin_admin_confirm": "После оплаты администратор подтвердит ваш заказ.",
        "myorders.detail.bitcoin_send_instruction": "⚠️ Пожалуйста, отправьте <b>{amount} {currency}</b> Bitcoin на этот адрес.",
        "myorders.detail.cash_awaiting_confirm": "Ваш заказ ожидает подтверждения администратора.",
        "myorders.detail.cash_payment_courier": "Оплата будет произведена курьеру при доставке.",
        "myorders.detail.cash_title": "💵 Оплата при доставке",
        "myorders.detail.cash_will_notify": "Вы будете уведомлены, когда заказ будет подтвержден и установлено время доставки.",
        "myorders.detail.confirmed_title": "✅ <b>Заказ подтвержден!</b>",
        "myorders.detail.delivered_thanks_message": "Спасибо за покупку! Надеемся увидеть вас снова! 🙏",
        "myorders.detail.delivered_title": "📦 <b>Заказ доставлен!</b>",
        "myorders.detail.payment_info_title": "<b>Информация об оплате:</b>",
        "myorders.detail.preparing_message": "Ваш заказ готовится к доставке.",
        "myorders.detail.scheduled_delivery_label": "Запланированная доставка: <b>{time}</b>",
        "myorders.order_summary_format": "{status_emoji} {code} - {items_count} товаров - {total} {currency}",
        "order.bonus.available_label": "Доступный бонус: <b>${amount}</b>",
        "order.bonus.choose_amount_hint": "Вы можете выбрать сколько использовать (до ${max_amount})",
        "order.bonus.enter_amount_title": "💵 <b>Введите сумму бонуса для применения</b>",
        "order.bonus.max_applicable_label": "Максимум применимо: <b>${amount}</b>",
        "order.bonus.order_total_label": "Сумма заказа: <b>${amount} {currency}</b>",
        "order.info.view_status_hint": "💡 Вы можете просмотреть статус заказа в любое время, используя команду /orders.",
        "order.payment.bitcoin.address_title": "<b>Bitcoin адрес для оплаты:</b>",
        "order.payment.bitcoin.admin_confirm": "• После оплаты администратор подтвердит ваш заказ",
        "order.payment.bitcoin.delivery_title": "<b>Доставка:</b>",
        "order.payment.bitcoin.important_title": "⚠️ <b>ВАЖНО:</b>",
        "order.payment.bitcoin.items_title": "<b>Товары:</b>",
        "order.payment.bitcoin.need_help": "Нужна помощь? Используйте /help для связи с поддержкой.",
        "order.payment.bitcoin.one_time_address": "• Этот адрес для ОДНОРАЗОВОГО использования",
        "order.payment.bitcoin.order_code": "Заказ: <b>{code}</b>",
        "order.payment.bitcoin.send_exact": "• Отправьте ТОЧНУЮ сумму, указанную выше",
        "order.payment.bitcoin.title": "💳 <b>Инструкции по оплате Bitcoin</b>",
        "order.payment.bitcoin.total_amount": "Сумма к оплате: <b>{amount} {currency}</b>",

        # Crypto payment (Card 18) — generic strings for all coins
        "crypto.payment.title": "💳 <b>{coin_name} Payment</b>",
        "crypto.payment.order_code": "Order: <b>{code}</b>",
        "crypto.payment.total_fiat": "Total: <b>{amount} {currency}</b>",
        "crypto.payment.rate": "Rate: 1 {coin} = {rate} {currency}",
        "crypto.payment.amount_due": "Amount due: <b>{crypto_amount} {coin}</b>",
        "crypto.payment.address": "<b>Send to this address:</b>\n<code>{address}</code>",
        "crypto.payment.send_exact": "• Send EXACTLY this amount",
        "crypto.payment.one_time": "• This address is for ONE-TIME use",
        "crypto.payment.auto_confirm": "• Your order will be automatically confirmed once the payment is detected on-chain.",
        "crypto.payment.waiting": "⏳ Waiting for payment...\nThis address expires in {timeout} minutes.",
        "crypto.payment.no_address": "❌ No {coin} addresses available. Please contact support or choose another payment method.",
        "crypto.payment_detected": (
            "✅ <b>Payment detected!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "⏳ Waiting for confirmations..."
        ),
        "crypto.payment_confirmed": (
            "✅ <b>Payment confirmed!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "Your order is now being processed."
        ),
        "crypto.payment_expired": "⏰ Payment window for your {coin} order ({order_code}) has expired. Please place a new order.",

        "order.payment.cash.admin_contact": "Администратор свяжется с вами в ближайшее время.",
        "order.payment.cash.after_confirm": "После подтверждения вы будете уведомлены о времени доставки.",
        "order.payment.cash.created": "Ваш заказ {code} создан и ожидает подтверждения администратора.",
        "order.payment.cash.important": "⏳ <b>Важно:</b> Заказ зарезервирован на ограниченное время.",
        "order.payment.cash.items_title": "Товары:",
        "order.payment.cash.payment_to_courier": "Оплата будет произведена курьеру при доставке.",
        "order.payment.cash.title": "💵 <b>Оплата при доставке</b>",
        "order.payment.cash.total": "Итого: {amount}",
        "order.payment.error_general": "❌ Ошибка создания заказа. Попробуйте снова или обратитесь в поддержку.",
        "order.summary.total_label": "<b>Итого: {amount} {currency}</b>",
        "order.payment.bonus_applied_label": "Применён бонус: <b>-{amount} {currency}</b>",
        "order.payment.cash.amount_with_bonus": "<b>Сумма к оплате при доставке: {amount} {currency}</b>",
        "order.payment.cash.total_label": "<b>Итого к оплате при доставке: {amount} {currency}</b>",
        "order.payment.final_amount_label": "<b>Итоговая сумма к оплате: {amount} {currency}</b>",
        "order.payment.order_label": "📋 <b>Заказ: {code}</b>",
        "order.payment.subtotal_label": "Подытог: <b>{amount} {currency}</b>",
        "order.payment.total_amount_label": "<b>Сумма к оплате: {amount} {currency}</b>",

        # === Card 9: Kitchen & Delivery Workflow ===
        "admin.menu.orders": "📋 Заказы",
        "admin.orders.list_title": "📋 <b>Заказы</b>",
        "admin.orders.empty": "Заказов не найдено",
        "admin.orders.filter_status": "Фильтр по статусу",
        "admin.orders.filter_all": "📋 Все заказы",
        "admin.orders.filter_active": "🔄 Активные",
        "admin.orders.detail": (
            "📋 <b>Заказ #{order_id}</b> ({order_code})\n"
            "👤 Покупатель: {buyer_id}\n"
            "💰 Сумма: {total}\n"
            "📦 Статус: {status}\n"
            "📅 Создан: {created_at}\n"
            "📍 Адрес: {address}\n"
            "📞 Телефон: {phone}"
        ),
        "admin.orders.status_changed": "Статус заказа #{order_id} изменён на <b>{new_status}</b>",
        "admin.orders.invalid_transition": "Невозможно изменить статус с {current} на {new}",
        "kitchen.order_received": (
            "🍳 <b>Новый заказ #{order_id}</b> ({order_code})\n\n"
            "{items}\n\n"
            "💰 Сумма: {total}\n"
            "📍 Адрес: {address}\n"
            "📞 Телефон: {phone}"
        ),
        "rider.order_ready": (
            "🚗 <b>Заказ готов #{order_id}</b> ({order_code})\n\n"
            "💰 Сумма: {total}\n"
            "📍 Адрес: {address}\n"
            "📞 Телефон: {phone}"
        ),
        "order.status.preparing": "🍳 Ваш заказ #{order_code} готовится",
        "order.status.ready": "✅ Ваш заказ #{order_code} готов к забору",
        "order.status.out_for_delivery": "🚗 Ваш заказ #{order_code} в пути",
        "order.status.delivered_notify": "📦 Ваш заказ #{order_code} доставлен",
        "kitchen.btn.start_preparing": "🍳 Начать приготовление",
        "kitchen.btn.mark_ready": "✅ Готов",
        "rider.btn.picked_up": "📦 Забрал",
        "rider.btn.delivered": "✅ Доставлен",

        # Delivery Photo Proof (Card 4)
        "delivery.photo.required": "Для доставки с оставлением в указанном месте требуется фото",
        "delivery.photo.upload_prompt": "Пожалуйста, загрузите фото доставки",
        "delivery.photo.received": "Фото доставки сохранено",
        "delivery.photo.sent_to_customer": "Фото доставки отправлено клиенту",
        "delivery.photo.customer_notification": "Ваш заказ {order_code} доставлен! Вот фото подтверждения.",

        # === New Feature Strings ===

        # === Restaurant Feature Strings ===
        "admin.goods.add.allergen.dairy": "Dairy",
        "admin.goods.add.allergen.eggs": "Eggs",
        "admin.goods.add.allergen.fish": "Fish",
        "admin.goods.add.allergen.gluten": "Gluten",
        "admin.goods.add.allergen.nuts": "Nuts",
        "admin.goods.add.allergen.sesame": "Sesame",
        "admin.goods.add.allergen.shellfish": "Shellfish",
        "admin.goods.add.allergen.soy": "Soy",
        "admin.goods.add.allergens.done": "✅ Done",
        "admin.goods.add.allergens.skip": "⏭ No Allergens",
        "admin.goods.add.availability.invalid": "❌ Invalid format. Use HH:MM-HH:MM (e.g. 06:00-22:00)",
        "admin.goods.add.availability.skip": "⏭ All Day",
        "admin.goods.add.daily_limit.invalid": "❌ Enter a positive number.",
        "admin.goods.add.daily_limit.skip": "⏭ Unlimited",
        "admin.goods.add.modifier.add_another_group": "➕ Another Group",
        "admin.goods.add.modifier.add_group": "➕ Add Modifier Group",
        "admin.goods.add.modifier.add_option": "➕ Add Option",
        "admin.goods.add.modifier.all_done": "✅ Finish",
        "admin.goods.add.modifier.finish": "✅ Finish (No Modifiers)",
        "admin.goods.add.modifier.group_added": "✅ Group added! Add another group or finish.",
        "admin.goods.add.modifier.group_name": "Enter modifier group name (e.g. Spice Level):",
        "admin.goods.add.modifier.group_type": "Select type for this group:",
        "admin.goods.add.modifier.option_added": "✅ Option added! Add another or press Done.",
        "admin.goods.add.modifier.option_label": "Enter option label (e.g. Mild, Extra Cheese):",
        "admin.goods.add.modifier.option_price": "Enter price adjustment for this option (0 for free):",
        "admin.goods.add.modifier.options_done": "✅ Done with Options",
        "admin.goods.add.modifier.paste_json": "📋 Paste JSON",
        "admin.goods.add.modifier.required_no": "⭕ Optional",
        "admin.goods.add.modifier.required_yes": "✅ Required",
        "admin.goods.add.modifier.type_multi": "Multi Choice",
        "admin.goods.add.modifier.type_single": "Single Choice",
        "admin.goods.add.photo.done": "✅ Done",
        "admin.goods.add.photo.received": "✅ Media received! Send more or press Done.",
        "admin.goods.add.photo.send_more": "Send more photos/videos or press Done:",
        "admin.goods.add.photo.skip": "⏭ Skip Photos",
        "admin.goods.add.prep_time.invalid": "❌ Enter a positive number.",
        "admin.goods.add.prep_time.skip": "⏭ Skip",
        "admin.goods.add.prompt.allergens": "⚠️ Select allergens (tap to toggle, then Done):",
        "admin.goods.add.prompt.availability": "🕐 Enter availability hours (e.g. 06:00-22:00) or press Skip for all-day:",
        "admin.goods.add.prompt.daily_limit": "📊 Enter daily limit (max units per day) or press Skip for unlimited:",
        "admin.goods.add.prompt.modifier_group": "Add a modifier group (e.g. Spice Level, Extras)?",
        "admin.goods.add.prompt.photo": "📸 Send a photo or video of this item (or press Skip):",
        "admin.goods.add.prompt.prep_time": "⏱ Enter prep time in minutes (or press Skip):",
        "admin.goods.toggle.active_off": "🚫 {item}: Deactivated",
        "admin.goods.toggle.active_on": "✅ {item}: Activated",
        "admin.goods.toggle.sold_out_off": "✅ {item}: Back in stock",
        "admin.goods.toggle.sold_out_on": "❌ {item}: Marked SOLD OUT",
        "btn.view_gallery": "📸 Gallery ({count})",
        "kitchen.order.modifier_detail": "    ↳ {modifiers}",
        "kitchen.order.prep_time": "⏱ Est. prep: {minutes} min",
        "kitchen.order.ready_by": "🕐 Ready by: {time}",
        "order.estimated_ready": "⏱ Estimated ready in ~{minutes} min",
        "shop.item.allergens": "⚠️ Allergens: {allergens}",
        "shop.item.availability": "🕐 Available: {from_time} - {until_time}",
        "shop.item.calories": "🔥 {calories} cal",
        "shop.item.daily_remaining": "📊 Today: {remaining}/{limit} left",
        "shop.item.no_gallery": "No gallery for this item.",
        "shop.item.type_product": "📦 Тип: Товар (упакованный)",
        "shop.item.type_prepared": "🍳 Тип: Приготовление на заказ",
        "shop.item.prep_time": "⏱ Prep: ~{minutes} min",
        "shop.item.sold_out": "❌ Sold out today",
        "admin.accounting.export_payments": "📥 Payment Reconciliation",
        "admin.accounting.export_products": "📥 Revenue by Product",
        "admin.accounting.export_sales": "📥 Export Sales CSV",
        "admin.accounting.export_sent": "✅ Report exported.",
        "admin.accounting.no_data": "No data for this period.",
        "admin.accounting.summary": "📊 <b>Revenue Summary ({period})</b>\n\n💰 Revenue: {total} {currency}\n📦 Orders: {orders}\n📈 Avg: {avg} {currency}\n\n<b>By Payment:</b>\n{payments}\n\n<b>Top Products:</b>\n{products}",
        "admin.accounting.summary_all": "📊 All Time",
        "admin.accounting.summary_month": "📊 This Month",
        "admin.accounting.summary_today": "📊 Today",
        "admin.accounting.summary_week": "📊 This Week",
        "admin.accounting.title": "📊 <b>Accounting & Reports</b>",
        "admin.coupon.create": "➕ Create Coupon",
        "admin.coupon.created": "✅ Coupon <b>{code}</b> created!\nType: {type}\nValue: {value}\nMin order: {min_order}\nMax uses: {max_uses}\nExpires: {expiry}",
        "admin.coupon.detail": "🎟 <b>{code}</b>\nType: {type}\nValue: {value}\nMin Order: {min_order}\nMax Uses: {max_uses}\nUsed: {used}\nStatus: {status}\nExpires: {expiry}",
        "admin.coupon.empty": "No coupons found.",
        "admin.coupon.enter_code": "Enter coupon code (or type <b>auto</b> for random):",
        "admin.coupon.enter_expiry": "Enter expiry in days (or <b>skip</b> for no expiry):",
        "admin.coupon.enter_max_uses": "Enter max total uses (or <b>skip</b> for unlimited):",
        "admin.coupon.enter_min_order": "Enter minimum order amount (or <b>skip</b>):",
        "admin.coupon.enter_value": "Enter discount value ({type}):",
        "admin.coupon.invalid_value": "❌ Invalid value. Enter a number.",
        "admin.coupon.list_active": "📋 Active Coupons",
        "admin.coupon.list_all": "📋 All Coupons",
        "admin.coupon.select_type": "Select discount type:",
        "admin.coupon.title": "🎟 <b>Coupon Management</b>",
        "admin.coupon.toggle_activate": "✅ Activate",
        "admin.coupon.toggle_deactivate": "❌ Deactivate",
        "admin.coupon.toggled": "✅ Coupon {code} is now {status}.",
        "admin.coupon.type_fixed": "💰 Fixed Amount",
        "admin.coupon.type_percent": "📊 Percentage (%)",
        "admin.menu.accounting": "📊 Accounting",
        "admin.menu.coupons": "🎟 Coupons",
        "admin.menu.segment_broadcast": "📣 Targeted Broadcast",
        "admin.menu.stores": "🏪 Stores",
        "admin.menu.tickets": "🎫 Tickets",
        "admin.menu.ai_assistant": "🤖 AI Assistant",
        "admin.segment.all_users": "👥 All Users",
        "admin.segment.count": "📊 Segment: <b>{segment}</b>\nUsers: <b>{count}</b>\n\nType your broadcast message:",
        "admin.segment.empty": "No users in this segment.",
        "admin.segment.high_spenders": "💰 High Spenders",
        "admin.segment.inactive": "😴 Inactive (30+ days)",
        "admin.segment.new_users": "🆕 New Users (7d)",
        "admin.segment.recent_buyers": "🛒 Recent Buyers (7d)",
        "admin.segment.sent": "✅ Sent to {sent}/{total} ({segment}).",
        "admin.segment.title": "📣 <b>Targeted Broadcast</b>\n\nSelect segment:",
        "admin.store.add": "➕ Add Store",
        "admin.store.address_prompt": "Enter store address (or <b>skip</b>):",
        "admin.store.btn_default": "⭐ Set as Default",
        "admin.store.created": "✅ Store <b>{name}</b> created!",
        "admin.store.detail": "🏪 <b>{name}</b>\nStatus: {status}\nDefault: {default}\nAddress: {address}\nLocation: {location}\nPhone: {phone}",
        "admin.store.empty": "No stores configured.",
        "admin.store.location_prompt": "Send GPS location (or type <b>skip</b>):",
        "admin.store.name_exists": "Store with this name already exists.",
        "admin.store.name_prompt": "Enter store name:",
        "admin.store.set_default": "✅ {name} set as default store.",
        "admin.store.title": "🏪 <b>Store Management</b>",
        "admin.store.toggle_activate": "✅ Activate",
        "admin.store.toggle_deactivate": "❌ Deactivate",
        "admin.store.toggled": "✅ Store {name} is now {status}.",
        "admin.ticket.detail": "🎫 <b>Ticket #{code}</b>\nUser: {user_id}\nStatus: {status}\nPriority: {priority}\nSubject: {subject}\nCreated: {date}",
        "admin.ticket.empty": "No open tickets.",
        "admin.ticket.list": "Open/In Progress Tickets:",
        "admin.ticket.reply_prompt": "Reply to ticket #{code}:",
        "admin.ticket.resolved": "✅ Ticket #{code} resolved.",
        "admin.ticket.title": "🎫 <b>Support Tickets</b>",
        "btn.admin.reply_ticket": "💬 Reply",
        "btn.admin.resolve_ticket": "✅ Resolve",
        "btn.apply_coupon": "🎟 Apply Coupon",
        "btn.close_ticket": "✖ Close Ticket",
        "btn.create_ticket": "➕ New Ticket",
        "btn.create_ticket_for_order": "🎫 Support Ticket",
        "btn.invoice": "🧾 Receipt",
        "btn.my_tickets": "🎫 Support",
        "btn.reorder": "🔄 Reorder",
        "btn.reply_ticket": "💬 Reply",
        "btn.review_order": "⭐ Leave Review",
        "btn.search": "🔍 Search",
        "btn.skip_coupon": "⏭ Skip Coupon",
        "coupon.already_used": "❌ You already used this coupon.",
        "coupon.applied": "✅ Coupon applied! Discount: -{discount} {currency}",
        "coupon.enter_code": "🎟 Enter coupon code (or press Skip):",
        "coupon.expired": "❌ This coupon has expired.",
        "coupon.invalid": "❌ Invalid or expired coupon code.",
        "coupon.max_uses_reached": "❌ Coupon usage limit reached.",
        "coupon.min_order_not_met": "❌ Min order of {min_order} required.",
        "coupon.not_yet_valid": "❌ This coupon is not yet valid.",
        "invoice.not_available": "Receipt not available.",
        "reorder.success": "✅ Added {added} item(s) to cart. {skipped} item(s) unavailable.",
        "review.already_reviewed": "You have already reviewed this order.",
        "review.comment_prompt": "You rated {rating}/5 ⭐\n\nAdd a comment? Type or press Skip:",
        "review.detail": "⭐{rating}/5 — {comment}",
        "review.item_rating": "⭐ <b>{item}</b>: {avg:.1f}/5 ({count} reviews)",
        "review.no_reviews": "No reviews yet.",
        "review.prompt": "⭐ <b>Rate your order #{order_code}</b>\n\nSelect your rating:",
        "review.rate_1": "⭐",
        "review.rate_2": "⭐⭐",
        "review.rate_3": "⭐⭐⭐",
        "review.rate_4": "⭐⭐⭐⭐",
        "review.rate_5": "⭐⭐⭐⭐⭐",
        "review.skip_comment": "⏭ Skip",
        "review.thanks": "✅ Thank you for your review! ({rating}/5 ⭐)",
        "search.no_results": "❌ No products found. Try different keywords.",
        "search.prompt": "🔍 Enter product name or keyword to search:",
        "search.result_count": "Found {count} product(s):\n",
        "search.results_title": "🔍 <b>Search results for:</b> {query}\n\n",
        "ticket.admin_replied": "💬 Admin replied to ticket #{code}:\n{text}",
        "ticket.closed": "✅ Ticket closed.",
        "ticket.created": "✅ Ticket <b>#{code}</b> created!",
        "ticket.message_format": "<b>{role}</b> ({date}):\n{text}\n",
        "ticket.message_prompt": "Describe your issue:",
        "ticket.no_tickets": "No support tickets.",
        "ticket.reply_prompt": "Type your reply:",
        "ticket.reply_sent": "✅ Reply sent.",
        "ticket.resolved_notification": "✅ Ticket #{code} resolved!",
        "ticket.status.closed": "⚫ Closed",
        "ticket.status.in_progress": "🔵 In Progress",
        "ticket.status.open": "🟢 Open",
        "ticket.status.resolved": "✅ Resolved",
        "ticket.subject_prompt": "Enter the subject:",
        "ticket.title": "🎫 <b>Support Tickets</b>",
        "ticket.view_title": "🎫 <b>Ticket #{code}</b>\nStatus: {status}\nSubject: {subject}\nCreated: {date}",

        # === Product Search ===
        "btn.search": "🔍 Поиск",
        "search.prompt": "🔍 Введите название или ключевое слово для поиска:",
        "search.results_title": "🔍 <b>Результаты поиска:</b> {query}\n\n",
        "search.no_results": "❌ Товары не найдены. Попробуйте другие ключевые слова.",
        "search.result_count": "Найдено {count} товар(ов):\n",

        # === Reorder ===
        "btn.reorder": "🔄 Повторить заказ",
        "reorder.success": "✅ Добавлено {added} товар(ов) в корзину. {skipped} товар(ов) недоступно.",

        # === Coupon / Promo Codes ===
        "admin.menu.coupons": "🎟 Купоны",
        "admin.coupon.title": "🎟 <b>Управление купонами</b>",
        "admin.coupon.create": "➕ Создать купон",
        "admin.coupon.list_active": "📋 Активные купоны",
        "admin.coupon.list_all": "📋 Все купоны",
        "admin.coupon.enter_code": "Введите код купона (или <b>auto</b> для случайного):",
        "admin.coupon.select_type": "Выберите тип скидки:",
        "admin.coupon.type_percent": "📊 Процент (%)",
        "admin.coupon.type_fixed": "💰 Фиксированная сумма",
        "admin.coupon.enter_value": "Введите значение скидки ({type}):",
        "admin.coupon.enter_min_order": "Мин. сумма заказа (или <b>skip</b>):",
        "admin.coupon.enter_max_uses": "Макс. использований (или <b>skip</b>):",
        "admin.coupon.enter_expiry": "Срок действия в днях (или <b>skip</b>):",
        "admin.coupon.created": "✅ Купон <b>{code}</b> создан!\nТип: {type}\nСкидка: {value}\nМин. заказ: {min_order}\nМакс. использований: {max_uses}\nИстекает: {expiry}",
        "admin.coupon.invalid_value": "❌ Неверное значение. Введите число.",
        "admin.coupon.empty": "Купоны не найдены.",
        "admin.coupon.detail": "🎟 <b>{code}</b>\nТип: {type}\nСкидка: {value}\nМин. заказ: {min_order}\nМакс. использований: {max_uses}\nИспользовано: {used}\nСтатус: {status}\nИстекает: {expiry}",
        "admin.coupon.toggled": "✅ Купон {code} теперь {status}.",
        "admin.coupon.toggle_activate": "✅ Активировать",
        "admin.coupon.toggle_deactivate": "❌ Деактивировать",
        "coupon.invalid": "❌ Неверный или просроченный код купона.",
        "coupon.min_order_not_met": "❌ Мин. заказ {min_order} для этого купона.",
        "coupon.already_used": "❌ Вы уже использовали этот купон.",
        "coupon.max_uses_reached": "❌ Купон исчерпан.",
        "coupon.expired": "❌ Купон просрочен.",
        "coupon.not_yet_valid": "❌ Купон ещё не действует.",
        "coupon.applied": "✅ Купон применён! Скидка: -{discount} {currency}",
        "coupon.enter_code": "🎟 Введите код купона (или нажмите Пропустить):",
        "btn.skip_coupon": "⏭ Пропустить купон",
        "btn.apply_coupon": "🎟 Применить купон",

        # === Review / Rating System ===
        "btn.review_order": "⭐ Оставить отзыв",
        "review.prompt": "⭐ <b>Оцените заказ #{order_code}</b>\n\nВыберите оценку:",
        "review.rate_1": "⭐",
        "review.rate_2": "⭐⭐",
        "review.rate_3": "⭐⭐⭐",
        "review.rate_4": "⭐⭐⭐⭐",
        "review.rate_5": "⭐⭐⭐⭐⭐",
        "review.comment_prompt": "Вы поставили {rating}/5 ⭐\n\nХотите добавить комментарий? Напишите или нажмите Пропустить:",
        "review.skip_comment": "⏭ Пропустить",
        "review.thanks": "✅ Спасибо за отзыв! ({rating}/5 ⭐)",
        "review.already_reviewed": "Вы уже оставили отзыв на этот заказ.",
        "review.item_rating": "⭐ <b>{item}</b>: {avg:.1f}/5 ({count} отзывов)",
        "review.no_reviews": "Отзывов пока нет.",
        "review.detail": "⭐{rating}/5 — {comment}",

        # === Invoice / Receipt ===
        "btn.invoice": "🧾 Чек",
        "invoice.not_available": "Чек недоступен для этого заказа.",

        # === Support Ticketing ===
        "btn.my_tickets": "🎫 Поддержка",
        "btn.create_ticket": "➕ Новый тикет",
        "btn.create_ticket_for_order": "🎫 Тикет поддержки",
        "ticket.title": "🎫 <b>Тикеты поддержки</b>",
        "ticket.no_tickets": "У вас нет тикетов.",
        "ticket.subject_prompt": "Введите тему обращения:",
        "ticket.message_prompt": "Опишите вашу проблему:",
        "ticket.created": "✅ Тикет <b>#{code}</b> создан! Мы скоро ответим.",
        "ticket.view_title": "🎫 <b>Тикет #{code}</b>\nСтатус: {status}\nТема: {subject}\nСоздан: {date}",
        "ticket.reply_prompt": "Напишите ваш ответ:",
        "ticket.reply_sent": "✅ Ответ отправлен.",
        "ticket.closed": "✅ Тикет закрыт.",
        "ticket.message_format": "<b>{role}</b> ({date}):\n{text}\n",
        "btn.reply_ticket": "💬 Ответить",
        "btn.close_ticket": "✖ Закрыть тикет",
        "ticket.status.open": "🟢 Открыт",
        "ticket.status.in_progress": "🔵 В работе",
        "ticket.status.resolved": "✅ Решён",
        "ticket.status.closed": "⚫ Закрыт",
        "ticket.admin_replied": "💬 Администратор ответил на тикет #{code}:\n{text}",
        "ticket.resolved_notification": "✅ Ваш тикет #{code} решён!",

        # === Admin Tickets ===
        "admin.menu.tickets": "🎫 Тикеты",
        "admin.menu.ai_assistant": "🤖 AI Ассистент",
        "admin.ticket.title": "🎫 <b>Тикеты поддержки</b>",
        "admin.ticket.list": "Открытые тикеты:",
        "admin.ticket.empty": "Нет открытых тикетов.",
        "admin.ticket.reply_prompt": "Ответ на тикет #{code}:",
        "admin.ticket.resolved": "✅ Тикет #{code} решён.",
        "admin.ticket.detail": "🎫 <b>Тикет #{code}</b>\nПользователь: {user_id}\nСтатус: {status}\nПриоритет: {priority}\nТема: {subject}\nСоздан: {date}",
        "btn.admin.resolve_ticket": "✅ Решить",
        "btn.admin.reply_ticket": "💬 Ответить",

        # === Accounting / Revenue Export ===
        "admin.menu.accounting": "📊 Бухгалтерия",
        "admin.accounting.title": "📊 <b>Бухгалтерия и отчёты</b>",
        "admin.accounting.summary_today": "📊 Сегодня",
        "admin.accounting.summary_week": "📊 Неделя",
        "admin.accounting.summary_month": "📊 Месяц",
        "admin.accounting.summary_all": "📊 Всё время",
        "admin.accounting.export_sales": "📥 Экспорт продаж CSV",
        "admin.accounting.export_products": "📥 Выручка по товарам",
        "admin.accounting.export_payments": "📥 Сверка платежей",
        "admin.accounting.summary": "📊 <b>Сводка выручки ({period})</b>\n\n💰 Общая выручка: {total} {currency}\n📦 Заказов: {orders}\n📈 Средний чек: {avg} {currency}\n\n<b>По способу оплаты:</b>\n{payments}\n\n<b>Топ товаров:</b>\n{products}",
        "admin.accounting.export_sent": "✅ Отчёт экспортирован.",
        "admin.accounting.no_data": "Нет данных за этот период.",

        # === Customer Segmentation ===
        "admin.menu.segment_broadcast": "📣 Адресная рассылка",
        "admin.segment.title": "📣 <b>Адресная рассылка</b>\n\nВыберите сегмент:",
        "admin.segment.all_users": "👥 Все пользователи",
        "admin.segment.high_spenders": "💰 Крупные покупатели",
        "admin.segment.recent_buyers": "🛒 Недавние покупатели (7 дн)",
        "admin.segment.inactive": "😴 Неактивные (30+ дн)",
        "admin.segment.new_users": "🆕 Новые пользователи (7 дн)",
        "admin.segment.count": "📊 Сегмент: <b>{segment}</b>\nПользователей: <b>{count}</b>\n\nВведите текст рассылки:",
        "admin.segment.empty": "Нет пользователей в этом сегменте.",
        "admin.segment.sent": "✅ Рассылка: {sent}/{total} ({segment}).",

        # === Multi-Store / Multi-Location ===
        "admin.menu.stores": "🏪 Точки продаж",
        "admin.store.title": "🏪 <b>Управление точками</b>",
        "admin.store.add": "➕ Добавить точку",
        "admin.store.name_prompt": "Введите название точки:",
        "admin.store.address_prompt": "Введите адрес (или <b>skip</b>):",
        "admin.store.location_prompt": "Отправьте GPS-координаты (или <b>skip</b>):",
        "admin.store.created": "✅ Точка <b>{name}</b> создана!",
        "admin.store.detail": "🏪 <b>{name}</b>\nСтатус: {status}\nПо умолчанию: {default}\nАдрес: {address}\nМестоположение: {location}\nТелефон: {phone}",
        "admin.store.toggled": "✅ Точка {name} теперь {status}.",
        "admin.store.set_default": "✅ {name} — точка по умолчанию.",
        "admin.store.toggle_activate": "✅ Активировать",
        "admin.store.toggle_deactivate": "❌ Деактивировать",
        "admin.store.btn_default": "⭐ По умолчанию",
        "admin.store.empty": "Точки не настроены.",
        "admin.store.name_exists": "Точка с таким названием уже существует.",

        # === PDPA Privacy Policy ===
        "btn.privacy": "🔒 Политика конфиденциальности",
        "privacy.notice": (
            "🔒 <b>Уведомление о конфиденциальности (PDPA)</b>\n\n"
            "Мы соблюдаем Закон о защите персональных данных Таиланда (PDPA).\n\n"
            "<b>Данные, которые мы собираем:</b>\n"
            "• Имя / телефон / адрес доставки\n"
            "• Детали и история заказов\n"
            "• Telegram ID\n\n"
            "<b>Цели обработки:</b>\n"
            "• Оформление и доставка заказов (договорная необходимость)\n"
            "• Предотвращение мошенничества\n"
            "• Маркетинг — только с вашего отдельного согласия\n\n"
            "<b>Срок хранения:</b> до удаления вами или 2 года после последнего заказа\n\n"
            "<b>Передача данных:</b> ресторанам, курьерам, платёжным системам — только для выполнения заказа. "
            "Мы не продаём ваши данные.\n\n"
            "<b>Ваши права по PDPA:</b>\n"
            "• Доступ / исправление / удаление данных\n"
            "• Отзыв согласия (для маркетинга)\n"
            "• Возражение / перенос данных\n"
            "• Жалоба в PDPC\n\n"
            "<b>Контроллер данных:</b> {company}\n"
            "Контакт: {email}\n\n"
            "Продолжая использование бота, вы подтверждаете ознакомление с данной политикой."
        ),
        "privacy.btn_full_policy": "📄 Полная политика",
        "privacy.btn_accept": "✅ Принять и продолжить",
        "privacy.accepted": "✅ Вы приняли политику конфиденциальности.",
        "privacy.already_accepted": "✅ Вы уже приняли политику конфиденциальности.",
        "privacy.no_url": "Полная политика конфиденциальности пока не настроена.",
    },

    "en": {
        # === Common Buttons ===
        "btn.shop": "🏪 Shop",
        "btn.rules": "📜 Rules",
        "btn.profile": "👤 Profile",
        "btn.support": "🆘 Support",
        "btn.channel": "ℹ News channel",
        "btn.admin_menu": "🎛 Admin panel",
        "btn.back": "⬅️ Back",
        "btn.close": "✖ Close",
        "btn.yes": "✅ Yes",
        "btn.no": "❌ No",
        "btn.check_subscription": "🔄 Check subscription",
        "btn.admin.ban_user": "🚫 Ban user",
        "btn.admin.unban_user": "✅ Unban user",

        # === Admin Buttons (user management shortcuts) ===
        "btn.admin.promote": "⬆️ Make admin",
        "btn.admin.demote": "⬇️ Remove admin",
        "btn.admin.add_user_bonus": "🎁 Add referral bonus",

        # === Titles / Generic Texts ===
        "menu.title": "⛩️ Main menu",
        "admin.goods.add.stock.error": "❌ Error adding initial stock: {error}",
        "admin.goods.stock.add_success": "✅ Added {quantity} units to \"{item}\"",
        "admin.goods.stock.add_units": "➕ Add units",
        "admin.goods.stock.current_status": "Current Status",
        "admin.goods.stock.error": "❌ Error managing stock: {error}",
        "admin.goods.stock.insufficient": "❌ Insufficient stock. Only {available} units available.",
        "admin.goods.stock.invalid_quantity": "⚠️ Invalid quantity. Enter a whole number.",
        "admin.goods.stock.management_title": "Stock Management: {item}",
        "admin.goods.stock.negative_quantity": "⚠️ Quantity cannot be negative.",
        "admin.goods.stock.no_products": "❌ No products in the shop yet",
        "admin.goods.stock.prompt.add_units": "Enter the number of units to add:",
        "admin.goods.stock.prompt.item_name": "Enter the product name to manage stock:",
        "admin.goods.stock.prompt.remove_units": "Enter the number of units to remove:",
        "admin.goods.stock.prompt.set_exact": "Enter the exact stock quantity:",
        "admin.goods.stock.redirect_message": "ℹ️ Stock management is now available through the \"Manage Stock\" menu",
        "admin.goods.stock.remove_success": "✅ Removed {quantity} units from \"{item}\"",
        "admin.goods.stock.remove_units": "➖ Remove units",
        "admin.goods.stock.select_action": "Select action",
        "admin.goods.stock.set_exact": "⚖️ Set exact quantity",
        "admin.goods.stock.set_success": "✅ Stock for \"{item}\" set to {quantity} units",
        "admin.goods.stock.status_title": "📊 Stock Status:",
        "errors.invalid_item_name": "❌ Invalid item name",
        "errors.invalid_language": "Invalid language",
        "shop.error.brand_required": "Please select a brand first",
        "shop.error.branch_unavailable": "Branch not available",
        "profile.caption": "👤 <b>Profile</b> — <a href='tg://user?id={id}'>{name}</a>",
        "rules.not_set": "❌ Rules have not been added",
        "admin.users.cannot_ban_owner": "❌ Cannot ban the owner",
        "admin.users.ban.success": "✅ User {name} has been successfully banned",
        "admin.users.ban.failed": "❌ Failed to ban user",
        "admin.users.ban.notify": "⛔ You have been banned by an administrator",
        "admin.users.unban.success": "✅ User {name} has been successfully unbanned",
        "admin.users.unban.failed": "❌ Failed to unban user",
        "admin.users.unban.notify": "✅ You have been unbanned by an administrator",

        # === Profile ===
        "btn.referral": "🎲 Referral system",
        "btn.purchased": "🎁 Purchased goods",
        "profile.referral_id": "👤 <b>Referral</b> — <code>{id}</code>",

        # === Subscription Flow ===
        "subscribe.prompt": "First, subscribe to the news channel",

        # === Profile Info Lines ===
        "profile.id": "🆔 <b>ID</b> — <code>{id}</code>",
        "profile.bonus_balance": "💰 <b>Referral Bonus:</b> ${bonus_balance}",
        "profile.purchased_count": "🎁 <b>Purchased items</b> — {count} pcs",
        "profile.registration_date": "🕢 <b>Registered at</b> — <code>{dt}</code>",

        # === Referral ===
        "referral.title": "💚 Referral system",
        "referral.count": "Referrals count: {count}",
        "referral.description": (
            "📔 The referral system lets you earn without any investment. "
            "Share your personal link and you will receive {percent}% of your referrals’ "
            "top-ups to your bot balance."
        ),
        "btn.view_referrals": "👥 My referrals",
        "btn.view_earnings": "💰 My earnings",

        "referrals.list.title": "👥 Your referrals:",
        "referrals.list.empty": "You don't have any active referrals yet",
        "referrals.item.format": "ID: {telegram_id} | Earned: {total_earned} {currency}",

        "referral.earnings.title": "💰 Earnings from referral <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>):",
        "referral.earnings.empty": "No earnings from this referral <code>{id}</code> (<a href='tg://user?id={id}'>{name}</a>) yet",
        "referral.earning.format": "{amount} {currency} | {date} | (from {original_amount} {currency})",
        "referral.item.info": ("💰 Earning number: <code>{id}</code>\n"
                               "👤 Referral: <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>)\n"
                               "🔢 Amount: {amount} {currency}\n"
                               "🕘 Date: <code>{date}</code>\n"
                               "💵 From a deposit to {original_amount} {currency}"),

        "referral.admin_bonus.info": ("💰 Earning number: <code>{id}</code>\n"
                                      "🎁 <b>Bonus from administrator</b>\n"
                                      "🔢 Amount: {amount} {currency}\n"
                                      "🕘 Date: <code>{date}</code>"),

        "all.earnings.title": "💰 All your referral earnings:",
        "all.earnings.empty": "You have no referral earnings yet",
        "all.earning.format.admin": "{amount} {currency} from Admin | {date}",

        "referrals.stats.template": (
            "📊 Referral system statistics:\n\n"
            "👥 Active referrals: {active_count}\n"
            "💰 Total earned: {total_earned} {currency}\n"
            "📈 Total referrals top-ups: {total_original} {currency}\n"
            "🔢 Number of earnings: {earnings_count}"
        ),

        # === Admin: Main Menu ===
        "admin.menu.main": "⛩️ Admin Menu",
        "admin.menu.shop": "🛒 Shop management",
        "admin.menu.goods": "📦 Items management",
        "admin.menu.categories": "📂 Categories management",
        "admin.menu.users": "👥 Users management",
        "admin.menu.broadcast": "📝 Broadcast",
        "admin.menu.rights": "Insufficient permissions",

        # === Admin: User Management ===
        "admin.users.prompt_enter_id": "👤 Enter the user ID to view / edit data",
        "admin.users.invalid_id": "⚠️ Please enter a valid numeric user ID.",
        "admin.users.profile_unavailable": "❌ Profile unavailable (such user never existed)",
        "admin.users.not_found": "❌ User not found",
        "admin.users.cannot_change_owner": "You cannot change the owner’s role",
        "admin.users.referrals": "👥 <b>User referrals</b> — {count}",
        "admin.users.btn.view_referrals": "👥 User's referrals",
        "admin.users.btn.view_earnings": "💰 User's earnings",
        "admin.users.role": "🎛 <b>Role</b> — {role}",
        "admin.users.set_admin.success": "✅ Role assigned to {name}",
        "admin.users.set_admin.notify": "✅ You have been granted the ADMIN role",
        "admin.users.remove_admin.success": "✅ Admin role revoked from {name}",
        "admin.users.remove_admin.notify": "❌ Your ADMIN role has been revoked",
        "admin.users.bonus.prompt": "Enter bonus amount in {currency}:",
        "admin.users.bonus.added": "✅ {name}'s referral bonus has been topped up by {amount} {currency}",
        "admin.users.bonus.added.notify": "🎁 You have been credited with a referral bonus of {amount} {currency}",
        "admin.users.bonus.invalid": "❌ Invalid amount. Enter a number from {min_amount} to {max_amount} {currency}.",

        # === Admin: Shop Management Menu ===
        "admin.shop.menu.title": "⛩️ Shop management",
        "admin.shop.menu.statistics": "📊 Statistics",
        "admin.shop.menu.logs": "📁 Show logs",
        "admin.shop.menu.admins": "👮 Admins",
        "admin.shop.menu.users": "👤 Users",

        # === Admin: Categories Management ===
        "admin.categories.menu.title": "⛩️ Categories management",
        "admin.categories.add": "➕ Add category",
        "admin.categories.rename": "✏️ Rename category",
        "admin.categories.delete": "🗑 Delete category",
        "admin.categories.prompt.add": "Enter a new category name:",
        "admin.categories.prompt.delete": "Enter the category name to delete:",
        "admin.categories.prompt.rename.old": "Enter the current category name to rename:",
        "admin.categories.prompt.rename.new": "Enter the new category name:",
        "admin.categories.add.exist": "❌ Category not created (already exists)",
        "admin.categories.add.success": "✅ Category created",
        "admin.categories.delete.not_found": "❌ Category not deleted (does not exist)",
        "admin.categories.delete.success": "✅ Category deleted",
        "admin.categories.rename.not_found": "❌ Category cannot be updated (does not exist)",
        "admin.categories.rename.exist": "❌ Cannot rename (a category with this name already exists)",
        "admin.categories.rename.success": "✅ Category \"{old}\" renamed to \"{new}\"",

        # === Admin: Goods / Items Management (Add / List / Item Info) ===
        "admin.goods.add_position": "➕ add item",
        "admin.goods.manage_stock": "➕ Add product to item",
        "admin.goods.update_position": "📝 change item",
        "admin.goods.delete_position": "❌ delete item",
        "admin.goods.add.prompt.type": "Choose the item type:",
        "admin.goods.add.type.prepared": "🍳 Made to order (food, beverages)",
        "admin.goods.add.type.product": "📦 Packaged product (water, snacks)",
        "admin.goods.add.prompt.name": "Enter the item name",
        "admin.goods.add.name.exists": "❌ Item cannot be created (it already exists)",
        "admin.goods.add.prompt.description": "Enter item description:",
        "admin.goods.add.prompt.price": "Enter item price (number in {currency}):",
        "admin.goods.add.price.invalid": "⚠️ Invalid price. Please enter a number.",
        "admin.goods.add.prompt.category": "Enter the category the item belongs to:",
        "admin.goods.add.category.not_found": "❌ Item cannot be created (invalid category provided)",
        "admin.goods.position.not_found": "❌ No goods (this item doesn't exist)",
        "admin.goods.menu.title": "⛩️ Items management menu",
        "admin.goods.add.stock.prompt": "Enter the quantity of goods to add",
        "admin.goods.add.stock.invalid": "⚠️ Incorrect quantity value. Please enter a number.",
        "admin.goods.add.stock.negative": "⚠️ Incorrect quantity value. Enter a positive number.",
        "admin.goods.add.result.created_with_stock": "✅ Item {item_name} created, {stock_quantity} added to the quantity of goods.",

        # === Admin: Goods / Items Update Flow ===
        "admin.goods.update.position.invalid": "Item not found.",
        "admin.goods.update.position.exists": "An item with this name already exists.",
        "admin.goods.update.prompt.name": "Enter the item name",
        "admin.goods.update.not_exists": "❌ Item cannot be updated (does not exist)",
        "admin.goods.update.prompt.new_name": "Enter a new item name:",
        "admin.goods.update.prompt.description": "Enter item description:",
        "admin.goods.update.success": "✅ Item updated",

        # === Admin: Goods / Items Delete Flow ===
        "admin.goods.delete.prompt.name": "Enter the item name",
        "admin.goods.delete.position.not_found": "❌ item not deleted (this item doesn't exist)",
        "admin.goods.delete.position.success": "✅ item deleted",

        # === Admin: Item Info ===
        "admin.goods.view_stock": "View items",

        # Admin Modifier Management (Card 8)
        "admin.goods.manage_modifiers": "🍳 Modifiers",
        "admin.goods.modifiers.prompt": "Would you like to add modifiers (spice, extras, etc.)?",
        "admin.goods.modifiers.add_btn": "➕ Add Modifiers",
        "admin.goods.modifiers.skip_btn": "⏭ Skip",
        "admin.goods.modifiers.json_prompt": "Paste the modifier JSON schema (see docs for format):",
        "admin.goods.modifiers.invalid_json": "❌ Invalid JSON: {error}",
        "admin.goods.modifiers.select_item": "Enter the product name to configure modifiers:",
        "admin.goods.modifiers.edit_instructions": "Choose an action:",
        "admin.goods.modifiers.set_new": "📝 Set New",
        "admin.goods.modifiers.clear": "🗑 Clear All",

        # === Admin: Logs ===
        "admin.shop.logs.caption": "Bot logs",
        "admin.shop.logs.empty": "❗️ No logs yet",

        # === Group Notifications ===
        "shop.group.new_upload": "New stock",
        "shop.group.item": "Item",
        "shop.group.stock": "Quantity",

        # === Admin: Statistics ===
        "admin.shop.stats.template": (
            "Shop statistics:\n"
            "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            "<b>◽USERS</b>\n"
            "◾️Users in last 24h: {today_users}\n"
            "◾️Total admins: {admins}\n"
            "◾️Total users: {users}\n"
            "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            "◽<b>MISC</b>\n"
            "◾Items: {items} pcs\n"
            "◾Positions: {goods} pcs\n"
            "◾Categories: {categories} pcs\n"
        ),

        # === Admin: Lists & Broadcast ===
        "admin.shop.admins.title": "👮 Bot admins:",
        "admin.shop.users.title": "Bot users:",
        "broadcast.prompt": "Send a message to broadcast:",
        "broadcast.creating": "📤 Starting the newsletter...\n👥 Total users: {ids}",
        "broadcast.progress": (
            "📤 Broadcasting in progress...\n\n\n"
            "📊 Progress: {progress:.1f}%{n}"
            "✅ Sent: {sent}/{total}\n"
            "❌ Errors: {failed}\n"
            "⏱ Time elapsed: {time} sec"),
        "broadcast.done": (
            "✅ Broadcasting is complete! \n\n"
            "📊 Statistics:📊\n"
            "👥 Total: {total}\n"
            "✅ Delivered: {sent}\n"
            "❌ Undelivered: {failed}\n"
            "🚫 Blocked bot: ~{blocked}\n"
            "📈 Success rate: {success}%\n"
            "⏱ Time: {duration} sec"
        ),
        "broadcast.cancel": "❌ The broadcast has been canceled.",
        "broadcast.warning": "No active broadcast",

        # === Brand / Store Selection ===
        "shop.brands.title": "🏪 Choose a restaurant",
        "shop.branches.title": "📍 Choose a branch",
        "shop.no_brands": "No restaurants available at the moment.",
        "shop.brand_unavailable": "This restaurant is currently unavailable.",

        # === Shop Browsing (Categories / Goods / Item Page) ===
        "shop.categories.title": "🏪 Shop categories",
        "shop.goods.choose": "🏪 Choose a product",
        "shop.item.not_found": "Item not found",
        "shop.item.title": "🏪 Item {name}",
        "shop.item.description": "Description: {description}",
        "shop.item.price": "Price — {amount} {currency}",
        "shop.item.quantity_unlimited": "Quantity — unlimited",
        "shop.item.quantity_left": "Quantity — {count} pcs",
        "shop.item.quantity_detailed": "📦 Total in stock: {total} pcs\n🔒 Reserved: {reserved} pcs\n✅ Available to order: {available} pcs",

        # === Purchases ===
        "purchases.title": "Purchased items:",
        "purchases.pagination.invalid": "Invalid pagination data",
        "purchases.item.not_found": "Purchase not found",
        "purchases.item.name": "<b>🧾 Item</b>: <code>{name}</code>",
        "purchases.item.price": "<b>💵 Price</b>: <code>{amount}</code> {currency}",
        "purchases.item.datetime": "<b>🕒 Purchased at</b>: <code>{dt}</code>",
        "purchases.item.unique_id": "<b>🧾 Unique ID</b>: <code>{uid}</code>",
        "purchases.item.value": "<b>🔑 Value</b>:\n<code>{value}</code>",

        # === Middleware ===
        "middleware.ban": "⏳ You are temporarily blocked. Wait {time} seconds.",
        "middleware.above_limits": "⚠️ Too many requests! You are temporarily blocked.",
        "middleware.waiting": "⏳ Wait {time} seconds for the next action.",
        "middleware.security.session_outdated": "⚠️ Session is outdated. Please start again.",
        "middleware.security.invalid_data": "❌ Invalid data",
        "middleware.security.blocked": "❌ Access blocked",
        "middleware.security.not_admin": "⛔ Insufficient permissions",
        "middleware.security.banned": "⛔ <b>You have been banned</b>\n\nReason: {reason}",
        "middleware.security.banned_no_reason": "⛔ <b>You have been banned</b>\n\nPlease contact the administrator for more information.",
        "middleware.security.rate_limit": "⚠️ Too many requests! Please wait a moment.",

        # === Errors ===
        "errors.not_subscribed": "You are not subscribed",
        "errors.pagination_invalid": "Invalid pagination data",
        "errors.invalid_data": "❌ Invalid data",
        "errors.channel.telegram_not_found": "I can't write to the channel. Add me as a channel admin for uploads @{channel} with the right to publish messages.",
        "errors.channel.telegram_forbidden_error": "Channel not found. Check the channel username for uploads @{channel}.",
        "errors.channel.telegram_bad_request": "Failed to send to the channel for uploads: {e}",

        # === Orders ===
        "order.payment_method.choose": "💳 Choose payment method:",
        "order.payment_method.bitcoin": "💳 Bitcoin",
        "order.payment_method.litecoin": "💳 Litecoin",
        "order.payment_method.solana": "💳 SOL",
        "order.payment_method.usdt_sol": "💳 USDT (Solana)",
        "order.payment_method.cash": "💵 Cash on Delivery",
        "order.status.notify_order_confirmed": (
            "Order {order_code} confirmed! 🎉\n\n"
            "Your order will be delivered at: {delivery_time}\n\n"
            "Items:\n{items}\n\n"
            "Total: {total}\n\n"
            "Wait for delivery!"
        ),
        "order.status.notify_order_delivered": (
            "Order {order_code} delivered! ✅\n\n"
            "Thank you for your purchase! We look forward to seeing you again! 🙏"
        ),
        "order.status.notify_order_modified": (
            "Order {order_code} modified by admin 📝\n\n"
            "Changes:\n{changes}\n\n"
            "New total: {total}"
        ),

        # === Additional Common Buttons ===
        "btn.cart": "🛒 Cart",
        "btn.my_orders": "📦 My Orders",
        "btn.reference_codes": "🔑 Reference Codes",
        "btn.settings": "⚙️ Settings",
        "btn.referral_bonus_percent": "💰 Referral Bonus %",
        "btn.order_timeout": "⏱️ Order Timeout",
        "btn.timezone": "🌍 Timezone",
        "btn.promptpay_account": "💳 PromptPay Account",
        "btn.currency": "💱 Currency",
        "btn.skip": "⏭️ Skip",
        "btn.use_saved_info": "✅ Use Saved Info",
        "btn.update_info": "✏️ Update Info",
        "btn.back_to_cart": "◀️ Back to Cart",
        "btn.clear_cart": "🗑️ Clear Cart",
        "btn.proceed_checkout": "💳 Proceed to Checkout",
        "btn.remove_item": "❌ Remove {item_name}",
        "btn.use_all_bonus": "Use all ${amount}",
        "btn.apply_bonus_yes": "✅ Yes, apply bonus",
        "btn.apply_bonus_no": "❌ No, save for later",
        "btn.cancel": "❌ Cancel",
        "btn.add_to_cart": "🛒 Add to Cart",

        # === Cart Management ===
        "cart.add_success": "✅ {item_name} added to cart!",
        "cart.add_error": "❌ {message}",
        "cart.empty": "🛒 Your cart is empty.\n\nBrowse the shop to add items!",
        "cart.title": "🛒 <b>Your Shopping Cart</b>\n\n",
        "cart.removed_success": "Item removed from cart",
        "cart.cleared_success": "✅ Cart cleared successfully!",
        "cart.empty_alert": "Cart is empty!",
        "cart.summary_title": "📦 <b>Order Summary</b>\n\n",
        "cart.saved_delivery_info": "Your saved delivery information:\n\n",
        "cart.delivery_address": "📍 Address: {address}\n",
        "cart.delivery_phone": "📞 Phone: {phone}\n",
        "cart.delivery_note": "📝 Note: {note}\n",
        "cart.use_info_question": "\n\nWould you like to use this information or update it?",
        "cart.no_saved_info": "❌ No saved delivery information found. Please enter manually.",

        # === Order/Delivery Flow ===
        "order.delivery.address_prompt": "📍 Please enter your delivery address:",
        "order.delivery.address_invalid": "❌ Please provide a valid delivery address (at least 5 characters).",
        "order.delivery.phone_prompt": "📞 Please enter your phone number (with country code):",
        "order.delivery.phone_invalid": "❌ Please provide a valid phone number (at least 8 digits).",
        "order.delivery.note_prompt": "📝 Any special delivery instructions? (Optional)\n\nYou can skip this by clicking the button below.",
        "order.delivery.info_save_error": "❌ Error saving delivery information. Please try again.",

        # Location Method Choice
        "order.delivery.location_method_prompt": "📍 How would you like to share your delivery location?\n\nChoose one of the options below:",
        "btn.location_method.gps": "📡 Send GPS via Telegram",
        "btn.location_method.live_gps": "📍 Share Live Location",
        "btn.location_method.google_link": "🗺 Share a Google Maps link",
        "btn.location_method.type_address": "✍️ Type an address",
        "order.delivery.gps_prompt": "📍 Tap the button below to share your location:",
        "order.delivery.gps_hint": "📍 Please use the button below to share your GPS location, or tap 'Back' to choose a different method.",
        "order.delivery.live_gps_prompt": "📍 To share your live location:\n\n1. Tap the attachment icon 📎 below\n2. Select 'Location'\n3. Tap 'Share My Live Location'\n4. Choose a duration\n\nThe driver will be able to see your location in real time!",
        "order.delivery.live_gps_saved": "✅ Live location received! The driver will be able to track your location.",
        "order.delivery.live_gps_hint": "📍 Please share your live location via the attachment menu (📎 → Location → Share Live Location).",
        "order.delivery.google_link_prompt": "🗺 Paste a Google Maps link with your location.\n\nOpen Google Maps, find the location, tap 'Share' and copy the link here.",
        "order.delivery.google_link_invalid": "❌ Could not recognize the Google Maps link. Make sure it starts with google.com/maps or goo.gl/maps.",
        "order.delivery.address_confirm_prompt": "📍 Your address:\n<b>{address}</b>\n\n🔗 <a href=\"{maps_link}\">View on map</a>\n\nIs this correct?",
        "btn.address_confirm_yes": "✅ Yes, that's correct",
        "btn.address_confirm_retry": "✏️ No, re-enter address",

        # GPS Location (Card 2)
        "order.delivery.location_prompt": "📍 Would you like to share your GPS location for more accurate delivery?\n\nTap the button below or skip this step.",
        "order.delivery.location_saved": "✅ Location saved!",
        "btn.share_location": "📍 Share Location",
        "btn.skip_location": "⏭ Skip",

        # Delivery Type (Card 3)
        "order.delivery.type_prompt": "🚚 Choose delivery type:",
        "btn.delivery.door": "🚪 Deliver to Door",
        "btn.delivery.dead_drop": "📦 Leave at Location",
        "btn.delivery.pickup": "🏪 Self Pickup",
        "order.delivery.drop_instructions_prompt": "📝 Describe where to leave your order (e.g., 'with security guard at lobby', 'under the mat at room 405'):",
        "order.delivery.drop_gps_prompt": "📍 Share the GPS location of the drop point by pressing the button below:",
        "btn.share_drop_location": "📍 Share Location",
        "order.delivery.drop_gps_saved": "✅ GPS location saved!",
        "order.delivery.drop_media_prompt": "📸 Send photos or videos of the drop location (you can send multiple). Press 'Done' when finished:",
        "order.delivery.drop_media_saved": "✅ {count} file(s) saved. Send more or press 'Done'.",
        "btn.drop_media_done": "✅ Done",
        "btn.skip_drop_media": "⏭ Skip",
        "order.delivery.drop_photo_prompt": "📸 Want to send a photo of the drop location? (optional)",
        "order.delivery.drop_photo_saved": "✅ Drop location photo saved!",
        "btn.skip_drop_photo": "⏭ Skip Photo",

        # PromptPay (Card 1)
        "order.payment_method.promptpay": "💳 PromptPay QR",
        "order.payment.promptpay.title": "💳 <b>PromptPay Payment</b>",
        "order.payment.promptpay.scan": "📱 Scan QR code to pay:",
        "order.payment.promptpay.upload_receipt": "📸 After payment, please upload your receipt/screenshot:",
        "order.payment.promptpay.receipt_received": "✅ Receipt received! Waiting for admin verification.",
        "order.payment.promptpay.receipt_invalid": "❌ Please send a photo of your payment receipt.",
        "order.payment.promptpay.slip_verified": "✅ Payment verified automatically! Your order is confirmed.",
        "admin.order.verify_payment": "✅ Verify Payment",
        "admin.order.payment_verified": "✅ Payment Verified",

        # Delivery Chat (Card 13)
        "order.delivery.chat_unavailable": "❌ Chat with driver unavailable. Rider group not configured.",
        "order.delivery.chat_started": "💬 You can message your driver. Send text, photo, or location.\n\nSend /endchat to end the chat.",
        "order.delivery.live_location_shared": "📍 Driver is sharing live location! You can track your delivery.",
        "order.delivery.chat_no_active_delivery": "❌ You have no active deliveries to chat about.",
        "order.delivery.chat_ended": "✅ Chat with driver ended.",
        "order.delivery.chat_message_sent": "✅ Message sent to driver.",
        "order.delivery.driver_no_active_order": "⚠️ No active order to relay this message.",
        "btn.chat_with_driver": "💬 Chat with Driver",

        # GPS tracking & chat session (Card 15)
        "delivery.gps.prompt": "📍 Your order {order_code} is on the way!\n\nHelp your driver find you faster — share your location:",
        "delivery.gps.btn_static": "📍 Send Location",
        "delivery.gps.btn_live": "📡 Live Location",
        "delivery.gps.btn_skip": "⏭ Skip",
        "delivery.gps.static_sent": "✅ Your location has been sent to the driver.",
        "delivery.gps.live_started": "📡 Live location enabled! Your driver can track you in real-time.",
        "delivery.gps.skipped": "⏭ Location skipped. Driver will use the address from your order.",
        "delivery.chat.session_closed": "⏹ This chat session has ended. Contact support for help.",
        "delivery.chat.post_delivery_open": "✅ Delivered! Chat stays open for {minutes} more minutes.",
        "delivery.chat.post_delivery_closed": "⏹ Post-delivery chat window has closed.",
        "btn.end_chat": "❌ End Chat",

        # === Bonus/Referral Application ===
        "order.bonus.available": "💰 <b>You have ${bonus_balance} in referral bonuses!</b>\n\n",
        "order.bonus.apply_question": "Would you like to apply referral bonus to this order?",
        "order.bonus.amount_positive_error": "❌ Please enter a positive amount.",
        "order.bonus.amount_too_high": "❌ Amount too high. Maximum applicable: ${max_applicable}\nPlease enter a valid amount:",
        "order.bonus.invalid_amount": "❌ Invalid amount. Please enter a number (e.g., 5.50):",
        "order.bonus.insufficient": "❌ Insufficient bonus balance. Please try again.",
        "order.bonus.enter_amount": "Enter the bonus amount you want to apply (maximum ${max_applicable}):\n\nOr use all available bonuses by clicking the button below.",

        # === Payment Instructions ===
        "order.payment.system_unavailable": "❌ <b>Payment System Temporarily Unavailable</b>\n\nNo Bitcoin addresses available. Please contact support.",
        "order.payment.customer_not_found": "❌ Customer info not found. Please try again.",
        "order.payment.creation_error": "❌ Error creating orders. Please try again or contact support.",

        # === Order Summary/Total ===
        "order.summary.title": "📦 <b>Order Summary</b>\n\n",
        "order.summary.cart_total": "Cart Total: ${cart_total}",
        "order.summary.bonus_applied": "Bonus Applied: -${bonus_applied}",
        "order.summary.final_amount": "Final Amount: ${final_amount}",

        # === Inventory/Reservation ===
        "order.inventory.unable_to_reserve": "❌ <b>Unable to Reserve Items</b>\n\nThe following items are not available in the requested quantities:\n\n{unavailable_items}\n\nPlease adjust your cart and try again.",

        # === My Orders View ===
        "myorders.title": "📦 <b>My Orders</b>\n\n",
        "myorders.total": "Total Orders: {count}",
        "myorders.active": "⏳ Active Orders: {count}",
        "myorders.delivered": "✅ Delivered: {count}",
        "myorders.select_category": "Select a category to view orders:",
        "myorders.active_orders": "⏳ Active Orders",
        "myorders.delivered_orders": "✅ Delivered Orders",
        "myorders.all_orders": "📋 All Orders",
        "myorders.no_orders_yet": "You haven't placed any orders yet.\n\nBrowse the shop to start shopping!",
        "myorders.browse_shop": "🛍️ Go to Shop",
        "myorders.back": "◀️ Back",
        "myorders.all_title": "📋 All Orders",
        "myorders.active_title": "⏳ Active Orders",
        "myorders.delivered_title": "✅ Delivered Orders",
        "myorders.invalid_filter": "Invalid filter",
        "myorders.not_found": "Orders not found.",
        "myorders.back_to_menu": "◀️ Back to Orders Menu",
        "myorders.select_details": "Select an order to view details:",
        "myorders.order_not_found": "Order not found",

        # === Order Details Display ===
        "myorders.detail.title": "📦 <b>Order Details #{order_code}</b>\n\n",
        "myorders.detail.status": "📊 <b>Status:</b> {status}\n",
        "myorders.detail.subtotal": "💵 <b>Subtotal:</b> ${subtotal}\n",
        "myorders.detail.bonus_applied": "🎁 <b>Bonus Applied:</b> ${bonus}\n",
        "myorders.detail.final_price": "💰 <b>Final Price:</b> ${total}\n",
        "myorders.detail.total_price": "💰 <b>Total Price:</b> ${total}\n",
        "myorders.detail.payment_method": "💳 <b>Payment Method:</b> {method}\n",
        "myorders.detail.ordered": "📅 <b>Ordered:</b> {date}\n",
        "myorders.detail.delivery_time": "🚚 <b>Scheduled Delivery:</b> {time}\n",
        "myorders.detail.completed": "✅ <b>Completed:</b> {date}\n",
        "myorders.detail.items": "\n📦 <b>Items:</b>\n{items}\n",
        "myorders.detail.delivery_info": "\n📍 <b>Delivery Information:</b>\n{address}\n{phone}\n{note}",

        # === Help System ===
        "help.prompt": "📧 <b>Need help?</b>\n\n",
        "help.describe_issue": "Please describe your issue or question, and it will be sent directly to the administrator.\n\nType your message below:",
        "help.admin_not_configured": "❌ Sorry, admin contact is not configured. Please try again later.",
        "help.admin_notification_title": "📧 <b>New Help Request</b>\n\n",
        "help.admin_notification_from": "<b>From:</b> @{username} (ID: {user_id})\n",
        "help.admin_notification_message": "<b>Message:</b>\n{message}",
        "help.sent_success": "✅ {auto_message}",
        "help.sent_error": "❌ Failed to send message to admin: {error}\n\nPlease try again later.",
        "help.cancelled": "Help request cancelled.",

        # === Admin Order Notifications ===
        "admin.order.action_required_title": "⏳ <b>Action Required:</b>",
        "admin.order.address_label": "Address: {address}",
        "admin.order.amount_to_collect_label": "<b>Amount to Collect: ${amount} {currency}</b>",
        "admin.order.amount_to_receive_label": "<b>Amount to Receive: ${amount} {currency}</b>",
        "admin.order.awaiting_payment_status": "⏳ Awaiting payment confirmation...",
        "admin.order.bitcoin_address_label": "Bitcoin Address: <code>{address}</code>",
        "admin.order.bonus_applied_label": "Bonus Applied: <b>-${amount}</b>",
        "admin.order.customer_label": "Customer: {username} (ID: {id})",
        "admin.order.delivery_info_title": "<b>Delivery Information:</b>",
        "admin.order.items_title": "<b>Items:</b>",
        "admin.order.new_bitcoin_order": "🔔 <b>New BITCOIN Order Received</b>",
        "admin.order.new_cash_order": "🔔 <b>New CASH Order Received</b> 💵",
        "admin.order.note_label": "Note: {note}",
        "admin.order.order_label": "Order: <b>{code}</b>",
        "admin.order.payment_cash": "Cash on Delivery",
        "admin.order.payment_method_label": "Payment Method: <b>{method}</b>",
        "admin.order.phone_label": "Phone: {phone}",
        "admin.order.subtotal_label": "Subtotal: <b>${amount} {currency}</b>",
        "admin.order.use_cli_confirm": "Use CLI to confirm order and set delivery time:\n<code>python bot_cli.py order --order-code {code} --status-confirmed --delivery-time \"YYYY-MM-DD HH:MM\"</code>",
        "btn.admin.back_to_panel": "🔙 Back to Admin Panel",
        "btn.admin.create_refcode": "➕ Create Reference Code",
        "btn.admin.list_refcodes": "📋 List All Codes",
        "btn.back_to_orders": "◀️ Back to Orders",
        "btn.create_reference_code": "➕ Create Reference Code",
        "btn.my_reference_codes": "🔑 My Reference Codes",
        "btn.need_help": "❓ Need Help?",
        "cart.item.price_format": "  Price: {price} {currency} × {quantity}",
        "cart.item.subtotal_format": "  Subtotal: {subtotal} {currency}",
        "cart.item.modifiers": "  Modifiers: {modifiers}",
        "cart.total_format": "<b>Total: {total} {currency}</b>",
        "cart.add_cancelled": "Adding cancelled",
        "modifier.select_title": "Choose {label}:",
        "modifier.selected": "Selected: {choice}",
        "modifier.required": "(required)",
        "modifier.optional": "(optional)",
        "modifier.done": "Done",
        "modifier.price_extra": "+{price}",
        "modifier.cancelled": "Modifier selection cancelled.",
        "help.pending_order.contact_support": "Use the /help command to contact support.",
        "help.pending_order.issues_title": "<b>Having issues?</b>",
        "help.pending_order.status": "Your order is currently pending payment.",
        "help.pending_order.step1": "1. Send the exact amount to the Bitcoin address shown",
        "help.pending_order.step2": "2. Wait for blockchain confirmation (usually 10-60 minutes)",
        "help.pending_order.step3": "3. Admin will confirm your payment and schedule a delivery time",
        "help.pending_order.step4": "4. Your goods will be delivered by courier.",
        "help.pending_order.title": "❓ <b>Need Help with Your Order?</b>",
        "help.pending_order.what_to_do_title": "<b>What to do:</b>",
        "myorders.detail.bitcoin_address_label": "Bitcoin Address:",
        "myorders.detail.bitcoin_admin_confirm": "After payment, our admin will confirm your order.",
        "myorders.detail.bitcoin_send_instruction": "⚠️ Please send <b>{amount} {currency}</b> worth of Bitcoin to this address.",
        "myorders.detail.cash_awaiting_confirm": "Your order is awaiting admin confirmation.",
        "myorders.detail.cash_payment_courier": "Payment will be made to the courier upon delivery.",
        "myorders.detail.cash_title": "💵 Cash on Delivery",
        "myorders.detail.cash_will_notify": "You will be notified when your order is confirmed and delivery time is set.",
        "myorders.detail.confirmed_title": "✅ <b>Order Confirmed!</b>",
        "myorders.detail.delivered_thanks_message": "Thank you for your purchase! We hope to see you again! 🙏",
        "myorders.detail.delivered_title": "📦 <b>Order Delivered!</b>",
        "myorders.detail.payment_info_title": "<b>Payment Information:</b>",
        "myorders.detail.preparing_message": "Your order is being prepared for delivery.",
        "myorders.detail.scheduled_delivery_label": "Scheduled delivery: <b>{time}</b>",
        "myorders.order_summary_format": "{status_emoji} {code} - {items_count} items - {total} {currency}",
        "order.bonus.available_label": "Available bonus: <b>${amount}</b>",
        "order.bonus.choose_amount_hint": "You can choose how much to use (up to ${max_amount})",
        "order.bonus.enter_amount_title": "💵 <b>Enter the bonus amount to apply</b>",
        "order.bonus.max_applicable_label": "Maximum applicable: <b>${amount}</b>",
        "order.bonus.order_total_label": "Order total: <b>${amount} {currency}</b>",
        "order.info.view_status_hint": "💡 You can view your order status anytime using the /orders command.",
        "order.payment.bitcoin.address_title": "<b>Bitcoin Payment Address:</b>",
        "order.payment.bitcoin.admin_confirm": "• After payment, our admin will confirm your order",
        "order.payment.bitcoin.delivery_title": "<b>Delivery:</b>",
        "order.payment.bitcoin.important_title": "⚠️ <b>IMPORTANT:</b>",
        "order.payment.bitcoin.items_title": "<b>Items:</b>",
        "order.payment.bitcoin.need_help": "Need help? Use /help to contact support.",
        "order.payment.bitcoin.one_time_address": "• This address is for ONE-TIME use only",
        "order.payment.bitcoin.order_code": "Order: <b>{code}</b>",
        "order.payment.bitcoin.send_exact": "• Send the EXACT amount shown above",
        "order.payment.bitcoin.title": "💳 <b>Bitcoin Payment Instructions</b>",
        "order.payment.bitcoin.total_amount": "Total Amount: <b>{amount} {currency}</b>",

        # Crypto payment (Card 18) — generic strings for all coins
        "crypto.payment.title": "💳 <b>{coin_name} Payment</b>",
        "crypto.payment.order_code": "Order: <b>{code}</b>",
        "crypto.payment.total_fiat": "Total: <b>{amount} {currency}</b>",
        "crypto.payment.rate": "Rate: 1 {coin} = {rate} {currency}",
        "crypto.payment.amount_due": "Amount due: <b>{crypto_amount} {coin}</b>",
        "crypto.payment.address": "<b>Send to this address:</b>\n<code>{address}</code>",
        "crypto.payment.send_exact": "• Send EXACTLY this amount",
        "crypto.payment.one_time": "• This address is for ONE-TIME use",
        "crypto.payment.auto_confirm": "• Your order will be automatically confirmed once the payment is detected on-chain.",
        "crypto.payment.waiting": "⏳ Waiting for payment...\nThis address expires in {timeout} minutes.",
        "crypto.payment.no_address": "❌ No {coin} addresses available. Please contact support or choose another payment method.",
        "crypto.payment_detected": (
            "✅ <b>Payment detected!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "⏳ Waiting for confirmations..."
        ),
        "crypto.payment_confirmed": (
            "✅ <b>Payment confirmed!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "Your order is now being processed."
        ),
        "crypto.payment_expired": "⏰ Payment window for your {coin} order ({order_code}) has expired. Please place a new order.",

        "order.payment.cash.admin_contact": "Admin will contact you shortly.",
        "order.payment.cash.after_confirm": "After confirmation, you will be notified of the delivery time.",
        "order.payment.cash.created": "Your order {code} has been created and is awaiting admin confirmation.",
        "order.payment.cash.important": "⏳ <b>Important:</b> The order is reserved for a limited time.",
        "order.payment.cash.items_title": "Items:",
        "order.payment.cash.payment_to_courier": "Payment will be made to the courier upon delivery.",
        "order.payment.cash.title": "💵 <b>Cash on Delivery</b>",
        "order.payment.cash.total": "Total: {amount}",
        "order.payment.error_general": "❌ Error creating order. Please try again or contact support.",
        "order.summary.total_label": "<b>Total: {amount} {currency}</b>",
        "order.payment.bonus_applied_label": "Bonus Applied: <b>-{amount} {currency}</b>",
        "order.payment.cash.amount_with_bonus": "<b>Amount to Pay on Delivery: {amount} {currency}</b>",
        "order.payment.cash.total_label": "<b>Total to Pay on Delivery: {amount} {currency}</b>",
        "order.payment.final_amount_label": "<b>Final Amount to Pay: {amount} {currency}</b>",
        "order.payment.order_label": "📋 <b>Order: {code}</b>",
        "order.payment.subtotal_label": "Subtotal: <b>{amount} {currency}</b>",
        "order.payment.total_amount_label": "<b>Total Amount: {amount} {currency}</b>",

        # === Card 9: Kitchen & Delivery Workflow ===
        "admin.menu.orders": "📋 Orders",
        "admin.orders.list_title": "📋 <b>Orders</b>",
        "admin.orders.empty": "No orders found",
        "admin.orders.filter_status": "Filter by status",
        "admin.orders.filter_all": "📋 All Orders",
        "admin.orders.filter_active": "🔄 Active",
        "admin.orders.detail": (
            "📋 <b>Order #{order_id}</b> ({order_code})\n"
            "👤 Buyer: {buyer_id}\n"
            "💰 Total: {total}\n"
            "📦 Status: {status}\n"
            "📅 Created: {created_at}\n"
            "📍 Address: {address}\n"
            "📞 Phone: {phone}"
        ),
        "admin.orders.status_changed": "Order #{order_id} status changed to <b>{new_status}</b>",
        "admin.orders.invalid_transition": "Cannot change status from {current} to {new}",
        "kitchen.order_received": (
            "🍳 <b>New Order #{order_id}</b> ({order_code})\n\n"
            "{items}\n\n"
            "💰 Total: {total}\n"
            "📍 Address: {address}\n"
            "📞 Phone: {phone}"
        ),
        "rider.order_ready": (
            "🚗 <b>Order Ready #{order_id}</b> ({order_code})\n\n"
            "💰 Total: {total}\n"
            "📍 Address: {address}\n"
            "📞 Phone: {phone}"
        ),
        "order.status.preparing": "🍳 Your order #{order_code} is being prepared",
        "order.status.ready": "✅ Your order #{order_code} is ready for pickup",
        "order.status.out_for_delivery": "🚗 Your order #{order_code} is on the way",
        "order.status.delivered_notify": "📦 Your order #{order_code} has been delivered",
        "kitchen.btn.start_preparing": "🍳 Start Preparing",
        "kitchen.btn.mark_ready": "✅ Mark Ready",
        "rider.btn.picked_up": "📦 Picked Up",
        "rider.btn.delivered": "✅ Mark Delivered",

        # Delivery Photo Proof (Card 4)
        "delivery.photo.required": "Photo required for dead drop delivery",
        "delivery.photo.upload_prompt": "Please upload delivery photo",
        "delivery.photo.received": "Delivery photo saved",
        "delivery.photo.sent_to_customer": "Delivery photo sent to customer",
        "delivery.photo.customer_notification": "Your order {order_code} has been delivered! Here is the delivery photo.",

        # === New Feature Strings ===

        # === Restaurant Feature Strings ===
        "admin.goods.add.allergen.dairy": "Dairy",
        "admin.goods.add.allergen.eggs": "Eggs",
        "admin.goods.add.allergen.fish": "Fish",
        "admin.goods.add.allergen.gluten": "Gluten",
        "admin.goods.add.allergen.nuts": "Nuts",
        "admin.goods.add.allergen.sesame": "Sesame",
        "admin.goods.add.allergen.shellfish": "Shellfish",
        "admin.goods.add.allergen.soy": "Soy",
        "admin.goods.add.allergens.done": "✅ Done",
        "admin.goods.add.allergens.skip": "⏭ No Allergens",
        "admin.goods.add.availability.invalid": "❌ Invalid format. Use HH:MM-HH:MM (e.g. 06:00-22:00)",
        "admin.goods.add.availability.skip": "⏭ All Day",
        "admin.goods.add.daily_limit.invalid": "❌ Enter a positive number.",
        "admin.goods.add.daily_limit.skip": "⏭ Unlimited",
        "admin.goods.add.modifier.add_another_group": "➕ Another Group",
        "admin.goods.add.modifier.add_group": "➕ Add Modifier Group",
        "admin.goods.add.modifier.add_option": "➕ Add Option",
        "admin.goods.add.modifier.all_done": "✅ Finish",
        "admin.goods.add.modifier.finish": "✅ Finish (No Modifiers)",
        "admin.goods.add.modifier.group_added": "✅ Group added! Add another group or finish.",
        "admin.goods.add.modifier.group_name": "Enter modifier group name (e.g. Spice Level):",
        "admin.goods.add.modifier.group_type": "Select type for this group:",
        "admin.goods.add.modifier.option_added": "✅ Option added! Add another or press Done.",
        "admin.goods.add.modifier.option_label": "Enter option label (e.g. Mild, Extra Cheese):",
        "admin.goods.add.modifier.option_price": "Enter price adjustment for this option (0 for free):",
        "admin.goods.add.modifier.options_done": "✅ Done with Options",
        "admin.goods.add.modifier.paste_json": "📋 Paste JSON",
        "admin.goods.add.modifier.required_no": "⭕ Optional",
        "admin.goods.add.modifier.required_yes": "✅ Required",
        "admin.goods.add.modifier.type_multi": "Multi Choice",
        "admin.goods.add.modifier.type_single": "Single Choice",
        "admin.goods.add.photo.done": "✅ Done",
        "admin.goods.add.photo.received": "✅ Media received! Send more or press Done.",
        "admin.goods.add.photo.send_more": "Send more photos/videos or press Done:",
        "admin.goods.add.photo.skip": "⏭ Skip Photos",
        "admin.goods.add.prep_time.invalid": "❌ Enter a positive number.",
        "admin.goods.add.prep_time.skip": "⏭ Skip",
        "admin.goods.add.prompt.allergens": "⚠️ Select allergens (tap to toggle, then Done):",
        "admin.goods.add.prompt.availability": "🕐 Enter availability hours (e.g. 06:00-22:00) or press Skip for all-day:",
        "admin.goods.add.prompt.daily_limit": "📊 Enter daily limit (max units per day) or press Skip for unlimited:",
        "admin.goods.add.prompt.modifier_group": "Add a modifier group (e.g. Spice Level, Extras)?",
        "admin.goods.add.prompt.photo": "📸 Send a photo or video of this item (or press Skip):",
        "admin.goods.add.prompt.prep_time": "⏱ Enter prep time in minutes (or press Skip):",
        "admin.goods.toggle.active_off": "🚫 {item}: Deactivated",
        "admin.goods.toggle.active_on": "✅ {item}: Activated",
        "admin.goods.toggle.sold_out_off": "✅ {item}: Back in stock",
        "admin.goods.toggle.sold_out_on": "❌ {item}: Marked SOLD OUT",
        "btn.view_gallery": "📸 Gallery ({count})",
        "kitchen.order.modifier_detail": "    ↳ {modifiers}",
        "kitchen.order.prep_time": "⏱ Est. prep: {minutes} min",
        "kitchen.order.ready_by": "🕐 Ready by: {time}",
        "order.estimated_ready": "⏱ Estimated ready in ~{minutes} min",
        "shop.item.allergens": "⚠️ Allergens: {allergens}",
        "shop.item.availability": "🕐 Available: {from_time} - {until_time}",
        "shop.item.calories": "🔥 {calories} cal",
        "shop.item.daily_remaining": "📊 Today: {remaining}/{limit} left",
        "shop.item.no_gallery": "No gallery for this item.",
        "shop.item.type_product": "📦 Type: Packaged product",
        "shop.item.type_prepared": "🍳 Type: Made to order",
        "shop.item.prep_time": "⏱ Prep: ~{minutes} min",
        "shop.item.sold_out": "❌ Sold out today",
        "admin.accounting.export_payments": "📥 Payment Reconciliation",
        "admin.accounting.export_products": "📥 Revenue by Product",
        "admin.accounting.export_sales": "📥 Export Sales CSV",
        "admin.accounting.export_sent": "✅ Report exported.",
        "admin.accounting.no_data": "No data for this period.",
        "admin.accounting.summary": "📊 <b>Revenue Summary ({period})</b>\n\n💰 Revenue: {total} {currency}\n📦 Orders: {orders}\n📈 Avg: {avg} {currency}\n\n<b>By Payment:</b>\n{payments}\n\n<b>Top Products:</b>\n{products}",
        "admin.accounting.summary_all": "📊 All Time",
        "admin.accounting.summary_month": "📊 This Month",
        "admin.accounting.summary_today": "📊 Today",
        "admin.accounting.summary_week": "📊 This Week",
        "admin.accounting.title": "📊 <b>Accounting & Reports</b>",
        "admin.coupon.create": "➕ Create Coupon",
        "admin.coupon.created": "✅ Coupon <b>{code}</b> created!\nType: {type}\nValue: {value}\nMin order: {min_order}\nMax uses: {max_uses}\nExpires: {expiry}",
        "admin.coupon.detail": "🎟 <b>{code}</b>\nType: {type}\nValue: {value}\nMin Order: {min_order}\nMax Uses: {max_uses}\nUsed: {used}\nStatus: {status}\nExpires: {expiry}",
        "admin.coupon.empty": "No coupons found.",
        "admin.coupon.enter_code": "Enter coupon code (or type <b>auto</b> for random):",
        "admin.coupon.enter_expiry": "Enter expiry in days (or <b>skip</b> for no expiry):",
        "admin.coupon.enter_max_uses": "Enter max total uses (or <b>skip</b> for unlimited):",
        "admin.coupon.enter_min_order": "Enter minimum order amount (or <b>skip</b>):",
        "admin.coupon.enter_value": "Enter discount value ({type}):",
        "admin.coupon.invalid_value": "❌ Invalid value. Enter a number.",
        "admin.coupon.list_active": "📋 Active Coupons",
        "admin.coupon.list_all": "📋 All Coupons",
        "admin.coupon.select_type": "Select discount type:",
        "admin.coupon.title": "🎟 <b>Coupon Management</b>",
        "admin.coupon.toggle_activate": "✅ Activate",
        "admin.coupon.toggle_deactivate": "❌ Deactivate",
        "admin.coupon.toggled": "✅ Coupon {code} is now {status}.",
        "admin.coupon.type_fixed": "💰 Fixed Amount",
        "admin.coupon.type_percent": "📊 Percentage (%)",
        "admin.menu.accounting": "📊 Accounting",
        "admin.menu.coupons": "🎟 Coupons",
        "admin.menu.segment_broadcast": "📣 Targeted Broadcast",
        "admin.menu.stores": "🏪 Stores",
        "admin.menu.tickets": "🎫 Tickets",
        "admin.menu.ai_assistant": "🤖 AI Assistant",
        "admin.segment.all_users": "👥 All Users",
        "admin.segment.count": "📊 Segment: <b>{segment}</b>\nUsers: <b>{count}</b>\n\nType your broadcast message:",
        "admin.segment.empty": "No users in this segment.",
        "admin.segment.high_spenders": "💰 High Spenders",
        "admin.segment.inactive": "😴 Inactive (30+ days)",
        "admin.segment.new_users": "🆕 New Users (7d)",
        "admin.segment.recent_buyers": "🛒 Recent Buyers (7d)",
        "admin.segment.sent": "✅ Sent to {sent}/{total} ({segment}).",
        "admin.segment.title": "📣 <b>Targeted Broadcast</b>\n\nSelect segment:",
        "admin.store.add": "➕ Add Store",
        "admin.store.address_prompt": "Enter store address (or <b>skip</b>):",
        "admin.store.btn_default": "⭐ Set as Default",
        "admin.store.created": "✅ Store <b>{name}</b> created!",
        "admin.store.detail": "🏪 <b>{name}</b>\nStatus: {status}\nDefault: {default}\nAddress: {address}\nLocation: {location}\nPhone: {phone}",
        "admin.store.empty": "No stores configured.",
        "admin.store.location_prompt": "Send GPS location (or type <b>skip</b>):",
        "admin.store.name_exists": "Store with this name already exists.",
        "admin.store.name_prompt": "Enter store name:",
        "admin.store.set_default": "✅ {name} set as default store.",
        "admin.store.title": "🏪 <b>Store Management</b>",
        "admin.store.toggle_activate": "✅ Activate",
        "admin.store.toggle_deactivate": "❌ Deactivate",
        "admin.store.toggled": "✅ Store {name} is now {status}.",
        "admin.ticket.detail": "🎫 <b>Ticket #{code}</b>\nUser: {user_id}\nStatus: {status}\nPriority: {priority}\nSubject: {subject}\nCreated: {date}",
        "admin.ticket.empty": "No open tickets.",
        "admin.ticket.list": "Open/In Progress Tickets:",
        "admin.ticket.reply_prompt": "Reply to ticket #{code}:",
        "admin.ticket.resolved": "✅ Ticket #{code} resolved.",
        "admin.ticket.title": "🎫 <b>Support Tickets</b>",
        "btn.admin.reply_ticket": "💬 Reply",
        "btn.admin.resolve_ticket": "✅ Resolve",
        "btn.apply_coupon": "🎟 Apply Coupon",
        "btn.close_ticket": "✖ Close Ticket",
        "btn.create_ticket": "➕ New Ticket",
        "btn.create_ticket_for_order": "🎫 Support Ticket",
        "btn.invoice": "🧾 Receipt",
        "btn.my_tickets": "🎫 Support",
        "btn.reorder": "🔄 Reorder",
        "btn.reply_ticket": "💬 Reply",
        "btn.review_order": "⭐ Leave Review",
        "btn.search": "🔍 Search",
        "btn.skip_coupon": "⏭ Skip Coupon",
        "coupon.already_used": "❌ You already used this coupon.",
        "coupon.applied": "✅ Coupon applied! Discount: -{discount} {currency}",
        "coupon.enter_code": "🎟 Enter coupon code (or press Skip):",
        "coupon.expired": "❌ This coupon has expired.",
        "coupon.invalid": "❌ Invalid or expired coupon code.",
        "coupon.max_uses_reached": "❌ Coupon usage limit reached.",
        "coupon.min_order_not_met": "❌ Min order of {min_order} required.",
        "coupon.not_yet_valid": "❌ This coupon is not yet valid.",
        "invoice.not_available": "Receipt not available.",
        "reorder.success": "✅ Added {added} item(s) to cart. {skipped} item(s) unavailable.",
        "review.already_reviewed": "You have already reviewed this order.",
        "review.comment_prompt": "You rated {rating}/5 ⭐\n\nAdd a comment? Type or press Skip:",
        "review.detail": "⭐{rating}/5 — {comment}",
        "review.item_rating": "⭐ <b>{item}</b>: {avg:.1f}/5 ({count} reviews)",
        "review.no_reviews": "No reviews yet.",
        "review.prompt": "⭐ <b>Rate your order #{order_code}</b>\n\nSelect your rating:",
        "review.rate_1": "⭐",
        "review.rate_2": "⭐⭐",
        "review.rate_3": "⭐⭐⭐",
        "review.rate_4": "⭐⭐⭐⭐",
        "review.rate_5": "⭐⭐⭐⭐⭐",
        "review.skip_comment": "⏭ Skip",
        "review.thanks": "✅ Thank you for your review! ({rating}/5 ⭐)",
        "search.no_results": "❌ No products found. Try different keywords.",
        "search.prompt": "🔍 Enter product name or keyword to search:",
        "search.result_count": "Found {count} product(s):\n",
        "search.results_title": "🔍 <b>Search results for:</b> {query}\n\n",
        "ticket.admin_replied": "💬 Admin replied to ticket #{code}:\n{text}",
        "ticket.closed": "✅ Ticket closed.",
        "ticket.created": "✅ Ticket <b>#{code}</b> created!",
        "ticket.message_format": "<b>{role}</b> ({date}):\n{text}\n",
        "ticket.message_prompt": "Describe your issue:",
        "ticket.no_tickets": "No support tickets.",
        "ticket.reply_prompt": "Type your reply:",
        "ticket.reply_sent": "✅ Reply sent.",
        "ticket.resolved_notification": "✅ Ticket #{code} resolved!",
        "ticket.status.closed": "⚫ Closed",
        "ticket.status.in_progress": "🔵 In Progress",
        "ticket.status.open": "🟢 Open",
        "ticket.status.resolved": "✅ Resolved",
        "ticket.subject_prompt": "Enter the subject:",
        "ticket.title": "🎫 <b>Support Tickets</b>",
        "ticket.view_title": "🎫 <b>Ticket #{code}</b>\nStatus: {status}\nSubject: {subject}\nCreated: {date}",

        # === Product Search ===
        "btn.search": "🔍 Search",
        "search.prompt": "🔍 Enter product name or keyword to search:",
        "search.results_title": "🔍 <b>Search results for:</b> {query}\n\n",
        "search.no_results": "❌ No products found. Try different keywords.",
        "search.result_count": "Found {count} product(s):\n",

        # === Reorder ===
        "btn.reorder": "🔄 Reorder",
        "reorder.success": "✅ Added {added} item(s) to cart. {skipped} item(s) unavailable.",

        # === Coupon / Promo Codes ===
        "admin.menu.coupons": "🎟 Coupons",
        "admin.coupon.title": "🎟 <b>Coupon Management</b>",
        "admin.coupon.create": "➕ Create Coupon",
        "admin.coupon.list_active": "📋 Active Coupons",
        "admin.coupon.list_all": "📋 All Coupons",
        "admin.coupon.enter_code": "Enter coupon code (or type <b>auto</b> for random):",
        "admin.coupon.select_type": "Select discount type:",
        "admin.coupon.type_percent": "📊 Percentage (%)",
        "admin.coupon.type_fixed": "💰 Fixed Amount",
        "admin.coupon.enter_value": "Enter discount value ({type}):",
        "admin.coupon.enter_min_order": "Enter minimum order amount (or <b>skip</b>):",
        "admin.coupon.enter_max_uses": "Enter max total uses (or <b>skip</b> for unlimited):",
        "admin.coupon.enter_expiry": "Enter expiry in days (or <b>skip</b> for no expiry):",
        "admin.coupon.created": "✅ Coupon <b>{code}</b> created!\nType: {type}\nDiscount: {value}\nMin order: {min_order}\nMax uses: {max_uses}\nExpires: {expiry}",
        "admin.coupon.invalid_value": "❌ Invalid value. Please enter a number.",
        "admin.coupon.empty": "No coupons found.",
        "admin.coupon.detail": "🎟 <b>{code}</b>\nType: {type}\nDiscount: {value}\nMin Order: {min_order}\nMax Uses: {max_uses}\nUsed: {used}\nStatus: {status}\nExpires: {expiry}",
        "admin.coupon.toggled": "✅ Coupon {code} is now {status}.",
        "admin.coupon.toggle_activate": "✅ Activate",
        "admin.coupon.toggle_deactivate": "❌ Deactivate",
        "coupon.invalid": "❌ Invalid or expired coupon code.",
        "coupon.min_order_not_met": "❌ Minimum order of {min_order} required for this coupon.",
        "coupon.already_used": "❌ You have already used this coupon.",
        "coupon.max_uses_reached": "❌ This coupon has reached its usage limit.",
        "coupon.expired": "❌ This coupon has expired.",
        "coupon.not_yet_valid": "❌ This coupon is not yet valid.",
        "coupon.applied": "✅ Coupon applied! Discount: -{discount} {currency}",
        "coupon.enter_code": "🎟 Enter coupon code (or press Skip):",
        "btn.skip_coupon": "⏭ Skip Coupon",
        "btn.apply_coupon": "🎟 Apply Coupon",

        # === Review / Rating System ===
        "btn.review_order": "⭐ Leave Review",
        "review.prompt": "⭐ <b>Rate your order #{order_code}</b>\n\nSelect your rating:",
        "review.rate_1": "⭐",
        "review.rate_2": "⭐⭐",
        "review.rate_3": "⭐⭐⭐",
        "review.rate_4": "⭐⭐⭐⭐",
        "review.rate_5": "⭐⭐⭐⭐⭐",
        "review.comment_prompt": "You rated {rating}/5 ⭐\n\nWould you like to add a comment? Type your comment or press Skip:",
        "review.skip_comment": "⏭ Skip",
        "review.thanks": "✅ Thank you for your review! ({rating}/5 ⭐)",
        "review.already_reviewed": "You have already reviewed this order.",
        "review.item_rating": "⭐ <b>{item}</b>: {avg:.1f}/5 ({count} reviews)",
        "review.no_reviews": "No reviews yet.",
        "review.detail": "⭐{rating}/5 — {comment}",

        # === Invoice / Receipt ===
        "btn.invoice": "🧾 Receipt",
        "invoice.not_available": "Receipt not available for this order.",

        # === Support Ticketing ===
        "btn.my_tickets": "🎫 Support",
        "btn.create_ticket": "➕ New Ticket",
        "btn.create_ticket_for_order": "🎫 Support Ticket",
        "ticket.title": "🎫 <b>Support Tickets</b>",
        "ticket.no_tickets": "You have no support tickets.",
        "ticket.subject_prompt": "Enter the subject of your support request:",
        "ticket.message_prompt": "Describe your issue:",
        "ticket.created": "✅ Ticket <b>#{code}</b> created! We'll get back to you soon.",
        "ticket.view_title": "🎫 <b>Ticket #{code}</b>\nStatus: {status}\nSubject: {subject}\nCreated: {date}",
        "ticket.reply_prompt": "Type your reply:",
        "ticket.reply_sent": "✅ Reply sent.",
        "ticket.closed": "✅ Ticket closed.",
        "ticket.message_format": "<b>{role}</b> ({date}):\n{text}\n",
        "btn.reply_ticket": "💬 Reply",
        "btn.close_ticket": "✖ Close Ticket",
        "ticket.status.open": "🟢 Open",
        "ticket.status.in_progress": "🔵 In Progress",
        "ticket.status.resolved": "✅ Resolved",
        "ticket.status.closed": "⚫ Closed",
        "ticket.admin_replied": "💬 Admin replied to ticket #{code}:\n{text}",
        "ticket.resolved_notification": "✅ Your ticket #{code} has been resolved!",

        # === Admin Tickets ===
        "admin.menu.tickets": "🎫 Tickets",
        "admin.menu.ai_assistant": "🤖 AI Assistant",
        "admin.ticket.title": "🎫 <b>Support Tickets</b>",
        "admin.ticket.list": "Open/In Progress Tickets:",
        "admin.ticket.empty": "No open tickets.",
        "admin.ticket.reply_prompt": "Type your reply to ticket #{code}:",
        "admin.ticket.resolved": "✅ Ticket #{code} marked as resolved.",
        "admin.ticket.detail": "🎫 <b>Ticket #{code}</b>\nUser: {user_id}\nStatus: {status}\nPriority: {priority}\nSubject: {subject}\nCreated: {date}",
        "btn.admin.resolve_ticket": "✅ Resolve",
        "btn.admin.reply_ticket": "💬 Reply",

        # === Accounting / Revenue Export ===
        "admin.menu.accounting": "📊 Accounting",
        "admin.accounting.title": "📊 <b>Accounting & Reports</b>",
        "admin.accounting.summary_today": "📊 Today",
        "admin.accounting.summary_week": "📊 This Week",
        "admin.accounting.summary_month": "📊 This Month",
        "admin.accounting.summary_all": "📊 All Time",
        "admin.accounting.export_sales": "📥 Export Sales CSV",
        "admin.accounting.export_products": "📥 Revenue by Product",
        "admin.accounting.export_payments": "📥 Payment Reconciliation",
        "admin.accounting.summary": "📊 <b>Revenue Summary ({period})</b>\n\n💰 Total Revenue: {total} {currency}\n📦 Orders: {orders}\n📈 Avg Order: {avg} {currency}\n\n<b>By Payment:</b>\n{payments}\n\n<b>Top Products:</b>\n{products}",
        "admin.accounting.export_sent": "✅ Report exported.",
        "admin.accounting.no_data": "No data for this period.",

        # === Customer Segmentation ===
        "admin.menu.segment_broadcast": "📣 Targeted Broadcast",
        "admin.segment.title": "📣 <b>Targeted Broadcast</b>\n\nSelect customer segment:",
        "admin.segment.all_users": "👥 All Users",
        "admin.segment.high_spenders": "💰 High Spenders",
        "admin.segment.recent_buyers": "🛒 Recent Buyers (7 days)",
        "admin.segment.inactive": "😴 Inactive (30+ days)",
        "admin.segment.new_users": "🆕 New Users (7 days)",
        "admin.segment.count": "📊 Segment: <b>{segment}</b>\nUsers: <b>{count}</b>\n\nType your broadcast message:",
        "admin.segment.empty": "No users in this segment.",
        "admin.segment.sent": "✅ Broadcast sent to {sent}/{total} users ({segment}).",

        # === Multi-Store / Multi-Location ===
        "admin.menu.stores": "🏪 Stores",
        "admin.store.title": "🏪 <b>Store Management</b>",
        "admin.store.add": "➕ Add Store",
        "admin.store.name_prompt": "Enter store name:",
        "admin.store.address_prompt": "Enter store address (or type <b>skip</b>):",
        "admin.store.location_prompt": "Send GPS location for the store (or type <b>skip</b>):",
        "admin.store.created": "✅ Store <b>{name}</b> created!",
        "admin.store.detail": "🏪 <b>{name}</b>\nStatus: {status}\nDefault: {default}\nAddress: {address}\nLocation: {location}\nPhone: {phone}",
        "admin.store.toggled": "✅ Store {name} is now {status}.",
        "admin.store.set_default": "✅ {name} set as default store.",
        "admin.store.toggle_activate": "✅ Activate",
        "admin.store.toggle_deactivate": "❌ Deactivate",
        "admin.store.btn_default": "⭐ Set as Default",
        "admin.store.empty": "No stores configured.",
        "admin.store.name_exists": "A store with this name already exists.",

        # === PDPA Privacy Policy ===
        "btn.privacy": "🔒 Privacy Policy",
        "privacy.notice": (
            "🔒 <b>Privacy Notice (PDPA)</b>\n\n"
            "We comply with Thailand's Personal Data Protection Act (PDPA).\n\n"
            "<b>Data we collect:</b>\n"
            "• Name / phone / delivery address\n"
            "• Order details & history\n"
            "• Telegram ID\n\n"
            "<b>Purposes:</b>\n"
            "• Order fulfillment & delivery (contractual necessity)\n"
            "• Fraud prevention & identity verification\n"
            "• Marketing — only with your separate consent\n\n"
            "<b>Retention:</b> Until you request deletion, or 2 years after your last order\n\n"
            "<b>Data sharing:</b> Restaurants, delivery riders, payment providers — only as needed for your order. "
            "We never sell your data.\n\n"
            "<b>Your PDPA rights:</b>\n"
            "• Access / correct / delete your data\n"
            "• Withdraw consent (for marketing)\n"
            "• Object to processing / request data portability\n"
            "• File a complaint with the PDPC\n\n"
            "<b>Data controller:</b> {company}\n"
            "Contact: {email}\n\n"
            "By continuing to use this bot, you acknowledge and accept this policy."
        ),
        "privacy.btn_full_policy": "📄 Read Full Policy",
        "privacy.btn_accept": "✅ Accept & Continue",
        "privacy.accepted": "✅ You have accepted the privacy policy.",
        "privacy.already_accepted": "✅ You have already accepted the privacy policy.",
        "privacy.no_url": "Full privacy policy page is not configured yet.",
    },

    "th": {
        # === Common Buttons ===
        "btn.shop": "🏪 ร้านค้า",
        "btn.rules": "📜 กฎระเบียบ",
        "btn.profile": "👤 โปรไฟล์",
        "btn.support": "🆘 ช่วยเหลือ",
        "btn.channel": "ℹ ช่องข่าว",
        "btn.admin_menu": "🎛 แผงควบคุม",
        "btn.back": "⬅️ กลับ",
        "btn.close": "✖ ปิด",
        "btn.yes": "✅ ใช่",
        "btn.no": "❌ ไม่",
        "btn.check_subscription": "🔄 ตรวจสอบการสมัครสมาชิก",
        "btn.admin.ban_user": "🚫 แบนผู้ใช้",
        "btn.admin.unban_user": "✅ ปลดแบนผู้ใช้",

        # === Admin Buttons (user management shortcuts) ===
        "btn.admin.promote": "⬆️ แต่งตั้งเป็นแอดมิน",
        "btn.admin.demote": "⬇️ ถอดถอนแอดมิน",
        "btn.admin.add_user_bonus": "🎁 เพิ่มโบนัสการแนะนำ",

        # === Titles / Generic Texts ===
        "menu.title": "⛩️ เมนูหลัก",
        "admin.goods.add.stock.error": "❌ เกิดข้อผิดพลาดในการเพิ่มสต็อกเริ่มต้น: {error}",
        "admin.goods.stock.add_success": "✅ เพิ่ม {quantity} หน่วยให้กับ \"{item}\"",
        "admin.goods.stock.add_units": "➕ เพิ่มจำนวน",
        "admin.goods.stock.current_status": "สถานะปัจจุบัน",
        "admin.goods.stock.error": "❌ เกิดข้อผิดพลาดในการจัดการสต็อก: {error}",
        "admin.goods.stock.insufficient": "❌ สต็อกไม่เพียงพอ มีเพียง {available} หน่วยเท่านั้น",
        "admin.goods.stock.invalid_quantity": "⚠️ จำนวนไม่ถูกต้อง กรุณากรอกจำนวนเต็ม",
        "admin.goods.stock.management_title": "จัดการสต็อก: {item}",
        "admin.goods.stock.negative_quantity": "⚠️ จำนวนต้องไม่ติดลบ",
        "admin.goods.stock.no_products": "❌ ยังไม่มีสินค้าในร้าน",
        "admin.goods.stock.prompt.add_units": "กรอกจำนวนหน่วยที่ต้องการเพิ่ม:",
        "admin.goods.stock.prompt.item_name": "กรอกชื่อสินค้าเพื่อจัดการสต็อก:",
        "admin.goods.stock.prompt.remove_units": "กรอกจำนวนหน่วยที่ต้องการลบ:",
        "admin.goods.stock.prompt.set_exact": "กรอกจำนวนสต็อกที่แน่นอน:",
        "admin.goods.stock.redirect_message": "ℹ️ การจัดการสต็อกพร้อมใช้งานแล้วผ่านเมนู \"จัดการสต็อก\"",
        "admin.goods.stock.remove_success": "✅ ลบ {quantity} หน่วยออกจาก \"{item}\"",
        "admin.goods.stock.remove_units": "➖ ลบจำนวน",
        "admin.goods.stock.select_action": "เลือกการดำเนินการ",
        "admin.goods.stock.set_exact": "⚖️ ตั้งค่าจำนวนที่แน่นอน",
        "admin.goods.stock.set_success": "✅ สต็อกของ \"{item}\" ถูกตั้งค่าเป็น {quantity} หน่วย",
        "admin.goods.stock.status_title": "📊 สถานะสต็อก:",
        "errors.invalid_item_name": "❌ ชื่อสินค้าไม่ถูกต้อง",
        "errors.invalid_language": "ภาษาไม่ถูกต้อง",
        "shop.error.brand_required": "กรุณาเลือกแบรนด์ก่อน",
        "shop.error.branch_unavailable": "สาขาไม่พร้อมให้บริการ",
        "profile.caption": "👤 <b>โปรไฟล์</b> — <a href='tg://user?id={id}'>{name}</a>",
        "rules.not_set": "❌ ยังไม่ได้เพิ่มกฎระเบียบ",
        "admin.users.cannot_ban_owner": "❌ ไม่สามารถแบนเจ้าของได้",
        "admin.users.ban.success": "✅ ผู้ใช้ {name} ถูกแบนเรียบร้อยแล้ว",
        "admin.users.ban.failed": "❌ ไม่สามารถแบนผู้ใช้ได้",
        "admin.users.ban.notify": "⛔ คุณถูกแบนโดยผู้ดูแลระบบ",
        "admin.users.unban.success": "✅ ผู้ใช้ {name} ถูกปลดแบนเรียบร้อยแล้ว",
        "admin.users.unban.failed": "❌ ไม่สามารถปลดแบนผู้ใช้ได้",
        "admin.users.unban.notify": "✅ คุณถูกปลดแบนโดยผู้ดูแลระบบ",

        # === Profile ===
        "btn.referral": "🎲 ระบบการแนะนำ",
        "btn.purchased": "🎁 สินค้าที่ซื้อแล้ว",
        "profile.referral_id": "👤 <b>การแนะนำ</b> — <code>{id}</code>",

        # === Subscription Flow ===
        "subscribe.prompt": "กรุณาสมัครสมาชิกช่องข่าวก่อน",

        # === Profile Info Lines ===
        "profile.id": "🆔 <b>ID</b> — <code>{id}</code>",
        "profile.bonus_balance": "💰 <b>โบนัสการแนะนำ:</b> ${bonus_balance}",
        "profile.purchased_count": "🎁 <b>สินค้าที่ซื้อแล้ว</b> — {count} ชิ้น",
        "profile.registration_date": "🕢 <b>วันที่ลงทะเบียน</b> — <code>{dt}</code>",

        # === Referral ===
        "referral.title": "💚 ระบบการแนะนำ",
        "referral.count": "จำนวนผู้ถูกแนะนำ: {count}",
        "referral.description": (
            "📔 ระบบการแนะนำช่วยให้คุณสามารถหารายได้โดยไม่ต้องลงทุน "
            "เพียงแค่แชร์ลิงก์แนะนำของคุณ แล้วคุณจะได้รับ {percent}% "
            "จากยอดเติมเงินของผู้ถูกแนะนำเข้าสู่ยอดเงินบอทของคุณ"
        ),
        "btn.view_referrals": "👥 ผู้ถูกแนะนำของฉัน",
        "btn.view_earnings": "💰 รายได้ของฉัน",

        "referrals.list.title": "👥 ผู้ถูกแนะนำของคุณ:",
        "referrals.list.empty": "คุณยังไม่มีผู้ถูกแนะนำที่ใช้งานอยู่",
        "referrals.item.format": "ID: {telegram_id} | รายได้: {total_earned} {currency}",

        "referral.earnings.title": "💰 รายได้จากผู้ถูกแนะนำ <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>):",
        "referral.earnings.empty": "ยังไม่มีรายได้จากผู้ถูกแนะนำ <code>{id}</code> (<a href='tg://user?id={id}'>{name}</a>)",
        "referral.earning.format": "{amount} {currency} | {date} | (จาก {original_amount} {currency})",
        "referral.item.info": ("💰 รายได้หมายเลข: <code>{id}</code>\n"
                               "👤 ผู้ถูกแนะนำ: <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>)\n"
                               "🔢 จำนวน: {amount} {currency}\n"
                               "🕘 วันที่: <code>{date}</code>\n"
                               "💵 จากยอดเติมเงิน {original_amount} {currency}"),

        "referral.admin_bonus.info": ("💰 รายได้หมายเลข: <code>{id}</code>\n"
                                      "🎁 <b>โบนัสจากผู้ดูแลระบบ</b>\n"
                                      "🔢 จำนวน: {amount} {currency}\n"
                                      "🕘 วันที่: <code>{date}</code>"),

        "all.earnings.title": "💰 รายได้จากการแนะนำทั้งหมดของคุณ:",
        "all.earnings.empty": "คุณยังไม่มีรายได้จากการแนะนำ",
        "all.earning.format.admin": "{amount} {currency} จาก Admin | {date}",

        "referrals.stats.template": (
            "📊 สถิติระบบการแนะนำ:\n\n"
            "👥 ผู้ถูกแนะนำที่ใช้งาน: {active_count}\n"
            "💰 รายได้ทั้งหมด: {total_earned} {currency}\n"
            "📈 ยอดเติมเงินรวมของผู้ถูกแนะนำ: {total_original} {currency}\n"
            "🔢 จำนวนครั้งที่ได้รับ: {earnings_count}"
        ),

        # === Admin: Main Menu ===
        "admin.menu.main": "⛩️ เมนูแอดมิน",
        "admin.menu.shop": "🛒 จัดการร้านค้า",
        "admin.menu.goods": "📦 จัดการสินค้า",
        "admin.menu.categories": "📂 จัดการหมวดหมู่",
        "admin.menu.users": "👥 จัดการผู้ใช้",
        "admin.menu.broadcast": "📝 ประกาศ",
        "admin.menu.rights": "สิทธิ์ไม่เพียงพอ",

        # === Admin: User Management ===
        "admin.users.prompt_enter_id": "👤 กรอก ID ผู้ใช้เพื่อดู / แก้ไขข้อมูล",
        "admin.users.invalid_id": "⚠️ กรุณากรอก ID ผู้ใช้ที่เป็นตัวเลขที่ถูกต้อง",
        "admin.users.profile_unavailable": "❌ ไม่พบโปรไฟล์ (ผู้ใช้นี้ไม่เคยมีอยู่)",
        "admin.users.not_found": "❌ ไม่พบผู้ใช้",
        "admin.users.cannot_change_owner": "ไม่สามารถเปลี่ยนบทบาทของเจ้าของได้",
        "admin.users.referrals": "👥 <b>ผู้ถูกแนะนำของผู้ใช้</b> — {count}",
        "admin.users.btn.view_referrals": "👥 ผู้ถูกแนะนำของผู้ใช้",
        "admin.users.btn.view_earnings": "💰 รายได้",
        "admin.users.role": "🎛 <b>บทบาท</b> — {role}",
        "admin.users.set_admin.success": "✅ กำหนดบทบาทให้ {name} แล้ว",
        "admin.users.set_admin.notify": "✅ คุณได้รับบทบาทแอดมินแล้ว",
        "admin.users.remove_admin.success": "✅ ถอดถอนบทบาทแอดมินจาก {name} แล้ว",
        "admin.users.remove_admin.notify": "❌ บทบาทแอดมินของคุณถูกถอดถอนแล้ว",
        "admin.users.bonus.prompt": "กรอกจำนวนโบนัสเป็น {currency}:",
        "admin.users.bonus.added": "✅ โบนัสการแนะนำของ {name} ถูกเติมเงิน {amount} {currency}",
        "admin.users.bonus.added.notify": "🎁 คุณได้รับโบนัสการแนะนำจำนวน {amount} {currency}",
        "admin.users.bonus.invalid": "❌ จำนวนไม่ถูกต้อง กรุณากรอกตัวเลขตั้งแต่ {min_amount} ถึง {max_amount} {currency}",

        # === Admin: Shop Management Menu ===
        "admin.shop.menu.title": "⛩️ จัดการร้านค้า",
        "admin.shop.menu.statistics": "📊 สถิติ",
        "admin.shop.menu.logs": "📁 แสดงบันทึก",
        "admin.shop.menu.admins": "👮 แอดมิน",
        "admin.shop.menu.users": "👤 ผู้ใช้",

        # === Admin: Categories Management ===
        "admin.categories.menu.title": "⛩️ จัดการหมวดหมู่",
        "admin.categories.add": "➕ เพิ่มหมวดหมู่",
        "admin.categories.rename": "✏️ เปลี่ยนชื่อหมวดหมู่",
        "admin.categories.delete": "🗑 ลบหมวดหมู่",
        "admin.categories.prompt.add": "กรอกชื่อหมวดหมู่ใหม่:",
        "admin.categories.prompt.delete": "กรอกชื่อหมวดหมู่ที่ต้องการลบ:",
        "admin.categories.prompt.rename.old": "กรอกชื่อหมวดหมู่ปัจจุบันที่ต้องการเปลี่ยนชื่อ:",
        "admin.categories.prompt.rename.new": "กรอกชื่อหมวดหมู่ใหม่:",
        "admin.categories.add.exist": "❌ ไม่สามารถสร้างหมวดหมู่ได้ (มีอยู่แล้ว)",
        "admin.categories.add.success": "✅ สร้างหมวดหมู่แล้ว",
        "admin.categories.delete.not_found": "❌ ไม่สามารถลบหมวดหมู่ได้ (ไม่มีหมวดหมู่นี้)",
        "admin.categories.delete.success": "✅ ลบหมวดหมู่แล้ว",
        "admin.categories.rename.not_found": "❌ ไม่สามารถอัปเดตหมวดหมู่ได้ (ไม่มีหมวดหมู่นี้)",
        "admin.categories.rename.exist": "❌ ไม่สามารถเปลี่ยนชื่อได้ (มีหมวดหมู่ชื่อนี้อยู่แล้ว)",
        "admin.categories.rename.success": "✅ หมวดหมู่ \"{old}\" เปลี่ยนชื่อเป็น \"{new}\"",

        # === Admin: Goods / Items Management (Add / List / Item Info) ===
        "admin.goods.add_position": "➕ เพิ่มสินค้า",
        "admin.goods.manage_stock": "➕ เพิ่มสินค้าในรายการ",
        "admin.goods.update_position": "📝 แก้ไขสินค้า",
        "admin.goods.delete_position": "❌ ลบสินค้า",
        "admin.goods.add.prompt.type": "เลือกประเภทสินค้า:",
        "admin.goods.add.type.prepared": "🍳 ทำสดใหม่ตามสั่ง (อาหาร, เครื่องดื่ม)",
        "admin.goods.add.type.product": "📦 สินค้าบรรจุภัณฑ์ (น้ำ, ขนม)",
        "admin.goods.add.prompt.name": "กรอกชื่อสินค้า",
        "admin.goods.add.name.exists": "❌ ไม่สามารถสร้างสินค้าได้ (มีอยู่แล้ว)",
        "admin.goods.add.prompt.description": "กรอกรายละเอียดสินค้า:",
        "admin.goods.add.prompt.price": "กรอกราคาสินค้า (ตัวเลขเป็น {currency}):",
        "admin.goods.add.price.invalid": "⚠️ ราคาไม่ถูกต้อง กรุณากรอกตัวเลข",
        "admin.goods.add.prompt.category": "กรอกหมวดหมู่ที่สินค้าจะอยู่:",
        "admin.goods.add.category.not_found": "❌ ไม่สามารถสร้างสินค้าได้ (หมวดหมู่ไม่ถูกต้อง)",
        "admin.goods.position.not_found": "❌ ไม่มีสินค้า (ไม่มีรายการนี้)",
        "admin.goods.menu.title": "⛩️ เมนูจัดการสินค้า",
        "admin.goods.add.stock.prompt": "กรอกจำนวนสินค้าที่ต้องการเพิ่ม",
        "admin.goods.add.stock.invalid": "⚠️ จำนวนสินค้าไม่ถูกต้อง กรุณากรอกตัวเลข",
        "admin.goods.add.stock.negative": "⚠️ จำนวนสินค้าไม่ถูกต้อง กรุณากรอกจำนวนที่เป็นบวก",
        "admin.goods.add.result.created_with_stock": "✅ สินค้า {item_name} ถูกสร้างแล้ว เพิ่ม {stock_quantity} เข้าในจำนวนสินค้า",

        # === Admin: Goods / Items Update Flow ===
        "admin.goods.update.position.invalid": "ไม่พบสินค้า",
        "admin.goods.update.position.exists": "มีสินค้าชื่อนี้อยู่แล้ว",
        "admin.goods.update.prompt.name": "กรอกชื่อสินค้า",
        "admin.goods.update.not_exists": "❌ ไม่สามารถแก้ไขสินค้าได้ (ไม่มีสินค้านี้)",
        "admin.goods.update.prompt.new_name": "กรอกชื่อสินค้าใหม่:",
        "admin.goods.update.prompt.description": "กรอกรายละเอียดสินค้า:",
        "admin.goods.update.success": "✅ อัปเดตสินค้าแล้ว",

        # === Admin: Goods / Items Delete Flow ===
        "admin.goods.delete.prompt.name": "กรอกชื่อสินค้า",
        "admin.goods.delete.position.not_found": "❌ ไม่สามารถลบสินค้าได้ (ไม่มีสินค้านี้)",
        "admin.goods.delete.position.success": "✅ ลบสินค้าแล้ว",

        # === Admin: Item Info ===
        "admin.goods.view_stock": "ดูสินค้า",

        # Admin Modifier Management (Card 8)
        "admin.goods.manage_modifiers": "🍳 ตัวเลือกเพิ่มเติม",
        "admin.goods.modifiers.prompt": "ต้องการเพิ่มตัวเลือก (ระดับเผ็ด เครื่องเคียง ฯลฯ) หรือไม่?",
        "admin.goods.modifiers.add_btn": "➕ เพิ่มตัวเลือก",
        "admin.goods.modifiers.skip_btn": "⏭ ข้าม",
        "admin.goods.modifiers.json_prompt": "วางสคีมา JSON ของตัวเลือก:",
        "admin.goods.modifiers.invalid_json": "❌ JSON ไม่ถูกต้อง: {error}",
        "admin.goods.modifiers.select_item": "กรอกชื่อสินค้าเพื่อตั้งค่าตัวเลือก:",
        "admin.goods.modifiers.edit_instructions": "เลือกการดำเนินการ:",
        "admin.goods.modifiers.set_new": "📝 ตั้งค่าใหม่",
        "admin.goods.modifiers.clear": "🗑 ล้างทั้งหมด",

        # === Admin: Logs ===
        "admin.shop.logs.caption": "บันทึกบอท",
        "admin.shop.logs.empty": "❗️ ยังไม่มีบันทึก",

        # === Group Notifications ===
        "shop.group.new_upload": "สต็อกใหม่",
        "shop.group.item": "สินค้า",
        "shop.group.stock": "จำนวน",

        # === Admin: Statistics ===
        "admin.shop.stats.template": (
            "สถิติร้านค้า:\n"
            "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            "<b>◽ผู้ใช้</b>\n"
            "◾️ผู้ใช้ใน 24 ชั่วโมงที่ผ่านมา: {today_users}\n"
            "◾️แอดมินทั้งหมด: {admins}\n"
            "◾️ผู้ใช้ทั้งหมด: {users}\n"
            "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            "◽<b>อื่นๆ</b>\n"
            "◾สินค้า: {items} ชิ้น\n"
            "◾รายการ: {goods} ชิ้น\n"
            "◾หมวดหมู่: {categories} ชิ้น\n"
        ),

        # === Admin: Lists & Broadcast ===
        "admin.shop.admins.title": "👮 แอดมินบอท:",
        "admin.shop.users.title": "ผู้ใช้บอท:",
        "broadcast.prompt": "ส่งข้อความเพื่อประกาศ:",
        "broadcast.creating": "📤 เริ่มการประกาศ...\n👥 ผู้ใช้ทั้งหมด: {ids}",
        "broadcast.progress": (
            "📤 กำลังประกาศ...\n\n\n"
            "📊 ความคืบหน้า: {progress:.1f}%{n}"
            "✅ ส่งแล้ว: {sent}/{total}\n"
            "❌ ข้อผิดพลาด: {failed}\n"
            "⏱ เวลาที่ผ่านไป: {time} วินาที"),
        "broadcast.done": (
            "✅ การประกาศเสร็จสิ้น!\n\n"
            "📊 สถิติ:📊\n"
            "👥 ทั้งหมด: {total}\n"
            "✅ ส่งสำเร็จ: {sent}\n"
            "❌ ส่งไม่สำเร็จ: {failed}\n"
            "🚫 บล็อกบอท: ~{blocked}\n"
            "📈 อัตราความสำเร็จ: {success}%\n"
            "⏱ เวลา: {duration} วินาที"
        ),
        "broadcast.cancel": "❌ ยกเลิกการประกาศแล้ว",
        "broadcast.warning": "ไม่มีการประกาศที่กำลังดำเนินอยู่",

        # === Brand / Store Selection ===
        "shop.brands.title": "🏪 เลือกร้านอาหาร",
        "shop.branches.title": "📍 เลือกสาขา",
        "shop.no_brands": "ยังไม่มีร้านอาหารในขณะนี้",
        "shop.brand_unavailable": "ร้านอาหารนี้ไม่พร้อมให้บริการในขณะนี้",

        # === Shop Browsing (Categories / Goods / Item Page) ===
        "shop.categories.title": "🏪 หมวดหมู่ร้านค้า",
        "shop.goods.choose": "🏪 เลือกสินค้าที่ต้องการ",
        "shop.item.not_found": "ไม่พบสินค้า",
        "shop.item.title": "🏪 สินค้า {name}",
        "shop.item.description": "รายละเอียด: {description}",
        "shop.item.price": "ราคา — {amount} {currency}",
        "shop.item.quantity_unlimited": "จำนวน — ไม่จำกัด",
        "shop.item.quantity_left": "จำนวน — {count} ชิ้น",
        "shop.item.quantity_detailed": "📦 สต็อกทั้งหมด: {total} ชิ้น\n🔒 จองแล้ว: {reserved} ชิ้น\n✅ พร้อมสั่งซื้อ: {available} ชิ้น",

        # === Purchases ===
        "purchases.title": "สินค้าที่ซื้อแล้ว:",
        "purchases.pagination.invalid": "ข้อมูลการแบ่งหน้าไม่ถูกต้อง",
        "purchases.item.not_found": "ไม่พบรายการซื้อ",
        "purchases.item.name": "<b>🧾 สินค้า</b>: <code>{name}</code>",
        "purchases.item.price": "<b>💵 ราคา</b>: <code>{amount}</code> {currency}",
        "purchases.item.datetime": "<b>🕒 วันที่ซื้อ</b>: <code>{dt}</code>",
        "purchases.item.unique_id": "<b>🧾 ID เฉพาะ</b>: <code>{uid}</code>",
        "purchases.item.value": "<b>🔑 ค่า</b>:\n<code>{value}</code>",

        # === Middleware ===
        "middleware.ban": "⏳ คุณถูกบล็อกชั่วคราว กรุณารอ {time} วินาที",
        "middleware.above_limits": "⚠️ คำขอมากเกินไป! คุณถูกบล็อกชั่วคราว",
        "middleware.waiting": "⏳ กรุณารอ {time} วินาทีก่อนดำเนินการต่อไป",
        "middleware.security.session_outdated": "⚠️ เซสชันหมดอายุแล้ว กรุณาเริ่มใหม่",
        "middleware.security.invalid_data": "❌ ข้อมูลไม่ถูกต้อง",
        "middleware.security.blocked": "❌ การเข้าถึงถูกบล็อก",
        "middleware.security.not_admin": "⛔ สิทธิ์ไม่เพียงพอ",
        "middleware.security.banned": "⛔ <b>คุณถูกแบน</b>\n\nเหตุผล: {reason}",
        "middleware.security.banned_no_reason": "⛔ <b>คุณถูกแบน</b>\n\nกรุณาติดต่อผู้ดูแลระบบเพื่อขอข้อมูลเพิ่มเติม",
        "middleware.security.rate_limit": "⚠️ คำขอมากเกินไป! กรุณารอสักครู่",

        # === Errors ===
        "errors.not_subscribed": "คุณยังไม่ได้สมัครสมาชิก",
        "errors.pagination_invalid": "ข้อมูลการแบ่งหน้าไม่ถูกต้อง",
        "errors.invalid_data": "❌ ข้อมูลไม่ถูกต้อง",
        "errors.channel.telegram_not_found": "ฉันไม่สามารถเขียนไปยังช่องได้ กรุณาเพิ่มฉันเป็นแอดมินช่อง @{channel} พร้อมสิทธิ์ในการเผยแพร่ข้อความ",
        "errors.channel.telegram_forbidden_error": "ไม่พบช่อง กรุณาตรวจสอบชื่อผู้ใช้ช่อง @{channel}",
        "errors.channel.telegram_bad_request": "ไม่สามารถส่งไปยังช่องได้: {e}",

        # === Orders ===
        "order.payment_method.choose": "💳 เลือกวิธีการชำระเงิน:",
        "order.payment_method.bitcoin": "💳 Bitcoin",
        "order.payment_method.litecoin": "💳 Litecoin",
        "order.payment_method.solana": "💳 SOL",
        "order.payment_method.usdt_sol": "💳 USDT (Solana)",
        "order.payment_method.cash": "💵 เก็บเงินปลายทาง",
        "order.status.notify_order_confirmed": (
            "คำสั่งซื้อ {order_code} ได้รับการยืนยัน! 🎉\n\n"
            "คำสั่งซื้อของคุณจะถูกจัดส่งเวลา: {delivery_time}\n\n"
            "สินค้า:\n{items}\n\n"
            "รวม: {total}\n\n"
            "รอรับสินค้า!"
        ),
        "order.status.notify_order_delivered": (
            "คำสั่งซื้อ {order_code} จัดส่งแล้ว! ✅\n\n"
            "ขอบคุณสำหรับการสั่งซื้อ! หวังว่าจะได้พบคุณอีก! 🙏"
        ),
        "order.status.notify_order_modified": (
            "คำสั่งซื้อ {order_code} ถูกแก้ไขโดยแอดมิน 📝\n\n"
            "การเปลี่ยนแปลง:\n{changes}\n\n"
            "ยอดรวมใหม่: {total}"
        ),

        # === Additional Common Buttons ===
        "btn.cart": "🛒 ตะกร้า",
        "btn.my_orders": "📦 คำสั่งซื้อของฉัน",
        "btn.reference_codes": "🔑 รหัสอ้างอิง",
        "btn.settings": "⚙️ ตั้งค่า",
        "btn.referral_bonus_percent": "💰 เปอร์เซ็นต์โบนัสการแนะนำ",
        "btn.order_timeout": "⏱️ หมดเวลาคำสั่งซื้อ",
        "btn.timezone": "🌍 เขตเวลา",
        "btn.promptpay_account": "💳 บัญชี PromptPay",
        "btn.currency": "💱 สกุลเงิน",
        "btn.skip": "⏭️ ข้าม",
        "btn.use_saved_info": "✅ ใช้ข้อมูลที่บันทึกไว้",
        "btn.update_info": "✏️ อัปเดตข้อมูล",
        "btn.back_to_cart": "◀️ กลับไปที่ตะกร้า",
        "btn.clear_cart": "🗑️ ล้างตะกร้า",
        "btn.proceed_checkout": "💳 ดำเนินการสั่งซื้อ",
        "btn.remove_item": "❌ ลบ {item_name}",
        "btn.use_all_bonus": "ใช้ทั้งหมด ${amount}",
        "btn.apply_bonus_yes": "✅ ใช่ ใช้โบนัส",
        "btn.apply_bonus_no": "❌ ไม่ เก็บไว้ใช้ทีหลัง",
        "btn.cancel": "❌ ยกเลิก",
        "btn.add_to_cart": "🛒 เพิ่มลงตะกร้า",

        # === Cart Management ===
        "cart.add_success": "✅ เพิ่ม {item_name} ลงตะกร้าแล้ว!",
        "cart.add_error": "❌ {message}",
        "cart.empty": "🛒 ตะกร้าของคุณว่างเปล่า\n\nเรียกดูร้านค้าเพื่อเพิ่มสินค้า!",
        "cart.title": "🛒 <b>ตะกร้าสินค้าของคุณ</b>\n\n",
        "cart.removed_success": "ลบสินค้าออกจากตะกร้าแล้ว",
        "cart.cleared_success": "✅ ล้างตะกร้าเรียบร้อยแล้ว!",
        "cart.empty_alert": "ตะกร้าว่างเปล่า!",
        "cart.summary_title": "📦 <b>สรุปคำสั่งซื้อ</b>\n\n",
        "cart.saved_delivery_info": "ข้อมูลการจัดส่งที่บันทึกไว้ของคุณ:\n\n",
        "cart.delivery_address": "📍 ที่อยู่: {address}\n",
        "cart.delivery_phone": "📞 โทรศัพท์: {phone}\n",
        "cart.delivery_note": "📝 หมายเหตุ: {note}\n",
        "cart.use_info_question": "\n\nคุณต้องการใช้ข้อมูลนี้หรือต้องการอัปเดต?",
        "cart.no_saved_info": "❌ ไม่พบข้อมูลการจัดส่งที่บันทึกไว้ กรุณากรอกข้อมูลด้วยตนเอง",

        # === Order/Delivery Flow ===
        "order.delivery.address_prompt": "📍 กรุณากรอกที่อยู่จัดส่ง:",
        "order.delivery.address_invalid": "❌ กรุณากรอกที่อยู่จัดส่งที่ถูกต้อง (อย่างน้อย 5 ตัวอักษร)",
        "order.delivery.phone_prompt": "📞 กรุณากรอกหมายเลขโทรศัพท์ (พร้อมรหัสประเทศ):",
        "order.delivery.phone_invalid": "❌ กรุณากรอกหมายเลขโทรศัพท์ที่ถูกต้อง (อย่างน้อย 8 หลัก)",
        "order.delivery.note_prompt": "📝 มีคำแนะนำพิเศษสำหรับการจัดส่งหรือไม่? (ไม่บังคับ)\n\nคุณสามารถข้ามขั้นตอนนี้โดยกดปุ่มด้านล่าง",
        "order.delivery.info_save_error": "❌ เกิดข้อผิดพลาดในการบันทึกข้อมูลการจัดส่ง กรุณาลองอีกครั้ง",

        # Location Method Choice
        "order.delivery.location_method_prompt": "📍 คุณต้องการแจ้งที่อยู่จัดส่งอย่างไร?\n\nเลือกวิธีด้านล่าง:",
        "btn.location_method.gps": "📡 ส่ง GPS ผ่าน Telegram",
        "btn.location_method.live_gps": "📍 แชร์ตำแหน่งสด",
        "btn.location_method.google_link": "🗺 ส่งลิงก์ Google Maps",
        "btn.location_method.type_address": "✍️ พิมพ์ที่อยู่",
        "order.delivery.gps_prompt": "📍 กดปุ่มด้านล่างเพื่อแชร์ตำแหน่งของคุณ:",
        "order.delivery.gps_hint": "📍 กรุณาใช้ปุ่มด้านล่างเพื่อแชร์ตำแหน่ง GPS หรือกด 'กลับ' เพื่อเลือกวิธีอื่น",
        "order.delivery.live_gps_prompt": "📍 วิธีแชร์ตำแหน่งสด:\n\n1. กดไอคอนแนบไฟล์ 📎 ด้านล่าง\n2. เลือก 'ตำแหน่ง'\n3. กด 'แชร์ตำแหน่งสด'\n4. เลือกระยะเวลา\n\nคนขับจะเห็นตำแหน่งของคุณแบบเรียลไทม์!",
        "order.delivery.live_gps_saved": "✅ ได้รับตำแหน่งสดแล้ว! คนขับจะสามารถติดตามตำแหน่งของคุณได้",
        "order.delivery.live_gps_hint": "📍 กรุณาแชร์ตำแหน่งสดผ่านเมนูแนบไฟล์ (📎 → ตำแหน่ง → แชร์ตำแหน่งสด)",
        "order.delivery.google_link_prompt": "🗺 วางลิงก์ Google Maps ที่มีตำแหน่งของคุณ\n\nเปิด Google Maps ค้นหาตำแหน่ง กด 'แชร์' แล้วคัดลอกลิงก์มาวางที่นี่",
        "order.delivery.google_link_invalid": "❌ ไม่สามารถรับรู้ลิงก์ Google Maps ได้ กรุณาตรวจสอบว่าลิงก์เริ่มต้นด้วย google.com/maps หรือ goo.gl/maps",
        "order.delivery.address_confirm_prompt": "📍 ที่อยู่ของคุณ:\n<b>{address}</b>\n\n🔗 <a href=\"{maps_link}\">ดูบนแผนที่</a>\n\nถูกต้องหรือไม่?",
        "btn.address_confirm_yes": "✅ ใช่ ถูกต้อง",
        "btn.address_confirm_retry": "✏️ ไม่ใช่ กรอกใหม่",

        # GPS Location (Card 2)
        "order.delivery.location_prompt": "📍 คุณต้องการแชร์ตำแหน่ง GPS เพื่อการจัดส่งที่แม่นยำยิ่งขึ้นหรือไม่?\n\nกดปุ่มด้านล่างหรือข้ามขั้นตอนนี้",
        "order.delivery.location_saved": "✅ บันทึกตำแหน่งแล้ว!",
        "btn.share_location": "📍 แชร์ตำแหน่ง",
        "btn.skip_location": "⏭ ข้าม",

        # Delivery Type (Card 3)
        "order.delivery.type_prompt": "🚚 เลือกประเภทการจัดส่ง:",
        "btn.delivery.door": "🚪 จัดส่งถึงหน้าประตู",
        "btn.delivery.dead_drop": "📦 วางไว้ที่จุดรับ",
        "btn.delivery.pickup": "🏪 รับเอง",
        "order.delivery.drop_instructions_prompt": "📝 อธิบายสถานที่ที่จะวางคำสั่งซื้อ (เช่น 'ฝากไว้กับรปภ.ที่ล็อบบี้', 'วางใต้พรมหน้าห้อง 405'):",
        "order.delivery.drop_gps_prompt": "📍 แชร์ตำแหน่ง GPS ของจุดรับโดยกดปุ่มด้านล่าง:",
        "btn.share_drop_location": "📍 แชร์ตำแหน่ง",
        "order.delivery.drop_gps_saved": "✅ บันทึกตำแหน่ง GPS แล้ว!",
        "order.delivery.drop_media_prompt": "📸 ส่งรูปถ่ายหรือวิดีโอของจุดรับ (ส่งได้หลายไฟล์) กด 'เสร็จสิ้น' เมื่อเสร็จ:",
        "order.delivery.drop_media_saved": "✅ บันทึกแล้ว {count} ไฟล์ ส่งเพิ่มหรือกด 'เสร็จสิ้น'",
        "btn.drop_media_done": "✅ เสร็จสิ้น",
        "btn.skip_drop_media": "⏭ ข้าม",
        "order.delivery.drop_photo_prompt": "📸 ต้องการส่งรูปถ่ายจุดรับหรือไม่? (ไม่บังคับ)",
        "order.delivery.drop_photo_saved": "✅ บันทึกรูปถ่ายจุดรับแล้ว!",
        "btn.skip_drop_photo": "⏭ ข้ามรูปถ่าย",

        # PromptPay (Card 1)
        "order.payment_method.promptpay": "💳 PromptPay QR",
        "order.payment.promptpay.title": "💳 <b>ชำระเงินผ่าน PromptPay</b>",
        "order.payment.promptpay.scan": "📱 สแกน QR เพื่อชำระเงิน:",
        "order.payment.promptpay.upload_receipt": "📸 หลังชำระเงินแล้ว กรุณาอัปโหลดสลิปการโอนเงิน:",
        "order.payment.promptpay.receipt_received": "✅ ได้รับสลิปแล้ว! รอการยืนยันจากแอดมิน",
        "order.payment.promptpay.receipt_invalid": "❌ กรุณาส่งรูปถ่ายสลิปการโอนเงิน",
        "order.payment.promptpay.slip_verified": "✅ ตรวจสอบการชำระเงินอัตโนมัติสำเร็จ! คำสั่งซื้อของคุณได้รับการยืนยันแล้ว",
        "admin.order.verify_payment": "✅ ยืนยันการชำระเงิน",
        "admin.order.payment_verified": "✅ ยืนยันการชำระเงินแล้ว",

        # Delivery Chat (Card 13)
        "order.delivery.chat_unavailable": "❌ แชทกับคนขับไม่พร้อมใช้งาน กลุ่มไรเดอร์ยังไม่ได้ตั้งค่า",
        "order.delivery.chat_started": "💬 คุณสามารถส่งข้อความถึงคนขับได้ ส่งข้อความ รูปภาพ หรือตำแหน่ง\n\nส่ง /endchat เพื่อจบการสนทนา",
        "order.delivery.live_location_shared": "📍 คนขับแชร์ตำแหน่งสด! คุณสามารถติดตามการจัดส่งได้",
        "order.delivery.chat_no_active_delivery": "❌ คุณไม่มีการจัดส่งที่กำลังดำเนินอยู่สำหรับแชท",
        "order.delivery.chat_ended": "✅ จบการสนทนากับคนขับแล้ว",
        "order.delivery.chat_message_sent": "✅ ส่งข้อความถึงคนขับแล้ว",
        "order.delivery.driver_no_active_order": "⚠️ ไม่มีออเดอร์ที่กำลังจัดส่งสำหรับส่งต่อข้อความนี้",
        "btn.chat_with_driver": "💬 แชทกับคนขับ",

        # GPS tracking & chat session (Card 15)
        "delivery.gps.prompt": "📍 ออเดอร์ {order_code} ของคุณกำลังมา!\n\nช่วยให้คนขับหาคุณเจอเร็วขึ้น — แชร์ตำแหน่งของคุณ:",
        "delivery.gps.btn_static": "📍 ส่งตำแหน่ง",
        "delivery.gps.btn_live": "📡 ตำแหน่งสด",
        "delivery.gps.btn_skip": "⏭ ข้าม",
        "delivery.gps.static_sent": "✅ ส่งตำแหน่งของคุณให้คนขับแล้ว",
        "delivery.gps.live_started": "📡 เปิดตำแหน่งสดแล้ว! คนขับสามารถติดตามคุณได้แบบเรียลไทม์",
        "delivery.gps.skipped": "⏭ ข้ามตำแหน่งแล้ว คนขับจะใช้ที่อยู่จากออเดอร์",
        "delivery.chat.session_closed": "⏹ เซสชันแชทนี้สิ้นสุดแล้ว ติดต่อฝ่ายสนับสนุนเพื่อขอความช่วยเหลือ",
        "delivery.chat.post_delivery_open": "✅ จัดส่งแล้ว! แชทยังเปิดอีก {minutes} นาที",
        "delivery.chat.post_delivery_closed": "⏹ หน้าต่างแชทหลังจัดส่งปิดแล้ว",
        "btn.end_chat": "❌ จบการสนทนา",

        # === Bonus/Referral Application ===
        "order.bonus.available": "💰 <b>คุณมีโบนัสการแนะนำ ${bonus_balance}!</b>\n\n",
        "order.bonus.apply_question": "คุณต้องการใช้โบนัสการแนะนำกับคำสั่งซื้อนี้หรือไม่?",
        "order.bonus.amount_positive_error": "❌ กรุณากรอกจำนวนที่เป็นบวก",
        "order.bonus.amount_too_high": "❌ จำนวนมากเกินไป สูงสุดที่ใช้ได้: ${max_applicable}\nกรุณากรอกจำนวนที่ถูกต้อง:",
        "order.bonus.invalid_amount": "❌ จำนวนไม่ถูกต้อง กรุณากรอกตัวเลข (เช่น 5.50):",
        "order.bonus.insufficient": "❌ ยอดโบนัสไม่เพียงพอ กรุณาลองอีกครั้ง",
        "order.bonus.enter_amount": "กรอกจำนวนโบนัสที่ต้องการใช้ (สูงสุด ${max_applicable}):\n\nหรือใช้โบนัสทั้งหมดโดยกดปุ่มด้านล่าง",

        # === Payment Instructions ===
        "order.payment.system_unavailable": "❌ <b>ระบบชำระเงินไม่พร้อมใช้งานชั่วคราว</b>\n\nไม่มีที่อยู่ Bitcoin ที่พร้อมใช้งาน กรุณาติดต่อฝ่ายสนับสนุน",
        "order.payment.customer_not_found": "❌ ไม่พบข้อมูลลูกค้า กรุณาลองอีกครั้ง",
        "order.payment.creation_error": "❌ เกิดข้อผิดพลาดในการสร้างคำสั่งซื้อ กรุณาลองอีกครั้งหรือติดต่อฝ่ายสนับสนุน",

        # === Order Summary/Total ===
        "order.summary.title": "📦 <b>สรุปคำสั่งซื้อ</b>\n\n",
        "order.summary.cart_total": "ยอดรวมตะกร้า: ${cart_total}",
        "order.summary.bonus_applied": "โบนัสที่ใช้: -${bonus_applied}",
        "order.summary.final_amount": "ยอดรวมสุทธิ: ${final_amount}",

        # === Inventory/Reservation ===
        "order.inventory.unable_to_reserve": "❌ <b>ไม่สามารถจองสินค้าได้</b>\n\nสินค้าต่อไปนี้ไม่พร้อมจำหน่ายในจำนวนที่ต้องการ:\n\n{unavailable_items}\n\nกรุณาปรับตะกร้าของคุณและลองอีกครั้ง",

        # === My Orders View ===
        "myorders.title": "📦 <b>คำสั่งซื้อของฉัน</b>\n\n",
        "myorders.total": "คำสั่งซื้อทั้งหมด: {count}",
        "myorders.active": "⏳ คำสั่งซื้อที่กำลังดำเนินการ: {count}",
        "myorders.delivered": "✅ จัดส่งแล้ว: {count}",
        "myorders.select_category": "เลือกหมวดหมู่เพื่อดูคำสั่งซื้อ:",
        "myorders.active_orders": "⏳ คำสั่งซื้อที่กำลังดำเนินการ",
        "myorders.delivered_orders": "✅ คำสั่งซื้อที่จัดส่งแล้ว",
        "myorders.all_orders": "📋 คำสั่งซื้อทั้งหมด",
        "myorders.no_orders_yet": "คุณยังไม่มีคำสั่งซื้อ\n\nเรียกดูร้านค้าเพื่อเริ่มช้อปปิ้ง!",
        "myorders.browse_shop": "🛍️ ไปที่ร้านค้า",
        "myorders.back": "◀️ กลับ",
        "myorders.all_title": "📋 คำสั่งซื้อทั้งหมด",
        "myorders.active_title": "⏳ คำสั่งซื้อที่กำลังดำเนินการ",
        "myorders.delivered_title": "✅ คำสั่งซื้อที่จัดส่งแล้ว",
        "myorders.invalid_filter": "ตัวกรองไม่ถูกต้อง",
        "myorders.not_found": "ไม่พบคำสั่งซื้อ",
        "myorders.back_to_menu": "◀️ กลับไปเมนูคำสั่งซื้อ",
        "myorders.select_details": "เลือกคำสั่งซื้อเพื่อดูรายละเอียด:",
        "myorders.order_not_found": "ไม่พบคำสั่งซื้อ",

        # === Order Details Display ===
        "myorders.detail.title": "📦 <b>รายละเอียดคำสั่งซื้อ #{order_code}</b>\n\n",
        "myorders.detail.status": "📊 <b>สถานะ:</b> {status}\n",
        "myorders.detail.subtotal": "💵 <b>ยอดรวมย่อย:</b> ${subtotal}\n",
        "myorders.detail.bonus_applied": "🎁 <b>โบนัสที่ใช้:</b> ${bonus}\n",
        "myorders.detail.final_price": "💰 <b>ราคาสุทธิ:</b> ${total}\n",
        "myorders.detail.total_price": "💰 <b>ราคารวม:</b> ${total}\n",
        "myorders.detail.payment_method": "💳 <b>วิธีการชำระเงิน:</b> {method}\n",
        "myorders.detail.ordered": "📅 <b>สั่งซื้อเมื่อ:</b> {date}\n",
        "myorders.detail.delivery_time": "🚚 <b>กำหนดจัดส่ง:</b> {time}\n",
        "myorders.detail.completed": "✅ <b>เสร็จสิ้น:</b> {date}\n",
        "myorders.detail.items": "\n📦 <b>สินค้า:</b>\n{items}\n",
        "myorders.detail.delivery_info": "\n📍 <b>ข้อมูลการจัดส่ง:</b>\n{address}\n{phone}\n{note}",

        # === Help System ===
        "help.prompt": "📧 <b>ต้องการความช่วยเหลือ?</b>\n\n",
        "help.describe_issue": "กรุณาอธิบายปัญหาหรือคำถามของคุณ แล้วจะถูกส่งตรงไปยังผู้ดูแลระบบ\n\nพิมพ์ข้อความด้านล่าง:",
        "help.admin_not_configured": "❌ ขออภัย ยังไม่ได้ตั้งค่าช่องทางติดต่อแอดมิน กรุณาลองอีกครั้งภายหลัง",
        "help.admin_notification_title": "📧 <b>คำขอช่วยเหลือใหม่</b>\n\n",
        "help.admin_notification_from": "<b>จาก:</b> @{username} (ID: {user_id})\n",
        "help.admin_notification_message": "<b>ข้อความ:</b>\n{message}",
        "help.sent_success": "✅ {auto_message}",
        "help.sent_error": "❌ ไม่สามารถส่งข้อความถึงแอดมินได้: {error}\n\nกรุณาลองอีกครั้งภายหลัง",
        "help.cancelled": "ยกเลิกคำขอช่วยเหลือแล้ว",

        # === Admin Order Notifications ===
        "admin.order.action_required_title": "⏳ <b>ต้องดำเนินการ:</b>",
        "admin.order.address_label": "ที่อยู่: {address}",
        "admin.order.amount_to_collect_label": "<b>จำนวนเงินที่ต้องเก็บ: ${amount} {currency}</b>",
        "admin.order.amount_to_receive_label": "<b>จำนวนเงินที่จะได้รับ: ${amount} {currency}</b>",
        "admin.order.awaiting_payment_status": "⏳ รอการยืนยันการชำระเงิน...",
        "admin.order.bitcoin_address_label": "ที่อยู่ Bitcoin: <code>{address}</code>",
        "admin.order.bonus_applied_label": "โบนัสที่ใช้: <b>-${amount}</b>",
        "admin.order.customer_label": "ลูกค้า: {username} (ID: {id})",
        "admin.order.delivery_info_title": "<b>ข้อมูลการจัดส่ง:</b>",
        "admin.order.items_title": "<b>สินค้า:</b>",
        "admin.order.new_bitcoin_order": "🔔 <b>ได้รับคำสั่งซื้อ BITCOIN ใหม่</b>",
        "admin.order.new_cash_order": "🔔 <b>ได้รับคำสั่งซื้อเงินสดใหม่</b> 💵",
        "admin.order.note_label": "หมายเหตุ: {note}",
        "admin.order.order_label": "คำสั่งซื้อ: <b>{code}</b>",
        "admin.order.payment_cash": "เก็บเงินปลายทาง",
        "admin.order.payment_method_label": "วิธีการชำระเงิน: <b>{method}</b>",
        "admin.order.phone_label": "โทรศัพท์: {phone}",
        "admin.order.subtotal_label": "ยอดรวมย่อย: <b>${amount} {currency}</b>",
        "admin.order.use_cli_confirm": "ใช้ CLI เพื่อยืนยันคำสั่งซื้อและตั้งเวลาจัดส่ง:\n<code>python bot_cli.py order --order-code {code} --status-confirmed --delivery-time \"YYYY-MM-DD HH:MM\"</code>",
        "btn.admin.back_to_panel": "🔙 กลับไปแผงควบคุม",
        "btn.admin.create_refcode": "➕ สร้างรหัสอ้างอิง",
        "btn.admin.list_refcodes": "📋 รายการรหัสทั้งหมด",
        "btn.back_to_orders": "◀️ กลับไปคำสั่งซื้อ",
        "btn.create_reference_code": "➕ สร้างรหัสอ้างอิง",
        "btn.my_reference_codes": "🔑 รหัสอ้างอิงของฉัน",
        "btn.need_help": "❓ ต้องการความช่วยเหลือ?",
        "cart.item.price_format": "  ราคา: {price} {currency} × {quantity}",
        "cart.item.subtotal_format": "  ยอดรวมย่อย: {subtotal} {currency}",
        "cart.item.modifiers": "  ตัวเลือกเพิ่มเติม: {modifiers}",
        "cart.total_format": "<b>รวม: {total} {currency}</b>",
        "cart.add_cancelled": "ยกเลิกการเพิ่ม",
        "modifier.select_title": "เลือก {label}:",
        "modifier.selected": "เลือกแล้ว: {choice}",
        "modifier.required": "(จำเป็น)",
        "modifier.optional": "(ไม่จำเป็น)",
        "modifier.done": "เสร็จสิ้น",
        "modifier.price_extra": "+{price}",
        "modifier.cancelled": "ยกเลิกการเลือกตัวเลือกเพิ่มเติม",
        "help.pending_order.contact_support": "ใช้คำสั่ง /help เพื่อติดต่อฝ่ายสนับสนุน",
        "help.pending_order.issues_title": "<b>มีปัญหาหรือไม่?</b>",
        "help.pending_order.status": "คำสั่งซื้อของคุณกำลังรอการชำระเงิน",
        "help.pending_order.step1": "1. ส่งจำนวนเงินที่แน่นอนไปยังที่อยู่ Bitcoin ที่แสดง",
        "help.pending_order.step2": "2. รอการยืนยันจาก blockchain (ปกติ 10-60 นาที)",
        "help.pending_order.step3": "3. แอดมินจะยืนยันการชำระเงินและกำหนดเวลาจัดส่ง",
        "help.pending_order.step4": "4. สินค้าของคุณจะถูกจัดส่งโดยพนักงานส่งของ",
        "help.pending_order.title": "❓ <b>ต้องการความช่วยเหลือเกี่ยวกับคำสั่งซื้อ?</b>",
        "help.pending_order.what_to_do_title": "<b>สิ่งที่ต้องทำ:</b>",
        "myorders.detail.bitcoin_address_label": "ที่อยู่ Bitcoin:",
        "myorders.detail.bitcoin_admin_confirm": "หลังชำระเงินแล้ว แอดมินจะยืนยันคำสั่งซื้อของคุณ",
        "myorders.detail.bitcoin_send_instruction": "⚠️ กรุณาส่ง <b>{amount} {currency}</b> Bitcoin ไปยังที่อยู่นี้",
        "myorders.detail.cash_awaiting_confirm": "คำสั่งซื้อของคุณกำลังรอการยืนยันจากแอดมิน",
        "myorders.detail.cash_payment_courier": "ชำระเงินให้พนักงานส่งของเมื่อจัดส่ง",
        "myorders.detail.cash_title": "💵 เก็บเงินปลายทาง",
        "myorders.detail.cash_will_notify": "คุณจะได้รับแจ้งเมื่อคำสั่งซื้อได้รับการยืนยันและกำหนดเวลาจัดส่ง",
        "myorders.detail.confirmed_title": "✅ <b>คำสั่งซื้อได้รับการยืนยัน!</b>",
        "myorders.detail.delivered_thanks_message": "ขอบคุณสำหรับการสั่งซื้อ! หวังว่าจะได้พบคุณอีก! 🙏",
        "myorders.detail.delivered_title": "📦 <b>คำสั่งซื้อจัดส่งแล้ว!</b>",
        "myorders.detail.payment_info_title": "<b>ข้อมูลการชำระเงิน:</b>",
        "myorders.detail.preparing_message": "คำสั่งซื้อของคุณกำลังเตรียมจัดส่ง",
        "myorders.detail.scheduled_delivery_label": "กำหนดจัดส่ง: <b>{time}</b>",
        "myorders.order_summary_format": "{status_emoji} {code} - {items_count} สินค้า - {total} {currency}",
        "order.bonus.available_label": "โบนัสที่ใช้ได้: <b>${amount}</b>",
        "order.bonus.choose_amount_hint": "คุณสามารถเลือกจำนวนที่ต้องการใช้ (สูงสุด ${max_amount})",
        "order.bonus.enter_amount_title": "💵 <b>กรอกจำนวนโบนัสที่ต้องการใช้</b>",
        "order.bonus.max_applicable_label": "สูงสุดที่ใช้ได้: <b>${amount}</b>",
        "order.bonus.order_total_label": "ยอดรวมคำสั่งซื้อ: <b>${amount} {currency}</b>",
        "order.info.view_status_hint": "💡 คุณสามารถดูสถานะคำสั่งซื้อได้ตลอดเวลาโดยใช้คำสั่ง /orders",
        "order.payment.bitcoin.address_title": "<b>ที่อยู่ Bitcoin สำหรับชำระเงิน:</b>",
        "order.payment.bitcoin.admin_confirm": "• หลังชำระเงินแล้ว แอดมินจะยืนยันคำสั่งซื้อของคุณ",
        "order.payment.bitcoin.delivery_title": "<b>การจัดส่ง:</b>",
        "order.payment.bitcoin.important_title": "⚠️ <b>สำคัญ:</b>",
        "order.payment.bitcoin.items_title": "<b>สินค้า:</b>",
        "order.payment.bitcoin.need_help": "ต้องการความช่วยเหลือ? ใช้ /help เพื่อติดต่อฝ่ายสนับสนุน",
        "order.payment.bitcoin.one_time_address": "• ที่อยู่นี้ใช้ได้ครั้งเดียวเท่านั้น",
        "order.payment.bitcoin.order_code": "คำสั่งซื้อ: <b>{code}</b>",
        "order.payment.bitcoin.send_exact": "• ส่งจำนวนเงินที่แน่นอนตามที่แสดงด้านบน",
        "order.payment.bitcoin.title": "💳 <b>คำแนะนำการชำระเงิน Bitcoin</b>",
        "order.payment.bitcoin.total_amount": "ยอดรวม: <b>{amount} {currency}</b>",

        # Crypto payment (Card 18) — generic strings for all coins
        "crypto.payment.title": "💳 <b>{coin_name} Payment</b>",
        "crypto.payment.order_code": "Order: <b>{code}</b>",
        "crypto.payment.total_fiat": "Total: <b>{amount} {currency}</b>",
        "crypto.payment.rate": "Rate: 1 {coin} = {rate} {currency}",
        "crypto.payment.amount_due": "Amount due: <b>{crypto_amount} {coin}</b>",
        "crypto.payment.address": "<b>Send to this address:</b>\n<code>{address}</code>",
        "crypto.payment.send_exact": "• Send EXACTLY this amount",
        "crypto.payment.one_time": "• This address is for ONE-TIME use",
        "crypto.payment.auto_confirm": "• Your order will be automatically confirmed once the payment is detected on-chain.",
        "crypto.payment.waiting": "⏳ Waiting for payment...\nThis address expires in {timeout} minutes.",
        "crypto.payment.no_address": "❌ No {coin} addresses available. Please contact support or choose another payment method.",
        "crypto.payment_detected": (
            "✅ <b>Payment detected!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "⏳ Waiting for confirmations..."
        ),
        "crypto.payment_confirmed": (
            "✅ <b>Payment confirmed!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "Your order is now being processed."
        ),
        "crypto.payment_expired": "⏰ Payment window for your {coin} order ({order_code}) has expired. Please place a new order.",

        "order.payment.cash.admin_contact": "แอดมินจะติดต่อคุณในเร็วๆ นี้",
        "order.payment.cash.after_confirm": "หลังยืนยันแล้ว คุณจะได้รับแจ้งเวลาจัดส่ง",
        "order.payment.cash.created": "คำสั่งซื้อ {code} ของคุณถูกสร้างแล้วและรอการยืนยันจากแอดมิน",
        "order.payment.cash.important": "⏳ <b>สำคัญ:</b> คำสั่งซื้อถูกจองไว้ในระยะเวลาจำกัด",
        "order.payment.cash.items_title": "สินค้า:",
        "order.payment.cash.payment_to_courier": "ชำระเงินให้พนักงานส่งของเมื่อจัดส่ง",
        "order.payment.cash.title": "💵 <b>เก็บเงินปลายทาง</b>",
        "order.payment.cash.total": "รวม: {amount}",
        "order.payment.error_general": "❌ เกิดข้อผิดพลาดในการสร้างคำสั่งซื้อ กรุณาลองอีกครั้งหรือติดต่อฝ่ายสนับสนุน",
        "order.summary.total_label": "<b>รวม: {amount} {currency}</b>",
        "order.payment.bonus_applied_label": "โบนัสที่ใช้: <b>-{amount} {currency}</b>",
        "order.payment.cash.amount_with_bonus": "<b>จำนวนเงินที่ต้องชำระเมื่อจัดส่ง: {amount} {currency}</b>",
        "order.payment.cash.total_label": "<b>ยอดรวมที่ต้องชำระเมื่อจัดส่ง: {amount} {currency}</b>",
        "order.payment.final_amount_label": "<b>ยอดรวมสุทธิที่ต้องชำระ: {amount} {currency}</b>",
        "order.payment.order_label": "📋 <b>คำสั่งซื้อ: {code}</b>",
        "order.payment.subtotal_label": "ยอดรวมย่อย: <b>{amount} {currency}</b>",
        "order.payment.total_amount_label": "<b>ยอดรวม: {amount} {currency}</b>",

        # === Card 9: Kitchen & Delivery Workflow ===
        "admin.menu.orders": "📋 คำสั่งซื้อ",
        "admin.orders.list_title": "📋 <b>คำสั่งซื้อ</b>",
        "admin.orders.empty": "ไม่พบคำสั่งซื้อ",
        "admin.orders.filter_status": "กรองตามสถานะ",
        "admin.orders.filter_all": "📋 คำสั่งซื้อทั้งหมด",
        "admin.orders.filter_active": "🔄 ที่ใช้งาน",
        "admin.orders.detail": (
            "📋 <b>คำสั่งซื้อ #{order_id}</b> ({order_code})\n"
            "👤 ผู้ซื้อ: {buyer_id}\n"
            "💰 ยอดรวม: {total}\n"
            "📦 สถานะ: {status}\n"
            "📅 สร้างเมื่อ: {created_at}\n"
            "📍 ที่อยู่: {address}\n"
            "📞 โทรศัพท์: {phone}"
        ),
        "admin.orders.status_changed": "สถานะคำสั่งซื้อ #{order_id} เปลี่ยนเป็น <b>{new_status}</b>",
        "admin.orders.invalid_transition": "ไม่สามารถเปลี่ยนสถานะจาก {current} เป็น {new}",
        "kitchen.order_received": (
            "🍳 <b>คำสั่งซื้อใหม่ #{order_id}</b> ({order_code})\n\n"
            "{items}\n\n"
            "💰 ยอดรวม: {total}\n"
            "📍 ที่อยู่: {address}\n"
            "📞 โทรศัพท์: {phone}"
        ),
        "rider.order_ready": (
            "🚗 <b>คำสั่งซื้อพร้อมแล้ว #{order_id}</b> ({order_code})\n\n"
            "💰 ยอดรวม: {total}\n"
            "📍 ที่อยู่: {address}\n"
            "📞 โทรศัพท์: {phone}"
        ),
        "order.status.preparing": "🍳 คำสั่งซื้อ #{order_code} กำลังเตรียม",
        "order.status.ready": "✅ คำสั่งซื้อ #{order_code} พร้อมรับแล้ว",
        "order.status.out_for_delivery": "🚗 คำสั่งซื้อ #{order_code} กำลังจัดส่ง",
        "order.status.delivered_notify": "📦 คำสั่งซื้อ #{order_code} จัดส่งแล้ว",
        "kitchen.btn.start_preparing": "🍳 เริ่มเตรียม",
        "kitchen.btn.mark_ready": "✅ พร้อมแล้ว",
        "rider.btn.picked_up": "📦 รับแล้ว",
        "rider.btn.delivered": "✅ จัดส่งแล้ว",

        # Delivery Photo Proof (Card 4)
        "delivery.photo.required": "ต้องถ่ายรูปสำหรับการจัดส่งแบบฝากไว้ที่จุดนัด",
        "delivery.photo.upload_prompt": "กรุณาอัปโหลดรูปถ่ายการจัดส่ง",
        "delivery.photo.received": "บันทึกรูปถ่ายการจัดส่งแล้ว",
        "delivery.photo.sent_to_customer": "ส่งรูปถ่ายการจัดส่งให้ลูกค้าแล้ว",
        "delivery.photo.customer_notification": "คำสั่งซื้อ {order_code} ของคุณถูกจัดส่งแล้ว! นี่คือรูปถ่ายยืนยันการจัดส่ง",

        # === New Feature Strings ===

        # === Restaurant Feature Strings ===
        "admin.goods.add.allergen.dairy": "Dairy",
        "admin.goods.add.allergen.eggs": "Eggs",
        "admin.goods.add.allergen.fish": "Fish",
        "admin.goods.add.allergen.gluten": "Gluten",
        "admin.goods.add.allergen.nuts": "Nuts",
        "admin.goods.add.allergen.sesame": "Sesame",
        "admin.goods.add.allergen.shellfish": "Shellfish",
        "admin.goods.add.allergen.soy": "Soy",
        "admin.goods.add.allergens.done": "✅ Done",
        "admin.goods.add.allergens.skip": "⏭ No Allergens",
        "admin.goods.add.availability.invalid": "❌ Invalid format. Use HH:MM-HH:MM (e.g. 06:00-22:00)",
        "admin.goods.add.availability.skip": "⏭ All Day",
        "admin.goods.add.daily_limit.invalid": "❌ Enter a positive number.",
        "admin.goods.add.daily_limit.skip": "⏭ Unlimited",
        "admin.goods.add.modifier.add_another_group": "➕ Another Group",
        "admin.goods.add.modifier.add_group": "➕ Add Modifier Group",
        "admin.goods.add.modifier.add_option": "➕ Add Option",
        "admin.goods.add.modifier.all_done": "✅ Finish",
        "admin.goods.add.modifier.finish": "✅ Finish (No Modifiers)",
        "admin.goods.add.modifier.group_added": "✅ Group added! Add another group or finish.",
        "admin.goods.add.modifier.group_name": "Enter modifier group name (e.g. Spice Level):",
        "admin.goods.add.modifier.group_type": "Select type for this group:",
        "admin.goods.add.modifier.option_added": "✅ Option added! Add another or press Done.",
        "admin.goods.add.modifier.option_label": "Enter option label (e.g. Mild, Extra Cheese):",
        "admin.goods.add.modifier.option_price": "Enter price adjustment for this option (0 for free):",
        "admin.goods.add.modifier.options_done": "✅ Done with Options",
        "admin.goods.add.modifier.paste_json": "📋 Paste JSON",
        "admin.goods.add.modifier.required_no": "⭕ Optional",
        "admin.goods.add.modifier.required_yes": "✅ Required",
        "admin.goods.add.modifier.type_multi": "Multi Choice",
        "admin.goods.add.modifier.type_single": "Single Choice",
        "admin.goods.add.photo.done": "✅ Done",
        "admin.goods.add.photo.received": "✅ Media received! Send more or press Done.",
        "admin.goods.add.photo.send_more": "Send more photos/videos or press Done:",
        "admin.goods.add.photo.skip": "⏭ Skip Photos",
        "admin.goods.add.prep_time.invalid": "❌ Enter a positive number.",
        "admin.goods.add.prep_time.skip": "⏭ Skip",
        "admin.goods.add.prompt.allergens": "⚠️ Select allergens (tap to toggle, then Done):",
        "admin.goods.add.prompt.availability": "🕐 Enter availability hours (e.g. 06:00-22:00) or press Skip for all-day:",
        "admin.goods.add.prompt.daily_limit": "📊 Enter daily limit (max units per day) or press Skip for unlimited:",
        "admin.goods.add.prompt.modifier_group": "Add a modifier group (e.g. Spice Level, Extras)?",
        "admin.goods.add.prompt.photo": "📸 Send a photo or video of this item (or press Skip):",
        "admin.goods.add.prompt.prep_time": "⏱ Enter prep time in minutes (or press Skip):",
        "admin.goods.toggle.active_off": "🚫 {item}: Deactivated",
        "admin.goods.toggle.active_on": "✅ {item}: Activated",
        "admin.goods.toggle.sold_out_off": "✅ {item}: Back in stock",
        "admin.goods.toggle.sold_out_on": "❌ {item}: Marked SOLD OUT",
        "btn.view_gallery": "📸 Gallery ({count})",
        "kitchen.order.modifier_detail": "    ↳ {modifiers}",
        "kitchen.order.prep_time": "⏱ Est. prep: {minutes} min",
        "kitchen.order.ready_by": "🕐 Ready by: {time}",
        "order.estimated_ready": "⏱ Estimated ready in ~{minutes} min",
        "shop.item.allergens": "⚠️ Allergens: {allergens}",
        "shop.item.availability": "🕐 Available: {from_time} - {until_time}",
        "shop.item.calories": "🔥 {calories} cal",
        "shop.item.daily_remaining": "📊 Today: {remaining}/{limit} left",
        "shop.item.no_gallery": "No gallery for this item.",
        "shop.item.type_product": "📦 ประเภท: สินค้าบรรจุภัณฑ์",
        "shop.item.type_prepared": "🍳 ประเภท: ทำสดใหม่ตามสั่ง",
        "shop.item.prep_time": "⏱ Prep: ~{minutes} min",
        "shop.item.sold_out": "❌ Sold out today",
        "admin.accounting.export_payments": "📥 Payment Reconciliation",
        "admin.accounting.export_products": "📥 Revenue by Product",
        "admin.accounting.export_sales": "📥 Export Sales CSV",
        "admin.accounting.export_sent": "✅ Report exported.",
        "admin.accounting.no_data": "No data for this period.",
        "admin.accounting.summary": "📊 <b>Revenue Summary ({period})</b>\n\n💰 Revenue: {total} {currency}\n📦 Orders: {orders}\n📈 Avg: {avg} {currency}\n\n<b>By Payment:</b>\n{payments}\n\n<b>Top Products:</b>\n{products}",
        "admin.accounting.summary_all": "📊 All Time",
        "admin.accounting.summary_month": "📊 This Month",
        "admin.accounting.summary_today": "📊 Today",
        "admin.accounting.summary_week": "📊 This Week",
        "admin.accounting.title": "📊 <b>Accounting & Reports</b>",
        "admin.coupon.create": "➕ Create Coupon",
        "admin.coupon.created": "✅ Coupon <b>{code}</b> created!\nType: {type}\nValue: {value}\nMin order: {min_order}\nMax uses: {max_uses}\nExpires: {expiry}",
        "admin.coupon.detail": "🎟 <b>{code}</b>\nType: {type}\nValue: {value}\nMin Order: {min_order}\nMax Uses: {max_uses}\nUsed: {used}\nStatus: {status}\nExpires: {expiry}",
        "admin.coupon.empty": "No coupons found.",
        "admin.coupon.enter_code": "Enter coupon code (or type <b>auto</b> for random):",
        "admin.coupon.enter_expiry": "Enter expiry in days (or <b>skip</b> for no expiry):",
        "admin.coupon.enter_max_uses": "Enter max total uses (or <b>skip</b> for unlimited):",
        "admin.coupon.enter_min_order": "Enter minimum order amount (or <b>skip</b>):",
        "admin.coupon.enter_value": "Enter discount value ({type}):",
        "admin.coupon.invalid_value": "❌ Invalid value. Enter a number.",
        "admin.coupon.list_active": "📋 Active Coupons",
        "admin.coupon.list_all": "📋 All Coupons",
        "admin.coupon.select_type": "Select discount type:",
        "admin.coupon.title": "🎟 <b>Coupon Management</b>",
        "admin.coupon.toggle_activate": "✅ Activate",
        "admin.coupon.toggle_deactivate": "❌ Deactivate",
        "admin.coupon.toggled": "✅ Coupon {code} is now {status}.",
        "admin.coupon.type_fixed": "💰 Fixed Amount",
        "admin.coupon.type_percent": "📊 Percentage (%)",
        "admin.menu.accounting": "📊 Accounting",
        "admin.menu.coupons": "🎟 Coupons",
        "admin.menu.segment_broadcast": "📣 Targeted Broadcast",
        "admin.menu.stores": "🏪 Stores",
        "admin.menu.tickets": "🎫 Tickets",
        "admin.menu.ai_assistant": "🤖 AI Assistant",
        "admin.segment.all_users": "👥 All Users",
        "admin.segment.count": "📊 Segment: <b>{segment}</b>\nUsers: <b>{count}</b>\n\nType your broadcast message:",
        "admin.segment.empty": "No users in this segment.",
        "admin.segment.high_spenders": "💰 High Spenders",
        "admin.segment.inactive": "😴 Inactive (30+ days)",
        "admin.segment.new_users": "🆕 New Users (7d)",
        "admin.segment.recent_buyers": "🛒 Recent Buyers (7d)",
        "admin.segment.sent": "✅ Sent to {sent}/{total} ({segment}).",
        "admin.segment.title": "📣 <b>Targeted Broadcast</b>\n\nSelect segment:",
        "admin.store.add": "➕ Add Store",
        "admin.store.address_prompt": "Enter store address (or <b>skip</b>):",
        "admin.store.btn_default": "⭐ Set as Default",
        "admin.store.created": "✅ Store <b>{name}</b> created!",
        "admin.store.detail": "🏪 <b>{name}</b>\nStatus: {status}\nDefault: {default}\nAddress: {address}\nLocation: {location}\nPhone: {phone}",
        "admin.store.empty": "No stores configured.",
        "admin.store.location_prompt": "Send GPS location (or type <b>skip</b>):",
        "admin.store.name_exists": "Store with this name already exists.",
        "admin.store.name_prompt": "Enter store name:",
        "admin.store.set_default": "✅ {name} set as default store.",
        "admin.store.title": "🏪 <b>Store Management</b>",
        "admin.store.toggle_activate": "✅ Activate",
        "admin.store.toggle_deactivate": "❌ Deactivate",
        "admin.store.toggled": "✅ Store {name} is now {status}.",
        "admin.ticket.detail": "🎫 <b>Ticket #{code}</b>\nUser: {user_id}\nStatus: {status}\nPriority: {priority}\nSubject: {subject}\nCreated: {date}",
        "admin.ticket.empty": "No open tickets.",
        "admin.ticket.list": "Open/In Progress Tickets:",
        "admin.ticket.reply_prompt": "Reply to ticket #{code}:",
        "admin.ticket.resolved": "✅ Ticket #{code} resolved.",
        "admin.ticket.title": "🎫 <b>Support Tickets</b>",
        "btn.admin.reply_ticket": "💬 Reply",
        "btn.admin.resolve_ticket": "✅ Resolve",
        "btn.apply_coupon": "🎟 Apply Coupon",
        "btn.close_ticket": "✖ Close Ticket",
        "btn.create_ticket": "➕ New Ticket",
        "btn.create_ticket_for_order": "🎫 Support Ticket",
        "btn.invoice": "🧾 Receipt",
        "btn.my_tickets": "🎫 Support",
        "btn.reorder": "🔄 Reorder",
        "btn.reply_ticket": "💬 Reply",
        "btn.review_order": "⭐ Leave Review",
        "btn.search": "🔍 Search",
        "btn.skip_coupon": "⏭ Skip Coupon",
        "coupon.already_used": "❌ You already used this coupon.",
        "coupon.applied": "✅ Coupon applied! Discount: -{discount} {currency}",
        "coupon.enter_code": "🎟 Enter coupon code (or press Skip):",
        "coupon.expired": "❌ This coupon has expired.",
        "coupon.invalid": "❌ Invalid or expired coupon code.",
        "coupon.max_uses_reached": "❌ Coupon usage limit reached.",
        "coupon.min_order_not_met": "❌ Min order of {min_order} required.",
        "coupon.not_yet_valid": "❌ This coupon is not yet valid.",
        "invoice.not_available": "Receipt not available.",
        "reorder.success": "✅ Added {added} item(s) to cart. {skipped} item(s) unavailable.",
        "review.already_reviewed": "You have already reviewed this order.",
        "review.comment_prompt": "You rated {rating}/5 ⭐\n\nAdd a comment? Type or press Skip:",
        "review.detail": "⭐{rating}/5 — {comment}",
        "review.item_rating": "⭐ <b>{item}</b>: {avg:.1f}/5 ({count} reviews)",
        "review.no_reviews": "No reviews yet.",
        "review.prompt": "⭐ <b>Rate your order #{order_code}</b>\n\nSelect your rating:",
        "review.rate_1": "⭐",
        "review.rate_2": "⭐⭐",
        "review.rate_3": "⭐⭐⭐",
        "review.rate_4": "⭐⭐⭐⭐",
        "review.rate_5": "⭐⭐⭐⭐⭐",
        "review.skip_comment": "⏭ Skip",
        "review.thanks": "✅ Thank you for your review! ({rating}/5 ⭐)",
        "search.no_results": "❌ No products found. Try different keywords.",
        "search.prompt": "🔍 Enter product name or keyword to search:",
        "search.result_count": "Found {count} product(s):\n",
        "search.results_title": "🔍 <b>Search results for:</b> {query}\n\n",
        "ticket.admin_replied": "💬 Admin replied to ticket #{code}:\n{text}",
        "ticket.closed": "✅ Ticket closed.",
        "ticket.created": "✅ Ticket <b>#{code}</b> created!",
        "ticket.message_format": "<b>{role}</b> ({date}):\n{text}\n",
        "ticket.message_prompt": "Describe your issue:",
        "ticket.no_tickets": "No support tickets.",
        "ticket.reply_prompt": "Type your reply:",
        "ticket.reply_sent": "✅ Reply sent.",
        "ticket.resolved_notification": "✅ Ticket #{code} resolved!",
        "ticket.status.closed": "⚫ Closed",
        "ticket.status.in_progress": "🔵 In Progress",
        "ticket.status.open": "🟢 Open",
        "ticket.status.resolved": "✅ Resolved",
        "ticket.subject_prompt": "Enter the subject:",
        "ticket.title": "🎫 <b>Support Tickets</b>",
        "ticket.view_title": "🎫 <b>Ticket #{code}</b>\nStatus: {status}\nSubject: {subject}\nCreated: {date}",

        # === PDPA Privacy Policy ===
        "btn.privacy": "🔒 นโยบายความเป็นส่วนตัว",
        "privacy.notice": (
            "🔒 <b>นโยบายความเป็นส่วนตัว (PDPA)</b>\n\n"
            "เราปฏิบัติตาม พ.ร.บ. คุ้มครองข้อมูลส่วนบุคคล พ.ศ. 2562 (PDPA) อย่างเคร่งครัด\n\n"
            "<b>ข้อมูลที่เราเก็บ:</b>\n"
            "• ชื่อ-นามสกุล / เบอร์โทรศัพท์ / ที่อยู่จัดส่ง\n"
            "• รายละเอียดคำสั่งซื้อ / ประวัติการสั่ง\n"
            "• Telegram ID\n\n"
            "<b>วัตถุประสงค์หลัก:</b>\n"
            "• ดำเนินการสั่งซื้อและส่งอาหาร (จำเป็นตามสัญญา)\n"
            "• ป้องกันการฉ้อโกง / ยืนยันตัวตน\n"
            "• ส่งโปรโมชัน/ข่าวสาร — ต้องยินยอมแยกต่างหาก\n\n"
            "<b>ระยะเวลาการเก็บ:</b> จนกว่าคุณจะลบข้อมูล หรือ 2 ปีหลังคำสั่งซื้อสุดท้าย\n\n"
            "<b>เราแชร์ข้อมูลกับ:</b> ร้านอาหาร พนักงานส่งอาหาร ผู้ให้บริการชำระเงิน — เฉพาะที่จำเป็นสำหรับคำสั่งซื้อ "
            "ไม่ขายข้อมูลของคุณให้ใคร\n\n"
            "<b>สิทธิของคุณตาม PDPA:</b>\n"
            "• เข้าถึง / แก้ไข / ลบข้อมูล\n"
            "• ถอนความยินยอม (สำหรับการตลาด)\n"
            "• คัดค้านการประมวลผล / ขอให้โอนย้ายข้อมูล\n"
            "• ร้องเรียนต่อ PDPC\n\n"
            "<b>ผู้ควบคุมข้อมูล:</b> {company}\n"
            "ติดต่อ: {email}\n\n"
            "หากคุณใช้บอทต่อ แสดงว่าคุณได้รับทราบและยอมรับนโยบายนี้แล้ว"
        ),
        "privacy.btn_full_policy": "📄 อ่านนโยบายฉบับเต็ม",
        "privacy.btn_accept": "✅ ยอมรับและดำเนินการต่อ",
        "privacy.accepted": "✅ คุณยอมรับนโยบายความเป็นส่วนตัวแล้ว",
        "privacy.already_accepted": "✅ คุณยอมรับนโยบายความเป็นส่วนตัวแล้ว",
        "privacy.no_url": "ยังไม่ได้ตั้งค่าหน้านโยบายความเป็นส่วนตัวฉบับเต็ม",
    },

    "ar": {
        # === Common Buttons ===
        "btn.shop": "🏪 المتجر",
        "btn.rules": "📜 القواعد",
        "btn.profile": "👤 الملف الشخصي",
        "btn.support": "🆘 الدعم",
        "btn.channel": "ℹ قناة الأخبار",
        "btn.admin_menu": "🎛 لوحة الإدارة",
        "btn.back": "⬅️ رجوع",
        "btn.close": "✖ إغلاق",
        "btn.yes": "✅ نعم",
        "btn.no": "❌ لا",
        "btn.check_subscription": "🔄 التحقق من الاشتراك",
        "btn.admin.ban_user": "🚫 حظر المستخدم",
        "btn.admin.unban_user": "✅ إلغاء حظر المستخدم",

        # === Admin Buttons (user management shortcuts) ===
        "btn.admin.promote": "⬆️ ترقية إلى مشرف",
        "btn.admin.demote": "⬇️ إزالة صلاحيات المشرف",
        "btn.admin.add_user_bonus": "🎁 إضافة مكافأة إحالة",

        # === Titles / Generic Texts ===
        "menu.title": "⛩️ القائمة الرئيسية",
        "admin.goods.add.stock.error": "❌ خطأ في إضافة المخزون الأولي: {error}",
        "admin.goods.stock.add_success": "✅ تمت إضافة {quantity} وحدة إلى \"{item}\"",
        "admin.goods.stock.add_units": "➕ إضافة وحدات",
        "admin.goods.stock.current_status": "الحالة الحالية",
        "admin.goods.stock.error": "❌ خطأ في إدارة المخزون: {error}",
        "admin.goods.stock.insufficient": "❌ المخزون غير كافٍ. يتوفر {available} وحدة فقط.",
        "admin.goods.stock.invalid_quantity": "⚠️ كمية غير صالحة. أدخل رقمًا صحيحًا.",
        "admin.goods.stock.management_title": "إدارة المخزون: {item}",
        "admin.goods.stock.negative_quantity": "⚠️ لا يمكن أن تكون الكمية سالبة.",
        "admin.goods.stock.no_products": "❌ لا توجد منتجات في المتجر بعد",
        "admin.goods.stock.prompt.add_units": "أدخل عدد الوحدات المراد إضافتها:",
        "admin.goods.stock.prompt.item_name": "أدخل اسم المنتج لإدارة المخزون:",
        "admin.goods.stock.prompt.remove_units": "أدخل عدد الوحدات المراد إزالتها:",
        "admin.goods.stock.prompt.set_exact": "أدخل كمية المخزون المحددة:",
        "admin.goods.stock.redirect_message": "ℹ️ إدارة المخزون متاحة الآن من خلال قائمة \"إدارة المخزون\"",
        "admin.goods.stock.remove_success": "✅ تمت إزالة {quantity} وحدة من \"{item}\"",
        "admin.goods.stock.remove_units": "➖ إزالة وحدات",
        "admin.goods.stock.select_action": "اختر الإجراء",
        "admin.goods.stock.set_exact": "⚖️ تعيين الكمية المحددة",
        "admin.goods.stock.set_success": "✅ تم تعيين مخزون \"{item}\" إلى {quantity} وحدة",
        "admin.goods.stock.status_title": "📊 حالة المخزون:",
        "errors.invalid_item_name": "❌ اسم المنتج غير صالح",
        "errors.invalid_language": "لغة غير صالحة",
        "shop.error.brand_required": "يرجى اختيار العلامة التجارية أولاً",
        "shop.error.branch_unavailable": "الفرع غير متاح",
        "profile.caption": "👤 <b>الملف الشخصي</b> — <a href='tg://user?id={id}'>{name}</a>",
        "rules.not_set": "❌ لم تتم إضافة القواعد",
        "admin.users.cannot_ban_owner": "❌ لا يمكن حظر المالك",
        "admin.users.ban.success": "✅ تم حظر المستخدم {name} بنجاح",
        "admin.users.ban.failed": "❌ فشل حظر المستخدم",
        "admin.users.ban.notify": "⛔ تم حظرك من قبل المشرف",
        "admin.users.unban.success": "✅ تم إلغاء حظر المستخدم {name} بنجاح",
        "admin.users.unban.failed": "❌ فشل إلغاء حظر المستخدم",
        "admin.users.unban.notify": "✅ تم إلغاء حظرك من قبل المشرف",

        # === Profile ===
        "btn.referral": "🎲 نظام الإحالة",
        "btn.purchased": "🎁 المشتريات",
        "profile.referral_id": "👤 <b>الإحالة</b> — <code>{id}</code>",

        # === Subscription Flow ===
        "subscribe.prompt": "أولاً، اشترك في قناة الأخبار",

        # === Profile Info Lines ===
        "profile.id": "🆔 <b>ID</b> — <code>{id}</code>",
        "profile.bonus_balance": "💰 <b>مكافأة الإحالة:</b> ${bonus_balance}",
        "profile.purchased_count": "🎁 <b>المنتجات المشتراة</b> — {count} قطعة",
        "profile.registration_date": "🕢 <b>تاريخ التسجيل</b> — <code>{dt}</code>",

        # === Referral ===
        "referral.title": "💚 نظام الإحالة",
        "referral.count": "عدد الإحالات: {count}",
        "referral.description": (
            "📔 يتيح لك نظام الإحالة كسب المال دون أي استثمار. "
            "شارك رابط الإحالة الخاص بك وستحصل على {percent}% من "
            "عمليات إيداع المُحالين في رصيد البوت الخاص بك."
        ),
        "btn.view_referrals": "👥 إحالاتي",
        "btn.view_earnings": "💰 أرباحي",

        "referrals.list.title": "👥 إحالاتك:",
        "referrals.list.empty": "ليس لديك إحالات نشطة بعد",
        "referrals.item.format": "ID: {telegram_id} | الأرباح: {total_earned} {currency}",

        "referral.earnings.title": "💰 الأرباح من الإحالة <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>):",
        "referral.earnings.empty": "لا توجد أرباح من هذه الإحالة <code>{id}</code> (<a href='tg://user?id={id}'>{name}</a>) بعد",
        "referral.earning.format": "{amount} {currency} | {date} | (من {original_amount} {currency})",
        "referral.item.info": ("💰 رقم الربح: <code>{id}</code>\n"
                               "👤 الإحالة: <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>)\n"
                               "🔢 المبلغ: {amount} {currency}\n"
                               "🕘 التاريخ: <code>{date}</code>\n"
                               "💵 من إيداع بقيمة {original_amount} {currency}"),

        "referral.admin_bonus.info": ("💰 رقم الربح: <code>{id}</code>\n"
                                      "🎁 <b>مكافأة من المشرف</b>\n"
                                      "🔢 المبلغ: {amount} {currency}\n"
                                      "🕘 التاريخ: <code>{date}</code>"),

        "all.earnings.title": "💰 جميع أرباح الإحالة الخاصة بك:",
        "all.earnings.empty": "ليس لديك أرباح إحالة بعد",
        "all.earning.format.admin": "{amount} {currency} من المشرف | {date}",

        "referrals.stats.template": (
            "📊 إحصائيات نظام الإحالة:\n\n"
            "👥 الإحالات النشطة: {active_count}\n"
            "💰 إجمالي الأرباح: {total_earned} {currency}\n"
            "📈 إجمالي إيداعات الإحالات: {total_original} {currency}\n"
            "🔢 عدد الأرباح: {earnings_count}"
        ),

        # === Admin: Main Menu ===
        "admin.menu.main": "⛩️ قائمة الإدارة",
        "admin.menu.shop": "🛒 إدارة المتجر",
        "admin.menu.goods": "📦 إدارة المنتجات",
        "admin.menu.categories": "📂 إدارة الفئات",
        "admin.menu.users": "👥 إدارة المستخدمين",
        "admin.menu.broadcast": "📝 الرسائل الجماعية",
        "admin.menu.rights": "صلاحيات غير كافية",

        # === Admin: User Management ===
        "admin.users.prompt_enter_id": "👤 أدخل معرّف المستخدم لعرض / تعديل البيانات",
        "admin.users.invalid_id": "⚠️ يرجى إدخال معرّف مستخدم رقمي صالح.",
        "admin.users.profile_unavailable": "❌ الملف الشخصي غير متوفر (هذا المستخدم لم يكن موجودًا أبدًا)",
        "admin.users.not_found": "❌ لم يتم العثور على المستخدم",
        "admin.users.cannot_change_owner": "لا يمكنك تغيير دور المالك",
        "admin.users.referrals": "👥 <b>إحالات المستخدم</b> — {count}",
        "admin.users.btn.view_referrals": "👥 إحالات المستخدم",
        "admin.users.btn.view_earnings": "💰 أرباح المستخدم",
        "admin.users.role": "🎛 <b>الدور</b> — {role}",
        "admin.users.set_admin.success": "✅ تم تعيين الدور لـ {name}",
        "admin.users.set_admin.notify": "✅ تم منحك دور المشرف",
        "admin.users.remove_admin.success": "✅ تم إلغاء دور المشرف من {name}",
        "admin.users.remove_admin.notify": "❌ تم إلغاء دور المشرف الخاص بك",
        "admin.users.bonus.prompt": "أدخل مبلغ المكافأة بـ {currency}:",
        "admin.users.bonus.added": "✅ تم إضافة مكافأة إحالة بقيمة {amount} {currency} لـ {name}",
        "admin.users.bonus.added.notify": "🎁 تم إضافة مكافأة إحالة بقيمة {amount} {currency} لحسابك",
        "admin.users.bonus.invalid": "❌ مبلغ غير صالح. أدخل رقمًا من {min_amount} إلى {max_amount} {currency}.",

        # === Admin: Shop Management Menu ===
        "admin.shop.menu.title": "⛩️ إدارة المتجر",
        "admin.shop.menu.statistics": "📊 الإحصائيات",
        "admin.shop.menu.logs": "📁 عرض السجلات",
        "admin.shop.menu.admins": "👮 المشرفون",
        "admin.shop.menu.users": "👤 المستخدمون",

        # === Admin: Categories Management ===
        "admin.categories.menu.title": "⛩️ إدارة الفئات",
        "admin.categories.add": "➕ إضافة فئة",
        "admin.categories.rename": "✏️ إعادة تسمية فئة",
        "admin.categories.delete": "🗑 حذف فئة",
        "admin.categories.prompt.add": "أدخل اسم الفئة الجديدة:",
        "admin.categories.prompt.delete": "أدخل اسم الفئة المراد حذفها:",
        "admin.categories.prompt.rename.old": "أدخل اسم الفئة الحالية المراد إعادة تسميتها:",
        "admin.categories.prompt.rename.new": "أدخل اسم الفئة الجديد:",
        "admin.categories.add.exist": "❌ لم يتم إنشاء الفئة (موجودة بالفعل)",
        "admin.categories.add.success": "✅ تم إنشاء الفئة",
        "admin.categories.delete.not_found": "❌ لم يتم حذف الفئة (غير موجودة)",
        "admin.categories.delete.success": "✅ تم حذف الفئة",
        "admin.categories.rename.not_found": "❌ لا يمكن تحديث الفئة (غير موجودة)",
        "admin.categories.rename.exist": "❌ لا يمكن إعادة التسمية (توجد فئة بهذا الاسم بالفعل)",
        "admin.categories.rename.success": "✅ تمت إعادة تسمية الفئة \"{old}\" إلى \"{new}\"",

        # === Admin: Goods / Items Management (Add / List / Item Info) ===
        "admin.goods.add_position": "➕ إضافة منتج",
        "admin.goods.manage_stock": "➕ إضافة بضاعة إلى المنتج",
        "admin.goods.update_position": "📝 تعديل المنتج",
        "admin.goods.delete_position": "❌ حذف المنتج",
        "admin.goods.add.prompt.type": "اختر نوع المنتج:",
        "admin.goods.add.type.prepared": "🍳 يُحضَّر عند الطلب (طعام، مشروبات)",
        "admin.goods.add.type.product": "📦 منتج معبأ (ماء، وجبات خفيفة)",
        "admin.goods.add.prompt.name": "أدخل اسم المنتج",
        "admin.goods.add.name.exists": "❌ لا يمكن إنشاء المنتج (موجود بالفعل)",
        "admin.goods.add.prompt.description": "أدخل وصف المنتج:",
        "admin.goods.add.prompt.price": "أدخل سعر المنتج (رقم بـ {currency}):",
        "admin.goods.add.price.invalid": "⚠️ سعر غير صالح. يرجى إدخال رقم.",
        "admin.goods.add.prompt.category": "أدخل الفئة التي ينتمي إليها المنتج:",
        "admin.goods.add.category.not_found": "❌ لا يمكن إنشاء المنتج (الفئة المدخلة غير صالحة)",
        "admin.goods.position.not_found": "❌ لا توجد بضائع (هذا المنتج غير موجود)",
        "admin.goods.menu.title": "⛩️ قائمة إدارة المنتجات",
        "admin.goods.add.stock.prompt": "أدخل كمية البضائع المراد إضافتها",
        "admin.goods.add.stock.invalid": "⚠️ قيمة كمية غير صحيحة. يرجى إدخال رقم.",
        "admin.goods.add.stock.negative": "⚠️ قيمة كمية غير صحيحة. أدخل رقمًا موجبًا.",
        "admin.goods.add.result.created_with_stock": "✅ تم إنشاء المنتج {item_name}، وتمت إضافة {stock_quantity} إلى كمية البضائع.",

        # === Admin: Goods / Items Update Flow ===
        "admin.goods.update.position.invalid": "المنتج غير موجود.",
        "admin.goods.update.position.exists": "يوجد منتج بهذا الاسم بالفعل.",
        "admin.goods.update.prompt.name": "أدخل اسم المنتج",
        "admin.goods.update.not_exists": "❌ لا يمكن تحديث المنتج (غير موجود)",
        "admin.goods.update.prompt.new_name": "أدخل اسم المنتج الجديد:",
        "admin.goods.update.prompt.description": "أدخل وصف المنتج:",
        "admin.goods.update.success": "✅ تم تحديث المنتج",

        # === Admin: Goods / Items Delete Flow ===
        "admin.goods.delete.prompt.name": "أدخل اسم المنتج",
        "admin.goods.delete.position.not_found": "❌ لم يتم حذف المنتج (غير موجود)",
        "admin.goods.delete.position.success": "✅ تم حذف المنتج",

        # === Admin: Item Info ===
        "admin.goods.view_stock": "عرض المنتجات",

        # Admin Modifier Management (Card 8)
        "admin.goods.manage_modifiers": "🍳 الإضافات",
        "admin.goods.modifiers.prompt": "هل تريد إضافة خيارات تعديل (التوابل، الإضافات، إلخ)?",
        "admin.goods.modifiers.add_btn": "➕ إضافة خيارات",
        "admin.goods.modifiers.skip_btn": "⏭ تخطي",
        "admin.goods.modifiers.json_prompt": "الصق مخطط JSON للخيارات:",
        "admin.goods.modifiers.invalid_json": "❌ JSON غير صالح: {error}",
        "admin.goods.modifiers.select_item": "أدخل اسم المنتج لإعداد الخيارات:",
        "admin.goods.modifiers.edit_instructions": "اختر إجراء:",
        "admin.goods.modifiers.set_new": "📝 تعيين جديد",
        "admin.goods.modifiers.clear": "🗑 مسح الكل",

        # === Admin: Logs ===
        "admin.shop.logs.caption": "سجلات البوت",
        "admin.shop.logs.empty": "❗️ لا توجد سجلات بعد",

        # === Group Notifications ===
        "shop.group.new_upload": "مخزون جديد",
        "shop.group.item": "المنتج",
        "shop.group.stock": "الكمية",

        # === Admin: Statistics ===
        "admin.shop.stats.template": (
            "إحصائيات المتجر:\n"
            "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            "<b>◽المستخدمون</b>\n"
            "◾️المستخدمون في آخر 24 ساعة: {today_users}\n"
            "◾️إجمالي المشرفين: {admins}\n"
            "◾️إجمالي المستخدمين: {users}\n"
            "➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            "◽<b>متنوع</b>\n"
            "◾المنتجات: {items} قطعة\n"
            "◾العناصر: {goods} قطعة\n"
            "◾الفئات: {categories} قطعة\n"
        ),

        # === Admin: Lists & Broadcast ===
        "admin.shop.admins.title": "👮 مشرفو البوت:",
        "admin.shop.users.title": "مستخدمو البوت:",
        "broadcast.prompt": "أرسل رسالة للبث:",
        "broadcast.creating": "📤 بدء البث...\n👥 إجمالي المستخدمين: {ids}",
        "broadcast.progress": (
            "📤 البث جارٍ...\n\n\n"
            "📊 التقدم: {progress:.1f}%{n}"
            "✅ تم الإرسال: {sent}/{total}\n"
            "❌ الأخطاء: {failed}\n"
            "⏱ الوقت المنقضي: {time} ثانية"),
        "broadcast.done": (
            "✅ اكتمل البث!\n\n"
            "📊 الإحصائيات:📊\n"
            "👥 الإجمالي: {total}\n"
            "✅ تم التسليم: {sent}\n"
            "❌ لم يتم التسليم: {failed}\n"
            "🚫 حظر البوت: ~{blocked}\n"
            "📈 معدل النجاح: {success}%\n"
            "⏱ الوقت: {duration} ثانية"
        ),
        "broadcast.cancel": "❌ تم إلغاء البث.",
        "broadcast.warning": "لا يوجد بث نشط",

        # === Brand / Store Selection ===
        "shop.brands.title": "🏪 اختر مطعمًا",
        "shop.branches.title": "📍 اختر فرعًا",
        "shop.no_brands": "لا توجد مطاعم متاحة حاليًا.",
        "shop.brand_unavailable": "هذا المطعم غير متاح حاليًا.",

        # === Shop Browsing (Categories / Goods / Item Page) ===
        "shop.categories.title": "🏪 فئات المتجر",
        "shop.goods.choose": "🏪 اختر منتجًا",
        "shop.item.not_found": "المنتج غير موجود",
        "shop.item.title": "🏪 المنتج {name}",
        "shop.item.description": "الوصف: {description}",
        "shop.item.price": "السعر — {amount} {currency}",
        "shop.item.quantity_unlimited": "الكمية — غير محدودة",
        "shop.item.quantity_left": "الكمية — {count} قطعة",
        "shop.item.quantity_detailed": "📦 إجمالي المخزون: {total} قطعة\n🔒 محجوز: {reserved} قطعة\n✅ متاح للطلب: {available} قطعة",

        # === Purchases ===
        "purchases.title": "المشتريات:",
        "purchases.pagination.invalid": "بيانات التصفح غير صالحة",
        "purchases.item.not_found": "لم يتم العثور على عملية الشراء",
        "purchases.item.name": "<b>🧾 المنتج</b>: <code>{name}</code>",
        "purchases.item.price": "<b>💵 السعر</b>: <code>{amount}</code> {currency}",
        "purchases.item.datetime": "<b>🕒 تاريخ الشراء</b>: <code>{dt}</code>",
        "purchases.item.unique_id": "<b>🧾 المعرّف الفريد</b>: <code>{uid}</code>",
        "purchases.item.value": "<b>🔑 القيمة</b>:\n<code>{value}</code>",

        # === Middleware ===
        "middleware.ban": "⏳ أنت محظور مؤقتًا. انتظر {time} ثانية.",
        "middleware.above_limits": "⚠️ طلبات كثيرة جدًا! أنت محظور مؤقتًا.",
        "middleware.waiting": "⏳ انتظر {time} ثانية قبل الإجراء التالي.",
        "middleware.security.session_outdated": "⚠️ انتهت صلاحية الجلسة. يرجى البدء من جديد.",
        "middleware.security.invalid_data": "❌ بيانات غير صالحة",
        "middleware.security.blocked": "❌ تم حظر الوصول",
        "middleware.security.not_admin": "⛔ صلاحيات غير كافية",
        "middleware.security.banned": "⛔ <b>تم حظرك</b>\n\nالسبب: {reason}",
        "middleware.security.banned_no_reason": "⛔ <b>تم حظرك</b>\n\nيرجى التواصل مع المشرف للحصول على مزيد من المعلومات.",
        "middleware.security.rate_limit": "⚠️ طلبات كثيرة جدًا! يرجى الانتظار قليلاً.",

        # === Errors ===
        "errors.not_subscribed": "أنت غير مشترك",
        "errors.pagination_invalid": "بيانات التصفح غير صالحة",
        "errors.invalid_data": "❌ بيانات غير صالحة",
        "errors.channel.telegram_not_found": "لا أستطيع الكتابة في القناة. أضفني كمشرف في قناة التحميلات @{channel} مع صلاحية نشر الرسائل.",
        "errors.channel.telegram_forbidden_error": "القناة غير موجودة. تحقق من اسم مستخدم القناة للتحميلات @{channel}.",
        "errors.channel.telegram_bad_request": "فشل الإرسال إلى قناة التحميلات: {e}",

        # === Orders ===
        "order.payment_method.choose": "💳 اختر طريقة الدفع:",
        "order.payment_method.bitcoin": "💳 Bitcoin",
        "order.payment_method.litecoin": "💳 Litecoin",
        "order.payment_method.solana": "💳 SOL",
        "order.payment_method.usdt_sol": "💳 USDT (Solana)",
        "order.payment_method.cash": "💵 الدفع عند الاستلام",
        "order.status.notify_order_confirmed": (
            "تم تأكيد الطلب {order_code}! 🎉\n\n"
            "سيتم تسليم طلبك في: {delivery_time}\n\n"
            "المنتجات:\n{items}\n\n"
            "الإجمالي: {total}\n\n"
            "انتظر التسليم!"
        ),
        "order.status.notify_order_delivered": (
            "تم تسليم الطلب {order_code}! ✅\n\n"
            "شكرًا لشرائك! نتطلع لرؤيتك مجددًا! 🙏"
        ),
        "order.status.notify_order_modified": (
            "تم تعديل الطلب {order_code} من قبل المشرف 📝\n\n"
            "التغييرات:\n{changes}\n\n"
            "الإجمالي الجديد: {total}"
        ),

        # === Additional Common Buttons ===
        "btn.cart": "🛒 سلة المشتريات",
        "btn.my_orders": "📦 طلباتي",
        "btn.reference_codes": "🔑 رموز الإحالة",
        "btn.settings": "⚙️ الإعدادات",
        "btn.referral_bonus_percent": "💰 نسبة مكافأة الإحالة",
        "btn.order_timeout": "⏱️ مهلة الطلب",
        "btn.timezone": "🌍 المنطقة الزمنية",
        "btn.promptpay_account": "💳 حساب PromptPay",
        "btn.currency": "💱 العملة",
        "btn.skip": "⏭️ تخطي",
        "btn.use_saved_info": "✅ استخدام المعلومات المحفوظة",
        "btn.update_info": "✏️ تحديث المعلومات",
        "btn.back_to_cart": "◀️ العودة إلى السلة",
        "btn.clear_cart": "🗑️ تفريغ السلة",
        "btn.proceed_checkout": "💳 متابعة الدفع",
        "btn.remove_item": "❌ إزالة {item_name}",
        "btn.use_all_bonus": "استخدام الكل ${amount}",
        "btn.apply_bonus_yes": "✅ نعم، تطبيق المكافأة",
        "btn.apply_bonus_no": "❌ لا، حفظها لاحقًا",
        "btn.cancel": "❌ إلغاء",
        "btn.add_to_cart": "🛒 إضافة إلى السلة",

        # === Cart Management ===
        "cart.add_success": "✅ تمت إضافة {item_name} إلى السلة!",
        "cart.add_error": "❌ {message}",
        "cart.empty": "🛒 سلتك فارغة.\n\nتصفح المتجر لإضافة منتجات!",
        "cart.title": "🛒 <b>سلة مشترياتك</b>\n\n",
        "cart.removed_success": "تمت إزالة المنتج من السلة",
        "cart.cleared_success": "✅ تم تفريغ السلة بنجاح!",
        "cart.empty_alert": "السلة فارغة!",
        "cart.summary_title": "📦 <b>ملخص الطلب</b>\n\n",
        "cart.saved_delivery_info": "معلومات التوصيل المحفوظة:\n\n",
        "cart.delivery_address": "📍 العنوان: {address}\n",
        "cart.delivery_phone": "📞 الهاتف: {phone}\n",
        "cart.delivery_note": "📝 ملاحظة: {note}\n",
        "cart.use_info_question": "\n\nهل تريد استخدام هذه المعلومات أم تحديثها؟",
        "cart.no_saved_info": "❌ لم يتم العثور على معلومات توصيل محفوظة. يرجى الإدخال يدويًا.",

        # === Order/Delivery Flow ===
        "order.delivery.address_prompt": "📍 يرجى إدخال عنوان التوصيل:",
        "order.delivery.address_invalid": "❌ يرجى تقديم عنوان توصيل صالح (5 أحرف على الأقل).",
        "order.delivery.phone_prompt": "📞 يرجى إدخال رقم هاتفك (مع رمز الدولة):",
        "order.delivery.phone_invalid": "❌ يرجى تقديم رقم هاتف صالح (8 أرقام على الأقل).",
        "order.delivery.note_prompt": "📝 هل لديك تعليمات توصيل خاصة؟ (اختياري)\n\nيمكنك تخطي ذلك بالنقر على الزر أدناه.",
        "order.delivery.info_save_error": "❌ خطأ في حفظ معلومات التوصيل. يرجى المحاولة مرة أخرى.",

        # Location Method Choice
        "order.delivery.location_method_prompt": "📍 كيف تريد مشاركة موقع التوصيل؟\n\nاختر أحد الخيارات أدناه:",
        "btn.location_method.gps": "📡 إرسال GPS عبر Telegram",
        "btn.location_method.live_gps": "📍 مشاركة الموقع المباشر",
        "btn.location_method.google_link": "🗺 مشاركة رابط Google Maps",
        "btn.location_method.type_address": "✍️ كتابة العنوان",
        "order.delivery.gps_prompt": "📍 انقر على الزر أدناه لمشاركة موقعك:",
        "order.delivery.gps_hint": "📍 يرجى استخدام الزر أدناه لمشاركة موقع GPS، أو انقر 'رجوع' لاختيار طريقة أخرى.",
        "order.delivery.live_gps_prompt": "📍 لمشاركة موقعك المباشر:\n\n1. انقر على أيقونة المرفقات 📎 أدناه\n2. اختر 'الموقع'\n3. انقر 'مشاركة الموقع المباشر'\n4. اختر المدة\n\nسيتمكن السائق من رؤية موقعك في الوقت الفعلي!",
        "order.delivery.live_gps_saved": "✅ تم استلام الموقع المباشر! سيتمكن السائق من تتبع موقعك.",
        "order.delivery.live_gps_hint": "📍 يرجى مشاركة موقعك المباشر عبر قائمة المرفقات (📎 ← الموقع ← مشاركة الموقع المباشر).",
        "order.delivery.google_link_prompt": "🗺 الصق رابط Google Maps بموقعك.\n\nافتح Google Maps، ابحث عن الموقع، انقر 'مشاركة' وانسخ الرابط هنا.",
        "order.delivery.google_link_invalid": "❌ لم يتم التعرف على رابط Google Maps. تأكد أنه يبدأ بـ google.com/maps أو goo.gl/maps.",
        "order.delivery.address_confirm_prompt": "📍 عنوانك:\n<b>{address}</b>\n\n🔗 <a href=\"{maps_link}\">عرض على الخريطة</a>\n\nهل هذا صحيح؟",
        "btn.address_confirm_yes": "✅ نعم، صحيح",
        "btn.address_confirm_retry": "✏️ لا، أعد الإدخال",

        # GPS Location (Card 2)
        "order.delivery.location_prompt": "📍 هل تريد مشاركة موقع GPS لتوصيل أكثر دقة؟\n\nانقر على الزر أدناه أو تخطَّ هذه الخطوة.",
        "order.delivery.location_saved": "✅ تم حفظ الموقع!",
        "btn.share_location": "📍 مشاركة الموقع",
        "btn.skip_location": "⏭ تخطي",

        # Delivery Type (Card 3)
        "order.delivery.type_prompt": "🚚 اختر نوع التوصيل:",
        "btn.delivery.door": "🚪 توصيل إلى الباب",
        "btn.delivery.dead_drop": "📦 ترك في الموقع",
        "btn.delivery.pickup": "🏪 استلام ذاتي",
        "order.delivery.drop_instructions_prompt": "📝 صف مكان ترك طلبك (مثلاً، 'مع حارس الأمن في الردهة'، 'تحت السجادة عند الغرفة 405'):",
        "order.delivery.drop_gps_prompt": "📍 شارك موقع GPS لنقطة التسليم بالضغط على الزر أدناه:",
        "btn.share_drop_location": "📍 مشاركة الموقع",
        "order.delivery.drop_gps_saved": "✅ تم حفظ موقع GPS!",
        "order.delivery.drop_media_prompt": "📸 أرسل صور أو فيديوهات لموقع التسليم (يمكنك إرسال عدة ملفات). اضغط 'تم' عند الانتهاء:",
        "order.delivery.drop_media_saved": "✅ تم حفظ {count} ملف(ات). أرسل المزيد أو اضغط 'تم'.",
        "btn.drop_media_done": "✅ تم",
        "btn.skip_drop_media": "⏭ تخطي",
        "order.delivery.drop_photo_prompt": "📸 هل تريد إرسال صورة لموقع التسليم؟ (اختياري)",
        "order.delivery.drop_photo_saved": "✅ تم حفظ صورة موقع التسليم!",
        "btn.skip_drop_photo": "⏭ تخطي الصورة",

        # PromptPay (Card 1)
        "order.payment_method.promptpay": "💳 PromptPay QR",
        "order.payment.promptpay.title": "💳 <b>الدفع عبر PromptPay</b>",
        "order.payment.promptpay.scan": "📱 امسح رمز QR للدفع:",
        "order.payment.promptpay.upload_receipt": "📸 بعد الدفع، يرجى تحميل إيصال الدفع:",
        "order.payment.promptpay.receipt_received": "✅ تم استلام الإيصال! في انتظار التحقق من المشرف.",
        "order.payment.promptpay.receipt_invalid": "❌ يرجى إرسال صورة لإيصال الدفع.",
        "order.payment.promptpay.slip_verified": "✅ تم التحقق من الدفع تلقائيًا! تم تأكيد طلبك.",
        "admin.order.verify_payment": "✅ التحقق من الدفع",
        "admin.order.payment_verified": "✅ تم التحقق من الدفع",

        # Delivery Chat (Card 13)
        "order.delivery.chat_unavailable": "❌ الدردشة مع السائق غير متاحة. مجموعة السائقين غير مهيأة.",
        "order.delivery.chat_started": "💬 يمكنك مراسلة السائق. أرسل نصًا أو صورة أو موقعًا.\n\nأرسل /endchat لإنهاء الدردشة.",
        "order.delivery.live_location_shared": "📍 السائق يشارك الموقع المباشر! يمكنك تتبع التوصيل.",
        "order.delivery.chat_no_active_delivery": "❌ ليس لديك توصيلات نشطة للدردشة.",
        "order.delivery.chat_ended": "✅ تم إنهاء الدردشة مع السائق.",
        "order.delivery.chat_message_sent": "✅ تم إرسال الرسالة إلى السائق.",
        "order.delivery.driver_no_active_order": "⚠️ لا يوجد طلب نشط لإعادة توجيه هذه الرسالة.",
        "btn.chat_with_driver": "💬 الدردشة مع السائق",

        # GPS tracking & chat session (Card 15)
        "delivery.gps.prompt": "📍 طلبك {order_code} في الطريق!\n\nساعد السائق في العثور عليك بسرعة — شارك موقعك:",
        "delivery.gps.btn_static": "📍 إرسال الموقع",
        "delivery.gps.btn_live": "📡 موقع مباشر",
        "delivery.gps.btn_skip": "⏭ تخطي",
        "delivery.gps.static_sent": "✅ تم إرسال موقعك إلى السائق.",
        "delivery.gps.live_started": "📡 تم تفعيل الموقع المباشر! يمكن للسائق تتبعك في الوقت الفعلي.",
        "delivery.gps.skipped": "⏭ تم تخطي الموقع. سيستخدم السائق العنوان من طلبك.",
        "delivery.chat.session_closed": "⏹ انتهت جلسة الدردشة. تواصل مع الدعم للمساعدة.",
        "delivery.chat.post_delivery_open": "✅ تم التوصيل! الدردشة تبقى مفتوحة لمدة {minutes} دقيقة إضافية.",
        "delivery.chat.post_delivery_closed": "⏹ انتهت فترة الدردشة بعد التوصيل.",
        "btn.end_chat": "❌ إنهاء الدردشة",

        # === Bonus/Referral Application ===
        "order.bonus.available": "💰 <b>لديك ${bonus_balance} في مكافآت الإحالة!</b>\n\n",
        "order.bonus.apply_question": "هل تريد تطبيق مكافأة الإحالة على هذا الطلب؟",
        "order.bonus.amount_positive_error": "❌ يرجى إدخال مبلغ موجب.",
        "order.bonus.amount_too_high": "❌ المبلغ كبير جدًا. الحد الأقصى المطبق: ${max_applicable}\nيرجى إدخال مبلغ صالح:",
        "order.bonus.invalid_amount": "❌ مبلغ غير صالح. يرجى إدخال رقم (مثلاً، 5.50):",
        "order.bonus.insufficient": "❌ رصيد المكافأة غير كافٍ. يرجى المحاولة مرة أخرى.",
        "order.bonus.enter_amount": "أدخل مبلغ المكافأة الذي تريد تطبيقه (الحد الأقصى ${max_applicable}):\n\nأو استخدم جميع المكافآت المتاحة بالنقر على الزر أدناه.",

        # === Payment Instructions ===
        "order.payment.system_unavailable": "❌ <b>نظام الدفع غير متاح مؤقتًا</b>\n\nلا تتوفر عناوين Bitcoin. يرجى التواصل مع الدعم.",
        "order.payment.customer_not_found": "❌ لم يتم العثور على معلومات العميل. يرجى المحاولة مرة أخرى.",
        "order.payment.creation_error": "❌ خطأ في إنشاء الطلبات. يرجى المحاولة مرة أخرى أو التواصل مع الدعم.",

        # === Order Summary/Total ===
        "order.summary.title": "📦 <b>ملخص الطلب</b>\n\n",
        "order.summary.cart_total": "إجمالي السلة: ${cart_total}",
        "order.summary.bonus_applied": "المكافأة المطبقة: -${bonus_applied}",
        "order.summary.final_amount": "المبلغ النهائي: ${final_amount}",

        # === Inventory/Reservation ===
        "order.inventory.unable_to_reserve": "❌ <b>تعذر حجز المنتجات</b>\n\nالمنتجات التالية غير متوفرة بالكميات المطلوبة:\n\n{unavailable_items}\n\nيرجى تعديل سلتك والمحاولة مرة أخرى.",

        # === My Orders View ===
        "myorders.title": "📦 <b>طلباتي</b>\n\n",
        "myorders.total": "إجمالي الطلبات: {count}",
        "myorders.active": "⏳ الطلبات النشطة: {count}",
        "myorders.delivered": "✅ تم التسليم: {count}",
        "myorders.select_category": "اختر فئة لعرض الطلبات:",
        "myorders.active_orders": "⏳ الطلبات النشطة",
        "myorders.delivered_orders": "✅ الطلبات المسلّمة",
        "myorders.all_orders": "📋 جميع الطلبات",
        "myorders.no_orders_yet": "لم تقم بأي طلبات بعد.\n\nتصفح المتجر لبدء التسوق!",
        "myorders.browse_shop": "🛍️ الذهاب إلى المتجر",
        "myorders.back": "◀️ رجوع",
        "myorders.all_title": "📋 جميع الطلبات",
        "myorders.active_title": "⏳ الطلبات النشطة",
        "myorders.delivered_title": "✅ الطلبات المسلّمة",
        "myorders.invalid_filter": "فلتر غير صالح",
        "myorders.not_found": "لم يتم العثور على طلبات.",
        "myorders.back_to_menu": "◀️ العودة إلى قائمة الطلبات",
        "myorders.select_details": "اختر طلبًا لعرض التفاصيل:",
        "myorders.order_not_found": "لم يتم العثور على الطلب",

        # === Order Details Display ===
        "myorders.detail.title": "📦 <b>تفاصيل الطلب #{order_code}</b>\n\n",
        "myorders.detail.status": "📊 <b>الحالة:</b> {status}\n",
        "myorders.detail.subtotal": "💵 <b>المجموع الفرعي:</b> ${subtotal}\n",
        "myorders.detail.bonus_applied": "🎁 <b>المكافأة المطبقة:</b> ${bonus}\n",
        "myorders.detail.final_price": "💰 <b>السعر النهائي:</b> ${total}\n",
        "myorders.detail.total_price": "💰 <b>السعر الإجمالي:</b> ${total}\n",
        "myorders.detail.payment_method": "💳 <b>طريقة الدفع:</b> {method}\n",
        "myorders.detail.ordered": "📅 <b>تاريخ الطلب:</b> {date}\n",
        "myorders.detail.delivery_time": "🚚 <b>التسليم المجدول:</b> {time}\n",
        "myorders.detail.completed": "✅ <b>مكتمل:</b> {date}\n",
        "myorders.detail.items": "\n📦 <b>المنتجات:</b>\n{items}\n",
        "myorders.detail.delivery_info": "\n📍 <b>معلومات التوصيل:</b>\n{address}\n{phone}\n{note}",

        # === Help System ===
        "help.prompt": "📧 <b>هل تحتاج مساعدة؟</b>\n\n",
        "help.describe_issue": "يرجى وصف مشكلتك أو سؤالك، وسيتم إرساله مباشرة إلى المشرف.\n\nاكتب رسالتك أدناه:",
        "help.admin_not_configured": "❌ عذرًا، لم يتم تهيئة جهة اتصال المشرف. يرجى المحاولة لاحقًا.",
        "help.admin_notification_title": "📧 <b>طلب مساعدة جديد</b>\n\n",
        "help.admin_notification_from": "<b>من:</b> @{username} (ID: {user_id})\n",
        "help.admin_notification_message": "<b>الرسالة:</b>\n{message}",
        "help.sent_success": "✅ {auto_message}",
        "help.sent_error": "❌ فشل إرسال الرسالة إلى المشرف: {error}\n\nيرجى المحاولة لاحقًا.",
        "help.cancelled": "تم إلغاء طلب المساعدة.",

        # === Admin Order Notifications ===
        "admin.order.action_required_title": "⏳ <b>إجراء مطلوب:</b>",
        "admin.order.address_label": "العنوان: {address}",
        "admin.order.amount_to_collect_label": "<b>المبلغ المطلوب تحصيله: ${amount} {currency}</b>",
        "admin.order.amount_to_receive_label": "<b>المبلغ المطلوب استلامه: ${amount} {currency}</b>",
        "admin.order.awaiting_payment_status": "⏳ في انتظار تأكيد الدفع...",
        "admin.order.bitcoin_address_label": "عنوان Bitcoin: <code>{address}</code>",
        "admin.order.bonus_applied_label": "المكافأة المطبقة: <b>-${amount}</b>",
        "admin.order.customer_label": "العميل: {username} (ID: {id})",
        "admin.order.delivery_info_title": "<b>معلومات التوصيل:</b>",
        "admin.order.items_title": "<b>المنتجات:</b>",
        "admin.order.new_bitcoin_order": "🔔 <b>طلب Bitcoin جديد مستلم</b>",
        "admin.order.new_cash_order": "🔔 <b>طلب نقدي جديد مستلم</b> 💵",
        "admin.order.note_label": "ملاحظة: {note}",
        "admin.order.order_label": "الطلب: <b>{code}</b>",
        "admin.order.payment_cash": "الدفع عند الاستلام",
        "admin.order.payment_method_label": "طريقة الدفع: <b>{method}</b>",
        "admin.order.phone_label": "الهاتف: {phone}",
        "admin.order.subtotal_label": "المجموع الفرعي: <b>${amount} {currency}</b>",
        "admin.order.use_cli_confirm": "استخدم CLI لتأكيد الطلب وتحديد وقت التسليم:\n<code>python bot_cli.py order --order-code {code} --status-confirmed --delivery-time \"YYYY-MM-DD HH:MM\"</code>",
        "btn.admin.back_to_panel": "🔙 العودة إلى لوحة الإدارة",
        "btn.admin.create_refcode": "➕ إنشاء رمز إحالة",
        "btn.admin.list_refcodes": "📋 قائمة جميع الرموز",
        "btn.back_to_orders": "◀️ العودة إلى الطلبات",
        "btn.create_reference_code": "➕ إنشاء رمز إحالة",
        "btn.my_reference_codes": "🔑 رموز الإحالة الخاصة بي",
        "btn.need_help": "❓ هل تحتاج مساعدة؟",
        "cart.item.price_format": "  السعر: {price} {currency} × {quantity}",
        "cart.item.subtotal_format": "  المجموع الفرعي: {subtotal} {currency}",
        "cart.item.modifiers": "  التعديلات: {modifiers}",
        "cart.total_format": "<b>الإجمالي: {total} {currency}</b>",
        "cart.add_cancelled": "تم إلغاء الإضافة",
        "modifier.select_title": "اختر {label}:",
        "modifier.selected": "تم الاختيار: {choice}",
        "modifier.required": "(مطلوب)",
        "modifier.optional": "(اختياري)",
        "modifier.done": "تم",
        "modifier.price_extra": "+{price}",
        "modifier.cancelled": "تم إلغاء اختيار التعديلات.",
        "help.pending_order.contact_support": "استخدم الأمر /help للتواصل مع الدعم.",
        "help.pending_order.issues_title": "<b>هل تواجه مشاكل؟</b>",
        "help.pending_order.status": "طلبك في انتظار الدفع حاليًا.",
        "help.pending_order.step1": "1. أرسل المبلغ المحدد إلى عنوان Bitcoin المعروض",
        "help.pending_order.step2": "2. انتظر تأكيد البلوكتشين (عادةً 10-60 دقيقة)",
        "help.pending_order.step3": "3. سيؤكد المشرف دفعتك ويحدد وقت التسليم",
        "help.pending_order.step4": "4. سيتم تسليم بضائعك بواسطة المندوب.",
        "help.pending_order.title": "❓ <b>هل تحتاج مساعدة في طلبك؟</b>",
        "help.pending_order.what_to_do_title": "<b>ما يجب فعله:</b>",
        "myorders.detail.bitcoin_address_label": "عنوان Bitcoin:",
        "myorders.detail.bitcoin_admin_confirm": "بعد الدفع، سيؤكد المشرف طلبك.",
        "myorders.detail.bitcoin_send_instruction": "⚠️ يرجى إرسال <b>{amount} {currency}</b> من Bitcoin إلى هذا العنوان.",
        "myorders.detail.cash_awaiting_confirm": "طلبك في انتظار تأكيد المشرف.",
        "myorders.detail.cash_payment_courier": "سيتم الدفع للمندوب عند التسليم.",
        "myorders.detail.cash_title": "💵 الدفع عند الاستلام",
        "myorders.detail.cash_will_notify": "سيتم إعلامك عندما يتم تأكيد طلبك وتحديد وقت التسليم.",
        "myorders.detail.confirmed_title": "✅ <b>تم تأكيد الطلب!</b>",
        "myorders.detail.delivered_thanks_message": "شكرًا لشرائك! نأمل أن نراك مجددًا! 🙏",
        "myorders.detail.delivered_title": "📦 <b>تم تسليم الطلب!</b>",
        "myorders.detail.payment_info_title": "<b>معلومات الدفع:</b>",
        "myorders.detail.preparing_message": "يتم تحضير طلبك للتسليم.",
        "myorders.detail.scheduled_delivery_label": "التسليم المجدول: <b>{time}</b>",
        "myorders.order_summary_format": "{status_emoji} {code} - {items_count} منتجات - {total} {currency}",
        "order.bonus.available_label": "المكافأة المتاحة: <b>${amount}</b>",
        "order.bonus.choose_amount_hint": "يمكنك اختيار المبلغ المراد استخدامه (حتى ${max_amount})",
        "order.bonus.enter_amount_title": "💵 <b>أدخل مبلغ المكافأة للتطبيق</b>",
        "order.bonus.max_applicable_label": "الحد الأقصى المطبق: <b>${amount}</b>",
        "order.bonus.order_total_label": "إجمالي الطلب: <b>${amount} {currency}</b>",
        "order.info.view_status_hint": "💡 يمكنك عرض حالة طلبك في أي وقت باستخدام الأمر /orders.",
        "order.payment.bitcoin.address_title": "<b>عنوان الدفع بـ Bitcoin:</b>",
        "order.payment.bitcoin.admin_confirm": "• بعد الدفع، سيؤكد المشرف طلبك",
        "order.payment.bitcoin.delivery_title": "<b>التوصيل:</b>",
        "order.payment.bitcoin.important_title": "⚠️ <b>مهم:</b>",
        "order.payment.bitcoin.items_title": "<b>المنتجات:</b>",
        "order.payment.bitcoin.need_help": "هل تحتاج مساعدة؟ استخدم /help للتواصل مع الدعم.",
        "order.payment.bitcoin.one_time_address": "• هذا العنوان للاستخدام مرة واحدة فقط",
        "order.payment.bitcoin.order_code": "الطلب: <b>{code}</b>",
        "order.payment.bitcoin.send_exact": "• أرسل المبلغ المحدد المعروض أعلاه",
        "order.payment.bitcoin.title": "💳 <b>تعليمات الدفع بـ Bitcoin</b>",
        "order.payment.bitcoin.total_amount": "المبلغ الإجمالي: <b>{amount} {currency}</b>",

        # Crypto payment (Card 18) — generic strings for all coins
        "crypto.payment.title": "💳 <b>{coin_name} Payment</b>",
        "crypto.payment.order_code": "Order: <b>{code}</b>",
        "crypto.payment.total_fiat": "Total: <b>{amount} {currency}</b>",
        "crypto.payment.rate": "Rate: 1 {coin} = {rate} {currency}",
        "crypto.payment.amount_due": "Amount due: <b>{crypto_amount} {coin}</b>",
        "crypto.payment.address": "<b>Send to this address:</b>\n<code>{address}</code>",
        "crypto.payment.send_exact": "• Send EXACTLY this amount",
        "crypto.payment.one_time": "• This address is for ONE-TIME use",
        "crypto.payment.auto_confirm": "• Your order will be automatically confirmed once the payment is detected on-chain.",
        "crypto.payment.waiting": "⏳ Waiting for payment...\nThis address expires in {timeout} minutes.",
        "crypto.payment.no_address": "❌ No {coin} addresses available. Please contact support or choose another payment method.",
        "crypto.payment_detected": (
            "✅ <b>Payment detected!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "⏳ Waiting for confirmations..."
        ),
        "crypto.payment_confirmed": (
            "✅ <b>Payment confirmed!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "Your order is now being processed."
        ),
        "crypto.payment_expired": "⏰ Payment window for your {coin} order ({order_code}) has expired. Please place a new order.",

        "order.payment.cash.admin_contact": "سيتواصل معك المشرف قريبًا.",
        "order.payment.cash.after_confirm": "بعد التأكيد، سيتم إعلامك بوقت التسليم.",
        "order.payment.cash.created": "تم إنشاء طلبك {code} وهو في انتظار تأكيد المشرف.",
        "order.payment.cash.important": "⏳ <b>مهم:</b> الطلب محجوز لفترة محدودة.",
        "order.payment.cash.items_title": "المنتجات:",
        "order.payment.cash.payment_to_courier": "سيتم الدفع للمندوب عند التسليم.",
        "order.payment.cash.title": "💵 <b>الدفع عند الاستلام</b>",
        "order.payment.cash.total": "الإجمالي: {amount}",
        "order.payment.error_general": "❌ خطأ في إنشاء الطلب. يرجى المحاولة مرة أخرى أو التواصل مع الدعم.",
        "order.summary.total_label": "<b>الإجمالي: {amount} {currency}</b>",
        "order.payment.bonus_applied_label": "المكافأة المطبقة: <b>-{amount} {currency}</b>",
        "order.payment.cash.amount_with_bonus": "<b>المبلغ المطلوب دفعه عند التسليم: {amount} {currency}</b>",
        "order.payment.cash.total_label": "<b>إجمالي المبلغ عند التسليم: {amount} {currency}</b>",
        "order.payment.final_amount_label": "<b>المبلغ النهائي للدفع: {amount} {currency}</b>",
        "order.payment.order_label": "📋 <b>الطلب: {code}</b>",
        "order.payment.subtotal_label": "المجموع الفرعي: <b>{amount} {currency}</b>",
        "order.payment.total_amount_label": "<b>المبلغ الإجمالي: {amount} {currency}</b>",

        # === Card 9: Kitchen & Delivery Workflow ===
        "admin.menu.orders": "📋 الطلبات",
        "admin.orders.list_title": "📋 <b>الطلبات</b>",
        "admin.orders.empty": "لم يتم العثور على طلبات",
        "admin.orders.filter_status": "تصفية حسب الحالة",
        "admin.orders.filter_all": "📋 جميع الطلبات",
        "admin.orders.filter_active": "🔄 النشطة",
        "admin.orders.detail": (
            "📋 <b>الطلب #{order_id}</b> ({order_code})\n"
            "👤 المشتري: {buyer_id}\n"
            "💰 الإجمالي: {total}\n"
            "📦 الحالة: {status}\n"
            "📅 تاريخ الإنشاء: {created_at}\n"
            "📍 العنوان: {address}\n"
            "📞 الهاتف: {phone}"
        ),
        "admin.orders.status_changed": "تم تغيير حالة الطلب #{order_id} إلى <b>{new_status}</b>",
        "admin.orders.invalid_transition": "لا يمكن تغيير الحالة من {current} إلى {new}",
        "kitchen.order_received": (
            "🍳 <b>طلب جديد #{order_id}</b> ({order_code})\n\n"
            "{items}\n\n"
            "💰 الإجمالي: {total}\n"
            "📍 العنوان: {address}\n"
            "📞 الهاتف: {phone}"
        ),
        "rider.order_ready": (
            "🚗 <b>الطلب جاهز #{order_id}</b> ({order_code})\n\n"
            "💰 الإجمالي: {total}\n"
            "📍 العنوان: {address}\n"
            "📞 الهاتف: {phone}"
        ),
        "order.status.preparing": "🍳 طلبك #{order_code} قيد التحضير",
        "order.status.ready": "✅ طلبك #{order_code} جاهز للاستلام",
        "order.status.out_for_delivery": "🚗 طلبك #{order_code} في الطريق",
        "order.status.delivered_notify": "📦 تم تسليم طلبك #{order_code}",
        "kitchen.btn.start_preparing": "🍳 بدء التحضير",
        "kitchen.btn.mark_ready": "✅ جاهز",
        "rider.btn.picked_up": "📦 تم الاستلام",
        "rider.btn.delivered": "✅ تم التسليم",

        # Delivery Photo Proof (Card 4)
        "delivery.photo.required": "مطلوب صورة للتسليم في نقطة التسليم",
        "delivery.photo.upload_prompt": "يرجى تحميل صورة التسليم",
        "delivery.photo.received": "تم حفظ صورة التسليم",
        "delivery.photo.sent_to_customer": "تم إرسال صورة التسليم للعميل",
        "delivery.photo.customer_notification": "تم تسليم طلبك {order_code}! إليك صورة التأكيد.",

        # === New Feature Strings ===

        # === Restaurant Feature Strings ===
        "admin.goods.add.allergen.dairy": "Dairy",
        "admin.goods.add.allergen.eggs": "Eggs",
        "admin.goods.add.allergen.fish": "Fish",
        "admin.goods.add.allergen.gluten": "Gluten",
        "admin.goods.add.allergen.nuts": "Nuts",
        "admin.goods.add.allergen.sesame": "Sesame",
        "admin.goods.add.allergen.shellfish": "Shellfish",
        "admin.goods.add.allergen.soy": "Soy",
        "admin.goods.add.allergens.done": "✅ Done",
        "admin.goods.add.allergens.skip": "⏭ No Allergens",
        "admin.goods.add.availability.invalid": "❌ Invalid format. Use HH:MM-HH:MM (e.g. 06:00-22:00)",
        "admin.goods.add.availability.skip": "⏭ All Day",
        "admin.goods.add.daily_limit.invalid": "❌ Enter a positive number.",
        "admin.goods.add.daily_limit.skip": "⏭ Unlimited",
        "admin.goods.add.modifier.add_another_group": "➕ Another Group",
        "admin.goods.add.modifier.add_group": "➕ Add Modifier Group",
        "admin.goods.add.modifier.add_option": "➕ Add Option",
        "admin.goods.add.modifier.all_done": "✅ Finish",
        "admin.goods.add.modifier.finish": "✅ Finish (No Modifiers)",
        "admin.goods.add.modifier.group_added": "✅ Group added! Add another group or finish.",
        "admin.goods.add.modifier.group_name": "Enter modifier group name (e.g. Spice Level):",
        "admin.goods.add.modifier.group_type": "Select type for this group:",
        "admin.goods.add.modifier.option_added": "✅ Option added! Add another or press Done.",
        "admin.goods.add.modifier.option_label": "Enter option label (e.g. Mild, Extra Cheese):",
        "admin.goods.add.modifier.option_price": "Enter price adjustment for this option (0 for free):",
        "admin.goods.add.modifier.options_done": "✅ Done with Options",
        "admin.goods.add.modifier.paste_json": "📋 Paste JSON",
        "admin.goods.add.modifier.required_no": "⭕ Optional",
        "admin.goods.add.modifier.required_yes": "✅ Required",
        "admin.goods.add.modifier.type_multi": "Multi Choice",
        "admin.goods.add.modifier.type_single": "Single Choice",
        "admin.goods.add.photo.done": "✅ Done",
        "admin.goods.add.photo.received": "✅ Media received! Send more or press Done.",
        "admin.goods.add.photo.send_more": "Send more photos/videos or press Done:",
        "admin.goods.add.photo.skip": "⏭ Skip Photos",
        "admin.goods.add.prep_time.invalid": "❌ Enter a positive number.",
        "admin.goods.add.prep_time.skip": "⏭ Skip",
        "admin.goods.add.prompt.allergens": "⚠️ Select allergens (tap to toggle, then Done):",
        "admin.goods.add.prompt.availability": "🕐 Enter availability hours (e.g. 06:00-22:00) or press Skip for all-day:",
        "admin.goods.add.prompt.daily_limit": "📊 Enter daily limit (max units per day) or press Skip for unlimited:",
        "admin.goods.add.prompt.modifier_group": "Add a modifier group (e.g. Spice Level, Extras)?",
        "admin.goods.add.prompt.photo": "📸 Send a photo or video of this item (or press Skip):",
        "admin.goods.add.prompt.prep_time": "⏱ Enter prep time in minutes (or press Skip):",
        "admin.goods.toggle.active_off": "🚫 {item}: Deactivated",
        "admin.goods.toggle.active_on": "✅ {item}: Activated",
        "admin.goods.toggle.sold_out_off": "✅ {item}: Back in stock",
        "admin.goods.toggle.sold_out_on": "❌ {item}: Marked SOLD OUT",
        "btn.view_gallery": "📸 Gallery ({count})",
        "kitchen.order.modifier_detail": "    ↳ {modifiers}",
        "kitchen.order.prep_time": "⏱ Est. prep: {minutes} min",
        "kitchen.order.ready_by": "🕐 Ready by: {time}",
        "order.estimated_ready": "⏱ Estimated ready in ~{minutes} min",
        "shop.item.allergens": "⚠️ Allergens: {allergens}",
        "shop.item.availability": "🕐 Available: {from_time} - {until_time}",
        "shop.item.calories": "🔥 {calories} cal",
        "shop.item.daily_remaining": "📊 Today: {remaining}/{limit} left",
        "shop.item.no_gallery": "No gallery for this item.",
        "shop.item.type_product": "📦 النوع: منتج معبأ",
        "shop.item.type_prepared": "🍳 النوع: يُحضَّر عند الطلب",
        "shop.item.prep_time": "⏱ Prep: ~{minutes} min",
        "shop.item.sold_out": "❌ Sold out today",
        "admin.accounting.export_payments": "📥 Payment Reconciliation",
        "admin.accounting.export_products": "📥 Revenue by Product",
        "admin.accounting.export_sales": "📥 Export Sales CSV",
        "admin.accounting.export_sent": "✅ Report exported.",
        "admin.accounting.no_data": "No data for this period.",
        "admin.accounting.summary": "📊 <b>Revenue Summary ({period})</b>\n\n💰 Revenue: {total} {currency}\n📦 Orders: {orders}\n📈 Avg: {avg} {currency}\n\n<b>By Payment:</b>\n{payments}\n\n<b>Top Products:</b>\n{products}",
        "admin.accounting.summary_all": "📊 All Time",
        "admin.accounting.summary_month": "📊 This Month",
        "admin.accounting.summary_today": "📊 Today",
        "admin.accounting.summary_week": "📊 This Week",
        "admin.accounting.title": "📊 <b>Accounting & Reports</b>",
        "admin.coupon.create": "➕ Create Coupon",
        "admin.coupon.created": "✅ Coupon <b>{code}</b> created!\nType: {type}\nValue: {value}\nMin order: {min_order}\nMax uses: {max_uses}\nExpires: {expiry}",
        "admin.coupon.detail": "🎟 <b>{code}</b>\nType: {type}\nValue: {value}\nMin Order: {min_order}\nMax Uses: {max_uses}\nUsed: {used}\nStatus: {status}\nExpires: {expiry}",
        "admin.coupon.empty": "No coupons found.",
        "admin.coupon.enter_code": "Enter coupon code (or type <b>auto</b> for random):",
        "admin.coupon.enter_expiry": "Enter expiry in days (or <b>skip</b> for no expiry):",
        "admin.coupon.enter_max_uses": "Enter max total uses (or <b>skip</b> for unlimited):",
        "admin.coupon.enter_min_order": "Enter minimum order amount (or <b>skip</b>):",
        "admin.coupon.enter_value": "Enter discount value ({type}):",
        "admin.coupon.invalid_value": "❌ Invalid value. Enter a number.",
        "admin.coupon.list_active": "📋 Active Coupons",
        "admin.coupon.list_all": "📋 All Coupons",
        "admin.coupon.select_type": "Select discount type:",
        "admin.coupon.title": "🎟 <b>Coupon Management</b>",
        "admin.coupon.toggle_activate": "✅ Activate",
        "admin.coupon.toggle_deactivate": "❌ Deactivate",
        "admin.coupon.toggled": "✅ Coupon {code} is now {status}.",
        "admin.coupon.type_fixed": "💰 Fixed Amount",
        "admin.coupon.type_percent": "📊 Percentage (%)",
        "admin.menu.accounting": "📊 Accounting",
        "admin.menu.coupons": "🎟 Coupons",
        "admin.menu.segment_broadcast": "📣 Targeted Broadcast",
        "admin.menu.stores": "🏪 Stores",
        "admin.menu.tickets": "🎫 Tickets",
        "admin.menu.ai_assistant": "🤖 AI Assistant",
        "admin.segment.all_users": "👥 All Users",
        "admin.segment.count": "📊 Segment: <b>{segment}</b>\nUsers: <b>{count}</b>\n\nType your broadcast message:",
        "admin.segment.empty": "No users in this segment.",
        "admin.segment.high_spenders": "💰 High Spenders",
        "admin.segment.inactive": "😴 Inactive (30+ days)",
        "admin.segment.new_users": "🆕 New Users (7d)",
        "admin.segment.recent_buyers": "🛒 Recent Buyers (7d)",
        "admin.segment.sent": "✅ Sent to {sent}/{total} ({segment}).",
        "admin.segment.title": "📣 <b>Targeted Broadcast</b>\n\nSelect segment:",
        "admin.store.add": "➕ Add Store",
        "admin.store.address_prompt": "Enter store address (or <b>skip</b>):",
        "admin.store.btn_default": "⭐ Set as Default",
        "admin.store.created": "✅ Store <b>{name}</b> created!",
        "admin.store.detail": "🏪 <b>{name}</b>\nStatus: {status}\nDefault: {default}\nAddress: {address}\nLocation: {location}\nPhone: {phone}",
        "admin.store.empty": "No stores configured.",
        "admin.store.location_prompt": "Send GPS location (or type <b>skip</b>):",
        "admin.store.name_exists": "Store with this name already exists.",
        "admin.store.name_prompt": "Enter store name:",
        "admin.store.set_default": "✅ {name} set as default store.",
        "admin.store.title": "🏪 <b>Store Management</b>",
        "admin.store.toggle_activate": "✅ Activate",
        "admin.store.toggle_deactivate": "❌ Deactivate",
        "admin.store.toggled": "✅ Store {name} is now {status}.",
        "admin.ticket.detail": "🎫 <b>Ticket #{code}</b>\nUser: {user_id}\nStatus: {status}\nPriority: {priority}\nSubject: {subject}\nCreated: {date}",
        "admin.ticket.empty": "No open tickets.",
        "admin.ticket.list": "Open/In Progress Tickets:",
        "admin.ticket.reply_prompt": "Reply to ticket #{code}:",
        "admin.ticket.resolved": "✅ Ticket #{code} resolved.",
        "admin.ticket.title": "🎫 <b>Support Tickets</b>",
        "btn.admin.reply_ticket": "💬 Reply",
        "btn.admin.resolve_ticket": "✅ Resolve",
        "btn.apply_coupon": "🎟 Apply Coupon",
        "btn.close_ticket": "✖ Close Ticket",
        "btn.create_ticket": "➕ New Ticket",
        "btn.create_ticket_for_order": "🎫 Support Ticket",
        "btn.invoice": "🧾 Receipt",
        "btn.my_tickets": "🎫 Support",
        "btn.reorder": "🔄 Reorder",
        "btn.reply_ticket": "💬 Reply",
        "btn.review_order": "⭐ Leave Review",
        "btn.search": "🔍 Search",
        "btn.skip_coupon": "⏭ Skip Coupon",
        "coupon.already_used": "❌ You already used this coupon.",
        "coupon.applied": "✅ Coupon applied! Discount: -{discount} {currency}",
        "coupon.enter_code": "🎟 Enter coupon code (or press Skip):",
        "coupon.expired": "❌ This coupon has expired.",
        "coupon.invalid": "❌ Invalid or expired coupon code.",
        "coupon.max_uses_reached": "❌ Coupon usage limit reached.",
        "coupon.min_order_not_met": "❌ Min order of {min_order} required.",
        "coupon.not_yet_valid": "❌ This coupon is not yet valid.",
        "invoice.not_available": "Receipt not available.",
        "reorder.success": "✅ Added {added} item(s) to cart. {skipped} item(s) unavailable.",
        "review.already_reviewed": "You have already reviewed this order.",
        "review.comment_prompt": "You rated {rating}/5 ⭐\n\nAdd a comment? Type or press Skip:",
        "review.detail": "⭐{rating}/5 — {comment}",
        "review.item_rating": "⭐ <b>{item}</b>: {avg:.1f}/5 ({count} reviews)",
        "review.no_reviews": "No reviews yet.",
        "review.prompt": "⭐ <b>Rate your order #{order_code}</b>\n\nSelect your rating:",
        "review.rate_1": "⭐",
        "review.rate_2": "⭐⭐",
        "review.rate_3": "⭐⭐⭐",
        "review.rate_4": "⭐⭐⭐⭐",
        "review.rate_5": "⭐⭐⭐⭐⭐",
        "review.skip_comment": "⏭ Skip",
        "review.thanks": "✅ Thank you for your review! ({rating}/5 ⭐)",
        "search.no_results": "❌ No products found. Try different keywords.",
        "search.prompt": "🔍 Enter product name or keyword to search:",
        "search.result_count": "Found {count} product(s):\n",
        "search.results_title": "🔍 <b>Search results for:</b> {query}\n\n",
        "ticket.admin_replied": "💬 Admin replied to ticket #{code}:\n{text}",
        "ticket.closed": "✅ Ticket closed.",
        "ticket.created": "✅ Ticket <b>#{code}</b> created!",
        "ticket.message_format": "<b>{role}</b> ({date}):\n{text}\n",
        "ticket.message_prompt": "Describe your issue:",
        "ticket.no_tickets": "No support tickets.",
        "ticket.reply_prompt": "Type your reply:",
        "ticket.reply_sent": "✅ Reply sent.",
        "ticket.resolved_notification": "✅ Ticket #{code} resolved!",
        "ticket.status.closed": "⚫ Closed",
        "ticket.status.in_progress": "🔵 In Progress",
        "ticket.status.open": "🟢 Open",
        "ticket.status.resolved": "✅ Resolved",
        "ticket.subject_prompt": "Enter the subject:",
        "ticket.title": "🎫 <b>Support Tickets</b>",
        "ticket.view_title": "🎫 <b>Ticket #{code}</b>\nStatus: {status}\nSubject: {subject}\nCreated: {date}",

        # === PDPA Privacy Policy ===
        "btn.privacy": "🔒 سياسة الخصوصية",
        "privacy.notice": (
            "🔒 <b>إشعار الخصوصية (PDPA)</b>\n\n"
            "نحن نلتزم بقانون حماية البيانات الشخصية في تايلاند (PDPA).\n\n"
            "<b>البيانات التي نجمعها:</b>\n"
            "• الاسم / الهاتف / عنوان التوصيل\n"
            "• تفاصيل الطلب والسجل\n"
            "• معرف تيليجرام\n\n"
            "<b>الأغراض:</b>\n"
            "• تنفيذ الطلب والتوصيل (ضرورة تعاقدية)\n"
            "• منع الاحتيال والتحقق من الهوية\n"
            "• التسويق — فقط بموافقتك المنفصلة\n\n"
            "<b>الاحتفاظ:</b> حتى تطلب الحذف، أو سنتين بعد آخر طلب\n\n"
            "<b>مشاركة البيانات:</b> المطاعم، سائقي التوصيل، مزودي الدفع — فقط حسب الحاجة لطلبك. "
            "لا نبيع بياناتك أبداً.\n\n"
            "<b>حقوقك بموجب PDPA:</b>\n"
            "• الوصول / تصحيح / حذف بياناتك\n"
            "• سحب الموافقة (للتسويق)\n"
            "• الاعتراض على المعالجة / طلب نقل البيانات\n"
            "• تقديم شكوى إلى PDPC\n\n"
            "<b>مراقب البيانات:</b> {company}\n"
            "التواصل: {email}\n\n"
            "باستمرارك في استخدام هذا البوت، فإنك تقر وتقبل هذه السياسة."
        ),
        "privacy.btn_full_policy": "📄 قراءة السياسة الكاملة",
        "privacy.btn_accept": "✅ قبول ومتابعة",
        "privacy.accepted": "✅ لقد قبلت سياسة الخصوصية.",
        "privacy.already_accepted": "✅ لقد قبلت سياسة الخصوصية بالفعل.",
        "privacy.no_url": "لم يتم تكوين صفحة سياسة الخصوصية الكاملة بعد.",
    },

    "fa": {
        # === Common Buttons ===
        "btn.shop": "🏪 فروشگاه",
        "btn.rules": "📜 قوانین",
        "btn.profile": "👤 پروفایل",
        "btn.support": "🆘 پشتیبانی",
        "btn.channel": "ℹ کانال اخبار",
        "btn.admin_menu": "🎛 پنل مدیریت",
        "btn.back": "⬅️ بازگشت",
        "btn.close": "✖ بستن",
        "btn.yes": "✅ بله",
        "btn.no": "❌ خیر",
        "btn.check_subscription": "🔄 بررسی اشتراک",
        "btn.admin.ban_user": "🚫 مسدود کردن کاربر",
        "btn.admin.unban_user": "✅ رفع مسدودیت کاربر",

        # === Admin Buttons (user management shortcuts) ===
        "btn.admin.promote": "⬆️ ارتقا به مدیر",
        "btn.admin.demote": "⬇️ حذف مدیریت",
        "btn.admin.add_user_bonus": "🎁 افزودن پاداش معرفی",

        # === Titles / Generic Texts ===
        "menu.title": "⛩️ منوی اصلی",
        "admin.goods.add.stock.error": "❌ خطا در افزودن موجودی اولیه: {error}",
        "admin.goods.stock.add_success": "✅ {quantity} واحد به \"{item}\" اضافه شد",
        "admin.goods.stock.add_units": "➕ افزودن واحد",
        "admin.goods.stock.current_status": "وضعیت فعلی",
        "admin.goods.stock.error": "❌ خطا در مدیریت موجودی: {error}",
        "admin.goods.stock.insufficient": "❌ موجودی کافی نیست. فقط {available} واحد موجود است.",
        "admin.goods.stock.invalid_quantity": "⚠️ مقدار نامعتبر. یک عدد صحیح وارد کنید.",
        "admin.goods.stock.management_title": "مدیریت موجودی: {item}",
        "admin.goods.stock.negative_quantity": "⚠️ مقدار نمی\u200cتواند منفی باشد.",
        "admin.goods.stock.no_products": "❌ هنوز محصولی در فروشگاه وجود ندارد",
        "admin.goods.stock.prompt.add_units": "تعداد واحدهای اضافه\u200cشونده را وارد کنید:",
        "admin.goods.stock.prompt.item_name": "نام محصول را برای مدیریت موجودی وارد کنید:",
        "admin.goods.stock.prompt.remove_units": "تعداد واحدهای حذف\u200cشونده را وارد کنید:",
        "admin.goods.stock.prompt.set_exact": "مقدار دقیق موجودی را وارد کنید:",
        "admin.goods.stock.redirect_message": "ℹ️ مدیریت موجودی اکنون از طریق منوی «مدیریت موجودی» در دسترس است",
        "admin.goods.stock.remove_success": "✅ {quantity} واحد از \"{item}\" حذف شد",
        "admin.goods.stock.remove_units": "➖ حذف واحد",
        "admin.goods.stock.select_action": "عملیات را انتخاب کنید",
        "admin.goods.stock.set_exact": "⚖️ تنظیم مقدار دقیق",
        "admin.goods.stock.set_success": "✅ موجودی \"{item}\" به {quantity} واحد تنظیم شد",
        "admin.goods.stock.status_title": "📊 وضعیت موجودی:",
        "errors.invalid_item_name": "❌ نام محصول نامعتبر",
        "errors.invalid_language": "زبان نامعتبر",
        "shop.error.brand_required": "لطفاً ابتدا برند را انتخاب کنید",
        "shop.error.branch_unavailable": "شعبه در دسترس نیست",
        "profile.caption": "👤 <b>پروفایل</b> — <a href='tg://user?id={id}'>{name}</a>",
        "rules.not_set": "❌ قوانین هنوز اضافه نشده\u200cاند",
        "admin.users.cannot_ban_owner": "❌ امکان مسدود کردن مالک وجود ندارد",
        "admin.users.ban.success": "✅ کاربر {name} با موفقیت مسدود شد",
        "admin.users.ban.failed": "❌ مسدود کردن کاربر ناموفق بود",
        "admin.users.ban.notify": "⛔ شما توسط مدیر مسدود شده\u200cاید",
        "admin.users.unban.success": "✅ مسدودیت کاربر {name} با موفقیت رفع شد",
        "admin.users.unban.failed": "❌ رفع مسدودیت کاربر ناموفق بود",
        "admin.users.unban.notify": "✅ مسدودیت شما توسط مدیر رفع شد",

        # === Profile ===
        "btn.referral": "🎲 سیستم معرفی",
        "btn.purchased": "🎁 محصولات خریداری\u200cشده",
        "profile.referral_id": "👤 <b>معرف</b> — <code>{id}</code>",

        # === Subscription Flow ===
        "subscribe.prompt": "ابتدا در کانال اخبار عضو شوید",

        # === Profile Info Lines ===
        "profile.id": "🆔 <b>شناسه</b> — <code>{id}</code>",
        "profile.bonus_balance": "💰 <b>پاداش معرفی:</b> ${bonus_balance}",
        "profile.purchased_count": "🎁 <b>محصولات خریداری\u200cشده</b> — {count} عدد",
        "profile.registration_date": "🕢 <b>تاریخ ثبت\u200cنام</b> — <code>{dt}</code>",

        # === Referral ===
        "referral.title": "💚 سیستم معرفی",
        "referral.count": "تعداد معرفی\u200cها: {count}",
        "referral.description": "📔 سیستم معرفی به شما امکان کسب درآمد بدون سرمایه\u200cگذاری را می\u200cدهد. لینک شخصی خود را به اشتراک بگذارید و {percent}% از شارژ حساب معرفی\u200cشدگان را در موجودی ربات خود دریافت کنید.",
        "btn.view_referrals": "👥 معرفی\u200cشدگان من",
        "btn.view_earnings": "💰 درآمد من",

        "referrals.list.title": "👥 معرفی\u200cشدگان شما:",
        "referrals.list.empty": "هنوز معرفی\u200cشده فعالی ندارید",
        "referrals.item.format": "ID: {telegram_id} | درآمد: {total_earned} {currency}",

        "referral.earnings.title": "💰 درآمد از معرفی\u200cشده <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>):",
        "referral.earnings.empty": "هنوز درآمدی از این معرفی\u200cشده <code>{id}</code> (<a href='tg://user?id={id}'>{name}</a>) کسب نشده",
        "referral.earning.format": "{amount} {currency} | {date} | (از {original_amount} {currency})",
        "referral.item.info": "💰 شماره درآمد: <code>{id}</code>\n👤 معرفی\u200cشده: <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>)\n🔢 مبلغ: {amount} {currency}\n🕘 تاریخ: <code>{date}</code>\n💵 از واریز به {original_amount} {currency}",

        "referral.admin_bonus.info": "💰 شماره درآمد: <code>{id}</code>\n🎁 <b>پاداش از مدیر</b>\n🔢 مبلغ: {amount} {currency}\n🕘 تاریخ: <code>{date}</code>",

        "all.earnings.title": "💰 تمام درآمدهای معرفی شما:",
        "all.earnings.empty": "هنوز درآمدی از معرفی ندارید",
        "all.earning.format.admin": "{amount} {currency} از مدیر | {date}",

        "referrals.stats.template": "📊 آمار سیستم معرفی:\n\n👥 معرفی\u200cهای فعال: {active_count}\n💰 کل درآمد: {total_earned} {currency}\n📈 کل شارژ معرفی\u200cشدگان: {total_original} {currency}\n🔢 تعداد درآمدها: {earnings_count}",

        # === Admin: Main Menu ===
        "admin.menu.main": "⛩️ منوی مدیریت",
        "admin.menu.shop": "🛒 مدیریت فروشگاه",
        "admin.menu.goods": "📦 مدیریت محصولات",
        "admin.menu.categories": "📂 مدیریت دسته\u200cبندی\u200cها",
        "admin.menu.users": "👥 مدیریت کاربران",
        "admin.menu.broadcast": "📝 ارسال همگانی",
        "admin.menu.rights": "مجوزهای کافی ندارید",

        # === Admin: User Management ===
        "admin.users.prompt_enter_id": "👤 شناسه کاربر را برای مشاهده / ویرایش وارد کنید",
        "admin.users.invalid_id": "⚠️ لطفاً یک شناسه عددی معتبر وارد کنید.",
        "admin.users.profile_unavailable": "❌ پروفایل در دسترس نیست (چنین کاربری وجود ندارد)",
        "admin.users.not_found": "❌ کاربر یافت نشد",
        "admin.users.cannot_change_owner": "امکان تغییر نقش مالک وجود ندارد",
        "admin.users.referrals": "👥 <b>معرفی\u200cشدگان کاربر</b> — {count}",
        "admin.users.btn.view_referrals": "👥 معرفی\u200cشدگان کاربر",
        "admin.users.btn.view_earnings": "💰 درآمدهای کاربر",
        "admin.users.role": "🎛 <b>نقش</b> — {role}",
        "admin.users.set_admin.success": "✅ نقش به {name} اختصاص داده شد",
        "admin.users.set_admin.notify": "✅ نقش مدیر به شما اعطا شد",
        "admin.users.remove_admin.success": "✅ نقش مدیر از {name} لغو شد",
        "admin.users.remove_admin.notify": "❌ نقش مدیر شما لغو شده است",
        "admin.users.bonus.prompt": "مبلغ پاداش را به {currency} وارد کنید:",
        "admin.users.bonus.added": "✅ پاداش معرفی {name} به مبلغ {amount} {currency} شارژ شد",
        "admin.users.bonus.added.notify": "🎁 پاداش معرفی به مبلغ {amount} {currency} به شما تعلق گرفت",
        "admin.users.bonus.invalid": "❌ مبلغ نامعتبر. عددی بین {min_amount} تا {max_amount} {currency} وارد کنید.",

        # === Admin: Shop Management Menu ===
        "admin.shop.menu.title": "⛩️ مدیریت فروشگاه",
        "admin.shop.menu.statistics": "📊 آمار",
        "admin.shop.menu.logs": "📁 نمایش لاگ\u200cها",
        "admin.shop.menu.admins": "👮 مدیران",
        "admin.shop.menu.users": "👤 کاربران",

        # === Admin: Categories Management ===
        "admin.categories.menu.title": "⛩️ مدیریت دسته\u200cبندی\u200cها",
        "admin.categories.add": "➕ افزودن دسته\u200cبندی",
        "admin.categories.rename": "✏️ تغییر نام دسته\u200cبندی",
        "admin.categories.delete": "🗑 حذف دسته\u200cبندی",
        "admin.categories.prompt.add": "نام دسته\u200cبندی جدید را وارد کنید:",
        "admin.categories.prompt.delete": "نام دسته\u200cبندی برای حذف را وارد کنید:",
        "admin.categories.prompt.rename.old": "نام فعلی دسته\u200cبندی برای تغییر نام را وارد کنید:",
        "admin.categories.prompt.rename.new": "نام جدید دسته\u200cبندی را وارد کنید:",
        "admin.categories.add.exist": "❌ دسته\u200cبندی ایجاد نشد (از قبل وجود دارد)",
        "admin.categories.add.success": "✅ دسته\u200cبندی ایجاد شد",
        "admin.categories.delete.not_found": "❌ دسته\u200cبندی حذف نشد (وجود ندارد)",
        "admin.categories.delete.success": "✅ دسته\u200cبندی حذف شد",
        "admin.categories.rename.not_found": "❌ دسته\u200cبندی به\u200cروزرسانی نشد (وجود ندارد)",
        "admin.categories.rename.exist": "❌ تغییر نام ممکن نیست (دسته\u200cبندی با این نام وجود دارد)",
        "admin.categories.rename.success": "✅ دسته\u200cبندی \"{old}\" به \"{new}\" تغییر نام داده شد",

        # === Admin: Goods / Items Management (Add / List / Item Info) ===
        "admin.goods.add_position": "➕ افزودن محصول",
        "admin.goods.manage_stock": "➕ افزودن کالا به محصول",
        "admin.goods.update_position": "📝 ویرایش محصول",
        "admin.goods.delete_position": "❌ حذف محصول",
        "admin.goods.add.prompt.type": "نوع محصول را انتخاب کنید:",
        "admin.goods.add.type.prepared": "🍳 تازه تهیه می‌شود (غذا، نوشیدنی)",
        "admin.goods.add.type.product": "📦 محصول بسته‌بندی شده (آب، تنقلات)",
        "admin.goods.add.prompt.name": "نام محصول را وارد کنید",
        "admin.goods.add.name.exists": "❌ محصول ایجاد نشد (از قبل وجود دارد)",
        "admin.goods.add.prompt.description": "توضیحات محصول را وارد کنید:",
        "admin.goods.add.prompt.price": "قیمت محصول را وارد کنید (عدد به {currency}):",
        "admin.goods.add.price.invalid": "⚠️ قیمت نامعتبر. لطفاً یک عدد وارد کنید.",
        "admin.goods.add.prompt.category": "دسته\u200cبندی محصول را وارد کنید:",
        "admin.goods.add.category.not_found": "❌ محصول ایجاد نشد (دسته\u200cبندی نامعتبر)",
        "admin.goods.position.not_found": "❌ کالایی یافت نشد (این محصول وجود ندارد)",
        "admin.goods.menu.title": "⛩️ منوی مدیریت محصولات",
        "admin.goods.add.stock.prompt": "تعداد کالاهای اضافه\u200cشونده را وارد کنید",
        "admin.goods.add.stock.invalid": "⚠️ مقدار نادرست. لطفاً یک عدد وارد کنید.",
        "admin.goods.add.stock.negative": "⚠️ مقدار نادرست. یک عدد مثبت وارد کنید.",
        "admin.goods.add.result.created_with_stock": "✅ محصول {item_name} ایجاد شد، {stock_quantity} به تعداد کالا اضافه شد.",

        # === Admin: Goods / Items Update Flow ===
        "admin.goods.update.position.invalid": "محصول یافت نشد.",
        "admin.goods.update.position.exists": "محصولی با این نام از قبل وجود دارد.",
        "admin.goods.update.prompt.name": "نام محصول را وارد کنید",
        "admin.goods.update.not_exists": "❌ محصول به\u200cروزرسانی نشد (وجود ندارد)",
        "admin.goods.update.prompt.new_name": "نام جدید محصول را وارد کنید:",
        "admin.goods.update.prompt.description": "توضیحات محصول را وارد کنید:",
        "admin.goods.update.success": "✅ محصول به\u200cروزرسانی شد",

        # === Admin: Goods / Items Delete Flow ===
        "admin.goods.delete.prompt.name": "نام محصول را وارد کنید",
        "admin.goods.delete.position.not_found": "❌ محصول حذف نشد (وجود ندارد)",
        "admin.goods.delete.position.success": "✅ محصول حذف شد",

        # === Admin: Item Info ===
        "admin.goods.view_stock": "مشاهده محصولات",

        # Admin Modifier Management (Card 8)
        "admin.goods.manage_modifiers": "🍳 افزودنی‌ها",
        "admin.goods.modifiers.prompt": "آیا می‌خواهید افزودنی (ادویه، اضافه‌ها و غیره) اضافه کنید?",
        "admin.goods.modifiers.add_btn": "➕ افزودن افزودنی",
        "admin.goods.modifiers.skip_btn": "⏭ رد شدن",
        "admin.goods.modifiers.json_prompt": "طرح JSON افزودنی‌ها را بچسبانید:",
        "admin.goods.modifiers.invalid_json": "❌ JSON نامعتبر: {error}",
        "admin.goods.modifiers.select_item": "نام محصول را برای پیکربندی افزودنی وارد کنید:",
        "admin.goods.modifiers.edit_instructions": "یک عملیات انتخاب کنید:",
        "admin.goods.modifiers.set_new": "📝 تنظیم جدید",
        "admin.goods.modifiers.clear": "🗑 پاک کردن همه",

        # === Admin: Logs ===
        "admin.shop.logs.caption": "لاگ\u200cهای ربات",
        "admin.shop.logs.empty": "❗️ هنوز لاگی وجود ندارد",

        # === Group Notifications ===
        "shop.group.new_upload": "موجودی جدید",
        "shop.group.item": "محصول",
        "shop.group.stock": "تعداد",

        # === Admin: Statistics ===
        "admin.shop.stats.template": "آمار فروشگاه:\n➖➖➖➖➖➖➖➖➖➖➖➖➖\n<b>◽کاربران</b>\n◾️کاربران ۲۴ ساعت اخیر: {today_users}\n◾️کل مدیران: {admins}\n◾️کل کاربران: {users}\n➖➖➖➖➖➖➖➖➖➖➖➖➖\n◽<b>متفرقه</b>\n◾محصولات: {items} عدد\n◾کالاها: {goods} عدد\n◾دسته\u200cبندی\u200cها: {categories} عدد\n",

        # === Admin: Lists & Broadcast ===
        "admin.shop.admins.title": "👮 مدیران ربات:",
        "admin.shop.users.title": "کاربران ربات:",
        "broadcast.prompt": "پیام ارسال همگانی را بفرستید:",
        "broadcast.creating": "📤 شروع ارسال همگانی...\n👥 کل کاربران: {ids}",
        "broadcast.progress": "📤 ارسال همگانی در حال انجام...\n\n\n📊 پیشرفت: {progress:.1f}%{n}✅ ارسال شده: {sent}/{total}\n❌ خطاها: {failed}\n⏱ زمان سپری\u200cشده: {time} ثانیه",
        "broadcast.done": "✅ ارسال همگانی تکمیل شد!\n\n📊 آمار:📊\n👥 کل: {total}\n✅ تحویل\u200cشده: {sent}\n❌ تحویل\u200cنشده: {failed}\n🚫 ربات مسدود: ~{blocked}\n📈 نرخ موفقیت: {success}%\n⏱ زمان: {duration} ثانیه",
        "broadcast.cancel": "❌ ارسال همگانی لغو شد.",
        "broadcast.warning": "ارسال همگانی فعالی وجود ندارد",

        # === Brand / Store Selection ===
        "shop.brands.title": "🏪 یک رستوران انتخاب کنید",
        "shop.branches.title": "📍 یک شعبه انتخاب کنید",
        "shop.no_brands": "در حال حاضر رستورانی در دسترس نیست.",
        "shop.brand_unavailable": "این رستوران در حال حاضر در دسترس نیست.",

        # === Shop Browsing (Categories / Goods / Item Page) ===
        "shop.categories.title": "🏪 دسته\u200cبندی\u200cهای فروشگاه",
        "shop.goods.choose": "🏪 یک محصول انتخاب کنید",
        "shop.item.not_found": "محصول یافت نشد",
        "shop.item.title": "🏪 محصول {name}",
        "shop.item.description": "توضیحات: {description}",
        "shop.item.price": "قیمت — {amount} {currency}",
        "shop.item.quantity_unlimited": "تعداد — نامحدود",
        "shop.item.quantity_left": "تعداد — {count} عدد",
        "shop.item.quantity_detailed": "📦 کل موجودی: {total} عدد\n🔒 رزرو شده: {reserved} عدد\n✅ قابل سفارش: {available} عدد",

        # === Purchases ===
        "purchases.title": "محصولات خریداری\u200cشده:",
        "purchases.pagination.invalid": "داده\u200cهای صفحه\u200cبندی نامعتبر",
        "purchases.item.not_found": "خرید یافت نشد",
        "purchases.item.name": "<b>🧾 محصول</b>: <code>{name}</code>",
        "purchases.item.price": "<b>💵 قیمت</b>: <code>{amount}</code> {currency}",
        "purchases.item.datetime": "<b>🕒 تاریخ خرید</b>: <code>{dt}</code>",
        "purchases.item.unique_id": "<b>🧾 شناسه یکتا</b>: <code>{uid}</code>",
        "purchases.item.value": "<b>🔑 مقدار</b>:\n<code>{value}</code>",

        # === Middleware ===
        "middleware.ban": "⏳ شما موقتاً مسدود شده\u200cاید. {time} ثانیه صبر کنید.",
        "middleware.above_limits": "⚠️ درخواست\u200cهای بیش از حد! شما موقتاً مسدود شده\u200cاید.",
        "middleware.waiting": "⏳ {time} ثانیه برای اقدام بعدی صبر کنید.",
        "middleware.security.session_outdated": "⚠️ نشست منقضی شده. لطفاً دوباره شروع کنید.",
        "middleware.security.invalid_data": "❌ داده\u200cهای نامعتبر",
        "middleware.security.blocked": "❌ دسترسی مسدود شد",
        "middleware.security.not_admin": "⛔ مجوزهای کافی ندارید",
        "middleware.security.banned": "⛔ <b>شما مسدود شده\u200cاید</b>\n\nدلیل: {reason}",
        "middleware.security.banned_no_reason": "⛔ <b>شما مسدود شده\u200cاید</b>\n\nبرای اطلاعات بیشتر با مدیر تماس بگیرید.",
        "middleware.security.rate_limit": "⚠️ درخواست\u200cهای بیش از حد! لطفاً کمی صبر کنید.",

        # === Errors ===
        "errors.not_subscribed": "شما عضو نشده\u200cاید",
        "errors.pagination_invalid": "داده\u200cهای صفحه\u200cبندی نامعتبر",
        "errors.invalid_data": "❌ داده\u200cهای نامعتبر",
        "errors.channel.telegram_not_found": "امکان نوشتن در کانال وجود ندارد. مرا به عنوان مدیر کانال آپلود @{channel} با حق انتشار پیام اضافه کنید.",
        "errors.channel.telegram_forbidden_error": "کانال یافت نشد. نام کاربری کانال آپلود @{channel} را بررسی کنید.",
        "errors.channel.telegram_bad_request": "ارسال به کانال آپلود ناموفق بود: {e}",

        # === Orders ===
        "order.payment_method.choose": "💳 روش پرداخت را انتخاب کنید:",
        "order.payment_method.bitcoin": "💳 Bitcoin",
        "order.payment_method.litecoin": "💳 Litecoin",
        "order.payment_method.solana": "💳 SOL",
        "order.payment_method.usdt_sol": "💳 USDT (Solana)",
        "order.payment_method.cash": "💵 پرداخت در محل",
        "order.status.notify_order_confirmed": "سفارش {order_code} تأیید شد! 🎉\n\nسفارش شما تحویل داده خواهد شد در: {delivery_time}\n\nمحصولات:\n{items}\n\nجمع کل: {total}\n\nمنتظر تحویل باشید!",
        "order.status.notify_order_delivered": "سفارش {order_code} تحویل داده شد! ✅\n\nاز خرید شما متشکریم! امیدواریم دوباره شما را ببینیم! 🙏",
        "order.status.notify_order_modified": "سفارش {order_code} توسط مدیر ویرایش شد 📝\n\nتغییرات:\n{changes}\n\nجمع جدید: {total}",

        # === Additional Common Buttons ===
        "btn.cart": "🛒 سبد خرید",
        "btn.my_orders": "📦 سفارش\u200cهای من",
        "btn.reference_codes": "🔑 کدهای مرجع",
        "btn.settings": "⚙️ تنظیمات",
        "btn.referral_bonus_percent": "💰 درصد پاداش معرفی",
        "btn.order_timeout": "⏱️ مهلت سفارش",
        "btn.timezone": "🌍 منطقه زمانی",
        "btn.promptpay_account": "💳 حساب PromptPay",
        "btn.currency": "💱 ارز",
        "btn.skip": "⏭️ رد کردن",
        "btn.use_saved_info": "✅ استفاده از اطلاعات ذخیره\u200cشده",
        "btn.update_info": "✏️ به\u200cروزرسانی اطلاعات",
        "btn.back_to_cart": "◀️ بازگشت به سبد خرید",
        "btn.clear_cart": "🗑️ پاک کردن سبد خرید",
        "btn.proceed_checkout": "💳 ادامه خرید",
        "btn.remove_item": "❌ حذف {item_name}",
        "btn.use_all_bonus": "استفاده از تمام ${amount}",
        "btn.apply_bonus_yes": "✅ بله، اعمال پاداش",
        "btn.apply_bonus_no": "❌ خیر، ذخیره برای بعد",
        "btn.cancel": "❌ لغو",
        "btn.add_to_cart": "🛒 افزودن به سبد خرید",

        # === Cart Management ===
        "cart.add_success": "✅ {item_name} به سبد خرید اضافه شد!",
        "cart.add_error": "❌ {message}",
        "cart.empty": "🛒 سبد خرید شما خالی است.\n\nفروشگاه را مرور کنید و محصول اضافه کنید!",
        "cart.title": "🛒 <b>سبد خرید شما</b>\n\n",
        "cart.removed_success": "محصول از سبد خرید حذف شد",
        "cart.cleared_success": "✅ سبد خرید با موفقیت پاک شد!",
        "cart.empty_alert": "سبد خرید خالی است!",
        "cart.summary_title": "📦 <b>خلاصه سفارش</b>\n\n",
        "cart.saved_delivery_info": "اطلاعات تحویل ذخیره\u200cشده شما:\n\n",
        "cart.delivery_address": "📍 آدرس: {address}\n",
        "cart.delivery_phone": "📞 تلفن: {phone}\n",
        "cart.delivery_note": "📝 یادداشت: {note}\n",
        "cart.use_info_question": "\n\nآیا می\u200cخواهید از این اطلاعات استفاده کنید یا آن\u200cها را به\u200cروزرسانی کنید؟",
        "cart.no_saved_info": "❌ اطلاعات تحویل ذخیره\u200cشده یافت نشد. لطفاً به صورت دستی وارد کنید.",

        # === Order/Delivery Flow ===
        "order.delivery.address_prompt": "📍 لطفاً آدرس تحویل خود را وارد کنید:",
        "order.delivery.address_invalid": "❌ لطفاً یک آدرس معتبر وارد کنید (حداقل ۵ کاراکتر).",
        "order.delivery.phone_prompt": "📞 لطفاً شماره تلفن خود را وارد کنید (با کد کشور):",
        "order.delivery.phone_invalid": "❌ لطفاً یک شماره تلفن معتبر وارد کنید (حداقل ۸ رقم).",
        "order.delivery.note_prompt": "📝 دستورالعمل خاصی برای تحویل دارید؟ (اختیاری)\n\nمی\u200cتوانید با کلیک دکمه زیر رد کنید.",
        "order.delivery.info_save_error": "❌ خطا در ذخیره اطلاعات تحویل. لطفاً دوباره امتحان کنید.",

        # Location Method Choice
        "order.delivery.location_method_prompt": "📍 چگونه می\u200cخواهید آدرس تحویل خود را مشخص کنید?\n\nیکی از گزینه\u200cهای زیر را انتخاب کنید:",
        "btn.location_method.gps": "📡 ارسال GPS از طریق Telegram",
        "btn.location_method.live_gps": "📍 اشتراک موقعیت زنده",
        "btn.location_method.google_link": "🗺 ارسال لینک Google Maps",
        "btn.location_method.type_address": "✍️ تایپ آدرس",
        "order.delivery.gps_prompt": "📍 دکمه زیر را بزنید تا موقعیت خود را ارسال کنید:",
        "order.delivery.gps_hint": "📍 لطفاً از دکمه زیر برای ارسال موقعیت GPS استفاده کنید، یا 'بازگشت' را بزنید تا روش دیگری انتخاب کنید.",
        "order.delivery.live_gps_prompt": "📍 برای اشتراک موقعیت زنده:\n\n1. روی آیکون پیوست 📎 در پایین بزنید\n2. 'موقعیت' را انتخاب کنید\n3. 'اشتراک موقعیت زنده' را بزنید\n4. مدت زمان را انتخاب کنید\n\nراننده می\u200cتواند موقعیت شما را در لحظه ببیند!",
        "order.delivery.live_gps_saved": "✅ موقعیت زنده دریافت شد! راننده می\u200cتواند موقعیت شما را پیگیری کند.",
        "order.delivery.live_gps_hint": "📍 لطفاً موقعیت زنده خود را از منوی پیوست ارسال کنید (📎 ← موقعیت ← اشتراک موقعیت زنده).",
        "order.delivery.google_link_prompt": "🗺 لینک Google Maps با موقعیت خود را اینجا قرار دهید.\n\nGoogle Maps را باز کنید، موقعیت را پیدا کنید، 'اشتراک' را بزنید و لینک را اینجا کپی کنید.",
        "order.delivery.google_link_invalid": "❌ لینک Google Maps شناسایی نشد. مطمئن شوید با google.com/maps یا goo.gl/maps شروع می\u200cشود.",
        "order.delivery.address_confirm_prompt": "📍 آدرس شما:\n<b>{address}</b>\n\n🔗 <a href=\"{maps_link}\">مشاهده روی نقشه</a>\n\nآیا درست است؟",
        "btn.address_confirm_yes": "✅ بله، درست است",
        "btn.address_confirm_retry": "✏️ نه، دوباره وارد کنم",

        # GPS Location (Card 2)
        "order.delivery.location_prompt": "📍 آیا می\u200cخواهید موقعیت GPS خود را برای تحویل دقیق\u200cتر به اشتراک بگذارید؟\n\nدکمه زیر را بزنید یا این مرحله را رد کنید.",
        "order.delivery.location_saved": "✅ موقعیت ذخیره شد!",
        "btn.share_location": "📍 اشتراک موقعیت",
        "btn.skip_location": "⏭ رد کردن",

        # Delivery Type (Card 3)
        "order.delivery.type_prompt": "🚚 نوع تحویل را انتخاب کنید:",
        "btn.delivery.door": "🚪 تحویل درب منزل",
        "btn.delivery.dead_drop": "📦 گذاشتن در محل",
        "btn.delivery.pickup": "🏪 دریافت حضوری",
        "order.delivery.drop_instructions_prompt": "📝 محل گذاشتن سفارش را توضیح دهید (مثلاً 'نزد نگهبان در لابی'، 'زیر پادری اتاق ۴۰۵'):",
        "order.delivery.drop_photo_prompt": "📸 می\u200cخواهید عکسی از محل تحویل ارسال کنید؟ (اختیاری)",
        "order.delivery.drop_photo_saved": "✅ عکس محل تحویل ذخیره شد!",
        "btn.skip_drop_photo": "⏭ رد عکس",

        # PromptPay (Card 1)
        "order.payment_method.promptpay": "💳 PromptPay QR",
        "order.payment.promptpay.title": "💳 <b>پرداخت PromptPay</b>",
        "order.payment.promptpay.scan": "📱 کد QR را برای پرداخت اسکن کنید:",
        "order.payment.promptpay.upload_receipt": "📸 پس از پرداخت، لطفاً رسید/تصویر خود را آپلود کنید:",
        "order.payment.promptpay.receipt_received": "✅ رسید دریافت شد! در انتظار تأیید مدیر.",
        "order.payment.promptpay.receipt_invalid": "❌ لطفاً عکس رسید پرداخت خود را ارسال کنید.",
        "order.payment.promptpay.slip_verified": "✅ پرداخت به صورت خودکار تأیید شد! سفارش شما تأیید شده است.",
        "admin.order.verify_payment": "✅ تأیید پرداخت",
        "admin.order.payment_verified": "✅ پرداخت تأیید شد",

        # Delivery Chat (Card 13)
        "order.delivery.chat_unavailable": "❌ چت با راننده در دسترس نیست. گروه پیک پیکربندی نشده.",
        "order.delivery.chat_started": "💬 می\u200cتوانید با راننده خود پیام بدهید. متن، عکس یا موقعیت ارسال کنید.",
        "order.delivery.live_location_shared": "📍 راننده موقعیت زنده خود را به اشتراک گذاشته است! می\u200cتوانید تحویل خود را پیگیری کنید.",
        "order.delivery.chat_no_active_delivery": "❌ شما هیچ تحویل فعالی برای چت ندارید.",
        "order.delivery.chat_ended": "✅ چت با راننده پایان یافت.",
        "order.delivery.chat_message_sent": "✅ پیام به راننده ارسال شد.",
        "order.delivery.driver_no_active_order": "⚠️ هیچ سفارش فعالی برای ارسال این پیام وجود ندارد.",
        "btn.chat_with_driver": "💬 چت با راننده",
        "order.delivery.drop_gps_prompt": "📍 موقعیت GPS محل تحویل را با فشردن دکمه زیر ارسال کنید:",
        "order.delivery.drop_gps_saved": "✅ موقعیت GPS ذخیره شد!",
        "order.delivery.drop_media_prompt": "📸 عکس یا ویدیو از محل تحویل ارسال کنید (چند فایل مجاز است). وقتی تمام شد «تمام» را بزنید:",
        "order.delivery.drop_media_saved": "✅ {count} فایل ذخیره شد. بیشتر ارسال کنید یا «تمام» را بزنید.",
        "btn.share_drop_location": "📍 ارسال موقعیت",
        "btn.drop_media_done": "✅ تمام",
        "btn.skip_drop_media": "⏭ رد کردن",
        "btn.end_chat": "❌ پایان چت",

        # GPS tracking & chat session (Card 15)

        # === Bonus/Referral Application ===
        "order.bonus.available": "💰 <b>شما ${bonus_balance} پاداش معرفی دارید!</b>\n\n",
        "order.bonus.apply_question": "آیا می\u200cخواهید پاداش معرفی را در این سفارش اعمال کنید؟",
        "order.bonus.amount_positive_error": "❌ لطفاً مبلغ مثبت وارد کنید.",
        "order.bonus.amount_too_high": "❌ مبلغ بیش از حد. حداکثر قابل اعمال: ${max_applicable}\nلطفاً مبلغ معتبر وارد کنید:",
        "order.bonus.invalid_amount": "❌ مبلغ نامعتبر. لطفاً یک عدد وارد کنید (مثلاً 5.50):",
        "order.bonus.insufficient": "❌ موجودی پاداش کافی نیست. لطفاً دوباره امتحان کنید.",
        "order.bonus.enter_amount": "مبلغ پاداشی که می\u200cخواهید اعمال کنید را وارد کنید (حداکثر ${max_applicable}):\n\nیا با کلیک دکمه زیر تمام پاداش موجود را استفاده کنید.",

        # === Payment Instructions ===
        "order.payment.system_unavailable": "❌ <b>سیستم پرداخت موقتاً در دسترس نیست</b>\n\nآدرس Bitcoin موجود نیست. لطفاً با پشتیبانی تماس بگیرید.",
        "order.payment.customer_not_found": "❌ اطلاعات مشتری یافت نشد. لطفاً دوباره امتحان کنید.",
        "order.payment.creation_error": "❌ خطا در ایجاد سفارش. لطفاً دوباره امتحان کنید یا با پشتیبانی تماس بگیرید.",

        # === Order Summary/Total ===
        "order.summary.title": "📦 <b>خلاصه سفارش</b>\n\n",
        "order.summary.cart_total": "جمع سبد خرید: ${cart_total}",
        "order.summary.bonus_applied": "پاداش اعمال\u200cشده: -${bonus_applied}",
        "order.summary.final_amount": "مبلغ نهایی: ${final_amount}",

        # === Inventory/Reservation ===
        "order.inventory.unable_to_reserve": "❌ <b>امکان رزرو محصولات وجود ندارد</b>\n\nمحصولات زیر به مقدار درخواستی موجود نیستند:\n\n{unavailable_items}\n\nلطفاً سبد خرید خود را تنظیم کنید و دوباره امتحان کنید.",

        # === My Orders View ===
        "myorders.title": "📦 <b>سفارش\u200cهای من</b>\n\n",
        "myorders.total": "کل سفارش\u200cها: {count}",
        "myorders.active": "⏳ سفارش\u200cهای فعال: {count}",
        "myorders.delivered": "✅ تحویل\u200cشده: {count}",
        "myorders.select_category": "یک دسته\u200cبندی برای مشاهده سفارش\u200cها انتخاب کنید:",
        "myorders.active_orders": "⏳ سفارش\u200cهای فعال",
        "myorders.delivered_orders": "✅ سفارش\u200cهای تحویل\u200cشده",
        "myorders.all_orders": "📋 همه سفارش\u200cها",
        "myorders.no_orders_yet": "هنوز سفارشی ثبت نکرده\u200cاید.\n\nفروشگاه را مرور کنید تا خرید را شروع کنید!",
        "myorders.browse_shop": "🛍️ رفتن به فروشگاه",
        "myorders.back": "◀️ بازگشت",
        "myorders.all_title": "📋 همه سفارش\u200cها",
        "myorders.active_title": "⏳ سفارش\u200cهای فعال",
        "myorders.delivered_title": "✅ سفارش\u200cهای تحویل\u200cشده",
        "myorders.invalid_filter": "فیلتر نامعتبر",
        "myorders.not_found": "سفارشی یافت نشد.",
        "myorders.back_to_menu": "◀️ بازگشت به منوی سفارش\u200cها",
        "myorders.select_details": "سفارشی را برای مشاهده جزئیات انتخاب کنید:",
        "myorders.order_not_found": "سفارش یافت نشد",

        # === Order Details Display ===
        "myorders.detail.title": "📦 <b>جزئیات سفارش #{order_code}</b>\n\n",
        "myorders.detail.status": "📊 <b>وضعیت:</b> {status}\n",
        "myorders.detail.subtotal": "💵 <b>جمع فرعی:</b> ${subtotal}\n",
        "myorders.detail.bonus_applied": "🎁 <b>پاداش اعمال\u200cشده:</b> ${bonus}\n",
        "myorders.detail.final_price": "💰 <b>قیمت نهایی:</b> ${total}\n",
        "myorders.detail.total_price": "💰 <b>قیمت کل:</b> ${total}\n",
        "myorders.detail.payment_method": "💳 <b>روش پرداخت:</b> {method}\n",
        "myorders.detail.ordered": "📅 <b>تاریخ سفارش:</b> {date}\n",
        "myorders.detail.delivery_time": "🚚 <b>تحویل برنامه\u200cریزی\u200cشده:</b> {time}\n",
        "myorders.detail.completed": "✅ <b>تکمیل\u200cشده:</b> {date}\n",
        "myorders.detail.items": "\n📦 <b>محصولات:</b>\n{items}\n",
        "myorders.detail.delivery_info": "\n📍 <b>اطلاعات تحویل:</b>\n{address}\n{phone}\n{note}",

        # === Help System ===
        "help.prompt": "📧 <b>نیاز به کمک دارید؟</b>\n\n",
        "help.describe_issue": "لطفاً مشکل یا سؤال خود را شرح دهید تا مستقیماً به مدیر ارسال شود.\n\nپیام خود را در زیر تایپ کنید:",
        "help.admin_not_configured": "❌ متأسفیم، تماس با مدیر پیکربندی نشده. لطفاً بعداً دوباره امتحان کنید.",
        "help.admin_notification_title": "📧 <b>درخواست کمک جدید</b>\n\n",
        "help.admin_notification_from": "<b>از:</b> @{username} (ID: {user_id})\n",
        "help.admin_notification_message": "<b>پیام:</b>\n{message}",
        "help.sent_success": "✅ {auto_message}",
        "help.sent_error": "❌ ارسال پیام به مدیر ناموفق بود: {error}\n\nلطفاً بعداً دوباره امتحان کنید.",
        "help.cancelled": "درخواست کمک لغو شد.",

        # === Admin Order Notifications ===
        "admin.order.action_required_title": "⏳ <b>نیاز به اقدام:</b>",
        "admin.order.address_label": "آدرس: {address}",
        "admin.order.amount_to_collect_label": "<b>مبلغ دریافتی: ${amount} {currency}</b>",
        "admin.order.amount_to_receive_label": "<b>مبلغ دریافتنی: ${amount} {currency}</b>",
        "admin.order.awaiting_payment_status": "⏳ در انتظار تأیید پرداخت...",
        "admin.order.bitcoin_address_label": "آدرس Bitcoin: <code>{address}</code>",
        "admin.order.bonus_applied_label": "پاداش اعمال\u200cشده: <b>-${amount}</b>",
        "admin.order.customer_label": "مشتری: {username} (ID: {id})",
        "admin.order.delivery_info_title": "<b>اطلاعات تحویل:</b>",
        "admin.order.items_title": "<b>محصولات:</b>",
        "admin.order.new_bitcoin_order": "🔔 <b>سفارش Bitcoin جدید دریافت شد</b>",
        "admin.order.new_cash_order": "🔔 <b>سفارش نقدی جدید دریافت شد</b> 💵",
        "admin.order.note_label": "یادداشت: {note}",
        "admin.order.order_label": "سفارش: <b>{code}</b>",
        "admin.order.payment_cash": "پرداخت در محل",
        "admin.order.payment_method_label": "روش پرداخت: <b>{method}</b>",
        "admin.order.phone_label": "تلفن: {phone}",
        "admin.order.subtotal_label": "جمع فرعی: <b>${amount} {currency}</b>",
        "admin.order.use_cli_confirm": "برای تأیید سفارش و تنظیم زمان تحویل از CLI استفاده کنید:\n<code>python bot_cli.py order --order-code {code} --status-confirmed --delivery-time \"YYYY-MM-DD HH:MM\"</code>",
        "btn.admin.back_to_panel": "🔙 بازگشت به پنل مدیریت",
        "btn.admin.create_refcode": "➕ ایجاد کد مرجع",
        "btn.admin.list_refcodes": "📋 لیست همه کدها",
        "btn.back_to_orders": "◀️ بازگشت به سفارش\u200cها",
        "btn.create_reference_code": "➕ ایجاد کد مرجع",
        "btn.my_reference_codes": "🔑 کدهای مرجع من",
        "btn.need_help": "❓ نیاز به کمک؟",
        "cart.item.price_format": "  قیمت: {price} {currency} × {quantity}",
        "cart.item.subtotal_format": "  جمع فرعی: {subtotal} {currency}",
        "cart.item.modifiers": "  تغییرات: {modifiers}",
        "cart.total_format": "<b>جمع کل: {total} {currency}</b>",
        "cart.add_cancelled": "افزودن لغو شد",
        "modifier.select_title": "انتخاب {label}:",
        "modifier.selected": "انتخاب شد: {choice}",
        "modifier.required": "(الزامی)",
        "modifier.optional": "(اختیاری)",
        "modifier.done": "تمام",
        "modifier.price_extra": "+{price}",
        "modifier.cancelled": "انتخاب تغییرات لغو شد.",
        "help.pending_order.contact_support": "از دستور /help برای تماس با پشتیبانی استفاده کنید.",
        "help.pending_order.issues_title": "<b>مشکلی دارید؟</b>",
        "help.pending_order.status": "سفارش شما در انتظار پرداخت است.",
        "help.pending_order.step1": "1. مبلغ دقیق را به آدرس Bitcoin نشان\u200cداده\u200cشده ارسال کنید",
        "help.pending_order.step2": "2. منتظر تأیید بلاک\u200cچین بمانید (معمولاً ۱۰ تا ۶۰ دقیقه)",
        "help.pending_order.step3": "3. مدیر پرداخت شما را تأیید و زمان تحویل را تعیین می\u200cکند",
        "help.pending_order.step4": "4. کالای شما توسط پیک تحویل داده خواهد شد.",
        "help.pending_order.title": "❓ <b>نیاز به کمک درباره سفارش؟</b>",
        "help.pending_order.what_to_do_title": "<b>چه باید کرد:</b>",
        "myorders.detail.bitcoin_address_label": "آدرس Bitcoin:",
        "myorders.detail.bitcoin_admin_confirm": "پس از پرداخت، مدیر ما سفارش شما را تأیید خواهد کرد.",
        "myorders.detail.bitcoin_send_instruction": "⚠️ لطفاً <b>{amount} {currency}</b> Bitcoin به این آدرس ارسال کنید.",
        "myorders.detail.cash_awaiting_confirm": "سفارش شما در انتظار تأیید مدیر است.",
        "myorders.detail.cash_payment_courier": "پرداخت هنگام تحویل به پیک انجام خواهد شد.",
        "myorders.detail.cash_title": "💵 پرداخت در محل",
        "myorders.detail.cash_will_notify": "هنگام تأیید سفارش و تعیین زمان تحویل به شما اطلاع داده خواهد شد.",
        "myorders.detail.confirmed_title": "✅ <b>سفارش تأیید شد!</b>",
        "myorders.detail.delivered_thanks_message": "از خرید شما متشکریم! امیدواریم دوباره شما را ببینیم! 🙏",
        "myorders.detail.delivered_title": "📦 <b>سفارش تحویل داده شد!</b>",
        "myorders.detail.payment_info_title": "<b>اطلاعات پرداخت:</b>",
        "myorders.detail.preparing_message": "سفارش شما در حال آماده\u200cسازی برای تحویل است.",
        "myorders.detail.scheduled_delivery_label": "تحویل برنامه\u200cریزی\u200cشده: <b>{time}</b>",
        "myorders.order_summary_format": "{status_emoji} {code} - {items_count} محصول - {total} {currency}",
        "order.bonus.available_label": "پاداش موجود: <b>${amount}</b>",
        "order.bonus.choose_amount_hint": "می\u200cتوانید مقدار مورد نظر را انتخاب کنید (حداکثر ${max_amount})",
        "order.bonus.enter_amount_title": "💵 <b>مبلغ پاداش برای اعمال را وارد کنید</b>",
        "order.bonus.max_applicable_label": "حداکثر قابل اعمال: <b>${amount}</b>",
        "order.bonus.order_total_label": "جمع سفارش: <b>${amount} {currency}</b>",
        "order.info.view_status_hint": "💡 می\u200cتوانید هر زمان وضعیت سفارش خود را با دستور /orders مشاهده کنید.",
        "order.payment.bitcoin.address_title": "<b>آدرس پرداخت Bitcoin:</b>",
        "order.payment.bitcoin.admin_confirm": "• پس از پرداخت، مدیر ما سفارش شما را تأیید خواهد کرد",
        "order.payment.bitcoin.delivery_title": "<b>تحویل:</b>",
        "order.payment.bitcoin.important_title": "⚠️ <b>مهم:</b>",
        "order.payment.bitcoin.items_title": "<b>محصولات:</b>",
        "order.payment.bitcoin.need_help": "نیاز به کمک دارید؟ از /help برای تماس با پشتیبانی استفاده کنید.",
        "order.payment.bitcoin.one_time_address": "• این آدرس فقط برای یک\u200cبار مصرف است",
        "order.payment.bitcoin.order_code": "سفارش: <b>{code}</b>",
        "order.payment.bitcoin.send_exact": "• مبلغ دقیق نشان\u200cداده\u200cشده را ارسال کنید",
        "order.payment.bitcoin.title": "💳 <b>دستورالعمل پرداخت Bitcoin</b>",
        "order.payment.bitcoin.total_amount": "مبلغ کل: <b>{amount} {currency}</b>",

        # Crypto payment (Card 18) — generic strings for all coins
        "crypto.payment.title": "💳 <b>{coin_name} Payment</b>",
        "crypto.payment.order_code": "Order: <b>{code}</b>",
        "crypto.payment.total_fiat": "Total: <b>{amount} {currency}</b>",
        "crypto.payment.rate": "Rate: 1 {coin} = {rate} {currency}",
        "crypto.payment.amount_due": "Amount due: <b>{crypto_amount} {coin}</b>",
        "crypto.payment.address": "<b>Send to this address:</b>\n<code>{address}</code>",
        "crypto.payment.send_exact": "• Send EXACTLY this amount",
        "crypto.payment.one_time": "• This address is for ONE-TIME use",
        "crypto.payment.auto_confirm": "• Your order will be automatically confirmed once the payment is detected on-chain.",
        "crypto.payment.waiting": "⏳ Waiting for payment...\nThis address expires in {timeout} minutes.",
        "crypto.payment.no_address": "❌ No {coin} addresses available. Please contact support or choose another payment method.",
        "crypto.payment_detected": (
            "✅ <b>Payment detected!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "⏳ Waiting for confirmations..."
        ),
        "crypto.payment_confirmed": (
            "✅ <b>Payment confirmed!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "Your order is now being processed."
        ),
        "crypto.payment_expired": "⏰ Payment window for your {coin} order ({order_code}) has expired. Please place a new order.",

        "order.payment.cash.admin_contact": "مدیر به زودی با شما تماس خواهد گرفت.",
        "order.payment.cash.after_confirm": "پس از تأیید، زمان تحویل به شما اطلاع داده خواهد شد.",
        "order.payment.cash.created": "سفارش {code} شما ایجاد شد و در انتظار تأیید مدیر است.",
        "order.payment.cash.important": "⏳ <b>مهم:</b> سفارش برای مدت محدودی رزرو شده است.",
        "order.payment.cash.items_title": "محصولات:",
        "order.payment.cash.payment_to_courier": "پرداخت هنگام تحویل به پیک انجام خواهد شد.",
        "order.payment.cash.title": "💵 <b>پرداخت در محل</b>",
        "order.payment.cash.total": "جمع کل: {amount}",
        "order.payment.error_general": "❌ خطا در ایجاد سفارش. لطفاً دوباره امتحان کنید یا با پشتیبانی تماس بگیرید.",
        "order.summary.total_label": "<b>جمع کل: {amount} {currency}</b>",
        "order.payment.bonus_applied_label": "پاداش اعمال\u200cشده: <b>-{amount} {currency}</b>",
        "order.payment.cash.amount_with_bonus": "<b>مبلغ قابل پرداخت در تحویل: {amount} {currency}</b>",
        "order.payment.cash.total_label": "<b>جمع کل پرداخت در تحویل: {amount} {currency}</b>",
        "order.payment.final_amount_label": "<b>مبلغ نهایی پرداخت: {amount} {currency}</b>",
        "order.payment.order_label": "📋 <b>سفارش: {code}</b>",
        "order.payment.subtotal_label": "جمع فرعی: <b>{amount} {currency}</b>",
        "order.payment.total_amount_label": "<b>مبلغ کل: {amount} {currency}</b>",

        # === Card 9: Kitchen & Delivery Workflow ===
        "admin.menu.orders": "📋 سفارشات",
        "admin.orders.list_title": "📋 <b>سفارشات</b>",
        "admin.orders.empty": "سفارشی یافت نشد",
        "admin.orders.filter_status": "فیلتر بر اساس وضعیت",
        "admin.orders.filter_all": "📋 همه سفارشات",
        "admin.orders.filter_active": "🔄 فعال",
        "admin.orders.detail": (
            "📋 <b>سفارش #{order_id}</b> ({order_code})\n"
            "👤 خریدار: {buyer_id}\n"
            "💰 مجموع: {total}\n"
            "📦 وضعیت: {status}\n"
            "📅 ایجاد شده: {created_at}\n"
            "📍 آدرس: {address}\n"
            "📞 تلفن: {phone}"
        ),
        "admin.orders.status_changed": "وضعیت سفارش #{order_id} به <b>{new_status}</b> تغییر کرد",
        "admin.orders.invalid_transition": "امکان تغییر وضعیت از {current} به {new} وجود ندارد",
        "kitchen.order_received": (
            "🍳 <b>سفارش جدید #{order_id}</b> ({order_code})\n\n"
            "{items}\n\n"
            "💰 مجموع: {total}\n"
            "📍 آدرس: {address}\n"
            "📞 تلفن: {phone}"
        ),
        "rider.order_ready": (
            "🚗 <b>سفارش آماده #{order_id}</b> ({order_code})\n\n"
            "💰 مجموع: {total}\n"
            "📍 آدرس: {address}\n"
            "📞 تلفن: {phone}"
        ),
        "order.status.preparing": "🍳 سفارش #{order_code} شما در حال آماده‌سازی است",
        "order.status.ready": "✅ سفارش #{order_code} شما آماده تحویل است",
        "order.status.out_for_delivery": "🚗 سفارش #{order_code} شما در راه است",
        "order.status.delivered_notify": "📦 سفارش #{order_code} شما تحویل داده شد",
        "kitchen.btn.start_preparing": "🍳 شروع آماده‌سازی",
        "kitchen.btn.mark_ready": "✅ آماده",
        "rider.btn.picked_up": "📦 تحویل گرفته شد",
        "rider.btn.delivered": "✅ تحویل داده شد",

        # Delivery Photo Proof (Card 4)
        "delivery.photo.required": "برای تحویل در نقطه تحویل عکس لازم است",
        "delivery.photo.upload_prompt": "لطفاً عکس تحویل را آپلود کنید",
        "delivery.photo.received": "عکس تحویل ذخیره شد",
        "delivery.photo.sent_to_customer": "عکس تحویل به مشتری ارسال شد",
        "delivery.photo.customer_notification": "سفارش {order_code} شما تحویل داده شد! این عکس تأیید تحویل است.",

        # === New Feature Strings ===

        # === Restaurant Feature Strings ===
        "admin.goods.add.allergen.dairy": "Dairy",
        "admin.goods.add.allergen.eggs": "Eggs",
        "admin.goods.add.allergen.fish": "Fish",
        "admin.goods.add.allergen.gluten": "Gluten",
        "admin.goods.add.allergen.nuts": "Nuts",
        "admin.goods.add.allergen.sesame": "Sesame",
        "admin.goods.add.allergen.shellfish": "Shellfish",
        "admin.goods.add.allergen.soy": "Soy",
        "admin.goods.add.allergens.done": "✅ Done",
        "admin.goods.add.allergens.skip": "⏭ No Allergens",
        "admin.goods.add.availability.invalid": "❌ Invalid format. Use HH:MM-HH:MM (e.g. 06:00-22:00)",
        "admin.goods.add.availability.skip": "⏭ All Day",
        "admin.goods.add.daily_limit.invalid": "❌ Enter a positive number.",
        "admin.goods.add.daily_limit.skip": "⏭ Unlimited",
        "admin.goods.add.modifier.add_another_group": "➕ Another Group",
        "admin.goods.add.modifier.add_group": "➕ Add Modifier Group",
        "admin.goods.add.modifier.add_option": "➕ Add Option",
        "admin.goods.add.modifier.all_done": "✅ Finish",
        "admin.goods.add.modifier.finish": "✅ Finish (No Modifiers)",
        "admin.goods.add.modifier.group_added": "✅ Group added! Add another group or finish.",
        "admin.goods.add.modifier.group_name": "Enter modifier group name (e.g. Spice Level):",
        "admin.goods.add.modifier.group_type": "Select type for this group:",
        "admin.goods.add.modifier.option_added": "✅ Option added! Add another or press Done.",
        "admin.goods.add.modifier.option_label": "Enter option label (e.g. Mild, Extra Cheese):",
        "admin.goods.add.modifier.option_price": "Enter price adjustment for this option (0 for free):",
        "admin.goods.add.modifier.options_done": "✅ Done with Options",
        "admin.goods.add.modifier.paste_json": "📋 Paste JSON",
        "admin.goods.add.modifier.required_no": "⭕ Optional",
        "admin.goods.add.modifier.required_yes": "✅ Required",
        "admin.goods.add.modifier.type_multi": "Multi Choice",
        "admin.goods.add.modifier.type_single": "Single Choice",
        "admin.goods.add.photo.done": "✅ Done",
        "admin.goods.add.photo.received": "✅ Media received! Send more or press Done.",
        "admin.goods.add.photo.send_more": "Send more photos/videos or press Done:",
        "admin.goods.add.photo.skip": "⏭ Skip Photos",
        "admin.goods.add.prep_time.invalid": "❌ Enter a positive number.",
        "admin.goods.add.prep_time.skip": "⏭ Skip",
        "admin.goods.add.prompt.allergens": "⚠️ Select allergens (tap to toggle, then Done):",
        "admin.goods.add.prompt.availability": "🕐 Enter availability hours (e.g. 06:00-22:00) or press Skip for all-day:",
        "admin.goods.add.prompt.daily_limit": "📊 Enter daily limit (max units per day) or press Skip for unlimited:",
        "admin.goods.add.prompt.modifier_group": "Add a modifier group (e.g. Spice Level, Extras)?",
        "admin.goods.add.prompt.photo": "📸 Send a photo or video of this item (or press Skip):",
        "admin.goods.add.prompt.prep_time": "⏱ Enter prep time in minutes (or press Skip):",
        "admin.goods.toggle.active_off": "🚫 {item}: Deactivated",
        "admin.goods.toggle.active_on": "✅ {item}: Activated",
        "admin.goods.toggle.sold_out_off": "✅ {item}: Back in stock",
        "admin.goods.toggle.sold_out_on": "❌ {item}: Marked SOLD OUT",
        "btn.view_gallery": "📸 Gallery ({count})",
        "kitchen.order.modifier_detail": "    ↳ {modifiers}",
        "kitchen.order.prep_time": "⏱ Est. prep: {minutes} min",
        "kitchen.order.ready_by": "🕐 Ready by: {time}",
        "order.estimated_ready": "⏱ Estimated ready in ~{minutes} min",
        "shop.item.allergens": "⚠️ Allergens: {allergens}",
        "shop.item.availability": "🕐 Available: {from_time} - {until_time}",
        "shop.item.calories": "🔥 {calories} cal",
        "shop.item.daily_remaining": "📊 Today: {remaining}/{limit} left",
        "shop.item.no_gallery": "No gallery for this item.",
        "shop.item.type_product": "📦 نوع: محصول بسته‌بندی شده",
        "shop.item.type_prepared": "🍳 نوع: تازه تهیه می‌شود",
        "shop.item.prep_time": "⏱ Prep: ~{minutes} min",
        "shop.item.sold_out": "❌ Sold out today",
        "admin.accounting.export_payments": "📥 Payment Reconciliation",
        "admin.accounting.export_products": "📥 Revenue by Product",
        "admin.accounting.export_sales": "📥 Export Sales CSV",
        "admin.accounting.export_sent": "✅ Report exported.",
        "admin.accounting.no_data": "No data for this period.",
        "admin.accounting.summary": "📊 <b>Revenue Summary ({period})</b>\n\n💰 Revenue: {total} {currency}\n📦 Orders: {orders}\n📈 Avg: {avg} {currency}\n\n<b>By Payment:</b>\n{payments}\n\n<b>Top Products:</b>\n{products}",
        "admin.accounting.summary_all": "📊 All Time",
        "admin.accounting.summary_month": "📊 This Month",
        "admin.accounting.summary_today": "📊 Today",
        "admin.accounting.summary_week": "📊 This Week",
        "admin.accounting.title": "📊 <b>Accounting & Reports</b>",
        "admin.coupon.create": "➕ Create Coupon",
        "admin.coupon.created": "✅ Coupon <b>{code}</b> created!\nType: {type}\nValue: {value}\nMin order: {min_order}\nMax uses: {max_uses}\nExpires: {expiry}",
        "admin.coupon.detail": "🎟 <b>{code}</b>\nType: {type}\nValue: {value}\nMin Order: {min_order}\nMax Uses: {max_uses}\nUsed: {used}\nStatus: {status}\nExpires: {expiry}",
        "admin.coupon.empty": "No coupons found.",
        "admin.coupon.enter_code": "Enter coupon code (or type <b>auto</b> for random):",
        "admin.coupon.enter_expiry": "Enter expiry in days (or <b>skip</b> for no expiry):",
        "admin.coupon.enter_max_uses": "Enter max total uses (or <b>skip</b> for unlimited):",
        "admin.coupon.enter_min_order": "Enter minimum order amount (or <b>skip</b>):",
        "admin.coupon.enter_value": "Enter discount value ({type}):",
        "admin.coupon.invalid_value": "❌ Invalid value. Enter a number.",
        "admin.coupon.list_active": "📋 Active Coupons",
        "admin.coupon.list_all": "📋 All Coupons",
        "admin.coupon.select_type": "Select discount type:",
        "admin.coupon.title": "🎟 <b>Coupon Management</b>",
        "admin.coupon.toggle_activate": "✅ Activate",
        "admin.coupon.toggle_deactivate": "❌ Deactivate",
        "admin.coupon.toggled": "✅ Coupon {code} is now {status}.",
        "admin.coupon.type_fixed": "💰 Fixed Amount",
        "admin.coupon.type_percent": "📊 Percentage (%)",
        "admin.menu.accounting": "📊 Accounting",
        "admin.menu.coupons": "🎟 Coupons",
        "admin.menu.segment_broadcast": "📣 Targeted Broadcast",
        "admin.menu.stores": "🏪 Stores",
        "admin.menu.tickets": "🎫 Tickets",
        "admin.menu.ai_assistant": "🤖 AI Assistant",
        "admin.segment.all_users": "👥 All Users",
        "admin.segment.count": "📊 Segment: <b>{segment}</b>\nUsers: <b>{count}</b>\n\nType your broadcast message:",
        "admin.segment.empty": "No users in this segment.",
        "admin.segment.high_spenders": "💰 High Spenders",
        "admin.segment.inactive": "😴 Inactive (30+ days)",
        "admin.segment.new_users": "🆕 New Users (7d)",
        "admin.segment.recent_buyers": "🛒 Recent Buyers (7d)",
        "admin.segment.sent": "✅ Sent to {sent}/{total} ({segment}).",
        "admin.segment.title": "📣 <b>Targeted Broadcast</b>\n\nSelect segment:",
        "admin.store.add": "➕ Add Store",
        "admin.store.address_prompt": "Enter store address (or <b>skip</b>):",
        "admin.store.btn_default": "⭐ Set as Default",
        "admin.store.created": "✅ Store <b>{name}</b> created!",
        "admin.store.detail": "🏪 <b>{name}</b>\nStatus: {status}\nDefault: {default}\nAddress: {address}\nLocation: {location}\nPhone: {phone}",
        "admin.store.empty": "No stores configured.",
        "admin.store.location_prompt": "Send GPS location (or type <b>skip</b>):",
        "admin.store.name_exists": "Store with this name already exists.",
        "admin.store.name_prompt": "Enter store name:",
        "admin.store.set_default": "✅ {name} set as default store.",
        "admin.store.title": "🏪 <b>Store Management</b>",
        "admin.store.toggle_activate": "✅ Activate",
        "admin.store.toggle_deactivate": "❌ Deactivate",
        "admin.store.toggled": "✅ Store {name} is now {status}.",
        "admin.ticket.detail": "🎫 <b>Ticket #{code}</b>\nUser: {user_id}\nStatus: {status}\nPriority: {priority}\nSubject: {subject}\nCreated: {date}",
        "admin.ticket.empty": "No open tickets.",
        "admin.ticket.list": "Open/In Progress Tickets:",
        "admin.ticket.reply_prompt": "Reply to ticket #{code}:",
        "admin.ticket.resolved": "✅ Ticket #{code} resolved.",
        "admin.ticket.title": "🎫 <b>Support Tickets</b>",
        "btn.admin.reply_ticket": "💬 Reply",
        "btn.admin.resolve_ticket": "✅ Resolve",
        "btn.apply_coupon": "🎟 Apply Coupon",
        "btn.close_ticket": "✖ Close Ticket",
        "btn.create_ticket": "➕ New Ticket",
        "btn.create_ticket_for_order": "🎫 Support Ticket",
        "btn.invoice": "🧾 Receipt",
        "btn.my_tickets": "🎫 Support",
        "btn.reorder": "🔄 Reorder",
        "btn.reply_ticket": "💬 Reply",
        "btn.review_order": "⭐ Leave Review",
        "btn.search": "🔍 Search",
        "btn.skip_coupon": "⏭ Skip Coupon",
        "coupon.already_used": "❌ You already used this coupon.",
        "coupon.applied": "✅ Coupon applied! Discount: -{discount} {currency}",
        "coupon.enter_code": "🎟 Enter coupon code (or press Skip):",
        "coupon.expired": "❌ This coupon has expired.",
        "coupon.invalid": "❌ Invalid or expired coupon code.",
        "coupon.max_uses_reached": "❌ Coupon usage limit reached.",
        "coupon.min_order_not_met": "❌ Min order of {min_order} required.",
        "coupon.not_yet_valid": "❌ This coupon is not yet valid.",
        "invoice.not_available": "Receipt not available.",
        "reorder.success": "✅ Added {added} item(s) to cart. {skipped} item(s) unavailable.",
        "review.already_reviewed": "You have already reviewed this order.",
        "review.comment_prompt": "You rated {rating}/5 ⭐\n\nAdd a comment? Type or press Skip:",
        "review.detail": "⭐{rating}/5 — {comment}",
        "review.item_rating": "⭐ <b>{item}</b>: {avg:.1f}/5 ({count} reviews)",
        "review.no_reviews": "No reviews yet.",
        "review.prompt": "⭐ <b>Rate your order #{order_code}</b>\n\nSelect your rating:",
        "review.rate_1": "⭐",
        "review.rate_2": "⭐⭐",
        "review.rate_3": "⭐⭐⭐",
        "review.rate_4": "⭐⭐⭐⭐",
        "review.rate_5": "⭐⭐⭐⭐⭐",
        "review.skip_comment": "⏭ Skip",
        "review.thanks": "✅ Thank you for your review! ({rating}/5 ⭐)",
        "search.no_results": "❌ No products found. Try different keywords.",
        "search.prompt": "🔍 Enter product name or keyword to search:",
        "search.result_count": "Found {count} product(s):\n",
        "search.results_title": "🔍 <b>Search results for:</b> {query}\n\n",
        "ticket.admin_replied": "💬 Admin replied to ticket #{code}:\n{text}",
        "ticket.closed": "✅ Ticket closed.",
        "ticket.created": "✅ Ticket <b>#{code}</b> created!",
        "ticket.message_format": "<b>{role}</b> ({date}):\n{text}\n",
        "ticket.message_prompt": "Describe your issue:",
        "ticket.no_tickets": "No support tickets.",
        "ticket.reply_prompt": "Type your reply:",
        "ticket.reply_sent": "✅ Reply sent.",
        "ticket.resolved_notification": "✅ Ticket #{code} resolved!",
        "ticket.status.closed": "⚫ Closed",
        "ticket.status.in_progress": "🔵 In Progress",
        "ticket.status.open": "🟢 Open",
        "ticket.status.resolved": "✅ Resolved",
        "ticket.subject_prompt": "Enter the subject:",
        "ticket.title": "🎫 <b>Support Tickets</b>",
        "ticket.view_title": "🎫 <b>Ticket #{code}</b>\nStatus: {status}\nSubject: {subject}\nCreated: {date}",

        # Delivery GPS (Card 15)
        "delivery.gps.prompt": "📍 سفارش {order_code} شما در راه است!\n\nبه راننده کمک کنید سریع‌تر شما را پیدا کند — موقعیت خود را به اشتراک بگذارید:",
        "delivery.gps.btn_static": "📍 ارسال موقعیت",
        "delivery.gps.btn_live": "📡 موقعیت زنده",
        "delivery.gps.btn_skip": "⏭ رد شدن",
        "delivery.gps.static_sent": "✅ موقعیت شما به راننده ارسال شد.",
        "delivery.gps.live_started": "📡 موقعیت زنده فعال شد! راننده شما را در لحظه ردیابی می‌کند.",
        "delivery.gps.skipped": "⏭ موقعیت رد شد. راننده از آدرس سفارش استفاده خواهد کرد.",
        "delivery.chat.session_closed": "⏹ این جلسه چت پایان یافته است. برای کمک با پشتیبانی تماس بگیرید.",
        "delivery.chat.post_delivery_open": "✅ تحویل داده شد! چت برای {minutes} دقیقه دیگر باز می‌ماند.",
        "delivery.chat.post_delivery_closed": "⏹ پنجره چت پس از تحویل بسته شد.",

        # === PDPA Privacy Policy ===
        "btn.privacy": "🔒 سیاست حریم خصوصی",
        "privacy.notice": (
            "🔒 <b>اطلاعیه حریم خصوصی (PDPA)</b>\n\n"
            "ما از قانون حفاظت از داده‌های شخصی تایلند (PDPA) پیروی می‌کنیم.\n\n"
            "<b>داده‌هایی که جمع‌آوری می‌کنیم:</b>\n"
            "• نام / تلفن / آدرس تحویل\n"
            "• جزئیات سفارش و سابقه\n"
            "• شناسه تلگرام\n\n"
            "<b>اهداف:</b>\n"
            "• انجام سفارش و تحویل (ضرورت قراردادی)\n"
            "• جلوگیری از تقلب و تأیید هویت\n"
            "• بازاریابی — فقط با رضایت جداگانه شما\n\n"
            "<b>نگهداری:</b> تا زمانی که درخواست حذف کنید، یا ۲ سال پس از آخرین سفارش\n\n"
            "<b>اشتراک داده:</b> رستوران‌ها، رانندگان تحویل، ارائه‌دهندگان پرداخت — فقط در صورت نیاز برای سفارش شما. "
            "ما هرگز داده‌های شما را نمی‌فروشیم.\n\n"
            "<b>حقوق شما طبق PDPA:</b>\n"
            "• دسترسی / اصلاح / حذف داده‌های شما\n"
            "• لغو رضایت (برای بازاریابی)\n"
            "• اعتراض به پردازش / درخواست قابلیت حمل داده\n"
            "• ارائه شکایت به PDPC\n\n"
            "<b>کنترل‌کننده داده:</b> {company}\n"
            "تماس: {email}\n\n"
            "با ادامه استفاده از این بات، شما این سیاست را تأیید و می‌پذیرید."
        ),
        "privacy.btn_full_policy": "📄 مطالعه سیاست کامل",
        "privacy.btn_accept": "✅ پذیرش و ادامه",
        "privacy.accepted": "✅ شما سیاست حریم خصوصی را پذیرفتید.",
        "privacy.already_accepted": "✅ شما قبلاً سیاست حریم خصوصی را پذیرفته‌اید.",
        "privacy.no_url": "صفحه سیاست حریم خصوصی کامل هنوز پیکربندی نشده است.",
    },
    "ps": {
        # === Common Buttons ===
        "btn.shop": "🏪 پلورنځی",
        "btn.rules": "📜 مقررات",
        "btn.profile": "👤 پروفایل",
        "btn.support": "🆘 ملاتړ",
        "btn.channel": "ℹ د خبرونو کانال",
        "btn.admin_menu": "🎛 د مدیر پینل",
        "btn.back": "⬅️ شاته",
        "btn.close": "✖ بندول",
        "btn.yes": "✅ هو",
        "btn.no": "❌ نه",
        "btn.check_subscription": "🔄 د ګډون کتنه",
        "btn.admin.ban_user": "🚫 کارن بندول",
        "btn.admin.unban_user": "✅ د کارن بندیز لرې کول",

        # === Admin Buttons (user management shortcuts) ===
        "btn.admin.promote": "⬆️ مدیر جوړول",
        "btn.admin.demote": "⬇️ د مدیریت لرې کول",
        "btn.admin.add_user_bonus": "🎁 د معرفي بونس ورزیاتول",

        # === Titles / Generic Texts ===
        "menu.title": "⛩️ اصلي مینو",
        "admin.goods.add.stock.error": "❌ د لومړني زیرمې په اضافه کولو کې تېروتنه: {error}",
        "admin.goods.stock.add_success": "✅ {quantity} واحده \"{item}\" ته اضافه شوې",
        "admin.goods.stock.add_units": "➕ واحدې اضافه کول",
        "admin.goods.stock.current_status": "اوسنی حالت",
        "admin.goods.stock.error": "❌ د زیرمې په مدیریت کې تېروتنه: {error}",
        "admin.goods.stock.insufficient": "❌ زیرمه کافي نه ده. یوازې {available} واحدې شتون لري.",
        "admin.goods.stock.invalid_quantity": "⚠️ ناسم مقدار. یو بشپړ عدد ولیکئ.",
        "admin.goods.stock.management_title": "د زیرمې مدیریت: {item}",
        "admin.goods.stock.negative_quantity": "⚠️ مقدار نشي کولی منفي وي.",
        "admin.goods.stock.no_products": "❌ تر اوسه پلورنځي کې محصول نشته",
        "admin.goods.stock.prompt.add_units": "د اضافه کیدونکو واحدو شمېر ولیکئ:",
        "admin.goods.stock.prompt.item_name": "د زیرمې مدیریت لپاره د محصول نوم ولیکئ:",
        "admin.goods.stock.prompt.remove_units": "د لرې کیدونکو واحدو شمېر ولیکئ:",
        "admin.goods.stock.prompt.set_exact": "دقیق د زیرمې مقدار ولیکئ:",
        "admin.goods.stock.redirect_message": "ℹ️ د زیرمې مدیریت اوس د «زیرمې مدیریت» مینو له لارې شتون لري",
        "admin.goods.stock.remove_success": "✅ {quantity} واحدې له \"{item}\" لرې شوې",
        "admin.goods.stock.remove_units": "➖ واحدې لرې کول",
        "admin.goods.stock.select_action": "عملیات وټاکئ",
        "admin.goods.stock.set_exact": "⚖️ دقیق مقدار ټاکل",
        "admin.goods.stock.set_success": "✅ د \"{item}\" زیرمه {quantity} واحدو ته وټاکل شوه",
        "admin.goods.stock.status_title": "📊 د زیرمې حالت:",
        "errors.invalid_item_name": "❌ ناسم د محصول نوم",
        "errors.invalid_language": "ناسمه ژبه",
        "shop.error.brand_required": "مهرباني وکړئ لومړی برانډ وټاکئ",
        "shop.error.branch_unavailable": "څانګه شتون نلري",
        "profile.caption": "👤 <b>پروفایل</b> — <a href='tg://user?id={id}'>{name}</a>",
        "rules.not_set": "❌ مقررات تر اوسه اضافه شوي نه دي",
        "admin.users.cannot_ban_owner": "❌ مالک نشي بندېدلی",
        "admin.users.ban.success": "✅ کارن {name} په بریالیتوب سره بند شو",
        "admin.users.ban.failed": "❌ د کارن بندول ناکام شو",
        "admin.users.ban.notify": "⛔ تاسو د مدیر لخوا بند شوي یاست",
        "admin.users.unban.success": "✅ د کارن {name} بندیز په بریالیتوب سره لرې شو",
        "admin.users.unban.failed": "❌ د کارن بندیز لرې کول ناکام شو",
        "admin.users.unban.notify": "✅ ستاسو بندیز د مدیر لخوا لرې شو",

        # === Profile ===
        "btn.referral": "🎲 د معرفي سیستم",
        "btn.purchased": "🎁 اخیستل شوي محصولات",
        "profile.referral_id": "👤 <b>معرف</b> — <code>{id}</code>",

        # === Subscription Flow ===
        "subscribe.prompt": "لومړی د خبرونو کانال کې ګډون وکړئ",

        # === Profile Info Lines ===
        "profile.id": "🆔 <b>پېژندنه</b> — <code>{id}</code>",
        "profile.bonus_balance": "💰 <b>د معرفي بونس:</b> ${bonus_balance}",
        "profile.purchased_count": "🎁 <b>اخیستل شوي محصولات</b> — {count} ټوټې",
        "profile.registration_date": "🕢 <b>د ثبت نېټه</b> — <code>{dt}</code>",

        # === Referral ===
        "referral.title": "💚 د معرفي سیستم",
        "referral.count": "د معرفیو شمېر: {count}",
        "referral.description": "📔 د معرفي سیستم تاسو ته پرته له پانګونې درآمد ترلاسه کولو امکان درکوي. خپل شخصي لینک شریک کړئ او د خپلو معرفي شویو د شارژ څخه {percent}% ترلاسه کړئ.",
        "btn.view_referrals": "👥 زما معرفي شوي",
        "btn.view_earnings": "💰 زما عاید",

        "referrals.list.title": "👥 ستاسو معرفي شوي:",
        "referrals.list.empty": "تاسو تر اوسه فعال معرفي شوي نه لرئ",
        "referrals.item.format": "ID: {telegram_id} | عاید: {total_earned} {currency}",

        "referral.earnings.title": "💰 د معرفي شوي <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>) څخه عاید:",
        "referral.earnings.empty": "تر اوسه د دې معرفي شوي <code>{id}</code> (<a href='tg://user?id={id}'>{name}</a>) څخه عاید نشته",
        "referral.earning.format": "{amount} {currency} | {date} | (د {original_amount} {currency} څخه)",
        "referral.item.info": "💰 د عاید شمېره: <code>{id}</code>\n👤 معرفي شوی: <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>)\n🔢 مبلغ: {amount} {currency}\n🕘 نېټه: <code>{date}</code>\n💵 د {original_amount} {currency} واریز څخه",

        "referral.admin_bonus.info": "💰 د عاید شمېره: <code>{id}</code>\n🎁 <b>د مدیر بونس</b>\n🔢 مبلغ: {amount} {currency}\n🕘 نېټه: <code>{date}</code>",

        "all.earnings.title": "💰 ستاسو ټول معرفي عایدات:",
        "all.earnings.empty": "تاسو تر اوسه د معرفي عاید نه لرئ",
        "all.earning.format.admin": "{amount} {currency} د مدیر څخه | {date}",

        "referrals.stats.template": "📊 د معرفي سیستم احصایې:\n\n👥 فعال معرفي شوي: {active_count}\n💰 ټول عاید: {total_earned} {currency}\n📈 د معرفي شویو ټول شارژ: {total_original} {currency}\n🔢 د عایداتو شمېر: {earnings_count}",

        # === Admin: Main Menu ===
        "admin.menu.main": "⛩️ د مدیر مینو",
        "admin.menu.shop": "🛒 د پلورنځي مدیریت",
        "admin.menu.goods": "📦 د محصولاتو مدیریت",
        "admin.menu.categories": "📂 د کتګوریو مدیریت",
        "admin.menu.users": "👥 د کارنانو مدیریت",
        "admin.menu.broadcast": "📝 عمومي خبرتیا",
        "admin.menu.rights": "کافي اجازې نشته",

        # === Admin: User Management ===
        "admin.users.prompt_enter_id": "👤 د لیدلو / سمولو لپاره د کارن ID ولیکئ",
        "admin.users.invalid_id": "⚠️ مهرباني وکړئ یو سم عددي ID ولیکئ.",
        "admin.users.profile_unavailable": "❌ پروفایل شتون نه لري (داسې کارن هېڅکله شتون نه لري)",
        "admin.users.not_found": "❌ کارن ونه موندل شو",
        "admin.users.cannot_change_owner": "تاسو نشئ کولی د مالک رول بدل کړئ",
        "admin.users.referrals": "👥 <b>د کارن معرفي شوي</b> — {count}",
        "admin.users.btn.view_referrals": "👥 د کارن معرفي شوي",
        "admin.users.btn.view_earnings": "💰 د کارن عایدات",
        "admin.users.role": "🎛 <b>رول</b> — {role}",
        "admin.users.set_admin.success": "✅ رول {name} ته ټاکل شو",
        "admin.users.set_admin.notify": "✅ تاسو ته د مدیر رول ورکړل شو",
        "admin.users.remove_admin.success": "✅ د مدیر رول له {name} لرې شو",
        "admin.users.remove_admin.notify": "❌ ستاسو د مدیر رول لرې شو",
        "admin.users.bonus.prompt": "د بونس مبلغ په {currency} ولیکئ:",
        "admin.users.bonus.added": "✅ د {name} معرفي بونس په {amount} {currency} شارژ شو",
        "admin.users.bonus.added.notify": "🎁 تاسو ته د {amount} {currency} معرفي بونس ورکړل شو",
        "admin.users.bonus.invalid": "❌ ناسم مبلغ. د {min_amount} تر {max_amount} {currency} پورې عدد ولیکئ.",

        # === Admin: Shop Management Menu ===
        "admin.shop.menu.title": "⛩️ د پلورنځي مدیریت",
        "admin.shop.menu.statistics": "📊 احصایې",
        "admin.shop.menu.logs": "📁 لاګونه ښکاره کول",
        "admin.shop.menu.admins": "👮 مدیران",
        "admin.shop.menu.users": "👤 کارنان",

        # === Admin: Categories Management ===
        "admin.categories.menu.title": "⛩️ د کتګوریو مدیریت",
        "admin.categories.add": "➕ کتګوري اضافه کول",
        "admin.categories.rename": "✏️ د کتګورۍ نوم بدلول",
        "admin.categories.delete": "🗑 کتګوري ړنګول",
        "admin.categories.prompt.add": "د نوې کتګورۍ نوم ولیکئ:",
        "admin.categories.prompt.delete": "د ړنګولو لپاره د کتګورۍ نوم ولیکئ:",
        "admin.categories.prompt.rename.old": "د نوم بدلولو لپاره اوسنی د کتګورۍ نوم ولیکئ:",
        "admin.categories.prompt.rename.new": "نوی د کتګورۍ نوم ولیکئ:",
        "admin.categories.add.exist": "❌ کتګوري جوړه نه شوه (مخکې شتون لري)",
        "admin.categories.add.success": "✅ کتګوري جوړه شوه",
        "admin.categories.delete.not_found": "❌ کتګوري ونه ړنګول شوه (شتون نه لري)",
        "admin.categories.delete.success": "✅ کتګوري ړنګه شوه",
        "admin.categories.rename.not_found": "❌ کتګوري نشي تازه کیدلی (شتون نه لري)",
        "admin.categories.rename.exist": "❌ نوم نشي بدلیدلی (د دې نوم سره کتګوري شتون لري)",
        "admin.categories.rename.success": "✅ کتګوري \"{old}\" د \"{new}\" په نوم بدل شوه",

        # === Admin: Goods / Items Management (Add / List / Item Info) ===
        "admin.goods.add_position": "➕ محصول اضافه کول",
        "admin.goods.manage_stock": "➕ محصول ته توکي اضافه کول",
        "admin.goods.update_position": "📝 محصول سمول",
        "admin.goods.delete_position": "❌ محصول ړنګول",
        "admin.goods.add.prompt.type": "د محصول ډول وټاکئ:",
        "admin.goods.add.type.prepared": "🍳 د غوښتنې پر اساس جوړیږي (خوراک، مشروبات)",
        "admin.goods.add.type.product": "📦 بسته‌بندي شوی محصول (اوبه، سنکونه)",
        "admin.goods.add.prompt.name": "د محصول نوم ولیکئ",
        "admin.goods.add.name.exists": "❌ محصول جوړ نه شو (مخکې شتون لري)",
        "admin.goods.add.prompt.description": "د محصول تشریح ولیکئ:",
        "admin.goods.add.prompt.price": "د محصول بیه ولیکئ (عدد په {currency}):",
        "admin.goods.add.price.invalid": "⚠️ ناسمه بیه. مهرباني وکړئ یو عدد ولیکئ.",
        "admin.goods.add.prompt.category": "د محصول کتګوري ولیکئ:",
        "admin.goods.add.category.not_found": "❌ محصول جوړ نه شو (ناسمه کتګوري)",
        "admin.goods.position.not_found": "❌ توکي ونه موندل شول (دا محصول شتون نه لري)",
        "admin.goods.menu.title": "⛩️ د محصولاتو مدیریت مینو",
        "admin.goods.add.stock.prompt": "د اضافه کیدونکو توکو شمېر ولیکئ",
        "admin.goods.add.stock.invalid": "⚠️ ناسم مقدار. مهرباني وکړئ یو عدد ولیکئ.",
        "admin.goods.add.stock.negative": "⚠️ ناسم مقدار. یو مثبت عدد ولیکئ.",
        "admin.goods.add.result.created_with_stock": "✅ محصول {item_name} جوړ شو، {stock_quantity} د توکو شمېر ته اضافه شول.",

        # === Admin: Goods / Items Update Flow ===
        "admin.goods.update.position.invalid": "محصول ونه موندل شو.",
        "admin.goods.update.position.exists": "د دې نوم سره محصول مخکې شتون لري.",
        "admin.goods.update.prompt.name": "د محصول نوم ولیکئ",
        "admin.goods.update.not_exists": "❌ محصول نشي تازه کیدلی (شتون نه لري)",
        "admin.goods.update.prompt.new_name": "نوی د محصول نوم ولیکئ:",
        "admin.goods.update.prompt.description": "د محصول تشریح ولیکئ:",
        "admin.goods.update.success": "✅ محصول تازه شو",

        # === Admin: Goods / Items Delete Flow ===
        "admin.goods.delete.prompt.name": "د محصول نوم ولیکئ",
        "admin.goods.delete.position.not_found": "❌ محصول ونه ړنګول شو (شتون نه لري)",
        "admin.goods.delete.position.success": "✅ محصول ړنګ شو",

        # === Admin: Item Info ===
        "admin.goods.view_stock": "محصولات لیدل",

        # Admin Modifier Management (Card 8)
        "admin.goods.manage_modifiers": "🍳 اضافي",
        "admin.goods.modifiers.prompt": "ایا تاسو غواړئ اضافي (مسالې، اضافې، او نور) اضافه کړئ?",
        "admin.goods.modifiers.add_btn": "➕ اضافي اضافه کړئ",
        "admin.goods.modifiers.skip_btn": "⏭ تېر شئ",
        "admin.goods.modifiers.json_prompt": "د اضافي JSON سکیما ولګوئ:",
        "admin.goods.modifiers.invalid_json": "❌ ناسم JSON: {error}",
        "admin.goods.modifiers.select_item": "د اضافي تنظیم لپاره د محصول نوم ولیکئ:",
        "admin.goods.modifiers.edit_instructions": "عملیات غوره کړئ:",
        "admin.goods.modifiers.set_new": "📝 نوی تنظیم",
        "admin.goods.modifiers.clear": "🗑 ټول پاک کړئ",

        # === Admin: Logs ===
        "admin.shop.logs.caption": "د بوټ لاګونه",
        "admin.shop.logs.empty": "❗️ تر اوسه لاګ نشته",

        # === Group Notifications ===
        "shop.group.new_upload": "نوې زیرمه",
        "shop.group.item": "محصول",
        "shop.group.stock": "شمېر",

        # === Admin: Statistics ===
        "admin.shop.stats.template": "د پلورنځي احصایې:\n➖➖➖➖➖➖➖➖➖➖➖➖➖\n<b>◽کارنان</b>\n◾️د تیرو ۲۴ ساعتونو کارنان: {today_users}\n◾️ټول مدیران: {admins}\n◾️ټول کارنان: {users}\n➖➖➖➖➖➖➖➖➖➖➖➖➖\n◽<b>متفرقه</b>\n◾محصولات: {items} ټوټې\n◾توکي: {goods} ټوټې\n◾کتګورۍ: {categories} ټوټې\n",

        # === Admin: Lists & Broadcast ===
        "admin.shop.admins.title": "👮 د بوټ مدیران:",
        "admin.shop.users.title": "د بوټ کارنان:",
        "broadcast.prompt": "د عمومي خبرتیا پیغام واستوئ:",
        "broadcast.creating": "📤 عمومي خبرتیا پیلیږي...\n👥 ټول کارنان: {ids}",
        "broadcast.progress": "📤 عمومي خبرتیا روانه ده...\n\n\n📊 پرمختګ: {progress:.1f}%{n}✅ استول شوي: {sent}/{total}\n❌ تېروتنې: {failed}\n⏱ تېر شوی وخت: {time} ثانیې",
        "broadcast.done": "✅ عمومي خبرتیا بشپړه شوه!\n\n📊 احصایې:📊\n👥 ټول: {total}\n✅ رسول شوي: {sent}\n❌ نه رسول شوي: {failed}\n🚫 بوټ بند: ~{blocked}\n📈 د بریالیتوب کچه: {success}%\n⏱ وخت: {duration} ثانیې",
        "broadcast.cancel": "❌ عمومي خبرتیا لغوه شوه.",
        "broadcast.warning": "فعاله عمومي خبرتیا نشته",

        # === Brand / Store Selection ===
        "shop.brands.title": "🏪 یو رستورانت وټاکئ",
        "shop.branches.title": "📍 یوه څانګه وټاکئ",
        "shop.no_brands": "اوس مهال هیڅ رستورانت شتون نلري.",
        "shop.brand_unavailable": "دا رستورانت اوس مهال شتون نلري.",

        # === Shop Browsing (Categories / Goods / Item Page) ===
        "shop.categories.title": "🏪 د پلورنځي کتګورۍ",
        "shop.goods.choose": "🏪 یو محصول وټاکئ",
        "shop.item.not_found": "محصول ونه موندل شو",
        "shop.item.title": "🏪 محصول {name}",
        "shop.item.description": "تشریح: {description}",
        "shop.item.price": "بیه — {amount} {currency}",
        "shop.item.quantity_unlimited": "شمېر — بې حده",
        "shop.item.quantity_left": "شمېر — {count} ټوټې",
        "shop.item.quantity_detailed": "📦 ټوله زیرمه: {total} ټوټې\n🔒 خوندي شوي: {reserved} ټوټې\n✅ د سفارش لپاره شتون لري: {available} ټوټې",

        # === Purchases ===
        "purchases.title": "اخیستل شوي محصولات:",
        "purchases.pagination.invalid": "ناسم مخپانه معلومات",
        "purchases.item.not_found": "پېرود ونه موندل شو",
        "purchases.item.name": "<b>🧾 محصول</b>: <code>{name}</code>",
        "purchases.item.price": "<b>💵 بیه</b>: <code>{amount}</code> {currency}",
        "purchases.item.datetime": "<b>🕒 د اخیستلو نېټه</b>: <code>{dt}</code>",
        "purchases.item.unique_id": "<b>🧾 ځانګړې پېژندنه</b>: <code>{uid}</code>",
        "purchases.item.value": "<b>🔑 ارزښت</b>:\n<code>{value}</code>",

        # === Middleware ===
        "middleware.ban": "⏳ تاسو لنډ مهاله بند یاست. {time} ثانیې انتظار وکړئ.",
        "middleware.above_limits": "⚠️ ډېرې غوښتنې! تاسو لنډ مهاله بند یاست.",
        "middleware.waiting": "⏳ د راتلونکي عمل لپاره {time} ثانیې انتظار وکړئ.",
        "middleware.security.session_outdated": "⚠️ ناست تېره شوې. مهرباني وکړئ بیا پیل کړئ.",
        "middleware.security.invalid_data": "❌ ناسم معلومات",
        "middleware.security.blocked": "❌ لاسرسی بند شو",
        "middleware.security.not_admin": "⛔ کافي اجازې نشته",
        "middleware.security.banned": "⛔ <b>تاسو بند شوي یاست</b>\n\nدلیل: {reason}",
        "middleware.security.banned_no_reason": "⛔ <b>تاسو بند شوي یاست</b>\n\nد نورو معلوماتو لپاره مدیر سره اړیکه ونیسئ.",
        "middleware.security.rate_limit": "⚠️ ډېرې غوښتنې! مهرباني وکړئ لږ انتظار وکړئ.",

        # === Errors ===
        "errors.not_subscribed": "تاسو ګډون نه دی کړی",
        "errors.pagination_invalid": "ناسم مخپانه معلومات",
        "errors.invalid_data": "❌ ناسم معلومات",
        "errors.channel.telegram_not_found": "کانال ته لیکل نشم. ما د اپلوډ کانال @{channel} کې د پیغام خپرولو حق سره د مدیر په توګه اضافه کړئ.",
        "errors.channel.telegram_forbidden_error": "کانال ونه موندل شو. د اپلوډ کانال @{channel} نوم وګورئ.",
        "errors.channel.telegram_bad_request": "کانال ته لیږل ناکام شو: {e}",

        # === Orders ===
        "order.payment_method.choose": "💳 د تادیې لاره وټاکئ:",
        "order.payment_method.bitcoin": "💳 Bitcoin",
        "order.payment_method.litecoin": "💳 Litecoin",
        "order.payment_method.solana": "💳 SOL",
        "order.payment_method.usdt_sol": "💳 USDT (Solana)",
        "order.payment_method.cash": "💵 د رسولو پر مهال تادیه",
        "order.status.notify_order_confirmed": "سفارش {order_code} تأیید شو! 🎉\n\nستاسو سفارش به رسول شي: {delivery_time}\n\nمحصولات:\n{items}\n\nټول: {total}\n\nد رسولو انتظار وکړئ!",
        "order.status.notify_order_delivered": "سفارش {order_code} رسول شو! ✅\n\nستاسو د اخیستنې مننه! هیله لرو بیا مو وګورو! 🙏",
        "order.status.notify_order_modified": "سفارش {order_code} د مدیر لخوا سم شو 📝\n\nبدلونونه:\n{changes}\n\nنوی ټول: {total}",

        # === Additional Common Buttons ===
        "btn.cart": "🛒 کارټ",
        "btn.my_orders": "📦 زما سفارشونه",
        "btn.reference_codes": "🔑 مرجع کوډونه",
        "btn.settings": "⚙️ ترتیبات",
        "btn.referral_bonus_percent": "💰 د معرفي بونس سلنه",
        "btn.order_timeout": "⏱️ د سفارش وخت",
        "btn.timezone": "🌍 وخت سیمه",
        "btn.promptpay_account": "💳 PromptPay حساب",
        "btn.currency": "💱 اسعار",
        "btn.skip": "⏭️ تېرول",
        "btn.use_saved_info": "✅ خوندي شوي معلومات کارول",
        "btn.update_info": "✏️ معلومات تازه کول",
        "btn.back_to_cart": "◀️ کارټ ته شاته",
        "btn.clear_cart": "🗑️ کارټ پاکول",
        "btn.proceed_checkout": "💳 اخیستلو ته دوام",
        "btn.remove_item": "❌ {item_name} لرې کول",
        "btn.use_all_bonus": "ټول ${amount} کارول",
        "btn.apply_bonus_yes": "✅ هو، بونس پلي کړئ",
        "btn.apply_bonus_no": "❌ نه، د وروسته لپاره خوندي کړئ",
        "btn.cancel": "❌ لغوه کول",
        "btn.add_to_cart": "🛒 کارټ ته اضافه کول",

        # === Cart Management ===
        "cart.add_success": "✅ {item_name} کارټ ته اضافه شو!",
        "cart.add_error": "❌ {message}",
        "cart.empty": "🛒 ستاسو کارټ خالي دی.\n\nد محصولاتو اضافه کولو لپاره پلورنځی وګورئ!",
        "cart.title": "🛒 <b>ستاسو کارټ</b>\n\n",
        "cart.removed_success": "محصول له کارټ لرې شو",
        "cart.cleared_success": "✅ کارټ په بریالیتوب سره پاک شو!",
        "cart.empty_alert": "کارټ خالي دی!",
        "cart.summary_title": "📦 <b>د سفارش لنډیز</b>\n\n",
        "cart.saved_delivery_info": "ستاسو خوندي شوي د رسولو معلومات:\n\n",
        "cart.delivery_address": "📍 پته: {address}\n",
        "cart.delivery_phone": "📞 تلیفون: {phone}\n",
        "cart.delivery_note": "📝 یادداشت: {note}\n",
        "cart.use_info_question": "\n\nایا غواړئ دا معلومات وکاروئ یا تازه یې کړئ؟",
        "cart.no_saved_info": "❌ خوندي شوي د رسولو معلومات ونه موندل شول. مهرباني وکړئ په لاسي ډول ولیکئ.",

        # === Order/Delivery Flow ===
        "order.delivery.address_prompt": "📍 مهرباني وکړئ خپله د رسولو پته ولیکئ:",
        "order.delivery.address_invalid": "❌ مهرباني وکړئ یوه سمه پته ولیکئ (لږ تر لږه ۵ توري).",
        "order.delivery.phone_prompt": "📞 مهرباني وکړئ خپل تلیفون شمېره ولیکئ (د هېواد کوډ سره):",
        "order.delivery.phone_invalid": "❌ مهرباني وکړئ یوه سمه تلیفون شمېره ولیکئ (لږ تر لږه ۸ عددونه).",
        "order.delivery.note_prompt": "📝 د رسولو ځانګړي لارښوونې لرئ؟ (اختیاري)\n\nتاسو کولی شئ لاندې تڼۍ فشار ورکړئ تېر شئ.",
        "order.delivery.info_save_error": "❌ د رسولو معلوماتو خوندي کولو کې تېروتنه. مهرباني وکړئ بیا هڅه وکړئ.",

        # Location Method Choice
        "order.delivery.location_method_prompt": "📍 تاسو د رسولو پته څنګه شریکول غواړئ?\n\nلاندې یو انتخاب وکړئ:",
        "btn.location_method.gps": "📡 د Telegram له لارې GPS واستوئ",
        "btn.location_method.live_gps": "📍 ژوندی موقعیت شریک کړئ",
        "btn.location_method.google_link": "🗺 د Google Maps لینک شریک کړئ",
        "btn.location_method.type_address": "✍️ پته ولیکئ",
        "order.delivery.gps_prompt": "📍 لاندې تڼۍ فشار ورکړئ ترڅو خپل موقعیت واستوئ:",
        "order.delivery.gps_hint": "📍 مهرباني وکړئ لاندې تڼۍ وکاروئ ترڅو GPS موقعیت واستوئ، یا 'شاته' فشار ورکړئ ترڅو بل لار وټاکئ.",
        "order.delivery.live_gps_prompt": "📍 د ژوندي موقعیت شریکولو لپاره:\n\n1. لاندې د ضمیمې آیکون 📎 فشار ورکړئ\n2. 'موقعیت' وټاکئ\n3. 'ژوندی موقعیت شریک کړئ' فشار ورکړئ\n4. مودې وټاکئ\n\nموټروان به ستاسو موقعیت په ریال ټایم وګوري!",
        "order.delivery.live_gps_saved": "✅ ژوندی موقعیت ترلاسه شو! موټروان به ستاسو موقعیت وڅاري.",
        "order.delivery.live_gps_hint": "📍 مهرباني وکړئ خپل ژوندی موقعیت د ضمیمې مینو له لارې واستوئ (📎 ← موقعیت ← ژوندی موقعیت شریک کړئ).",
        "order.delivery.google_link_prompt": "🗺 د Google Maps لینک دلته ولیکئ.\n\nGoogle Maps خلاص کړئ، ځای ومومئ، 'شریکول' فشار ورکړئ او لینک دلته کاپي کړئ.",
        "order.delivery.google_link_invalid": "❌ د Google Maps لینک وپېژندل نه شو. ډاډ ترلاسه کړئ چې له google.com/maps یا goo.gl/maps سره پیل کېږي.",
        "order.delivery.address_confirm_prompt": "📍 ستاسو پته:\n<b>{address}</b>\n\n🔗 <a href=\"{maps_link}\">په نقشه کې وګورئ</a>\n\nایا سمه ده؟",
        "btn.address_confirm_yes": "✅ هو، سمه ده",
        "btn.address_confirm_retry": "✏️ نه، بیا ولیکئ",

        # GPS Location (Card 2)
        "order.delivery.location_prompt": "📍 ایا غواړئ د دقیق رسولو لپاره خپل GPS موقعیت شریک کړئ؟\n\nلاندې تڼۍ فشار ورکړئ یا دا مرحله تېره کړئ.",
        "order.delivery.location_saved": "✅ موقعیت خوندي شو!",
        "btn.share_location": "📍 موقعیت شریکول",
        "btn.skip_location": "⏭ تېرول",

        # Delivery Type (Card 3)
        "order.delivery.type_prompt": "🚚 د رسولو ډول وټاکئ:",
        "btn.delivery.door": "🚪 دروازې ته رسول",
        "btn.delivery.dead_drop": "📦 په ځای کې پرېښودل",
        "btn.delivery.pickup": "🏪 پخپله ترلاسه کول",
        "order.delivery.drop_instructions_prompt": "📝 تشریح کړئ چېرته سفارش پرېږدئ (مثلاً 'د لابي نګهبان سره'، 'د ۴۰۵ کوټې دروازې لاندې'):",
        "order.delivery.drop_photo_prompt": "📸 ایا غواړئ د پرېښودلو ځای عکس واستوئ؟ (اختیاري)",
        "order.delivery.drop_photo_saved": "✅ د پرېښودلو ځای عکس خوندي شو!",
        "btn.skip_drop_photo": "⏭ عکس تېرول",

        # PromptPay (Card 1)
        "order.payment_method.promptpay": "💳 PromptPay QR",
        "order.payment.promptpay.title": "💳 <b>PromptPay تادیه</b>",
        "order.payment.promptpay.scan": "📱 د تادیې لپاره QR کوډ سکین کړئ:",
        "order.payment.promptpay.upload_receipt": "📸 د تادیې وروسته، مهرباني وکړئ خپل رسید/سکرین شاټ اپلوډ کړئ:",
        "order.payment.promptpay.receipt_received": "✅ رسید ترلاسه شو! د مدیر تأیید ته انتظار.",
        "order.payment.promptpay.receipt_invalid": "❌ مهرباني وکړئ د خپل تادیې رسید عکس واستوئ.",
        "order.payment.promptpay.slip_verified": "✅ تادیه په اتوماتیک ډول تأیید شوه! ستاسو سفارش تأیید شوی دی.",
        "admin.order.verify_payment": "✅ تادیه تأیید کول",
        "admin.order.payment_verified": "✅ تادیه تأیید شوه",

        # Delivery Chat (Card 13)
        "order.delivery.chat_unavailable": "❌ د موټروان سره خبرې شتون نه لري. د پیک ګروپ تنظیم شوی نه دی.",
        "order.delivery.chat_started": "💬 تاسو کولی شئ خپل موټروان ته پیغام واستوئ. متن، عکس یا موقعیت واستوئ.",
        "order.delivery.live_location_shared": "📍 موټروان خپل ژوندی موقعیت شریک کړی دی! تاسو کولی شئ خپل رسول وڅارئ.",
        "order.delivery.chat_no_active_delivery": "❌ تاسو د خبرو لپاره فعاله رسول نه لرئ.",
        "order.delivery.chat_ended": "✅ د موټروان سره خبرې پای ته ورسېدې.",
        "order.delivery.chat_message_sent": "✅ پیغام موټروان ته واستول شو.",
        "order.delivery.driver_no_active_order": "⚠️ د دې پیغام لیږلو لپاره فعاله سفارش نشته.",
        "btn.chat_with_driver": "💬 د موټروان سره خبرې",
        "order.delivery.drop_gps_prompt": "📍 د پرېښودلو ځای GPS موقعیت لاندې تڼۍ فشارولو سره شریک کړئ:",
        "order.delivery.drop_gps_saved": "✅ GPS موقعیت خوندي شو!",
        "order.delivery.drop_media_prompt": "📸 د پرېښودلو ځای عکسونه یا ویډیوګانې واستوئ (څو فایلونه واستولی شئ). کله چې پای ته ورسېد «ترسره شو» فشار ورکړئ:",
        "order.delivery.drop_media_saved": "✅ {count} فایل(ونه) خوندي شول. نور واستوئ یا «ترسره شو» فشار ورکړئ.",
        "btn.share_drop_location": "📍 موقعیت شریکول",
        "btn.drop_media_done": "✅ ترسره شو",
        "btn.skip_drop_media": "⏭ تېرول",
        "btn.end_chat": "❌ د خبرو پای",

        # GPS tracking & chat session (Card 15)

        # === Bonus/Referral Application ===
        "order.bonus.available": "💰 <b>تاسو ${bonus_balance} معرفي بونس لرئ!</b>\n\n",
        "order.bonus.apply_question": "ایا غواړئ معرفي بونس پر دې سفارش پلي کړئ؟",
        "order.bonus.amount_positive_error": "❌ مهرباني وکړئ مثبت مبلغ ولیکئ.",
        "order.bonus.amount_too_high": "❌ مبلغ ډېر دی. اعظمي قابل تطبیق: ${max_applicable}\nمهرباني وکړئ سم مبلغ ولیکئ:",
        "order.bonus.invalid_amount": "❌ ناسم مبلغ. مهرباني وکړئ عدد ولیکئ (مثلاً 5.50):",
        "order.bonus.insufficient": "❌ د بونس موجودي کافي نه ده. مهرباني وکړئ بیا هڅه وکړئ.",
        "order.bonus.enter_amount": "هغه بونس مبلغ ولیکئ چې غواړئ پلي کړئ (اعظمي ${max_applicable}):\n\nیا لاندې تڼۍ فشار ورکړئ ټول شتون لرونکي بونس وکاروئ.",

        # === Payment Instructions ===
        "order.payment.system_unavailable": "❌ <b>د تادیې سیستم لنډ مهاله شتون نه لري</b>\n\nد Bitcoin پته شتون نه لري. مهرباني وکړئ ملاتړ سره اړیکه ونیسئ.",
        "order.payment.customer_not_found": "❌ د پیرودونکي معلومات ونه موندل شول. مهرباني وکړئ بیا هڅه وکړئ.",
        "order.payment.creation_error": "❌ د سفارش جوړولو کې تېروتنه. مهرباني وکړئ بیا هڅه وکړئ یا ملاتړ سره اړیکه ونیسئ.",

        # === Order Summary/Total ===
        "order.summary.title": "📦 <b>د سفارش لنډیز</b>\n\n",
        "order.summary.cart_total": "د کارټ ټول: ${cart_total}",
        "order.summary.bonus_applied": "پلي شوی بونس: -${bonus_applied}",
        "order.summary.final_amount": "وروستی مبلغ: ${final_amount}",

        # === Inventory/Reservation ===
        "order.inventory.unable_to_reserve": "❌ <b>د محصولاتو خوندي کول ممکن نه دي</b>\n\nلاندې محصولات په غوښتل شوي مقدار کې شتون نه لري:\n\n{unavailable_items}\n\nمهرباني وکړئ خپل کارټ تنظیم کړئ او بیا هڅه وکړئ.",

        # === My Orders View ===
        "myorders.title": "📦 <b>زما سفارشونه</b>\n\n",
        "myorders.total": "ټول سفارشونه: {count}",
        "myorders.active": "⏳ فعال سفارشونه: {count}",
        "myorders.delivered": "✅ رسول شوي: {count}",
        "myorders.select_category": "د سفارشونو لیدلو لپاره کتګوري وټاکئ:",
        "myorders.active_orders": "⏳ فعال سفارشونه",
        "myorders.delivered_orders": "✅ رسول شوي سفارشونه",
        "myorders.all_orders": "📋 ټول سفارشونه",
        "myorders.no_orders_yet": "تاسو تر اوسه سفارش نه دی ورکړی.\n\nد اخیستلو پیلولو لپاره پلورنځی وګورئ!",
        "myorders.browse_shop": "🛍️ پلورنځي ته تګ",
        "myorders.back": "◀️ شاته",
        "myorders.all_title": "📋 ټول سفارشونه",
        "myorders.active_title": "⏳ فعال سفارشونه",
        "myorders.delivered_title": "✅ رسول شوي سفارشونه",
        "myorders.invalid_filter": "ناسم فلتر",
        "myorders.not_found": "سفارشونه ونه موندل شول.",
        "myorders.back_to_menu": "◀️ د سفارشونو مینو ته شاته",
        "myorders.select_details": "د توضیحاتو لپاره سفارش وټاکئ:",
        "myorders.order_not_found": "سفارش ونه موندل شو",

        # === Order Details Display ===
        "myorders.detail.title": "📦 <b>د سفارش توضیحات #{order_code}</b>\n\n",
        "myorders.detail.status": "📊 <b>حالت:</b> {status}\n",
        "myorders.detail.subtotal": "💵 <b>فرعي مجموعه:</b> ${subtotal}\n",
        "myorders.detail.bonus_applied": "🎁 <b>پلي شوی بونس:</b> ${bonus}\n",
        "myorders.detail.final_price": "💰 <b>وروستۍ بیه:</b> ${total}\n",
        "myorders.detail.total_price": "💰 <b>ټوله بیه:</b> ${total}\n",
        "myorders.detail.payment_method": "💳 <b>د تادیې لاره:</b> {method}\n",
        "myorders.detail.ordered": "📅 <b>سفارش شوی:</b> {date}\n",
        "myorders.detail.delivery_time": "🚚 <b>ټاکل شوی رسول:</b> {time}\n",
        "myorders.detail.completed": "✅ <b>بشپړ شوی:</b> {date}\n",
        "myorders.detail.items": "\n📦 <b>محصولات:</b>\n{items}\n",
        "myorders.detail.delivery_info": "\n📍 <b>د رسولو معلومات:</b>\n{address}\n{phone}\n{note}",

        # === Help System ===
        "help.prompt": "📧 <b>مرستې ته اړتیا لرئ؟</b>\n\n",
        "help.describe_issue": "مهرباني وکړئ خپله ستونزه یا پوښتنه تشریح کړئ، نو مستقیماً مدیر ته به واستول شي.\n\nخپل پیغام لاندې ولیکئ:",
        "help.admin_not_configured": "❌ بخښنه غواړو، د مدیر اړیکه تنظیم شوې نه ده. مهرباني وکړئ وروسته بیا هڅه وکړئ.",
        "help.admin_notification_title": "📧 <b>نوې د مرستې غوښتنه</b>\n\n",
        "help.admin_notification_from": "<b>له:</b> @{username} (ID: {user_id})\n",
        "help.admin_notification_message": "<b>پیغام:</b>\n{message}",
        "help.sent_success": "✅ {auto_message}",
        "help.sent_error": "❌ مدیر ته د پیغام لیږل ناکام شو: {error}\n\nمهرباني وکړئ وروسته بیا هڅه وکړئ.",
        "help.cancelled": "د مرستې غوښتنه لغوه شوه.",

        # === Admin Order Notifications ===
        "admin.order.action_required_title": "⏳ <b>عمل ته اړتیا:</b>",
        "admin.order.address_label": "پته: {address}",
        "admin.order.amount_to_collect_label": "<b>د ترلاسه کولو مبلغ: ${amount} {currency}</b>",
        "admin.order.amount_to_receive_label": "<b>د ترلاسه کیدونکی مبلغ: ${amount} {currency}</b>",
        "admin.order.awaiting_payment_status": "⏳ د تادیې تأیید ته انتظار...",
        "admin.order.bitcoin_address_label": "د Bitcoin پته: <code>{address}</code>",
        "admin.order.bonus_applied_label": "پلي شوی بونس: <b>-${amount}</b>",
        "admin.order.customer_label": "پیرودونکی: {username} (ID: {id})",
        "admin.order.delivery_info_title": "<b>د رسولو معلومات:</b>",
        "admin.order.items_title": "<b>محصولات:</b>",
        "admin.order.new_bitcoin_order": "🔔 <b>نوی Bitcoin سفارش ترلاسه شو</b>",
        "admin.order.new_cash_order": "🔔 <b>نوی نقدي سفارش ترلاسه شو</b> 💵",
        "admin.order.note_label": "یادداشت: {note}",
        "admin.order.order_label": "سفارش: <b>{code}</b>",
        "admin.order.payment_cash": "د رسولو پر مهال تادیه",
        "admin.order.payment_method_label": "د تادیې لاره: <b>{method}</b>",
        "admin.order.phone_label": "تلیفون: {phone}",
        "admin.order.subtotal_label": "فرعي مجموعه: <b>${amount} {currency}</b>",
        "admin.order.use_cli_confirm": "د سفارش تأیید او د رسولو وخت ټاکلو لپاره CLI وکاروئ:\n<code>python bot_cli.py order --order-code {code} --status-confirmed --delivery-time \"YYYY-MM-DD HH:MM\"</code>",
        "btn.admin.back_to_panel": "🔙 د مدیر پینل ته شاته",
        "btn.admin.create_refcode": "➕ مرجع کوډ جوړول",
        "btn.admin.list_refcodes": "📋 ټول کوډونه لیست کول",
        "btn.back_to_orders": "◀️ سفارشونو ته شاته",
        "btn.create_reference_code": "➕ مرجع کوډ جوړول",
        "btn.my_reference_codes": "🔑 زما مرجع کوډونه",
        "btn.need_help": "❓ مرستې ته اړتیا؟",
        "cart.item.price_format": "  بیه: {price} {currency} × {quantity}",
        "cart.item.subtotal_format": "  فرعي مجموعه: {subtotal} {currency}",
        "cart.item.modifiers": "  بدلونونه: {modifiers}",
        "cart.total_format": "<b>ټول: {total} {currency}</b>",
        "cart.add_cancelled": "اضافه کول لغوه شوه",
        "modifier.select_title": "{label} وټاکئ:",
        "modifier.selected": "ټاکل شوی: {choice}",
        "modifier.required": "(اړین)",
        "modifier.optional": "(اختیاري)",
        "modifier.done": "ترسره شو",
        "modifier.price_extra": "+{price}",
        "modifier.cancelled": "د بدلونونو انتخاب لغوه شو.",
        "help.pending_order.contact_support": "د ملاتړ سره اړیکې لپاره /help کمانډ وکاروئ.",
        "help.pending_order.issues_title": "<b>ستونزه لرئ؟</b>",
        "help.pending_order.status": "ستاسو سفارش د تادیې انتظار کې دی.",
        "help.pending_order.step1": "1. دقیق مبلغ ښودل شوي Bitcoin پتې ته واستوئ",
        "help.pending_order.step2": "2. د بلاکچین تأیید ته انتظار وکړئ (معمولاً ۱۰ تر ۶۰ دقیقې)",
        "help.pending_order.step3": "3. مدیر به ستاسو تادیه تأیید کړي او د رسولو وخت وټاکي",
        "help.pending_order.step4": "4. ستاسو توکي به د پیک لخوا رسول شي.",
        "help.pending_order.title": "❓ <b>د سفارش په اړه مرستې ته اړتیا؟</b>",
        "help.pending_order.what_to_do_title": "<b>څه وکړئ:</b>",
        "myorders.detail.bitcoin_address_label": "د Bitcoin پته:",
        "myorders.detail.bitcoin_admin_confirm": "د تادیې وروسته، زموږ مدیر به ستاسو سفارش تأیید کړي.",
        "myorders.detail.bitcoin_send_instruction": "⚠️ مهرباني وکړئ <b>{amount} {currency}</b> Bitcoin دې پتې ته واستوئ.",
        "myorders.detail.cash_awaiting_confirm": "ستاسو سفارش د مدیر تأیید ته انتظار کې دی.",
        "myorders.detail.cash_payment_courier": "تادیه به د رسولو پر مهال پیک ته شي.",
        "myorders.detail.cash_title": "💵 د رسولو پر مهال تادیه",
        "myorders.detail.cash_will_notify": "کله چې سفارش تأیید شي او د رسولو وخت وټاکل شي تاسو ته به خبر درکړل شي.",
        "myorders.detail.confirmed_title": "✅ <b>سفارش تأیید شو!</b>",
        "myorders.detail.delivered_thanks_message": "ستاسو د اخیستنې مننه! هیله لرو بیا مو وګورو! 🙏",
        "myorders.detail.delivered_title": "📦 <b>سفارش رسول شو!</b>",
        "myorders.detail.payment_info_title": "<b>د تادیې معلومات:</b>",
        "myorders.detail.preparing_message": "ستاسو سفارش د رسولو لپاره چمتو کیږي.",
        "myorders.detail.scheduled_delivery_label": "ټاکل شوی رسول: <b>{time}</b>",
        "myorders.order_summary_format": "{status_emoji} {code} - {items_count} محصولات - {total} {currency}",
        "order.bonus.available_label": "شتون لرونکی بونس: <b>${amount}</b>",
        "order.bonus.choose_amount_hint": "تاسو کولی شئ وټاکئ څومره وکاروئ (اعظمي ${max_amount})",
        "order.bonus.enter_amount_title": "💵 <b>د پلي کیدونکي بونس مبلغ ولیکئ</b>",
        "order.bonus.max_applicable_label": "اعظمي قابل تطبیق: <b>${amount}</b>",
        "order.bonus.order_total_label": "د سفارش ټول: <b>${amount} {currency}</b>",
        "order.info.view_status_hint": "💡 تاسو کولی شئ هر وخت د /orders کمانډ سره د سفارش حالت وګورئ.",
        "order.payment.bitcoin.address_title": "<b>د Bitcoin تادیې پته:</b>",
        "order.payment.bitcoin.admin_confirm": "• د تادیې وروسته، زموږ مدیر به ستاسو سفارش تأیید کړي",
        "order.payment.bitcoin.delivery_title": "<b>رسول:</b>",
        "order.payment.bitcoin.important_title": "⚠️ <b>مهم:</b>",
        "order.payment.bitcoin.items_title": "<b>محصولات:</b>",
        "order.payment.bitcoin.need_help": "مرستې ته اړتیا لرئ؟ د ملاتړ لپاره /help وکاروئ.",
        "order.payment.bitcoin.one_time_address": "• دا پته یوازې د یو ځل کارولو لپاره ده",
        "order.payment.bitcoin.order_code": "سفارش: <b>{code}</b>",
        "order.payment.bitcoin.send_exact": "• پورته ښودل شوی دقیق مبلغ واستوئ",
        "order.payment.bitcoin.title": "💳 <b>د Bitcoin تادیې لارښوونې</b>",
        "order.payment.bitcoin.total_amount": "ټول مبلغ: <b>{amount} {currency}</b>",

        # Crypto payment (Card 18) — generic strings for all coins
        "crypto.payment.title": "💳 <b>{coin_name} Payment</b>",
        "crypto.payment.order_code": "Order: <b>{code}</b>",
        "crypto.payment.total_fiat": "Total: <b>{amount} {currency}</b>",
        "crypto.payment.rate": "Rate: 1 {coin} = {rate} {currency}",
        "crypto.payment.amount_due": "Amount due: <b>{crypto_amount} {coin}</b>",
        "crypto.payment.address": "<b>Send to this address:</b>\n<code>{address}</code>",
        "crypto.payment.send_exact": "• Send EXACTLY this amount",
        "crypto.payment.one_time": "• This address is for ONE-TIME use",
        "crypto.payment.auto_confirm": "• Your order will be automatically confirmed once the payment is detected on-chain.",
        "crypto.payment.waiting": "⏳ Waiting for payment...\nThis address expires in {timeout} minutes.",
        "crypto.payment.no_address": "❌ No {coin} addresses available. Please contact support or choose another payment method.",
        "crypto.payment_detected": (
            "✅ <b>Payment detected!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "⏳ Waiting for confirmations..."
        ),
        "crypto.payment_confirmed": (
            "✅ <b>Payment confirmed!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "Your order is now being processed."
        ),
        "crypto.payment_expired": "⏰ Payment window for your {coin} order ({order_code}) has expired. Please place a new order.",

        "order.payment.cash.admin_contact": "مدیر به ډېر ژر تاسو سره اړیکه ونیسي.",
        "order.payment.cash.after_confirm": "د تأیید وروسته، د رسولو وخت به تاسو ته خبر درکړل شي.",
        "order.payment.cash.created": "ستاسو سفارش {code} جوړ شو او د مدیر تأیید ته انتظار کې دی.",
        "order.payment.cash.important": "⏳ <b>مهم:</b> سفارش د محدود وخت لپاره خوندي شوی دی.",
        "order.payment.cash.items_title": "محصولات:",
        "order.payment.cash.payment_to_courier": "تادیه به د رسولو پر مهال پیک ته شي.",
        "order.payment.cash.title": "💵 <b>د رسولو پر مهال تادیه</b>",
        "order.payment.cash.total": "ټول: {amount}",
        "order.payment.error_general": "❌ د سفارش جوړولو کې تېروتنه. مهرباني وکړئ بیا هڅه وکړئ یا ملاتړ سره اړیکه ونیسئ.",
        "order.summary.total_label": "<b>ټول: {amount} {currency}</b>",
        "order.payment.bonus_applied_label": "پلي شوی بونس: <b>-{amount} {currency}</b>",
        "order.payment.cash.amount_with_bonus": "<b>د رسولو پر مهال د تادیې مبلغ: {amount} {currency}</b>",
        "order.payment.cash.total_label": "<b>د رسولو ټوله تادیه: {amount} {currency}</b>",
        "order.payment.final_amount_label": "<b>وروستی د تادیې مبلغ: {amount} {currency}</b>",
        "order.payment.order_label": "📋 <b>سفارش: {code}</b>",
        "order.payment.subtotal_label": "فرعي مجموعه: <b>{amount} {currency}</b>",
        "order.payment.total_amount_label": "<b>ټول مبلغ: {amount} {currency}</b>",

        # Delivery Photo Proof (Card 4)
        "delivery.photo.required": "د ځای پر ځای تحویل لپاره عکس اړین دی",
        "delivery.photo.upload_prompt": "مهرباني وکړئ د تحویل عکس اپلوډ کړئ",
        "delivery.photo.received": "د تحویل عکس خوندي شو",
        "delivery.photo.sent_to_customer": "د تحویل عکس پیرودونکي ته واستول شو",
        "delivery.photo.customer_notification": "ستاسو سفارش {order_code} تحویل شو! دا د تحویل تأیید عکس دی.",

        # === New Feature Strings ===

        # === Restaurant Feature Strings ===
        "admin.goods.add.allergen.dairy": "Dairy",
        "admin.goods.add.allergen.eggs": "Eggs",
        "admin.goods.add.allergen.fish": "Fish",
        "admin.goods.add.allergen.gluten": "Gluten",
        "admin.goods.add.allergen.nuts": "Nuts",
        "admin.goods.add.allergen.sesame": "Sesame",
        "admin.goods.add.allergen.shellfish": "Shellfish",
        "admin.goods.add.allergen.soy": "Soy",
        "admin.goods.add.allergens.done": "✅ Done",
        "admin.goods.add.allergens.skip": "⏭ No Allergens",
        "admin.goods.add.availability.invalid": "❌ Invalid format. Use HH:MM-HH:MM (e.g. 06:00-22:00)",
        "admin.goods.add.availability.skip": "⏭ All Day",
        "admin.goods.add.daily_limit.invalid": "❌ Enter a positive number.",
        "admin.goods.add.daily_limit.skip": "⏭ Unlimited",
        "admin.goods.add.modifier.add_another_group": "➕ Another Group",
        "admin.goods.add.modifier.add_group": "➕ Add Modifier Group",
        "admin.goods.add.modifier.add_option": "➕ Add Option",
        "admin.goods.add.modifier.all_done": "✅ Finish",
        "admin.goods.add.modifier.finish": "✅ Finish (No Modifiers)",
        "admin.goods.add.modifier.group_added": "✅ Group added! Add another group or finish.",
        "admin.goods.add.modifier.group_name": "Enter modifier group name (e.g. Spice Level):",
        "admin.goods.add.modifier.group_type": "Select type for this group:",
        "admin.goods.add.modifier.option_added": "✅ Option added! Add another or press Done.",
        "admin.goods.add.modifier.option_label": "Enter option label (e.g. Mild, Extra Cheese):",
        "admin.goods.add.modifier.option_price": "Enter price adjustment for this option (0 for free):",
        "admin.goods.add.modifier.options_done": "✅ Done with Options",
        "admin.goods.add.modifier.paste_json": "📋 Paste JSON",
        "admin.goods.add.modifier.required_no": "⭕ Optional",
        "admin.goods.add.modifier.required_yes": "✅ Required",
        "admin.goods.add.modifier.type_multi": "Multi Choice",
        "admin.goods.add.modifier.type_single": "Single Choice",
        "admin.goods.add.photo.done": "✅ Done",
        "admin.goods.add.photo.received": "✅ Media received! Send more or press Done.",
        "admin.goods.add.photo.send_more": "Send more photos/videos or press Done:",
        "admin.goods.add.photo.skip": "⏭ Skip Photos",
        "admin.goods.add.prep_time.invalid": "❌ Enter a positive number.",
        "admin.goods.add.prep_time.skip": "⏭ Skip",
        "admin.goods.add.prompt.allergens": "⚠️ Select allergens (tap to toggle, then Done):",
        "admin.goods.add.prompt.availability": "🕐 Enter availability hours (e.g. 06:00-22:00) or press Skip for all-day:",
        "admin.goods.add.prompt.daily_limit": "📊 Enter daily limit (max units per day) or press Skip for unlimited:",
        "admin.goods.add.prompt.modifier_group": "Add a modifier group (e.g. Spice Level, Extras)?",
        "admin.goods.add.prompt.photo": "📸 Send a photo or video of this item (or press Skip):",
        "admin.goods.add.prompt.prep_time": "⏱ Enter prep time in minutes (or press Skip):",
        "admin.goods.toggle.active_off": "🚫 {item}: Deactivated",
        "admin.goods.toggle.active_on": "✅ {item}: Activated",
        "admin.goods.toggle.sold_out_off": "✅ {item}: Back in stock",
        "admin.goods.toggle.sold_out_on": "❌ {item}: Marked SOLD OUT",
        "btn.view_gallery": "📸 Gallery ({count})",
        "kitchen.order.modifier_detail": "    ↳ {modifiers}",
        "kitchen.order.prep_time": "⏱ Est. prep: {minutes} min",
        "kitchen.order.ready_by": "🕐 Ready by: {time}",
        "order.estimated_ready": "⏱ Estimated ready in ~{minutes} min",
        "shop.item.allergens": "⚠️ Allergens: {allergens}",
        "shop.item.availability": "🕐 Available: {from_time} - {until_time}",
        "shop.item.calories": "🔥 {calories} cal",
        "shop.item.daily_remaining": "📊 Today: {remaining}/{limit} left",
        "shop.item.no_gallery": "No gallery for this item.",
        "shop.item.type_product": "📦 ڈول: بسته‌بندي شوی محصول",
        "shop.item.type_prepared": "🍳 ڈول: د غوښتنې پر اساس جوړیږي",
        "shop.item.prep_time": "⏱ Prep: ~{minutes} min",
        "shop.item.sold_out": "❌ Sold out today",
        "admin.accounting.export_payments": "📥 Payment Reconciliation",
        "admin.accounting.export_products": "📥 Revenue by Product",
        "admin.accounting.export_sales": "📥 Export Sales CSV",
        "admin.accounting.export_sent": "✅ Report exported.",
        "admin.accounting.no_data": "No data for this period.",
        "admin.accounting.summary": "📊 <b>Revenue Summary ({period})</b>\n\n💰 Revenue: {total} {currency}\n📦 Orders: {orders}\n📈 Avg: {avg} {currency}\n\n<b>By Payment:</b>\n{payments}\n\n<b>Top Products:</b>\n{products}",
        "admin.accounting.summary_all": "📊 All Time",
        "admin.accounting.summary_month": "📊 This Month",
        "admin.accounting.summary_today": "📊 Today",
        "admin.accounting.summary_week": "📊 This Week",
        "admin.accounting.title": "📊 <b>Accounting & Reports</b>",
        "admin.coupon.create": "➕ Create Coupon",
        "admin.coupon.created": "✅ Coupon <b>{code}</b> created!\nType: {type}\nValue: {value}\nMin order: {min_order}\nMax uses: {max_uses}\nExpires: {expiry}",
        "admin.coupon.detail": "🎟 <b>{code}</b>\nType: {type}\nValue: {value}\nMin Order: {min_order}\nMax Uses: {max_uses}\nUsed: {used}\nStatus: {status}\nExpires: {expiry}",
        "admin.coupon.empty": "No coupons found.",
        "admin.coupon.enter_code": "Enter coupon code (or type <b>auto</b> for random):",
        "admin.coupon.enter_expiry": "Enter expiry in days (or <b>skip</b> for no expiry):",
        "admin.coupon.enter_max_uses": "Enter max total uses (or <b>skip</b> for unlimited):",
        "admin.coupon.enter_min_order": "Enter minimum order amount (or <b>skip</b>):",
        "admin.coupon.enter_value": "Enter discount value ({type}):",
        "admin.coupon.invalid_value": "❌ Invalid value. Enter a number.",
        "admin.coupon.list_active": "📋 Active Coupons",
        "admin.coupon.list_all": "📋 All Coupons",
        "admin.coupon.select_type": "Select discount type:",
        "admin.coupon.title": "🎟 <b>Coupon Management</b>",
        "admin.coupon.toggle_activate": "✅ Activate",
        "admin.coupon.toggle_deactivate": "❌ Deactivate",
        "admin.coupon.toggled": "✅ Coupon {code} is now {status}.",
        "admin.coupon.type_fixed": "💰 Fixed Amount",
        "admin.coupon.type_percent": "📊 Percentage (%)",
        "admin.menu.accounting": "📊 Accounting",
        "admin.menu.coupons": "🎟 Coupons",
        "admin.menu.segment_broadcast": "📣 Targeted Broadcast",
        "admin.menu.stores": "🏪 Stores",
        "admin.menu.tickets": "🎫 Tickets",
        "admin.menu.ai_assistant": "🤖 AI Assistant",
        "admin.segment.all_users": "👥 All Users",
        "admin.segment.count": "📊 Segment: <b>{segment}</b>\nUsers: <b>{count}</b>\n\nType your broadcast message:",
        "admin.segment.empty": "No users in this segment.",
        "admin.segment.high_spenders": "💰 High Spenders",
        "admin.segment.inactive": "😴 Inactive (30+ days)",
        "admin.segment.new_users": "🆕 New Users (7d)",
        "admin.segment.recent_buyers": "🛒 Recent Buyers (7d)",
        "admin.segment.sent": "✅ Sent to {sent}/{total} ({segment}).",
        "admin.segment.title": "📣 <b>Targeted Broadcast</b>\n\nSelect segment:",
        "admin.store.add": "➕ Add Store",
        "admin.store.address_prompt": "Enter store address (or <b>skip</b>):",
        "admin.store.btn_default": "⭐ Set as Default",
        "admin.store.created": "✅ Store <b>{name}</b> created!",
        "admin.store.detail": "🏪 <b>{name}</b>\nStatus: {status}\nDefault: {default}\nAddress: {address}\nLocation: {location}\nPhone: {phone}",
        "admin.store.empty": "No stores configured.",
        "admin.store.location_prompt": "Send GPS location (or type <b>skip</b>):",
        "admin.store.name_exists": "Store with this name already exists.",
        "admin.store.name_prompt": "Enter store name:",
        "admin.store.set_default": "✅ {name} set as default store.",
        "admin.store.title": "🏪 <b>Store Management</b>",
        "admin.store.toggle_activate": "✅ Activate",
        "admin.store.toggle_deactivate": "❌ Deactivate",
        "admin.store.toggled": "✅ Store {name} is now {status}.",
        "admin.ticket.detail": "🎫 <b>Ticket #{code}</b>\nUser: {user_id}\nStatus: {status}\nPriority: {priority}\nSubject: {subject}\nCreated: {date}",
        "admin.ticket.empty": "No open tickets.",
        "admin.ticket.list": "Open/In Progress Tickets:",
        "admin.ticket.reply_prompt": "Reply to ticket #{code}:",
        "admin.ticket.resolved": "✅ Ticket #{code} resolved.",
        "admin.ticket.title": "🎫 <b>Support Tickets</b>",
        "btn.admin.reply_ticket": "💬 Reply",
        "btn.admin.resolve_ticket": "✅ Resolve",
        "btn.apply_coupon": "🎟 Apply Coupon",
        "btn.close_ticket": "✖ Close Ticket",
        "btn.create_ticket": "➕ New Ticket",
        "btn.create_ticket_for_order": "🎫 Support Ticket",
        "btn.invoice": "🧾 Receipt",
        "btn.my_tickets": "🎫 Support",
        "btn.reorder": "🔄 Reorder",
        "btn.reply_ticket": "💬 Reply",
        "btn.review_order": "⭐ Leave Review",
        "btn.search": "🔍 Search",
        "btn.skip_coupon": "⏭ Skip Coupon",
        "coupon.already_used": "❌ You already used this coupon.",
        "coupon.applied": "✅ Coupon applied! Discount: -{discount} {currency}",
        "coupon.enter_code": "🎟 Enter coupon code (or press Skip):",
        "coupon.expired": "❌ This coupon has expired.",
        "coupon.invalid": "❌ Invalid or expired coupon code.",
        "coupon.max_uses_reached": "❌ Coupon usage limit reached.",
        "coupon.min_order_not_met": "❌ Min order of {min_order} required.",
        "coupon.not_yet_valid": "❌ This coupon is not yet valid.",
        "invoice.not_available": "Receipt not available.",
        "reorder.success": "✅ Added {added} item(s) to cart. {skipped} item(s) unavailable.",
        "review.already_reviewed": "You have already reviewed this order.",
        "review.comment_prompt": "You rated {rating}/5 ⭐\n\nAdd a comment? Type or press Skip:",
        "review.detail": "⭐{rating}/5 — {comment}",
        "review.item_rating": "⭐ <b>{item}</b>: {avg:.1f}/5 ({count} reviews)",
        "review.no_reviews": "No reviews yet.",
        "review.prompt": "⭐ <b>Rate your order #{order_code}</b>\n\nSelect your rating:",
        "review.rate_1": "⭐",
        "review.rate_2": "⭐⭐",
        "review.rate_3": "⭐⭐⭐",
        "review.rate_4": "⭐⭐⭐⭐",
        "review.rate_5": "⭐⭐⭐⭐⭐",
        "review.skip_comment": "⏭ Skip",
        "review.thanks": "✅ Thank you for your review! ({rating}/5 ⭐)",
        "search.no_results": "❌ No products found. Try different keywords.",
        "search.prompt": "🔍 Enter product name or keyword to search:",
        "search.result_count": "Found {count} product(s):\n",
        "search.results_title": "🔍 <b>Search results for:</b> {query}\n\n",
        "ticket.admin_replied": "💬 Admin replied to ticket #{code}:\n{text}",
        "ticket.closed": "✅ Ticket closed.",
        "ticket.created": "✅ Ticket <b>#{code}</b> created!",
        "ticket.message_format": "<b>{role}</b> ({date}):\n{text}\n",
        "ticket.message_prompt": "Describe your issue:",
        "ticket.no_tickets": "No support tickets.",
        "ticket.reply_prompt": "Type your reply:",
        "ticket.reply_sent": "✅ Reply sent.",
        "ticket.resolved_notification": "✅ Ticket #{code} resolved!",
        "ticket.status.closed": "⚫ Closed",
        "ticket.status.in_progress": "🔵 In Progress",
        "ticket.status.open": "🟢 Open",
        "ticket.status.resolved": "✅ Resolved",
        "ticket.subject_prompt": "Enter the subject:",
        "ticket.title": "🎫 <b>Support Tickets</b>",
        "ticket.view_title": "🎫 <b>Ticket #{code}</b>\nStatus: {status}\nSubject: {subject}\nCreated: {date}",

        # Delivery GPS (Card 15)
        "delivery.gps.prompt": "📍 ستاسو سفارش {order_code} په لاره ده!\n\nچلوونکي سره مرسته وکړئ چې تاسو ژر ومومي — خپل ځای شریک کړئ:",
        "delivery.gps.btn_static": "📍 ځای واستوئ",
        "delivery.gps.btn_live": "📡 ژوندی ځای",
        "delivery.gps.btn_skip": "⏭ تېر شئ",
        "delivery.gps.static_sent": "✅ ستاسو ځای چلوونکي ته واستول شو.",
        "delivery.gps.live_started": "📡 ژوندی ځای فعال شو! ستاسو چلوونکی تاسو په حقیقي وخت کې تعقیبوي.",
        "delivery.gps.skipped": "⏭ ځای تېر شو. چلوونکی به د سفارش له پتې څخه کار واخلي.",
        "delivery.chat.session_closed": "⏹ دا د چت غونډه پای ته ورسېدله. د مرستې لپاره له ملاتړ سره اړیکه ونیسئ.",
        "delivery.chat.post_delivery_open": "✅ تحویل شو! چت به د {minutes} نورو دقیقو لپاره خلاص پاتې شي.",
        "delivery.chat.post_delivery_closed": "⏹ د تحویل وروسته د چت کړکۍ وتړل شوه.",

        # === Card 9: Kitchen & Delivery Workflow ===
        "admin.menu.orders": "📋 سفارشونه",
        "admin.orders.list_title": "📋 <b>سفارشونه</b>",
        "admin.orders.empty": "هیڅ سفارش ونه موندل شو",
        "admin.orders.filter_status": "د حالت پر اساس فلتر",
        "admin.orders.filter_all": "📋 ټولې سفارشونه",
        "admin.orders.filter_active": "🔄 فعالې",
        "admin.orders.detail": (
            "📋 <b>سفارش #{order_id}</b> ({order_code})\n"
            "👤 اخیستونکی: {buyer_id}\n"
            "💰 ټول: {total}\n"
            "📦 حالت: {status}\n"
            "📅 جوړ شوی: {created_at}\n"
            "📍 پته: {address}\n"
            "📞 تلفون: {phone}"
        ),
        "admin.orders.status_changed": "د سفارش #{order_id} حالت <b>{new_status}</b> ته بدل شو",
        "admin.orders.invalid_transition": "د {current} څخه {new} ته حالت بدلول ممکن نه دي",
        "kitchen.order_received": (
            "🍳 <b>نوی سفارش #{order_id}</b> ({order_code})\n\n"
            "{items}\n\n"
            "💰 ټول: {total}\n"
            "📍 پته: {address}\n"
            "📞 تلفون: {phone}"
        ),
        "rider.order_ready": (
            "🚗 <b>سفارش چمتو #{order_id}</b> ({order_code})\n\n"
            "💰 ټول: {total}\n"
            "📍 پته: {address}\n"
            "📞 تلفون: {phone}"
        ),
        "order.status.preparing": "🍳 ستاسو سفارش #{order_code} چمتو کیږي",
        "order.status.ready": "✅ ستاسو سفارش #{order_code} د ترلاسه کولو لپاره چمتو دی",
        "order.status.out_for_delivery": "🚗 ستاسو سفارش #{order_code} په لاره کې دی",
        "order.status.delivered_notify": "📦 ستاسو سفارش #{order_code} تحویل شو",
        "kitchen.btn.start_preparing": "🍳 چمتو کول پیل کړئ",
        "kitchen.btn.mark_ready": "✅ چمتو",
        "rider.btn.picked_up": "📦 ترلاسه شو",
        "rider.btn.delivered": "✅ تحویل شو",

        # === PDPA Privacy Policy ===
        "btn.privacy": "🔒 د محرمیت تګلاره",
        "privacy.notice": (
            "🔒 <b>د محرمیت خبرتیا (PDPA)</b>\n\n"
            "موږ د تایلند د شخصي معلوماتو د ساتنې قانون (PDPA) سره مطابقت لرو.\n\n"
            "<b>هغه معلومات چې موږ یې راټولوو:</b>\n"
            "• نوم / تلیفون / د تحویلۍ پته\n"
            "• د سفارش توضیحات او تاریخچه\n"
            "• د تلیګرام پیژندنه\n\n"
            "<b>موخې:</b>\n"
            "• د سفارش تکمیل او تحویلي (تړونیزه اړتیا)\n"
            "• د درغلیو مخنیوی او د پیژندنې تایید\n"
            "• بازارموندنه — یوازې ستاسو د جلا رضایت سره\n\n"
            "<b>ساتل:</b> تر هغه چې تاسو د حذف غوښتنه وکړئ، یا ستاسو د وروستي سفارش څخه ۲ کاله وروسته\n\n"
            "<b>د معلوماتو شریکول:</b> رستورانتونه، د تحویلۍ موټر چلوونکي، د تادیاتو چمتو کوونکي — یوازې ستاسو د سفارش لپاره. "
            "موږ هیڅکله ستاسو معلومات نه پلورو.\n\n"
            "<b>ستاسو د PDPA حقونه:</b>\n"
            "• خپلو معلوماتو ته لاسرسی / سمون / حذف\n"
            "• رضایت بیرته اخیستل (د بازارموندنې لپاره)\n"
            "• پروسس ته اعتراض / د معلوماتو لیږدولو غوښتنه\n"
            "• PDPC ته شکایت ورکول\n\n"
            "<b>د معلوماتو کنټرولر:</b> {company}\n"
            "اړیکه: {email}\n\n"
            "د دې بوټ کارولو ته دوام ورکولو سره، تاسو دا تګلاره منئ او قبلوئ."
        ),
        "privacy.btn_full_policy": "📄 بشپړه تګلاره ولولئ",
        "privacy.btn_accept": "✅ ومنئ او دوام ورکړئ",
        "privacy.accepted": "✅ تاسو د محرمیت تګلاره ومنله.",
        "privacy.already_accepted": "✅ تاسو مخکې د محرمیت تګلاره منلې ده.",
        "privacy.no_url": "د محرمیت بشپړې تګلارې پاڼه لا تر اوسه تنظیم شوې نه ده.",
    },
    "fr": {
        # === Common Buttons ===
        "btn.shop": "🏪 Boutique",
        "btn.rules": "📜 Règles",
        "btn.profile": "👤 Profil",
        "btn.support": "🆘 Assistance",
        "btn.channel": "ℹ Canal d'actualités",
        "btn.admin_menu": "🎛 Panneau d'administration",
        "btn.back": "⬅️ Retour",
        "btn.close": "✖ Fermer",
        "btn.yes": "✅ Oui",
        "btn.no": "❌ Non",
        "btn.check_subscription": "🔄 Vérifier l'abonnement",
        "btn.admin.ban_user": "🚫 Bannir l'utilisateur",
        "btn.admin.unban_user": "✅ Débannir l'utilisateur",

        # === Admin Buttons (user management shortcuts) ===
        "btn.admin.promote": "⬆️ Nommer administrateur",
        "btn.admin.demote": "⬇️ Révoquer administrateur",
        "btn.admin.add_user_bonus": "🎁 Ajouter un bonus de parrainage",

        # === Titles / Generic Texts ===
        "menu.title": "⛩️ Menu principal",
        "admin.goods.add.stock.error": "❌ Erreur lors de l'ajout du stock initial : {error}",
        "admin.goods.stock.add_success": "✅ {quantity} unités ajoutées à \"{item}\"",
        "admin.goods.stock.add_units": "➕ Ajouter des unités",
        "admin.goods.stock.current_status": "Statut actuel",
        "admin.goods.stock.error": "❌ Erreur de gestion du stock : {error}",
        "admin.goods.stock.insufficient": "❌ Stock insuffisant. Seulement {available} unités disponibles.",
        "admin.goods.stock.invalid_quantity": "⚠️ Quantité invalide. Entrez un nombre entier.",
        "admin.goods.stock.management_title": "Gestion du stock : {item}",
        "admin.goods.stock.negative_quantity": "⚠️ La quantité ne peut pas être négative.",
        "admin.goods.stock.no_products": "❌ Aucun produit dans la boutique pour le moment",
        "admin.goods.stock.prompt.add_units": "Entrez le nombre d'unités à ajouter :",
        "admin.goods.stock.prompt.item_name": "Entrez le nom du produit pour gérer le stock :",
        "admin.goods.stock.prompt.remove_units": "Entrez le nombre d'unités à retirer :",
        "admin.goods.stock.prompt.set_exact": "Entrez la quantité exacte du stock :",
        "admin.goods.stock.redirect_message": "ℹ️ La gestion du stock est maintenant disponible via le menu « Gérer le stock »",
        "admin.goods.stock.remove_success": "✅ {quantity} unités retirées de \"{item}\"",
        "admin.goods.stock.remove_units": "➖ Retirer des unités",
        "admin.goods.stock.select_action": "Sélectionnez une action",
        "admin.goods.stock.set_exact": "⚖️ Définir la quantité exacte",
        "admin.goods.stock.set_success": "✅ Le stock de \"{item}\" a été défini à {quantity} unités",
        "admin.goods.stock.status_title": "📊 Statut du stock :",
        "errors.invalid_item_name": "❌ Nom de produit invalide",
        "errors.invalid_language": "Langue invalide",
        "shop.error.brand_required": "Veuillez d'abord sélectionner une marque",
        "shop.error.branch_unavailable": "Succursale non disponible",
        "profile.caption": "👤 <b>Profil</b> — <a href='tg://user?id={id}'>{name}</a>",
        "rules.not_set": "❌ Les règles n'ont pas encore été ajoutées",
        "admin.users.cannot_ban_owner": "❌ Impossible de bannir le propriétaire",
        "admin.users.ban.success": "✅ L'utilisateur {name} a été banni avec succès",
        "admin.users.ban.failed": "❌ Échec du bannissement de l'utilisateur",
        "admin.users.ban.notify": "⛔ Vous avez été banni par un administrateur",
        "admin.users.unban.success": "✅ L'utilisateur {name} a été débanni avec succès",
        "admin.users.unban.failed": "❌ Échec du débannissement de l'utilisateur",
        "admin.users.unban.notify": "✅ Vous avez été débanni par un administrateur",

        # === Profile ===
        "btn.referral": "🎲 Système de parrainage",
        "btn.purchased": "🎁 Achats effectués",
        "profile.referral_id": "👤 <b>Parrain</b> — <code>{id}</code>",

        # === Subscription Flow ===
        "subscribe.prompt": "Abonnez-vous d'abord au canal d'actualités",

        # === Profile Info Lines ===
        "profile.id": "🆔 <b>ID</b> — <code>{id}</code>",
        "profile.bonus_balance": "💰 <b>Bonus de parrainage :</b> ${bonus_balance}",
        "profile.purchased_count": "🎁 <b>Articles achetés</b> — {count} pcs",
        "profile.registration_date": "🕢 <b>Inscrit le</b> — <code>{dt}</code>",

        # === Referral ===
        "referral.title": "💚 Système de parrainage",
        "referral.count": "Nombre de filleuls : {count}",
        "referral.description": "📔 Le système de parrainage vous permet de gagner sans investissement. Partagez votre lien personnel et recevez {percent}% des recharges de vos filleuls sur votre solde du bot.",
        "btn.view_referrals": "👥 Mes filleuls",
        "btn.view_earnings": "💰 Mes revenus",

        "referrals.list.title": "👥 Vos filleuls :",
        "referrals.list.empty": "Vous n'avez pas encore de filleuls actifs",
        "referrals.item.format": "ID : {telegram_id} | Gagné : {total_earned} {currency}",

        "referral.earnings.title": "💰 Revenus du filleul <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>) :",
        "referral.earnings.empty": "Pas encore de revenus de ce filleul <code>{id}</code> (<a href='tg://user?id={id}'>{name}</a>)",
        "referral.earning.format": "{amount} {currency} | {date} | (de {original_amount} {currency})",
        "referral.item.info": "💰 Revenu n° : <code>{id}</code>\n👤 Filleul : <code>{telegram_id}</code> (<a href='tg://user?id={telegram_id}'>{name}</a>)\n🔢 Montant : {amount} {currency}\n🕘 Date : <code>{date}</code>\n💵 D'un dépôt de {original_amount} {currency}",

        "referral.admin_bonus.info": "💰 Revenu n° : <code>{id}</code>\n🎁 <b>Bonus de l'administrateur</b>\n🔢 Montant : {amount} {currency}\n🕘 Date : <code>{date}</code>",

        "all.earnings.title": "💰 Tous vos revenus de parrainage :",
        "all.earnings.empty": "Vous n'avez pas encore de revenus de parrainage",
        "all.earning.format.admin": "{amount} {currency} de l'admin | {date}",

        "referrals.stats.template": "📊 Statistiques du système de parrainage :\n\n👥 Filleuls actifs : {active_count}\n💰 Total gagné : {total_earned} {currency}\n📈 Total des recharges des filleuls : {total_original} {currency}\n🔢 Nombre de revenus : {earnings_count}",

        # === Admin: Main Menu ===
        "admin.menu.main": "⛩️ Menu administrateur",
        "admin.menu.shop": "🛒 Gestion de la boutique",
        "admin.menu.goods": "📦 Gestion des articles",
        "admin.menu.categories": "📂 Gestion des catégories",
        "admin.menu.users": "👥 Gestion des utilisateurs",
        "admin.menu.broadcast": "📝 Diffusion",
        "admin.menu.rights": "Permissions insuffisantes",

        # === Admin: User Management ===
        "admin.users.prompt_enter_id": "👤 Entrez l'ID de l'utilisateur pour voir / modifier les données",
        "admin.users.invalid_id": "⚠️ Veuillez entrer un ID utilisateur numérique valide.",
        "admin.users.profile_unavailable": "❌ Profil indisponible (cet utilisateur n'a jamais existé)",
        "admin.users.not_found": "❌ Utilisateur non trouvé",
        "admin.users.cannot_change_owner": "Vous ne pouvez pas modifier le rôle du propriétaire",
        "admin.users.referrals": "👥 <b>Filleuls de l'utilisateur</b> — {count}",
        "admin.users.btn.view_referrals": "👥 Filleuls de l'utilisateur",
        "admin.users.btn.view_earnings": "💰 Revenus de l'utilisateur",
        "admin.users.role": "🎛 <b>Rôle</b> — {role}",
        "admin.users.set_admin.success": "✅ Rôle attribué à {name}",
        "admin.users.set_admin.notify": "✅ Le rôle d'administrateur vous a été attribué",
        "admin.users.remove_admin.success": "✅ Rôle d'administrateur révoqué de {name}",
        "admin.users.remove_admin.notify": "❌ Votre rôle d'administrateur a été révoqué",
        "admin.users.bonus.prompt": "Entrez le montant du bonus en {currency} :",
        "admin.users.bonus.added": "✅ Le bonus de parrainage de {name} a été crédité de {amount} {currency}",
        "admin.users.bonus.added.notify": "🎁 Un bonus de parrainage de {amount} {currency} vous a été crédité",
        "admin.users.bonus.invalid": "❌ Montant invalide. Entrez un nombre entre {min_amount} et {max_amount} {currency}.",

        # === Admin: Shop Management Menu ===
        "admin.shop.menu.title": "⛩️ Gestion de la boutique",
        "admin.shop.menu.statistics": "📊 Statistiques",
        "admin.shop.menu.logs": "📁 Afficher les journaux",
        "admin.shop.menu.admins": "👮 Administrateurs",
        "admin.shop.menu.users": "👤 Utilisateurs",

        # === Admin: Categories Management ===
        "admin.categories.menu.title": "⛩️ Gestion des catégories",
        "admin.categories.add": "➕ Ajouter une catégorie",
        "admin.categories.rename": "✏️ Renommer une catégorie",
        "admin.categories.delete": "🗑 Supprimer une catégorie",
        "admin.categories.prompt.add": "Entrez le nom de la nouvelle catégorie :",
        "admin.categories.prompt.delete": "Entrez le nom de la catégorie à supprimer :",
        "admin.categories.prompt.rename.old": "Entrez le nom actuel de la catégorie à renommer :",
        "admin.categories.prompt.rename.new": "Entrez le nouveau nom de la catégorie :",
        "admin.categories.add.exist": "❌ Catégorie non créée (elle existe déjà)",
        "admin.categories.add.success": "✅ Catégorie créée",
        "admin.categories.delete.not_found": "❌ Catégorie non supprimée (elle n'existe pas)",
        "admin.categories.delete.success": "✅ Catégorie supprimée",
        "admin.categories.rename.not_found": "❌ Catégorie non mise à jour (elle n'existe pas)",
        "admin.categories.rename.exist": "❌ Impossible de renommer (une catégorie avec ce nom existe déjà)",
        "admin.categories.rename.success": "✅ Catégorie \"{old}\" renommée en \"{new}\"",

        # === Admin: Goods / Items Management (Add / List / Item Info) ===
        "admin.goods.add_position": "➕ Ajouter un article",
        "admin.goods.manage_stock": "➕ Ajouter du stock à l'article",
        "admin.goods.update_position": "📝 Modifier un article",
        "admin.goods.delete_position": "❌ Supprimer un article",
        "admin.goods.add.prompt.type": "Choisissez le type d'article :",
        "admin.goods.add.type.prepared": "🍳 Préparé à la commande (plats, boissons)",
        "admin.goods.add.type.product": "📦 Produit emballé (eau, snacks)",
        "admin.goods.add.prompt.name": "Entrez le nom de l'article",
        "admin.goods.add.name.exists": "❌ L'article n'a pas pu être créé (il existe déjà)",
        "admin.goods.add.prompt.description": "Entrez la description de l'article :",
        "admin.goods.add.prompt.price": "Entrez le prix de l'article (nombre en {currency}) :",
        "admin.goods.add.price.invalid": "⚠️ Prix invalide. Veuillez entrer un nombre.",
        "admin.goods.add.prompt.category": "Entrez la catégorie de l'article :",
        "admin.goods.add.category.not_found": "❌ L'article n'a pas pu être créé (catégorie invalide)",
        "admin.goods.position.not_found": "❌ Aucun article trouvé (cet article n'existe pas)",
        "admin.goods.menu.title": "⛩️ Menu de gestion des articles",
        "admin.goods.add.stock.prompt": "Entrez la quantité de stock à ajouter",
        "admin.goods.add.stock.invalid": "⚠️ Quantité incorrecte. Veuillez entrer un nombre.",
        "admin.goods.add.stock.negative": "⚠️ Quantité incorrecte. Entrez un nombre positif.",
        "admin.goods.add.result.created_with_stock": "✅ Article {item_name} créé, {stock_quantity} ajoutés au stock.",

        # === Admin: Goods / Items Update Flow ===
        "admin.goods.update.position.invalid": "Article non trouvé.",
        "admin.goods.update.position.exists": "Un article avec ce nom existe déjà.",
        "admin.goods.update.prompt.name": "Entrez le nom de l'article",
        "admin.goods.update.not_exists": "❌ L'article n'a pas pu être mis à jour (il n'existe pas)",
        "admin.goods.update.prompt.new_name": "Entrez le nouveau nom de l'article :",
        "admin.goods.update.prompt.description": "Entrez la description de l'article :",
        "admin.goods.update.success": "✅ Article mis à jour",

        # === Admin: Goods / Items Delete Flow ===
        "admin.goods.delete.prompt.name": "Entrez le nom de l'article",
        "admin.goods.delete.position.not_found": "❌ Article non supprimé (il n'existe pas)",
        "admin.goods.delete.position.success": "✅ Article supprimé",

        # === Admin: Item Info ===
        "admin.goods.view_stock": "Voir les articles",

        # Admin Modifier Management (Card 8)
        "admin.goods.manage_modifiers": "🍳 Options",
        "admin.goods.modifiers.prompt": "Souhaitez-vous ajouter des options (epices, supplements, etc.) ?",
        "admin.goods.modifiers.add_btn": "➕ Ajouter des options",
        "admin.goods.modifiers.skip_btn": "⏭ Passer",
        "admin.goods.modifiers.json_prompt": "Collez le schema JSON des options :",
        "admin.goods.modifiers.invalid_json": "❌ JSON invalide : {error}",
        "admin.goods.modifiers.select_item": "Entrez le nom du produit pour configurer les options :",
        "admin.goods.modifiers.edit_instructions": "Choisissez une action :",
        "admin.goods.modifiers.set_new": "📝 Definir nouveau",
        "admin.goods.modifiers.clear": "🗑 Tout effacer",

        # === Admin: Logs ===
        "admin.shop.logs.caption": "Journaux du bot",
        "admin.shop.logs.empty": "❗️ Aucun journal disponible",

        # === Group Notifications ===
        "shop.group.new_upload": "Nouveau stock",
        "shop.group.item": "Article",
        "shop.group.stock": "Quantité",

        # === Admin: Statistics ===
        "admin.shop.stats.template": "Statistiques de la boutique :\n➖➖➖➖➖➖➖➖➖➖➖➖➖\n<b>◽UTILISATEURS</b>\n◾️Utilisateurs des dernières 24h : {today_users}\n◾️Total administrateurs : {admins}\n◾️Total utilisateurs : {users}\n➖➖➖➖➖➖➖➖➖➖➖➖➖\n◽<b>DIVERS</b>\n◾Articles : {items} pcs\n◾Positions : {goods} pcs\n◾Catégories : {categories} pcs\n",

        # === Admin: Lists & Broadcast ===
        "admin.shop.admins.title": "👮 Administrateurs du bot :",
        "admin.shop.users.title": "Utilisateurs du bot :",
        "broadcast.prompt": "Envoyez un message à diffuser :",
        "broadcast.creating": "📤 Démarrage de la diffusion...\n👥 Total utilisateurs : {ids}",
        "broadcast.progress": "📤 Diffusion en cours...\n\n\n📊 Progression : {progress:.1f}%{n}✅ Envoyés : {sent}/{total}\n❌ Erreurs : {failed}\n⏱ Temps écoulé : {time} sec",
        "broadcast.done": "✅ Diffusion terminée !\n\n📊 Statistiques :📊\n👥 Total : {total}\n✅ Livrés : {sent}\n❌ Non livrés : {failed}\n🚫 Bot bloqué : ~{blocked}\n📈 Taux de réussite : {success}%\n⏱ Durée : {duration} sec",
        "broadcast.cancel": "❌ La diffusion a été annulée.",
        "broadcast.warning": "Aucune diffusion active",

        # === Brand / Store Selection ===
        "shop.brands.title": "🏪 Choisissez un restaurant",
        "shop.branches.title": "📍 Choisissez une succursale",
        "shop.no_brands": "Aucun restaurant disponible pour le moment.",
        "shop.brand_unavailable": "Ce restaurant est actuellement indisponible.",

        # === Shop Browsing (Categories / Goods / Item Page) ===
        "shop.categories.title": "🏪 Catégories de la boutique",
        "shop.goods.choose": "🏪 Choisissez un produit",
        "shop.item.not_found": "Article non trouvé",
        "shop.item.title": "🏪 Article {name}",
        "shop.item.description": "Description : {description}",
        "shop.item.price": "Prix — {amount} {currency}",
        "shop.item.quantity_unlimited": "Quantité — illimitée",
        "shop.item.quantity_left": "Quantité — {count} pcs",
        "shop.item.quantity_detailed": "📦 Total en stock : {total} pcs\n🔒 Réservés : {reserved} pcs\n✅ Disponibles : {available} pcs",

        # === Purchases ===
        "purchases.title": "Articles achetés :",
        "purchases.pagination.invalid": "Données de pagination invalides",
        "purchases.item.not_found": "Achat non trouvé",
        "purchases.item.name": "<b>🧾 Article</b> : <code>{name}</code>",
        "purchases.item.price": "<b>💵 Prix</b> : <code>{amount}</code> {currency}",
        "purchases.item.datetime": "<b>🕒 Acheté le</b> : <code>{dt}</code>",
        "purchases.item.unique_id": "<b>🧾 ID unique</b> : <code>{uid}</code>",
        "purchases.item.value": "<b>🔑 Valeur</b> :\n<code>{value}</code>",

        # === Middleware ===
        "middleware.ban": "⏳ Vous êtes temporairement bloqué. Attendez {time} secondes.",
        "middleware.above_limits": "⚠️ Trop de requêtes ! Vous êtes temporairement bloqué.",
        "middleware.waiting": "⏳ Attendez {time} secondes avant la prochaine action.",
        "middleware.security.session_outdated": "⚠️ La session est expirée. Veuillez recommencer.",
        "middleware.security.invalid_data": "❌ Données invalides",
        "middleware.security.blocked": "❌ Accès bloqué",
        "middleware.security.not_admin": "⛔ Permissions insuffisantes",
        "middleware.security.banned": "⛔ <b>Vous avez été banni</b>\n\nRaison : {reason}",
        "middleware.security.banned_no_reason": "⛔ <b>Vous avez été banni</b>\n\nVeuillez contacter l'administrateur pour plus d'informations.",
        "middleware.security.rate_limit": "⚠️ Trop de requêtes ! Veuillez patienter un instant.",

        # === Errors ===
        "errors.not_subscribed": "Vous n'êtes pas abonné",
        "errors.pagination_invalid": "Données de pagination invalides",
        "errors.invalid_data": "❌ Données invalides",
        "errors.channel.telegram_not_found": "Impossible d'écrire dans le canal. Ajoutez-moi comme administrateur du canal @{channel} avec le droit de publier des messages.",
        "errors.channel.telegram_forbidden_error": "Canal non trouvé. Vérifiez le nom du canal @{channel}.",
        "errors.channel.telegram_bad_request": "Échec de l'envoi au canal : {e}",

        # === Orders ===
        "order.payment_method.choose": "💳 Choisissez le mode de paiement :",
        "order.payment_method.bitcoin": "💳 Bitcoin",
        "order.payment_method.litecoin": "💳 Litecoin",
        "order.payment_method.solana": "💳 SOL",
        "order.payment_method.usdt_sol": "💳 USDT (Solana)",
        "order.payment_method.cash": "💵 Paiement à la livraison",
        "order.status.notify_order_confirmed": "Commande {order_code} confirmée ! 🎉\n\nVotre commande sera livrée le : {delivery_time}\n\nArticles :\n{items}\n\nTotal : {total}\n\nPatientez pour la livraison !",
        "order.status.notify_order_delivered": "Commande {order_code} livrée ! ✅\n\nMerci pour votre achat ! Nous espérons vous revoir bientôt ! 🙏",
        "order.status.notify_order_modified": "Commande {order_code} modifiée par l'admin 📝\n\nModifications :\n{changes}\n\nNouveau total : {total}",

        # === Additional Common Buttons ===
        "btn.cart": "🛒 Panier",
        "btn.my_orders": "📦 Mes commandes",
        "btn.reference_codes": "🔑 Codes de référence",
        "btn.settings": "⚙️ Paramètres",
        "btn.referral_bonus_percent": "💰 % du bonus de parrainage",
        "btn.order_timeout": "⏱️ Délai de commande",
        "btn.timezone": "🌍 Fuseau horaire",
        "btn.promptpay_account": "💳 Compte PromptPay",
        "btn.currency": "💱 Devise",
        "btn.skip": "⏭️ Passer",
        "btn.use_saved_info": "✅ Utiliser les infos enregistrées",
        "btn.update_info": "✏️ Mettre à jour les infos",
        "btn.back_to_cart": "◀️ Retour au panier",
        "btn.clear_cart": "🗑️ Vider le panier",
        "btn.proceed_checkout": "💳 Passer à la caisse",
        "btn.remove_item": "❌ Supprimer {item_name}",
        "btn.use_all_bonus": "Utiliser la totalité ${amount}",
        "btn.apply_bonus_yes": "✅ Oui, appliquer le bonus",
        "btn.apply_bonus_no": "❌ Non, garder pour plus tard",
        "btn.cancel": "❌ Annuler",
        "btn.add_to_cart": "🛒 Ajouter au panier",

        # === Cart Management ===
        "cart.add_success": "✅ {item_name} ajouté au panier !",
        "cart.add_error": "❌ {message}",
        "cart.empty": "🛒 Votre panier est vide.\n\nParcourez la boutique pour ajouter des articles !",
        "cart.title": "🛒 <b>Votre panier</b>\n\n",
        "cart.removed_success": "Article retiré du panier",
        "cart.cleared_success": "✅ Panier vidé avec succès !",
        "cart.empty_alert": "Le panier est vide !",
        "cart.summary_title": "📦 <b>Récapitulatif de la commande</b>\n\n",
        "cart.saved_delivery_info": "Vos informations de livraison enregistrées :\n\n",
        "cart.delivery_address": "📍 Adresse : {address}\n",
        "cart.delivery_phone": "📞 Téléphone : {phone}\n",
        "cart.delivery_note": "📝 Note : {note}\n",
        "cart.use_info_question": "\n\nSouhaitez-vous utiliser ces informations ou les mettre à jour ?",
        "cart.no_saved_info": "❌ Aucune information de livraison enregistrée. Veuillez saisir manuellement.",

        # === Order/Delivery Flow ===
        "order.delivery.address_prompt": "📍 Veuillez entrer votre adresse de livraison :",
        "order.delivery.address_invalid": "❌ Veuillez fournir une adresse valide (au moins 5 caractères).",
        "order.delivery.phone_prompt": "📞 Veuillez entrer votre numéro de téléphone (avec l'indicatif pays) :",
        "order.delivery.phone_invalid": "❌ Veuillez fournir un numéro de téléphone valide (au moins 8 chiffres).",
        "order.delivery.note_prompt": "📝 Des instructions de livraison spéciales ? (Optionnel)\n\nVous pouvez passer en cliquant sur le bouton ci-dessous.",
        "order.delivery.info_save_error": "❌ Erreur lors de l'enregistrement des informations de livraison. Veuillez réessayer.",

        # Location Method Choice
        "order.delivery.location_method_prompt": "📍 Comment souhaitez-vous indiquer votre adresse de livraison ?\n\nChoisissez une option ci-dessous :",
        "btn.location_method.gps": "📡 Envoyer GPS via Telegram",
        "btn.location_method.live_gps": "📍 Partager la position en direct",
        "btn.location_method.google_link": "🗺 Partager un lien Google Maps",
        "btn.location_method.type_address": "✍️ Saisir une adresse",
        "order.delivery.gps_prompt": "📍 Appuyez sur le bouton ci-dessous pour partager votre position :",
        "order.delivery.gps_hint": "📍 Veuillez utiliser le bouton ci-dessous pour partager votre position GPS, ou appuyez sur 'Retour' pour choisir une autre méthode.",
        "order.delivery.live_gps_prompt": "📍 Pour partager votre position en direct :\n\n1. Appuyez sur l'icône de pièce jointe 📎 ci-dessous\n2. Sélectionnez 'Position'\n3. Appuyez sur 'Partager ma position en direct'\n4. Choisissez une durée\n\nLe livreur pourra voir votre position en temps réel !",
        "order.delivery.live_gps_saved": "✅ Position en direct reçue ! Le livreur pourra suivre votre position.",
        "order.delivery.live_gps_hint": "📍 Veuillez partager votre position en direct via le menu des pièces jointes (📎 → Position → Partager la position en direct).",
        "order.delivery.google_link_prompt": "🗺 Collez un lien Google Maps avec votre emplacement.\n\nOuvrez Google Maps, trouvez l'emplacement, appuyez sur 'Partager' et copiez le lien ici.",
        "order.delivery.google_link_invalid": "❌ Impossible de reconnaître le lien Google Maps. Assurez-vous qu'il commence par google.com/maps ou goo.gl/maps.",
        "order.delivery.address_confirm_prompt": "📍 Votre adresse :\n<b>{address}</b>\n\n🔗 <a href=\"{maps_link}\">Voir sur la carte</a>\n\nEst-ce correct ?",
        "btn.address_confirm_yes": "✅ Oui, c'est correct",
        "btn.address_confirm_retry": "✏️ Non, ressaisir l'adresse",

        # GPS Location (Card 2)
        "order.delivery.location_prompt": "📍 Souhaitez-vous partager votre position GPS pour une livraison plus précise ?\n\nAppuyez sur le bouton ci-dessous ou passez cette étape.",
        "order.delivery.location_saved": "✅ Position enregistrée !",
        "btn.share_location": "📍 Partager la position",
        "btn.skip_location": "⏭ Passer",

        # Delivery Type (Card 3)
        "order.delivery.type_prompt": "🚚 Choisissez le type de livraison :",
        "btn.delivery.door": "🚪 Livraison à domicile",
        "btn.delivery.dead_drop": "📦 Déposer sur place",
        "btn.delivery.pickup": "🏪 Retrait sur place",
        "order.delivery.drop_instructions_prompt": "📝 Décrivez où déposer votre commande (ex. : 'avec le gardien dans le hall', 'sous le paillasson chambre 405') :",
        "order.delivery.drop_photo_prompt": "📸 Voulez-vous envoyer une photo du lieu de dépôt ? (optionnel)",
        "order.delivery.drop_photo_saved": "✅ Photo du lieu de dépôt enregistrée !",
        "btn.skip_drop_photo": "⏭ Passer la photo",

        # PromptPay (Card 1)
        "order.payment_method.promptpay": "💳 PromptPay QR",
        "order.payment.promptpay.title": "💳 <b>Paiement PromptPay</b>",
        "order.payment.promptpay.scan": "📱 Scannez le code QR pour payer :",
        "order.payment.promptpay.upload_receipt": "📸 Après le paiement, veuillez télécharger votre reçu/capture d'écran :",
        "order.payment.promptpay.receipt_received": "✅ Reçu reçu ! En attente de vérification par l'administrateur.",
        "order.payment.promptpay.receipt_invalid": "❌ Veuillez envoyer une photo de votre reçu de paiement.",
        "order.payment.promptpay.slip_verified": "✅ Paiement vérifié automatiquement ! Votre commande est confirmée.",
        "admin.order.verify_payment": "✅ Vérifier le paiement",
        "admin.order.payment_verified": "✅ Paiement vérifié",

        # Delivery Chat (Card 13)
        "order.delivery.chat_unavailable": "❌ Chat avec le livreur indisponible. Le groupe de livraison n'est pas configuré.",
        "order.delivery.chat_started": "💬 Vous pouvez envoyer un message à votre livreur. Envoyez du texte, une photo ou une position.",
        "order.delivery.live_location_shared": "📍 Le livreur partage sa position en direct ! Vous pouvez suivre votre livraison.",
        "order.delivery.chat_no_active_delivery": "❌ Vous n'avez aucune livraison active pour discuter.",
        "order.delivery.chat_ended": "✅ Chat avec le livreur terminé.",
        "order.delivery.chat_message_sent": "✅ Message envoyé au livreur.",
        "order.delivery.driver_no_active_order": "⚠️ Aucune commande active pour transmettre ce message.",
        "btn.chat_with_driver": "💬 Discuter avec le livreur",
        "order.delivery.drop_gps_prompt": "📍 Partagez la position GPS du point de dépôt en appuyant sur le bouton ci-dessous :",
        "order.delivery.drop_gps_saved": "✅ Position GPS enregistrée !",
        "order.delivery.drop_media_prompt": "📸 Envoyez des photos ou vidéos du lieu de dépôt (plusieurs fichiers possibles). Appuyez sur « Terminé » quand vous avez fini :",
        "order.delivery.drop_media_saved": "✅ {count} fichier(s) enregistré(s). Envoyez-en d'autres ou appuyez sur « Terminé ».",
        "btn.share_drop_location": "📍 Partager la position",
        "btn.drop_media_done": "✅ Terminé",
        "btn.skip_drop_media": "⏭ Passer",
        "btn.end_chat": "❌ Terminer le chat",

        # GPS tracking & chat session (Card 15)

        # === Bonus/Referral Application ===
        "order.bonus.available": "💰 <b>Vous avez ${bonus_balance} en bonus de parrainage !</b>\n\n",
        "order.bonus.apply_question": "Souhaitez-vous appliquer le bonus de parrainage à cette commande ?",
        "order.bonus.amount_positive_error": "❌ Veuillez entrer un montant positif.",
        "order.bonus.amount_too_high": "❌ Montant trop élevé. Maximum applicable : ${max_applicable}\nVeuillez entrer un montant valide :",
        "order.bonus.invalid_amount": "❌ Montant invalide. Veuillez entrer un nombre (ex. : 5.50) :",
        "order.bonus.insufficient": "❌ Solde bonus insuffisant. Veuillez réessayer.",
        "order.bonus.enter_amount": "Entrez le montant du bonus à appliquer (maximum ${max_applicable}) :\n\nOu utilisez tous les bonus disponibles en cliquant sur le bouton ci-dessous.",

        # === Payment Instructions ===
        "order.payment.system_unavailable": "❌ <b>Système de paiement temporairement indisponible</b>\n\nAucune adresse Bitcoin disponible. Veuillez contacter le support.",
        "order.payment.customer_not_found": "❌ Informations client introuvables. Veuillez réessayer.",
        "order.payment.creation_error": "❌ Erreur lors de la création de la commande. Veuillez réessayer ou contacter le support.",

        # === Order Summary/Total ===
        "order.summary.title": "📦 <b>Récapitulatif de la commande</b>\n\n",
        "order.summary.cart_total": "Total du panier : ${cart_total}",
        "order.summary.bonus_applied": "Bonus appliqué : -${bonus_applied}",
        "order.summary.final_amount": "Montant final : ${final_amount}",

        # === Inventory/Reservation ===
        "order.inventory.unable_to_reserve": "❌ <b>Impossible de réserver les articles</b>\n\nLes articles suivants ne sont pas disponibles dans les quantités demandées :\n\n{unavailable_items}\n\nVeuillez ajuster votre panier et réessayer.",

        # === My Orders View ===
        "myorders.title": "📦 <b>Mes commandes</b>\n\n",
        "myorders.total": "Total des commandes : {count}",
        "myorders.active": "⏳ Commandes actives : {count}",
        "myorders.delivered": "✅ Livrées : {count}",
        "myorders.select_category": "Sélectionnez une catégorie pour voir les commandes :",
        "myorders.active_orders": "⏳ Commandes actives",
        "myorders.delivered_orders": "✅ Commandes livrées",
        "myorders.all_orders": "📋 Toutes les commandes",
        "myorders.no_orders_yet": "Vous n'avez pas encore passé de commande.\n\nParcourez la boutique pour commencer vos achats !",
        "myorders.browse_shop": "🛍️ Aller à la boutique",
        "myorders.back": "◀️ Retour",
        "myorders.all_title": "📋 Toutes les commandes",
        "myorders.active_title": "⏳ Commandes actives",
        "myorders.delivered_title": "✅ Commandes livrées",
        "myorders.invalid_filter": "Filtre invalide",
        "myorders.not_found": "Commandes non trouvées.",
        "myorders.back_to_menu": "◀️ Retour au menu des commandes",
        "myorders.select_details": "Sélectionnez une commande pour voir les détails :",
        "myorders.order_not_found": "Commande non trouvée",

        # === Order Details Display ===
        "myorders.detail.title": "📦 <b>Détails de la commande #{order_code}</b>\n\n",
        "myorders.detail.status": "📊 <b>Statut :</b> {status}\n",
        "myorders.detail.subtotal": "💵 <b>Sous-total :</b> ${subtotal}\n",
        "myorders.detail.bonus_applied": "🎁 <b>Bonus appliqué :</b> ${bonus}\n",
        "myorders.detail.final_price": "💰 <b>Prix final :</b> ${total}\n",
        "myorders.detail.total_price": "💰 <b>Prix total :</b> ${total}\n",
        "myorders.detail.payment_method": "💳 <b>Mode de paiement :</b> {method}\n",
        "myorders.detail.ordered": "📅 <b>Commandé le :</b> {date}\n",
        "myorders.detail.delivery_time": "🚚 <b>Livraison prévue :</b> {time}\n",
        "myorders.detail.completed": "✅ <b>Terminée le :</b> {date}\n",
        "myorders.detail.items": "\n📦 <b>Articles :</b>\n{items}\n",
        "myorders.detail.delivery_info": "\n📍 <b>Informations de livraison :</b>\n{address}\n{phone}\n{note}",

        # === Help System ===
        "help.prompt": "📧 <b>Besoin d'aide ?</b>\n\n",
        "help.describe_issue": "Veuillez décrire votre problème ou question, il sera envoyé directement à l'administrateur.\n\nTapez votre message ci-dessous :",
        "help.admin_not_configured": "❌ Désolé, le contact administrateur n'est pas configuré. Veuillez réessayer plus tard.",
        "help.admin_notification_title": "📧 <b>Nouvelle demande d'aide</b>\n\n",
        "help.admin_notification_from": "<b>De :</b> @{username} (ID : {user_id})\n",
        "help.admin_notification_message": "<b>Message :</b>\n{message}",
        "help.sent_success": "✅ {auto_message}",
        "help.sent_error": "❌ Échec de l'envoi du message à l'administrateur : {error}\n\nVeuillez réessayer plus tard.",
        "help.cancelled": "Demande d'aide annulée.",

        # === Admin Order Notifications ===
        "admin.order.action_required_title": "⏳ <b>Action requise :</b>",
        "admin.order.address_label": "Adresse : {address}",
        "admin.order.amount_to_collect_label": "<b>Montant à encaisser : ${amount} {currency}</b>",
        "admin.order.amount_to_receive_label": "<b>Montant à recevoir : ${amount} {currency}</b>",
        "admin.order.awaiting_payment_status": "⏳ En attente de confirmation du paiement...",
        "admin.order.bitcoin_address_label": "Adresse Bitcoin : <code>{address}</code>",
        "admin.order.bonus_applied_label": "Bonus appliqué : <b>-${amount}</b>",
        "admin.order.customer_label": "Client : {username} (ID : {id})",
        "admin.order.delivery_info_title": "<b>Informations de livraison :</b>",
        "admin.order.items_title": "<b>Articles :</b>",
        "admin.order.new_bitcoin_order": "🔔 <b>Nouvelle commande Bitcoin reçue</b>",
        "admin.order.new_cash_order": "🔔 <b>Nouvelle commande en espèces reçue</b> 💵",
        "admin.order.note_label": "Note : {note}",
        "admin.order.order_label": "Commande : <b>{code}</b>",
        "admin.order.payment_cash": "Paiement à la livraison",
        "admin.order.payment_method_label": "Mode de paiement : <b>{method}</b>",
        "admin.order.phone_label": "Téléphone : {phone}",
        "admin.order.subtotal_label": "Sous-total : <b>${amount} {currency}</b>",
        "admin.order.use_cli_confirm": "Utilisez le CLI pour confirmer la commande et définir l'heure de livraison :\n<code>python bot_cli.py order --order-code {code} --status-confirmed --delivery-time \"YYYY-MM-DD HH:MM\"</code>",
        "btn.admin.back_to_panel": "🔙 Retour au panneau d'administration",
        "btn.admin.create_refcode": "➕ Créer un code de référence",
        "btn.admin.list_refcodes": "📋 Lister tous les codes",
        "btn.back_to_orders": "◀️ Retour aux commandes",
        "btn.create_reference_code": "➕ Créer un code de référence",
        "btn.my_reference_codes": "🔑 Mes codes de référence",
        "btn.need_help": "❓ Besoin d'aide ?",
        "cart.item.price_format": "  Prix : {price} {currency} × {quantity}",
        "cart.item.subtotal_format": "  Sous-total : {subtotal} {currency}",
        "cart.item.modifiers": "  Options : {modifiers}",
        "cart.total_format": "<b>Total : {total} {currency}</b>",
        "cart.add_cancelled": "Ajout annule",
        "modifier.select_title": "Choisissez {label} :",
        "modifier.selected": "Choisi : {choice}",
        "modifier.required": "(obligatoire)",
        "modifier.optional": "(facultatif)",
        "modifier.done": "Terminer",
        "modifier.price_extra": "+{price}",
        "modifier.cancelled": "Selection des options annulee.",
        "help.pending_order.contact_support": "Utilisez la commande /help pour contacter le support.",
        "help.pending_order.issues_title": "<b>Des problèmes ?</b>",
        "help.pending_order.status": "Votre commande est en attente de paiement.",
        "help.pending_order.step1": "1. Envoyez le montant exact à l'adresse Bitcoin indiquée",
        "help.pending_order.step2": "2. Attendez la confirmation de la blockchain (généralement 10 à 60 minutes)",
        "help.pending_order.step3": "3. L'administrateur confirmera votre paiement et planifiera une heure de livraison",
        "help.pending_order.step4": "4. Vos articles seront livrés par coursier.",
        "help.pending_order.title": "❓ <b>Besoin d'aide avec votre commande ?</b>",
        "help.pending_order.what_to_do_title": "<b>Que faire :</b>",
        "myorders.detail.bitcoin_address_label": "Adresse Bitcoin :",
        "myorders.detail.bitcoin_admin_confirm": "Après le paiement, notre administrateur confirmera votre commande.",
        "myorders.detail.bitcoin_send_instruction": "⚠️ Veuillez envoyer <b>{amount} {currency}</b> en Bitcoin à cette adresse.",
        "myorders.detail.cash_awaiting_confirm": "Votre commande est en attente de confirmation de l'administrateur.",
        "myorders.detail.cash_payment_courier": "Le paiement sera effectué au coursier lors de la livraison.",
        "myorders.detail.cash_title": "💵 Paiement à la livraison",
        "myorders.detail.cash_will_notify": "Vous serez notifié lorsque votre commande sera confirmée et l'heure de livraison fixée.",
        "myorders.detail.confirmed_title": "✅ <b>Commande confirmée !</b>",
        "myorders.detail.delivered_thanks_message": "Merci pour votre achat ! Nous espérons vous revoir bientôt ! 🙏",
        "myorders.detail.delivered_title": "📦 <b>Commande livrée !</b>",
        "myorders.detail.payment_info_title": "<b>Informations de paiement :</b>",
        "myorders.detail.preparing_message": "Votre commande est en cours de préparation pour la livraison.",
        "myorders.detail.scheduled_delivery_label": "Livraison prévue : <b>{time}</b>",
        "myorders.order_summary_format": "{status_emoji} {code} - {items_count} articles - {total} {currency}",
        "order.bonus.available_label": "Bonus disponible : <b>${amount}</b>",
        "order.bonus.choose_amount_hint": "Vous pouvez choisir le montant à utiliser (jusqu'à ${max_amount})",
        "order.bonus.enter_amount_title": "💵 <b>Entrez le montant du bonus à appliquer</b>",
        "order.bonus.max_applicable_label": "Maximum applicable : <b>${amount}</b>",
        "order.bonus.order_total_label": "Total de la commande : <b>${amount} {currency}</b>",
        "order.info.view_status_hint": "💡 Vous pouvez consulter le statut de votre commande à tout moment avec la commande /orders.",
        "order.payment.bitcoin.address_title": "<b>Adresse de paiement Bitcoin :</b>",
        "order.payment.bitcoin.admin_confirm": "• Après le paiement, notre administrateur confirmera votre commande",
        "order.payment.bitcoin.delivery_title": "<b>Livraison :</b>",
        "order.payment.bitcoin.important_title": "⚠️ <b>IMPORTANT :</b>",
        "order.payment.bitcoin.items_title": "<b>Articles :</b>",
        "order.payment.bitcoin.need_help": "Besoin d'aide ? Utilisez /help pour contacter le support.",
        "order.payment.bitcoin.one_time_address": "• Cette adresse est à usage UNIQUE",
        "order.payment.bitcoin.order_code": "Commande : <b>{code}</b>",
        "order.payment.bitcoin.send_exact": "• Envoyez le montant EXACT indiqué ci-dessus",
        "order.payment.bitcoin.title": "💳 <b>Instructions de paiement Bitcoin</b>",
        "order.payment.bitcoin.total_amount": "Montant total : <b>{amount} {currency}</b>",

        # Crypto payment (Card 18) — generic strings for all coins
        "crypto.payment.title": "💳 <b>{coin_name} Payment</b>",
        "crypto.payment.order_code": "Order: <b>{code}</b>",
        "crypto.payment.total_fiat": "Total: <b>{amount} {currency}</b>",
        "crypto.payment.rate": "Rate: 1 {coin} = {rate} {currency}",
        "crypto.payment.amount_due": "Amount due: <b>{crypto_amount} {coin}</b>",
        "crypto.payment.address": "<b>Send to this address:</b>\n<code>{address}</code>",
        "crypto.payment.send_exact": "• Send EXACTLY this amount",
        "crypto.payment.one_time": "• This address is for ONE-TIME use",
        "crypto.payment.auto_confirm": "• Your order will be automatically confirmed once the payment is detected on-chain.",
        "crypto.payment.waiting": "⏳ Waiting for payment...\nThis address expires in {timeout} minutes.",
        "crypto.payment.no_address": "❌ No {coin} addresses available. Please contact support or choose another payment method.",
        "crypto.payment_detected": (
            "✅ <b>Payment detected!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "⏳ Waiting for confirmations..."
        ),
        "crypto.payment_confirmed": (
            "✅ <b>Payment confirmed!</b>\n"
            "TX: <code>{tx_hash}</code>\n"
            "Amount: {amount} {coin}\n"
            "Confirmations: {confirmations}/{required}\n\n"
            "Your order is now being processed."
        ),
        "crypto.payment_expired": "⏰ Payment window for your {coin} order ({order_code}) has expired. Please place a new order.",

        "order.payment.cash.admin_contact": "L'administrateur vous contactera sous peu.",
        "order.payment.cash.after_confirm": "Après confirmation, vous serez notifié de l'heure de livraison.",
        "order.payment.cash.created": "Votre commande {code} a été créée et est en attente de confirmation de l'administrateur.",
        "order.payment.cash.important": "⏳ <b>Important :</b> La commande est réservée pour une durée limitée.",
        "order.payment.cash.items_title": "Articles :",
        "order.payment.cash.payment_to_courier": "Le paiement sera effectué au coursier lors de la livraison.",
        "order.payment.cash.title": "💵 <b>Paiement à la livraison</b>",
        "order.payment.cash.total": "Total : {amount}",
        "order.payment.error_general": "❌ Erreur lors de la création de la commande. Veuillez réessayer ou contacter le support.",
        "order.summary.total_label": "<b>Total : {amount} {currency}</b>",
        "order.payment.bonus_applied_label": "Bonus appliqué : <b>-{amount} {currency}</b>",
        "order.payment.cash.amount_with_bonus": "<b>Montant à payer à la livraison : {amount} {currency}</b>",
        "order.payment.cash.total_label": "<b>Total à payer à la livraison : {amount} {currency}</b>",
        "order.payment.final_amount_label": "<b>Montant final à payer : {amount} {currency}</b>",
        "order.payment.order_label": "📋 <b>Commande : {code}</b>",
        "order.payment.subtotal_label": "Sous-total : <b>{amount} {currency}</b>",
        "order.payment.total_amount_label": "<b>Montant total : {amount} {currency}</b>",

        # Delivery Photo Proof (Card 4)
        "delivery.photo.required": "Photo requise pour la livraison en point de depot",
        "delivery.photo.upload_prompt": "Veuillez telecharger la photo de livraison",
        "delivery.photo.received": "Photo de livraison enregistree",
        "delivery.photo.sent_to_customer": "Photo de livraison envoyee au client",
        "delivery.photo.customer_notification": "Votre commande {order_code} a ete livree ! Voici la photo de confirmation.",

        # === New Feature Strings ===

        # === Restaurant Feature Strings ===
        "admin.goods.add.allergen.dairy": "Dairy",
        "admin.goods.add.allergen.eggs": "Eggs",
        "admin.goods.add.allergen.fish": "Fish",
        "admin.goods.add.allergen.gluten": "Gluten",
        "admin.goods.add.allergen.nuts": "Nuts",
        "admin.goods.add.allergen.sesame": "Sesame",
        "admin.goods.add.allergen.shellfish": "Shellfish",
        "admin.goods.add.allergen.soy": "Soy",
        "admin.goods.add.allergens.done": "✅ Done",
        "admin.goods.add.allergens.skip": "⏭ No Allergens",
        "admin.goods.add.availability.invalid": "❌ Invalid format. Use HH:MM-HH:MM (e.g. 06:00-22:00)",
        "admin.goods.add.availability.skip": "⏭ All Day",
        "admin.goods.add.daily_limit.invalid": "❌ Enter a positive number.",
        "admin.goods.add.daily_limit.skip": "⏭ Unlimited",
        "admin.goods.add.modifier.add_another_group": "➕ Another Group",
        "admin.goods.add.modifier.add_group": "➕ Add Modifier Group",
        "admin.goods.add.modifier.add_option": "➕ Add Option",
        "admin.goods.add.modifier.all_done": "✅ Finish",
        "admin.goods.add.modifier.finish": "✅ Finish (No Modifiers)",
        "admin.goods.add.modifier.group_added": "✅ Group added! Add another group or finish.",
        "admin.goods.add.modifier.group_name": "Enter modifier group name (e.g. Spice Level):",
        "admin.goods.add.modifier.group_type": "Select type for this group:",
        "admin.goods.add.modifier.option_added": "✅ Option added! Add another or press Done.",
        "admin.goods.add.modifier.option_label": "Enter option label (e.g. Mild, Extra Cheese):",
        "admin.goods.add.modifier.option_price": "Enter price adjustment for this option (0 for free):",
        "admin.goods.add.modifier.options_done": "✅ Done with Options",
        "admin.goods.add.modifier.paste_json": "📋 Paste JSON",
        "admin.goods.add.modifier.required_no": "⭕ Optional",
        "admin.goods.add.modifier.required_yes": "✅ Required",
        "admin.goods.add.modifier.type_multi": "Multi Choice",
        "admin.goods.add.modifier.type_single": "Single Choice",
        "admin.goods.add.photo.done": "✅ Done",
        "admin.goods.add.photo.received": "✅ Media received! Send more or press Done.",
        "admin.goods.add.photo.send_more": "Send more photos/videos or press Done:",
        "admin.goods.add.photo.skip": "⏭ Skip Photos",
        "admin.goods.add.prep_time.invalid": "❌ Enter a positive number.",
        "admin.goods.add.prep_time.skip": "⏭ Skip",
        "admin.goods.add.prompt.allergens": "⚠️ Select allergens (tap to toggle, then Done):",
        "admin.goods.add.prompt.availability": "🕐 Enter availability hours (e.g. 06:00-22:00) or press Skip for all-day:",
        "admin.goods.add.prompt.daily_limit": "📊 Enter daily limit (max units per day) or press Skip for unlimited:",
        "admin.goods.add.prompt.modifier_group": "Add a modifier group (e.g. Spice Level, Extras)?",
        "admin.goods.add.prompt.photo": "📸 Send a photo or video of this item (or press Skip):",
        "admin.goods.add.prompt.prep_time": "⏱ Enter prep time in minutes (or press Skip):",
        "admin.goods.toggle.active_off": "🚫 {item}: Deactivated",
        "admin.goods.toggle.active_on": "✅ {item}: Activated",
        "admin.goods.toggle.sold_out_off": "✅ {item}: Back in stock",
        "admin.goods.toggle.sold_out_on": "❌ {item}: Marked SOLD OUT",
        "btn.view_gallery": "📸 Gallery ({count})",
        "kitchen.order.modifier_detail": "    ↳ {modifiers}",
        "kitchen.order.prep_time": "⏱ Est. prep: {minutes} min",
        "kitchen.order.ready_by": "🕐 Ready by: {time}",
        "order.estimated_ready": "⏱ Estimated ready in ~{minutes} min",
        "shop.item.allergens": "⚠️ Allergens: {allergens}",
        "shop.item.availability": "🕐 Available: {from_time} - {until_time}",
        "shop.item.calories": "🔥 {calories} cal",
        "shop.item.daily_remaining": "📊 Today: {remaining}/{limit} left",
        "shop.item.no_gallery": "No gallery for this item.",
        "shop.item.type_product": "📦 Type : Produit emballé",
        "shop.item.type_prepared": "🍳 Type : Préparé à la commande",
        "shop.item.prep_time": "⏱ Prep: ~{minutes} min",
        "shop.item.sold_out": "❌ Sold out today",
        "admin.accounting.export_payments": "📥 Payment Reconciliation",
        "admin.accounting.export_products": "📥 Revenue by Product",
        "admin.accounting.export_sales": "📥 Export Sales CSV",
        "admin.accounting.export_sent": "✅ Report exported.",
        "admin.accounting.no_data": "No data for this period.",
        "admin.accounting.summary": "📊 <b>Revenue Summary ({period})</b>\n\n💰 Revenue: {total} {currency}\n📦 Orders: {orders}\n📈 Avg: {avg} {currency}\n\n<b>By Payment:</b>\n{payments}\n\n<b>Top Products:</b>\n{products}",
        "admin.accounting.summary_all": "📊 All Time",
        "admin.accounting.summary_month": "📊 This Month",
        "admin.accounting.summary_today": "📊 Today",
        "admin.accounting.summary_week": "📊 This Week",
        "admin.accounting.title": "📊 <b>Accounting & Reports</b>",
        "admin.coupon.create": "➕ Create Coupon",
        "admin.coupon.created": "✅ Coupon <b>{code}</b> created!\nType: {type}\nValue: {value}\nMin order: {min_order}\nMax uses: {max_uses}\nExpires: {expiry}",
        "admin.coupon.detail": "🎟 <b>{code}</b>\nType: {type}\nValue: {value}\nMin Order: {min_order}\nMax Uses: {max_uses}\nUsed: {used}\nStatus: {status}\nExpires: {expiry}",
        "admin.coupon.empty": "No coupons found.",
        "admin.coupon.enter_code": "Enter coupon code (or type <b>auto</b> for random):",
        "admin.coupon.enter_expiry": "Enter expiry in days (or <b>skip</b> for no expiry):",
        "admin.coupon.enter_max_uses": "Enter max total uses (or <b>skip</b> for unlimited):",
        "admin.coupon.enter_min_order": "Enter minimum order amount (or <b>skip</b>):",
        "admin.coupon.enter_value": "Enter discount value ({type}):",
        "admin.coupon.invalid_value": "❌ Invalid value. Enter a number.",
        "admin.coupon.list_active": "📋 Active Coupons",
        "admin.coupon.list_all": "📋 All Coupons",
        "admin.coupon.select_type": "Select discount type:",
        "admin.coupon.title": "🎟 <b>Coupon Management</b>",
        "admin.coupon.toggle_activate": "✅ Activate",
        "admin.coupon.toggle_deactivate": "❌ Deactivate",
        "admin.coupon.toggled": "✅ Coupon {code} is now {status}.",
        "admin.coupon.type_fixed": "💰 Fixed Amount",
        "admin.coupon.type_percent": "📊 Percentage (%)",
        "admin.menu.accounting": "📊 Accounting",
        "admin.menu.coupons": "🎟 Coupons",
        "admin.menu.segment_broadcast": "📣 Targeted Broadcast",
        "admin.menu.stores": "🏪 Stores",
        "admin.menu.tickets": "🎫 Tickets",
        "admin.menu.ai_assistant": "🤖 AI Assistant",
        "admin.segment.all_users": "👥 All Users",
        "admin.segment.count": "📊 Segment: <b>{segment}</b>\nUsers: <b>{count}</b>\n\nType your broadcast message:",
        "admin.segment.empty": "No users in this segment.",
        "admin.segment.high_spenders": "💰 High Spenders",
        "admin.segment.inactive": "😴 Inactive (30+ days)",
        "admin.segment.new_users": "🆕 New Users (7d)",
        "admin.segment.recent_buyers": "🛒 Recent Buyers (7d)",
        "admin.segment.sent": "✅ Sent to {sent}/{total} ({segment}).",
        "admin.segment.title": "📣 <b>Targeted Broadcast</b>\n\nSelect segment:",
        "admin.store.add": "➕ Add Store",
        "admin.store.address_prompt": "Enter store address (or <b>skip</b>):",
        "admin.store.btn_default": "⭐ Set as Default",
        "admin.store.created": "✅ Store <b>{name}</b> created!",
        "admin.store.detail": "🏪 <b>{name}</b>\nStatus: {status}\nDefault: {default}\nAddress: {address}\nLocation: {location}\nPhone: {phone}",
        "admin.store.empty": "No stores configured.",
        "admin.store.location_prompt": "Send GPS location (or type <b>skip</b>):",
        "admin.store.name_exists": "Store with this name already exists.",
        "admin.store.name_prompt": "Enter store name:",
        "admin.store.set_default": "✅ {name} set as default store.",
        "admin.store.title": "🏪 <b>Store Management</b>",
        "admin.store.toggle_activate": "✅ Activate",
        "admin.store.toggle_deactivate": "❌ Deactivate",
        "admin.store.toggled": "✅ Store {name} is now {status}.",
        "admin.ticket.detail": "🎫 <b>Ticket #{code}</b>\nUser: {user_id}\nStatus: {status}\nPriority: {priority}\nSubject: {subject}\nCreated: {date}",
        "admin.ticket.empty": "No open tickets.",
        "admin.ticket.list": "Open/In Progress Tickets:",
        "admin.ticket.reply_prompt": "Reply to ticket #{code}:",
        "admin.ticket.resolved": "✅ Ticket #{code} resolved.",
        "admin.ticket.title": "🎫 <b>Support Tickets</b>",
        "btn.admin.reply_ticket": "💬 Reply",
        "btn.admin.resolve_ticket": "✅ Resolve",
        "btn.apply_coupon": "🎟 Apply Coupon",
        "btn.close_ticket": "✖ Close Ticket",
        "btn.create_ticket": "➕ New Ticket",
        "btn.create_ticket_for_order": "🎫 Support Ticket",
        "btn.invoice": "🧾 Receipt",
        "btn.my_tickets": "🎫 Support",
        "btn.reorder": "🔄 Reorder",
        "btn.reply_ticket": "💬 Reply",
        "btn.review_order": "⭐ Leave Review",
        "btn.search": "🔍 Search",
        "btn.skip_coupon": "⏭ Skip Coupon",
        "coupon.already_used": "❌ You already used this coupon.",
        "coupon.applied": "✅ Coupon applied! Discount: -{discount} {currency}",
        "coupon.enter_code": "🎟 Enter coupon code (or press Skip):",
        "coupon.expired": "❌ This coupon has expired.",
        "coupon.invalid": "❌ Invalid or expired coupon code.",
        "coupon.max_uses_reached": "❌ Coupon usage limit reached.",
        "coupon.min_order_not_met": "❌ Min order of {min_order} required.",
        "coupon.not_yet_valid": "❌ This coupon is not yet valid.",
        "invoice.not_available": "Receipt not available.",
        "reorder.success": "✅ Added {added} item(s) to cart. {skipped} item(s) unavailable.",
        "review.already_reviewed": "You have already reviewed this order.",
        "review.comment_prompt": "You rated {rating}/5 ⭐\n\nAdd a comment? Type or press Skip:",
        "review.detail": "⭐{rating}/5 — {comment}",
        "review.item_rating": "⭐ <b>{item}</b>: {avg:.1f}/5 ({count} reviews)",
        "review.no_reviews": "No reviews yet.",
        "review.prompt": "⭐ <b>Rate your order #{order_code}</b>\n\nSelect your rating:",
        "review.rate_1": "⭐",
        "review.rate_2": "⭐⭐",
        "review.rate_3": "⭐⭐⭐",
        "review.rate_4": "⭐⭐⭐⭐",
        "review.rate_5": "⭐⭐⭐⭐⭐",
        "review.skip_comment": "⏭ Skip",
        "review.thanks": "✅ Thank you for your review! ({rating}/5 ⭐)",
        "search.no_results": "❌ No products found. Try different keywords.",
        "search.prompt": "🔍 Enter product name or keyword to search:",
        "search.result_count": "Found {count} product(s):\n",
        "search.results_title": "🔍 <b>Search results for:</b> {query}\n\n",
        "ticket.admin_replied": "💬 Admin replied to ticket #{code}:\n{text}",
        "ticket.closed": "✅ Ticket closed.",
        "ticket.created": "✅ Ticket <b>#{code}</b> created!",
        "ticket.message_format": "<b>{role}</b> ({date}):\n{text}\n",
        "ticket.message_prompt": "Describe your issue:",
        "ticket.no_tickets": "No support tickets.",
        "ticket.reply_prompt": "Type your reply:",
        "ticket.reply_sent": "✅ Reply sent.",
        "ticket.resolved_notification": "✅ Ticket #{code} resolved!",
        "ticket.status.closed": "⚫ Closed",
        "ticket.status.in_progress": "🔵 In Progress",
        "ticket.status.open": "🟢 Open",
        "ticket.status.resolved": "✅ Resolved",
        "ticket.subject_prompt": "Enter the subject:",
        "ticket.title": "🎫 <b>Support Tickets</b>",
        "ticket.view_title": "🎫 <b>Ticket #{code}</b>\nStatus: {status}\nSubject: {subject}\nCreated: {date}",

        # Delivery GPS (Card 15)
        "delivery.gps.prompt": "📍 Votre commande {order_code} est en route !\n\nAidez votre livreur a vous trouver plus vite — partagez votre position :",
        "delivery.gps.btn_static": "📍 Envoyer la position",
        "delivery.gps.btn_live": "📡 Position en direct",
        "delivery.gps.btn_skip": "⏭ Passer",
        "delivery.gps.static_sent": "✅ Votre position a ete envoyee au livreur.",
        "delivery.gps.live_started": "📡 Position en direct activee ! Votre livreur peut vous suivre en temps reel.",
        "delivery.gps.skipped": "⏭ Position ignoree. Le livreur utilisera l'adresse de votre commande.",
        "delivery.chat.session_closed": "⏹ Cette session de chat est terminee. Contactez le support pour de l'aide.",
        "delivery.chat.post_delivery_open": "✅ Livre ! Le chat reste ouvert pendant {minutes} minutes supplementaires.",
        "delivery.chat.post_delivery_closed": "⏹ La fenetre de chat post-livraison est fermee.",

        # === Card 9: Kitchen & Delivery Workflow ===
        "admin.menu.orders": "📋 Commandes",
        "admin.orders.list_title": "📋 <b>Commandes</b>",
        "admin.orders.empty": "Aucune commande trouvee",
        "admin.orders.filter_status": "Filtrer par statut",
        "admin.orders.filter_all": "📋 Toutes les commandes",
        "admin.orders.filter_active": "🔄 Actives",
        "admin.orders.detail": (
            "📋 <b>Commande #{order_id}</b> ({order_code})\n"
            "👤 Acheteur : {buyer_id}\n"
            "💰 Total : {total}\n"
            "📦 Statut : {status}\n"
            "📅 Cree le : {created_at}\n"
            "📍 Adresse : {address}\n"
            "📞 Telephone : {phone}"
        ),
        "admin.orders.status_changed": "Le statut de la commande #{order_id} a ete change en <b>{new_status}</b>",
        "admin.orders.invalid_transition": "Impossible de changer le statut de {current} a {new}",
        "kitchen.order_received": (
            "🍳 <b>Nouvelle commande #{order_id}</b> ({order_code})\n\n"
            "{items}\n\n"
            "💰 Total : {total}\n"
            "📍 Adresse : {address}\n"
            "📞 Telephone : {phone}"
        ),
        "rider.order_ready": (
            "🚗 <b>Commande prete #{order_id}</b> ({order_code})\n\n"
            "💰 Total : {total}\n"
            "📍 Adresse : {address}\n"
            "📞 Telephone : {phone}"
        ),
        "order.status.preparing": "🍳 Votre commande #{order_code} est en cours de preparation",
        "order.status.ready": "✅ Votre commande #{order_code} est prete pour le retrait",
        "order.status.out_for_delivery": "🚗 Votre commande #{order_code} est en route",
        "order.status.delivered_notify": "📦 Votre commande #{order_code} a ete livree",
        "kitchen.btn.start_preparing": "🍳 Commencer la preparation",
        "kitchen.btn.mark_ready": "✅ Pret",
        "rider.btn.picked_up": "📦 Recupere",
        "rider.btn.delivered": "✅ Livre",

        # === PDPA Privacy Policy ===
        "btn.privacy": "🔒 Politique de confidentialité",
        "privacy.notice": (
            "🔒 <b>Avis de confidentialité (PDPA)</b>\n\n"
            "Nous respectons la loi thaïlandaise sur la protection des données personnelles (PDPA).\n\n"
            "<b>Données collectées :</b>\n"
            "• Nom / téléphone / adresse de livraison\n"
            "• Détails et historique des commandes\n"
            "• Identifiant Telegram\n\n"
            "<b>Finalités :</b>\n"
            "• Exécution des commandes et livraison (nécessité contractuelle)\n"
            "• Prévention de la fraude et vérification d'identité\n"
            "• Marketing — uniquement avec votre consentement séparé\n\n"
            "<b>Conservation :</b> Jusqu'à votre demande de suppression, ou 2 ans après votre dernière commande\n\n"
            "<b>Partage des données :</b> Restaurants, livreurs, prestataires de paiement — uniquement selon les besoins de votre commande. "
            "Nous ne vendons jamais vos données.\n\n"
            "<b>Vos droits PDPA :</b>\n"
            "• Accéder / corriger / supprimer vos données\n"
            "• Retirer votre consentement (pour le marketing)\n"
            "• Vous opposer au traitement / demander la portabilité des données\n"
            "• Déposer une plainte auprès du PDPC\n\n"
            "<b>Responsable du traitement :</b> {company}\n"
            "Contact : {email}\n\n"
            "En continuant à utiliser ce bot, vous reconnaissez et acceptez cette politique."
        ),
        "privacy.btn_full_policy": "📄 Lire la politique complète",
        "privacy.btn_accept": "✅ Accepter et continuer",
        "privacy.accepted": "✅ Vous avez accepté la politique de confidentialité.",
        "privacy.already_accepted": "✅ Vous avez déjà accepté la politique de confidentialité.",
        "privacy.no_url": "La page de politique de confidentialité complète n'est pas encore configurée.",
    },

}
