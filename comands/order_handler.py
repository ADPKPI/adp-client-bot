from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove
from telegram.ext import CallbackContext
from db_manager import CartRepository, UserRepository, OrderRepository
from prettytable import PrettyTable
from start_command import StartCommand
from command_base import CommandBase
import logging

class StartOrderCommand(CommandBase):
    def __init__(self, user_repository: UserRepository, order_repository: OrderRepository, cart_repository: CartRepository):
        self.user_repository = user_repository

    def set_factory(self, factory):
        self.factory = factory

    def execute(self, update: Update, context: CallbackContext):
        try:
            context.user_data['processing_order'] = True

            user_id = update.effective_user.id
            user = self.user_repository.get_user(user_id)
            if user:
                self.factory.get_command("request_order_confirmation").execute(update, context)
            else:
                username = update.effective_user.username
                firstname = update.effective_user.first_name
                lastname = update.effective_user.last_name
                self.user_repository.add_user(user_id, username, firstname, lastname)
                self.factory.get_command("request_phone_number").execute(update, context)
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Start Order Command execute error: {e}", exc_info=True)


class ConfirmOrderCommand(CommandBase):
    def __init__(self, user_repository: UserRepository, order_repository: OrderRepository, cart_repository: CartRepository):
        self.user_repository = user_repository
        self.order_repository = order_repository
        self.cart_repository = cart_repository

    def execute(self, update: Update, context: CallbackContext):
        try:
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

                user_id = update.effective_user.id
                self.cart_repository.clear_cart(user_id)

                context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Ваше замовлення #{order_id} оформлено. Очікуйте на дзвінок кур'єра ❣️")
            else:
                StartCommand().execute(update, context)
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Confirm Order Command execute error: {e}", exc_info=True)


class CancelOrderCommand(CommandBase):
    def execute(self, update: Update, context: CallbackContext):
        try:
            if context.user_data['processing_order']:
                context.user_data['processing_order'] = False
                menu_button = InlineKeyboardButton("📋 Переглянути меню", callback_data="menu")
                cart_button = InlineKeyboardButton("🧺 Перейти до кошику", callback_data="open_cart")
                context.bot.send_message(chat_id=update.effective_chat.id, text="Замовлення відхилено ❌",
                                         reply_markup=InlineKeyboardMarkup([[menu_button], [cart_button]]))
            else:
                StartCommand().execute(update, context)
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Cancel Order Command execute error: {e}", exc_info=True)


class RequestOrderConfirmationCommand(CommandBase):
    def __init__(self, user_repository: UserRepository, cart_repository: CartRepository):
        self.user_repository = user_repository
        self.cart_repository = cart_repository

    def execute(self, update: Update, context: CallbackContext):
        try:
            if context.user_data['processing_order']:
                user_id = update.effective_user.id
                cart_items = self.cart_repository.get_cart(user_id)
                total = sum(item[2] for item in cart_items)

                output = PrettyTable()
                output.field_names = ["Назва", "N", "Сума"]
                output.add_rows(cart_items)

                user_data = self.user_repository.get_user(user_id)
                location = user_data[5].split("|") if user_data and user_data[5] else (0, 0)
                latitude, longitude = map(float, location)

                order_button = InlineKeyboardButton("✅ Підтвердити замовлення", callback_data="confirm_order")
                clean_button = InlineKeyboardButton("❌ Відхилити замовлення", callback_data="cancel_order")
                menu_button = InlineKeyboardButton("🗺️ Змінити адресу", callback_data="request_location")
                keyboard = InlineKeyboardMarkup([[order_button], [clean_button], [menu_button]])

                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=f'📄 Ваше замолення:\n<code>{output}</code>\n\n💵 <b>До сплати:</b> {total}\n\n📱 Номер телефону: {user_data[4]}\n🗺️ Адреса доставки:',
                                         parse_mode='HTML')
                context.bot.send_location(chat_id=update.effective_chat.id, latitude=latitude, longitude=longitude,
                                          reply_markup=keyboard)
            else:
                StartCommand().execute(update, context)
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Request Order Confirmation Command execute error: {e}", exc_info=True)


class RequestPhoneNumberCommand(CommandBase):
    def execute(self, update: Update, context: CallbackContext):
        try:
            contact_keyboard = KeyboardButton('📱 Поділитися номером телефону', request_contact=True)
            contact_markup = ReplyKeyboardMarkup([[contact_keyboard]], one_time_keyboard=True)
            context.bot.send_message(chat_id=update.effective_chat.id, text='Будь ласка, надайте номер телефону 📱',
                                     reply_markup=contact_markup)
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Request Phone Number Command execute error: {e}", exc_info=True)


class RequestLocationCommand(CommandBase):
    def execute(self, update: Update, context: CallbackContext):
        try:
            context.bot.send_message(chat_id=update.effective_chat.id, text='Будь ласка, вкажіть адресу доставки 🗺️\n\n<i>Telegram -> Attach -> Location<i>', parse_method='HTML')
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Request Location Command execute error: {e}", exc_info=True)

class GotPhoneNumberCommand(CommandBase):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def set_factory(self, factory):
        self.factory = factory

    def execute(self, update: Update, context: CallbackContext):
        try:
            if context.user_data['processing_order']:
                user_id = update.effective_user.id
                phone_number = update.message.contact.phone_number
                self.user_repository.update_user_contact(user_id, phone_number=phone_number)
                context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Номер збережено", reply_markup=ReplyKeyboardRemove())

                user_data = self.user_repository.get_user(user_id)
                if user_data[5] is None:
                    self.factory.get_command("request_location").execute(update, context)
            else:
                StartCommand().execute(update, context)
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Got Phone Number Command execute error: {e}", exc_info=True)


class GotLocationCommand(CommandBase):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def set_factory(self, factory):
        self.factory = factory

    def execute(self, update: Update, context: CallbackContext):
        try:
            if context.user_data['processing_order']:
                user_id = update.effective_user.id
                location = f"{update.message.location.latitude}|{update.message.location.longitude}"
                self.user_repository.update_user_contact(user_id, location=location)
                context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Адресу збережено")
                self.factory.get_command("request_order_confirmation").execute(update, context)
            else:
                StartCommand().execute(update, context)
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Got Location Command execute error: {e}", exc_info=True)