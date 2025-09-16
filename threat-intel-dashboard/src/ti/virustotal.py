from __future__ import annotations
import requests
from typing import Optional
from .base import IOC, TIResult
from .cache import get_cached, set_cache
from ..config import VT_API_KEY

SOURCE = "virustotal"
API_BASE = "https://www.virustotal.com/api/v3"

def enabled() -> bool:
    return bool(VT_API_KEY)

def _headers():
    return {"x-apikey": VT_API_KEY}

# -----------------------
# IP
# -----------------------
def query_ip(ip: str) -> Optional[dict]:
    if not enabled():
        return None
    cached = get_cached("ip", ip, SOURCE)
    if cached is not None:
        return cached
    try:
        r = requests.get(f"{API_BASE}/ip_addresses/{ip}", headers=_headers(), timeout=15)
        if r.status_code == 200:
            data = r.json()
            set_cache("ip", ip, SOURCE, data)
            return data
        return None
    except Exception:
        return None

def resolve_ip(ip: str) -> Optional[TIResult]:
    data = query_ip(ip)
    if data is None:
        return None
    stats = (data.get("data") or {}).get("attributes", {}).get("last_analysis_stats", {})
    score = score_from_stats(stats)
    return TIResult(ioc=IOC("ip", ip), reputation_score=score, source=SOURCE, raw=data)

# -----------------------
# Domain
# -----------------------
def query_domain(domain: str) -> Optional[dict]:
    if not enabled():
        return None
    cached = get_cached("domain", domain, SOURCE)
    if cached is not None:
        return cached
    try:
        r = requests.get(f"{API_BASE}/domains/{domain}", headers=_headers(), timeout=15)
        if r.status_code == 200:
            data = r.json()
            set_cache("domain", domain, SOURCE, data)
            return data
        return None
    except Exception:
        return None

def resolve_domain(domain: str) -> Optional[TIResult]:
    data = query_domain(domain)
    if data is None:
        return None
    stats = (data.get("data") or {}).get("attributes", {}).get("last_analysis_stats", {})
    score = score_from_stats(stats)
    return TIResult(ioc=IOC("domain", domain), reputation_score=score, source=SOURCE, raw=data)

# -----------------------
# File hash (md5/sha1/sha256)
# -----------------------
def query_hash(h: str) -> Optional[dict]:
    if not enabled():
        return None
    cached = get_cached("hash", h, SOURCE)
    if cached is not None:
        return cached
    try:
        r = requests.get(f"{API_BASE}/files/{h}", headers=_headers(), timeout=20)
        if r.status_code == 200:
            data = r.json()
            set_cache("hash", h, SOURCE, data)
            return data
        return None
    except Exception:
        return None

def resolve_hash(h: str) -> Optional[TIResult]:
    data = query_hash(h)
    if data is None:
        return None
    stats = (data.get("data") or {}).get("attributes", {}).get("last_analysis_stats", {})
    score = score_from_stats(stats)
    return TIResult(ioc=IOC("hash", h), reputation_score=score, source=SOURCE, raw=data)

# -----------------------
# Common
# -----------------------
def score_from_stats(stats: dict) -> int:
    """
    Mapa simple para VT:
      score = malicious*10 + suspicious*5 (cap a 100)
    """
    if not isinstance(stats, dict):
        return 0
    mal = int(stats.get("malicious", 0))
    susp = int(stats.get("suspicious", 0))
    score = mal * 10 + susp * 5
    return max(0, min(100, score))
