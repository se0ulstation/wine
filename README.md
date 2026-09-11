# 🍷 Wine Cellar

개인 와인 셀러 인벤토리 및 컨설팅 기록.

- [`data/cellar.json`](data/cellar.json) — **원본 데이터.** 인벤토리는 여기서만 수정한다.
- [`CELLAR.md`](CELLAR.md) — 셀러 현황, 음용 우선순위, 홀드 목록. **자동 생성물이므로 직접 수정하지 말 것.**
- [`web/dashboard.html`](web/dashboard.html) — 대시보드. **자동 생성물.** ([`web/dashboard.template.html`](web/dashboard.template.html) 을 수정할 것)
- `scripts/build_cellar.py`, `scripts/build_dashboard.py` — 생성기

```
python3 scripts/build_cellar.py     # → CELLAR.md
python3 scripts/build_dashboard.py  # → web/dashboard.html
```

대시보드는 Artifact 로 배포되어 있다. 데이터를 고친 뒤 두 스크립트를 돌리고 같은 경로로 재배포하면 링크가 유지된다.

## 데이터 스키마

| 필드 | 설명 |
|---|---|
| `id` | 병 고유 번호 |
| `producer` / `wine` / `vintage` | 생산자 / 와인명 / 빈티지 (`null` = NV 또는 미확인) |
| `country` / `region` / `classification` | 원산지 및 등급 |
| `type` | `red` / `white` / `sparkling` |
| `grapes` | 품종 |
| `qty` | 수량 |
| `drink_from` / `drink_to` | 음용 창 (연도) |
| `status` | `urgent` · `drink_now` · `peak` · `drink_or_hold` · `hold` · `verify` |
| `display` | 표기용 이름 |
| `category` | 구성 개요 분류 |
| `short` | 요약 테이블용 한 줄 코멘트 |
| `format_ml` | 병 용량 (750 외일 때만) |
| `notes` | 상세 코멘트 |

## 추가 예정 필드

구매가, 구매처, 입고일, 보관 위치, 시음 기록.
