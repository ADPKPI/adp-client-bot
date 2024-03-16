from telegram.ext import Updater, CommandHandler, CallbackQueryHandler,MessageHandler, Filters
from commands import StartCommand, MenuCommand, DetailsCommand, ButtonHandler, OrderHandler, CartHandler
from db_manager import DBManager, MenuRepository, CartRepository, UserRepository, OrderRepository

class BotManager:
    def __init__(self, token, dbconfig):
        self.updater = Updater(token, use_context=True)
        DBManager(dbconfig)

        self.menu_repository = MenuRepository()
        self.cart_repository = CartRepository()
        self.user_repository = UserRepository()
        self.order_repository = OrderRepository()
        self.order_handler = OrderHandler(self.user_repository, self.order_repository, self.cart_repository)
        self.cart_handler = CartHandler(self.menu_repository, self.cart_repository)

        self._register_handlers()

    def _register_handlers(self):
        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", lambda u, c: StartCommand().execute(u, c)))
        dispatcher.add_handler(CommandHandler("details", lambda u, c: DetailsCommand(self.menu_repository).execute(u, c), pass_args=True))
        dispatcher.add_handler(CallbackQueryHandler(lambda u, c: ButtonHandler(self.menu_repository, self.cart_repository, self.order_handler, self.cart_handler).execute(u, c)))
        dispatcher.add_handler(MessageHandler(Filters.contact, lambda u, c:self.order_handler.get_phone_number(u, c)))
        dispatcher.add_handler(MessageHandler(Filters.location, lambda u, c:self.order_handler.get_location(u, c)))

    def run(self):
        self.updater.start_polling()
        self.updater.idle()



