import json
from pathlib import Path
from typing import Optional, Dict
import requests
import os

CACHE_PATH = Path("./data/ip_geo_cache.json")

class GeoResolver:
    def __init__(self, ipinfo_token: Optional[str] = None, cache_path: Path = CACHE_PATH):
        self.token = ipinfo_token or os.getenv("IPINFO_TOKEN", "").strip()
        self.cache_path = cache_path
        self.cache: Dict[str, dict] = {}
        self._load_cache()

    def _load_cache(self):
        try:
            if self.cache_path.exists():
                self.cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except Exception:
            self.cache = {}

    def _save_cache(self):
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(
                json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    def resolve(self, ip: str) -> dict:
        """
        Devuelve dict con: {lat, lon, country, org}. Usa caché.
        """
        if ip in self.cache:
            return self.cache[ip]

        data = {"lat": None, "lon": None, "country": None, "org": None}

        try:
            if self.token:
                # ipinfo
                url = f"https://ipinfo.io/{ip}/json?token={self.token}"
                r = requests.get(url, timeout=5)
                if r.ok:
                    j = r.json()
                    loc = j.get("loc", "")
                    lat, lon = (loc.split(",") + [None, None])[:2]
                    data["lat"] = float(lat) if lat else None
                    data["lon"] = float(lon) if lon else None
                    data["country"] = j.get("country")
                    data["org"] = j.get("org")
            else:
                # ipapi.co como fallback
                url = f"https://ipapi.co/{ip}/json/"
                r = requests.get(url, timeout=5)
                if r.ok:
                    j = r.json()
                    data["lat"] = j.get("latitude")
                    data["lon"] = j.get("longitude")
                    data["country"] = j.get("country_name") or j.get("country")
                    data["org"] = j.get("org") or j.get("asn")
        except Exception:
            pass

        self.cache[ip] = data
        self._save_cache()
        return data
