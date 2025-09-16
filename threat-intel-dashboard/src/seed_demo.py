from __future__ import annotations
import argparse, random, time, json
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from . import db

COUNTRIES = ["US","DE","NL","FR","GB","ES","IT","PL","SE","CA","RU","CN","BR","AU","IN","SG","JP"]
ASNS = [
    "AS15169 Google LLC","AS13335 Cloudflare, Inc.","AS16509 Amazon.com, Inc.",
    "AS8075 Microsoft Corporation","AS14061 DigitalOcean, LLC","AS16276 OVH SAS",
    "AS24940 Hetzner Online GmbH","AS14618 Amazon AWS","AS9009 M247 Ltd","AS20473 Choopa, LLC"
]

IP_SAMPLES = [
    "8.8.8.8","1.1.1.1","185.220.101.1","104.16.132.229","34.117.201.170",
    "172.67.149.123","23.129.64.130","51.68.174.62","151.101.1.69","45.155.205.233"
]
DOM_SAMPLES = [
    "example.com","malware-traffic-analysis.net","test.phishing.example",
    "download.free-tools.cc","cdn-static-files.net","secure-login-check.app"
]
HASH_SAMPLES = [
    # MD5 / SHA256 de ejemplo (algunos inventados)
    "44d88612fea8a8f36de82e1278abb02f",
    "e2fc714c4727ee9395f324cd2e7f331f",
    "275a021bbfb6480f2a3080f5b6f9a5f2b5a021bbfb6480f2a3080f5b6f9a5f2",
    "d4735e3a265e16eee03f59718b9b5d03b6b93ff3f27a9c8e7a6c6d6d6d6d6d6"
]

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def _rand_ts(within_hours: int = 72) -> str:
    dt = datetime.now(timezone.utc) - timedelta(hours=random.randint(0, within_hours), minutes=random.randint(0, 59))
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def seed_ips(n: int):
    for _ in range(n):
        ip = random.choice(IP_SAMPLES)
        score = random.randint(5, 95)
        ts = _rand_ts()
        country = random.choice(COUNTRIES)
        org = random.choice(ASNS)
        profile = {"country": country, "lat": None, "lon": None, "org": org, "ti_score": score}
        db.upsert_ioc("ip", ip, first_seen=ts, last_seen=ts, ti_score=score)
        db.upsert_attr("ip", ip, "profile", json.dumps(profile, separators=(",",":")), int(time.time()))
        # Fuente “virustotal” sintética
        vt = {"last_analysis_stats": {"malicious": score//15, "suspicious": (score%10)//2}}
        db.upsert_attr("ip", ip, "virustotal", json.dumps(vt, separators=(",",":")), int(time.time()))

def seed_domains(n: int):
    for _ in range(n):
        d = random.choice(DOM_SAMPLES)
        score = random.randint(0, 90)
        ts = _rand_ts()
        db.upsert_ioc("domain", d, first_seen=ts, last_seen=ts, ti_score=score)
        prof = {"ti_score": score}
        db.upsert_attr("domain", d, "profile", json.dumps(prof, separators=(",",":")), int(time.time()))
        vt = {"last_analysis_stats": {"malicious": score//20, "suspicious": (score%8)//2}}
        db.upsert_attr("domain", d, "virustotal", json.dumps(vt, separators=(",",":")), int(time.time()))

def seed_hashes(n: int):
    for _ in range(n):
        h = random.choice(HASH_SAMPLES)
        score = random.randint(0, 100)
        ts = _rand_ts()
        db.upsert_ioc("hash", h, first_seen=ts, last_seen=ts, ti_score=score)
        prof = {"ti_score": score, "type_description": "executable", "meaningful_name": "demo_sample.bin", "size": random.randint(50_000, 5_000_000)}
        db.upsert_attr("hash", h, "profile", json.dumps(prof, separators=(",",":")), int(time.time()))
        vt = {
            "last_analysis_stats": {"malicious": score//10, "suspicious": (score%10)//3},
            "type_description": "executable","meaningful_name": "demo_sample.bin",
            "md5": h if len(h)==32 else None, "sha256": h if len(h)==64 else None, "size": prof["size"]
        }
        db.upsert_attr("hash", h, "virustotal", json.dumps(vt, separators=(",",":")), int(time.time()))

def main():
    ap = argparse.ArgumentParser(description="Seed demo data for the TI dashboard (no APIs required).")
    ap.add_argument("--ips", type=int, default=20)
    ap.add_argument("--domains", type=int, default=10)
    ap.add_argument("--hashes", type=int, default=8)
    args = ap.parse_args()
    db.init_db()
    seed_ips(args.ips)
    seed_domains(args.domains)
    seed_hashes(args.hashes)
    print(f"[OK] Seed demo: ips={args.ips}, domains={args.domains}, hashes={args.hashes}")

if __name__ == "__main__":
    main()
