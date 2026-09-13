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

    hi_short = [b for b in B if b["price"]["avg_usd"] >= med_v and b["drink_to"] - NOW < med_t]
    hs_v, hs_p = share(hi_short)

    dry_white = [b for b in B if b["type"] == "white"]
    dry_left = [b for b in dry_white if b["drink_to"] > 2029]

    cab = sum(qty(b) for b in B if b["grapes"] and b["grapes"][0] == "Cabernet Sauvignon")
    champ = [b for b in B if b["category"] == "샴페인"]
    ch_v, ch_p = share(champ)
    ch_n = sum(qty(b) for b in champ)

    seconds = [b for b in B if b.get("classification") == "Second Wine" or b["id"] == 12]
    sec_v, sec_p = share(seconds)
    sec_short = sum(qty(b) for b in seconds if b["drink_to"] <= 2029)

    y96 = [b for b in B if b["vintage"] == 1996]
    v96, _ = share(y96)

    have = {b["vintage"] for b in B if b["vintage"]}
    bdx = {b["vintage"] for b in B if "Bordeaux" in b["region"]}

    def sig(tag, sev, head, metric, detail, sel):
        """sel: 이 신호가 가리키는 병들. 콘솔에서 신호를 누르면 그대로 필터가 된다."""
        return {"tag": tag, "sev": sev, "head": head, "metric": metric,
                "detail": detail, "ids": [b["id"] for b in sel]}

    names = " · ".join(short(b) for b in sorted(hi_short, key=lambda x: x["drink_to"]))
    d["insights"] = [
        sig("RISK", "high", "고가 · 단기 구역", f"{usd(hs_v)} · {hs_p:.0f}%",
            f"{len(hi_short)}종 — {names}", hi_short),
        sig("GAP", "high", "드라이 화이트 소멸", f"{len(dry_white)} → {len(dry_left)} · 2029",
            "샤사뉴 2028 · 푸이 퓌메 2027 이후 스위트와 샴페인만 남음", dry_white),
        sig("CONC", "med", "상위 8종 가치 집중", f"{top8_p:.0f}% · {usd(top8_v)}",
            f"나머지 24병 합계 {usd(worth - top8_v)}", ranked[:8]),
        sig("MIX", "med", "카베르네 편중", f"{cab}/{total} · {cab / total * 100:.0f}%",
            "레드 피노 누아 0병 · 산지오베제 1병 · 시라 0병",
            [b for b in B if b["grapes"] and b["grapes"][0] == "Cabernet Sauvignon"]),
        sig("GAP", "med", "보르도 2009 · 2010 없음", f"보유 {len(bdx)}개 빈티지",
            " · ".join(str(y) for y in sorted(bdx)),
            [b for b in B if "Bordeaux" in b["region"]]),
        sig("MIX", "low", "샴페인 가치 초과", f"병 {ch_n / total * 100:.0f}% → 가치 {ch_p:.0f}%",
            f"{ch_n}병 중 6병이 프레스티지 큐베 · 데일리 1병", champ),
        sig("OPP", "low", "1996 수평 가능", f"4병 · {usd(v96)}",
            "좌안 · 우안 · 볼게리 · 나파 — 전부 3년 내 마감", y96),
        sig("MIX", "low", "세컨 와인 비중", f"{sum(qty(b) for b in seconds)}병 · {sec_p:.0f}%",
            f"{sec_short}병이 2029년 내 마감 · 장기 보관 대상 아님", seconds),
    ]

    d["stats"] = {
        "total": total, "worth": round(worth), "kinds": len(B),
        "median_value": round(med_v), "median_years": round(med_t),
        "avg": round(worth / total),
    }
    return d


def main():
    tpl = (ROOT / "web" / "dashboard.template.html").read_text()
    data = analyse(json.loads((ROOT / "data" / "cellar.json").read_text()))
    out = ROOT / "web" / "dashboard.html"
    out.write_text(tpl.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False)))
    print(f"{out.relative_to(ROOT)}: {data['stats']['total']}병 · 인사이트 {len(data['insights'])}건")


if __name__ == "__main__":
    main()
