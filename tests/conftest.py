"""Pytest fixtures for PAA scraper tests."""
import pathlib

import pytest


@pytest.fixture
def paa_fixture_html() -> str:
    """Load realistic PAA SERP HTML from fixtures."""
    path = pathlib.Path(__file__).parent / "fixtures" / "paa_serp.html"
    return path.read_text(encoding="utf-8")
