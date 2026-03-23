"""Configuration for the PAA scraper. Token from env; do not hardcode."""

import os

# Crawlbase API (https://crawlbase.com/docs/crawling-api/)
CRAWLBASE_API_BASE = "https://api.crawlbase.com/"
CRAWLBASE_TOKEN = os.environ.get("CRAWLBASE_TOKEN")

# Use JavaScript token for Google SERPs (JS-rendered)
CRAWLBASE_JS_TOKEN = os.environ.get("CRAWLBASE_JS_TOKEN") or CRAWLBASE_TOKEN

# Timeout: 90s recommended per Crawlbase docs
DEFAULT_TIMEOUT_SECONDS = 90

# Response validation
MIN_RESPONSE_LENGTH = 100

# Output
DEFAULT_OUTPUT_PATH = "output.json"

# Retries for transient API errors
RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT_SECONDS = 2
RETRY_MAX_WAIT_SECONDS = 10


def get_token(use_js: bool = True) -> str:
    """Return Crawlbase token from environment. Raises if missing."""
    token = CRAWLBASE_JS_TOKEN if use_js else CRAWLBASE_TOKEN
    if not token or not str(token).strip():
        raise ValueError(
            "CRAWLBASE_TOKEN or CRAWLBASE_JS_TOKEN is not set. Set it in your environment."
        )
    return str(token).strip()
