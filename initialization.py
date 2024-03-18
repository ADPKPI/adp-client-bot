from dotenv import load_dotenv
from bot_manager import BotManager
import os
import logging
from logging.handlers import TimedRotatingFileHandler

def config_logging():
    logger = logging.getLogger('adp-client-bot-logger')
    logger.setLevel(logging.INFO)

    handler = TimedRotatingFileHandler(f'{os.getenv("ADP-CLIENT-BOT-LOGS-LOCATION")}/adp-client-bot.log', when="M", interval=1, backupCount=12)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logger.addHandler(handler)

if __name__ == '__main__':
    load_dotenv()
    config_logging()
    token = os.getenv("CLIENT_BOT_TOKEN")
    dbconfig = {
        "host": "78.140.189.245",
        "user": "tg-client-user",
        "password": "LmkPJVndwb7Z",
        "database": "adp_pizza_db"
    }
    bot_manager = BotManager(token, dbconfig)
    bot_manager.run()

