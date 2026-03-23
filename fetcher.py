"""Crawlbase Crawling API client for Google PAA scraping. Single responsibility: HTTP requests."""

import logging
from typing import Optional

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import (
    CRAWLBASE_API_BASE,
    DEFAULT_TIMEOUT_SECONDS,
    MIN_RESPONSE_LENGTH,
    RETRY_ATTEMPTS,
    RETRY_MAX_WAIT_SECONDS,
    RETRY_MIN_WAIT_SECONDS,
    get_token,
)

logger = logging.getLogger(__name__)


def fetch_page(
    url: str,
    *,
    token: Optional[str] = None,
    page_wait: Optional[int] = None,
    css_click_selector: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    use_js: bool = True,
) -> str:
    """
    Request page HTML from Crawlbase Crawling API.

    For Google SERPs, use JS token and page_wait for dynamic PAA content.
    Use css_click_selector to simulate clicks on PAA expand buttons for nested questions.

    Args:
        url: Target URL to fetch (e.g. Google search URL).
        token: API token (default: from env via get_token).
        page_wait: Milliseconds to wait for dynamic content (JS token only).
        css_click_selector: CSS selector(s) to click before capture. Use pipe (|) for multiple.
        timeout: Request timeout in seconds.
        use_js: Use JavaScript token for JS-rendered pages (required for Google).

    Returns:
        Raw HTML string.

    Raises:
        ValueError: Empty or too-small response.
        requests.RequestException: On HTTP errors.
    """
    token = token or get_token(use_js=use_js)
    params: dict[str, str | int | bool] = {
        "token": token,
        "url": url,
    }
    if page_wait is not None:
        params["page_wait"] = page_wait
    if css_click_selector:
        params["css_click_selector"] = css_click_selector

    resp = requests.get(
        CRAWLBASE_API_BASE,
        params=params,
        timeout=timeout,
    )
    resp.raise_for_status()

    text = resp.text
    if not text or len(text.strip()) < MIN_RESPONSE_LENGTH:
        raise ValueError("Empty or too small response")

    return text


def fetch_page_enterprise_crawler(
    url: str,
    crawler_name: str,
    *,
    token: Optional[str] = None,
    page_wait: Optional[int] = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    use_js: bool = True,
) -> dict:
    """
    Push URL to Crawlbase Enterprise Crawler (async, webhook delivery).

    Add callback=true and crawler=Name to receive results via webhook.
    Returns Request ID (rid) immediately; HTML delivered to your webhook later.

    See: https://crawlbase.com/docs/crawler
    """
    token = token or get_token(use_js=use_js)
    params: dict[str, str | int | bool] = {
        "token": token,
        "url": url,
        "callback": True,
        "crawler": crawler_name,
    }
    if page_wait is not None:
        params["page_wait"] = page_wait

    resp = requests.get(
        CRAWLBASE_API_BASE,
        params=params,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()
