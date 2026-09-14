# Wine Cellar

A personal cellar: what is in it, when to drink it, and what it is worth.

`data/cellar.json` is the only file edited by hand. Everything else is generated,
so the numbers in the Markdown and in the dashboard can never drift apart.

```
python3 scripts/build_cellar.py     # -> CELLAR.md
python3 scripts/build_prices.py     # -> PRICES.md
python3 scripts/build_dashboard.py  # -> web/dashboard.html
```

| Path | |
|---|---|
| [`data/cellar.json`](data/cellar.json) | **Source of truth.** Edit the inventory here and nowhere else. |
| [`scripts/cellar.py`](scripts/cellar.py) | Shared domain: status, value, regions, appellations. Every generator imports it. |
| [`CELLAR.md`](CELLAR.md) | The cellar as a document. Generated. |
| [`PRICES.md`](PRICES.md) | Which prices still need confirming. Generated. |
| [`web/dashboard.html`](web/dashboard.html) | The dashboard body. Generated, published as an Artifact. |
| [`docs/index.html`](docs/index.html) | The same page, standalone, served by GitHub Pages. Generated. |

The dashboard is a static document — no client-side script. Filtering, sorting
and the expanding rows are hidden radios and `<details>` read by CSS sibling
selectors, so it works with JavaScript off and prints as it reads. Rebuild and
republish to the same file path and the Artifact link stays the same.

Type is Aptos where the reader has it, falling back through Segoe UI to the
system sans. Nothing is embedded: Aptos is proprietary, not licensed for
self-hosting as a webfont, and not on Google Fonts.

## Schema

| Field | |
|---|---|
| `id` | Bottle number |
| `producer` / `wine` / `vintage` | `vintage: null` means NV — set `vintage_label` |
| `country` / `region` / `classification` | Origin and rank |
| `type` | `red` / `white` / `sparkling` |
| `grapes` | Varieties, most important first |
| `qty` | How many bottles |
| `format_ml` | Bottle size; omit for 750 |
| `drink_from` / `drink_to` | Drinking window, in years |
| `display` / `short` / `category` | Name and one-line note for the tables |
| `notes` | The practical note: what to do with this bottle |
| `profile` | `style`, `tasting`, `story`, `serve`, `pair` |
| `price` | `avg_usd` on a 750ml basis, plus `confidence` and its provenance |
| `ws_url` | Wine-Searcher page for this wine and vintage |

**Status is not stored.** It is derived from the drinking window every build:
past the window is post peak; inside its last quarter is urgent; not yet open is
hold; a quarter of the way in — or five years past the opening — is peak;
everything else is drink now. A stored status would be wrong within a year.

Urgency is **relative to the window, not a fixed countdown**. A year left on a
Cava is a third of its life; a year left on a 1996 Napa Cabernet is four per
cent of it. An absolute threshold puts those two in the same bucket, which is
wrong in both directions.

**`price.confidence`** is honest about provenance: `verified` was read off a
Wine-Searcher page, `estimate` is a triangulated median of real merchant
listings, `unverified` came from a single web search and has been wrong by 2.7x
before. See `PRICES.md`.

## Not yet tracked

Purchase price, merchant, date acquired, rack position, tasting history.
