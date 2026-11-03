# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A static, Hebrew (RTL) daily siddur website, hosted on GitHub Pages. It picks the correct prayer text for the current date, time and location in three nusachim (Ashkenaz `a`, Sefard `s`, Edot HaMizrach `em`). Prayer texts, instructions and the per-day logic are taken from the "Tfilon+" app (v0.2.21) by Uri Hollander; copyright remains his. User-facing strings and docs are in Hebrew.

There is no build step, package manager, linter or test suite. All code lives in `index.html` (CSS + three inline `<script>` IIFEs); everything else is data.

## Running locally

The page loads its data with `fetch`, so it won't work from `file://`. Serve the folder:

```
python -m http.server 8000
```

then open `http://localhost:8000`. Deployment is just pushing to `main` (GitHub Pages, root folder; `.nojekyll` must stay).

## Architecture

### Data is precomputed, not calculated

The site does **not** compute the Hebrew calendar or halachic rules. `data/days.json` is a precomputed table (generated from the Tfilon app) covering 2026–2036. Extending the range means regenerating it from the app, not writing calendar code. `tachanun_logic_explained.md` is a standalone pseudocode write-up of those rules for reference only; nothing in the site uses it.

- `data/days.json`: `{start, n, toks, mkeys, vals, il, ch}`. `il` (Israel) and `ch` (diaspora) are arrays indexed by days since `start`. Each row is `[hexBitmask, markerValueIndexes[], infoStrings[]]`. Bit *k* set means condition token `toks[k]` is true that day; `markerValueIndexes[k]` indexes into `vals` for marker key `mkeys[k]` (`-1` → null). `dayData()` in `index.html` decodes a row into `{bits: Set, mk, info}`.
- `data/texts.json`: map of template name → raw text in Tfilon's line format (names like `s_shacharit`, `specials/a_mincha`, `tikun_chatzot`).
- `data/motzash.json`, `data/chanukatHabayit.json`: standalone texts keyed by nusach, loaded lazily and not run through the resolver.
- `data/z/<cityIndex>.txt`: one line per day (same index as `days.json`). The first 13 zmanim are 3-hex-digit minute values (`---` = none) in the order of `ZL.core`. These are followed by optional 4-char entries: a letter (`A`+index into `ZL.extra`) plus 3 hex digits. Times are stored in the city's standard-time offset (`CITIES[i][2]`). `zmanim()` corrects them for DST using `Intl` and the IANA zone (`CITIES[i][3]`).
- `CITIES` (inline in `index.html`): `[name, isIsrael, stdOffsetHours, ianaZone]`. The array index is the file name in `data/z/`, so never reorder it.

### Scripts in `index.html`

1. **`TfilonResolver`**: a faithful port of Tfilon's line resolver; keep its behavior identical to the original. It expands a template line by line:
   - `()name` includes template `name` unconditionally.
   - `()name COND` includes `name` only if `COND` (uppercased) is in the day's bits.
   - Lines in `MARKERS` are replaced by the day's marker value. `:::` resolves per nusach (`:::a` / `:::s`).
   - Lines starting with the `PASS` tokens are left in place for the renderer.
2. **`PdfMaker`**: client-side PDF generation with no libraries. It loads the woff2 files from `fonts/` (as `FontFace` and as base64 for embedding) and paginates text into fixed layouts (`LAYOUTS`: A4, A4 two-column, A5, booklets, imposition, and the "one double-sided sheet" fit). It rasterizes each page via SVG `foreignObject` (for correct Hebrew shaping) and writes a JPEG-based PDF by hand (`writePDF`). `calibrate()` compensates for browser text zoom.
3. **App IIFE**: state, navigation and rendering.
   - `current()` picks the day index, and switches to the *next* day after local sunset ("אור ל…") unless a manual date is set.
   - `menuItems()` builds the per-nusach prayer list, partly driven by day bits (`MUSAF`, `OMER`, `CHANUKA`).
   - `toHTML()` turns resolved lines into sections and paragraphs using the text markup:
     - `=====title` starts a section with a page break; `-----title` starts a section.
     - `(: … :)` is a note, `([ … ])` is an insertion, `(=== … ===)` and `(--- … ---)` are variants.
     - In display text, `~` is stripped, `K` becomes qamatz qatan and `;` becomes sof pasuq.
   - Views are `<div>`s toggled by `show()`, with a manual history stack hooked to `popstate`.
   - Settings (nusach, city, font size) persist in `localStorage` under `sid-*` keys.
   - PDF downloads use `window.claude.use('downloads')` when available and otherwise fall back to a normal anchor download.

## Notes

- Zmanim are informational only, and the UI says not to rely on them halachically. Keep that disclaimer.
- The code style is dense ES5 (no modules, `var`, one-line functions). Match it when editing.
