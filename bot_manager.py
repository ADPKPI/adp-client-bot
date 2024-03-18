from telegram.ext import Updater, CommandHandler, CallbackQueryHandler,MessageHandler, Filters
from db_manager import DBManager, MenuRepository, CartRepository, UserRepository, OrderRepository
from command_factory import CommandFactory

class BotManager:
    def __init__(self, token, dbconfig):
        self.updater = Updater(token, use_context=True)
        DBManager(dbconfig)

        self.menu_repository = MenuRepository()
        self.cart_repository = CartRepository()
        self.user_repository = UserRepository()
        self.order_repository = OrderRepository()

        self._register_handlers()

    def _register_handlers(self):
        self.factory = CommandFactory(self.menu_repository, self.cart_repository, self.user_repository, self.order_repository)
        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", lambda u, c: self.factory.get_command("start").execute(u, c)))
        dispatcher.add_handler(CommandHandler("details", lambda u, c: self.factory.get_command("details").execute(u, c), pass_args=True))
        dispatcher.add_handler(CallbackQueryHandler(lambda u, c: self.factory.get_command("button_handler").execute(u, c)))
        dispatcher.add_handler(MessageHandler(Filters.contact, lambda u, c: self.factory.get_command("got_phone_number").execute(u,c)))
        dispatcher.add_handler(MessageHandler(Filters.location, lambda u, c: self.factory.get_command("got_location").execute(u,c)))

    def run(self):
        self.updater.start_polling()
        self.updater.idle()



