"""Etape 4ter: recoupement avec le fichier existant de suivi concurrence.

Two supported inputs (dispatched on file extension in run_report.py):

- .xlsx : the real BIBLE ("BIBLE KP & FM Distribution List.xlsx"), read
  directly from its "Competition" worksheet as a door-level database (one
  row per physical door, not a per-region summary). This is the current,
  primary path - see load_bible_competition() / filter_bible_rows() /
  build_bible_index() and the three comparison functions below.

- .csv : the older per-brand regional-summary export (BRAND | EMEA | UK |
  NOAM | LATAM | CHINA | APAC | TOTAL | SOURCE | DATE). Kept for backward
  compatibility (load_existing_export() / compare_with_existing()) - it
  predates the door-level BIBLE integration and some earlier setup may
  still rely on it.
"""

from __future__ import annotations

import csv
from pathlib import Path

import openpyxl

from normalize import normalize
from region_mapping import REGIONS, get_region

# A one-store difference is normal noise (a boutique that opened/closed the
# same week the export was made); below this, don't bother the user.
SIGNIFICANT_DIFF_THRESHOLD = 2

COMPETITION_SHEET_NAME = "Competition"

# Substring markers (checked on the raw, un-normalized RETAILER text) that
# indicate an online/marketplace listing rather than a physical door.
ONLINE_RETAILER_MARKERS = ("retail.com",)


# --- Legacy CSV export path (backward compatible) --------------------------

def load_existing_export(path: Path | str) -> dict[str, dict]:
    """Read the tracker's own column layout: BRAND | EMEA | UK | NOAM | LATAM
    | CHINA | APAC | TOTAL | SOURCE | DATE. Returns {brand_name_lower: row}."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Competition export not found at {path}")

    existing = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            brand = (row.get("BRAND") or "").strip()
            if not brand:
                continue
            existing[brand.lower()] = row
    return existing


def _to_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def compare_with_existing(results: list[dict], existing: dict[str, dict]) -> list[dict]:
    """Only returns rows worth a human's attention: brands missing from the
    existing export entirely, or a region/total whose new value differs from
    the existing one by more than SIGNIFICANT_DIFF_THRESHOLD.
    """
    discrepancies = []

    for brand in results:
        if brand.get("status") not in ("ok", "manual") or brand.get("total") is None:
            continue

        existing_row = existing.get(brand["brand"].strip().lower())
        if existing_row is None:
            discrepancies.append({
                "brand": brand["brand"],
                "field": "TOTAL",
                "existing_value": None,
                "new_value": brand["total"],
                "note": "absent de l'export Competition existant",
            })
            continue

        existing_total = _to_int(existing_row.get("TOTAL"))
        if existing_total is not None and abs(brand["total"] - existing_total) >= SIGNIFICANT_DIFF_THRESHOLD:
            discrepancies.append({
                "brand": brand["brand"],
                "field": "TOTAL",
                "existing_value": existing_total,
                "new_value": brand["total"],
                "note": "écart significatif avec l'export existant",
            })

        for region in REGIONS:
            existing_value = _to_int(existing_row.get(region))
            new_value = brand["regions"].get(region)
            if existing_value is None or new_value is None:
                continue
            if abs(new_value - existing_value) >= SIGNIFICANT_DIFF_THRESHOLD:
                discrepancies.append({
                    "brand": brand["brand"],
                    "field": region,
                    "existing_value": existing_value,
                    "new_value": new_value,
                    "note": "écart significatif avec l'export existant",
                })

    return discrepancies


# --- Door-level BIBLE xlsx path ---------------------------------------------

def load_bible_competition(path: Path | str, sheet_name: str = COMPETITION_SHEET_NAME) -> list[dict]:
    """Read the Competition worksheet directly from the BIBLE workbook.

    Opens read-only and never calls .save() - the original file is never
    modified. Returns one dict per row, keyed by the sheet's own header
    text (upper-cased/stripped), e.g. "BRAND", "DOOR NAME", "OFF/ONLINE".
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"BIBLE file not found at {path}")

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        if sheet_name not in workbook.sheetnames:
            raise ValueError(
                f"Worksheet '{sheet_name}' not found in {path.name} "
                f"(available: {', '.join(workbook.sheetnames)})"
            )
        sheet = workbook[sheet_name]
        rows_iter = sheet.iter_rows(values_only=True)
        try:
            header_values = next(rows_iter)
        except StopIteration:
            return []
        header = [str(h).strip().upper() if h is not None else "" for h in header_values]

        rows = []
        for values in rows_iter:
            if values is None or all(v is None for v in values):
                continue
            rows.append(dict(zip(header, values)))
        return rows
    finally:
        workbook.close()


def _door_count(value) -> int:
    if value is None or value == "":
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _is_online_row(row: dict) -> bool:
    if normalize(row.get("OFF/ONLINE")) == "online":
        return True
    if normalize(row.get("CITY")) == "online":
        return True
    retailer = str(row.get("RETAILER") or "").lower()
    if any(marker in retailer for marker in ONLINE_RETAILER_MARKERS):
        return True
    return False


def filter_bible_rows(rows: list[dict]) -> tuple[list[dict], dict]:
    """Apply the "door-level, not online" exclusion rules. Returns
    (kept_rows, stats) where stats reports what was excluded and why, so a
    run can report exact counts rather than a silent filter.
    """
    stats = {"total_loaded": len(rows), "excluded_online": 0, "excluded_no_door_count": 0, "retained": 0}
    kept = []
    for row in rows:
        if _is_online_row(row):
            stats["excluded_online"] += 1
            continue
        if _door_count(row.get("DOOR COUNT")) <= 0:
            stats["excluded_no_door_count"] += 1
            continue
        kept.append(row)
    stats["retained"] = len(kept)
    return kept, stats


def _door_key(brand, country, city, door_name) -> tuple[str, str, str, str]:
    return (normalize(brand), normalize(country), normalize(city), normalize(door_name))


def build_bible_index(rows: list[dict]) -> dict:
    """Index the filtered BIBLE rows for comparison:
    - by_door_key: {(brand, country, city, door_name) normalized: [rows]}
    - by_brand: {normalized brand: [rows]} - all doors for a brand
    - region_totals: {normalized brand: {region: total DOOR COUNT}}, region
      derived from our own region_mapping (not the BIBLE's own REGION text
      column) so it lines up with the regions the scrapers compute.
    """
    by_door_key: dict[tuple, list[dict]] = {}
    by_brand: dict[str, list[dict]] = {}
    region_totals: dict[str, dict[str, int]] = {}

    for row in rows:
        norm_brand = normalize(row.get("BRAND"))
        key = _door_key(row.get("BRAND"), row.get("COUNTRY"), row.get("CITY"), row.get("DOOR NAME"))
        by_door_key.setdefault(key, []).append(row)
        by_brand.setdefault(norm_brand, []).append(row)

        region = get_region(row.get("COUNTRY"))
        if region:
            region_totals.setdefault(norm_brand, {r: 0 for r in REGIONS})
            region_totals[norm_brand][region] += _door_count(row.get("DOOR COUNT"))

    return {"by_door_key": by_door_key, "by_brand": by_brand, "region_totals": region_totals}


def find_new_stores(results: list[dict], bible_index: dict) -> list[dict]:
    """Scraped stores that don't match any door in the BIBLE, by (brand,
    country, city, door name). Only meaningful for brands whose scraper
    returns per-store detail (brand["stores"]) - aggregate-only locators
    like Diptyque's "all-addresses" totals page have no door name/city to
    match against, so they produce nothing here (regional_total_differences
    still covers them).
    """
    new_rows = []
    for brand in results:
        if brand.get("status") != "ok" or not brand.get("stores"):
            continue
        for store in brand["stores"]:
            key = _door_key(brand["brand"], store.get("country"), store.get("city"), store.get("name"))
            if key in bible_index["by_door_key"]:
                continue
            new_rows.append({
                "BRAND": brand["brand"],
                "REGION": store.get("region"),
                "COUNTRY": store.get("country"),
                "CITY": store.get("city"),
                "DOOR NAME": store.get("name"),
                "NOTE": "boutique scrapée non trouvée dans la BIBLE",
            })
    return new_rows


# Reasons a brand's scrape is not trustworthy enough to infer a closure from
# an unmatched BIBLE door. Under-coverage is judged against the brand's own
# door count in the BIBLE: if the scraper found much less than half of what
# the BIBLE lists, that's a scraping gap, not a wave of closures.
MIN_COVERAGE_RATIO_FOR_CLOSURES = 0.5


def _closure_detection_skip_reason(brand: dict, bible_brand_total_doors: int) -> str | None:
    if brand.get("status") == "error":
        return "le scraper a échoué (voir la colonne erreur du rapport) - fiabilité non garantie"
    if brand.get("status") == "manual":
        return "pas de scraper (confiance manuelle) - aucune détection de fermeture possible"
    if brand.get("confidence") == "manuelle":
        return "confiance manuelle - filtre FSS non fiable, on ne déduit pas de fermeture de cette donnée"
    if brand.get("partial"):
        return "couverture scraper probablement tronquée (plafond de résultats atteint) - résultat partiel"
    if not brand.get("stores"):
        return "pas de détail par boutique disponible pour cette marque (données agrégées uniquement)"
    scraped_count = len(brand["stores"])
    if bible_brand_total_doors and scraped_count < MIN_COVERAGE_RATIO_FOR_CLOSURES * bible_brand_total_doors:
        return (
            f"couverture scraper visiblement incomplète ({scraped_count} boutiques scrapées "
            f"vs {bible_brand_total_doors} portes dans la BIBLE)"
        )
    return None


def find_possible_closures(results: list[dict], bible_index: dict) -> tuple[list[dict], list[dict]]:
    """BIBLE doors not matched by any scraped store for a brand - NEVER
    labelled as a confirmed closure, always "TO VERIFY": a door can be
    missing from a scrape for reasons that have nothing to do with the
    store actually closing (site changed, page paginated, blocked request).

    A brand is skipped entirely (no closure rows produced, ever) when its
    scrape isn't reliable enough to trust an absence - see
    _closure_detection_skip_reason(). Returns (closure_rows, skipped_notes).
    """
    closure_rows = []
    skipped = []

    for brand in results:
        norm_brand = normalize(brand["brand"])
        bible_doors = bible_index["by_brand"].get(norm_brand, [])
        if not bible_doors:
            continue  # brand not in the BIBLE at all - nothing to compare closures against

        bible_brand_total_doors = len(bible_doors)
        skip_reason = _closure_detection_skip_reason(brand, bible_brand_total_doors)
        if skip_reason:
            skipped.append({"brand": brand["brand"], "reason": skip_reason})
            continue

        scraped_keys = {
            _door_key(brand["brand"], s.get("country"), s.get("city"), s.get("name"))
            for s in brand["stores"]
        }
        for row in bible_doors:
            key = _door_key(row.get("BRAND"), row.get("COUNTRY"), row.get("CITY"), row.get("DOOR NAME"))
            if key in scraped_keys:
                continue
            closure_rows.append({
                "BRAND": row.get("BRAND"),
                "REGION": row.get("REGION"),
                "COUNTRY": row.get("COUNTRY"),
                "CITY": row.get("CITY"),
                "DOOR NAME": row.get("DOOR NAME"),
                "DOOR COUNT (BIBLE)": row.get("DOOR COUNT"),
                "STATUS": "TO VERIFY",
                "NOTE": "porte présente dans la BIBLE, non retrouvée dans le dernier relevé scrapé",
            })

    return closure_rows, skipped


def write_rows_csv(rows: list[dict], path: Path, fieldnames: list[str] | None = None) -> int:
    """Same pattern as aggregate.write_a_verifier_csv: write the rows, or
    remove a stale file from a previous run if there's nothing to report
    this time - never leave an empty/outdated CSV lying around silently."""
    path = Path(path)
    if not rows:
        if path.exists():
            path.unlink()
        return 0
    fieldnames = fieldnames or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def find_regional_total_differences(results: list[dict], bible_index: dict) -> list[dict]:
    """Per-brand, per-region: BIBLE door-count total vs freshly scraped
    total. Only rows with an actual difference are reported - covers
    aggregate-only brands (Diptyque) too, since this comparison only needs
    each side's region totals, not door-level detail.
    """
    diff_rows = []
    for brand in results:
        if brand.get("status") not in ("ok", "manual") or brand.get("regions") is None:
            continue
        norm_brand = normalize(brand["brand"])
        bible_regions = bible_index["region_totals"].get(norm_brand)
        if bible_regions is None:
            continue  # brand not in the BIBLE at all - nothing to diff against
        for region in REGIONS:
            bible_value = bible_regions.get(region, 0)
            scraped_value = brand["regions"].get(region, 0) if brand["status"] == "ok" else None
            if scraped_value is None:
                continue
            diff = scraped_value - bible_value
            if diff == 0:
                continue
            diff_rows.append({
                "BRAND": brand["brand"],
                "REGION": region,
                "DOOR COUNT (BIBLE)": bible_value,
                "SCRAPED COUNT": scraped_value,
                "DIFF": diff,
            })
    return diff_rows
