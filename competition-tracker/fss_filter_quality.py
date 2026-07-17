"""Etape (FSS classification quality): builds the two review artifacts that
tell a human whether to trust a brand-specific classification pass -
data/fss_validation_sample.csv (a manageable sample to eyeball) and
data/fss_filter_quality.csv (FILTER_STATUS per brand). Both are derived
purely from what aggregate.py's fss_classified_records already computed -
no new scraping or classification logic here.
"""

from __future__ import annotations

import csv
import random
from datetime import date
from pathlib import Path

from brand_aliases import brand_match_key
from fss_classifier import FSS_CATEGORIES
from normalize import normalize
from region_mapping import REGIONS

VALIDATION_SAMPLE_COLUMNS = [
    "BRAND", "REGION", "COUNTRY", "CITY", "RAW_STORE_NAME", "RAW_ADDRESS",
    "CURRENT_CLASSIFICATION", "CLASSIFICATION_REASON", "RULE_MATCHED", "CONFIDENCE",
    "OFFICIAL_SOURCE_URL", "BIBLE_MATCH", "MANUAL_VERDICT", "MANUAL_NOTES",
]

FILTER_QUALITY_COLUMNS = [
    "BRAND", "RAW_LOCATIONS", "INCLUDED_FSS_FSF", "EXCLUDED_DEPARTMENT_STORE",
    "EXCLUDED_PERFUMERY", "EXCLUDED_MULTIBRAND", "EXCLUDED_CORNER", "EXCLUDED_ONLINE",
    "UNCLEAR", "BIBLE_FSS_FSF", "DIFFERENCE_VS_BIBLE", "PRECISION_SAMPLE_SIZE",
    "FALSE_POSITIVES_FOUND", "FALSE_NEGATIVES_FOUND", "FILTER_STATUS", "CONFIDENCE", "NOTES",
]

# Below this many samples requested per bucket, take everything instead of
# sampling ("all ambiguous locations when fewer than 20").
SAMPLE_SIZE_PER_BUCKET = 20

# A brand where the classifier isolates this few genuine FSS/FSF locations
# out of a large raw feed has no reliable network to report - "if no
# reliable FSS/FSF network can be isolated, mark ... INSUFFICIENT_DATA".
MIN_INCLUDED_FOR_A_NETWORK = 3
MIN_RAW_FOR_INSUFFICIENT_CHECK = 50

# A brand/BIBLE gap bigger than this (in absolute doors, or this fraction of
# the BIBLE total, whichever is larger) counts as "large" and unexplained
# unless a human has validated the sample.
MIN_ABS_DIFF_FOR_LARGE_GAP = 5
MIN_REL_DIFF_FOR_LARGE_GAP = 0.5

# Above this share of UNCLEAR locations in the raw feed, "ambiguous
# locations are limited" is not satisfied.
MAX_UNCLEAR_RATIO_FOR_RELIABLE = 0.4


def bible_fss_fsf_total(bible_index: dict | None, brand_name: str) -> int | None:
    if bible_index is None:
        return None
    region_totals = bible_index["region_totals"].get(brand_match_key(brand_name))
    if region_totals is None:
        return None
    return sum(region_totals.values())


def _bible_match(bible_index: dict | None, brand_name: str, record: dict) -> bool:
    """Whether this exact (brand, country, city, door name) already exists
    in the BIBLE's FSS/FSF rows - reused as a lightweight, purely
    informational signal in the validation sample, not a verdict."""
    if bible_index is None:
        return False
    key = (
        brand_match_key(brand_name), normalize(record.get("resolved_country")),
        normalize(record.get("city")), normalize(record.get("raw_store_name")),
    )
    return key in bible_index["by_door_key"]


def build_validation_sample(
    brand_name: str,
    classified_records: list[dict],
    source_url: str,
    bible_index: dict | None = None,
    sample_size: int = SAMPLE_SIZE_PER_BUCKET,
    rng: random.Random | None = None,
) -> list[dict]:
    """A manually-reviewable sample: >= sample_size FSS/FSF, >= sample_size
    excluded, all ambiguous (UNCLEAR) when fewer than sample_size (else a
    sample of that size too, still large enough to be useful), covering
    every region present in the data where possible.
    """
    rng = rng or random.Random(0)  # deterministic sampling across runs

    fss_fsf = [r for r in classified_records if r["classification"] in FSS_CATEGORIES]
    excluded = [r for r in classified_records if r["classification"] not in FSS_CATEGORIES and r["classification"] != "UNCLEAR"]
    unclear = [r for r in classified_records if r["classification"] == "UNCLEAR"]

    def _sample_covering_regions(bucket: list[dict], size: int) -> list[dict]:
        if len(bucket) <= size:
            return list(bucket)
        by_region: dict[str | None, list[dict]] = {}
        for r in bucket:
            by_region.setdefault(r.get("resolved_region"), []).append(r)
        picked, seen_ids = [], set()
        # One from each region first, so no available region is left out.
        for region in list(by_region):
            candidates = by_region[region]
            choice = rng.choice(candidates)
            picked.append(choice)
            seen_ids.add(id(choice))
        remaining = [r for r in bucket if id(r) not in seen_ids]
        rng.shuffle(remaining)
        for r in remaining:
            if len(picked) >= size:
                break
            picked.append(r)
        return picked[:size]

    selected = (
        _sample_covering_regions(fss_fsf, sample_size)
        + _sample_covering_regions(excluded, sample_size)
        + _sample_covering_regions(unclear, sample_size)
    )

    rows = []
    for r in selected:
        rows.append({
            "BRAND": brand_name,
            "REGION": r.get("resolved_region"),
            "COUNTRY": r.get("resolved_country"),
            "CITY": r.get("city"),
            "RAW_STORE_NAME": r.get("raw_store_name"),
            "RAW_ADDRESS": r.get("raw_address"),
            "CURRENT_CLASSIFICATION": r["classification"],
            "CLASSIFICATION_REASON": r["classification_reason"],
            "RULE_MATCHED": r.get("rule_matched"),
            "CONFIDENCE": r["confidence"],
            "OFFICIAL_SOURCE_URL": source_url,
            "BIBLE_MATCH": _bible_match(bible_index, brand_name, r),
            "MANUAL_VERDICT": "",
            "MANUAL_NOTES": "",
        })
    return rows


def load_previous_verdicts(path: Path | str) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_precision_from_verdicts(previous_rows: list[dict], brand_name: str) -> tuple[int, int, int]:
    """From a PRIOR run's fss_validation_sample.csv, once a human has filled
    in MANUAL_VERDICT: (sample_size reviewed, false_positives, false_negatives).
    A false positive is a location we called FSS/FSF that the human says
    isn't; a false negative is the reverse. Rows with no verdict yet are
    not counted - there's nothing to compare against."""
    reviewed = [
        r for r in previous_rows
        if brand_match_key(r.get("BRAND", "")) == brand_match_key(brand_name) and (r.get("MANUAL_VERDICT") or "").strip()
    ]
    false_positives = sum(
        1 for r in reviewed
        if r["CURRENT_CLASSIFICATION"] in FSS_CATEGORIES and normalize(r["MANUAL_VERDICT"]) not in ("fss", "fsf")
    )
    false_negatives = sum(
        1 for r in reviewed
        if r["CURRENT_CLASSIFICATION"] not in FSS_CATEGORIES and normalize(r["MANUAL_VERDICT"]) in ("fss", "fsf")
    )
    return len(reviewed), false_positives, false_negatives


def determine_filter_status(
    raw_count: int,
    included_count: int,
    unclear_count: int,
    bible_total: int | None,
    precision_sample_size: int,
    false_positives: int,
    false_negatives: int,
) -> tuple[str, str]:
    if raw_count == 0:
        return "INSUFFICIENT_DATA", "Aucune donnee brute disponible."

    if included_count < MIN_INCLUDED_FOR_A_NETWORK and raw_count >= MIN_RAW_FOR_INSUFFICIENT_CHECK:
        return "INSUFFICIENT_DATA", (
            f"Seulement {included_count} boutique(s) FSS/FSF identifiee(s) sur {raw_count} lignes brutes - "
            "aucun reseau FSS/FSF fiable ne peut etre isole depuis cette source."
        )

    unclear_ratio = unclear_count / raw_count
    diff_vs_bible = None if bible_total is None else included_count - bible_total
    large_unexplained_diff = diff_vs_bible is not None and abs(diff_vs_bible) > max(
        MIN_ABS_DIFF_FOR_LARGE_GAP, MIN_REL_DIFF_FOR_LARGE_GAP * max(bible_total, 1)
    )

    if precision_sample_size == 0:
        # No human validation has happened yet on this data - can never be
        # RELIABLE regardless of how clean the numbers look.
        if large_unexplained_diff or unclear_ratio > MAX_UNCLEAR_RATIO_FOR_RELIABLE:
            return "UNRELIABLE", (
                "Ecart important vs BIBLE et/ou taux d'ambiguite eleve, et aucune validation manuelle "
                "disponible pour l'expliquer - voir data/fss_validation_sample.csv."
            )
        return "NEEDS_REVIEW", (
            "Regles deterministes appliquees mais pas encore validees manuellement - "
            "remplir MANUAL_VERDICT dans data/fss_validation_sample.csv puis relancer."
        )

    if false_positives > 0 or false_negatives > 0:
        return "NEEDS_REVIEW", (
            f"{false_positives} faux positif(s) et {false_negatives} faux negatif(s) trouves lors de la "
            "derniere validation manuelle - regles a affiner dans fss_classification_rules.yaml."
        )

    if large_unexplained_diff:
        return "NEEDS_REVIEW", "Ecart significatif vs BIBLE non explique malgre une validation manuelle sans faux positif/negatif."

    if unclear_ratio > MAX_UNCLEAR_RATIO_FOR_RELIABLE:
        return "NEEDS_REVIEW", f"Trop de boutiques ambigues (UNCLEAR = {unclear_ratio:.0%} du brut) pour declarer le filtre fiable."

    return "RELIABLE", "Validation manuelle sans faux positif/negatif, ecart vs BIBLE explique, ambiguite limitee."


def build_filter_quality_row(
    brand_name: str,
    scrape_stats: dict,
    bible_index: dict | None,
    precision_sample_size: int,
    false_positives: int,
    false_negatives: int,
    confidence_label: str,
    checked_date: date | None = None,
) -> dict:
    checked_date = checked_date or date.today()
    category_counts = scrape_stats.get("category_counts", {})
    included = category_counts.get("FSS", 0) + category_counts.get("FSF", 0)
    unclear = category_counts.get("UNCLEAR", 0)
    bible_total = bible_fss_fsf_total(bible_index, brand_name)
    diff_vs_bible = None if bible_total is None else included - bible_total

    status, notes = determine_filter_status(
        raw_count=scrape_stats.get("raw_count", 0), included_count=included, unclear_count=unclear,
        bible_total=bible_total, precision_sample_size=precision_sample_size,
        false_positives=false_positives, false_negatives=false_negatives,
    )

    return {
        "BRAND": brand_name,
        "RAW_LOCATIONS": scrape_stats.get("raw_count", 0),
        "INCLUDED_FSS_FSF": included,
        "EXCLUDED_DEPARTMENT_STORE": category_counts.get("DEPARTMENT_STORE", 0),
        "EXCLUDED_PERFUMERY": category_counts.get("PERFUMERY", 0),
        "EXCLUDED_MULTIBRAND": category_counts.get("MULTIBRAND_RETAILER", 0),
        "EXCLUDED_CORNER": category_counts.get("CORNER_OR_CONCESSION", 0),
        "EXCLUDED_ONLINE": category_counts.get("ONLINE", 0),
        "UNCLEAR": unclear,
        "BIBLE_FSS_FSF": bible_total,
        "DIFFERENCE_VS_BIBLE": diff_vs_bible,
        "PRECISION_SAMPLE_SIZE": precision_sample_size,
        "FALSE_POSITIVES_FOUND": false_positives,
        "FALSE_NEGATIVES_FOUND": false_negatives,
        "FILTER_STATUS": status,
        "CONFIDENCE": confidence_label,
        "NOTES": notes,
    }
