from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove
from telegram.ext import CallbackContext
from db_manager import DBManager, MenuRepository, CartRepository, UserRepository, OrderRepository
from prettytable import PrettyTable
from functools import partial





class CommandBase:
    def execute(self, update: Update, context: CallbackContext):
        raise NotImplementedError

class StartCommand(CommandBase):
    def execute(self, update: Update, context: CallbackContext):
        context.user_data['processing_order'] = False

        menu_button = InlineKeyboardButton("📋 Переглянути меню", callback_data="MENU")
        cart_button = InlineKeyboardButton("🧺 Перейти до кошику", callback_data="OPEN_CART")

        context.bot.send_message(chat_id=update.effective_chat.id,text= 'Вітаю у <b>ADP Pizza</b>! 🍕 Це ваш особистий помічник, завдяки якому ви зможете ознайомитися з нашим меню, '
            'замовити піцу та отримати інформацію про акції.\n\nСподіваємось, ви знайдете улюблені смаки та насолоджуватиметесь кожним шматочком! Cмачного! 🍕', parse_mode='HTML',
                                 reply_markup=InlineKeyboardMarkup([[menu_button], [cart_button]]))


class MenuCommand(CommandBase):
    def __init__(self, menu_repository: MenuRepository):
        self.menu_repository = menu_repository

    def execute(self, update: Update, context: CallbackContext):
        context.user_data['processing_order'] = False

        rows = self.menu_repository.get_menu()

        keyboard = [[InlineKeyboardButton(row[0], callback_data=row[0])] for row in rows]
        keyboard.append([InlineKeyboardButton("Показати всі товари", callback_data="SHOW_ALL")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(chat_id=update.effective_chat.id, text='📋 Меню <b>ADP Pizza</b>', parse_mode='HTML', reply_markup=reply_markup)



class DetailsCommand(CommandBase):
    def __init__(self, menu_repository: MenuRepository):
        self.menu_repository = menu_repository

    def execute(self, update: Update, context: CallbackContext):
        context.user_data['processing_order'] = False

        pizza_name = ' '.join(context.args)
        row = self.menu_repository.get_pizza_details(pizza_name)

        if row:
            message = f"🍕 <b>{row[0]}</b>\n\n💡 <b>Склад:</b> <i>{row[1]}</i>\n\n💵 <b>Ціна:</b> {row[3]} грн"
            cart_button = [[InlineKeyboardButton("➕ Додати до замовлення", callback_data=f"ADD_TO_CART_{row[4]}")]]
            reply_markup = InlineKeyboardMarkup(cart_button)

            if row[2]:
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=row[2], caption=message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML', reply_markup=reply_markup)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Товар не знайдено 😶‍🌫️")

    def show_all_details(self, update: Update, context: CallbackContext):
        context.user_data['processing_order'] = False

        rows = self.menu_repository.get_menu()
        for row in rows:
            pizza_name = row[0]
            context.args = [pizza_name]
            DetailsCommand(self.menu_repository).execute(update, context)



class CartHandler(CommandBase):
    def __init__(self, menu_repository: MenuRepository, cart_repository: CartRepository):
        self.menu_repository = menu_repository
        self.cart_repository = cart_repository

    def add_to_cart(self, user_id, product_id, update: Update, context: CallbackContext):
        context.user_data['processing_order'] = False

        menu_row = self.menu_repository.get_pizza_details_by_id(product_id)

        if menu_row:
            self.cart_repository.add_to_cart(user_id, product_id)

            cart_button = [[InlineKeyboardButton("🧺 Перейти до кошику", callback_data="OPEN_CART")]]
            reply_markup = InlineKeyboardMarkup(cart_button)
            context.bot.send_message(chat_id=update.effective_chat.id, text="Товар додано в кошик 🧺",
                                     reply_markup=reply_markup)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Товар не знайдено 😶‍🌫")


    def open_cart(self, user_id, update: Update, context: CallbackContext):
        context.user_data['processing_order'] = False

        rows = self.cart_repository.get_cart(user_id)

        output = PrettyTable()
        output.field_names = ["Назва", "N", "Сума"]

        order_button = InlineKeyboardButton("📄 Перейти до замовлення", callback_data="START_ORDER")
        clean_button = InlineKeyboardButton("❌ Очистити кошик", callback_data="CLEAN")
        menu_button = InlineKeyboardButton("📋 Переглянути меню", callback_data="MENU")
        keyboard = [[order_button], [clean_button], [menu_button]]

        if rows:
            output.add_rows(rows)
            total = sum(row[2] for row in rows)
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"<code>{output}</code>\n\n💵 <b>До сплати:</b> {total} грн", parse_mode='HTML',
                                     reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='Наразі кошик пустий 😔',
                                     reply_markup=InlineKeyboardMarkup([[menu_button]]))

    def clean_cart(self, user_id, update: Update, context: CallbackContext):
        context.user_data['processing_order'] = False

        self.cart_repository.clear_cart(user_id)

        menu_button = InlineKeyboardButton("📋 Переглянути меню", callback_data="MENU")
        context.bot.send_message(chat_id=update.effective_chat.id, text="Наразі кошик пустий 😔",
                                 reply_markup=InlineKeyboardMarkup([[menu_button]]))
class OrderHandler(CommandBase):
    def __init__(self, user_repository: UserRepository, order_repository: OrderRepository, cart_repository: CartRepository):
        self.user_repository = user_repository
        self.order_repository = order_repository
        self.cart_repository = cart_repository

    def start_order(self, user_id, update: Update, context: CallbackContext):
        context.user_data['processing_order'] = True

        user = self.user_repository.get_user(user_id)
        if user:
            self.request_order_confirmation(user_id, update, context)
        else:
            username = update.effective_user.username
            firstname = update.effective_user.first_name
            lastname = update.effective_user.last_name
            self.user_repository.add_user(user_id, username, firstname, lastname)
            self.request_phone_number(update, context)

    def confirm_order(self, update: Update, context: CallbackContext):
        if context.user_data['processing_order']:
            context.user_data['processing_order'] = False

            user_id = update.effective_user.id
            cart_items = self.cart_repository.get_cart(user_id)
            order_list = [(item[0], item[1], item[2]) for item in cart_items]
            total_price = sum(item[2] for item in cart_items)

            user_info = self.user_repository.get_user(user_id)
            phone_number = user_info[4]
            location = user_info[5]

            order_id = self.order_repository.create_order(user_id, phone_number, order_list, total_price, location)
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Ваше замовлення #{order_id} оформлено. Очікуйте на дзвінок кур'єра ❣️")
        else:
            StartCommand().execute(update, context)


    def request_phone_number(self, update: Update, context: CallbackContext):
        contact_keyboard = KeyboardButton('📱 Поділитися номером телефону', request_contact=True)
        contact_markup = ReplyKeyboardMarkup([[contact_keyboard]], one_time_keyboard=True)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Будь ласка, надайте номер телефону 📱',
                                 reply_markup=contact_markup)

    def request_location(self, update: Update, context: CallbackContext):
        context.bot.send_message(chat_id=update.effective_chat.id, text='Будь ласка, вкажіть адресу доставки 🗺️')

    def request_order_confirmation(self, user_id, update: Update, context: CallbackContext):
        if context.user_data['processing_order']:
            cart_items = self.cart_repository.get_cart(user_id)
            total = sum(item[2] for item in cart_items)

            output = PrettyTable()
            output.field_names = ["Назва", "N", "Сума"]
            output.add_rows(cart_items)

            user_data = self.user_repository.get_user(user_id)
            location = user_data[5].split("|") if user_data and user_data[5] else (0, 0)
            latitude, longitude = map(float, location)

            order_button = InlineKeyboardButton("✅ Підтвердити замолвення", callback_data="CONFIRMED_ORDER")
            clean_button = InlineKeyboardButton("❌ Відхилити замовлення", callback_data="CANCELED_ORDER")
            menu_button = InlineKeyboardButton("🗺️ Змінити адресу", callback_data="CHANGE_LOCATION")
            keyboard = InlineKeyboardMarkup([[order_button], [clean_button], [menu_button]])

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f'📄 Ваше замолення:\n<code>{output}</code>\n\n💵 <b>До сплати:</b> {total}\n\n📱 Номер телефону: {user_data[4]}\n🗺️ Адреса доставки:',
                                     parse_mode='HTML')
            context.bot.send_location(chat_id=update.effective_chat.id, latitude=latitude, longitude=longitude,
                                      reply_markup=keyboard)
        else:
            StartCommand().execute(update, context)

    def get_phone_number(self, update: Update, context: CallbackContext):
        if context.user_data['processing_order']:
            user_id = update.effective_user.id
            phone_number = update.message.contact.phone_number
            self.user_repository.update_user_contact(user_id, phone_number=phone_number)
            context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Номер збережено", reply_markup=ReplyKeyboardRemove())

            user_data = self.user_repository.get_user(user_id)
            if user_data[5] is None:
                self.request_location(update, context)
        else:
            StartCommand().execute(update, context)

    def get_location(self, update: Update, context: CallbackContext):
        if context.user_data['processing_order']:
            user_id = update.effective_user.id
            location = f"{update.message.location.latitude}|{update.message.location.longitude}"
            self.user_repository.update_user_contact(user_id, location=location)
            context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Адресу збережено")
            self.request_order_confirmation(user_id, update, context)
        else:
            StartCommand().execute(update, context)

    def cancel_order(self, update: Update, context: CallbackContext):
        if context.user_data['processing_order']:
            context.user_data['processing_order'] = False
            menu_button = InlineKeyboardButton("📋 Переглянути меню", callback_data="MENU")
            cart_button = InlineKeyboardButton("🧺 Перейти до кошику", callback_data="OPEN_CART")
            context.bot.send_message(chat_id=update.effective_chat.id, text="Замовлення відхилено ❌",
                                     reply_markup=InlineKeyboardMarkup([[menu_button], [cart_button]]))
        else:
            StartCommand().execute(update, context)




class ButtonHandler(CommandBase):
    def __init__(self, menu_repository: MenuRepository, cart_repository: CartRepository, order_handler, cart_handler):
        self.menu_repository = menu_repository
        self.cart_repository = cart_repository
        self.order_handler = order_handler
        self.cart_handler = cart_handler

    def execute(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        callback_data = query.data
        user_id = update.effective_user.id

        command_map = {
            "SHOW_ALL": partial(DetailsCommand(self.menu_repository).show_all_details, update, context),
            "OPEN_CART": partial(self.cart_handler.open_cart, user_id, update, context),
            "CLEAN": partial(self.cart_handler.clean_cart, user_id, update, context),
            "MENU": partial(MenuCommand(self.menu_repository).execute, update, context),
            "START_ORDER": partial(self.order_handler.start_order, user_id, update, context),
            "CANCELED_ORDER": partial(self.order_handler.cancel_order, update, context),
            "CHANGE_LOCATION": partial(self.order_handler.request_location, update, context),
            "CONFIRMED_ORDER": partial(self.order_handler.confirm_order, update, context)
        }

        if callback_data.startswith("ADD_TO_CART_"):
            product_id = callback_data.split("_", 3)[-1]
            self.cart_handler.add_to_cart(user_id, product_id, update, context)
        else:
            command_key = callback_data
            command = command_map.get(command_key)
            if command:
                command()
            elif callback_data not in command_map:
                pizza_name = callback_data
                context.args = [pizza_name]
                DetailsCommand(self.menu_repository).execute(update, context)








