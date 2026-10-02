# Feature: Visual HTML report (ofertas.html)

## Objective
Generate `ofertas.html` — a visual card-grid report with product images and category sections — from the scraper state, alongside the existing `ofertas.md`.

## Problem
`ofertas.md` and `state.json` are text/JSON only. Offers are hard to scan visually.

## Why
User wants product images and category division to browse offers faster. Scraper runs elsewhere (GitHub Actions); outputs must be produced by the pipeline.

## Scope
- Extract `image_url` and `category` in `parser.py`
- Persist both on product records in `state.py` (and backfill in `update_product`)
- New `html_report.py` rendering `ofertas.html` from the state dict
- Wire into `scraper.py` run + `config.py` + `.github/workflows/scrape.yml`
- Keep `ofertas.md` output unchanged (HTML is additive)

## Out of scope
- Multi-category scraping (still one category URL)
- Replacing markdown/state outputs
- New dependencies

## Constraints
- No new dependencies (stdlib + existing only)
- HTML UI copy in Spanish (project language); code comments match file style
- Category = leaf URL path segment before the product file (e.g. `ropa-escalada`), display title-cased
- Image = first product `img`, prefer `data-src` (lazyload) over `src`; skip `data:` placeholders
- Old state entries without image/category must render with a placeholder and `Sin categoría`
- Minimal diff. No abstractions for one use. No frameworks.

## Authorized scope
Repository `blackisard-scraper`, branch `feat/html-ofertas`. Work-unit commits authorized; push/PR/merge stay with the user.

## TDD
- Mode: **off** (no project TDD config; test framework presence alone does not enable TDD)
- Source: no session/project TDD setting found
- Test runner: `python -m pytest`

## Tasks
- [x] T1 parser+state: extract and persist `image_url`, `category`
      route: delegated | commit evidence: ca8f997
- [x] T2 `html_report.py`: generate `ofertas.html` from state (cards, images, category sections, offer history in `<details>`, `__main__` self-check)
      route: delegated | commit evidence: 60966e9
- [x] T3 wire-up: `config.HTML_OUTPUT_FILE`, `scraper.py` hook, workflow artifacts + commit
      route: delegated | commit evidence: 6506a82

## Acceptance criteria
- `python html_report.py` self-check passes
- `python -m pytest test_parser.py test_state.py test_formatter.py -q` passes
- `ofertas.html` contains product images, category sections, prices and discount badges

## Applicable checks
- `python -m pytest test_parser.py test_state.py test_formatter.py -q`
- `python html_report.py`

## Progress
- T1 done (ca8f997): `extract_image_url` / `extract_category` in `parser.py`, persisted + backfilled in `state.py`.
- T2 done (60966e9): `html_report.py` with `generate()`, category sections, product cards, offer history, inline CSS, `__main__` self-check.
- T3 done (6506a82): `config.HTML_OUTPUT_FILE`, `scraper.py` hook after markdown report, workflow artifact + `git add` include `ofertas.html`.

## Verification evidence
- `python -m pytest test_parser.py test_state.py test_formatter.py -q` → `45 passed in 0.09s`
- `python html_report.py` → `Test del generador HTML` / `OK` (exit 0)

## Next step
None — feature complete on `feat/html-ofertas`. Push/PR left to the user.
