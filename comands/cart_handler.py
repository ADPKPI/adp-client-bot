from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from db_manager import MenuRepository, CartRepository
from prettytable import PrettyTable
from command_base import CommandBase
import logging


class AddToCartCommand(CommandBase):
    def __init__(self, menu_repository: MenuRepository, cart_repository: CartRepository):
        self.menu_repository = menu_repository
        self.cart_repository = cart_repository

    def execute(self, product_id, update: Update, context: CallbackContext):
        try:
            context.user_data['processing_order'] = False

            user_id = update.effective_user.id
            menu_row = self.menu_repository.get_pizza_details_by_id(product_id)

            if menu_row:
                self.cart_repository.add_to_cart(user_id, product_id)

                cart_button = [[InlineKeyboardButton("🧺 Перейти до кошику", callback_data="open_cart")]]
                reply_markup = InlineKeyboardMarkup(cart_button)
                context.bot.send_message(chat_id=update.effective_chat.id, text="Товар додано в кошик 🧺",
                                         reply_markup=reply_markup)
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text="Товар не знайдено 😶‍🌫")
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Add To Cart Command execute error: {e}", exc_info=True)


class OpenCartCommand(CommandBase):
    def __init__(self, cart_repository: CartRepository):
        self.cart_repository = cart_repository

    def execute(self, update: Update, context: CallbackContext):
        try:
            context.user_data['processing_order'] = False

            user_id = update.effective_user.id
            rows = self.cart_repository.get_cart(user_id)

            output = PrettyTable()
            output.field_names = ["Назва", "N", "Сума"]

            order_button = InlineKeyboardButton("📄 Перейти до замовлення", callback_data="start_order")
            clean_button = InlineKeyboardButton("❌ Очистити кошик", callback_data="clean_cart")
            menu_button = InlineKeyboardButton("📋 Переглянути меню", callback_data="menu")
            keyboard = [[order_button], [clean_button], [menu_button]]

            if rows:
                output.add_rows(rows)
                total = sum(row[2] for row in rows)
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=f"<code>{output}</code>\n\n💵 <b>До сплати:</b> {total} грн",
                                         parse_mode='HTML',
                                         reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text='Наразі кошик пустий 😔',
                                         reply_markup=InlineKeyboardMarkup([[menu_button]]))
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Open Cart Command execute error: {e}", exc_info=True)


class CleanCartCommand(CommandBase):
    def __init__(self, cart_repository: CartRepository):
        self.cart_repository = cart_repository

    def execute(self, update: Update, context: CallbackContext):
        try:
            context.user_data['processing_order'] = False

            user_id = update.effective_user.id
            self.cart_repository.clear_cart(user_id)

            menu_button = InlineKeyboardButton("📋 Переглянути меню", callback_data="menu")
            context.bot.send_message(chat_id=update.effective_chat.id, text="Наразі кошик пустий 😔",
                                     reply_markup=InlineKeyboardMarkup([[menu_button]]))
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Clean Cart Command execute error: {e}", exc_info=True)
