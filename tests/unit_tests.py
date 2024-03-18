import unittest
from unittest.mock import patch, MagicMock
from telegram import Chat, Message, User, CallbackQuery
from comands.commands import MenuCommand, DetailsCommand, AllDetailsCommand, ButtonHandler
from command_factory import CommandFactory
from comands.cart_handler import *
from comands.order_handler import *

class MockMenuRepository:
    def get_menu(self):
        return [('Маргарита',), ('Пепероні',)]

    def get_pizza_details(self, pizza_name):
        if pizza_name == "Маргарита":
            return ("Маргарита", "Томатний соус, моцарелла", "url_to_photo", 100, 1)
        return None

    def get_pizza_details_by_id(self, product_id):
        if product_id == "1":
            return ("Томатний соус, моцарелла", "url_to_photo", 100, 1)
        return None

class MockCartRepository:
    def __init__(self):
        self.clear_cart = MagicMock()


    def add_to_cart(self, user_id, product_id):
        pass
    def get_cart(self, user_id):
        if user_id == "user_with_items":
            return [("Маргарита", 2, 200), ("Пепероні", 1, 150)]
        else:
            return []
    def clear_cart(self, user_id):
        pass

class TestStartCommand(unittest.TestCase):
    def setUp(self):
        self.update = MagicMock(spec=Update)
        self.update.effective_chat.id = 123456  # Пример ID чата
        self.update.effective_user = User(1, 'test', False)  # Пример пользователя
        self.update.message = Message(1, self.update.effective_user, None, Chat(1, 'private'))

        self.context = MagicMock(spec=CallbackContext)
        self.context.bot.send_message = MagicMock()
        self.context.user_data = {}

    def test_execute(self):
        command = StartCommand()

        command.execute(self.update, self.context)

        self.context.bot.send_message.assert_called_once()
        args, kwargs = self.context.bot.send_message.call_args
        self.assertEqual(kwargs['chat_id'], self.update.effective_chat.id)
        self.assertIn('Вітаю у <b>ADP Pizza</b>!', kwargs['text'])
        self.assertEqual(kwargs['parse_mode'], 'HTML')
        self.assertTrue('reply_markup' in kwargs)

        self.assertFalse(self.context.user_data['processing_order'])

class TestMenuCommand(unittest.TestCase):
    def setUp(self):
        self.update = MagicMock(spec=Update)
        self.update.effective_chat.id = 123456  # Пример ID чата
        self.update.effective_user = User(1, 'test_user', False)  # Пример пользователя
        self.update.message = Message(1, self.update.effective_user, None, Chat(1, 'private'))

        self.context = MagicMock(spec=CallbackContext)
        self.context.bot.send_message = MagicMock()
        self.context.user_data = {}

        self.mock_menu_repository = MockMenuRepository()

    def test_execute(self):
        command = MenuCommand(self.mock_menu_repository)

        command.execute(self.update, self.context)

        self.context.bot.send_message.assert_called_once()
        args, kwargs = self.context.bot.send_message.call_args
        self.assertEqual(kwargs['chat_id'], self.update.effective_chat.id)
        self.assertIn('📋 Меню <b>ADP Pizza</b>', kwargs['text'])
        self.assertEqual(kwargs['parse_mode'], 'HTML')
        self.assertIsInstance(kwargs['reply_markup'], InlineKeyboardMarkup)

        expected_buttons = ['Маргарита', 'Пепероні', 'Показати всі товари']
        sent_buttons = [button[0].text for button in kwargs['reply_markup'].inline_keyboard[:-1]] + [kwargs['reply_markup'].inline_keyboard[-1][0].text]
        self.assertListEqual(expected_buttons, sent_buttons)


class TestDetailsCommand(unittest.TestCase):
    def setUp(self):
        self.update = MagicMock(spec=Update)
        self.update.effective_chat.id = 123456
        self.update.effective_user = User(1, 'test_user', False)
        self.update.message = Message(1, None, None, Chat(1, 'private'))

        self.context = MagicMock(spec=CallbackContext)
        self.context.bot.send_message = MagicMock()
        self.context.bot.send_photo = MagicMock()
        self.context.args = ["Маргарита"]

        self.menu_repository = MockMenuRepository()

    @patch('commands.MenuRepository', new=MockMenuRepository)
    def test_execute_with_details(self):
        command = DetailsCommand(self.menu_repository)
        command.execute(self.update, self.context)

        self.context.bot.send_photo.assert_called_once()
        args, kwargs = self.context.bot.send_photo.call_args
        self.assertIn("Маргарита", kwargs['caption'])

    @patch('commands.MenuRepository', new=MockMenuRepository)
    def test_execute_without_details(self):
        self.context.args = ["Неизвестная"]
        command = DetailsCommand(self.menu_repository)
        command.execute(self.update, self.context)

        self.context.bot.send_message.assert_called_once_with(chat_id=123456, text="Товар не знайдено 😶‍🌫️")


class TestAllDetailsCommand(unittest.TestCase):
    def setUp(self):
        self.update = MagicMock(spec=Update)
        self.update.effective_chat.id = 123456
        self.update.effective_user = User(1, 'test_user', False)
        self.update.message = Message(1, None, None, Chat(1, 'private'))

        self.context = MagicMock(spec=CallbackContext)
        self.context.bot.send_message = MagicMock()
        self.context.args = []

        self.menu_repository = MockMenuRepository()

    @patch('commands.DetailsCommand')
    def test_execute(self, mock_details_command):
        mock_details_command_instance = mock_details_command.return_value
        mock_details_command_instance.execute = MagicMock()

        command = AllDetailsCommand(self.menu_repository)
        command.execute(self.update, self.context)

        self.assertEqual(len(self.menu_repository.get_menu()), 2)
        self.assertEqual(mock_details_command_instance.execute.call_count, 2)


class TestButtonHandler(unittest.TestCase):
    def setUp(self):
        self.update = MagicMock(spec=Update)
        self.callback_query = MagicMock(spec=CallbackQuery)
        self.callback_query.data = "add_to_cart_1"
        self.update.callback_query = self.callback_query
        self.callback_query.message.chat_id = 123456
        self.callback_query.from_user = User(1, 'test_user', False)

        self.factory = CommandFactory(None, None, None, None)
        self.factory.get_command = MagicMock()

        self.mock_command = MagicMock()
        self.factory.get_command.return_value = self.mock_command

        self.context = MagicMock()

    @patch('command_factory.CommandFactory')
    def test_execute_add_to_cart(self, mock_factory):
        handler = ButtonHandler()
        handler.set_factory(self.factory)

        handler.execute(self.update, self.context)

        self.factory.get_command.assert_called_once_with("add_to_cart")
        self.mock_command.execute.assert_called_once()


class TestAddToCartCommand(unittest.TestCase):
    def setUp(self):
        self.update = MagicMock(spec=Update)
        self.update.effective_chat.id = 123456
        self.update.effective_user = User(1, 'test_user', False)
        self.update.message = Message(1, None, None, Chat(1, 'private'))

        self.context = MagicMock(spec=CallbackContext)
        self.context.bot.send_message = MagicMock()

        self.menu_repository = MockMenuRepository()
        self.cart_repository = MockCartRepository()

    def test_execute_product_found(self):
        command = AddToCartCommand(self.menu_repository, self.cart_repository)
        command.execute("1", self.update, self.context)

        self.assertEqual(self.context.bot.send_message.call_args[1]['chat_id'], 123456)
        self.assertEqual(self.context.bot.send_message.call_args[1]['text'], "Товар додано в кошик 🧺")
        self.assertIsInstance(self.context.bot.send_message.call_args[1]['reply_markup'], InlineKeyboardMarkup)

    def test_execute_product_not_found(self):
        command = AddToCartCommand(self.menu_repository, self.cart_repository)
        command.execute("unknown_id", self.update, self.context)

        self.context.bot.send_message.assert_called_once_with(chat_id=123456, text="Товар не знайдено 😶‍🌫")


class TestOpenCartCommand(unittest.TestCase):
    def setUp(self):
        self.update = MagicMock(spec=Update)
        self.update.effective_chat.id = 123456
        self.update.effective_user = User(1, 'test_user', False)
        self.update.message = Message(1, None, None, Chat(1, 'private'))

        self.context = MagicMock(spec=CallbackContext)
        self.context.bot.send_message = MagicMock()

        self.cart_repository = MockCartRepository()

    def test_execute_with_items(self):
        command = OpenCartCommand(self.cart_repository)
        self.update.effective_user.id = "user_with_items"
        command.execute(self.update, self.context)

        self.context.bot.send_message.assert_called_once()
        args, kwargs = self.context.bot.send_message.call_args
        self.assertTrue("<code>" in kwargs['text'] and "Маргарита" in kwargs['text'])

    def test_execute_empty_cart(self):
        command = OpenCartCommand(self.cart_repository)
        self.update.effective_user.id = "user_with_empty_cart"
        command.execute(self.update, self.context)

        called_args, called_kwargs = self.context.bot.send_message.call_args

        self.assertEqual(called_kwargs['chat_id'], 123456)
        self.assertEqual(called_kwargs['text'], 'Наразі кошик пустий 😔')

        self.assertIsInstance(called_kwargs['reply_markup'], InlineKeyboardMarkup)


class TestCleanCartCommand(unittest.TestCase):
    def setUp(self):
        self.update = MagicMock(spec=Update)
        self.update.effective_chat.id = 123456
        self.update.effective_user = User(1, 'test_user', False)
        self.update.message = Message(1, None, None, Chat(1, 'private'))

        self.context = MagicMock(spec=CallbackContext)
        self.context.bot.send_message = MagicMock()

        self.cart_repository = MockCartRepository()

    def test_execute_empty_cart(self):
        command = CleanCartCommand(self.cart_repository)
        self.update.effective_user.id = "user_with_empty_cart"
        command.execute(self.update, self.context)

        called_args, called_kwargs = self.context.bot.send_message.call_args

        self.assertEqual(called_kwargs['chat_id'], 123456)
        self.assertEqual(called_kwargs['text'], 'Наразі кошик пустий 😔')

        self.assertIsInstance(called_kwargs['reply_markup'], InlineKeyboardMarkup)


class TestStartOrderCommand(unittest.TestCase):
    def setUp(self):
        self.update = MagicMock(spec=Update)
        self.update.effective_chat.id = 123456
        self.update.effective_user = User(1, 'test_user', False)

        self.context = MagicMock(spec=CallbackContext)
        self.context.user_data = {}

        self.user_repository = MagicMock()
        self.order_repository = MagicMock()
        self.cart_repository = MagicMock()

        self.factory = CommandFactory(None, None, None, None)
        self.factory.get_command = MagicMock()

    @patch('start_command.StartCommand')
    def test_execute_user_exists(self, mock_start_command):
        self.user_repository.get_user.return_value = True

        command = StartOrderCommand(self.user_repository, self.order_repository, self.cart_repository)
        command.set_factory(self.factory)

        command.execute(self.update, self.context)

        self.factory.get_command.assert_called_once_with("request_order_confirmation")

    @patch('order_handler.RequestPhoneNumberCommand')
    def test_execute_user_does_not_exist(self, mock_request_phone_number_command):
        self.user_repository.get_user.return_value = None

        command = StartOrderCommand(self.user_repository, self.order_repository, self.cart_repository)
        command.set_factory(self.factory)

        command.execute(self.update, self.context)

        self.user_repository.add_user.assert_called_once()
        self.factory.get_command.assert_called_once_with("request_phone_number")


if __name__ == '__main__':
    unittest.main()