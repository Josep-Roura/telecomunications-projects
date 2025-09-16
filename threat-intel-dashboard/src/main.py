from __future__ import annotations
import argparse, json, time as _t
from datetime import datetime, timezone
from . import db
from .ti.resolve import resolve_ip_all, resolve_domain_all, resolve_hash_all

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def resolve_and_store_ip(ip: str):
    res = resolve_ip_all(ip)
    if not res:
        print("[ERR] No TI data (IP)")
        return
    geo = res.get("geo", {})
    db.upsert_ioc("ip", ip, first_seen=_now(), last_seen=_now(), ti_score=int(res.get("ti_score", 0)))
    profile = {"country": geo.get("country"), "lat": geo.get("lat"), "lon": geo.get("lon"),
               "org": res.get("org"), "ti_score": res.get("ti_score")}
    db.upsert_attr("ip", ip, "profile", json.dumps(profile, separators=(",",":")), int(_t.time()))
    for src, payload in (res.get("sources") or {}).items():
        db.upsert_attr("ip", ip, src, json.dumps(payload, separators=(",",":")), int(_t.time()))
    print(f"[OK] IP {ip} ti_score={res.get('ti_score')} sources={list((res.get('sources') or {}).keys())}")

def resolve_and_store_domain(domain: str):
    res = resolve_domain_all(domain)
    if not res:
        print("[ERR] No TI data (domain)")
        return
    db.upsert_ioc("domain", domain, first_seen=_now(), last_seen=_now(), ti_score=int(res.get("ti_score", 0)))
    profile = {"ti_score": res.get("ti_score")}
    db.upsert_attr("domain", domain, "profile", json.dumps(profile, separators=(",",":")), int(_t.time()))
    for src, payload in (res.get("sources") or {}).items():
        db.upsert_attr("domain", domain, src, json.dumps(payload, separators=(",",":")), int(_t.time()))
    print(f"[OK] DOMAIN {domain} ti_score={res.get('ti_score')} sources={list((res.get('sources') or {}).keys())}")

def resolve_and_store_hash(h: str):
    res = resolve_hash_all(h)
    if not res:
        print("[ERR] No TI data (hash)")
        return
    db.upsert_ioc("hash", h, first_seen=_now(), last_seen=_now(), ti_score=int(res.get("ti_score", 0)))
    # snapshot de hash (perfil VT básico)
    file_prof = res.get("file", {}) or {}
    db.upsert_attr("hash", h, "profile", json.dumps({"ti_score": res.get("ti_score"), **file_prof}, separators=(",",":")), int(_t.time()))
    for src, payload in (res.get("sources") or {}).items():
        db.upsert_attr("hash", h, src, json.dumps(payload, separators=(",",":")), int(_t.time()))
    print(f"[OK] HASH {h} ti_score={res.get('ti_score')} sources={list((res.get('sources') or {}).keys())}")

def main():
    ap = argparse.ArgumentParser(description="Threat Intelligence CLI")
    ap.add_argument("--init-db", action="store_true", help="Crear/migrar DB")
    ap.add_argument("--ioc-ip", type=str, help="Resolver IP (multi-fuente) y registrar")
    ap.add_argument("--ioc-domain", type=str, help="Resolver dominio (multi-fuente) y registrar")
    ap.add_argument("--ioc-hash", type=str, help="Resolver hash (VirusTotal) y registrar")
    args = ap.parse_args()

    if args.init_db:
        db.init_db()
        print("[OK] DB inicializada")

    if args.ioc_ip:
        db.init_db()
        resolve_and_store_ip(args.ioc_ip)

    if args.ioc_domain:
        db.init_db()
        resolve_and_store_domain(args.ioc_domain)

    if args.ioc_hash:
        db.init_db()
        resolve_and_store_hash(args.ioc_hash)

if __name__ == "__main__":
    main()
