#!/usr/bin/env python3
"""Check data/cellar.json against the invariants the generators assume.

    python3 scripts/check.py

Exits non-zero on the first failing bottle, so it can gate a commit. These are
the rules that have actually been broken at some point, not a wish list: a
window that opens before the vintage, a price outside the listings it claims to
come from, a white wine whose lead grape is red.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cellar import (STATUS, appellations, drunk, held, load, qty, regions,
                    status, value, vintage)

REQUIRED = ("producer", "wine", "display", "short", "country", "region", "type",
            "grapes", "drink_from", "drink_to", "notes", "profile", "price",
            "ws_url", "vintage_note")
PROFILE = ("style", "tasting", "story", "serve", "pair")
TIERS = ("verified", "estimate", "unverified")
RATINGS = ("great", "very good", "good", "mixed", "poor", "n/a")
REDS = {"Cabernet Sauvignon", "Merlot", "Pinot Noir", "Syrah", "Shiraz", "Sangiovese",
        "Cabernet Franc", "Petit Verdot", "Malbec", "Grenache"}
WHITES = {"Chardonnay", "Sauvignon Blanc", "Sémillon", "Chenin Blanc", "Riesling",
          "Macabeo", "Xarel·lo", "Parellada", "Muscadelle"}


def main():
    d = load()
    B = sorted(d["wines"], key=lambda b: b["id"])
    bad = []

    def need(b, ok, msg):
        if not ok:
            bad.append(f'{b["id"]:>2} {b["display"][:38]:<38} {msg}')

    for b in B:
        for k in REQUIRED:
            need(b, b.get(k), f"missing {k}")
        for k in PROFILE:
            need(b, b["profile"].get(k), f"missing profile.{k}")

        v, lo, hi = b.get("vintage"), b["drink_from"], b["drink_to"]
        need(b, lo < hi, f"window not ascending: {lo}-{hi}")
        need(b, v or b.get("vintage_label"), "no vintage and no vintage_label")
        if v:
            need(b, lo >= v, f"window opens {lo}, before the {v} vintage")
            need(b, lo - v <= 20, f"window opens {lo - v} years after the vintage")
        need(b, b.get("format_ml", 750) in (375, 750, 1500),
             f'format {b.get("format_ml")} is not a size we stock')
        need(b, qty(b) >= 0, f"holding went negative: {qty(b)}")
        if b.get("abv"):
            need(b, 5 < b["abv"] < 20, f'abv {b["abv"]}')

        g0 = b["grapes"][0] if b["grapes"] else None
        if b["type"] == "red":
            need(b, g0 not in WHITES, f"type red, lead grape {g0}")
        if b["type"] == "white" and "Blanc de Noirs" not in b["display"]:
            need(b, g0 not in REDS, f"type white, lead grape {g0}")

        p = b["price"]
        need(b, p["confidence"] in TIERS, f'confidence {p["confidence"]}')
        need(b, p["avg_usd"] > 0, "price is not positive")
        need(b, p.get("source"), "price has no stated source")
        e = p.get("est")
        if e:
            need(b, e["low"] <= p["avg_usd"] <= e["high"],
                 f'price {p["avg_usd"]} outside its listings {e["low"]}-{e["high"]}')
            need(b, e["n_listings"] >= 2, f'"estimate" from {e["n_listings"]} listing')

        vn = b["vintage_note"]
        need(b, vn.get("rating") in RATINGS, f'rating {vn.get("rating")}')
        need(b, (vn.get("rating") == "n/a") == (not v),
             f'rating n/a does not match vintage {v}')
        need(b, len(vn.get("text", "")) > 40, "vintage note too short to say anything")

        need(b, b["ws_url"].startswith("https://www.wine-searcher.com/find/"),
             "ws_url is not a Wine-Searcher search")
        m = re.search(r"/(\d{4})$", b["ws_url"])
        if v:
            need(b, m and int(m.group(1)) == v,
                 f'ws_url vintage {m.group(1) if m else "missing"} != {v}')

    seen = {}
    for b in B:
        k = (b["display"], b.get("vintage"))
        need(b, k not in seen, f"duplicate of #{seen.get(k)}")
        seen[k] = b["id"]

    # Every bottle must land in a region and an appellation the dashboard can name.
    groups, order = regions(B)
    aps = appellations(B)
    for b in B:
        need(b, b["_rg"] in groups and b["_ap"] in aps, "does not map to a region")
        need(b, status(b) in dict((k, t) for k, t, _ in STATUS), "status does not resolve")

    # The event log is the only source of a count, so it carries its own rules.
    ids = {b["id"] for b in B}
    for i, e in enumerate(d.get("events", [])):
        where = f"events[{i}]"
        if e.get("wine") not in ids:
            bad.append(f'{where:<44} references no wine: {e.get("wine")}')
        if e.get("type") not in ("in", "out"):
            bad.append(f'{where:<44} type {e.get("type")!r}')
        if not isinstance(e.get("qty"), int) or e["qty"] < 1:
            bad.append(f'{where:<44} qty {e.get("qty")!r}')
        # An opening balance has no date on purpose; anything else must carry one.
        if e.get("type") == "out" and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", e.get("date") or ""):
            bad.append(f'{where:<44} out-event date is not YYYY-MM-DD')
        if e.get("date") is None and e.get("type") != "in":
            bad.append(f'{where:<44} only an opening balance may have a null date')

    total = sum(qty(x) for x in held(B))
    worth = sum(value(x) for x in held(B))
    if bad:
        print(f"{len(bad)} problem(s):\n")
        print("\n".join(bad))
        return 1
    gone = len(B) - len(held(B))
    finished = f", {gone} finished" if gone else ""
    print(f"ok — {len(held(B))} labels{finished}, {total} bottles, ${worth:,.0f}, "
          f"{len(order)} regions, {len(aps)} appellations, "
          f"{len(d.get('events', []))} events, {len(drunk(d))} drunk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
