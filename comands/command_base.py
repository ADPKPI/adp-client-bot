from telegram import Update
from telegram.ext import CallbackContext

class CommandBase:
    def execute(self, update: Update, context: CallbackContext):
        raise NotImplementedError