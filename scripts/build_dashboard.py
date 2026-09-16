#!/usr/bin/env python3
"""data/cellar.json -> web/dashboard.html

A plain static document: white ground, Aptos where the reader has it, no
client-side script and no embedded font.

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
from cellar import (CLS, LABEL, NOW, ROOT, STATUS, appellations, load, qty,
                    regions, status, usd, value, vintage)

BASIS = {"verified": "confirmed", "estimate": "estimated", "unverified": "unverified"}

# key, chip label, sort key. The first is the default: rows are emitted in that
# order, so it costs no rules and is what the page shows before anything is
# clicked. Non-vintage bottles sort to the end rather than to 0.
SORTS = [
    ("vintage", "Vintage", lambda b, g: (b.get("vintage") or 9999, b["id"])),
    ("value", "Value", lambda b, g: (value(b), b["id"])),
    ("window", "Window", lambda b, g: (b["drink_to"], b["drink_from"], b["id"])),
    ("region", "Region", lambda b, g: (g[b["_rg"]]["name"], b["display"].lower())),
    ("name", "Name", lambda b, g: (b["display"].lower(), b.get("vintage") or 0)),
    ("catalogued", "Catalogued", lambda b, g: b["id"]),
]
DEFAULT_SORT = SORTS[0][0]


def esc(x):
    return _html.escape(str(x), quote=True)


CSS = """
/* Aptos is Microsoft's, proprietary, and not licensed for self-hosting as a
   webfont — and it is not on Google Fonts, the only external font host the
   artifact CSP admits. So it is asked for locally: anyone with Microsoft 365,
   Office or Windows 11 has it installed and sees it, and everyone else lands on
   the nearest humanist sans their system already has. Nothing is embedded. */

/* Committed to light. The cellar list is a paper document and the owner asked
   for a white ground; the neutrals carry a slight warm bias so they read as
   chosen rather than inherited. Red and green are the only hues, and they mean
   status — nothing decorative gets to use them. */
:root{
  color-scheme:light;
  --bg:#fff;
  --ink:#15130f;
  --ink-2:#6d675d;
  --ink-3:#9b958c;
  --rule:#e7e4de;
  --rule-2:#f1efea;
  --wash:#faf9f7;
  --urgent:#a8321f;
  --peak:#2d6a4a;
  --cols:15px 52px minmax(0,2.3fr) minmax(0,1.55fr) 78px 96px 70px 78px;
}
*{box-sizing:border-box}
html,body{background:var(--bg);color:var(--ink)}
body{font-family:Aptos,"Segoe UI Variable Text","Segoe UI",system-ui,
    -apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif;
  font-size:15px;font-weight:400;line-height:1.6;margin:0;
  padding-block:30px 80px;padding-inline:20px;
  max-width:940px;margin-inline:auto;-webkit-text-size-adjust:100%;
  counter-reset:bb 0 ll 0;
  font-variant-numeric:tabular-nums}
p{margin:0}
a{color:inherit;text-decoration:underline;text-decoration-color:var(--ink-3);
  text-underline-offset:2px}
a:hover{text-decoration-color:var(--ink)}
:focus-visible{outline:2px solid var(--ink);outline-offset:3px;border-radius:1px}
.sr{position:absolute;width:1px;height:1px;clip-path:inset(50%);overflow:hidden}

/* Masthead */
.top{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 14px;
  padding-bottom:16px;border-bottom:1px solid var(--ink)}
h1{font-size:21px;font-weight:700;letter-spacing:-.012em;margin:0;text-wrap:balance}
.meta{color:var(--ink-2);font-size:12.5px;line-height:1.5}

/* Section labels do the work the old black rules were doing. */
.sec{display:block;font-size:11px;font-weight:600;letter-spacing:.1em;
  text-transform:uppercase;color:var(--ink-3);margin:30px 0 10px}

/* Summary — figures first, names second. */
.sum{display:flex;flex-wrap:wrap;gap:6px 26px;align-items:baseline}
.fig{display:inline-flex;align-items:baseline;gap:6px;font-size:13px;color:var(--ink-2)}
.fig b{font-size:20px;font-weight:700;letter-spacing:-.01em;color:inherit}
.s-urgent,.s-post{color:var(--urgent)}
.s-peak{color:var(--peak)}
.s-now{color:var(--ink)}
.s-hold{color:var(--ink-3)}
.prices{color:var(--ink-2);font-size:12.5px;margin-top:9px}

/* Controls. One label gutter so every row starts on the same line. */
.f{position:absolute;width:1px;height:1px;margin:-1px;padding:0;border:0;
  clip-path:inset(50%);overflow:hidden;white-space:nowrap}
.nav{display:grid;grid-template-columns:58px minmax(0,1fr);gap:0 14px;
  align-items:baseline;margin-bottom:7px}
.nav .lbl{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:var(--ink-3);padding-top:1px}
.opts{display:flex;flex-wrap:wrap;gap:2px 15px}
.opts label{font-size:13.5px;cursor:pointer;color:var(--ink-2);
  text-decoration:underline;text-decoration-color:var(--rule);text-underline-offset:3px;
  white-space:nowrap}
.opts label:hover{color:var(--ink);text-decoration-color:var(--ink-3)}
.opts label .n{font-size:12px;color:var(--ink-3)}
.apnav{display:none}
.apnav .sub{display:none}
.dirsep{width:1px;align-self:stretch;background:var(--rule);margin:2px 1px}

/* Inventory. A flex column, so a row's sort position is one `order` and the
   direction is one axis flip. */
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch}
.tbl{display:flex;flex-direction:column;min-width:770px}
.hd,.row{display:grid;grid-template-columns:var(--cols);gap:0 10px;align-items:baseline}
.hd{order:0;font-size:10.5px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;
  color:var(--ink-3);padding:0 2px 7px;border-bottom:1px solid var(--ink)}
.w{border-bottom:1px solid var(--rule-2)}
.row{font-size:13.5px;padding:9px 2px;cursor:pointer;list-style:none;
  color:var(--ink-2);transition:background .1s}
.row::-webkit-details-marker{display:none}
.w:hover>.row{background:var(--wash)}
.w[open]{background:var(--wash);border-bottom-color:var(--rule)}
.w[open]>.row{background:none}
.num{text-align:right;white-space:nowrap}
.yr{font-weight:700;font-size:14.5px;color:var(--ink);white-space:nowrap;
  letter-spacing:-.01em}
.nm{color:var(--ink);font-weight:500}
.w[open] .nm{font-weight:600}
/* Bottle qualifiers, set rather than boxed. Quantity is the one being scanned
   for, so it takes ink and weight; format is a footnote on the name. */
.qty{font-weight:700;color:var(--ink);white-space:nowrap;letter-spacing:.01em}
.fmt{color:var(--ink-3);font-weight:400;white-space:nowrap}
.mult{display:block;color:var(--ink-3);font-size:11.5px;margin-top:2px}
.st{white-space:nowrap;font-weight:500}
.car{color:var(--ink-3);font-size:10px;line-height:2;transition:transform .14s ease}
.w[open] .car{transform:rotate(90deg);color:var(--ink)}

/* How far through its life this bottle is. The one thing on the page that is
   about wine rather than about rows. */
.wb{display:block;height:2px;margin-top:4px;background:var(--rule);border-radius:2px}
.wb::before{content:"";display:block;height:100%;width:var(--p);
  background:currentColor;opacity:.55;border-radius:2px}

/* The note, opened in place. */
.body{padding:2px 2px 20px 44px}
.body dl{display:grid;grid-template-columns:84px minmax(0,1fr);gap:9px 20px;
  align-items:baseline;margin:0;max-width:700px}
.body dt{font-size:10.5px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;
  color:var(--ink-3);text-align:right;line-height:1.9}
.body dd{margin:0;font-size:14px;line-height:1.65}
.body dd.lead{font-size:15px}
/* Vintage verdict. Weight carries the scale; the two hues already mean status
   elsewhere, so only the extremes borrow them. */
.vr{font-weight:700}
.vr-great{color:var(--peak)}
.vr-very-good,.vr-good{color:var(--ink)}
.vr-mixed{color:var(--ink-2)}
.vr-poor{color:var(--urgent)}
.body .q{color:var(--ink-2);font-size:13px}

.readout{color:var(--ink-3);font-size:12px;margin-top:12px}
.readout .cb::before{content:counter(bb)}
.readout .cl::before{content:counter(ll)}
.empty{display:none;color:var(--ink-2);margin-top:20px}

/* Flags and method notes. */
.drunk{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:5px;
  font-size:13.5px}
.drunk li{display:grid;grid-template-columns:96px minmax(0,1fr);gap:0 10px}
.drunk .dt{color:var(--ink-3);font-size:12.5px}
.flags{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:14px}
.flags b{font-weight:600}
.flags p{color:var(--ink-2);font-size:13.5px;margin-top:2px;max-width:700px}
.method{margin-top:34px;padding-top:16px;border-top:1px solid var(--rule);
  display:flex;flex-direction:column;gap:11px}
.method p{color:var(--ink-3);font-size:12px;line-height:1.6;max-width:760px}

@media (max-width:760px){
  :root{--cols:15px 48px minmax(0,1fr) 76px 64px}
  body{padding-inline:16px}
  .tbl{min-width:0}
  .c-region,.c-window,.c-basis{display:none}
  .nav{grid-template-columns:1fr;gap:1px}
  .body{padding-left:18px}
  .body dl{grid-template-columns:minmax(0,1fr);gap:1px}
  .body dt{text-align:left;margin-top:11px;line-height:1.6}
}

@media (prefers-reduced-motion:reduce){*{transition:none!important}}

@media print{
  .tbl{display:block;min-width:0}
  .nav,.readout,.car{display:none}
  .w{break-inside:avoid;background:none}
}
"""


def render(d):
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
        if key == DEFAULT_SORT:
            continue                                    # already the document order
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
    everything = RV + SV + [(f"f-so-{k}", None) for k, _, _ in SORTS]
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
    A("<style>" + CSS + "\n" + "\n".join(rules) + "</style>")

    A('<div class="top"><h1>CellarOS</h1>'
      f'<p class="meta">{total} bottles · {len(B)} labels · est. {usd(worth)} · '
      f'vintages {min(yrs)}–{max(yrs)} · cellar {d["storage"]["temp_c"]}°C · '
      f'as of {d["updated"]}</p></div>')

    tiers = {}
    for b in B:
        tiers[b["price"]["confidence"]] = tiers.get(b["price"]["confidence"], 0) + 1
    A('<h2 class="sec">Summary</h2>')
    A('<div class="sum">' + "".join(
        f'<span class="fig {CLS[k]}"><b>{st_n[k]}</b> {t}</span>'
        for k, t, _ in STATUS if st_n[k]) + "</div>")
    A(f'<p class="prices">Prices — {tiers.get("verified",0)} confirmed · '
      f'{tiers.get("estimate",0)} estimated · {tiers.get("unverified",0)} unverified.</p>')

    # Region group first, then status, so the sibling selectors can pair them.
    A('<input class="f" type="radio" name="rg" id="f-rg-all" checked>')
    for s_ in order:
        A(f'<input class="f" type="radio" name="rg" id="f-rg-{s_}">')
    for s_ in multi:
        for a in subs[s_]:
            A(f'<input class="f" type="radio" name="rg" id="f-ap-{a["slug"]}">')
    A('<input class="f" type="radio" name="st" id="f-st-all" checked>')
    for k in st_order:
        A(f'<input class="f" type="radio" name="st" id="f-st-{k}">')
    for k, _, _ in SORTS:
        ck = " checked" if k == DEFAULT_SORT else ""
        A(f'<input class="f" type="radio" name="so" id="f-so-{k}"{ck}>')
    A('<input class="f" type="radio" name="dir" id="f-dir-asc" checked>')
    A('<input class="f" type="radio" name="dir" id="f-dir-desc">')

    A('<h2 class="sec">Browse</h2>')

    chips = ['<label for="f-rg-all">All</label>']
    chips += [f'<label for="f-rg-{s_}">{esc(groups[s_]["name"])} '
              f'<span class="n">{groups[s_]["n"]}</span></label>' for s_ in order]
    A('<div class="nav"><span class="lbl">Region</span>'
      '<span class="opts">' + "\n".join(chips) + "</span></div>")

    sub_chips = [f'<label class="sub sub-{s_}" for="f-ap-{a["slug"]}">'
                 f'{esc(a["name"])} <span class="n">{a["n"]}</span></label>'
                 for s_ in multi for a in subs[s_]]
    A('<div class="nav apnav"><span class="lbl">Within</span>'
      '<span class="opts">' + "\n".join(sub_chips) + "</span></div>")

    st_chips = ['<label for="f-st-all">Any</label>']
    st_chips += [f'<label for="f-st-{k}"><span class="{CLS[k]}">{LABEL[k]}</span> '
                 f'<span class="n">{st_n[k]}</span></label>' for k in st_order]
    A('<div class="nav"><span class="lbl">Status</span>'
      '<span class="opts">' + "\n".join(st_chips) + "</span></div>")

    so_chips = [f'<label for="f-so-{k}">{t}</label>' for k, t, _ in SORTS]
    so_chips += ['<span class="dirsep" aria-hidden="true"></span>',
                 '<label for="f-dir-asc">↑<span class="sr"> Ascending</span></label>',
                 '<label for="f-dir-desc">↓<span class="sr"> Descending</span></label>']
    A('<div class="nav"><span class="lbl">Sort</span>'
      '<span class="opts">' + "\n".join(so_chips) + "</span></div>")

    A('<div class="main">')
    A('<h2 class="sec">Inventory</h2><div class="tw"><div class="tbl">')
    A('<div class="hd" aria-hidden="true"><span></span>'
      '<span>Vintage</span><span>Wine</span><span class="c-region">Region</span>'
      '<span>Status</span><span class="num c-window">Window</span>'
      '<span class="num">Value</span><span class="c-basis">Basis</span></div>')

    dom = sorted(B, key=lambda x: SORTS[0][2](x, groups))
    for b in dom:
        k = status(b)
        pf, pr = b["profile"], b["price"]
        lo, hi = b["drink_from"], b["drink_to"]
        through = min(max((NOW - lo) / max(hi - lo, 1), 0), 1)
        ml = b.get("format_ml", 750)
        fm = (f' <span class="fmt">{"1.5L" if ml == 1500 else f"{ml}ml"}</span>'
              if ml != 750 else "")
        qt = (f' <span class="qty">×{qty(b)}</span>' if qty(b) > 1 else "")
        each = value(b) / qty(b)
        mult = (f'<span class="mult">{qty(b)} × {usd(each)}</span>'
                if qty(b) > 1 else "")
        A(f'<details class="w w{b["id"]:02d} rg-{b["_rg"]} ap-{b["_ap"]} k-{k}" '
          f'style="counter-increment:bb {qty(b)} ll 1">')
        A(f'<summary class="row"><span class="car">▶</span>'
          f'<span class="yr">{vintage(b)}</span>'
          f'<span class="nm">{esc(b["display"])}{qt}{fm}</span>'
          f'<span class="c-region">{esc(b["region"])}</span>'
          f'<span class="st {CLS[k]}">{LABEL[k]}</span>'
          f'<span class="num c-window">{lo}–{hi}'
          f'<span class="wb {CLS[k]}" style="--p:{through:.0%}"></span></span>'
          f'<span class="num">{usd(value(b))}{mult}</span>'
          f'<span class="c-basis">{BASIS[pr["confidence"]]}</span></summary>')

        A('<div class="body"><dl>')
        A(f'<dt>Region</dt><dd class="lead">{esc(b["region"])} · {esc(b["country"])}</dd>')
        vn = b.get("vintage_note")
        if vn:
            r = vn["rating"]
            head = ("Non-vintage" if r == "n/a"
                    else f'{vintage(b)} <span class="vr vr-{r.replace(" ", "-")}">'
                         f'{r[0].upper() + r[1:]}</span>')
            A(f'<dt>Vintage</dt><dd>{head}<span class="q"> — {esc(vn["text"])}</span></dd>')
        A(f'<dt>Style</dt><dd class="lead">{esc(pf["style"])}</dd>')
        A(f'<dt>Tasting</dt><dd>{esc(pf["tasting"])}</dd>')
        A(f'<dt>Background</dt><dd>{esc(pf["story"])}</dd>')
        A(f'<dt>Serving</dt><dd>{esc(pf["serve"]["temp"])} · decant '
          f'{esc(pf["serve"]["decant"])} · {esc(pf["serve"]["glass"])} glass</dd>')
        A(f'<dt>Pairing</dt><dd>{esc(" · ".join(pf["pair"]))}</dd>')
        A(f'<dt>Window</dt><dd>{lo}–{hi} · <span class="{CLS[k]}">{LABEL[k]}</span>'
          f'<span class="q"> · {through:.0%} through</span></dd>')
        A(f'<dt>Note</dt><dd>{esc(b["notes"])}</dd>')
        e = pr.get("est")
        src = esc(pr.get("source", ""))
        if e:
            src += f' · {e["n_listings"]} listings {usd(e["low"])}–{usd(e["high"])}'
            if e.get("ws_snippet"):
                src += f' · WS snippet {usd(e["ws_snippet"])}'
        held = (f'{qty(b)} bottles, {usd(value(b))} in total · '
                if qty(b) > 1 else "")
        A(f'<dt>Price</dt><dd>{usd(pr["avg_usd"])} per 750ml · {held}'
          f'<span class="q">{BASIS[pr["confidence"]]} — {src}</span></dd>')
        meta = [f'#{b["id"]:02d}', esc(b["producer"])]
        if b.get("classification"):
            meta.append(esc(b["classification"]))
        if b.get("grapes"):
            meta.append(esc(" · ".join(b["grapes"])))
        if b.get("abv"):
            meta.append(f'{b["abv"]}%')
        meta.append(f"{ml}ml")
        A(f'<dt>Bottle</dt><dd class="q">{" · ".join(meta)} · '
          f'<a href="{esc(b["ws_url"])}" target="_blank" rel="noopener">Wine-Searcher</a></dd>')
        A("</dl></div></details>")

    A("</div></div>")
    A(f'<p class="readout">Showing <span class="cb"></span> of {total} bottles · '
      f'<span class="cl"></span> of {len(B)} labels</p>')
    A("</div>")
    A('<p class="empty">Nothing in the cellar matches that combination.</p>')

    byid = {b["id"]: b for b in B}
    if d.get("flags"):
        A('<h2 class="sec">Check</h2><ul class="flags">')
        for f in d["flags"]:
            fb = byid[f["id"]]
            A(f'<li><b>{esc(fb["display"])} {vintage(fb)} — '
              f'{esc(f["title"])}</b><p>{esc(f["text"])}</p></li>')
        A("</ul>")

    if d.get("drunk"):
        A('<h2 class="sec">Drunk</h2><ul class="drunk">')
        for x in sorted(d["drunk"], key=lambda x: x["date"], reverse=True):
            note = f'<span class="q"> — {esc(x["note"])}</span>' if x.get("note") else ""
            A(f'<li><span class="dt">{esc(x["date"])}</span>'
              f'<span><b>{esc(x.get("vintage") or "NV")}</b> {esc(x["display"])}'
              f'{note}</span></li>')
        A("</ul>")

    A('<div class="method">')
    A('<p>Status is derived from the drinking window, not stored by hand: past the '
      'window is post peak; inside its last quarter is urgent; not yet open is hold; a '
      'quarter of the way in, or five years past the opening, is peak; everything else '
      'is drink now. Urgency is relative to the window rather than a fixed countdown, '
      'because a year left on a Cava is a third of its life and a year left on a 1996 '
      'Napa Cabernet is four per cent of it. The bar under each window shows how far '
      'through that span the wine is today. Value scales a 750ml average price by the '
      'actual bottle format.</p>')
    A(f'<p>{esc(d["vintage_note"])}</p>')
    A(f'<p>{esc(d["price_note"])}</p>')
    A(f'<p>{esc(d["storage"]["note"])}</p>')
    A("</div>")
    return "\n".join(o)


# GitHub Pages serves a raw file, so the standalone copy needs the document
# scaffolding the Artifact host supplies for the other one.
PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<link rel="icon" href="data:image/svg+xml,\
%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E\
%3Ctext y='14' font-size='14'%3E%F0%9F%8D%B7%3C/text%3E%3C/svg%3E">
<style>html,body{margin:0}</style>
</head>
<body>
__BODY__
</body>
</html>
"""


def main():
    d = load()
    body = render(d)
    n = sum(qty(b) for b in d["bottles"])

    out = ROOT / "web" / "dashboard.html"        # Artifact: host wraps it
    out.write_text(body)
    page = ROOT / "docs" / "index.html"          # GitHub Pages: standalone
    page.parent.mkdir(exist_ok=True)
    page.write_text(PAGE.replace("__BODY__", body))
    (page.parent / ".nojekyll").write_text("")

    # Pages can be pointed at the branch root or at /docs. This makes the clean
    # URL land on the standalone document under either setting, and keeps anyone
    # who followed a repo path off web/dashboard.html, which is the Artifact body
    # and renders in quirks mode with no viewport when served raw.
    (ROOT / ".nojekyll").write_text("")
    (ROOT / "index.html").write_text(
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<title>CellarOS</title>\n'
        '<meta http-equiv="refresh" content="0; url=docs/index.html">\n'
        '<link rel="canonical" href="docs/index.html">\n</head>\n'
        '<body><p><a href="docs/index.html">CellarOS</a></p></body>\n</html>\n')

    for f in (out, page):
        print(f"{f.relative_to(ROOT)}: {n} bottles · {len(d['bottles'])} labels · "
              f"{f.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
