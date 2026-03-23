"""Parse Google People Also Ask (PAA) data from SERP HTML. Uses layered fallbacks for selector resilience."""

import logging
import re
from typing import Any

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Schema: {question, answer, source_url, children?}
PAA_ITEM = dict[str, Any]


def parse_paa(html: str, source_url: str = "") -> list[PAA_ITEM]:
    """
    Extract PAA questions, answers, and source URLs from Google SERP HTML.

    Uses layered fallback selectors because Google frequently changes DOM structure.
    Extracts visible questions; answers appear when PAA items are expanded.

    Args:
        html: Raw HTML from Google search results page.
        source_url: URL of the search (for reference).

    Returns:
        List of dicts: {question, answer, source_url, children}
    """
    soup = BeautifulSoup(html, "html.parser")
    results: list[PAA_ITEM] = []

    # Find PAA section - look for "People also ask" or similar heading
    paa_section = _find_paa_section(soup)
    if not paa_section:
        logger.debug("No PAA section found")
        return results

    # Question text selectors (layered fallbacks - Google changes these)
    question_selectors = [
        "span.CSkcDe",  # Historical Oxylabs pattern
        "[data-attrid] span",
        "div[role='button'] span",
        "div.g div span",
        "accordion-entry-search-icon ~ * span",
        ".mEUgP",
    ]

    # Container for each PAA item (Google uses data-hveid, data-ved, jsname, accordion)
    item_containers = paa_section.select(
        "div[data-hveid][data-ved], "
        "div[data-attrid], "
        "div[data-ved], "
        "div[role='button'][jsname], "
        "div.g, "
        "accordion-entry-search-icon"
    )

    seen_questions: set[str] = set()

    for container in item_containers:
        question_text = None
        for sel in question_selectors:
            el = container.select_one(sel)
            if el and el.get_text(strip=True) and len(el.get_text(strip=True)) > 10:
                question_text = el.get_text(strip=True)
                break
        if not question_text or question_text in seen_questions:
            continue

        # Skip if it looks like "People also ask" heading
        if question_text.lower().startswith("people also"):
            continue

        seen_questions.add(question_text)

        # Answer snippet (may be empty if not expanded)
        answer = _extract_answer(container)
        source_link = _extract_source_url(container)

        results.append({
            "question": question_text,
            "answer": answer or "",
            "source_url": source_link or "",
            "children": [],
        })

    return results


def _find_paa_section(soup: BeautifulSoup) -> BeautifulSoup | None:
    """Locate the PAA block. Google may wrap it differently over time."""
    # Look for text "People also ask" - go up to container that holds both heading and items
    for el in soup.find_all(string=re.compile(r"people\s+also\s+ask", re.I)):
        parent = el.parent
        if parent:
            # Go up to get the block container (items are often siblings of the heading)
            for _ in range(6):
                parent = getattr(parent, "parent", None)
                if parent and parent.name == "div":
                    # Check this container has PAA items (data-ved, CSkcDe, etc.)
                    if parent.select("div[data-ved], div[data-hveid], span.CSkcDe, div[data-attrid]"):
                        return parent
            # Fallback: return outermost div containing the heading
            parent = el.parent
            for _ in range(5):
                if parent and parent.name == "div":
                    return parent
                parent = getattr(parent, "parent", None)
    # Fallback: look for accordion-entry (PAA uses accordion UI)
    accordion = soup.select_one("accordion-entry-search-icon, [role='button'][jsname]")
    if accordion:
        parent = accordion.parent
        for _ in range(5):
            if parent and parent.name == "div":
                return parent
            parent = getattr(parent, "parent", None) if parent else None
    return None


def _extract_answer(container) -> str:
    """Extract answer snippet from expanded PAA item."""
    # Answer often in div with specific classes or data attributes
    answer_el = container.select_one(
        "div[data-attrid='wa:/description'], "
        "div.s span, "
        ".s3v9rd, "
        "div[data-sncf]"
    )
    if answer_el:
        return answer_el.get_text(separator=" ", strip=True)[:500]
    return ""


def _extract_source_url(container) -> str:
    """Extract source URL from PAA item."""
    link = container.select_one("a[href^='http']")
    if link and link.get("href"):
        href = link["href"]
        # Skip Google redirect URLs
        if "google.com" not in href.split("/")[2]:
            return href
    return ""
