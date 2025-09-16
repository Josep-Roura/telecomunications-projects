from __future__ import annotations
import sqlite3
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
from .config import DB_PATH

def _connect():
    con = sqlite3.connect(str(DB_PATH))
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    return con

def init_db():
    con = _connect()
    try:
        con.execute("""
        CREATE TABLE IF NOT EXISTS ioc (
          ioc_type TEXT NOT NULL,          -- ip | domain | url | hash
          value TEXT NOT NULL,
          first_seen TEXT,
          last_seen TEXT,
          ti_score INTEGER,                -- 0-100 (score combinado)
          PRIMARY KEY (ioc_type, value)
        );
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS ioc_attrs (
          ioc_type TEXT NOT NULL,
          value TEXT NOT NULL,
          source TEXT NOT NULL,            -- abuseipdb, virustotal, etc.
          json TEXT NOT NULL,              -- respuesta cruda (compactada)
          updated_at INTEGER NOT NULL,     -- epoch
          PRIMARY KEY (ioc_type, value, source)
        );
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_ioc_value ON ioc(value);")
        con.commit()
    finally:
        con.close()

def upsert_ioc(ioc_type: str, value: str, first_seen: Optional[str], last_seen: Optional[str], ti_score: Optional[int]):
    con = _connect()
    try:
        con.execute("""
            INSERT INTO ioc(ioc_type, value, first_seen, last_seen, ti_score)
            VALUES(?,?,?,?,?)
            ON CONFLICT(ioc_type, value) DO UPDATE SET
              first_seen = COALESCE(ioc.first_seen, excluded.first_seen),
              last_seen  = excluded.last_seen,
              ti_score   = excluded.ti_score;
        """, (ioc_type, value, first_seen, last_seen, ti_score))
        con.commit()
    finally:
        con.close()

def upsert_attr(ioc_type: str, value: str, source: str, json_text: str, updated_at: int):
    con = _connect()
    try:
        con.execute("""
            INSERT INTO ioc_attrs(ioc_type, value, source, json, updated_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(ioc_type, value, source) DO UPDATE SET
              json = excluded.json,
              updated_at = excluded.updated_at;
        """, (ioc_type, value, source, json_text, updated_at))
        con.commit()
    finally:
        con.close()

def get_attr(ioc_type: str, value: str, source: str) -> Optional[Tuple[str,int]]:
    con = _connect()
    try:
        cur = con.execute("SELECT json, updated_at FROM ioc_attrs WHERE ioc_type=? AND value=? AND source=?;",
                          (ioc_type, value, source))
        row = cur.fetchone()
        return (row[0], row[1]) if row else None
    finally:
        con.close()

def get_all_attrs(ioc_type: str, value: str) -> List[Tuple[str, str, int]]:
    """
    Devuelve lista de (source, json, updated_at) para un IOC.
    """
    con = _connect()
    try:
        cur = con.execute("SELECT source, json, updated_at FROM ioc_attrs WHERE ioc_type=? AND value=? ORDER BY source ASC;",
                          (ioc_type, value))
        return cur.fetchall()
    finally:
        con.close()

def get_ioc(ioc_type: str, value: str) -> Optional[dict]:
    con = _connect()
    try:
        cur = con.execute("SELECT ioc_type, value, first_seen, last_seen, ti_score FROM ioc WHERE ioc_type=? AND value=?;",
                          (ioc_type, value))
        r = cur.fetchone()
        if not r: return None
        return {"ioc_type": r[0], "value": r[1], "first_seen": r[2], "last_seen": r[3], "ti_score": r[4]}
    finally:
        con.close()

def list_ioc(limit: int = 200) -> list[dict]:
    con = _connect()
    try:
        cur = con.execute("SELECT ioc_type, value, first_seen, last_seen, ti_score FROM ioc ORDER BY last_seen DESC LIMIT ?;", (limit,))
        rows = cur.fetchall()
        return [{"ioc_type": a, "value": b, "first_seen": c, "last_seen": d, "ti_score": e} for (a,b,c,d,e) in rows]
    finally:
        con.close()
