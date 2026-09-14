#!/usr/bin/env python3
"""Fetch each bottle's price_average from the Wine-Searcher wine-check API.

    WS_API_KEY=... python3 scripts/fetch_ws_prices.py            # every bottle
    WS_API_KEY=... python3 scripts/fetch_ws_prices.py --only 30  # one bottle
    python3 scripts/fetch_ws_prices.py --dry-run                 # print the requests only

price_average in the wine-check response is the "Average retail price across all
listings" — the same number the Wine-Searcher page shows as Avg Price. Leaving
location and state off keeps it worldwide instead of narrowing to one country,
which is exactly what we want, so this script never sends them.

The endpoint path was inferred by API Evangelist from public material and may not
match the real one, so the first request tries each candidate shape in turn and
reuses whichever works.
"""
import argparse, json, os, ssl, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "cellar.json"
BASE = "https://www.wine-searcher.com/ws_api.php"
# Wine-Searcher's own documentation says only that the base URL is ws_api.php and
# that api_key and winename are required. The path-suffixed shapes were inferred
# rather than documented, so try the flat shape the docs describe first.
CANDIDATES = [
    BASE,                           # the shape the documentation describes
    BASE + "/wine-check",           # the shape inferred from the OpenAPI spec
    BASE + "?action=wine-check",
]
PAUSE = 7.0                         # trial keys allow 100 calls a day; leave room


def winename(b):
    """The stored Wine-Searcher URL slug is already their canonical spelling."""
    slug = b["ws_url"].rstrip("/").split("/find/")[-1]
    return slug.split("/")[0]


def build(url, key, b):
    q = {"api_key": key, "winename": winename(b), "currencycode": "USD", "format": "json"}
    if b.get("vintage"):
        q["vintage"] = str(b["vintage"])
    elif b.get("vintage_label") == "NV":
        q["vintage"] = "NV"
    # '+' is Wine-Searcher's word separator inside winename. The default encoder
    # would turn it into %2B, so pass it through via safe.
    sep = "&" if "?" in url else "?"
    return url + sep + urllib.parse.urlencode(q, quote_via=urllib.parse.quote, safe="+")


def ctx():
    ca = "/root/.ccr/ca-bundle.crt"
    return ssl.create_default_context(cafile=ca) if os.path.exists(ca) else ssl.create_default_context()


def call(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "cellaros/1.0"})
    with urllib.request.urlopen(req, timeout=30, context=ctx()) as r:
        return json.loads(r.read().decode())


def redact(url, key):
    return url.replace(key, "***") if key else url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", type=int, action="append", help="bottle number; repeatable")
    a = ap.parse_args()

    key = os.environ.get("WS_API_KEY", "")
    if not key and not a.dry_run:
        sys.exit("WS_API_KEY is not set. Run with WS_API_KEY=... or use --dry-run.")

    d = json.loads(SRC.read_text())
    bottles = [b for b in d["bottles"] if not a.only or b["id"] in a.only]

    if a.dry_run:
        for b in bottles:
            print(f"{b['id']:>2} {b['display'][:38]:<38} {redact(build(CANDIDATES[0], key or 'KEY', b), key)}")
        print(f"\n{len(bottles)} requests · {PAUSE}s apart · about {len(bottles) * PAUSE / 60:.1f} min")
        return

    shape = None
    ok = bad = 0
    for i, b in enumerate(bottles):
        tries = [shape] if shape else CANDIDATES
        data = None
        for cand in tries:
            try:
                r = call(build(cand, key, b))
            except Exception as e:                       # a wrong shape returns 404 or 500
                print(f"  · {cand.split('ws_api.php')[-1] or '(query only)'} → {e}")
                continue
            if r.get("status") == 0 and r.get("wine"):
                shape, data = cand, r["wine"]
                break
            print(f"  · status={r.get('status')} {r.get('message')}")
        if not data:
            print(f"{b['id']:>2} {b['display'][:34]:<34} failed")
            bad += 1
        else:
            avg = data.get("price_average")
            if avg:
                b["price"].update({
                    "avg_usd": round(float(avg)),
                    "confidence": "verified", "source_kind": "api",
                    "source": "Wine-Searcher wine-check API · price_average (USD, worldwide)",
                    "basis": "750ml, ex-tax",
                    "ws_min": data.get("price_min"), "ws_max": data.get("price_max"),
                    "ws_listings": data.get("listing_count"),
                })
                b["price"].pop("note", None)
                b["price"]["verified"] = (
                    f"API response · low {data.get('price_min')} / high {data.get('price_max')}"
                    f" / {data.get('listing_count')} listings")
                print(f"{b['id']:>2} {b['display'][:34]:<34} ${round(float(avg)):>5}")
                ok += 1
            else:
                print(f"{b['id']:>2} {b['display'][:34]:<34} no price_average")
                bad += 1
        if i < len(bottles) - 1:
            time.sleep(PAUSE)

    SRC.write_text(json.dumps(d, ensure_ascii=False, indent=2))
    print(f"\n{ok} confirmed · {bad} failed → {SRC.relative_to(ROOT)} updated")
    print("Next: python3 scripts/build_dashboard.py && python3 scripts/build_cellar.py")


if __name__ == "__main__":
    main()
