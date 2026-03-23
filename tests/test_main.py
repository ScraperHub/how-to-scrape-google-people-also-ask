"""Tests for main module (URL builder, scrape_paa with mocked fetch)."""
from pathlib import Path
from unittest.mock import patch

import pytest

from main import build_serp_url, scrape_paa


def test_build_serp_url() -> None:
    """URL contains q, gl, hl for given query, country, lang."""
    url = build_serp_url("web scraping", country="uk", lang="en")
    assert "q=" in url
    assert "gl=uk" in url
    assert "hl=en" in url
    assert "https://www.google.com/search" in url


def test_scrape_paa_with_mocked_fetch(paa_fixture_html: str, tmp_path: Path) -> None:
    """Full pipeline works when fetch_page returns fixture HTML."""
    output_path = tmp_path / "out.json"
    with patch("main.fetch_page", return_value=paa_fixture_html):
        with patch("main.get_token", return_value="mock-token"):
            count = scrape_paa(
                "web scraping",
                country="us",
                output_path=str(output_path),
            )
    assert count >= 2
    assert output_path.exists()
    import json
    data = json.loads(output_path.read_text())
    assert data["query"] == "web scraping"
    assert data["country"] == "us"
    assert len(data["paa"]) >= 2
