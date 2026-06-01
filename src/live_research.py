"""Lightweight live web research for Jarvis using public web pages."""

from __future__ import annotations

from html import unescape
import re
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse
from urllib.request import Request, urlopen

from src.logger import get_logger

logger = get_logger(__name__)

SEARCH_URL = "https://html.duckduckgo.com/html/?q={query}"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0 Safari/537.36"
    )
}

RESULT_BLOCK_RE = re.compile(
    r'<div class="result results_links results_links_deep web-result ">(.*?)</div>\s*</div>',
    re.IGNORECASE | re.DOTALL,
)
TITLE_RE = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
SNIPPET_RE = re.compile(
    r'<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
DISPLAY_URL_RE = re.compile(
    r'<a[^>]+class="result__url"[^>]*>(?P<display>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
SCRIPT_STYLE_RE = re.compile(r"<(script|style|noscript).*?>.*?</\1>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")

CURRENT_EVENT_HINTS = (
    "current",
    "latest",
    "news",
    "recent",
    "today",
    "update",
    "what happened",
)


def _strip_html(html: str) -> str:
    """Convert a small HTML fragment into compact text."""
    cleaned = SCRIPT_STYLE_RE.sub(" ", html or "")
    cleaned = re.sub(r"</(p|div|section|article|li|h\d)>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<br\s*/?>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = TAG_RE.sub(" ", cleaned)
    cleaned = unescape(cleaned)
    cleaned = cleaned.replace("\xa0", " ")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*", "\n", cleaned)
    return cleaned.strip()


def _clip_text(text: str, limit: int = 280) -> str:
    """Return a single-line clipped summary string."""
    normalized = WHITESPACE_RE.sub(" ", str(text or "")).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _decode_duckduckgo_href(href: str) -> str:
    """Resolve DuckDuckGo redirect links into direct URLs."""
    href = unescape(href or "").strip()
    if href.startswith("//"):
        href = f"https:{href}"

    parsed = urlparse(href)
    if "duckduckgo.com" not in parsed.netloc:
        return href

    query = parse_qs(parsed.query or "")
    direct = query.get("uddg", [None])[0]
    return direct or href


def _is_allowed_url(url: str) -> bool:
    """Keep research requests on normal public HTTP(S) pages only."""
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def looks_like_live_research_request(text: str) -> bool:
    """Heuristically detect requests that likely want fresh internet info."""
    lower = " ".join(str(text or "").lower().split())
    if not lower:
        return False

    words = set(re.findall(r"[a-z0-9_]+", lower))
    for hint in CURRENT_EVENT_HINTS:
        if " " in hint:
            if hint in lower:
                return True
            continue
        if hint in words:
            return True
    return False


class WebResearcher:
    """Search the web and fetch compact source excerpts for Jarvis."""

    def __init__(self, timeout: int = 12):
        self.timeout = timeout

    def _fetch_text(self, url: str) -> str:
        request = Request(url, headers=DEFAULT_HEADERS)
        with urlopen(request, timeout=self.timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                return ""
            html = response.read().decode("utf-8", errors="ignore")
        return html

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Fetch a small set of public search results."""
        url = SEARCH_URL.format(query=quote_plus(query))
        html = self._fetch_text(url)
        results = []

        for block in RESULT_BLOCK_RE.findall(html):
            title_match = TITLE_RE.search(block)
            if not title_match:
                continue

            source_url = _decode_duckduckgo_href(title_match.group("href"))
            if not _is_allowed_url(source_url):
                continue

            snippet_match = SNIPPET_RE.search(block)
            display_match = DISPLAY_URL_RE.search(block)
            title = _clip_text(_strip_html(title_match.group("title")), limit=140)
            snippet = _clip_text(
                _strip_html(snippet_match.group("snippet")) if snippet_match else "",
                limit=220,
            )
            display_url = _clip_text(
                _strip_html(display_match.group("display")) if display_match else urlparse(source_url).netloc,
                limit=120,
            )

            results.append({
                "title": title or source_url,
                "url": source_url,
                "display_url": display_url,
                "snippet": snippet,
            })

            if len(results) >= limit:
                break

        return results

    def fetch_source_excerpt(self, url: str, max_chars: int = 1800) -> str:
        """Fetch and extract readable text from a web page."""
        if not _is_allowed_url(url):
            raise ValueError("Only http and https URLs are supported for live research")

        html = self._fetch_text(url)
        text = _strip_html(html)
        return _clip_text(text, limit=max_chars)

    def research(self, query: str, result_limit: int = 5, fetch_limit: int = 3) -> dict | None:
        """Run live web research and prepare a prompt block for grounded answers."""
        cleaned_query = WHITESPACE_RE.sub(" ", str(query or "")).strip()
        if not cleaned_query:
            raise ValueError("Research query is required")

        search_results = self.search(cleaned_query, limit=result_limit)
        if not search_results:
            return None

        sources = []
        for index, result in enumerate(search_results[:fetch_limit], start=1):
            excerpt = ""
            try:
                excerpt = self.fetch_source_excerpt(result["url"], max_chars=1400)
            except Exception as exc:  # pragma: no cover - network failures are expected sometimes
                logger.warning(f"Could not fetch research source {result['url']}: {exc}")

            sources.append({
                "id": index,
                **result,
                "excerpt": excerpt or result["snippet"],
            })

        prompt_lines = [
            "Live web research is attached for this turn.",
            "Use the sources below when they help, and cite claims with bracketed source numbers like [1] or [2].",
            f"Research query: {cleaned_query}",
        ]

        for source in sources:
            prompt_lines.extend([
                "",
                f"[{source['id']}] {source['title']}",
                f"URL: {source['url']}",
                f"Snippet: {source['snippet']}",
                f"Excerpt: {source['excerpt']}",
            ])

        return {
            "query": cleaned_query,
            "sources": sources,
            "summary": f"Loaded {len(sources)} live web sources for '{cleaned_query}'.",
            "prompt_block": "\n".join(prompt_lines).strip(),
        }


web_researcher = WebResearcher()
