"""Brand coverage audit: for each brand in brands.yaml, an honest account
of what its official source can and can't give us. No new scraping or
parsing logic - this is purely a reporting layer over what brands.yaml
already declares and what aggregate.py's process_brand() already computed,
so a brand's story stays in one place instead of being re-derived twice.
"""

from __future__ import annotations

import re
from datetime import date

from region_mapping import REGIONS

AUDIT_COLUMNS = [
    "BRAND", "OFFICIAL_SOURCE", "SOURCE_TYPE", "ACCESSIBLE", "STORE_LEVEL_DATA",
    "COUNTRY_DATA", "CITY_DATA", "ADDRESS_DATA", "REGIONAL_TOTALS", "WORLDWIDE_TOTAL",
    "PHOTOS_AVAILABLE", "MIXES_WHOLESALE", "FSS_FILTER_RELIABLE",
    *(f"{r}_STATUS" for r in REGIONS),
    "OVERALL_STATUS", "CONFIDENCE", "MISSING_DATA", "MANUAL_ACTION_REQUIRED", "LAST_CHECKED",
]

FAILURE_COLUMNS = [
    "BRAND", "OFFICIAL_URL", "HTTP_STATUS", "ERROR_TYPE", "ERROR_MESSAGE",
    "FALLBACK_RESEARCH_RUN", "FALLBACK_RESULT", "LAST_CHECKED",
]

# Confidence labels used everywhere else in the codebase are French
# (haute/moyenne/manuelle) - this audit's spec asks for English, so map
# rather than introduce a second confidence vocabulary throughout the code.
CONFIDENCE_EN = {"haute": "high", "moyenne": "medium", "manuelle": "low"}

# Below this ratio of name-ambiguous entries (store name didn't obviously
# match the brand - the FSS-vs-wholesale signal, not a geography lookup
# gap) to raw scraped entries, a "moyenne" confidence source's FSS filter
# is still considered usable without heavier manual review.
MAX_AMBIGUOUS_RATIO_FOR_RELIABLE = 0.3


def _region_status(brand_result: dict, region: str) -> str:
    if brand_result["status"] != "ok":
        return "not_checked"
    value = brand_result["regions"].get(region)
    if value is None:
        return "not_checked"
    return "found" if value > 0 else "zero"


def _has_field(brand_result: dict, field: str) -> bool:
    return any(s.get(field) for s in (brand_result.get("stores") or []))


def _fss_filter_reliable(brand_result: dict, brand_config: dict) -> bool:
    if brand_config["scraper_type"] == "manual" or brand_result["status"] != "ok":
        return False
    confidence = brand_config.get("confidence")
    if confidence == "manuelle":
        return False
    if confidence == "haute":
        return True
    stats = brand_result.get("scrape_stats") or {}
    if stats.get("included_count") is None:
        # Aggregate-only source (e.g. Diptyque's per-country totals): no
        # per-store FSS-vs-wholesale classification ever runs here, so
        # there's no filter to vouch for outside "haute" confidence.
        return False
    raw = stats.get("raw_count") or 0
    name_ambiguous = stats.get("name_ambiguous_count") or 0
    return raw > 0 and (name_ambiguous / raw) < MAX_AMBIGUOUS_RATIO_FOR_RELIABLE


def _overall_status(brand_result: dict, brand_config: dict) -> str:
    """Data completeness for this run - deliberately independent of
    CONFIDENCE (a separate column): a "moyenne" source that scraped fully
    and untruncated this time is "complete" for this audit's purposes, same
    as a "haute" one. Confidence is about how much to trust the FSS
    classification; this is about whether we got a full read this run.
    """
    if brand_config["scraper_type"] == "manual" or brand_result["status"] == "manual":
        return "manual"
    if brand_result["status"] == "error":
        return "failed"
    return "partial" if brand_result.get("partial") else "complete"


def _mixes_wholesale(brand_result: dict, brand_config: dict) -> bool:
    stats = brand_result.get("scrape_stats") or {}
    if (stats.get("blocklist_excluded_count") or 0) > 0:
        return True
    notes = (brand_config.get("notes") or "").lower()
    return any(kw in notes for kw in ("wholesale", "revendeur", "multi-marques", "multi marques"))


def _missing_data_reason(brand_result: dict, brand_config: dict) -> str:
    if brand_config["scraper_type"] == "manual":
        return "Pas de scraper automatise - aucune donnee en direct pour cette marque"
    if brand_result["status"] == "error":
        return f"Scraper en echec : {brand_result.get('error')}"
    if brand_result.get("partial"):
        return "Resultat scraper probablement tronque (plafond de resultats atteint sur une requete)"
    stats = brand_result.get("scrape_stats") or {}
    if stats.get("included_count") is None:
        # Generalizes to any current/future aggregate-only source (only
        # Diptyque today), not just that one parser by name.
        return "La source ne donne que des totaux agreges (par pays), pas le detail par boutique"
    missing_regions = [r for r in REGIONS if _region_status(brand_result, r) == "zero"]
    if missing_regions:
        return f"Zero boutique trouvee dans : {', '.join(missing_regions)} (a confirmer que la marque n'y est vraiment pas presente)"
    return ""


def _manual_action(brand_result: dict, brand_config: dict) -> str:
    if brand_config["scraper_type"] == "manual":
        return "Confirmer le total par verification manuelle ou email aux equipes regionales"
    if brand_result["status"] == "error":
        return "Reessayer plus tard, ou verifier a la main si l'URL/la structure du site a change"
    if brand_config.get("confidence") != "haute":
        return "Revoir _a_verifier.csv pour confirmer le filtre FSS vs wholesale avant d'utiliser ce chiffre"
    return ""


def build_audit_row(brand_config: dict, brand_result: dict, checked_date: date | None = None) -> dict:
    checked_date = checked_date or date.today()
    return {
        "BRAND": brand_config["name"],
        "OFFICIAL_SOURCE": brand_config["store_locator_url"],
        "SOURCE_TYPE": brand_config["scraper_type"],
        "ACCESSIBLE": brand_result["status"] == "ok",
        "STORE_LEVEL_DATA": bool(brand_result.get("stores")),
        "COUNTRY_DATA": _has_field(brand_result, "country"),
        "CITY_DATA": _has_field(brand_result, "city"),
        "ADDRESS_DATA": _has_field(brand_result, "address"),
        "REGIONAL_TOTALS": brand_result["status"] == "ok",
        "WORLDWIDE_TOTAL": brand_result.get("total") is not None,
        "PHOTOS_AVAILABLE": _has_field(brand_result, "image_url"),
        "MIXES_WHOLESALE": _mixes_wholesale(brand_result, brand_config),
        "FSS_FILTER_RELIABLE": _fss_filter_reliable(brand_result, brand_config),
        **{f"{r}_STATUS": _region_status(brand_result, r) for r in REGIONS},
        "OVERALL_STATUS": _overall_status(brand_result, brand_config),
        "CONFIDENCE": CONFIDENCE_EN.get(brand_config.get("confidence"), "low"),
        "MISSING_DATA": _missing_data_reason(brand_result, brand_config),
        "MANUAL_ACTION_REQUIRED": _manual_action(brand_result, brand_config),
        "LAST_CHECKED": checked_date.isoformat(),
    }


def build_coverage_audit(brands: list[dict], results: list[dict], checked_date: date | None = None) -> list[dict]:
    results_by_slug = {r["slug"]: r for r in results}
    rows = []
    for brand_config in brands:
        result = results_by_slug.get(brand_config["slug"])
        if result is None:
            continue  # not part of this run's --brands scope
        rows.append(build_audit_row(brand_config, result, checked_date))
    return rows


def needs_manual_follow_up(audit_row: dict) -> bool:
    return audit_row["OVERALL_STATUS"] != "complete" or not audit_row["FSS_FILTER_RELIABLE"]


def build_manual_follow_up(audit_rows: list[dict]) -> list[dict]:
    return [row for row in audit_rows if needs_manual_follow_up(row)]


_HTTP_STATUS_RE = re.compile(r"HTTP (\d{3})")


def _classify_error(error_message: str) -> tuple[str | None, str]:
    if not error_message:
        return None, "unknown"
    match = _HTTP_STATUS_RE.search(error_message)
    if match:
        return match.group(1), "http_error"
    if "robots.txt" in error_message:
        return None, "robots_disallowed"
    if "network error" in error_message:
        return None, "network_error"
    if "zero" in error_message.lower() or "yielded" in error_message.lower():
        return None, "empty_result"
    return None, "unknown"


def build_source_failures(
    brands: list[dict],
    results: list[dict],
    fallback_summary: dict[str, dict] | None = None,
    checked_date: date | None = None,
) -> list[dict]:
    """One row per brand whose scraper failed this run. fallback_summary
    (brand display name -> {"ran": bool, "result": str}, as returned by
    online_research.fallback_summary_by_brand()) is filled in after online
    fallback research runs, if it does - left blank/False otherwise."""
    fallback_summary = fallback_summary or {}
    checked_date = checked_date or date.today()
    configs_by_slug = {b["slug"]: b for b in brands}

    rows = []
    for result in results:
        if result["status"] != "error":
            continue
        brand_config = configs_by_slug.get(result["slug"], {})
        http_status, error_type = _classify_error(result.get("error") or "")
        fallback = fallback_summary.get(result["brand"], {})
        rows.append({
            "BRAND": result["brand"],
            "OFFICIAL_URL": brand_config.get("store_locator_url"),
            "HTTP_STATUS": http_status,
            "ERROR_TYPE": error_type,
            "ERROR_MESSAGE": result.get("error"),
            "FALLBACK_RESEARCH_RUN": fallback.get("ran", False),
            "FALLBACK_RESULT": fallback.get("result", ""),
            "LAST_CHECKED": checked_date.isoformat(),
        })
    return rows
