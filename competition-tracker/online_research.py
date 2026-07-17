"""Online fallback research: for brands/regions the official-source
scrapers can't reliably cover, this reads a locally-cached, curated
research file (data/online_research_cache.json) rather than performing a
live web search from inside this script.

Why a cache and not a live search: a real web search needs either a paid
API key (SerpAPI, Bing, Google Custom Search - none of which this personal,
zero-cost tool assumes access to) or scraping a search engine's results
page directly, which most engines' terms of service prohibit. So instead,
research entries are added out-of-band (by whoever/whatever does have real
web search access - a Claude Code session, a person doing the searches by
hand) via add_research_entry(), each one carrying its own URL, source type,
and confidence per the classification rules; this module's job is only to
store that faithfully and turn it into online_fallback_sources.csv.
--refresh-online-research (see run_report.py) clears the targeted brands'
cached entries so the next research pass knows to redo them - it can't
trigger a live search itself, for the same reason.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from brand_aliases import brand_match_key
from coverage_audit import needs_manual_follow_up

BASE_DIR = Path(__file__).parent
CACHE_PATH_DEFAULT = BASE_DIR / "data" / "online_research_cache.json"

FALLBACK_COLUMNS = [
    "BRAND", "REGION", "COUNTRY", "CITY", "STORE_NAME", "ADDRESS", "URL", "SOURCE_TITLE",
    "SOURCE_DOMAIN", "SOURCE_TYPE", "SOURCE_DATE", "STORE_CLASSIFICATION", "CONFIDENCE",
    "EVIDENCE", "STATUS", "VERIFICATION_NOTES", "LAST_CHECKED",
]

CONFIDENCE_LEVELS = ("high", "medium", "low")
STATUS_VALUES = ("CONFIRMED", "PROBABLE", "TO VERIFY")
CLASSIFICATION_VALUES = ("FSS", "FSF", "counter", "department store", "wholesale", "online", "unclear")


def load_cache(path: Path | str = CACHE_PATH_DEFAULT) -> dict:
    path = Path(path)
    if not path.exists():
        return {"entries": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_cache(cache: dict, path: Path | str = CACHE_PATH_DEFAULT) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def brands_needing_fallback(audit_rows: list[dict]) -> list[str]:
    """Brand names the coverage audit flags as needing follow-up - the
    candidate list for online fallback research."""
    return [row["BRAND"] for row in audit_rows if needs_manual_follow_up(row)]


def clear_brand_entries(cache: dict, brands: list[str]) -> dict:
    """Used by --refresh-online-research: drop cached entries for the given
    brands so the next research pass starts clean instead of accumulating
    stale findings alongside new ones."""
    keys = {brand_match_key(b) for b in brands}
    cache["entries"] = [e for e in cache.get("entries", []) if brand_match_key(e.get("brand", "")) not in keys]
    return cache


def add_research_entry(cache: dict, entry: dict) -> dict:
    """Append one researched finding. Validates confidence/status/
    classification against the allowed vocabulary rather than accepting
    anything silently - a typo here would otherwise surface as a blank
    cell in the CSV with no explanation."""
    if entry.get("confidence") not in CONFIDENCE_LEVELS:
        raise ValueError(f"invalid confidence {entry.get('confidence')!r} - expected one of {CONFIDENCE_LEVELS}")
    if entry.get("status") not in STATUS_VALUES:
        raise ValueError(f"invalid status {entry.get('status')!r} - expected one of {STATUS_VALUES}")
    if entry.get("store_classification") not in CLASSIFICATION_VALUES:
        raise ValueError(
            f"invalid store_classification {entry.get('store_classification')!r} - expected one of {CLASSIFICATION_VALUES}"
        )
    entry.setdefault("researched_at", date.today().isoformat())
    cache.setdefault("entries", []).append(entry)
    return cache


def build_fallback_rows(cache: dict, brands: list[str] | None = None) -> list[dict]:
    entries = cache.get("entries", [])
    if brands is not None:
        keys = {brand_match_key(b) for b in brands}
        entries = [e for e in entries if brand_match_key(e.get("brand", "")) in keys]

    return [{
        "BRAND": e.get("brand"),
        "REGION": e.get("region"),
        "COUNTRY": e.get("country"),
        "CITY": e.get("city"),
        "STORE_NAME": e.get("store_name"),
        "ADDRESS": e.get("address"),
        "URL": e.get("url"),
        "SOURCE_TITLE": e.get("source_title"),
        "SOURCE_DOMAIN": e.get("source_domain"),
        "SOURCE_TYPE": e.get("source_type"),
        "SOURCE_DATE": e.get("source_date"),
        "STORE_CLASSIFICATION": e.get("store_classification"),
        "CONFIDENCE": e.get("confidence"),
        "EVIDENCE": e.get("evidence"),
        "STATUS": e.get("status"),
        "VERIFICATION_NOTES": e.get("verification_notes"),
        "LAST_CHECKED": e.get("researched_at"),
    } for e in entries]


def fallback_summary_by_brand(cache: dict, brands: list[str]) -> dict[str, dict]:
    """{slug-agnostic brand name -> {"ran": bool, "result": str}} for
    coverage_audit.build_source_failures()'s FALLBACK_RESEARCH_RUN/RESULT
    columns."""
    summary = {}
    for brand in brands:
        entries = [e for e in cache.get("entries", []) if brand_match_key(e.get("brand", "")) == brand_match_key(brand)]
        if not entries:
            summary[brand] = {"ran": False, "result": "Aucune recherche en cache pour cette marque"}
            continue
        confirmed = sum(1 for e in entries if e.get("status") == "CONFIRMED")
        probable = sum(1 for e in entries if e.get("status") == "PROBABLE")
        to_verify = sum(1 for e in entries if e.get("status") == "TO VERIFY")
        summary[brand] = {
            "ran": True,
            "result": f"{len(entries)} source(s) trouvee(s) : {confirmed} confirmee(s), {probable} probable(s), {to_verify} a verifier",
        }
    return summary
