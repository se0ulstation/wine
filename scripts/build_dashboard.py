#!/usr/bin/env python3
"""data/cellar.json -> web/dashboard.html

A plain static document: white background, black text, links. No client-side
script. Region browsing is pure CSS (:target), so the page stays a document
that works with JavaScript off and prints as it reads.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cellar import (CLS, LABEL, PANELS, ROOT, STATUS, load, qty, regions,
                    status, usd, value, vintage)

BASIS = {"verified": "confirmed", "estimate": "estimated",
         "unverified": "unverified"}

# Rendering

import html as _html


def esc(x):
    return _html.escape(str(x), quote=True)


CSS = """
@font-face{font-family:Pretendard;font-weight:45 930;font-style:normal;font-display:swap;
  src:url(data:font/woff2;base64,__FONT__) format("woff2")}
:root{color-scheme:light}
html,body{background:#fff;color:#111}
body{font-family:Pretendard,-apple-system,BlinkMacSystemFont,system-ui,sans-serif;
  font-size:15px;line-height:1.65;margin:0;padding:28px 20px 72px;
  max-width:880px;margin-inline:auto;-webkit-text-size-adjust:100%}
h1{font-size:20px;margin:0 0 2px}
h2{font-size:15px;margin:34px 0 8px;padding-bottom:4px;border-bottom:1px solid #111}
p{margin:0 0 10px}
a{color:#0b57d0}
a:hover{color:#083a8c}
.meta{color:#666;font-size:13px;margin-bottom:0}
.q{color:#666}
.s-urgent,.s-post{color:#c2352b}
.s-peak{color:#1b7f4e}
.s-hold{color:#888}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:6px 0 0}
th,td{border-bottom:1px solid #e3e3e3;padding:6px 8px;text-align:left;vertical-align:top}
th{border-bottom:1px solid #111;font-weight:600;white-space:nowrap;color:#666;font-size:12.5px}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.st{white-space:nowrap}
td.yr{font-weight:700;font-size:14.5px;font-variant-numeric:tabular-nums;white-space:nowrap}
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch}
.tw table{min-width:700px}
ul{margin:0 0 10px;padding-left:20px}
li{margin-bottom:5px}
details{border-bottom:1px solid #e3e3e3;padding:7px 0}
summary{cursor:pointer;font-size:14px}
summary b{font-variant-numeric:tabular-nums;margin-right:2px}
.body{padding:8px 0 4px 16px}
.body dt{color:#666;font-size:12.5px;margin-top:8px}
.body dd{margin:0}
.body dd.place{font-size:15px}
dl{margin:0}
hr{border:0;border-top:1px solid #e3e3e3;margin:34px 0 12px}
.foot{color:#666;font-size:12.5px}
.rgt{display:block;height:0}
.map{display:flex;flex-wrap:wrap;gap:14px;margin:10px 0 4px}
.map figure{margin:0}
.map figcaption{color:#666;font-size:12px;margin-top:2px}
.map svg{display:block;border:1px solid #e3e3e3;background:#fff}
.map .grid{stroke:#eee;stroke-width:1}
.map .pin circle{fill:#111}
.map .pin text{fill:#111;font-size:10px;font-family:inherit}
.map .pin{cursor:pointer}
.map .pin:hover circle{fill:#0b57d0}
.map .pin:hover text{fill:#0b57d0}
.map .sb line{stroke:#111;stroke-width:1.5}
.map .sb text{fill:#666;font-size:9px;font-family:inherit}
.rgnav{font-size:13.5px;margin:8px 0 0;line-height:2}
.rgnav a{margin-right:14px;white-space:nowrap}
.rgnav a .n{color:#666;font-variant-numeric:tabular-nums}
"""


def project(pts, w, h, pad=24, foot=34, floor=2.5):
    """Equirectangular with a latitude correction; aspect preserved inside the panel.

    `floor` keeps a panel holding one or two pins from blowing them up to fill the
    frame, which would imply a precision the map does not have. `foot` reserves the
    strip the scale bar and the pin labels sit in.
    """
    mlat = sum(p[1] for p in pts) / len(pts)
    k = math.cos(math.radians(mlat))
    xs = [p[0] * k for p in pts]
    ys = [-p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    dx, dy = max(x1 - x0, floor), max(y1 - y0, floor)
    s = min((w - 2 * pad) / dx, (h - pad - foot) / dy)
    ox = (w - dx * s) / 2 - x0 * s
    oy = pad + (h - pad - foot - dy * s) / 2 - y0 * s
    return [(x * s + ox, y * s + oy) for x, y in zip(xs, ys)], s, k, ox, oy


def render_map(groups):
    """A small dot map, each panel at its own scale. Clicking a dot filters."""
    W, H = 214, 150
    out = ['<div class="map">']
    for pid, title in PANELS:
        pins = [g for g in groups.values() if g["panel"] == pid]
        if not pins:
            continue
        xy, s, k, ox, oy = project([(g["lon"], g["lat"]) for g in pins], W, H)
        out.append(f'<figure><svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
                   f'role="img" aria-label="{esc(title)}">')
        step = 10 if s * k < 4 else (5 if s * k < 12 else 1)
        lo = math.floor(min(g["lon"] for g in pins) / step) * step - step
        hi = math.ceil(max(g["lon"] for g in pins) / step) * step + step
        for t in range(int(lo), int(hi) + 1, step):
            x = t * k * s + ox
            if 0 < x < W:
                out.append(f'<line class="grid" x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{H}"/>')
        la = math.floor(min(g["lat"] for g in pins) / step) * step - step
        lb = math.ceil(max(g["lat"] for g in pins) / step) * step + step
        for t in range(int(la), int(lb) + 1, step):
            y = -t * s + oy
            if 0 < y < H:
                out.append(f'<line class="grid" x1="0" y1="{y:.1f}" x2="{W}" y2="{y:.1f}"/>')
        placed = []
        for g, (x, y) in zip(pins, xy):
            r = 2.6 + math.sqrt(g["n"]) * 1.3
            txt = f'{g["name"]} {g["n"]}'
            tw = len(txt) * 5.4
            # Try below, above, right, left — first position that clears the pins
            # already labelled and stays inside the frame.
            spots = [(x, y + r + 11, "middle", x - tw / 2),
                     (x, y - r - 5, "middle", x - tw / 2),
                     (x + r + 5, y + 3.5, "start", x + r + 5),
                     (x - r - 5, y + 3.5, "end", x - r - 5 - tw)]
            tx, ty, anchor, bx = spots[0]
            for cx, cy, ca, cbx in spots:
                box = (cbx, cy - 9, cbx + tw, cy + 2)
                if box[0] < 2 or box[2] > W - 2 or box[1] < 2 or box[3] > H - 13:
                    continue
                if any(box[0] < q[2] and q[0] < box[2] and box[1] < q[3] and q[1] < box[3]
                       for q in placed):
                    continue
                tx, ty, anchor, bx = cx, cy, ca, cbx
                break
            placed.append((bx, ty - 9, bx + tw, ty + 2))
            out.append(f'<a class="pin rg-{g["slug"]}" href="#rg-{g["slug"]}">'
                       f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" stroke="#fff" stroke-width="1.5"/>'
                       f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anchor}">'
                       f'{esc(txt)}</text></a>')
        # Every panel has its own scale, so each says what its own distances mean.
        for km in (2000, 1000, 500, 200, 100, 50, 20):
            px = km / 111.32 * s
            if px <= W * 0.36:
                break
        out.append(f'<g class="sb"><line x1="9" y1="{H-9}" x2="{9+px:.1f}" y2="{H-9}"/>'
                   f'<text x="{9+px+5:.1f}" y="{H-6}">{km} km</text></g>')
        out.append(f"</svg><figcaption>{esc(title)}</figcaption></figure>")
    out.append("</div>")
    return "\n".join(out)


def render(d, font):
    B = sorted(d["bottles"], key=lambda b: b["id"])
    total = sum(qty(b) for b in B)
    worth = sum(value(b) for b in B)
    yrs = [b["vintage"] for b in B if b.get("vintage")]

    groups, order = regions(B)

    rules = []
    for s in order:
        rules += [
            f'#rg-{s}:target ~ .tw tbody tr:not(.rg-{s}){{display:none}}',
            f'#rg-{s}:target ~ .note:not(.rg-{s}){{display:none}}',
            f'#rg-{s}:target ~ .rgnav a[href="#rg-{s}"]{{font-weight:700;color:#111}}',
            f'#rg-{s}:target ~ .map .pin:not(.rg-{s}){{opacity:.3}}',
        ]

    o = []
    A = o.append
    A("<title>CellarOS</title>")
    A("<style>" + CSS.replace("__FONT__", font) + "\n" + "\n".join(rules) + "</style>")
    A("<h1>CellarOS</h1>")
    A(f'<p class="meta">{total} bottles · {len(B)} labels · est. {usd(worth)} · '
      f'vintages {min(yrs)}–{max(yrs)} · cellar {d["storage"]["temp_c"]}°C · '
      f'as of {d["updated"]}</p>')

    # Summary
    cnt = {k: sum(qty(b) for b in B if status(b) == k) for k, _, _ in STATUS}
    tiers = {}
    for b in B:
        tiers[b["price"]["confidence"]] = tiers.get(b["price"]["confidence"], 0) + 1
    parts = [f'<span class="{CLS[k]}">{t} {cnt[k]}</span>' for k, t, _ in STATUS if cnt[k]]
    A("<h2>Summary</h2>")
    A(f'<p>{" · ".join(parts)}.<br>'
      f'<span class="q">Prices — {tiers.get("verified",0)} confirmed · '
      f'{tiers.get("estimate",0)} estimated · {tiers.get("unverified",0)} unverified.</span></p>')

    # Regions. The :target anchors must precede everything they filter.
    A('<i class="rgt" id="rg-all"></i>')
    for s in order:
        A(f'<i class="rgt" id="rg-{s}"></i>')
    A("<h2>Regions</h2>")
    A(render_map(groups))
    nav = ['<a href="#rg-all">All</a>']
    for s in order:
        g = groups[s]
        nav.append(f'<a href="#rg-{s}">{esc(g["name"])} <span class="n">{g["n"]}</span></a>')
    A('<p class="rgnav">' + "".join(nav) + "</p>")

    # Inventory
    A('<h2>Inventory</h2><div class="tw"><table><thead>')
    A('<tr><th class="num">#</th><th class="num">Vintage</th><th>Wine</th><th>Region</th>'
      '<th>Status</th><th class="num">Window</th><th class="num">Value</th><th>Basis</th></tr>')
    A("</thead><tbody>")
    for b in B:
        k = status(b)
        n = f' <span class="q">×{qty(b)}</span>' if qty(b) > 1 else ""
        fm = f' <span class="q">1.5L</span>' if b.get("format_ml") == 1500 else (
            f' <span class="q">375ml</span>' if b.get("format_ml") == 375 else "")
        A(f'<tr class="rg-{b["_rg"]}"><td class="num">{b["id"]:02d}</td>'
          f'<td class="yr">{vintage(b)}</td>'
          f'<td><a href="{esc(b["ws_url"])}" target="_blank" rel="noopener">'
          f'{esc(b["display"])}</a>{n}{fm}</td>'
          f'<td>{esc(b["region"])}</td>'
          f'<td class="st {CLS[k]}">{LABEL[k]}</td>'
          f'<td class="num">{b["drink_from"]}–{b["drink_to"]}</td>'
          f'<td class="num">{usd(value(b))}</td>'
          f'<td class="q">{BASIS[b["price"]["confidence"]]}</td></tr>')
    A("</tbody></table></div>")

    # Notes
    A("<h2>Notes</h2>")
    for b in B:
        pf, pr = b["profile"], b["price"]
        k = status(b)
        g = groups[b["_rg"]]
        A(f'<details class="note rg-{b["_rg"]}"><summary>'
          f'<b>{vintage(b)}</b> · {esc(b["display"])} '
          f'<span class="q">— {esc(g["name"])} · '
          f'<span class="{CLS[k]}">{LABEL[k]}</span> · {usd(pr["avg_usd"])}</span></summary>')
        A('<div class="body"><dl>')
        A(f'<dt>Region</dt><dd class="place">{esc(b["region"])} · {esc(b["country"])}</dd>')
        A(f'<dt>Style</dt><dd>{esc(pf["style"])}</dd>')
        A(f'<dt>Tasting</dt><dd>{esc(pf["tasting"])}</dd>')
        A(f'<dt>Background</dt><dd>{esc(pf["story"])}</dd>')
        A(f'<dt>Serving</dt><dd>{esc(pf["serve"]["temp"])} · decant {esc(pf["serve"]["decant"])} · '
          f'{esc(pf["serve"]["glass"])} glass</dd>')
        A(f'<dt>Pairing</dt><dd>{esc(" · ".join(pf["pair"]))}</dd>')
        A(f'<dt>Note</dt><dd>{esc(b["notes"])}</dd>')
        e = pr.get("est")
        src = esc(pr.get("source", ""))
        if e:
            src += f' · {e["n_listings"]} listings {usd(e["low"])}–{usd(e["high"])}'
            if e.get("ws_snippet"):
                src += f' · WS snippet {usd(e["ws_snippet"])}'
        A(f'<dt>Price basis</dt><dd>{BASIS[pr["confidence"]]} — {src}</dd>')
        meta = [esc(b["producer"])]
        if b.get("classification"):
            meta.append(esc(b["classification"]))
        if b.get("grapes"):
            meta.append(esc(" · ".join(b["grapes"])))
        if b.get("abv"):
            meta.append(f'{b["abv"]}%')
        meta.append(f'{b.get("format_ml", 750)}ml')
        A(f'<dt>Detail</dt><dd class="q">{" · ".join(meta)} · '
          f'<a href="{esc(b["ws_url"])}" target="_blank" rel="noopener">Wine-Searcher</a></dd>')
        A("</dl></div></details>")

    # Check
    byid = {b["id"]: b for b in B}
    if d.get("flags"):
        A("<h2>Check</h2><ul>")
        for f in d["flags"]:
            A(f'<li><b>{f["id"]:02d}. {esc(byid[f["id"]]["display"])} — {esc(f["title"])}</b><br>'
              f'<span class="q">{esc(f["text"])}</span></li>')
        A("</ul>")

    A("<hr>")
    A('<p class="foot">Status is derived from the drinking window, not stored by hand: '
      'past the window is post peak; two years or less left is urgent; not yet open is hold; '
      'a quarter of the way in — or five years past the opening — is peak; everything else is '
      'drink now. Value scales a 750ml average price by the actual bottle format.</p>')
    A(f'<p class="foot">{esc(d["price_note"])}</p>')
    A(f'<p class="foot">{esc(d["storage"]["note"])}</p>')
    return "\n".join(o)


def main():
    d = load()
    font = (ROOT / "web" / "font" / "pretendard.b64").read_text().strip()
    out = ROOT / "web" / "dashboard.html"
    out.write_text(render(d, font))
    n = sum(qty(b) for b in d["bottles"])
    print(f"{out.relative_to(ROOT)}: {n} bottles · {len(d['bottles'])} labels · "
          f"{out.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
