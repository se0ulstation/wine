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

    def ins(kicker, act, head, detail, sel):
        return {"kicker": kicker, "act": act, "head": head, "detail": detail,
                "ids": [b["id"] for b in sel]}

    names = " · ".join(short(b) for b in sorted(hi_short, key=lambda x: x["drink_to"])[:3])
    d["insights"] = [
        ins("공백", True, "드라이 화이트가 2029년에 사라진다",
            f"드라이 화이트는 샤사뉴 2022(창 2028)와 푸이 퓌메 2024(창 2027) 둘뿐이고 나머지 화이트는 스위트다. "
            f"둘이 닫히면 생선·해산물 자리에 낼 카드가 프레스티지 샴페인밖에 남지 않는다.", dry_white),
        ins("리스크", True, f"가치 {hs_p:.0f}%가 시간이 없는 쪽에 있다",
            f"{len(hi_short)}종 {usd(hs_v)} — {names} 외. 병당 가치가 중앙값 위이면서 잔여 기간은 중앙값 미만이라, "
            f"여는 순서를 잘못 잡으면 손실이 가장 큰 그룹이다.", hi_short),
        ins("공백", False, "보르도 2009 · 2010만 비어 수직이 미완성이다",
            f"보유 보르도가 {', '.join(str(y) for y in sorted(bdx))}인데 금세기 최고로 꼽히는 두 해만 정확히 없다. "
            f"2000 · 2005 · 2008을 이미 갖고 있어 두 병이면 흐름이 이어진다.",
            [b for b in B if "Bordeaux" in b["region"]]),
        ins("구조", False, "산지는 다양한데 골격은 겹친다",
            f"카베르네 소비뇽이 주품종인 병이 {cab}/{total}. 보르도 좌안 · 나파 · 볼게리 · 호주가 모두 같은 축에 얹혀 있다. "
            f"레드 피노 누아와 시라는 0병이라, 축을 바꾸는 한 병이 같은 축 다섯 병보다 셀러를 넓힌다.",
            [b for b in B if b["grapes"] and b["grapes"][0] == "Cabernet Sauvignon"]),
        ins("구조", False, "가볍게 딸 샴페인이 없다",
            f"샴페인 {ch_n}병 중 6병이 프레스티지 큐베이고 그로워는 모니알 1병뿐이다. "
            f"'샴페인을 연다'가 늘 큰 결정이 되는 구성이다.", champ),
        ins("집중", False, f"상위 8종이 가치의 {top8_p:.0f}%를 차지한다",
            f"{usd(top8_v)} 대 나머지 24병 {usd(worth - top8_v)}. 보관 사고나 코르크 불량 한 번의 기대손실이 "
            f"그만큼 크고, 셀러의 성패도 이 여덟 병을 언제 여느냐에 달려 있다.", ranked[:8]),
        ins("기회", False, "1996은 유효기간이 있는 기회다",
            f"하우트 브리옹(좌안) · 도멘 드 레글리즈(우안) · 오르넬라이아(볼게리) · 실버 오크(나파). "
            f"한 해를 네 산지로 비교할 수 있는 유일한 조합인데 네 병 모두 3년 내 마감이다.", y96),
        ins("구조", False, "세컨 와인은 장기 자산이 아니다",
            f"{sum(qty(b) for b in seconds)}병 {usd(sec_v)} 중 {sec_short}병이 이미 2029년 내 마감이다. "
            f"그랑뱅을 기다리는 동안 열 병으로는 좋지만 묵히는 대상으로 잡으면 안 된다.", seconds),
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
    font = (ROOT / "web" / "font" / "pretendard.b64").read_text().strip()
    html = tpl.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
    out.write_text(html.replace("__FONT__", font))
    print(f"{out.relative_to(ROOT)}: {data['stats']['total']}병 · 인사이트 {len(data['insights'])}건")


if __name__ == "__main__":
    main()
