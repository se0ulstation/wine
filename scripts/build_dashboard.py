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

    def ins(tag, sev, head, metric, body):
        return {"tag": tag, "sev": sev, "head": head, "metric": metric, "body": body}

    d["insights"] = [
        ins("리스크", "high",
            "고가 · 단기 사분면에 셀러의 4분의 1이 묶여 있다",
            f"{len(hi_short)}종 · {usd(hs_v)} · 전체의 {hs_p:.0f}%",
            f"병당 가치가 중앙값({usd(med_v)}) 위이면서 남은 기간이 중앙값({med_t:.0f}년) 미만인 병들이다. "
            f"비싼데 시간이 없다는 뜻이라 순서를 잘못 잡으면 가장 크게 손해 보는 그룹이고, "
            f"실제로 " + ", ".join(b["display"] for b in sorted(hi_short, key=lambda x: x["drink_to"])[:3]) +
            " 가 여기 들어간다. 아래 매트릭스의 좌상단이 이 구역이다."),

        ins("공백", "high",
            "2029년이면 드라이 화이트가 0병이 된다",
            f"현재 {len(dry_white)}병 → 2029년 {len(dry_left)}병",
            "화이트로 분류된 병은 샤사뉴 몽라셰 2022(창 2028)와 푸이 퓌메 2024(창 2027) 둘뿐이고, "
            "나머지 화이트 2병은 쿠테와 물랭 투셰 — 둘 다 스위트다. "
            "3년 안에 드라이 화이트가 소멸하면 해산물·생선 자리에 낼 카드가 스위트 아니면 샴페인밖에 안 남는다. "
            "샴페인은 전부 프레스티지 큐베라 평일 생선 요리에 열기엔 과하다."),

        ins("집중", "med",
            f"상위 8종이 전체 가치의 절반을 넘는다",
            f"{top8_p:.0f}% · {usd(top8_v)}",
            f"34병 중 10병(중복 빈티지 포함)이 {usd(top8_v)}를 차지한다. 나머지 24병을 다 합쳐도 "
            f"{usd(worth - top8_v)}다. 셀러의 성패가 사실상 이 8종을 언제 어떻게 여느냐에 달려 있다는 뜻이고, "
            f"보관 사고나 코르크 불량 한 번의 기대손실도 그만큼 크다."),

        ins("구조", "med",
            "카베르네 소비뇽이 주품종인 병이 절반을 넘는다",
            f"{cab}/{total}병 · {cab / total * 100:.0f}%",
            "보르도 좌안·나파·볼게리·호주가 전부 카베르네 축에 얹혀 있어서, 산지는 다양해 보여도 "
            "잔에서 만나는 골격은 상당히 겹친다. 산지오베제 1병, 피노 누아는 샴페인 안에만 있고 "
            "레드로는 0병이다. 다양성을 늘리는 가장 값싼 방법은 병 수를 늘리는 게 아니라 축을 바꾸는 것 — "
            "부르고뉴 피노와 북부 론 시라 각 1병이 카베르네 5병보다 셀러를 넓힌다."),

        ins("공백", "med",
            "보르도 2009 · 2010이 통째로 비어 있다",
            f"보유 보르도 빈티지 {len(bdx)}개 · 2009 · 2010 없음",
            "2009와 2010은 금세기 보르도 최고 빈티지로 나란히 꼽히는 해다. 보유 보르도가 "
            f"{', '.join(str(y) for y in sorted(bdx))}인데 이 두 해만 정확히 비어 있다. "
            "지금 있는 2000·2005·2008과 함께 놓으면 빈티지 수직이 완성되는 자리이고, "
            "가격도 아직 정점 전이라 채워 넣을 값이 있는 공백이다."),

        ins("구조", "low",
            f"샴페인이 병 수보다 가치 비중이 크다",
            f"병 {ch_n / total * 100:.0f}% → 가치 {ch_p:.0f}% · {usd(ch_v)}",
            f"샴페인 {ch_n}병 중 크뤼그·크리스탈·DP 3종·퀴베 루이즈까지 6병이 프레스티지 큐베다. "
            "즉 '샴페인을 연다'가 항상 큰 결정이 되는 구조라, 정작 가볍게 딸 한 병이 없다. "
            "그로워 샴페인(모니알)이 유일한 완충인데 1병뿐이다."),

        ins("기회", "low",
            "1996이 네 병 — 유일하게 수평 시음이 성립하는 해",
            f"4병 · {usd(v96)} · 전부 3년 내 마감",
            "하우트 브리옹(좌안) · 도멘 드 레글리즈(우안) · 오르넬라이아(볼게리) · 실버 오크(나파). "
            "한 해를 네 산지가 어떻게 다르게 소화했는지 한 자리에서 볼 수 있는 조합인데, "
            "네 병 모두 창 끝자락이라 유효기간이 있는 기회다. 다른 어떤 해도 이만한 폭이 안 나온다."),

        ins("구조", "low",
            "세컨 와인 비중이 가치의 8분의 1",
            f"{sum(qty(b) for b in seconds)}병 · {usd(sec_v)} · {sec_p:.0f}%",
            f"프티 무통 · 파비용 루즈 · 알테르 에고 · 오버추어 2병. 세컨은 그랑뱅보다 창이 일찍 닫히는데 "
            f"실제로 {sec_short}병이 이미 2029년 내 마감 구간이다. 그랑뱅을 기다리는 동안 열 병으로는 좋지만, "
            "장기 보관 자산으로 취급하면 안 되는 그룹이다."),
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
