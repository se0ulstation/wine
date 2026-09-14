#!/usr/bin/env python3
"""data/cellar.json -> web/dashboard.html

A plain static document: white background, black text, links. No client-side
script.

The inventory is one list of disclosure widgets whose summaries share a grid
template, so it reads as a table but every row opens onto its own note. Filter,
sort and direction are hidden radio inputs that sibling selectors read: region
and status compose as two independent dimensions, sort is a flex `order` per
row, direction is one `flex-direction` flip, and the counts are live CSS
counters that skip whatever a filter has hidden. Works with JavaScript off.
"""
import html as _html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cellar import (CLS, LABEL, ROOT, STATUS, appellations, load, qty, regions,
                    status, usd, value, vintage)

BASIS = {"verified": "confirmed", "estimate": "estimated", "unverified": "unverified"}

# key, chip label, sort key. Cellar order needs no rules — it is document order.
SORTS = [
    ("vintage", "Vintage", lambda b, g: (b.get("vintage") or 9999, b["id"])),
    ("value", "Value", lambda b, g: (value(b), b["id"])),
    ("window", "Window", lambda b, g: (b["drink_to"], b["drink_from"], b["id"])),
    ("region", "Region", lambda b, g: (g[b["_rg"]]["name"], b["display"].lower())),
    ("name", "Name", lambda b, g: (b["display"].lower(), b.get("vintage") or 0)),
]


def esc(x):
    return _html.escape(str(x), quote=True)


CSS = """
@font-face{font-family:Pretendard;font-weight:45 930;font-style:normal;font-display:swap;
  src:url(data:font/woff2;base64,__FONT__) format("woff2")}
:root{color-scheme:light;
  --cols:14px 28px 54px minmax(0,2.1fr) minmax(0,1.55fr) 84px 94px 70px 80px}
html,body{background:#fff;color:#111}
body{font-family:Pretendard,-apple-system,BlinkMacSystemFont,system-ui,sans-serif;
  font-size:15px;line-height:1.65;margin:0;padding:28px 20px 72px;
  max-width:920px;margin-inline:auto;-webkit-text-size-adjust:100%;
  counter-reset:bb 0 ll 0}
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

/* The inventory. A flex column so a row's sort position is one `order`, and a
   flip of the axis reverses every row at once. */
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch}
.tbl{display:flex;flex-direction:column;min-width:760px;margin-top:6px}
.hd,.row{display:grid;grid-template-columns:var(--cols);gap:0 8px;align-items:start}
.hd{order:0;color:#666;font-size:12.5px;font-weight:600;
  border-bottom:1px solid #111;padding:0 2px 4px}
.w{border-bottom:1px solid #e3e3e3}
.row{font-size:13.5px;padding:6px 2px;cursor:pointer;list-style:none}
.row::-webkit-details-marker{display:none}
.w:hover .row{background:#fafafa}
.row .num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.row .yr{font-weight:700;font-size:14.5px;font-variant-numeric:tabular-nums;
  white-space:nowrap}
.row .nm{color:#111}
.w[open] .row .nm{font-weight:600}
.row .st{white-space:nowrap}
.car{color:#888;transition:transform .12s;line-height:1.5}
.w[open] .car{transform:rotate(90deg)}
.body{padding:4px 2px 14px 42px;font-size:14px;max-width:660px}
.body dt{color:#666;font-size:12.5px;margin-top:8px}
.body dd{margin:0}
.body dd.place{font-size:15px}
dl{margin:0}
ul{margin:0 0 10px;padding-left:20px}
li{margin-bottom:5px}
hr{border:0;border-top:1px solid #e3e3e3;margin:34px 0 12px}
.foot{color:#666;font-size:12.5px}

/* Filter, sort and direction state. Hidden radios that sibling selectors read,
   kept visually hidden rather than display:none so they stay keyboard reachable. */
.f{position:absolute;width:1px;height:1px;margin:-1px;padding:0;border:0;
  clip-path:inset(50%);overflow:hidden;white-space:nowrap}
.nav{font-size:13.5px;line-height:2.1;margin:6px 0 0}
.nav .lbl{color:#666;font-size:12.5px;font-weight:600;margin-right:8px}
.nav label{margin-right:14px;white-space:nowrap;cursor:pointer;color:#0b57d0;
  text-decoration:underline;text-underline-offset:2px}
.nav label:hover{color:#083a8c}
.nav label .n{color:#666;font-variant-numeric:tabular-nums}
.apnav{display:none;padding-left:14px}
.apnav .sub{display:none}
.readout{color:#666;font-size:12.5px;margin:10px 0 0}
.readout .cb::before{content:counter(bb)}
.readout .cl::before{content:counter(ll)}
.empty{display:none;color:#666;margin-top:16px}

/* Narrow: drop the columns that the open note repeats anyway, rather than
   making the page scroll sideways. */
@media (max-width:760px){
  :root{--cols:14px 26px 50px minmax(0,1fr) 82px 66px}
  .tbl{min-width:0}
  .c-region,.c-window,.c-basis{display:none}
  .body{padding-left:16px}
}

@media print{
  .tbl{display:block;min-width:0}
  .nav,.readout{display:none}
  .w{break-inside:avoid}
}
"""


def render(d, font):
    B = sorted(d["bottles"], key=lambda b: b["id"])
    total = sum(qty(b) for b in B)
    worth = sum(value(b) for b in B)
    yrs = [b["vintage"] for b in B if b.get("vintage")]
    groups, order = regions(B)
    aps = appellations(B)

    subs = {s: sorted([a for a in aps.values() if a["rg"] == s],
                      key=lambda a: (-a["n"], a["name"])) for s in order}
    multi = [s for s in order if len(subs[s]) > 1]

    st_n = {k: sum(qty(b) for b in B if status(b) == k) for k, _, _ in STATUS}
    st_order = [k for k, _, _ in STATUS if st_n[k]]

    RV = [("f-rg-all", lambda b: True)]
    RV += [(f"f-rg-{s}", (lambda s: lambda b: b["_rg"] == s)(s)) for s in order]
    RV += [(f"f-ap-{a['slug']}", (lambda k: lambda b: b["_ap"] == k)(a["slug"]))
           for s in multi for a in subs[s]]
    SV = [("f-st-all", lambda b: True)]
    SV += [(f"f-st-{k}", (lambda k: lambda b: status(b) == k)(k)) for k in st_order]

    rules = []
    for rid, _ in RV[1:]:
        rules.append(f'#{rid}:checked ~ .main .w:not(.{rid[2:]}){{display:none}}')
    for sid, _ in SV[1:]:
        rules.append(f'#{sid}:checked ~ .main .w:not(.k-{sid[len("f-st-"):]}){{display:none}}')

    # Sort: one `order` per row per key. Direction is a single axis flip, with the
    # header pushed to the far end so it stays on top either way.
    for key, _, fn in SORTS:
        for i, b in enumerate(sorted(B, key=lambda x: fn(x, groups)), start=1):
            rules.append(f'#f-so-{key}:checked ~ .main .w{b["id"]:02d}{{order:{i}}}')
    rules += ['#f-dir-desc:checked ~ .main .tbl{flex-direction:column-reverse}',
              '#f-dir-desc:checked ~ .main .hd{order:9999}']

    for s in multi:
        on = [f"#f-rg-{s}:checked"] + [f'#f-ap-{a["slug"]}:checked' for a in subs[s]]
        rules.append(", ".join(f"{x} ~ .apnav" for x in on) + "{display:block}")
        rules.append(", ".join(f"{x} ~ .apnav .sub-{s}" for x in on) + "{display:inline}")

    for rid, rp in RV:
        for sid, sp in SV:
            if any(rp(b) and sp(b) for b in B):
                continue
            rules += [f'#{rid}:checked ~ #{sid}:checked ~ .main{{display:none}}',
                      f'#{rid}:checked ~ #{sid}:checked ~ .empty{{display:block}}',
                      f'#{sid}:checked ~ .nav label[for="{rid}"]{{opacity:.32}}',
                      f'#{rid}:checked ~ .nav label[for="{sid}"]{{opacity:.32}}']

    # Last, so a chosen option beats a dim rule aimed at it.
    everything = RV + SV + [("f-so-cellar", None)] + [(f"f-so-{k}", None) for k, _, _ in SORTS]
    everything += [("f-dir-asc", None), ("f-dir-desc", None)]
    for vid, _ in everything:
        rules.append(f'#{vid}:checked ~ .nav label[for="{vid}"],'
                     f'#{vid}:checked ~ .nav label[for="{vid}"] span'
                     f'{{color:#111;font-weight:700;text-decoration:none;opacity:1}}')
        rules.append(f'#{vid}:focus-visible ~ .nav label[for="{vid}"]'
                     f'{{outline:2px solid #0b57d0;outline-offset:3px}}')

    o = []
    A = o.append
    A("<title>CellarOS</title>")
    A("<style>" + CSS.replace("__FONT__", font) + "\n" + "\n".join(rules) + "</style>")
    A("<h1>CellarOS</h1>")
    A(f'<p class="meta">{total} bottles · {len(B)} labels · est. {usd(worth)} · '
      f'vintages {min(yrs)}–{max(yrs)} · cellar {d["storage"]["temp_c"]}°C · '
      f'as of {d["updated"]}</p>')

    tiers = {}
    for b in B:
        tiers[b["price"]["confidence"]] = tiers.get(b["price"]["confidence"], 0) + 1
    A("<h2>Summary</h2>")
    A('<p>' + " · ".join(f'<span class="{CLS[k]}">{t} {st_n[k]}</span>'
                         for k, t, _ in STATUS if st_n[k]) + '.<br>'
      f'<span class="q">Prices — {tiers.get("verified",0)} confirmed · '
      f'{tiers.get("estimate",0)} estimated · {tiers.get("unverified",0)} unverified.</span></p>')

    # Region group first, then status, so the sibling selectors can pair them.
    A('<input class="f" type="radio" name="rg" id="f-rg-all" checked>')
    for s in order:
        A(f'<input class="f" type="radio" name="rg" id="f-rg-{s}">')
    for s in multi:
        for a in subs[s]:
            A(f'<input class="f" type="radio" name="rg" id="f-ap-{a["slug"]}">')
    A('<input class="f" type="radio" name="st" id="f-st-all" checked>')
    for k in st_order:
        A(f'<input class="f" type="radio" name="st" id="f-st-{k}">')
    A('<input class="f" type="radio" name="so" id="f-so-cellar" checked>')
    for k, _, _ in SORTS:
        A(f'<input class="f" type="radio" name="so" id="f-so-{k}">')
    A('<input class="f" type="radio" name="dir" id="f-dir-asc" checked>')
    A('<input class="f" type="radio" name="dir" id="f-dir-desc">')

    A("<h2>Browse</h2>")
    chips = ['<span class="lbl">Region</span>', '<label for="f-rg-all">All</label>']
    for s in order:
        chips.append(f'<label for="f-rg-{s}">{esc(groups[s]["name"])} '
                     f'<span class="n">{groups[s]["n"]}</span></label>')
    A('<p class="nav">' + "\n".join(chips) + "</p>")

    sub_chips = ['<span class="lbl">Within</span>']
    for s in multi:
        for a in subs[s]:
            sub_chips.append(f'<label class="sub sub-{s}" for="f-ap-{a["slug"]}">'
                             f'{esc(a["name"])} <span class="n">{a["n"]}</span></label>')
    A('<p class="nav apnav">' + "\n".join(sub_chips) + "</p>")

    st_chips = ['<span class="lbl">Status</span>', '<label for="f-st-all">Any</label>']
    for k in st_order:
        st_chips.append(f'<label for="f-st-{k}"><span class="{CLS[k]}">{LABEL[k]}</span> '
                        f'<span class="n">{st_n[k]}</span></label>')
    A('<p class="nav">' + "\n".join(st_chips) + "</p>")

    so_chips = ['<span class="lbl">Sort</span>', '<label for="f-so-cellar">Cellar #</label>']
    so_chips += [f'<label for="f-so-{k}">{t}</label>' for k, t, _ in SORTS]
    so_chips += ['<span class="lbl" style="margin-left:10px">Order</span>',
                 '<label for="f-dir-asc">↑ Ascending</label>',
                 '<label for="f-dir-desc">↓ Descending</label>']
    A('<p class="nav">' + "\n".join(so_chips) + "</p>")

    A('<div class="main">')
    A('<h2>Inventory</h2><div class="tw"><div class="tbl">')
    A('<div class="hd" aria-hidden="true"><span></span><span class="num">#</span>'
      '<span>Vintage</span><span>Wine</span><span class="c-region">Region</span>'
      '<span>Status</span><span class="num c-window">Window</span>'
      '<span class="num">Value</span><span class="c-basis">Basis</span></div>')

    for b in B:
        k = status(b)
        pf, pr = b["profile"], b["price"]
        n = f' <span class="q">×{qty(b)}</span>' if qty(b) > 1 else ""
        ml = b.get("format_ml", 750)
        fm = f' <span class="q">{"1.5L" if ml == 1500 else f"{ml}ml"}</span>' if ml != 750 else ""
        A(f'<details class="w w{b["id"]:02d} rg-{b["_rg"]} ap-{b["_ap"]} k-{k}" '
          f'style="counter-increment:bb {qty(b)} ll 1">')
        A(f'<summary class="row"><span class="car">▸</span>'
          f'<span class="num q">{b["id"]:02d}</span>'
          f'<span class="yr">{vintage(b)}</span>'
          f'<span class="nm">{esc(b["display"])}{n}{fm}</span>'
          f'<span class="c-region q">{esc(b["region"])}</span>'
          f'<span class="st {CLS[k]}">{LABEL[k]}</span>'
          f'<span class="num c-window q">{b["drink_from"]}–{b["drink_to"]}</span>'
          f'<span class="num">{usd(value(b))}</span>'
          f'<span class="c-basis q">{BASIS[pr["confidence"]]}</span></summary>')
        A('<div class="body"><dl>')
        A(f'<dt>Region</dt><dd class="place">{esc(b["region"])} · {esc(b["country"])}</dd>')
        A(f'<dt>Style</dt><dd>{esc(pf["style"])}</dd>')
        A(f'<dt>Tasting</dt><dd>{esc(pf["tasting"])}</dd>')
        A(f'<dt>Background</dt><dd>{esc(pf["story"])}</dd>')
        A(f'<dt>Serving</dt><dd>{esc(pf["serve"]["temp"])} · decant {esc(pf["serve"]["decant"])} · '
          f'{esc(pf["serve"]["glass"])} glass</dd>')
        A(f'<dt>Pairing</dt><dd>{esc(" · ".join(pf["pair"]))}</dd>')
        A(f'<dt>Drinking window</dt><dd>{b["drink_from"]}–{b["drink_to"]} · '
          f'<span class="{CLS[k]}">{LABEL[k]}</span></dd>')
        A(f'<dt>Note</dt><dd>{esc(b["notes"])}</dd>')
        e = pr.get("est")
        src = esc(pr.get("source", ""))
        if e:
            src += f' · {e["n_listings"]} listings {usd(e["low"])}–{usd(e["high"])}'
            if e.get("ws_snippet"):
                src += f' · WS snippet {usd(e["ws_snippet"])}'
        A(f'<dt>Price</dt><dd>{usd(pr["avg_usd"])} per 750ml · '
          f'{BASIS[pr["confidence"]]} — {src}</dd>')
        meta = [esc(b["producer"])]
        if b.get("classification"):
            meta.append(esc(b["classification"]))
        if b.get("grapes"):
            meta.append(esc(" · ".join(b["grapes"])))
        if b.get("abv"):
            meta.append(f'{b["abv"]}%')
        meta.append(f'{ml}ml')
        A(f'<dt>Detail</dt><dd class="q">{" · ".join(meta)} · '
          f'<a href="{esc(b["ws_url"])}" target="_blank" rel="noopener">Wine-Searcher</a></dd>')
        A("</dl></div></details>")

    A("</div></div>")
    A(f'<p class="readout">Showing <span class="cb"></span> of {total} bottles · '
      f'<span class="cl"></span> of {len(B)} labels</p>')
    A("</div>")
    A('<p class="empty">Nothing in the cellar matches that combination.</p>')

    byid = {b["id"]: b for b in B}
    if d.get("flags"):
        A("<h2>Check</h2><ul>")
        for f in d["flags"]:
            A(f'<li><b>{f["id"]:02d}. {esc(byid[f["id"]]["display"])} — {esc(f["title"])}</b><br>'
              f'<span class="q">{esc(f["text"])}</span></li>')
        A("</ul>")

    A("<hr>")
    A('<p class="foot">Status is derived from the drinking window, not stored by hand: '
      'past the window is post peak; inside its last quarter is urgent; not yet open is '
      'hold; a quarter of the way in, or five years past the opening, is peak; everything '
      'else is drink now. Urgency is relative to the window rather than a fixed countdown, '
      'because a year left on a Cava is a third of its life and a year left on a 1996 Napa '
      'Cabernet is four per cent of it. Value scales a 750ml average price by the actual '
      'bottle format.</p>')
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
