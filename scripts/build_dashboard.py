#!/usr/bin/env python3
"""data/cellar.json -> web/dashboard.html

A plain static document: white background, black text, links. No client-side
script. Filtering is hidden radio inputs plus sibling selectors, so region and
status are two independent dimensions that compose, the counts under the table
are live CSS counters, and a filter combination that holds nothing says so.
Everything still works with JavaScript off and prints as it reads.
"""
import html as _html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cellar import (CLS, LABEL, ROOT, STATUS, appellations, load, qty, regions,
                    status, usd, value, vintage)

BASIS = {"verified": "confirmed", "estimate": "estimated", "unverified": "unverified"}


def esc(x):
    return _html.escape(str(x), quote=True)


CSS = """
@font-face{font-family:Pretendard;font-weight:45 930;font-style:normal;font-display:swap;
  src:url(data:font/woff2;base64,__FONT__) format("woff2")}
:root{color-scheme:light}
html,body{background:#fff;color:#111}
body{font-family:Pretendard,-apple-system,BlinkMacSystemFont,system-ui,sans-serif;
  font-size:15px;line-height:1.65;margin:0;padding:28px 20px 72px;
  max-width:880px;margin-inline:auto;-webkit-text-size-adjust:100%;
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

/* Filter state. Kept in the page rather than in a script: hidden radios that
   sibling selectors read. Visually hidden, not display:none, so they stay
   reachable by keyboard. */
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
"""


def render(d, font):
    B = sorted(d["bottles"], key=lambda b: b["id"])
    total = sum(qty(b) for b in B)
    worth = sum(value(b) for b in B)
    yrs = [b["vintage"] for b in B if b.get("vintage")]
    groups, order = regions(B)
    aps = appellations(B)

    # A region only offers a second level when it actually splits.
    subs = {s: sorted([a for a in aps.values() if a["rg"] == s],
                      key=lambda a: (-a["n"], a["name"])) for s in order}
    multi = [s for s in order if len(subs[s]) > 1]

    st_n = {k: sum(qty(b) for b in B if status(b) == k) for k, _, _ in STATUS}
    st_order = [k for k, _, _ in STATUS if st_n[k]]

    # Every selectable value, as (input id, predicate) so counts and rules agree.
    RV = [("f-rg-all", lambda b: True)]
    RV += [(f"f-rg-{s}", (lambda s: lambda b: b["_rg"] == s)(s)) for s in order]
    RV += [(f"f-ap-{a['slug']}", (lambda k: lambda b: b["_ap"] == k)(a["slug"]))
           for s in multi for a in subs[s]]
    SV = [("f-st-all", lambda b: True)]
    SV += [(f"f-st-{k}", (lambda k: lambda b: status(b) == k)(k)) for k in st_order]

    rules = []
    for rid, pred in RV[1:]:
        cls = rid[2:]                                   # f-rg-napa -> rg-napa
        rules += [f'#{rid}:checked ~ .main tbody tr:not(.{cls}){{display:none}}',
                  f'#{rid}:checked ~ .main .note:not(.{cls}){{display:none}}']
    for sid, _ in SV[1:]:
        cls = "k-" + sid[len("f-st-"):]
        rules += [f'#{sid}:checked ~ .main tbody tr:not(.{cls}){{display:none}}',
                  f'#{sid}:checked ~ .main .note:not(.{cls}){{display:none}}']

    # Second level appears only once its parent is in play.
    for s in multi:
        on = [f"#f-rg-{s}:checked"] + [f'#f-ap-{a["slug"]}:checked' for a in subs[s]]
        rules.append(", ".join(f"{x} ~ .apnav" for x in on) + "{display:block}")
        rules.append(", ".join(f"{x} ~ .apnav .sub-{s}" for x in on) + "{display:inline}")

    # A combination holding nothing dims the option beforehand and says so after.
    for rid, rp in RV:
        for sid, sp in SV:
            if any(rp(b) and sp(b) for b in B):
                continue
            rules += [f'#{rid}:checked ~ #{sid}:checked ~ .main{{display:none}}',
                      f'#{rid}:checked ~ #{sid}:checked ~ .empty{{display:block}}',
                      f'#{sid}:checked ~ .nav label[for="{rid}"]{{opacity:.32}}',
                      f'#{rid}:checked ~ .nav label[for="{sid}"]{{opacity:.32}}']

    # Last, so the chosen option wins over a dim rule aimed at it — you can pick a
    # combination that holds nothing, and it still reads as the thing you picked.
    for vid, _ in RV + SV:
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

    # Filter inputs. Region group first, then status, so the sibling selectors
    # above can pair one with the other.
    A('<input class="f" type="radio" name="rg" id="f-rg-all" checked>')
    for s in order:
        A(f'<input class="f" type="radio" name="rg" id="f-rg-{s}">')
    for s in multi:
        for a in subs[s]:
            A(f'<input class="f" type="radio" name="rg" id="f-ap-{a["slug"]}">')
    A('<input class="f" type="radio" name="st" id="f-st-all" checked>')
    for k in st_order:
        A(f'<input class="f" type="radio" name="st" id="f-st-{k}">')

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

    A('<div class="main">')

    A('<h2>Inventory</h2><div class="tw"><table><thead>')
    A('<tr><th class="num">#</th><th class="num">Vintage</th><th>Wine</th><th>Region</th>'
      '<th>Status</th><th class="num">Window</th><th class="num">Value</th><th>Basis</th></tr>')
    A("</thead><tbody>")
    for b in B:
        k = status(b)
        n = f' <span class="q">×{qty(b)}</span>' if qty(b) > 1 else ""
        ml = b.get("format_ml", 750)
        fm = f' <span class="q">{"1.5L" if ml == 1500 else f"{ml}ml"}</span>' if ml != 750 else ""
        A(f'<tr class="rg-{b["_rg"]} ap-{b["_ap"]} k-{k}" '
          f'style="counter-increment:bb {qty(b)} ll 1">'
          f'<td class="num">{b["id"]:02d}</td>'
          f'<td class="yr">{vintage(b)}</td>'
          f'<td><a href="{esc(b["ws_url"])}" target="_blank" rel="noopener">'
          f'{esc(b["display"])}</a>{n}{fm}</td>'
          f'<td>{esc(b["region"])}</td>'
          f'<td class="st {CLS[k]}">{LABEL[k]}</td>'
          f'<td class="num">{b["drink_from"]}–{b["drink_to"]}</td>'
          f'<td class="num">{usd(value(b))}</td>'
          f'<td class="q">{BASIS[b["price"]["confidence"]]}</td></tr>')
    A("</tbody></table></div>")
    # Counters skip rows a filter has hidden, so this total is live.
    A(f'<p class="readout">Showing <span class="cb"></span> of {total} bottles · '
      f'<span class="cl"></span> of {len(B)} labels</p>')

    A("<h2>Notes</h2>")
    for b in B:
        pf, pr = b["profile"], b["price"]
        k = status(b)
        A(f'<details class="note rg-{b["_rg"]} ap-{b["_ap"]} k-{k}"><summary>'
          f'<b>{vintage(b)}</b> · {esc(b["display"])} '
          f'<span class="q">— {esc(aps[b["_ap"]]["name"])} · '
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
      'past the window is post peak; a year or less left — or two years that are the last '
      'third of the window — is urgent; not yet open is hold; a quarter of the way in, or '
      'five years past the opening, is peak; everything else is drink now. Value scales a '
      '750ml average price by the actual bottle format.</p>')
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
