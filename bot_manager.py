from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from commands import StartCommand, MenuCommand, DetailsCommand, ButtonHandler
from db_manager import DBManager

class BotManager:
    def __init__(self, token, dbconfig):
        self.updater = Updater(token, use_context=True)
        DBManager(dbconfig)  # Initialize DB connection pool
        self._register_handlers()

    def _register_handlers(self):
        dispatcher = self.updater.dispatcher
        dispatcher.add_handler(CommandHandler("start", lambda u, c: StartCommand().execute(u, c)))
        dispatcher.add_handler(CommandHandler("menu", lambda u, c: MenuCommand().execute(u, c)))
        dispatcher.add_handler(CommandHandler("details", lambda u, c: DetailsCommand().execute(u, c), pass_args=True))
        dispatcher.add_handler(CallbackQueryHandler(lambda u, c: ButtonHandler().execute(u, c)))

    def run(self):
        self.updater.start_polling()
        self.updater.idle()
