#!/usr/bin/env python3
"""Shared domain for the cellar generators.

Everything derived from the inventory lives here so the Markdown and the HTML
can never disagree. data/cellar.json is the only source of truth; nothing
written by hand is duplicated in either output.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOW = 2026

# key, label, css class
STATUS = [
    ("urgent", "Urgent", "s-urgent"),
    ("now", "Drink now", "s-now"),
    ("peak", "Peak", "s-peak"),
    ("hold", "Hold", "s-hold"),
    ("post", "Post peak", "s-post"),
]
LABEL = {k: t for k, t, _ in STATUS}
CLS = {k: c for k, _, c in STATUS}

# substring of the region field, display name, id slug, lon, lat, map panel
REGIONS = [
    ("Bordeaux", "Bordeaux", "bordeaux", -0.58, 44.84, "eu"),
    ("Burgundy", "Burgundy", "burgundy", 4.83, 47.05, "eu"),
    ("Champagne", "Champagne", "champagne", 4.03, 49.05, "eu"),
    ("Loire", "Loire", "loire", 0.90, 47.35, "eu"),
    ("Anjou", "Loire", "loire", 0.90, 47.35, "eu"),
    ("Toscana", "Tuscany", "tuscany", 10.60, 43.20, "eu"),
    ("Bolgheri", "Tuscany", "tuscany", 10.60, 43.20, "eu"),
    ("Penedès", "Penedès", "penedes", 1.70, 41.45, "eu"),
    ("Napa Valley", "Napa Valley", "napa", -122.33, 38.51, "ca"),
    ("Paso Robles", "Paso Robles", "paso", -120.69, 35.63, "ca"),
    ("Coonawarra", "Australia", "australia", 140.83, -37.29, "oz"),
    ("Margaret River", "Australia", "australia", 140.83, -37.29, "oz"),
    ("Marlborough", "Marlborough", "marlborough", 173.86, -41.52, "oz"),
]
PANELS = [("eu", "Western Europe"), ("ca", "California"), ("oz", "Australia & New Zealand")]


def load():
    return json.loads((ROOT / "data" / "cellar.json").read_text())


def qty(b):
    return b.get("qty", 1)


def value(b):
    """avg_usd is a 750ml price. Scale it by the format actually owned."""
    return b["price"]["avg_usd"] * (b.get("format_ml", 750) / 750) * qty(b)


def usd(n):
    return "$" + format(round(n), ",")


def vintage(b):
    return b.get("vintage") or b.get("vintage_label") or "NV"


def status(b):
    """Derived from the drinking window, so it stays true as years pass."""
    lo, hi = b["drink_from"], b["drink_to"]
    span = max(hi - lo, 1)
    left = hi - NOW
    if left < 0:
        return "post"
    # Urgent is relative to the window, not an absolute countdown: two years left
    # on a Bordeaux is the end of the road, two years left on a Cava is half of it.
    if left <= 1 or (left <= 2 and left / span <= 0.3):
        return "urgent"
    if NOW < lo:
        return "hold"
    if (NOW - lo) / span >= 0.25 or NOW - lo >= 5:
        return "peak"
    return "now"


def region_of(b):
    """(display name, slug, lon, lat, panel) — falls back to the trailing part."""
    for key, name, slug, lon, lat, panel in REGIONS:
        if key in b["region"]:
            return name, slug, lon, lat, panel
    tail = b["region"].split(",")[-1].strip()
    slug = re.sub(r"[^a-z0-9]+", "-", tail.lower()).strip("-") or "other"
    return tail, slug, None, None, None


def regions(bottles):
    """slug -> {name, slug, n, v, lon, lat, panel}, sorted by bottle count."""
    out = {}
    for b in bottles:
        name, slug, lon, lat, panel = region_of(b)
        g = out.setdefault(slug, {"name": name, "slug": slug, "n": 0, "v": 0,
                                  "lon": lon, "lat": lat, "panel": panel})
        g["n"] += qty(b)
        g["v"] += value(b)
        b["_rg"] = slug
    return out, sorted(out, key=lambda s: (-out[s]["n"], out[s]["name"]))
