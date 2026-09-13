#!/usr/bin/env python3
"""Wine-Searcher wine-check API 로 각 병의 price_average 를 받아 cellar.json 에 기록한다.

    WS_API_KEY=... python3 scripts/fetch_ws_prices.py            # 전체
    WS_API_KEY=... python3 scripts/fetch_ws_prices.py --only 30  # 한 병만
    python3 scripts/fetch_ws_prices.py --dry-run                 # 키 없이 요청만 확인

wine-check 응답의 price_average 는 "Average retail price across all listings" 로,
Wine-Searcher 페이지의 Avg Price 와 같은 값이다. location/state 를 붙이지 않으면
특정 국가로 좁혀지지 않으므로 전세계 기준이 된다 — 그래서 여기서는 붙이지 않는다.

엔드포인트 경로는 API Evangelist 가 공개 자료에서 '유도'한 것이라 실제와 다를 수
있다. 그래서 첫 요청에서 후보 형태를 차례로 시도하고, 성공한 형태를 이후에 재사용한다.
"""
import argparse, json, os, ssl, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "cellar.json"
BASE = "https://www.wine-searcher.com/ws_api.php"
CANDIDATES = [                      # 성공하는 형태를 첫 병에서 찾아 고정한다
    BASE + "/wine-check",           # OpenAPI 스펙이 기술한 형태
    BASE,                           # 쿼리만 붙이는 고전적 형태
    BASE + "?action=wine-check",
]
PAUSE = 7.0                         # 분당 10회 한도를 넉넉히 밑도는 간격


def winename(b):
    """저장해 둔 Wine-Searcher URL 슬러그가 곧 그쪽 정식 표기다."""
    slug = b["ws_url"].rstrip("/").split("/find/")[-1]
    return slug.split("/")[0]


def build(url, key, b):
    q = {"api_key": key, "winename": winename(b), "currencycode": "USD", "format": "json"}
    if b.get("vintage"):
        q["vintage"] = str(b["vintage"])
    elif b.get("vintage_label") == "NV":
        q["vintage"] = "NV"
    # winename 의 '+' 는 Wine-Searcher 의 단어 구분자다. 기본 인코더는 이걸 %2B 로
    # 바꿔버리므로 safe 에 넣어 그대로 통과시킨다.
    sep = "&" if "?" in url else "?"
    return url + sep + urllib.parse.urlencode(q, quote_via=urllib.parse.quote, safe="+")


def ctx():
    ca = "/root/.ccr/ca-bundle.crt"
    return ssl.create_default_context(cafile=ca) if os.path.exists(ca) else ssl.create_default_context()


def call(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "cellaros/1.0"})
    with urllib.request.urlopen(req, timeout=30, context=ctx()) as r:
        return json.loads(r.read().decode())


def redact(url, key):
    return url.replace(key, "***") if key else url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", type=int, action="append", help="병 번호 (여러 번 지정 가능)")
    a = ap.parse_args()

    key = os.environ.get("WS_API_KEY", "")
    if not key and not a.dry_run:
        sys.exit("WS_API_KEY 가 없습니다. WS_API_KEY=... 로 실행하거나 --dry-run 을 쓰세요.")

    d = json.loads(SRC.read_text())
    bottles = [b for b in d["bottles"] if not a.only or b["id"] in a.only]

    if a.dry_run:
        for b in bottles:
            print(f"{b['id']:>2} {b['display'][:38]:<38} {redact(build(CANDIDATES[0], key or 'KEY', b), key)}")
        print(f"\n{len(bottles)}건 · 간격 {PAUSE}s · 예상 {len(bottles) * PAUSE / 60:.1f}분")
        return

    shape = None
    ok = bad = 0
    for i, b in enumerate(bottles):
        tries = [shape] if shape else CANDIDATES
        data = None
        for cand in tries:
            try:
                r = call(build(cand, key, b))
            except Exception as e:                       # 형태가 틀리면 404/500 이 난다
                print(f"  · {cand.split('ws_api.php')[-1] or '(query only)'} → {e}")
                continue
            if r.get("status") == 0 and r.get("wine"):
                shape, data = cand, r["wine"]
                break
            print(f"  · status={r.get('status')} {r.get('message')}")
        if not data:
            print(f"{b['id']:>2} {b['display'][:34]:<34} 실패")
            bad += 1
        else:
            avg = data.get("price_average")
            if avg:
                b["price"].update({
                    "avg_usd": round(float(avg)),
                    "confidence": "verified", "source_kind": "api",
                    "source": "Wine-Searcher wine-check API · price_average (USD, 전세계)",
                    "basis": "750ml, ex-tax",
                    "ws_min": data.get("price_min"), "ws_max": data.get("price_max"),
                    "ws_listings": data.get("listing_count"),
                })
                b["price"].pop("note", None)
                b["price"]["verified"] = (
                    f"API 응답 · 최저 {data.get('price_min')} / 최고 {data.get('price_max')}"
                    f" / 등재 {data.get('listing_count')}곳")
                print(f"{b['id']:>2} {b['display'][:34]:<34} ${round(float(avg)):>5}")
                ok += 1
            else:
                print(f"{b['id']:>2} {b['display'][:34]:<34} price_average 없음")
                bad += 1
        if i < len(bottles) - 1:
            time.sleep(PAUSE)

    SRC.write_text(json.dumps(d, ensure_ascii=False, indent=2))
    print(f"\n확인 {ok} · 실패 {bad} → {SRC.relative_to(ROOT)} 갱신")
    print("이어서: python3 scripts/build_dashboard.py && python3 scripts/build_cellar.py")


if __name__ == "__main__":
    main()
