# src/db.py
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional, Tuple, List

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "events.db"

def _connect():
    con = sqlite3.connect(str(DB_PATH))
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    return con

def _table_exists(con: sqlite3.Connection, name: str) -> bool:
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (name,))
    return cur.fetchone() is not None

def _col_exists(con: sqlite3.Connection, table: str, col: str) -> bool:
    cur = con.execute(f"PRAGMA table_info({table});")
    return any(row[1] == col for row in cur.fetchall())

def init_db():
    con = _connect()
    try:
        # events
        if not _table_exists(con, "events"):
            con.execute("""
                CREATE TABLE events(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT NOT NULL,
                  ip TEXT NOT NULL,
                  count INTEGER NOT NULL,
                  time_window INTEGER NOT NULL,
                  level TEXT,
                  lat REAL, lon REAL, country TEXT, org TEXT,
                  abuse_confidence INTEGER, total_reports INTEGER, last_reported_at TEXT,
                  blocked INTEGER DEFAULT 0,
                  ml_score REAL,               -- NUEVO ML
                  ml_flag INTEGER DEFAULT 0    -- NUEVO ML
                );
            """)
            con.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(timestamp);")
            con.execute("CREATE INDEX IF NOT EXISTS idx_events_ip ON events(ip);")
        else:
            # Migraciones no destructivas
            for c, t in [
                ("lat", "REAL"), ("lon", "REAL"), ("country", "TEXT"), ("org", "TEXT"),
                ("abuse_confidence","INTEGER"), ("total_reports","INTEGER"), ("last_reported_at","TEXT"),
                ("blocked","INTEGER"),
                ("ml_score","REAL"),
                ("ml_flag","INTEGER")
            ]:
                if not _col_exists(con, "events", c):
                    con.execute(f"ALTER TABLE events ADD COLUMN {c} {t};")
            # defaults razonables
            con.execute("UPDATE events SET blocked=COALESCE(blocked,0) WHERE blocked IS NULL;")
            con.execute("UPDATE events SET ml_flag=COALESCE(ml_flag,0) WHERE ml_flag IS NULL;")

        # ti_abuse
        if not _table_exists(con, "ti_abuse"):
            con.execute("""
                CREATE TABLE ti_abuse(
                  ip TEXT PRIMARY KEY,
                  abuse_confidence INTEGER,
                  total_reports INTEGER,
                  last_reported_at TEXT,
                  updated_at INTEGER
                );
            """)

        # blocklist
        if not _table_exists(con, "blocklist"):
            con.execute("""
                CREATE TABLE blocklist(
                  ip TEXT PRIMARY KEY,
                  reason TEXT,
                  created_at TEXT DEFAULT (datetime('now'))
                );
            """)

        # allowlist
        if not _table_exists(con, "allowlist"):
            con.execute("""
                CREATE TABLE allowlist(
                  ip TEXT PRIMARY KEY,
                  reason TEXT,
                  created_at TEXT DEFAULT (datetime('now'))
                );
            """)

        con.commit()
    finally:
        con.close()

def insert_event(
    timestamp: str,
    ip: str,
    count: int,
    time_window: int,
    level: str,
    lat: float = None,
    lon: float = None,
    country: str = None,
    org: str = None,
    abuse_confidence: int = None,
    total_reports: int = None,
    last_reported_at: str = None,
    blocked: int = 0,
    ml_score: float = None,
    ml_flag: int = 0
):
    con = _connect()
    try:
        con.execute("""
            INSERT INTO events(
              timestamp, ip, count, time_window, level,
              lat, lon, country, org,
              abuse_confidence, total_reports, last_reported_at,
              blocked, ml_score, ml_flag
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
        """, (
            timestamp, ip, int(count), int(time_window), level,
            lat, lon, country, org,
            abuse_confidence, total_reports, last_reported_at,
            int(blocked), ml_score, int(ml_flag)
        ))
        con.commit()
    finally:
        con.close()

# ─────────── Threat Intel (AbuseIPDB cache) ───────────
def upsert_ti(ip: str, abuse_confidence: int, total_reports: int, last_reported_at: str, updated_at: int):
    con = _connect()
    try:
        con.execute("""
            INSERT INTO ti_abuse(ip, abuse_confidence, total_reports, last_reported_at, updated_at)
            VALUES (?,?,?,?,?)
            ON CONFLICT(ip) DO UPDATE SET
              abuse_confidence=excluded.abuse_confidence,
              total_reports=excluded.total_reports,
              last_reported_at=excluded.last_reported_at,
              updated_at=excluded.updated_at;
        """, (ip, abuse_confidence, total_reports, last_reported_at, updated_at))
        con.commit()
    finally:
        con.close()

# ─────────── Listas de control ───────────
def add_block(ip: str, reason: str = None):
    con = _connect()
    try:
        con.execute("INSERT OR REPLACE INTO blocklist(ip,reason,created_at) VALUES (?, ?, datetime('now'));", (ip, reason))
        con.commit()
    finally:
        con.close()

def del_block(ip: str):
    con = _connect()
    try:
        con.execute("DELETE FROM blocklist WHERE ip=?;", (ip,))
        con.commit()
    finally:
        con.close()

def list_blocklist() -> List[tuple]:
    con = _connect()
    try:
        cur = con.execute("SELECT ip,reason,created_at FROM blocklist ORDER BY created_at DESC;")
        return cur.fetchall()
    finally:
        con.close()

def add_allow(ip: str, reason: str = None):
    con = _connect()
    try:
        con.execute("INSERT OR REPLACE INTO allowlist(ip,reason,created_at) VALUES (?, ?, datetime('now'));", (ip, reason))
        con.commit()
    finally:
        con.close()

def del_allow(ip: str):
    con = _connect()
    try:
        con.execute("DELETE FROM allowlist WHERE ip=?;", (ip,))
        con.commit()
    finally:
        con.close()

def list_allowlist() -> List[tuple]:
    con = _connect()
    try:
        cur = con.execute("SELECT ip,reason,created_at FROM allowlist ORDER BY created_at DESC;")
        return cur.fetchall()
    finally:
        con.close()

def in_allowlist(ip: str) -> bool:
    con = _connect()
    try:
        cur = con.execute("SELECT 1 FROM allowlist WHERE ip=? LIMIT 1;", (ip,))
        return cur.fetchone() is not None
    finally:
        con.close()

def in_blocklist(ip: str) -> bool:
    con = _connect()
    try:
        cur = con.execute("SELECT 1 FROM blocklist WHERE ip=? LIMIT 1;", (ip,))
        return cur.fetchone() is not None
    finally:
        con.close()
