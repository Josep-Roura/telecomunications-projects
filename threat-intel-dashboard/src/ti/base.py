from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class IOC:
    ioc_type: str  # "ip" | "domain" | "url" | "hash"
    value: str

@dataclass
class TIResult:
    ioc: IOC
    reputation_score: int  # 0..100 (map propio por fuente)
    source: str
    raw: dict
