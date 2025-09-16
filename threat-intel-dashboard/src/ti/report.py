from __future__ import annotations
import argparse, json, sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
import csv

from .config import DB_PATH, REPORTS_DIR

def _now():
    return datetime.now(timezone.utc)

def _read_events(hours: int):
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    try:
        since = (_now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        rows = con.execute("""
            SELECT ioc_type, value, first_seen, last_seen, ti_score
            FROM ioc
            WHERE last_seen >= ?
            ORDER BY ti_score DESC, last_seen DESC
        """, (since,)).fetchall()
        attrs = con.execute("""
            SELECT ioc_type, value, source, json
            FROM ioc_attrs
            WHERE source='profile'
        """).fetchall()
    finally:
        con.close()
    prof = {}
    for r in attrs:
        try:
            prof[(r["ioc_type"], r["value"])] = json.loads(r["json"])
        except Exception:
            prof[(r["ioc_type"], r["value"])] = {}
    data = []
    for r in rows:
        key = (r["ioc_type"], r["value"])
        p = prof.get(key, {})
        data.append({
            "ioc_type": r["ioc_type"],
            "value": r["value"],
            "ti_score": r["ti_score"],
            "last_seen": r["last_seen"],
            "country": p.get("country"),
            "org": p.get("org"),
        })
    return data

def write_csv(rows, out_csv: Path):
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ioc_type","value","ti_score","last_seen","country","org"])
        w.writeheader()
        w.writerows(rows)

def write_html(rows, out_html: Path, hours: int):
    now = _now().strftime("%Y-%m-%d %H:%M:%S UTC")
    html = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>Threat Intelligence Report</title>",
        "<style>body{font-family:system-ui,Segoe UI,Arial,sans-serif;padding:20px}"
        "h1{margin-bottom:0} .meta{color:#666} table{border-collapse:collapse;width:100%;margin-top:16px}"
        "th,td{border:1px solid #ddd;padding:8px;font-size:14px} th{background:#f5f5f5;text-align:left}"
        ".badge{display:inline-block;padding:2px 8px;border-radius:12px;background:#111;color:#fff;font-size:12px}"
        "</style></head><body>"
    ]
    html.append("<h1>Threat Intelligence Report</h1>")
    html.append(f"<div class='meta'>Generated: {now} &nbsp;•&nbsp; Window: last {hours}h</div>")
    if not rows:
        html += ["<p>No IOCs in the selected window.</p>", "</body></html>"]
        out_html.write_text("\n".join(html), encoding="utf-8")
        return
    high = sum(1 for r in rows if (r["ti_score"] or 0) >= 70)
    med  = sum(1 for r in rows if 40 <= (r["ti_score"] or 0) < 70)
    low  = sum(1 for r in rows if (r["ti_score"] or 0) < 40)
    html.append("<p><strong>Summary:</strong> "
                f"Total: {len(rows)} &nbsp;•&nbsp; High: <span class='badge'>{high}</span> "
                f"&nbsp;•&nbsp; Medium: <span class='badge' style='background:#eab308'>{med}</span> "
                f"&nbsp;•&nbsp; Low: <span class='badge' style='background:#0ea5e9'>{low}</span></p>")
    html.append("<table><thead><tr>"
                "<th>Type</th><th>Value</th><th>TI score</th><th>Country</th><th>Org/ASN</th><th>Last seen</th>"
                "</tr></thead><tbody>")
    for r in rows:
        html.append("<tr>"
                    f"<td>{r['ioc_type']}</td>"
                    f"<td>{r['value']}</td>"
                    f"<td>{r['ti_score'] if r['ti_score'] is not None else ''}</td>"
                    f"<td>{r.get('country') or ''}</td>"
                    f"<td>{r.get('org') or ''}</td>"
                    f"<td>{r['last_seen']}</td>"
                    "</tr>")
    html.append("</tbody></table></body></html>")
    out_html.write_text("\n".join(html), encoding="utf-8")

def generate_report(hours: int = 24) -> dict:
    rows = _read_events(hours)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_csv  = REPORTS_DIR / f"report_{hours}h_{stamp}.csv"
    out_html = REPORTS_DIR / f"report_{hours}h_{stamp}.html"
    write_csv(rows, out_csv)
    write_html(rows, out_html, hours)
    return {"csv": str(out_csv), "html": str(out_html), "count": len(rows)}

def main():
    ap = argparse.ArgumentParser(description="Generate TI reports (CSV + HTML)")
    ap.add_argument("--hours", type=int, default=24, help="Time window (hours)")
    args = ap.parse_args()
    res = generate_report(args.hours)
    print(json.dumps(res, ensure_ascii=False))

if __name__ == "__main__":
    main()
