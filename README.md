# PAA Scraper (blog example)

Scrapes Google People Also Ask (PAA) via the [Crawlbase Crawling API](https://crawlbase.com/docs/crawling-api/), parses questions, answers, and source URLs, and writes JSON. Supports geo-targeting via `gl`/`hl` and the [Enterprise Crawler](https://crawlbase.com/docs/crawler) for bulk scale.

Matches the blog post *How to Scrape Google People Also Ask*.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
export CRAWLBASE_TOKEN=your_normal_token
export CRAWLBASE_JS_TOKEN=your_js_token   # Required for Google SERPs
```

## Run

```bash
# Scrape PAA for a query (default: US geo)
python main.py "how to scrape google"

# With country and output
python main.py "content gap analysis" --country uk -o paa_uk.json

# Custom page wait for slower loads
python main.py "web scraping best practices" --page-wait 3000
```

## Layout

- **config.py** — Env-based config (token, API base, timeouts, retries).
- **fetcher.py** — Crawlbase Crawling API client; `fetch_page()`, `fetch_page_enterprise_crawler()`.
- **parser.py** — `parse_paa()` with layered fallback selectors for Google DOM changes.
- **main.py** — CLI; builds SERP URL, fetches via Crawlbase, parses, writes JSON.

Output is JSON: `{query, country, url, paa: [{question, answer, source_url, children}]}`.

## Tests

Run tests with realistic PAA fixture data:

```bash
python3 run_tests.py
```

Or with pytest (if installed):

```bash
python3 -m pytest tests/ -v
```
