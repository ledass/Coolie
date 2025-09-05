import logging
import logging.config
from dotenv import load_dotenv
from threading import Thread
from web import app as flask_app  # Import Flask app

from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from pyromod import listen
from utils import Media
from info import SESSION, API_ID, API_HASH, BOT_TOKEN

load_dotenv()

# Logging
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.WARNING)


class Bot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        await super().start()
        await Media.ensure_indexes()
        me = await self.get_me()
        self.username = '@' + me.username
        print(f"{me.first_name} with Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")

    async def stop(self, *args):
        await super().stop()
        print("Bot stopped. Bye.")


# Function to run Flask
def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    # Start Flask in a separate thread
    Thread(target=run_flask, daemon=True).start()

    # Start Pyrogram bot
    app = Bot()
    app.run()
          
