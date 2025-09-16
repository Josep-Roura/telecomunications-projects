from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
load_dotenv(ENV_PATH)  # si no existe, usa variables del entorno

ABUSEIPDB_KEY = os.getenv("ABUSEIPDB_KEY", "").strip()
TI_CACHE_TTL = int(os.getenv("TI_CACHE_TTL", "86400"))  # 24h
ABUSE_MAX_AGE_DAYS = int(os.getenv("ABUSE_MAX_AGE_DAYS", "180"))
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "").strip()

IPINFO_TOKEN = os.getenv("IPINFO_TOKEN", "").strip()
VT_API_KEY = os.getenv("VT_API_KEY", "").strip()

DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "threats.db"

REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
