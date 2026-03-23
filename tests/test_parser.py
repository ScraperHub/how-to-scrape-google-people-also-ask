"""Tests for PAA parser."""
import pytest

from parser import parse_paa


def test_parse_paa_extracts_questions(paa_fixture_html: str) -> None:
    """Parser extracts at least 2 questions from realistic PAA HTML."""
    items = parse_paa(paa_fixture_html, source_url="https://google.com/search?q=test")
    assert len(items) >= 2
    questions = [i["question"] for i in items]
    assert any("web scraping" in q.lower() for q in questions)


def test_parse_paa_extracts_answer_when_present(paa_fixture_html: str) -> None:
    """Parser extracts answer snippet when present in HTML."""
    items = parse_paa(paa_fixture_html)
    with_answer = [i for i in items if i.get("answer")]
    assert len(with_answer) >= 1
    assert "extracting" in with_answer[0]["answer"].lower() or "scraping" in with_answer[0]["answer"].lower()


def test_parse_paa_extracts_source_url(paa_fixture_html: str) -> None:
    """Parser extracts source URL and skips google.com links."""
    items = parse_paa(paa_fixture_html)
    with_url = [i for i in items if i.get("source_url")]
    assert len(with_url) >= 1
    assert with_url[0]["source_url"].startswith("https://")
    assert "google.com" not in with_url[0]["source_url"]


def test_parse_paa_returns_empty_when_no_section() -> None:
    """Parser returns empty list when PAA section is absent."""
    html = "<html><body><div>No People also ask here</div></body></html>"
    assert parse_paa(html) == []
