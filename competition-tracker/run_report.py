#!/usr/bin/env python3
"""Export recent mono-brand FSS/FSF boutique openings into one workbook."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

from aggregate import run_all
from diff_existing import write_rows_csv
from fss_filter_quality import (
    FILTER_QUALITY_COLUMNS,
    VALIDATION_SAMPLE_COLUMNS,
    build_filter_quality_row,
    build_validation_sample,
    compute_precision_from_verdicts,
    load_previous_verdicts,
)
from recent_openings import (
    build_recent_openings_rows,
    load_bible_index,
    load_research_cache,
    write_recent_openings_workbook,
)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export recent FSS/FSF boutique openings.")
    parser.add_argument(
        "--brands",
        type=str,
        default="pdm,amouage,creed,matiere_premiere,mfk,byredo,nishane,ex_nihilo,bdk,initio",
        help="Comma-separated brand slugs to check for recent openings.",
    )
    parser.add_argument(
        "--existing-file",
        type=str,
        required=True,
        help="Path to the trusted BIBLE .xlsx workbook.",
    )
    parser.add_argument(
        "--recent-days",
        type=int,
        default=60,
        help="Only keep openings with dated evidence from the last N days (default: 60).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(BASE_DIR / "recent_openings.xlsx"),
        help="Path to the Excel workbook to write.",
    )
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Accepted for backward compatibility; no email is ever sent by this workflow.",
    )
    parser.add_argument(
        "--include-classifier-diagnostics",
        action="store_true",
        help=(
            "Also write data/fss_filter_quality.csv and data/fss_validation_sample.csv - a "
            "read-only diagnostic on the brand-specific FSS/FSF classifier's own output "
            "(fss_classifier.py) for brands that have it. Never affects recent_openings.xlsx. "
            "Omitted by default."
        ),
    )
    return parser.parse_args()


def _load_same_day_snapshot(for_date: date) -> dict[str, dict]:
    path = SNAPSHOTS_DIR / f"{for_date.isoformat()}.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {brand["slug"]: brand for brand in payload.get("brands", [])}


def _research_only_result(brand_name: str, slug: str, research_cache: dict) -> dict | None:
    entries = [
        entry for entry in research_cache.get("entries", [])
        if entry.get("brand") == brand_name and entry.get("store_classification") in {"FSS", "FSF"}
    ]
    if not entries:
        return None

    stores = []
    seen = set()
    for entry in entries:
        key = (
            (entry.get("country") or "").strip().lower(),
            (entry.get("city") or "").strip().lower(),
            (entry.get("store_name") or "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        stores.append({
            "name": entry.get("store_name"),
            "address": entry.get("address"),
            "city": entry.get("city"),
            "country": entry.get("country"),
            "region": entry.get("region"),
        })

    return {
        "brand": brand_name,
        "slug": slug,
        "status": "ok",
        "stores": stores,
    }


def _merge_results_with_fallbacks(
    live_results: list[dict],
    brands: list[dict],
    research_cache: dict,
    only_slugs: list[str] | None,
    today: date,
) -> list[dict]:
    brand_by_slug = {brand["slug"]: brand for brand in brands}
    snapshot_by_slug = _load_same_day_snapshot(today)
    merged = []

    for result in live_results:
        if result.get("status") == "ok":
            merged.append(result)
            continue

        snapshot_result = snapshot_by_slug.get(result["slug"])
        if snapshot_result and snapshot_result.get("status") == "ok":
            merged.append(snapshot_result)
            continue

        fallback_result = _research_only_result(brand_by_slug[result["slug"]]["name"], result["slug"], research_cache)
        merged.append(fallback_result or result)

    if only_slugs is None:
        return merged

    merged_by_slug = {result["slug"]: result for result in merged}
    ordered = []
    for slug in only_slugs:
        if slug in merged_by_slug:
            ordered.append(merged_by_slug[slug])
            continue
        brand = brand_by_slug.get(slug)
        if brand is None:
            continue
        fallback_result = _research_only_result(brand["name"], slug, research_cache)
        if fallback_result is not None:
            ordered.append(fallback_result)
    return ordered


def _write_workbook_with_fallback(recent_rows: list[dict], verify_rows: list[dict], output_path: Path) -> tuple[Path, bool]:
    try:
        return write_recent_openings_workbook(recent_rows, verify_rows, output_path), False
    except PermissionError:
        fallback_path = output_path.with_name(f"{output_path.stem}.generated{output_path.suffix}")
        return write_recent_openings_workbook(recent_rows, verify_rows, fallback_path), True


def _run_classifier_diagnostics(brands: list[dict], live_results: list[dict], bible_index: dict, today: date) -> int:
    """data/fss_validation_sample.csv + data/fss_filter_quality.csv - a
    read-only diagnostic layer over what aggregate.py's brand-specific FSS
    classifier (fss_classifier.py) already computed. Only opt-in via
    --include-classifier-diagnostics, and deliberately reads live_results
    (aggregate.run_all()'s own output, before _merge_results_with_fallbacks)
    since only that carries fss_classified_records/scrape_stats - it has no
    effect on recent_rows/verify_rows/the workbook, which are built
    separately from the merged results.
    """
    validation_path = DATA_DIR / "fss_validation_sample.csv"
    previous_verdicts = load_previous_verdicts(validation_path)
    brand_by_name = {brand["name"]: brand for brand in brands}

    all_sample_rows = []
    quality_rows = []

    for result in live_results:
        if result.get("fss_classified_records") is None:
            continue
        brand_name = result["brand"]
        source_url = brand_by_name.get(brand_name, {}).get("store_locator_url")

        all_sample_rows.extend(build_validation_sample(
            brand_name, result["fss_classified_records"], source_url, bible_index=bible_index,
        ))

        reviewed, false_positives, false_negatives = compute_precision_from_verdicts(previous_verdicts, brand_name)
        quality_rows.append(build_filter_quality_row(
            brand_name, result["scrape_stats"], bible_index,
            precision_sample_size=reviewed, false_positives=false_positives, false_negatives=false_negatives,
            confidence_label=result.get("confidence"), checked_date=today,
        ))

    write_rows_csv(all_sample_rows, validation_path, fieldnames=VALIDATION_SAMPLE_COLUMNS)
    write_rows_csv(quality_rows, DATA_DIR / "fss_filter_quality.csv", fieldnames=FILTER_QUALITY_COLUMNS)
    return len(quality_rows)


def main() -> int:
    args = parse_args()
    only_slugs = [slug.strip() for slug in args.brands.split(",") if slug.strip()] if args.brands else None
    today = date.today()

    brands = yaml.safe_load((BASE_DIR / "brands.yaml").read_text(encoding="utf-8"))
    print(f"Checking {len(brands) if only_slugs is None else len(only_slugs)} brand(s)...")
    live_results = run_all(brands, only_slugs=only_slugs)

    bible_index = load_bible_index(Path(args.existing_file))

    if args.include_classifier_diagnostics:
        n_diagnosed = _run_classifier_diagnostics(brands, live_results, bible_index, today)
        print(
            f"{n_diagnosed} brand(s) with a dedicated FSS/FSF classifier diagnosed -> "
            "data/fss_filter_quality.csv, data/fss_validation_sample.csv"
        )

    research_cache = load_research_cache()
    results = _merge_results_with_fallbacks(live_results, brands, research_cache, only_slugs, today)
    recent_rows, verify_rows, summary = build_recent_openings_rows(
        results,
        bible_index,
        research_cache,
        recent_days=args.recent_days,
        checked_date=today,
    )
    output_path, used_fallback_output = _write_workbook_with_fallback(recent_rows, verify_rows, Path(args.output))

    if args.no_email:
        print("--no-email accepted; no email step is run in this streamlined workflow.")
    if used_fallback_output:
        print(f"Requested output was locked; workbook was written to {output_path} instead.")

    print(f"Brands checked: {summary.brands_checked}")
    print(f"Recent openings found: {summary.recent_openings_found}")
    print(f"Candidates placed in TO VERIFY: {summary.to_verify_count}")
    print(f"Candidates excluded because they already exist in the BIBLE: {summary.excluded_in_bible}")
    print(f"Locations excluded as non-FSS/FSF: {summary.excluded_non_fss_fsf}")
    print(f"Candidates excluded as old openings (known date outside the window): {summary.excluded_old_openings}")
    print(f"Output file: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
