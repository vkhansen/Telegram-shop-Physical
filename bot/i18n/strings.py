DEFAULT_LOCALE = "th"

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

        # === Orders ===
        "order.payment_method.choose": "💳 Выберите способ оплаты:",
        "order.payment_method.bitcoin": "💳 Bitcoin",
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
        "admin.order.verify_payment": "✅ Подтвердить оплату",
        "admin.order.payment_verified": "✅ Оплата подтверждена",

        # Delivery Chat (Card 13)
        "order.delivery.chat_unavailable": "❌ Чат с водителем недоступен. Группа курьеров не настроена.",
        "order.delivery.chat_started": "💬 Вы можете отправить сообщение водителю. Отправьте текст, фото или локацию.",
        "order.delivery.live_location_shared": "📍 Водитель поделился живой локацией! Вы можете отслеживать доставку.",

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
        "cart.total_format": "<b>Итого: {total} {currency}</b>",
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
        "admin.order.verify_payment": "✅ Verify Payment",
        "admin.order.payment_verified": "✅ Payment Verified",

        # Delivery Chat (Card 13)
        "order.delivery.chat_unavailable": "❌ Chat with driver unavailable. Rider group not configured.",
        "order.delivery.chat_started": "💬 You can message your driver. Send text, photo, or location.",
        "order.delivery.live_location_shared": "📍 Driver is sharing live location! You can track your delivery.",

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
        "cart.total_format": "<b>Total: {total} {currency}</b>",
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
        "admin.order.verify_payment": "✅ ยืนยันการชำระเงิน",
        "admin.order.payment_verified": "✅ ยืนยันการชำระเงินแล้ว",

        # Delivery Chat (Card 13)
        "order.delivery.chat_unavailable": "❌ แชทกับคนขับไม่พร้อมใช้งาน กลุ่มไรเดอร์ยังไม่ได้ตั้งค่า",
        "order.delivery.chat_started": "💬 คุณสามารถส่งข้อความถึงคนขับได้ ส่งข้อความ รูปภาพ หรือตำแหน่ง",
        "order.delivery.live_location_shared": "📍 คนขับแชร์ตำแหน่งสด! คุณสามารถติดตามการจัดส่งได้",

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
        "cart.total_format": "<b>รวม: {total} {currency}</b>",
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
    },
}
