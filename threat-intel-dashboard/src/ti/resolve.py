from __future__ import annotations
from typing import Dict, Any, List
from .base import IOC, TIResult
from . import abuseipdb as abip
from . import ipinfo as ipi
from . import virustotal as vt

def resolve_ip_all(ip: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "ioc_type": "ip",
        "value": ip,
        "sources": {},
        "geo": {},
        "asn": None,
        "org": None,
        "score_components": {}
    }

    # AbuseIPDB
    if abip.enabled():
        r = abip.resolve_ip(ip)
        if r:
            abuse = r.raw.get("data", {})
            data["sources"]["abuseipdb"] = {
                "abuseConfidenceScore": abuse.get("abuseConfidenceScore", 0),
                "totalReports": abuse.get("totalReports", 0),
                "lastReportedAt": abuse.get("lastReportedAt")
            }
            data["score_components"]["abuseipdb"] = r.reputation_score

    # ipinfo
    if ipi.enabled():
        r = ipi.resolve_ip(ip)
        if r:
            info = r.raw
            data["sources"]["ipinfo"] = info
            data["geo"]["country"] = info.get("country")
            loc = (info.get("loc") or ",").split(",")
            if len(loc) == 2:
                data["geo"]["lat"] = _safe_float(loc[0])
                data["geo"]["lon"] = _safe_float(loc[1])
            data["asn"] = info.get("org")
            data["org"] = info.get("hostname") or info.get("org")
            data["score_components"]["ipinfo_hint"] = r.reputation_score

    # VirusTotal (IP)
    if vt.enabled():
        r = vt.resolve_ip(ip)
        if r:
            vt_stats = ((r.raw.get("data") or {}).get("attributes") or {}).get("last_analysis_stats", {})
            data["sources"]["virustotal"] = {"last_analysis_stats": vt_stats}
            data["score_components"]["vt"] = r.reputation_score

    # Score consolidado
    abuse = data["score_components"].get("abuseipdb", 0)
    vt_s  = data["score_components"].get("vt", 0)
    hint  = data["score_components"].get("ipinfo_hint", 0)
    ti_score = round(0.8 * abuse + 0.2 * vt_s + 0.1 * hint)
    data["ti_score"] = int(max(0, min(100, ti_score)))
    return data

def resolve_domain_all(domain: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {"ioc_type": "domain", "value": domain, "sources": {}, "score_components": {}}
    if vt.enabled():
        r = vt.resolve_domain(domain)
        if r:
            vt_stats = ((r.raw.get("data") or {}).get("attributes") or {}).get("last_analysis_stats", {})
            data["sources"]["virustotal"] = {"last_analysis_stats": vt_stats}
            data["score_components"]["vt"] = r.reputation_score
    data["ti_score"] = int(data["score_components"].get("vt", 0))
    return data

def resolve_hash_all(h: str) -> Dict[str, Any]:
    """
    Resolver hash de fichero (MD5/SHA1/SHA256) con VirusTotal.
    """
    data: Dict[str, Any] = {"ioc_type": "hash", "value": h, "sources": {}, "score_components": {}, "file": {}}
    if vt.enabled():
        r = vt.resolve_hash(h)
        if r:
            attrs = ((r.raw.get("data") or {}).get("attributes") or {})
            vt_stats = attrs.get("last_analysis_stats", {})
            data["sources"]["virustotal"] = {
                "last_analysis_stats": vt_stats,
                "type_description": attrs.get("type_description"),
                "meaningful_name": attrs.get("meaningful_name"),
                "md5": attrs.get("md5"),
                "sha1": attrs.get("sha1"),
                "sha256": attrs.get("sha256"),
                "size": attrs.get("size"),
                "last_analysis_results": attrs.get("last_analysis_results")
            }
            data["file"] = {
                "type_description": attrs.get("type_description"),
                "meaningful_name": attrs.get("meaningful_name"),
                "size": attrs.get("size"),
            }
            data["score_components"]["vt"] = r.reputation_score
    data["ti_score"] = int(data["score_components"].get("vt", 0))
    return data

def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return None
