"""Etape 4ter (three-way): compare the live website scrape, the BIBLE
door-level database, and the (optional) Competition Distribution PDF
reference, side by side, without ever treating any one of them as
automatically correct - see three_source_comparison.csv's STATUS column.

A brand also gets one "WORLDWIDE" pseudo-region row (in addition to the six
real regions) whenever the PDF only gives a worldwide total with no
regional breakdown - the per-region PDF columns would otherwise stay empty
even though there is a real number to compare against.
"""

from __future__ import annotations

import csv
from pathlib import Path

from brand_aliases import brand_match_key
from diff_existing import SIGNIFICANT_DIFF_THRESHOLD
from region_mapping import REGIONS

WORLDWIDE = "WORLDWIDE"

STATUS_MATCH = "MATCH"
STATUS_MINOR = "MINOR_DIFFERENCE"
STATUS_SIGNIFICANT = "SIGNIFICANT_DIFFERENCE"
STATUS_PDF_CONTRADICTION = "PDF_CONTRADICTION"
STATUS_WEBSITE_PARTIAL = "WEBSITE_PARTIAL"
STATUS_MANUAL_REVIEW = "MANUAL_REVIEW"

COLUMNS = [
    "BRAND", "REGION", "WEBSITE_TOTAL", "BIBLE_TOTAL", "PDF_REFERENCE_TOTAL",
    "WEBSITE_VS_BIBLE", "WEBSITE_VS_PDF", "BIBLE_VS_PDF",
    "PDF_REFERENCE_DATE", "PDF_PAGE", "STATUS", "NOTES",
]


def _website_reliability(brand_result: dict | None) -> str:
    """"absent" (brand wasn't part of this run's scrape scope at all - not
    the same as an unreliable result, just no opinion from the website this
    time), "unreliable" (scraped but shouldn't be trusted: failed, manual
    confidence, or a partial/capped result), or "reliable"."""
    if brand_result is None:
        return "absent"
    if (
        brand_result.get("status") == "ok"
        and brand_result.get("confidence") != "manuelle"
        and not brand_result.get("partial")
    ):
        return "reliable"
    return "unreliable"


def _pdf_region_value(pdf_records: list[dict], brand: str, region: str | None) -> dict:
    """Returns {"value": int|None, "pages": [...], "dates": [...],
    "contradiction": bool, "candidates": [int, ...]} for one (brand, region)
    - region=None/"WORLDWIDE" means the brand's worldwide_total records.
    """
    key = brand_match_key(brand)
    if region is None or region == WORLDWIDE:
        matches = [r for r in pdf_records if r["kind"] == "worldwide_total" and brand_match_key(r["brand"]) == key]
    else:
        matches = [
            r for r in pdf_records
            if r["kind"] == "regional_breakdown" and brand_match_key(r["brand"]) == key and r["region"] == region
        ]

    if not matches:
        return {"value": None, "pages": [], "dates": [], "contradiction": False, "candidates": []}

    distinct_values = sorted({r["worldwide_fss_total"] for r in matches})
    pages = sorted({r["source_page"] for r in matches})
    dates = sorted({r["reference_date"] for r in matches if r["reference_date"]})
    contradiction = len(distinct_values) > 1

    return {
        "value": None if contradiction else distinct_values[0],
        "pages": pages,
        "dates": dates,
        "contradiction": contradiction,
        "candidates": distinct_values,
    }


def _diff(a: int | None, b: int | None) -> int | None:
    return None if a is None or b is None else a - b


def _classify_status(website_total, bible_total, pdf_info: dict, website_reliability: str) -> tuple[str, str]:
    if pdf_info["contradiction"]:
        return STATUS_PDF_CONTRADICTION, (
            f"Le PDF se contredit pour cette ligne : valeurs {pdf_info['candidates']} "
            f"(pages {pdf_info['pages']}) - non réconciliées automatiquement."
        )

    if website_reliability == "unreliable":
        return STATUS_WEBSITE_PARTIAL, (
            "Chiffre website non fiable pour cette comparaison (scraper en échec, "
            "confiance manuelle, ou couverture partielle) - voir le rapport principal."
        )

    values = [v for v in (website_total, bible_total, pdf_info["value"]) if v is not None]
    if len(values) < 2:
        return STATUS_MANUAL_REVIEW, "Pas assez de sources avec une valeur pour comparer - vérification manuelle."

    pairwise = [d for d in (
        _diff(website_total, bible_total), _diff(website_total, pdf_info["value"]), _diff(bible_total, pdf_info["value"]),
    ) if d is not None]
    max_abs_diff = max(abs(d) for d in pairwise)

    if max_abs_diff == 0:
        return STATUS_MATCH, "Les sources disponibles concordent."
    if max_abs_diff < SIGNIFICANT_DIFF_THRESHOLD:
        return STATUS_MINOR, f"Écart mineur (max {max_abs_diff}) entre les sources disponibles."
    return STATUS_SIGNIFICANT, f"Écart significatif (max {max_abs_diff}) entre les sources disponibles."


def build_three_source_rows(
    results: list[dict],
    bible_index: dict | None,
    pdf_records: list[dict] | None,
) -> list[dict]:
    bible_index = bible_index or {"region_totals": {}}
    pdf_records = pdf_records or []

    pdf_brands = {brand_match_key(r["brand"]) for r in pdf_records}
    bible_brands = set(bible_index["region_totals"].keys())
    website_brands = {brand_match_key(r["brand"]) for r in results}
    all_brand_keys = website_brands | bible_brands | pdf_brands

    brand_display_names = {brand_match_key(r["brand"]): r["brand"] for r in results}
    for r in pdf_records:
        brand_display_names.setdefault(brand_match_key(r["brand"]), r["brand"])

    results_by_key = {brand_match_key(r["brand"]): r for r in results}

    rows = []
    for brand_key in sorted(all_brand_keys):
        brand_name = brand_display_names.get(brand_key, brand_key)
        website_result = results_by_key.get(brand_key)
        website_reliability = _website_reliability(website_result)
        bible_regions = bible_index["region_totals"].get(brand_key, {})

        # Always add the WORLDWIDE row, regardless of whether a regional PDF
        # breakdown also exists: a worldwide_total contradiction (e.g.
        # Amouage's 20-vs-30) lives at the worldwide level and would
        # otherwise never surface even when a - separately consistent -
        # regional breakdown is also present on another page.
        region_list = list(REGIONS) + [WORLDWIDE]

        for region in region_list:
            if region == WORLDWIDE:
                website_total = website_result["total"] if website_result and website_result.get("status") == "ok" else None
                bible_total = sum(bible_regions.values()) if bible_regions else None
            else:
                website_total = website_result["regions"].get(region) if website_result and website_result.get("status") == "ok" else None
                bible_total = bible_regions.get(region)

            pdf_info = _pdf_region_value(pdf_records, brand_name, region)

            nothing_to_report = (
                not pdf_info["contradiction"]
                and (website_total or 0) == 0
                and (bible_total or 0) == 0
                and (pdf_info["value"] or 0) == 0
            )
            if nothing_to_report:
                continue  # no presence and no signal anywhere - not worth a row

            status, note = _classify_status(website_total, bible_total, pdf_info, website_reliability)

            rows.append({
                "BRAND": brand_name,
                "REGION": region,
                "WEBSITE_TOTAL": website_total,
                "BIBLE_TOTAL": bible_total,
                "PDF_REFERENCE_TOTAL": pdf_info["value"],
                "WEBSITE_VS_BIBLE": _diff(website_total, bible_total),
                "WEBSITE_VS_PDF": _diff(website_total, pdf_info["value"]),
                "BIBLE_VS_PDF": _diff(bible_total, pdf_info["value"]),
                "PDF_REFERENCE_DATE": "; ".join(pdf_info["dates"]) or None,
                "PDF_PAGE": ", ".join(str(p) for p in pdf_info["pages"]) or None,
                "STATUS": status,
                "NOTES": note,
            })

    return rows


def write_three_source_csv(rows: list[dict], path: Path | str) -> int:
    path = Path(path)
    if not rows:
        if path.exists():
            path.unlink()
        return 0
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
