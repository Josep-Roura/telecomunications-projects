from __future__ import annotations
import requests
from typing import Optional
from .base import IOC, TIResult
from .cache import get_cached, set_cache
from ..config import os, ABUSE_MAX_AGE_DAYS  # reusamos si quieres limitar “freshness”

SOURCE = "ipinfo"
API = "https://ipinfo.io/"  # /{ip}?token=...

IPINFO_TOKEN = os.getenv("IPINFO_TOKEN", "").strip()

def enabled() -> bool:
    return bool(IPINFO_TOKEN)

def query(ip: str) -> Optional[dict]:
    if not enabled():
        return None
    cached = get_cached("ip", ip, SOURCE)
    if cached is not None:
        return cached
    try:
        r = requests.get(f"{API}{ip}", params={"token": IPINFO_TOKEN}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            set_cache("ip", ip, SOURCE, data)
            return data
        return None
    except Exception:
        return None

def score_from_response(data: dict) -> int:
    """
    ipinfo no da 'reputation'. Mapeo heurístico suave:
    - Si org/ASN típico de hosting (AS de cloud) => 10
    - País no penaliza por defecto (0)
    """
    org = (data.get("org") or "").lower()
    cloud_hint = any(k in org for k in ["aws", "amazon", "google", "gcp", "azure", "digitalocean", "ovh", "hetzner"])
    return 10 if cloud_hint else 0

def resolve_ip(ip: str) -> Optional[TIResult]:
    data = query(ip)
    if data is None:
        return None
    score = score_from_response(data)
    return TIResult(ioc=IOC("ip", ip), reputation_score=score, source=SOURCE, raw=data)
