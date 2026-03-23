"""
CLI entry point for Google People Also Ask (PAA) scraping.

Usage:
    python main.py "search query" [--country US] [--output output.json]
    python main.py "how to scrape google" --country US
"""
import argparse
import json
import logging
import sys
from urllib.parse import quote_plus, urlencode

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_TIMEOUT_SECONDS,
    RETRY_ATTEMPTS,
    RETRY_MAX_WAIT_SECONDS,
    RETRY_MIN_WAIT_SECONDS,
    get_token,
)
from fetcher import fetch_page
from parser import parse_paa

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_serp_url(query: str, country: str = "us", lang: str = "en") -> str:
    """Build Google search URL with geo parameters."""
    base = "https://www.google.com/search"
    params = {"q": query}
    if country:
        params["gl"] = country.lower()
    if lang:
        params["hl"] = lang.lower()
    return f"{base}?{urlencode(params)}"


def scrape_paa(
    query: str,
    *,
    country: str = "us",
    lang: str = "en",
    output_path: str = DEFAULT_OUTPUT_PATH,
    page_wait: int = 2000,
) -> int:
    """
    Scrape PAA data for a query and write to JSON.

    Returns:
        Number of PAA items extracted.
    """
    get_token()
    url = build_serp_url(query, country=country, lang=lang)

    @retry(
        stop=stop_after_attempt(RETRY_ATTEMPTS),
        wait=wait_exponential(
            min=RETRY_MIN_WAIT_SECONDS,
            max=RETRY_MAX_WAIT_SECONDS,
        ),
        retry=retry_if_exception_type((ConnectionError,)),
        reraise=True,
    )
    def _fetch() -> str:
        return fetch_page(
            url,
            page_wait=page_wait,
            use_js=True,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )

    html = _fetch()
    items = parse_paa(html, source_url=url)

    output = {
        "query": query,
        "country": country,
        "url": url,
        "paa": items,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info("Extracted %d PAA items for '%s'", len(items), query)
    return len(items)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scrape Google People Also Ask via Crawlbase Crawling API."
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--country",
        default="us",
        help="Country code for geo-targeting (default: us)",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="Language code (default: en)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output JSON path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--page-wait",
        type=int,
        default=2000,
        help="Milliseconds to wait for dynamic content (default: 2000)",
    )
    args = parser.parse_args()

    count = scrape_paa(
        args.query,
        country=args.country,
        lang=args.lang,
        output_path=args.output,
        page_wait=args.page_wait,
    )
    logger.info("Written to %s", args.output)
    return 0 if count >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
