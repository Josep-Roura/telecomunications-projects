import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MY_IP: str = os.getenv("MY_IP", "0.0.0.0")
    REQUEST_THRESHOLD: int = int(os.getenv("REQUEST_THRESHOLD", "5"))
    TIME_WINDOW: int = int(os.getenv("TIME_WINDOW", "5"))        # segundos
    BLOCK_TIME: int = int(os.getenv("BLOCK_TIME", "15"))         # segundos

    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    ALERT_LOG_PATH: str = os.getenv("ALERT_LOG_PATH", "./alerts.txt")

settings = Settings()