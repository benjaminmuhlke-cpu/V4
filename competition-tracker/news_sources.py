"""Loader for news_sources.yaml - the curated industry/luxury/beauty/
travel-retail news sources that complement (never replace) official brand
sources in the recent-openings discovery workflow. See news_sources.yaml's
own header for the exact schema and SOURCE_PRIORITY tiers.

This module only reads the config; it does not perform any live search
(same reasoning as online_research.py - no search API key available to
this script, see that module's docstring).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent
NEWS_SOURCES_PATH = BASE_DIR / "news_sources.yaml"

CATEGORIES = (
    "OFFICIAL_BRAND", "OFFICIAL_MALL_OR_LANDLORD", "INDUSTRY_NEWS",
    "LUXURY_NEWS", "BEAUTY_NEWS", "TRAVEL_RETAIL_NEWS", "LINKEDIN", "OTHER",
)


def slugify(name: str) -> str:
    """A curated source's name -> the source_type slug used to tag cache
    entries (data/online_research_cache.json) and to key
    recent_openings.py's priority/gating maps - one deterministic
    derivation, so news_sources.yaml stays the single source of truth for
    both the source's display name and its code-facing identifier."""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug


def load_news_sources(path: Path | str = NEWS_SOURCES_PATH) -> list[dict]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return data.get("sources", [])


def source_type_slugs(sources: list[dict] | None = None) -> dict[str, str]:
    """{source name -> source_type slug} for every curated source."""
    sources = sources if sources is not None else load_news_sources()
    return {source["name"]: slugify(source["name"]) for source in sources}


def source_priorities(sources: list[dict] | None = None) -> dict[str, int]:
    """{source_type slug -> SOURCE_PRIORITY} for every curated source -
    merged into recent_openings.py's priority map so a cached finding
    citing one of these outlets ranks the same simple, deterministic way
    as an official source, just at its documented tier."""
    sources = sources if sources is not None else load_news_sources()
    return {slugify(source["name"]): source["priority"] for source in sources}
