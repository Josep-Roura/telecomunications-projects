# src/ti_abuseipdb.py
import os
import time
import requests
from typing import Optional, Dict

ABUSE_URL = "https://api.abuseipdb.com/api/v2/check"
DEFAULT_TTL_SEC = 6 * 3600  # 6 horas de cache

class AbuseIPDB:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 6, cache_ttl: int = DEFAULT_TTL_SEC):
        self.api_key = api_key or os.getenv("ABUSEIPDB_KEY", "").strip()
        self.timeout = timeout
        self.cache_ttl = cache_ttl

    def enabled(self) -> bool:
        return bool(self.api_key)

    def headers(self) -> Dict[str, str]:
        return {"Key": self.api_key, "Accept": "application/json"}

    def check(self, ip: str) -> Optional[Dict]:
        """
        Devuelve dict:
        {
          "ipAddress": "...",
          "abuseConfidenceScore": int,
          "totalReports": int,
          "lastReportedAt": "YYYY-MM-DDTHH:MM:SS+00:00" | None
        }
        o None si falla o no hay clave.
        """
        if not self.enabled():
            return None
        try:
            r = requests.get(
                ABUSE_URL,
                params={"ipAddress": ip, "maxAgeInDays": 365},
                headers=self.headers(),
                timeout=self.timeout,
            )
            if not r.ok:
                return None
            j = r.json()
            data = j.get("data") or {}
            return {
                "ipAddress": data.get("ipAddress"),
                "abuseConfidenceScore": int(data.get("abuseConfidenceScore", 0)),
                "totalReports": int(data.get("totalReports", 0)),
                "lastReportedAt": data.get("lastReportedAt"),
            }
        except Exception:
            return None

    @staticmethod
    def severity(score: int) -> str:
        # Ajusta umbrales a tu gusto
        if score >= 80: return "CRITICA"
        if score >= 50: return "ALTA"
        if score >= 20: return "MEDIA"
        if score >= 1:  return "BAJA"
        return "LIMPIA"
