#!/usr/bin/env python3
"""data/cellar.json 으로부터 CELLAR.md 를 생성한다.

CELLAR.md 는 직접 수정하지 말 것. 인벤토리는 JSON 에서만 고치고 이 스크립트를 실행한다.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "cellar.json"
OUT = ROOT / "CELLAR.md"

STATUS_LABEL = {
    "urgent": "긴급",
    "drink_now": "지금",
    "peak": "피크",
    "drink_or_hold": "음용/홀드",
    "hold": "홀드",
    "verify": "확인 필요",
}


def vintage(b):
    return str(b["vintage"]) if b.get("vintage") else b.get("vintage_label", "NV")


def window(b):
    f, t = b.get("drink_from"), b.get("drink_to")
    if f and t:
        return f"{f}–{t}"
    if t:
        return f"~{t}"
    return "—"


def label(b):
    s = b.get("display") or f"{b['producer']} {b['wine']}"
    if b.get("format_ml") and b["format_ml"] != 750:
        s += f" ({b['format_ml']}ml)"
    if b.get("qty", 1) > 1:
        s += f" ×{b['qty']}"
    return s


def open_from(b, updated):
    """음용 창이 이미 열린 병은 연도 대신 '지금 가능'으로 표시한다."""
    year = int(updated[:4])
    f = b.get("drink_from")
    return "지금 가능" if f and f <= year else f"{f}+"


def table(rows, header):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def main():
    d = json.loads(SRC.read_text())
    bs = sorted(d["bottles"], key=lambda b: b["id"])
    total = sum(b.get("qty", 1) for b in bs)

    L = [
        "<!-- 이 파일은 scripts/build_cellar.py 가 data/cellar.json 에서 생성합니다. 직접 수정하지 마세요. -->",
        "",
        "# 셀러 인벤토리",
        "",
        f"기준일: {d['updated']} · 총 {total}병 / {len(bs)}종",
        "",
        "## 구성 개요",
        "",
    ]

    counts = Counter()
    for b in bs:
        counts[b["category"]] += b.get("qty", 1)
    L.append(table([[c, str(n)] for c, n in counts.most_common()], ["카테고리", "병수"]))
    L += ["", d["summary"], "", "---", ""]

    def section(title, statuses, cols, row, sort):
        sel = sorted([b for b in bs if b["status"] in statuses], key=sort)
        if not sel:
            return
        L.append(f"## {title}")
        L.append("")
        L.append(table([row(b) for b in sel], cols))
        L.append("")

    section(
        "🔴 최우선 소비 (2년 내)", {"urgent", "drink_now"},
        ["#", "와인", "빈티지", "이유"],
        lambda b: [str(b["id"]), label(b), vintage(b), b["short"]],
        lambda b: (b.get("drink_to") or 9999, b["id"]),
    )
    section(
        "🟢 지금이 피크 (언제 열어도 좋음)", {"peak"},
        ["#", "와인", "빈티지", "코멘트"],
        lambda b: [str(b["id"]), label(b), vintage(b), b["short"]],
        lambda b: (b.get("vintage") or 9999, b["id"]),
    )
    section(
        "🟡 음용/홀드 (지금 열어도 되지만 더 기다리면 좋아짐)", {"drink_or_hold"},
        ["#", "와인", "빈티지", "본령", "코멘트"],
        lambda b: [str(b["id"]), label(b), vintage(b), f"{b['peak_from']}년 전후", b["short"]],
        lambda b: (b.get("vintage") or 9999, b["id"]),
    )
    section(
        "🔵 홀드 (열지 말 것)", {"hold"},
        ["#", "와인", "빈티지", "개봉 권장", "코멘트"],
        lambda b: [str(b["id"]), label(b), vintage(b), open_from(b, d["updated"]), b["short"]],
        lambda b: (b.get("drink_from") or 0, b["id"]),
    )
    section(
        "⚠️ 확인 필요", {"verify"},
        ["#", "와인", "빈티지", "필요한 정보"],
        lambda b: [str(b["id"]), label(b), vintage(b), b["short"]],
        lambda b: b["id"],
    )

    L += ["---", "", "## 전체 목록", ""]
    L.append(table(
        [[str(b["id"]), label(b), vintage(b), b["region"],
          STATUS_LABEL[b["status"]], window(b)] for b in bs],
        ["#", "와인", "빈티지", "지역", "상태", "음용 창"],
    ))
    L += [
        "",
        "> 음용 창은 일반적인 빈티지 평가 기준이며, 실제 보관 환경"
        "(온도 12–14°C, 습도 70%, 진동·광 차단)에 따라 달라집니다.",
        "",
    ]
    OUT.write_text("\n".join(L))
    print(f"{OUT.name}: {total}병 / {len(bs)}종")


if __name__ == "__main__":
    main()
