"""Constitutional article registry."""

from __future__ import annotations

from typing import Any

from constitutional.core.articles import (
    ARTICLE_H,
    ARTICLE_JPSS,
    ARTICLE_JPSS_C,
    ARTICLE_JPSS_I,
    ARTICLE_LEGITIMACY,
    ARTICLE_P,
    ARTICLE_Q,
    ARTICLE_Q2,
    ARTICLE_Q5,
    ARTICLE_Q6,
    ARTICLE_Q7,
    ARTICLE_R,
    ARTICLE_S,
    ARTICLE_S2,
    ConstitutionalArticle,
)


class ConstitutionalRegistry:
    """In-memory registry of governed constitutional articles."""

    def __init__(self) -> None:
        self._articles: dict[str, ConstitutionalArticle] = {}
        self._by_invariant: dict[str, ConstitutionalArticle] = {}

    def register_article(self, article: ConstitutionalArticle) -> None:
        self._articles[article["id"]] = article
        if article["invariant"] not in self._by_invariant:
            self._by_invariant[article["invariant"]] = article

    def get_article(self, article_id: str) -> ConstitutionalArticle | None:
        return self._articles.get(article_id)

    def get_by_invariant(self, invariant: str) -> ConstitutionalArticle | None:
        return self._by_invariant.get(invariant)

    def list_articles(self) -> list[ConstitutionalArticle]:
        return list(self._articles.values())

    def is_non_derogable(self, article_id: str) -> bool:
        article = self.get_article(article_id)
        return bool(article and article.get("non_derogable"))

    def snapshot(self) -> dict[str, Any]:
        return {
            "articles": [dict(article) for article in self.list_articles()],
        }


constitutional_registry = ConstitutionalRegistry()
constitutional_registry.register_article(ARTICLE_R)
constitutional_registry.register_article(ARTICLE_S)
constitutional_registry.register_article(ARTICLE_P)
constitutional_registry.register_article(ARTICLE_H)
constitutional_registry.register_article(ARTICLE_Q)
constitutional_registry.register_article(ARTICLE_Q2)
constitutional_registry.register_article(ARTICLE_Q5)
constitutional_registry.register_article(ARTICLE_S2)
constitutional_registry.register_article(ARTICLE_Q6)
constitutional_registry.register_article(ARTICLE_Q7)
constitutional_registry.register_article(ARTICLE_JPSS)
constitutional_registry.register_article(ARTICLE_JPSS_I)
constitutional_registry.register_article(ARTICLE_JPSS_C)
constitutional_registry.register_article(ARTICLE_LEGITIMACY)
