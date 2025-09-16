import requests
from .config import settings

class Notifier:
    def __init__(self, token: str | None = None, chat_id: str | None = None):
        self.token = token or settings.TELEGRAM_TOKEN
        self.chat_id = chat_id or settings.TELEGRAM_CHAT_ID

    def send_telegram(self, message: str) -> bool:
        if not self.token or not self.chat_id:
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            r = requests.post(url, params={"chat_id": self.chat_id, "text": message}, timeout=10)
            return r.status_code == 200
        except Exception:
            return False
