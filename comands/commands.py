from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from db_manager import MenuRepository
from command_base import CommandBase
import logging

class MenuCommand(CommandBase):
    def __init__(self, menu_repository: MenuRepository):
        self.menu_repository = menu_repository

    def execute(self, update: Update, context: CallbackContext):
        try:
            context.user_data['processing_order'] = False

            rows = self.menu_repository.get_menu()

            keyboard = [[InlineKeyboardButton(row[0], callback_data=row[0])] for row in rows]
            keyboard.append([InlineKeyboardButton("Показати всі товари", callback_data="all_details")])
            reply_markup = InlineKeyboardMarkup(keyboard)

            context.bot.send_message(chat_id=update.effective_chat.id, text='📋 Меню <b>ADP Pizza</b>',
                                     parse_mode='HTML', reply_markup=reply_markup)
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Menu Command execute error: {e}", exc_info=True)


class DetailsCommand(CommandBase):
    def __init__(self, menu_repository: MenuRepository):
        self.menu_repository = menu_repository

    def execute(self, update: Update, context: CallbackContext):
        try:
            context.user_data['processing_order'] = False

            pizza_name = ' '.join(context.args)
            row = self.menu_repository.get_pizza_details(pizza_name)

            if row:
                message = f"🍕 <b>{row[0]}</b>\n\n💡 <b>Склад:</b> <i>{row[1]}</i>\n\n💵 <b>Ціна:</b> {row[3]} грн"
                cart_button = [[InlineKeyboardButton("➕ Додати до замовлення", callback_data=f"add_to_cart_{row[4]}")]]
                reply_markup = InlineKeyboardMarkup(cart_button)

                if row[2]:
                    context.bot.send_photo(chat_id=update.effective_chat.id, photo=row[2], caption=message,
                                           parse_mode='HTML', reply_markup=reply_markup)
                else:
                    context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML',
                                             reply_markup=reply_markup)
            else:
                context.bot.send_message(chat_id=update.effective_chat.id, text="Товар не знайдено 😶‍🌫️")
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Details Command execute error: {e}", exc_info=True)


class AllDetailsCommand(CommandBase):
    def __init__(self, menu_repository: MenuRepository):
        self.menu_repository = menu_repository

    def execute(self, update: Update, context: CallbackContext):
        try:
            context.user_data['processing_order'] = False

            rows = self.menu_repository.get_menu()
            for row in rows:
                pizza_name = row[0]
                context.args = [pizza_name]
                DetailsCommand(self.menu_repository).execute(update, context)
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"All-Details Command execute error: {e}", exc_info=True)




class ButtonHandler(CommandBase):
    def set_factory(self, factory):
        self.command_factory = factory

    def execute(self, update: Update, context: CallbackContext):
        try:
            query = update.callback_query
            query.answer()
            callback_data = query.data

            if callback_data.startswith("add_to_cart_"):
                product_id = callback_data.split("_", 3)[-1]
                add_to_cart_command = self.command_factory.get_command("add_to_cart")
                add_to_cart_command.execute(product_id,update, context)
            else:
                try:
                    command = self.command_factory.get_command(callback_data)
                    command.execute(update, context)
                except:
                    context.args = [callback_data]
                    command = self.command_factory.get_command("details")
                    command.execute(update, context)
        except Exception as e:
            logger = logging.getLogger('adp-client-bot-logger')
            logger.error(f"Button Handler execute error: {e}", exc_info=True)