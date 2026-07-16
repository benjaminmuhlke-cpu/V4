"""Etape 4ter: recoupement avec l'export CSV existant de l'onglet Competition
de la BIBLE. Only surfaces discrepancies - brands/regions missing from the
existing file, or numbers that diverge meaningfully - so the report doesn't
re-state data that's already correct in the official tracker.
"""

from __future__ import annotations

import csv
from pathlib import Path

from region_mapping import REGIONS

# A one-store difference is normal noise (a boutique that opened/closed the
# same week the export was made); below this, don't bother the user.
SIGNIFICANT_DIFF_THRESHOLD = 2


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
