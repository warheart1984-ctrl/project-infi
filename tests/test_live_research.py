"""Tests for live web research helpers."""

import unittest
from unittest.mock import patch

from src.live_research import WebResearcher, looks_like_live_research_request


SEARCH_HTML = """
<div class="result results_links results_links_deep web-result ">
  <div class="links_main links_deep result__body">
    <h2 class="result__title">
      <a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fopenai.com%2Fnews%2F">OpenAI News</a>
    </h2>
    <div class="result__extras">
      <div class="result__extras__url">
        <a class="result__url" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fopenai.com%2Fnews%2F">openai.com/news/</a>
      </div>
    </div>
    <a class="result__snippet" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fopenai.com%2Fnews%2F">Latest updates from OpenAI.</a>
  </div>
</div>
"""

PAGE_HTML = """
<html>
  <body>
    <main>
      <article>
        <h1>OpenAI News</h1>
        <p>OpenAI shared a new update about its latest launch.</p>
      </article>
    </main>
  </body>
</html>
"""


class TestLiveResearch(unittest.TestCase):
    """Verify search parsing and live-research packaging."""

    def test_live_research_request_heuristic(self):
        """Fresh-info phrasing should trigger live research mode heuristically."""
        self.assertTrue(looks_like_live_research_request("What is the latest OpenAI news today?"))
        self.assertFalse(
            looks_like_live_research_request(
                "Explain where the Jarvis workspace tools live and how they connect to the chat API."
            )
        )
        self.assertFalse(looks_like_live_research_request("Help me refactor this React component."))

    def test_search_parses_duckduckgo_results(self):
        """DuckDuckGo HTML results should become clean source records."""
        researcher = WebResearcher()

        with patch.object(researcher, "_fetch_text", return_value=SEARCH_HTML):
            results = researcher.search("latest OpenAI news", limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "OpenAI News")
        self.assertEqual(results[0]["url"], "https://openai.com/news/")
        self.assertEqual(results[0]["display_url"], "openai.com/news/")

    def test_research_builds_prompt_block_with_sources(self):
        """Research results should include source excerpts and a grounding prompt."""
        researcher = WebResearcher()

        with patch.object(researcher, "search", return_value=[{
            "title": "OpenAI News",
            "url": "https://openai.com/news/",
            "display_url": "openai.com/news/",
            "snippet": "Latest updates from OpenAI.",
        }]):
            with patch.object(researcher, "fetch_source_excerpt", return_value="OpenAI shared a new update."):
                result = researcher.research("latest OpenAI news")

        self.assertEqual(result["query"], "latest OpenAI news")
        self.assertEqual(result["sources"][0]["title"], "OpenAI News")
        self.assertIn("Live web research is attached", result["prompt_block"])
        self.assertIn("[1] OpenAI News", result["prompt_block"])


if __name__ == "__main__":
    unittest.main()
