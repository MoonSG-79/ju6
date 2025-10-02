
import os
from app.core.utils import get_logger

log = get_logger("notifier")

try:
    from telegram import Bot
except Exception:
    Bot = None

class Notifier:
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or os.getenv("TELEGRAM_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.bot = Bot(self.token) if (self.token and Bot is not None) else None

    def send(self, text: str):
        if self.bot and self.chat_id:
            try:
                self.bot.send_message(chat_id=self.chat_id, text=text)
                return True
            except Exception as e:
                log.error(f"Telegram send failed: {e}")
        log.info(f"[Notify] {text}")
        return False
