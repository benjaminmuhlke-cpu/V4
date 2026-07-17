"""Etape 3 (filtre FSS vs wholesale + region) + Etape 4 (historique/deltas/
tendance) + Etape 4quater (tag de confiance).

One function per brand's scraper_type (static_html / js_widget / manual) -
a plain if/elif dispatcher, no plugin system, since there are only two real
scraper kinds at this scale.
"""

from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path

from region_mapping import REGIONS, get_region
from scrapers.static import ScraperError, scrape_caron, scrape_diptyque, scrape_mfk, scrape_nishane
from scrapers.dynamic import scrape_stockist

BASE_DIR = Path(__file__).parent
SNAPSHOTS_DIR = BASE_DIR / "data" / "snapshots"
BLOCKLIST_PATH = BASE_DIR / "known_retailers_blocklist.json"
A_VERIFIER_PATH = BASE_DIR / "_a_verifier.csv"

# Best-effort city -> country resolution for scrapers whose store data has no
# country field of its own (MFK, Stockist widgets sometimes). Deliberately
# small and hand-maintained: anything not in here is logged to
# _a_verifier.csv instead of guessed. Extend as new unresolved cities show up.
CITY_COUNTRY_HINTS = {
    "paris": "France", "lyon": "France", "cannes": "France", "nice": "France",
    "london": "United Kingdom",
    "palermo": "Italy", "taormina": "Italy", "naples": "Italy", "rome": "Italy",
    "milan": "Italy", "milano": "Italy", "porto cervo": "Italy", "caserta": "Italy",
    "pistoia": "Italy", "forio": "Italy",
    "madrid": "Spain", "barcelona": "Spain", "ibiza": "Spain", "palma": "Spain",
    "andorra": "Andorra",
    "zurich": "Switzerland", "geneva": "Switzerland",
    "berlin": "Germany", "munich": "Germany", "frankfurt": "Germany",
    "amsterdam": "Netherlands",
    "brussels": "Belgium",
    "dubai": "United Arab Emirates", "abu dhabi": "United Arab Emirates",
    "doha": "Qatar", "riyadh": "Saudi Arabia", "jeddah": "Saudi Arabia",
    "muscat": "Oman", "beirut": "Lebanon", "istanbul": "Turkey",
    "new york": "United States", "los angeles": "United States",
    "miami": "United States", "chicago": "United States", "dallas": "United States",
    "las vegas": "United States", "san francisco": "United States",
    "toronto": "Canada", "vancouver": "Canada", "halifax": "Canada", "montreal": "Canada",
    "mexico city": "Mexico",
    "sao paulo": "Brazil", "são paulo": "Brazil", "rio de janeiro": "Brazil",
    "buenos aires": "Argentina", "bogota": "Colombia", "santiago": "Chile",
    "beijing": "China", "shanghai": "China", "guangzhou": "China", "shenzhen": "China",
    "hong kong": "China",
    "tokyo": "Japan", "osaka": "Japan", "seoul": "South Korea",
    "taipei": "Taiwan", "tainan": "Taiwan", "kaohsiung": "Taiwan",
    "singapore": "Singapore", "bangkok": "Thailand", "kuala lumpur": "Malaysia",
    "jakarta": "Indonesia", "manila": "Philippines", "makati city": "Philippines",
    "sydney": "Australia", "melbourne": "Australia", "mumbai": "India", "delhi": "India",
    "mykonos": "Greece", "athens": "Greece",
}


def load_blocklist() -> list[str]:
    data = json.loads(BLOCKLIST_PATH.read_text(encoding="utf-8"))
    return [entry.lower() for entry in data["blocklist"]]


def _resolve_country(record: dict, city_hint_source: str | None) -> str | None:
    country = record.get("country")
    if country:
        return country
    for field in ("city", "city_postal", "address", "name"):
        value = record.get(field)
        if not value:
            continue
        lowered = value.lower()
        for city, resolved_country in CITY_COUNTRY_HINTS.items():
            if city in lowered:
                return resolved_country
    return None


def classify_store(record: dict, brand_slug: str, brand_keywords: list[str], blocklist: list[str]) -> dict:
    """Apply the FSS filter to one raw store record.

    Returns the record enriched with "region", "country", "included" (bool),
    "verify_reason" (set only when the decision is worth a human look), and
    "name_ambiguous" (True specifically when the store's *name* didn't
    obviously match the brand - as opposed to a geography-lookup gap, which
    also sets verify_reason but says nothing about FSS-vs-wholesale
    classification quality). Keeping the two apart matters: a brand can have
    a perfectly reliable name-based filter and still hit unmapped countries,
    and conflating the two would misreport the filter as unreliable.
    """
    name = (record.get("name") or "").strip()
    name_lower = name.lower()

    verify_reason = None
    included = True
    name_ambiguous = False

    blocklist_hit = next((b for b in blocklist if b in name_lower), None)
    if blocklist_hit:
        included = False
        verify_reason = None  # confident exclusion, not "douteuse" - no need to log
    elif brand_keywords and not any(kw in name_lower for kw in brand_keywords):
        # Name doesn't obviously match the brand and isn't a known wholesaler
        # either - keep it (better a false positive we can review than a
        # silently dropped boutique) but flag it for manual review.
        verify_reason = f"nom '{name}' ne contient ni le mot-clé de la marque ni une entrée blocklist connue"
        name_ambiguous = True

    country = _resolve_country(record, brand_slug)
    region = get_region(country) if country else None
    if included and region is None:
        note = "pays introuvable" if not country else f"pays '{country}' non reconnu dans region_mapping"
        verify_reason = f"{verify_reason + ' ; ' if verify_reason else ''}{note}"

    record = {
        **record, "country": country, "region": region, "included": included,
        "verify_reason": verify_reason, "name_ambiguous": name_ambiguous,
    }
    return record


def _empty_region_totals() -> dict[str, int]:
    return {r: 0 for r in REGIONS}


def aggregate_stores(records: list[dict], brand_slug: str, brand_name: str, blocklist: list[str]) -> tuple[dict, list[dict], list[dict], dict]:
    """FSS-filter + region-classify a raw per-store record list.

    Returns (region_totals, included_stores, verify_rows, stats).
    included_stores keeps enough detail (name/address/city/country/region/
    image_url) for store-level delta detection (Etape 4) and photo
    downloads (Etape 4bis) - verify_rows is ready to append to
    _a_verifier.csv. stats = {"raw_count", "included_count",
    "blocklist_excluded_count", "ambiguous_count", "name_ambiguous_count"} -
    used by the brand coverage audit. "ambiguous_count" is every row flagged
    for _a_verifier.csv for any reason (name mismatch and/or unmapped
    country); "name_ambiguous_count" is specifically the FSS-vs-wholesale
    name-match failures - the one that actually measures filter reliability,
    since a brand can hit unmapped countries with a perfectly reliable name
    filter and the two shouldn't be conflated into one ratio.
    """
    brand_keywords = [w.lower() for w in brand_name.replace("'", " ").split() if len(w) > 2]
    totals = _empty_region_totals()
    verify_rows = []
    included_stores = []
    blocklist_excluded_count = 0
    name_ambiguous_count = 0

    for raw in records:
        classified = classify_store(raw, brand_slug, brand_keywords, blocklist)
        if not classified["included"] and not classified["verify_reason"]:
            blocklist_excluded_count += 1  # confident blocklist exclusion, not ambiguous
        if classified["name_ambiguous"]:
            name_ambiguous_count += 1
        if classified["verify_reason"]:
            verify_rows.append({
                "brand": brand_name,
                "store_name": raw.get("name"),
                "address": raw.get("address") or raw.get("city_postal") or raw.get("city"),
                "included": classified["included"],
                "reason": classified["verify_reason"],
                "source": raw.get("source"),
            })
        if classified["included"] and classified["region"]:
            totals[classified["region"]] += classified.get("count", 1)
            included_stores.append({
                "name": raw.get("name"),
                "address": raw.get("address") or raw.get("city_postal"),
                "city": raw.get("city"),
                "country": classified["country"],
                "region": classified["region"],
                "image_url": raw.get("image_url"),
            })

    stats = {
        "raw_count": len(records),
        "included_count": len(included_stores),
        "blocklist_excluded_count": blocklist_excluded_count,
        "ambiguous_count": len(verify_rows),
        "name_ambiguous_count": name_ambiguous_count,
    }
    return totals, included_stores, verify_rows, stats


def aggregate_country_counts(records: list[dict]) -> tuple[dict, list[dict]]:
    """For scrapers that already return one row per country (Diptyque-style),
    just map country -> region and sum. No FSS filter needed: these locators
    are monobrand by construction.
    """
    totals = _empty_region_totals()
    verify_rows = []
    for row in records:
        region = get_region(row["country"])
        if region is None:
            verify_rows.append({
                "brand": None, "store_name": None, "address": row["country"],
                "included": True, "reason": f"pays '{row['country']}' non reconnu dans region_mapping",
                "source": row.get("source"),
            })
            continue
        totals[region] += row["count"]
    return totals, verify_rows


def _run_scraper(brand: dict) -> tuple[list[dict], bool]:
    """Returns (records, partial). partial is True when the scraper itself
    knows its coverage may be clipped (currently only Stockist, which hits a
    per-query result cap) - static-HTML parsers always return a full page,
    so partial is always False for them."""
    parser = brand.get("parser")
    if brand["scraper_type"] == "static_html":
        if parser == "diptyque":
            return scrape_diptyque(brand["store_locator_url"]), False
        if parser == "mfk":
            return scrape_mfk(brand["store_locator_url"]), False
        if parser == "nishane":
            return scrape_nishane(brand["store_locator_url"]), False
        if parser == "caron":
            return scrape_caron(brand["store_locator_url"]), False
        raise ScraperError(f"no static_html parser registered for '{parser}'")
    if brand["scraper_type"] == "js_widget":
        if parser == "stockist":
            return scrape_stockist(brand["stockist_widget_tag"], brand["store_locator_url"])
        raise ScraperError(f"no js_widget parser registered for '{parser}'")
    raise ScraperError(f"scraper_type '{brand['scraper_type']}' has no automated scraper (manual brand)")


def process_brand(brand: dict, blocklist: list[str]) -> dict:
    """Scrape + classify one brand. Never raises - a failed brand is
    reported as such rather than blocking the rest of the run (Etape 6)."""
    result = {
        "brand": brand["name"],
        "slug": brand["slug"],
        "confidence": brand.get("confidence", "manuelle"),
        "source": brand["store_locator_url"],
        "known_total": brand.get("known_total"),
        "status": "ok",
        "error": None,
        "regions": _empty_region_totals(),
        "total": 0,
        "verify_rows": [],
        "stores": [],
        "partial": False,
        "scrape_stats": None,
    }

    if brand["scraper_type"] == "manual":
        result["status"] = "manual"
        result["total"] = brand.get("known_total")
        return result

    try:
        records, partial = _run_scraper(brand)
    except ScraperError as exc:
        result["status"] = "error"
        result["error"] = str(exc)
        return result

    result["partial"] = partial

    if brand.get("parser") == "diptyque":
        totals, verify_rows = aggregate_country_counts(records)
        stores = []  # Diptyque only gives per-country totals, no per-store detail
        # included_count=None (not 0) is a deliberate sentinel: this source
        # never runs a per-store FSS-vs-wholesale filter at all, so there is
        # no "how many included" to report - it's not applicable, not zero.
        # name_ambiguous_count=0 for the same reason: no per-store name
        # classification happens here to be ambiguous about.
        stats = {
            "raw_count": len(records), "included_count": None,
            "blocklist_excluded_count": 0, "ambiguous_count": len(verify_rows),
            "name_ambiguous_count": 0,
        }
    else:
        totals, stores, verify_rows, stats = aggregate_stores(records, brand["slug"], brand["name"], blocklist)

    for row in verify_rows:
        if row["brand"] is None:
            row["brand"] = brand["name"]

    result["regions"] = totals
    result["total"] = sum(totals.values())
    result["verify_rows"] = verify_rows
    result["stores"] = stores
    result["scrape_stats"] = stats
    return result


def run_all(brands: list[dict], only_slugs: list[str] | None = None) -> list[dict]:
    blocklist = load_blocklist()
    selected = [b for b in brands if only_slugs is None or b["slug"] in only_slugs]
    return [process_brand(b, blocklist) for b in selected]


def write_a_verifier_csv(results: list[dict], path: Path = A_VERIFIER_PATH) -> int:
    rows = [row for r in results for row in r["verify_rows"]]
    if not rows:
        if path.exists():
            path.unlink()
        return 0
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["brand", "store_name", "address", "included", "reason", "source"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


# --- Historique / deltas / tendance (Etape 4) -------------------------------

def snapshot_path(for_date: date) -> Path:
    return SNAPSHOTS_DIR / f"{for_date.isoformat()}.json"


def save_snapshot(results: list[dict], for_date: date | None = None) -> Path:
    for_date = for_date or date.today()
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = snapshot_path(for_date)
    payload = {"date": for_date.isoformat(), "brands": results}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def list_snapshots() -> list[Path]:
    if not SNAPSHOTS_DIR.exists():
        return []
    return sorted(SNAPSHOTS_DIR.glob("*.json"))


def load_snapshot(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def previous_snapshot(before: date | None = None) -> dict | None:
    before = before or date.today()
    candidates = [p for p in list_snapshots() if p.stem < before.isoformat()]
    if not candidates:
        return None
    return load_snapshot(candidates[-1])


def compute_deltas(current_results: list[dict], previous: dict | None) -> dict:
    """Per-brand total/region delta vs the previous snapshot. Returns
    {slug: {"total_delta": int, "regions_delta": {...}}} - brands with no
    previous data get a delta of None (first time seeing them), not 0."""
    prev_by_slug = {b["slug"]: b for b in previous["brands"]} if previous else {}
    deltas = {}
    for brand in current_results:
        prev = prev_by_slug.get(brand["slug"])
        no_usable_data = (
            prev is None
            or brand.get("status") != "ok"
            or prev.get("status") != "ok"
            or prev.get("total") is None
            or brand.get("total") is None
        )
        if no_usable_data:
            deltas[brand["slug"]] = {"total_delta": None, "regions_delta": None}
            continue
        region_delta = {
            region: brand["regions"].get(region, 0) - prev.get("regions", {}).get(region, 0)
            for region in REGIONS
        }
        deltas[brand["slug"]] = {
            "total_delta": brand["total"] - prev["total"],
            "regions_delta": region_delta,
        }
    return deltas


def _store_key(store: dict) -> tuple:
    return ((store.get("name") or "").strip().lower(), (store.get("city") or store.get("address") or "").strip().lower())


def compute_store_deltas(current_results: list[dict], previous: dict | None) -> dict:
    """Per-brand new/removed stores vs the previous snapshot, for brands that
    have store-level detail (not Diptyque-style country totals). Used for
    the email's "nouvelles ouvertures/fermetures" line and for photos.py.

    Returns {slug: {"new_stores": [...], "removed_stores": [...]}}."""
    prev_by_slug = {b["slug"]: b for b in previous["brands"]} if previous else {}
    result = {}
    for brand in current_results:
        if not brand.get("stores"):
            result[brand["slug"]] = {"new_stores": [], "removed_stores": []}
            continue
        prev = prev_by_slug.get(brand["slug"])
        prev_stores = prev.get("stores", []) if prev else []
        prev_keys = {_store_key(s) for s in prev_stores}
        current_keys = {_store_key(s) for s in brand["stores"]}
        result[brand["slug"]] = {
            "new_stores": [s for s in brand["stores"] if _store_key(s) not in prev_keys],
            "removed_stores": [s for s in prev_stores if _store_key(s) not in current_keys] if prev else [],
        }
    return result


def compute_trend(min_snapshots: int = 2) -> list[tuple[str, int]]:
    """Which brand opened the most stores across all recorded snapshots
    (earliest vs latest total for brands present in both). No analytics
    engine - just a loop over the JSON files already on disk."""
    snapshots = [load_snapshot(p) for p in list_snapshots()]
    if len(snapshots) < min_snapshots:
        return []

    earliest, latest = snapshots[0], snapshots[-1]
    earliest_totals = {b["slug"]: b["total"] for b in earliest["brands"] if b.get("status") == "ok"}
    latest_totals = {b["slug"]: b["total"] for b in latest["brands"] if b.get("status") == "ok"}
    latest_names = {b["slug"]: b["brand"] for b in latest["brands"]}

    growth = [
        (latest_names[slug], latest_totals[slug] - earliest_totals[slug])
        for slug in latest_totals
        if slug in earliest_totals
    ]
    return sorted(growth, key=lambda pair: pair[1], reverse=True)
