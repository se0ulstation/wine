#!/usr/bin/env python3
"""web/dashboard.template.html + data/cellar.json → web/dashboard.html

인벤토리에서 파생되는 분석(인사이트·분위)은 원본 데이터에 저장하지 않고
빌드할 때마다 여기서 다시 계산한다. 병을 추가하면 문구의 숫자도 따라 바뀐다.
"""
import json
import statistics as stat
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOW = 2026


def qty(b):
    return b.get("qty", 1)


def value(b):
    return b["price"]["avg_usd"] * (0.5 if b.get("format_ml") == 375 else 1) * qty(b)


def usd(n):
    return "$" + format(round(n), ",")


def short(b):
    """신호 한 줄에 들어갈 짧은 표기."""
    s = b["display"]
    for junk in ("Château ", "Chateau ", " Cabernet Sauvignon", " Napa Valley",
                 " de Mouton Rothschild", " du Château Margaux", " Coteaux du Layon",
                 " Brut (Blanc de Noirs)", " (Fines Caillottes)", " Chassagne-Montrachet"):
        s = s.replace(junk, "")
    return s.strip() or b["display"]


def analyse(d):
    B = d["bottles"]
    total = sum(qty(b) for b in B)
    worth = sum(value(b) for b in B)
    med_v = stat.median(b["price"]["avg_usd"] for b in B)
    med_t = stat.median(b["drink_to"] - NOW for b in B)

    def share(sel):
        v = sum(value(b) for b in sel)
        return v, v / worth * 100

    ranked = sorted(B, key=value, reverse=True)
    top8_v, top8_p = share(ranked[:8])

    dry_white = [b for b in B if b["type"] == "white"]

    cab = sum(qty(b) for b in B if b["grapes"] and b["grapes"][0] == "Cabernet Sauvignon")
    champ = [b for b in B if b["category"] == "샴페인"]
    ch_v, ch_p = share(champ)
    ch_n = sum(qty(b) for b in champ)

    seconds = [b for b in B if b.get("classification") == "Second Wine" or b["id"] == 12]
    sec_v, _ = share(seconds)

    d["facts"] = [
        {"label": "보유", "value": f"{total}병 · {len(B)}종", "ids": []},
        {"label": "추정 가치", "value": usd(worth), "ids": []},
        {"label": "병당", "value": f"평균 {usd(worth / total)} · 중앙 {usd(med_v)}", "ids": []},
        {"label": "음용 창 잔여", "value": f"중앙 {med_t:.0f}년", "ids": []},
        {"label": "주품종 카베르네 소비뇽",
         "value": f"{cab}/{total}병 · {cab / total * 100:.0f}%",
         "ids": [b["id"] for b in B if b["grapes"] and b["grapes"][0] == "Cabernet Sauvignon"]},
        {"label": "샴페인", "value": f"{ch_n}병 · {usd(ch_v)} · 가치 {ch_p:.0f}%",
         "ids": [b["id"] for b in champ]},
        {"label": "화이트 · 스위트",
         "value": f"{sum(qty(b) for b in B if 'white' in b['type'])}병 · 드라이 {len(dry_white)}병",
         "ids": [b["id"] for b in B if "white" in b["type"]]},
        {"label": "세컨 와인", "value": f"{sum(qty(b) for b in seconds)}병 · {usd(sec_v)}",
         "ids": [b["id"] for b in seconds]},
        {"label": "상위 8종 비중", "value": f"{top8_p:.0f}% · {usd(top8_v)}",
         "ids": [b["id"] for b in ranked[:8]]},
        {"label": "3년 내 마감",
         "value": f"{sum(qty(b) for b in B if b['drink_to'] - NOW <= 3)}병 · "
                  f"{usd(sum(value(b) for b in B if b['drink_to'] - NOW <= 3))}",
         "ids": [b["id"] for b in B if b["drink_to"] - NOW <= 3]},
        {"label": "보유 빈티지", "value": f"{len({b['vintage'] for b in B if b['vintage']})}개", "ids": []},
        {"label": "보관", "value": f"{d['storage']['temp_c']}°C", "ids": []},
        {"label": "가격 확인",
         "value": f"확인 {sum(1 for b in B if b['price']['confidence']=='verified')} · "
                  f"추정 {sum(1 for b in B if b['price']['confidence']=='estimate')} · "
                  f"미확인 {sum(1 for b in B if b['price']['confidence']=='unverified')}",
         "ids": [b["id"] for b in B if b["price"]["confidence"] == "unverified"]},
    ]

    d["stats"] = {
        "total": total, "worth": round(worth), "kinds": len(B),
        "median_value": round(med_v), "median_years": round(med_t),
        "avg": round(worth / total),
    }
    return d


# ── 정적 문서 렌더링 ─────────────────────────────────
# 흰 배경 · 검은 텍스트 · 링크. 차트도 스크립트도 없다. 상태만 빨강/초록.

import html as _html


def esc(x):
    return _html.escape(str(x), quote=True)


TONE = {"urgent": ("소진", "r"), "drink_now": ("소진", "r"), "peak": ("정점", "g"),
        "drink_or_hold": ("대기", ""), "hold": ("대기", "")}
LABEL = {"urgent": "임박", "drink_now": "지금", "peak": "정점",
         "drink_or_hold": "음용·대기", "hold": "대기"}
TIER = {"verified": "확인", "estimate": "추정", "unverified": "미확인"}

CSS = """
@font-face{font-family:Pretendard;font-weight:45 930;font-style:normal;font-display:swap;
  src:url(data:font/woff2;base64,__FONT__) format("woff2")}
:root{color-scheme:light}
html,body{background:#fff;color:#111}
body{font-family:Pretendard,-apple-system,BlinkMacSystemFont,system-ui,sans-serif;
  font-size:15px;line-height:1.65;margin:0;padding:28px 20px 72px;
  max-width:860px;margin-inline:auto;-webkit-text-size-adjust:100%}
h1{font-size:20px;margin:0 0 2px}
h2{font-size:15px;margin:34px 0 8px;padding-bottom:4px;border-bottom:1px solid #111}
p{margin:0 0 10px}
a{color:#0b57d0}
a:hover{color:#083a8c}
.meta{color:#666;font-size:13px;margin-bottom:0}
.n{font-variant-numeric:tabular-nums}
.r{color:#c2352b}
.g{color:#1b7f4e}
.q{color:#666}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:6px 0 0}
th,td{border-bottom:1px solid #e3e3e3;padding:6px 8px;text-align:left;vertical-align:top}
th{border-bottom:1px solid #111;font-weight:600;white-space:nowrap}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.q,td.st{white-space:nowrap}
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch}
.tw table{min-width:680px}
ul{margin:0 0 10px;padding-left:20px}
li{margin-bottom:5px}
details{border-bottom:1px solid #e3e3e3;padding:7px 0}
summary{cursor:pointer;font-size:14px}
summary .q{font-weight:400}
.body{padding:8px 0 4px 16px}
.body dt{color:#666;font-size:12.5px;margin-top:8px}
.body dd{margin:0}
dl{margin:0}
hr{border:0;border-top:1px solid #e3e3e3;margin:34px 0 12px}
.foot{color:#666;font-size:12.5px}
"""


def render(d, font):
    B = sorted(d["bottles"], key=lambda b: b["id"])
    st = d["stats"]
    yrs = [b["vintage"] for b in B if b.get("vintage")]
    o = []
    A = o.append

    A("<title>CellarOS</title>")
    A("<style>" + CSS.replace("__FONT__", font) + "</style>")
    A(f"<h1>CellarOS</h1>")
    A(f'<p class="meta">{st["total"]}병 · {st["kinds"]}종 · 추정가치 {usd(st["worth"])} · '
      f'빈티지 {min(yrs)}–{max(yrs)} · 셀러 {d["storage"]["temp_c"]}°C · {d["updated"]} 기준</p>')

    # 요약
    tiers = {}
    for b in B:
        tiers[b["price"]["confidence"]] = tiers.get(b["price"]["confidence"], 0) + 1
    cnt = lambda t: sum(qty(b) for b in B if TONE[b["status"]][0] == t)
    A("<h2>요약</h2>")
    A(f'<p>병당 평균 {usd(st["avg"])}, 중앙값 {usd(st["median_value"])}. '
      f'음용 창 잔여 중앙값 {st["median_years"]}년.<br>'
      f'<span class="r">소진 구간 {cnt("소진")}병</span> · '
      f'<span class="g">정점 {cnt("정점")}병</span> · 대기 {cnt("대기")}병.<br>'
      f'가격 근거 — 확인 {tiers.get("verified",0)}종 · 추정 {tiers.get("estimate",0)}종 · '
      f'미확인 {tiers.get("unverified",0)}종.</p>')

    # 지표
    A("<h2>지표</h2><table>")
    for f in d["facts"]:
        A(f'<tr><td>{esc(f["label"])}</td><td class="num">{esc(f["value"])}</td></tr>')
    A("</table>")

    # 인벤토리
    A('<h2>인벤토리</h2><div class="tw"><table>')
    A('<tr><th class="num">#</th><th>와인</th><th class="num">빈티지</th><th>지역</th>'
      '<th>상태</th><th class="num">음용 창</th><th class="num">가치</th><th>근거</th></tr>')
    for b in B:
        t, cls = TONE[b["status"]]
        v = b.get("vintage") or b.get("vintage_label") or "NV"
        q = f' ×{qty(b)}' if qty(b) > 1 else ""
        A(f'<tr><td class="num">{b["id"]:02d}</td>'
          f'<td><a href="{esc(b["ws_url"])}" target="_blank" rel="noopener">{esc(b["display"])}</a>{q}</td>'
          f'<td class="num">{v}</td><td>{esc(b["region"])}</td>'
          f'<td class="st {cls}">{LABEL[b["status"]]}</td>'
          f'<td class="num">{b["drink_from"]}–{b["drink_to"]}</td>'
          f'<td class="num">{usd(b["price"]["avg_usd"])}</td>'
          f'<td class="q">{TIER.get(b["price"]["confidence"], "")}</td></tr>')
    A("</table></div>")

    # 와인별 노트
    A("<h2>와인별 노트</h2>")
    for b in B:
        pf, pr = b["profile"], b["price"]
        v = b.get("vintage") or b.get("vintage_label") or "NV"
        t, cls = TONE[b["status"]]
        A("<details><summary>"
          f'{b["id"]:02d}. {esc(b["display"])} {v} '
          f'<span class="q">— <span class="{cls}">{LABEL[b["status"]]}</span> · '
          f'{usd(pr["avg_usd"])} {TIER.get(pr["confidence"],"")}</span></summary>')
        A('<div class="body"><dl>')
        A(f'<dt>스타일</dt><dd>{esc(pf["style"])}</dd>')
        A(f'<dt>시음 노트</dt><dd>{esc(pf["tasting"])}</dd>')
        A(f'<dt>배경</dt><dd>{esc(pf["story"])}</dd>')
        A(f'<dt>서빙</dt><dd>{esc(pf["serve"]["temp"])} · 디캔팅 {esc(pf["serve"]["decant"])} · '
          f'{esc(pf["serve"]["glass"])}</dd>')
        A(f'<dt>페어링</dt><dd>{esc(" · ".join(pf["pair"]))}</dd>')
        A(f'<dt>메모</dt><dd>{esc(b["notes"])}</dd>')
        e = pr.get("est")
        src = esc(pr.get("source", ""))
        if e:
            src += f' · 호가 {e["n_listings"]}곳 {usd(e["low"])}~{usd(e["high"])}'
            if e.get("ws_snippet"):
                src += f' · WS 스니펫 {usd(e["ws_snippet"])}'
        A(f'<dt>가격 근거</dt><dd>{TIER.get(pr["confidence"],"")} — {src}</dd>')
        meta = [esc(b["producer"])]
        if b.get("classification"):
            meta.append(esc(b["classification"]))
        if b.get("grapes"):
            meta.append(esc(" · ".join(b["grapes"])))
        if b.get("abv"):
            meta.append(f'{b["abv"]}%')
        meta.append(f'{b.get("format_ml", 750)}ml')
        A(f'<dt>정보</dt><dd class="q">{" · ".join(meta)} · '
          f'<a href="{esc(b["ws_url"])}" target="_blank" rel="noopener">Wine-Searcher</a></dd>')
        A("</dl></div></details>")

    # 확인할 것
    byid = {b["id"]: b for b in B}
    if d.get("flags"):
        A("<h2>확인할 것</h2><ul>")
        for f in d["flags"]:
            A(f'<li><b>{f["id"]:02d}. {esc(byid[f["id"]]["display"])} — {esc(f["title"])}</b><br>'
              f'<span class="q">{esc(f["text"])}</span></li>')
        A("</ul>")

    A("<hr>")
    A(f'<p class="foot">{esc(d["price_note"])}</p>')
    A(f'<p class="foot">{esc(d["storage"]["note"])}</p>')
    return "\n".join(o)


def main():
    data = analyse(json.loads((ROOT / "data" / "cellar.json").read_text()))
    font = (ROOT / "web" / "font" / "pretendard.b64").read_text().strip()
    out = ROOT / "web" / "dashboard.html"
    out.write_text(render(data, font))
    kb = out.stat().st_size / 1024
    print(f"{out.relative_to(ROOT)}: {data['stats']['total']}병 · {kb:.0f} KB · 정적 문서")


if __name__ == "__main__":
    main()
