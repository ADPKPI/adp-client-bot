from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
import mysql.connector
from mysql.connector import pooling
import logging

# Настройка базового логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class DBManager:
    _instance = None

    def __new__(cls, dbconfig):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            cls.pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **dbconfig)
        return cls._instance

    @staticmethod
    def get_connection():
        return DBManager._instance.pool.get_connection()


class CommandBase:
    def execute(self, update: Update, context: CallbackContext):
        raise NotImplementedError


class StartCommand(CommandBase):
    def execute(self, update: Update, context: CallbackContext):
        update.message.reply_text(
            'Hi! Use /show to display pizza names. Use /details <pizza_name> to get details about a specific pizza.')


class ShowCommand(CommandBase):
    def execute(self, update: Update, context: CallbackContext):
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT name FROM menu")
        rows = cursor.fetchall()

        keyboard = [[InlineKeyboardButton(row[0], callback_data=row[0])] for row in rows]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Please choose:', reply_markup=reply_markup)

        cursor.close()
        cnx.close()


class DetailsCommand(CommandBase):
    def execute(self, update: Update, context: CallbackContext):
        pizza_name = ' '.join(context.args)
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT name, description, photo_url, price FROM menu WHERE name = %s", (pizza_name,))
        row = cursor.fetchone()

        if row:
            message = f"Details for {row[0]}: {row[1]}\nPrice: {row[3]}"
            if row[2]:
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=row[2], caption=message)
            else:
                update.message.reply_text(message)
        else:
            update.message.reply_text("Pizza not found.")

        cursor.close()
        cnx.close()

class ButtonHandler(CommandBase):
    def execute(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()  # Отправляем подтверждение обработки callback
        pizza_name = query.data
        # Мы передаём имя пиццы через context.args, чтобы использовать существующую логику DetailsCommand
        context.args = [pizza_name]
        DetailsCommand().execute(update, context)

class BotManager:
    def __init__(self, token, dbconfig):
        self.updater = Updater(token, use_context=True)
        DBManager(dbconfig)  # Initialize DB connection pool
        self._register_handlers()

    def _register_handlers(self):
        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", lambda u, c: StartCommand().execute(u, c)))
        dispatcher.add_handler(CommandHandler("show", lambda u, c: ShowCommand().execute(u, c)))
        dispatcher.add_handler(CommandHandler("details", lambda u, c: DetailsCommand().execute(u, c), pass_args=True))
        dispatcher.add_handler(CallbackQueryHandler(lambda u, c: ButtonHandler().execute(u, c)))
        # Add CallbackQueryHandler and other handlers as needed

    def run(self):
        self.updater.start_polling()
        self.updater.idle()


if __name__ == '__main__':
    token = "6723650184:AAFuUD9zeqtqdp0ihFcm6pOVdoAVoXQTmrU"
    dbconfig = {
        "host": "78.140.189.245",
        "user": "tg-client-user",
        "password": "LmkPJVndwb7Z",
        "database": "adp_pizza_db"
    }
    bot_manager = BotManager(token, dbconfig)
    bot_manager.run()
