"""Fetch curated external sources — no LLM, no direct model access."""

from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
import json
from typing import Any
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from src.ugr.ingestion.config import IngestionSource


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def _fetch_url(url: str, *, timeout: float = 20.0) -> str:
    req = Request(url, headers={"User-Agent": "project-infi-ugr-ingestion/0.1"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_arxiv(source: IngestionSource) -> list[dict[str, Any]]:
    feed_url = str(source.options.get("feed_url") or "")
    if not feed_url:
        return []
    xml_text = _fetch_url(feed_url)
    root = ET.fromstring(xml_text)
    records: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        entry_id = (entry.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
        title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").strip()
        published = (entry.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()
        tags = [
            cat.attrib.get("term", "")
            for cat in entry.findall("atom:category", ATOM_NS)
            if cat.attrib.get("term")
        ]
        records.append(
            {
                "source_uri": entry_id,
                "title": title,
                "summary": summary,
                "published_at": published or datetime.now(UTC).isoformat(),
                "tags": tags,
                "actors": ["arxiv"],
            }
        )
    max_results = int(source.options.get("max_results") or 5)
    return records[:max_results]


def fetch_github_releases(source: IngestionSource) -> list[dict[str, Any]]:
    repo = str(source.options.get("repo") or "").strip()
    if not repo:
        return []
    limit = int(source.options.get("limit") or 3)
    url = f"https://api.github.com/repos/{repo}/releases?per_page={max(1, limit)}"
    payload = json.loads(_fetch_url(url))
    records: list[dict[str, Any]] = []
    for item in payload if isinstance(payload, list) else []:
        records.append(
            {
                "source_uri": str(item.get("html_url") or item.get("url") or ""),
                "title": str(item.get("name") or item.get("tag_name") or "release"),
                "summary": str(item.get("body") or "")[:500],
                "published_at": str(item.get("published_at") or datetime.now(UTC).isoformat()),
                "tags": ["github", "release"],
                "actors": [repo.split("/")[0] if "/" in repo else repo],
            }
        )
    return records[:limit]


def fetch_rss(source: IngestionSource) -> list[dict[str, Any]]:
    feed_url = str(source.options.get("url") or "")
    if not feed_url:
        return []
    xml_text = _fetch_url(feed_url)
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []
    records: list[dict[str, Any]] = []
    for item in channel.findall("item"):
        link = (item.findtext("link") or "").strip()
        title = (item.findtext("title") or "").strip()
        description = (item.findtext("description") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        records.append(
            {
                "source_uri": link or title,
                "title": title,
                "summary": description,
                "published_at": pub_date or datetime.now(UTC).isoformat(),
                "tags": ["rss"],
                "actors": list(source.options.get("actors") or ["rss-feed"]),
            }
        )
    max_items = int(source.options.get("max_items") or 5)
    return records[:max_items]


def fetch_source(source: IngestionSource) -> list[dict[str, Any]]:
    if source.source_type == "arxiv":
        return fetch_arxiv(source)
    if source.source_type == "github_releases":
        return fetch_github_releases(source)
    if source.source_type == "rss":
        return fetch_rss(source)
    return []
