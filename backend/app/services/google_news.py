"""Google News RSS integration.

Provides utility functions to fetch and parse Google News RSS feeds.
"""
import html
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from urllib.parse import quote_plus
# pyrefly: ignore [missing-impor
# pyrefly: ignore [missing-import]
import aiohttp

logger = logging.getLogger(__name__)

# Simple in-memory cache
_cache: Dict[str, Dict] = {}
CACHE_TTL = timedelta(minutes=5)
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=10)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def clean_html(raw_html: Optional[str]) -> str:
    """Remove HTML tags and decode HTML entities from text."""
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", "", raw_html)
    return html.unescape(text).strip()


async def fetch_rss(url: str) -> bytes:
    """Fetch raw XML bytes from Google News RSS feed."""
    async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT, headers=HEADERS) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.read()


def parse_rss(xml_bytes: bytes) -> List[Dict]:
    """Parse Google News RSS XML bytes into structured dictionaries."""
    root = ET.fromstring(xml_bytes)
    items = []
    for item in root.findall(".//item"):
        source_elem = item.find("source")
        items.append({
            "title": clean_html(item.findtext("title")),
            "link": item.findtext("link") or "",
            "pubDate": item.findtext("pubDate") or "",
            "description": clean_html(item.findtext("description")),
            "source": source_elem.text if source_elem is not None and source_elem.text else "",
            "source_url": source_elem.get("url", "") if source_elem is not None else "",
        })
    return items


async def get_news(query: str, max_items: int = 10) -> List[Dict]:
    """Fetch news for *query* using Google News RSS.

    Args:
        query: Search term (e.g., "Fintech India").
        max_items: Maximum number of articles to return.
    """
    cache_key = f"{query}:{max_items}".lower()
    now = datetime.now(timezone.utc)

    # Return cached if fresh
    if cache_key in _cache:
        entry = _cache[cache_key]
        if now - entry["timestamp"] < CACHE_TTL:
            return entry["data"]

    q = quote_plus(query)
    rss_url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"

    try:
        raw_xml = await fetch_rss(rss_url)
        news_items = parse_rss(raw_xml)[:max_items]
        _cache[cache_key] = {"timestamp": now, "data": news_items}
        return news_items
    except Exception as exc:
        logger.error(f"Failed to fetch Google News for query '{query}': {exc}")
        # Fallback to stale cache if available, or return empty list
        if cache_key in _cache:
            return _cache[cache_key]["data"]
        return []

