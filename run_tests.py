#!/usr/bin/env python3
"""Simple test runner when pytest is not available. Run: python3 run_tests.py"""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from main import build_serp_url, scrape_paa
from parser import parse_paa

FIXTURE_PATH = Path(__file__).parent / "tests" / "fixtures" / "paa_serp.html"


def load_fixture() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_parse_paa_extracts_questions() -> None:
    html = load_fixture()
    items = parse_paa(html)
    assert len(items) >= 2, f"Expected >=2 items, got {len(items)}"
    questions = [i["question"] for i in items]
    assert any("web scraping" in q.lower() for q in questions), f"Expected 'web scraping' in questions: {questions}"


def test_parse_paa_extracts_answer() -> None:
    html = load_fixture()
    items = parse_paa(html)
    with_answer = [i for i in items if i.get("answer")]
    assert len(with_answer) >= 1, f"No items with answer: {items}"
    a = with_answer[0]["answer"].lower()
    assert "extracting" in a or "scraping" in a, f"Expected answer content, got: {a[:100]}"


def test_parse_paa_extracts_source_url() -> None:
    html = load_fixture()
    items = parse_paa(html)
    with_url = [i for i in items if i.get("source_url")]
    assert len(with_url) >= 1, f"No items with source_url"
    assert with_url[0]["source_url"].startswith("https://")
    assert "google.com" not in with_url[0]["source_url"]


def test_parse_paa_empty_when_no_section() -> None:
    html = "<html><body><div>No PAA</div></body></html>"
    assert parse_paa(html) == []


def test_build_serp_url() -> None:
    url = build_serp_url("web scraping", country="uk", lang="en")
    assert "q=" in url and "gl=uk" in url and "hl=en" in url
    assert "https://www.google.com/search" in url


def test_scrape_paa_mocked() -> None:
    html = load_fixture()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        with patch("main.fetch_page", return_value=html):
            with patch("main.get_token", return_value="mock"):
                count = scrape_paa("web scraping", country="us", output_path=path)
        assert count >= 2, f"Expected >=2, got {count}"
        data = json.loads(Path(path).read_text())
        assert data["query"] == "web scraping" and len(data["paa"]) >= 2
    finally:
        Path(path).unlink(missing_ok=True)


TESTS = [
    ("parse_extracts_questions", test_parse_paa_extracts_questions),
    ("parse_extracts_answer", test_parse_paa_extracts_answer),
    ("parse_extracts_source_url", test_parse_paa_extracts_source_url),
    ("parse_empty_no_section", test_parse_paa_empty_when_no_section),
    ("build_serp_url", test_build_serp_url),
    ("scrape_paa_mocked", test_scrape_paa_mocked),
]


def main() -> int:
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"PASS {name}")
        except AssertionError as e:
            print(f"FAIL {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {name}: {e}")
            failed += 1
    print(f"\n{failed} failed, {len(TESTS) - failed} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
