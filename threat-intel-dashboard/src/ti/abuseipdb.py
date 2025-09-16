from __future__ import annotations
import requests, time
from typing import Optional
from .base import IOC, TIResult
from .cache import get_cached, set_cache
from ..config import ABUSEIPDB_KEY, ABUSE_MAX_AGE_DAYS

API_URL = "https://api.abuseipdb.com/api/v2/check"
SOURCE = "abuseipdb"

def enabled() -> bool:
    return bool(ABUSEIPDB_KEY)

def query(ip: str) -> Optional[dict]:
    if not enabled():
        return None
    # cache
    cached = get_cached("ip", ip, SOURCE)
    if cached is not None:
        return cached
    # request
    try:
        r = requests.get(
            API_URL,
            headers={"Key": ABUSEIPDB_KEY, "Accept": "application/json"},
            params={"ipAddress": ip, "maxAgeInDays": ABUSE_MAX_AGE_DAYS, "verbose": "true"},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            set_cache("ip", ip, SOURCE, data)
            return data
        return None
    except Exception:
        return None

def score_from_response(data: dict) -> int:
    """
    Map sencillo: abuseConfidenceScore ya es 0..100.
    """
    try:
        return int(data["data"]["abuseConfidenceScore"])
    except Exception:
        return 0

def resolve_ip(ip: str) -> Optional[TIResult]:
    data = query(ip)
    if data is None:
        return None
    score = score_from_response(data)
    return TIResult(ioc=IOC("ip", ip), reputation_score=score, source=SOURCE, raw=data)
