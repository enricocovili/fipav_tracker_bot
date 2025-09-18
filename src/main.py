import os
import asyncio
from dotenv import load_dotenv
from telethon.sync import TelegramClient
import logging

import handlers.menu

# Set up logging: DEBUG and up to file, INFO and up to console
log_formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"
)

file_handler = logging.FileHandler("logs/bot.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])

load_dotenv()

api_id = int(str(os.getenv("API_ID")))
api_hash = str(os.getenv("API_HASH"))
bot_token = str(os.getenv("BOT_TOKEN"))


async def main():
    bot = TelegramClient("bot", api_id, api_hash)

    bot.add_event_handler(handlers.menu.MainMenu.handle)
    bot.add_event_handler(handlers.menu.MainMenu.callback)

    bot.users_state = {}

    await bot.start(bot_token=bot_token)

    logging.info("started")
    await bot.run_until_disconnected()


asyncio.run(main())
