# 🍷 Wine Cellar

개인 와인 셀러 인벤토리 및 컨설팅 기록.

- [`CELLAR.md`](CELLAR.md) — 사람이 읽는 셀러 현황, 음용 우선순위, 홀드 목록
- [`data/cellar.json`](data/cellar.json) — 구조화된 인벤토리 데이터

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
| `notes` | 코멘트 |

## 추가 예정 필드

구매가, 구매처, 입고일, 병 포맷(750ml/매그넘), 보관 위치, 시음 기록.
