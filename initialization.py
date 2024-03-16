from dotenv import load_dotenv
from bot_manager import BotManager
import os
import logging

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    load_dotenv()
    token = os.getenv("CLIENT_BOT_TOKEN")
    dbconfig = {
        "host": "78.140.189.245",
        "user": "tg-client-user",
        "password": "LmkPJVndwb7Z",
        "database": "adp_pizza_db"
    }
    bot_manager = BotManager(token, dbconfig)
    bot_manager.run()
