"""Brand-specific FSS/FSF classification: reads fss_classification_rules.yaml
and applies a deterministic, ordered rule check to each raw scraped
location. No ML, no plugin system - just pattern lists read from YAML and
checked in a fixed priority order (see the YAML file's own header comment
for the exact order and rationale).

Deliberately does NOT classify a location as FSS just because the brand's
name appears in it - only an explicit pattern/exact match does that. Any
location matching nothing gets UNCLEAR + manual_review_required=True rather
than a guess.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from normalize import normalize

BASE_DIR = Path(__file__).parent
RULES_PATH = BASE_DIR / "fss_classification_rules.yaml"

CATEGORIES = (
    "FSS", "FSF", "DEPARTMENT_STORE", "PERFUMERY", "MULTIBRAND_RETAILER",
    "CORNER_OR_CONCESSION", "ONLINE", "UNCLEAR",
)

# Categories that count towards a brand's FSS/FSF total.
FSS_CATEGORIES = ("FSS", "FSF")


def load_rules(path: Path | str = RULES_PATH) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return {brand: cfg for brand, cfg in data.items() if not brand.startswith("_")}


def _matches_any(patterns: list[str], haystack_norm: str) -> str | None:
    for pattern in patterns:
        if normalize(pattern) and normalize(pattern) in haystack_norm:
            return pattern
    return None


def _result(record: dict, category: str, reason: str, rule: str | None, confidence: str, manual_review: bool) -> dict:
    return {
        "raw_store_name": record.get("name"),
        "raw_address": record.get("address") or record.get("city_postal"),
        "city": record.get("city"),
        "country": record.get("country"),
        "official_source_url": record.get("source"),
        "source_location_id": record.get("source_location_id"),
        "classification": category,
        "classification_reason": reason,
        "rule_matched": rule,
        "confidence": confidence,
        "manual_review_required": manual_review,
    }


def classify_location(record: dict, brand_slug: str, rules: dict) -> dict:
    """Classify one raw location record into one of CATEGORIES.

    rules is the dict returned by load_rules() (brand slug -> pattern
    lists). A brand with no entry in the YAML gets everything UNCLEAR -
    that's a config gap, not something to guess around.
    """
    brand_rules = rules.get(brand_slug)
    if brand_rules is None:
        return _result(record, "UNCLEAR", f"aucune regle configuree pour la marque '{brand_slug}'", None, "basse", True)

    name = record.get("name") or ""
    address = record.get("address") or record.get("city_postal") or ""
    city = record.get("city") or ""
    name_norm = normalize(name)
    combined_norm = normalize(f"{name} {address}")

    # 1. Curated, human-confirmed exact matches (highest priority, highest confidence).
    for exact in brand_rules.get("exact_inclusions", []):
        if normalize(exact) == name_norm:
            return _result(record, "FSS", f"nom exact repertorie comme boutique : '{exact}'", "exact_inclusions", "haute", False)
    for addr in brand_rules.get("known_fss_addresses", []):
        if normalize(addr) and normalize(addr) in combined_norm:
            return _result(record, "FSS", f"adresse repertoriee comme boutique : '{addr}'", "known_fss_addresses", "haute", False)

    # 2. Exceptions that rescue a location from the exclusion patterns below
    #    (a mall/location that looks generic but is a confirmed dedicated
    #    boutique - "a mall address can still be an FSS").
    exception_hit = _matches_any(brand_rules.get("mall_or_location_exceptions", []), combined_norm)
    if exception_hit:
        return _result(record, "FSS", f"exception connue (mall/emplacement) : '{exception_hit}'", "mall_or_location_exceptions", "moyenne", True)

    # 3. Curated non-FSS exact matches. No target category is specified in
    #    the YAML for these (they're a flat list), so both default to a
    #    conservative bucket with manual_review_required=True rather than
    #    guessing a precise category from text alone.
    for exact in brand_rules.get("exact_exclusions", []):
        if normalize(exact) and normalize(exact) in name_norm:
            return _result(record, "UNCLEAR", f"exclusion exacte connue : '{exact}' - categorie precise a confirmer", "exact_exclusions", "moyenne", True)
    for addr in brand_rules.get("known_non_fss_addresses", []):
        if normalize(addr) and normalize(addr) in combined_norm:
            return _result(record, "CORNER_OR_CONCESSION", f"adresse connue comme corner/concession : '{addr}'", "known_non_fss_addresses", "moyenne", True)

    # 4-6. Pattern-based exclusions, most to least specific.
    hit = _matches_any(brand_rules.get("retailer_blocklist", []), name_norm)
    if hit:
        return _result(record, "MULTIBRAND_RETAILER", f"correspond au blocklist revendeur : '{hit}'", "retailer_blocklist", "haute", False)

    hit = _matches_any(brand_rules.get("department_store_patterns", []), name_norm)
    if hit:
        return _result(record, "DEPARTMENT_STORE", f"correspond a un grand magasin connu : '{hit}'", "department_store_patterns", "haute", False)

    hit = _matches_any(brand_rules.get("perfumery_patterns", []), name_norm)
    if hit:
        return _result(record, "PERFUMERY", f"correspond a une parfumerie independante : '{hit}'", "perfumery_patterns", "haute", False)

    # Online markers.
    if normalize(city) == "online" or ".com" in name.lower() or ".com" in address.lower():
        return _result(record, "ONLINE", "ville/nom/adresse indique une vente en ligne", "online_marker", "haute", False)

    # 7-8. Brand's own boutique/flagship naming conventions.
    hit = _matches_any(brand_rules.get("flagship_name_patterns", []), name_norm)
    if hit:
        return _result(record, "FSF", f"correspond au motif flagship : '{hit}'", "flagship_name_patterns", "moyenne", False)

    hit = _matches_any(brand_rules.get("boutique_name_patterns", []), name_norm)
    if hit:
        return _result(record, "FSS", f"correspond au motif boutique : '{hit}'", "boutique_name_patterns", "moyenne", False)

    # 9. Nothing matched - never guess FSS just because the brand name
    #    appears in the text; always flag for a human instead.
    return _result(record, "UNCLEAR", "aucune regle ne correspond - a verifier manuellement", None, "basse", True)


def classify_locations(records: list[dict], brand_slug: str, rules: dict) -> list[dict]:
    """Classify every raw record - one classification result per input
    record, 1:1, duplicates included (never silently merged or dropped;
    see fss_classification_rules.yaml's safety rules)."""
    return [classify_location(record, brand_slug, rules) for record in records]
