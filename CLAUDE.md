# CellarOS

A personal wine cellar: what is in it, when to drink it, what it is worth.
40 bottles across 35 labels.

## The one rule

`data/cellar.json` is the only file edited by hand. `CELLAR.md`, `PRICES.md`
and `web/dashboard.html` are all generated from it. Never edit a generated
file — the change is gone at the next build, and the two documents drift apart,
which is the failure this layout exists to prevent.

```
python3 scripts/build_cellar.py     # -> CELLAR.md
python3 scripts/build_prices.py     # -> PRICES.md
python3 scripts/build_dashboard.py  # -> web/dashboard.html
```

Run all three after any data change. `scripts/cellar.py` holds everything
derived — status, value, regions, appellations — so the Markdown and the HTML
cannot disagree about a number.

## Status is derived, never stored

`scripts/cellar.py::status()` computes it from the drinking window at build
time. There is no `status` field to trust; a stored one is wrong within a year.

Urgency is **relative to the window, not an absolute countdown**. A year left
on a Cava is a third of its life; a year left on a 1996 Napa Cabernet is four
per cent of it. An absolute threshold put those two in the same bucket and was
wrong in both directions. If you are tempted to add `left <= N` back, don't —
that exact escape hatch has already been removed once.

Five states: post peak, urgent, hold, peak, drink now. Adding a sixth means
touching `STATUS` in `cellar.py` and nothing else.

## Prices are graded by provenance, and the grade is the point

`price.confidence` is one of:

- **`verified`** — read directly off the Wine-Searcher page. Two wines.
- **`estimate`** — median of real retailer listings for the matching vintage,
  outliers removed.
- **`unverified`** — a single web-search value.

**Never promote a price without the evidence to match.** A search snippet put
Château Canon 2000 at **$603** when the real Wine-Searcher average is **$220** —
inflated 2.7x, and confirmed by five differently-phrased searches, because
snippets happily scrape an all-vintage average page. Repetition across searches
is not corroboration. If you cannot open a page and read the number, the wine
stays `unverified` and goes in `PRICES.md`.

`scripts/fetch_ws_prices.py` resolves the whole list in one pass given a
Wine-Searcher API key (`WS_API_KEY=... python3 scripts/fetch_ws_prices.py`).
Wine-Searcher blocks automated access with a CAPTCHA; do not try to defeat it.

`avg_usd` is always a **750ml** price. `value()` scales it by `format_ml`, so
a magnum counts double and a half-bottle counts half.

## The dashboard has no JavaScript, and that is deliberate

Filtering, sorting and expanding are hidden radio and disclosure elements read
by sibling selectors. Three things will silently break it:

1. **Input order.** Region radios must come before status radios, and both
   before `.main`. The empty-combination rules are `#rg:checked ~ #st:checked ~
   .main`, and `~` only looks forward.
2. **`.main` as a sibling.** Every filter rule is `#id:checked ~ .main ...`.
   Wrapping `.main` in anything, or moving the inputs inside it, kills all of
   them at once.
3. **Rule order.** The active-chip rules are emitted last on purpose, so a
   chosen option beats a dim rule aimed at it. Appending rules after them
   reintroduces the bug where a selected filter renders greyed out.

Sort is one `order` per row; direction is a single `flex-direction:
column-reverse` with the header pinned at `order:9999`. The "showing N of 40"
line is a CSS counter — rows hidden by a filter are not counted, so it stays
true without script. Don't replace any of this with JS to "simplify" it.

**The default sort is free because rows are emitted in it.** `SORTS[0]` is the
default (vintage); the render loop sorts the DOM by it and emits no `order`
rules for it. Change `SORTS[0]` and the DOM order follows automatically — but
never reorder `SORTS` without checking that, or the page loads showing one
order while claiming another.

There is no `#` column. The id is an insertion-order key, not a rack position,
and once rows can be sorted it reads as noise; it survives in the data, in each
opened note, and nowhere else.

Quantity belongs beside the **name**, as a tag, not only in the value column —
it has been moved twice and it belongs where the eye already is. The value cell
carries the arithmetic instead (`$1,008` over `2 × $504`), which is a different
question asked in a different place. Value is always the line total, so the
column sums to the cellar total in the masthead; don't switch it to per-bottle
without changing that figure too.

Verify changes by rendering the file in headless Chromium and pre-checking a
radio (`id="f-rg-bordeaux" checked`) to inspect a filter state. Note that
headless reports `innerWidth` 500 regardless of `--window-size`, so apparent
right-edge clipping in a narrow screenshot is a capture artifact — check
`documentElement.scrollWidth` against `clientWidth` for real overflow.

## Typeface

Aptos, asked for locally. It is proprietary to Microsoft, not licensed for
self-hosting as a webfont, and not on Google Fonts — which is the only external
font host the artifact CSP admits. Nothing is embedded; readers without it fall
back through Segoe UI to the system sans. Do not add a `@font-face` for it.

## Vintage notes

Each bottle carries `vintage_note: {rating, text}` — one of `great`, `very
good`, `good`, `mixed`, `poor`, or `n/a` for non-vintage. These rate **the
growing season in that region and year, not the bottle**: a good estate makes
decent wine in a poor year. They come from general knowledge rather than a
source, so where one is shaky the text says so outright (bottle 32, Layon
1981). Keep that habit — a hedge is worth more than false precision.

## Get the wine right before writing about it

Two errors worth not repeating, both from assuming the common case:

- **Chassagne-Montrachet is not automatically white.** Bottle 23 is red Pinot
  Noir; it was catalogued as Chardonnay, and every tasting note, pairing and
  serving temperature written for it was wrong as a result.
- **"Domaine des Fines Caillottes" is an estate name, not a cuvée.** It was
  written as a parenthetical on bottle 29. The Pabiot family use it to tell
  themselves apart from the six other Pabiots in Pouilly.

Check colour, grape and what part of the name is the producer before writing a
profile. The prose is long and confident, which makes a wrong premise expensive.

## Conventions

- **English throughout** — code, comments, data, output. No Korean anywhere.
- Palette is ink on white with red and green reserved for status. Colour that
  does not mean something does not belong.
- Everything must survive printing and reading with JavaScript off.

## Publishing

The dashboard is a published Artifact. Republishing `web/dashboard.html` keeps
the same URL: https://claude.ai/code/artifact/aeb0a766-9914-40bd-a841-1d7f055d955e

Work happens on `claude/loving-shannon-3b2a6l`.

## Open

- 33 of 35 labels still need a real Wine-Searcher average. `PRICES.md` lists
  them worst-first by how much each moves the cellar total.
- Bottle 30 (Château Canon 2000) is flagged for bottle variation.
- Non-vintage windows are soft — without a disgorgement date there is nothing
  to anchor them to. Bottles 12, 20 and 34.
- Not tracked: purchase price, merchant, date acquired, rack position, tasting
  history. A real rack position would be worth a column; the insertion-order id
  never was.
