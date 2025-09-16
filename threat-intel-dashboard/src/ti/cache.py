from __future__ import annotations
import json, time
from typing import Optional, Tuple
from .. import db
from ..config import TI_CACHE_TTL

def get_cached(ioc_type: str, value: str, source: str) -> Optional[dict]:
    row = db.get_attr(ioc_type, value, source)
    if not row: return None
    json_text, updated_at = row
    if (time.time() - updated_at) > TI_CACHE_TTL:
        return None
    try:
        return json.loads(json_text)
    except Exception:
        return None

def set_cache(ioc_type: str, value: str, source: str, data: dict):
    try:
        db.upsert_attr(ioc_type, value, source, json.dumps(data, separators=(",",":")), int(time.time()))
    except Exception:
        pass
