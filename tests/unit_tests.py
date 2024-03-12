import unittest
from unittest.mock import patch, MagicMock
from telegram import Update, Chat, Message, User, InlineKeyboardMarkup, Bot, CallbackQuery
from telegram.ext import CallbackContext

# Импорт команды StartCommand из вашего файла с командами
from commands import StartCommand, MenuCommand, DetailsCommand, ButtonHandler

class TestStartCommand(unittest.TestCase):
    def setUp(self):
        # Создаем мок объектов, необходимых для тестирования
        self.bot = MagicMock()
        self.update = MagicMock(spec=Update)
        self.context = MagicMock(spec=CallbackContext)

        # Настраиваем мок Update, чтобы имитировать сообщение от пользователя
        self.update.effective_chat = Chat(id=123, type='private')
        self.update.message = Message(message_id=1, date=None, chat=self.update.effective_chat,
                                      from_user=User(id=456, first_name='Test User', is_bot=False),
                                      text='/start', bot=self.bot)

    @patch('commands.Update')
    def test_start_command_sends_correct_message(self, mock_update):
        StartCommand.execute(self, self.update, self.context)
        self.bot.send_message.assert_called_once()  # Проверяем, что метод был вызван

        # Теперь проверяем ключевые аргументы вызова
        called_args, called_kwargs = self.bot.send_message.call_args
        self.assertEqual(called_kwargs['chat_id'], 123)
        self.assertIn('Вітаю у <b>ADP Pizza</b>', called_kwargs['text'])
        self.assertEqual(called_kwargs['parse_mode'], 'HTML')


class TestMenuCommand(unittest.TestCase):
    def setUp(self):
        self.bot = MagicMock(spec=Bot)
        self.chat_id = 12345
        self.user = User(id=456, first_name='Test User', is_bot=False)

        # Настраиваем мок сообщения и чата
        self.message = Message(message_id=123, date=None, chat=Chat(id=self.chat_id, type='private'),
                               from_user=self.user, text='/menu', bot=self.bot)
        self.update = MagicMock(spec=Update, message=self.message)

        # Создаем мок CallbackContext
        self.context = MagicMock(spec=CallbackContext, bot=self.bot)

    @patch('commands.DBManager.get_connection')
    def test_menu_command_sends_buttons(self, mock_get_connection):
        # Подготавливаем мокированный ответ от базы данных
        mock_cursor = MagicMock()
        mock_connection = mock_get_connection.return_value
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [('Margherita',), ('Pepperoni',)]

        menu_command = MenuCommand()
        menu_command.execute(self.update, self.context)

        # Проверяем, что send_message был вызван с ожидаемыми параметрами
        self.bot.send_message.assert_called_once()
        args, kwargs = self.bot.send_message.call_args

        # Проверяем, что в kwargs содержится reply_markup с InlineKeyboardMarkup
        self.assertIsInstance(kwargs['reply_markup'], InlineKeyboardMarkup)

        # Дополнительно проверяем количество кнопок
        buttons = kwargs['reply_markup'].inline_keyboard
        self.assertEqual(len(buttons), 3)  # 2 пиццы + 1 кнопка "Show All"


class TestDetailsCommand(unittest.TestCase):
    def setUp(self):
        self.bot = MagicMock(spec=Bot)
        self.update = MagicMock(spec=Update)
        self.context = MagicMock(spec=CallbackContext)
        self.context.args = ['Margherita']

        # Настройка update для имитации сообщения от пользователя
        self.chat_id = 12345
        self.update.effective_chat = Chat(self.chat_id, 'private')
        self.update.message = Message(message_id=1, date=None, chat=self.update.effective_chat,
                                      from_user=User(1, 'test', False), text='/details Margherita', bot=self.bot)

        # Настройка context.bot для имитации ответа бота
        self.context.bot = self.bot

    @patch('commands.DBManager.get_connection')
    def test_details_command(self, mock_get_connection):
        # Настройка мокированного ответа от базы данных
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        # Здесь настраиваем возвращаемое значение для fetchone()
        # Обратите внимание, что значения должны быть конкретными значениями, а не MagicMock объектами
        mock_cursor.fetchone.return_value = (
        'Margherita', 'Delicious tomato and cheese', 'http://example.com/photo.jpg', 10)

        details_command = DetailsCommand()
        details_command.execute(self.update, self.context)

        # Проверка, что send_photo был вызван с ожидаемыми параметрами
        self.bot.send_photo.assert_called_once_with(
            chat_id=self.chat_id,
            photo='http://example.com/photo.jpg',
            caption='🍕 <b>Margherita</b>\n\n💡 <b>Склад:</b> <i>Delicious tomato and cheese</i>\n\n💵 <b>Ціна:</b> 10 грн',
            parse_mode='HTML'
        )


if __name__ == '__main__':
    unittest.main()
