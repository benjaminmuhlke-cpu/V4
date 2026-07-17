"""Etape (recent openings): surfaces confirmed newly-opened FSS/FSF doors so
they can be added to the BIBLE, using data/online_research_cache.json as the
evidence source (see online_research.py's module docstring for why that's a
curated cache rather than a live search).

Two independent discovery routes feed the same check - neither gates the
other, and a finding never has to come from both:

  A. store-locator candidate -> recent-opening evidence: the scraper already
     returned this door (results[i]["stores"]) and online research
     separately dates its opening.
  B. recent-opening announcement -> official locator + BIBLE check: a dated,
     credible cache entry, whether or not the scraper's own coverage
     happened to include the same door (a fixed seed list, a paginated
     locator, a blocked request, or a city-name mismatch between sources can
     all cause the scraper to miss a real door - that is not a reason to
     miss the opening too).

A cache entry becomes a RECENT OPENING row only when ALL of:
  - store_classification is FSS or FSF (never counters/wholesale/online -
    an opening of a department-store corner is not what this feeds)
  - status is CONFIRMED or PROBABLE (never a bare "TO VERIFY" cache entry -
    see the source-confidence rules in online_research.py)
  - it carries a dated source_date (an "opening" is only "recent" if it is
    dated - an undated "this store exists" finding is not opening evidence)
  - the exact door is not already in the BIBLE (checked with the same
    (brand, country, city, door name) key diff_existing.py uses everywhere
    else, so "already tracked" means the same thing across the whole tool)

A cache entry that identifies a real, credible store but has no dated
opening evidence (or isn't yet CONFIRMED/PROBABLE) is never silently
promoted or silently dropped - it always comes back in the second list,
still_to_verify_rows, regardless of whether that door is already in the
BIBLE. Being in the BIBLE only ever suppresses the RECENT OPENING row (it's
not "new"); it never suppresses the "needs a dated source" note, because
those are two different questions.
"""

from __future__ import annotations

from diff_existing import _door_key
from normalize import normalize

RECENT_OPENING_COLUMNS = [
    "BRAND", "REGION", "COUNTRY", "CITY", "STORE_NAME", "ADDRESS", "DOOR_TYPE",
    "OPENING_EVIDENCE_DATE", "SOURCE_URL", "SOURCE_TYPE", "CONFIDENCE", "STATUS",
    "DISCOVERY_ROUTE", "EVIDENCE",
]

STILL_TO_VERIFY_COLUMNS = [
    "BRAND", "REGION", "COUNTRY", "CITY", "STORE_NAME", "ADDRESS",
    "ALREADY_IN_BIBLE", "STATUS", "REASON",
]

_OPENING_CLASSIFICATIONS = ("FSS", "FSF")
_OPENING_STATUSES = ("CONFIRMED", "PROBABLE")


def _scraped_names_by_brand(results: list[dict] | None) -> dict[str, set[str]]:
    """{brand name lower: {normalized scraped store names}} - used only to
    label which discovery route a finding came through, never to gate
    whether it counts (see module docstring)."""
    by_brand: dict[str, set[str]] = {}
    for brand in results or []:
        if brand.get("status") != "ok" or not brand.get("stores"):
            continue
        names = by_brand.setdefault(brand["brand"].strip().lower(), set())
        for store in brand["stores"]:
            if store.get("name"):
                names.add(normalize(store["name"]))
    return by_brand


def find_recent_openings(
    cache: dict, bible_index: dict, results: list[dict] | None = None
) -> tuple[list[dict], list[dict]]:
    """Returns (recent_opening_rows, still_to_verify_rows) - see module
    docstring for exactly what qualifies for each list."""
    scraped_names = _scraped_names_by_brand(results)
    opened_rows: list[dict] = []
    to_verify_rows: list[dict] = []

    for entry in cache.get("entries", []):
        brand = entry.get("brand")
        store_name = entry.get("store_name")
        if not brand or not store_name:
            continue
        if entry.get("store_classification") not in _OPENING_CLASSIFICATIONS:
            continue  # not a monobrand door - out of scope for "openings"

        key = _door_key(brand, entry.get("country"), entry.get("city"), store_name)
        already_in_bible = key in bible_index.get("by_door_key", {})

        if entry.get("status") not in _OPENING_STATUSES or not entry.get("source_date"):
            to_verify_rows.append({
                "BRAND": brand,
                "REGION": entry.get("region"),
                "COUNTRY": entry.get("country"),
                "CITY": entry.get("city"),
                "STORE_NAME": store_name,
                "ADDRESS": entry.get("address"),
                "ALREADY_IN_BIBLE": already_in_bible,
                "STATUS": "TO VERIFY",
                "REASON": (
                    "boutique référencée mais sans date d'ouverture confirmée/probable - "
                    "reste TO VERIFY tant qu'aucune source datée n'est trouvée"
                ),
            })
            continue

        if already_in_bible:
            continue  # already tracked in the BIBLE - not a new opening

        route = "A (retrouvée par le scraper)" if normalize(store_name) in scraped_names.get(brand.strip().lower(), set()) else "B (annonce en ligne uniquement)"
        opened_rows.append({
            "BRAND": brand,
            "REGION": entry.get("region"),
            "COUNTRY": entry.get("country"),
            "CITY": entry.get("city"),
            "STORE_NAME": store_name,
            "ADDRESS": entry.get("address"),
            "DOOR_TYPE": entry.get("store_classification"),
            "OPENING_EVIDENCE_DATE": entry.get("source_date"),
            "SOURCE_URL": entry.get("url"),
            "SOURCE_TYPE": entry.get("source_type"),
            "CONFIDENCE": entry.get("confidence"),
            "STATUS": entry.get("status"),
            "DISCOVERY_ROUTE": route,
            "EVIDENCE": entry.get("evidence"),
        })

    return opened_rows, to_verify_rows
