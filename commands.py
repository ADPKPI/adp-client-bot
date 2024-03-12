from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from db_manager import DBManager

class CommandBase:
    def execute(self, update: Update, context: CallbackContext):
        raise NotImplementedError

class StartCommand(CommandBase):
    def execute(self, update: Update, context: CallbackContext):
        update.message.reply_text(
            'Вітаю у <b>ADP Pizza</b>! 🍕 Це ваш особистий помічник, завдяки якому ви зможете ознайомитися з нашим меню, '
            'замовити піцу та отримати інформацію про акції.\n\n<b>Доступні команди:</b>\n<i>/menu</i> - перегляд меню наших піц\n\nСподіваємось, '
            'ви знайдете улюблені смаки та насолоджуватиметесь кожним шматочком! Cмачного! 🍕', parse_mode='HTML')


class MenuCommand(CommandBase):
    def execute(self, update: Update, context: CallbackContext):
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT name FROM menu")
        rows = cursor.fetchall()

        # Добавление кнопок для каждой пиццы
        keyboard = [[InlineKeyboardButton(row[0], callback_data=row[0])] for row in rows]

        # Добавление кнопки "Show All"
        keyboard.append([InlineKeyboardButton("Show All", callback_data="SHOW_ALL")])

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
            message = f"🍕 <b>{row[0]}</b>\n\n💡 <b>Склад:</b> <i>{row[1]}</i>\n\n💵 <b>Ціна:</b> {row[3]} грн"
            if row[2]:
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=row[2], caption=message, parse_mode='HTML')
            else:
                update.message.reply_text(message)
        else:
            update.message.reply_text("Pizza not found.")

        cursor.close()
        cnx.close()

class ButtonHandler(CommandBase):
    def execute(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()  # Подтверждение обработки callback
        callback_data = query.data

        if callback_data == "SHOW_ALL":
            self.show_all_details(update, context)
        else:
            pizza_name = callback_data
            context.args = [pizza_name]
            DetailsCommand().execute(update, context)

    def show_all_details(self, update: Update, context: CallbackContext):
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT name FROM menu")
        rows = cursor.fetchall()

        for row in rows:
            pizza_name = row[0]
            context.args = [pizza_name]
            DetailsCommand().execute(update, context)

        cursor.close()
        cnx.close()

