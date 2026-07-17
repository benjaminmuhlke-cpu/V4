from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import openpyxl
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from brand_aliases import brand_match_key
from diff_existing import _door_key, build_bible_index, filter_bible_rows, load_bible_competition
from normalize import normalize
from online_research import CACHE_PATH_DEFAULT, load_cache

RECENT_OPENINGS_SHEET = "RECENT OPENINGS"
TO_VERIFY_SHEET = "TO VERIFY"

RECENT_OPENINGS_COLUMNS = [
    "BRAND",
    "REGION",
    "COUNTRY",
    "CITY",
    "DOOR NAME",
    "FULL ADDRESS",
    "DOOR TYPE",
    "OPENING DATE",
    "SOURCE",
    "SOURCE URL",
    "DATE CHECKED",
    "NOTES",
]

TO_VERIFY_COLUMNS = [
    "BRAND",
    "REGION",
    "COUNTRY",
    "CITY",
    "DOOR NAME",
    "FULL ADDRESS",
    "REASON TO VERIFY",
    "SOURCE",
    "SOURCE URL",
    "DATE CHECKED",
    "NOTES",
]

RECENT_SOURCE_TYPES = {
    "official_brand_website": 1,
    "official_brand_newsroom": 1,
    "official_brand_store_page": 1,
    "official_verified_brand_social_post": 2,
    "official_mall_landlord_directory": 3,
    "official_mall_landlord_website": 3,
    "official_airport_website": 3,
    "official_shopping_centre_website": 3,
    "industry_publication": 4,
    "beauty_publication": 4,
    "luxury_publication": 4,
    "retail_publication": 4,
    "travel_retail_publication": 4,
    "local_publication": 4,
}

ALLOWED_DOOR_TYPES = {"FSS", "FSF"}
RECENT_OPENING_STATUSES = {"CONFIRMED", "PROBABLE"}
VERIFYABLE_STATUSES = {"CONFIRMED", "PROBABLE", "TO VERIFY"}
ROW_KEY_FIELDS = ("BRAND", "COUNTRY", "CITY", "DOOR NAME")


@dataclass(frozen=True)
class PipelineSummary:
    brands_checked: int
    recent_openings_found: int
    to_verify_count: int
    excluded_non_fss_fsf: int
    excluded_in_bible: int
    excluded_old_openings: int = 0
    recent_openings_by_brand: dict[str, int] = field(default_factory=dict)
    to_verify_by_brand: dict[str, int] = field(default_factory=dict)
    source_links_used: tuple[str, ...] = ()


def _parse_source_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _is_within_recent_days(opening_date: date | None, checked_date: date, recent_days: int) -> bool:
    if opening_date is None:
        return False
    earliest = checked_date - timedelta(days=recent_days)
    return earliest <= opening_date <= checked_date


def _source_priority(entry: dict) -> int:
    return RECENT_SOURCE_TYPES.get(entry.get("source_type"), 99)


def _store_lookup_key(brand: str, store: dict) -> tuple[str, str, str, str]:
    return _door_key(brand, store.get("country"), store.get("city"), store.get("name"))


def _brandless_tokens(text: str | None, brand: str) -> set[str]:
    tokens = normalize(text).split()
    brand_tokens = set(normalize(brand).split())
    return {token for token in tokens if token not in brand_tokens}


def _entry_matches_store(entry: dict, brand_name: str, store: dict) -> bool:
    if brand_match_key(entry.get("brand")) != brand_match_key(brand_name):
        return False

    store_country = normalize(store.get("country"))
    entry_country = normalize(entry.get("country"))
    if store_country and entry_country and store_country != entry_country:
        return False

    store_city = normalize(store.get("city"))
    entry_city = normalize(entry.get("city"))
    if store_city and entry_city and store_city != entry_city:
        return False

    store_name = normalize(store.get("name"))
    entry_name = normalize(entry.get("store_name"))
    store_address = normalize(store.get("address"))
    entry_address = normalize(entry.get("address"))

    if store_name and entry_name and store_name == entry_name:
        return True
    if store_address and entry_address and store_address == entry_address:
        return True
    if store_address and entry_address and (store_address in entry_address or entry_address in store_address):
        return True

    store_tokens = _brandless_tokens(store.get("name"), brand_name)
    entry_tokens = _brandless_tokens(entry.get("store_name"), brand_name)
    if store_city and entry_city and store_tokens and entry_tokens and store_tokens.intersection(entry_tokens):
        return True

    return False


def _best_entry(entries: list[dict]) -> dict | None:
    if not entries:
        return None
    return sorted(
        entries,
        key=lambda entry: (
            _source_priority(entry),
            0 if _parse_source_date(entry.get("source_date")) else 1,
            -int(entry.get("status") == "CONFIRMED"),
            entry.get("source_title") or "",
        ),
    )[0]


def _recent_sort_key(entry: dict) -> tuple[int, int, str]:
    opening_date = _parse_source_date(entry.get("source_date"))
    return (
        _source_priority(entry),
        -opening_date.toordinal() if opening_date else 0,
        entry.get("source_title") or "",
    )


def load_bible_index(existing_file: Path | str) -> dict:
    rows = load_bible_competition(existing_file)
    filtered_rows, _ = filter_bible_rows(rows)
    return build_bible_index(filtered_rows)


def load_research_cache(cache_path: Path | str = CACHE_PATH_DEFAULT) -> dict:
    return load_cache(cache_path)


def _format_source_label(entry: dict) -> str:
    return entry.get("source_title") or entry.get("source_domain") or "Source"


def _recent_row(brand_name: str, store: dict, entry: dict, checked_date: date) -> dict:
    notes = entry.get("verification_notes") or ""
    if entry.get("status") == "PROBABLE":
        notes = "PROBABLE - " + notes if notes else "PROBABLE"
    return {
        "BRAND": brand_name,
        "REGION": store.get("region") or entry.get("region"),
        "COUNTRY": store.get("country") or entry.get("country"),
        "CITY": store.get("city") or entry.get("city"),
        "DOOR NAME": store.get("name") or entry.get("store_name"),
        "FULL ADDRESS": store.get("address") or entry.get("address"),
        "DOOR TYPE": entry.get("store_classification"),
        "OPENING DATE": entry.get("source_date"),
        "SOURCE": _format_source_label(entry),
        "SOURCE URL": entry.get("url"),
        "DATE CHECKED": checked_date.isoformat(),
        "NOTES": notes,
    }


def _verify_row(brand_name: str, store: dict, entry: dict, checked_date: date, reason: str) -> dict:
    return {
        "BRAND": brand_name,
        "REGION": store.get("region") or entry.get("region"),
        "COUNTRY": store.get("country") or entry.get("country"),
        "CITY": store.get("city") or entry.get("city"),
        "DOOR NAME": store.get("name") or entry.get("store_name"),
        "FULL ADDRESS": store.get("address") or entry.get("address"),
        "REASON TO VERIFY": reason,
        "SOURCE": _format_source_label(entry),
        "SOURCE URL": entry.get("url"),
        "DATE CHECKED": checked_date.isoformat(),
        "NOTES": entry.get("verification_notes") or entry.get("evidence") or "",
    }


def _row_key(row: dict) -> tuple[str, ...]:
    return tuple(normalize(row.get(field)) for field in ROW_KEY_FIELDS)


def _store_from_entry(entry: dict) -> dict:
    return {
        "name": entry.get("store_name"),
        "address": entry.get("address"),
        "city": entry.get("city"),
        "country": entry.get("country"),
        "region": entry.get("region"),
    }


def _candidate_reason(best_entry: dict) -> str | None:
    """Only ever called once every matched entry's opening date is unknown
    (see process_candidate) - so a known-but-old date is never described
    here as "to verify"; it's excluded entirely instead."""
    if _source_priority(best_entry) >= 99:
        return "source type is below the accepted priority threshold"
    return "opening source has no date"


def _selected_brand_map(results: list[dict]) -> dict[str, str]:
    selected = {}
    for result in results:
        brand_name = result.get("brand")
        if brand_name:
            selected[brand_match_key(brand_name)] = brand_name
    return selected


def build_recent_openings_rows(
    results: list[dict],
    bible_index: dict,
    research_cache: dict,
    recent_days: int = 60,
    checked_date: date | None = None,
) -> tuple[list[dict], list[dict], PipelineSummary]:
    checked_date = checked_date or date.today()
    recent_rows: list[dict] = []
    verify_rows: list[dict] = []
    recent_row_keys: set[tuple[str, ...]] = set()
    verify_row_keys: set[tuple[str, ...]] = set()
    recent_by_brand: defaultdict[str, int] = defaultdict(int)
    verify_by_brand: defaultdict[str, int] = defaultdict(int)
    source_links_used: set[str] = set()
    excluded_non_fss_fsf = 0
    excluded_in_bible = 0
    excluded_old_openings = 0

    selected_brands = _selected_brand_map(results)
    entries = [entry for entry in research_cache.get("entries", []) if brand_match_key(entry.get("brand")) in selected_brands]
    processed_candidates: set[tuple[str, str, str, str]] = set()
    counted_bible_exclusions: set[tuple[str, str, str, str]] = set()

    def process_candidate(brand_name: str, store: dict, matched_entries: list[dict]) -> None:
        nonlocal excluded_non_fss_fsf, excluded_in_bible, excluded_old_openings

        if not matched_entries:
            return

        candidate_key = _store_lookup_key(brand_name, store)
        if candidate_key in processed_candidates:
            return

        # A scraper's own door name and a research entry's door name can
        # both refer to the same physical BIBLE door under different text
        # (e.g. a locator's "Boutique Marais" vs the BIBLE's own "LE
        # MARAIS"). Check every name we have for this candidate - not just
        # whichever one built this particular store dict - so a door that's
        # already tracked under any of them is never re-reported as new.
        candidate_bible_keys = {candidate_key} | {
            _store_lookup_key(brand_name, _store_from_entry(entry)) for entry in matched_entries
        }
        matched_bible_key = next((key for key in candidate_bible_keys if key in bible_index["by_door_key"]), None)
        if matched_bible_key is not None:
            if matched_bible_key not in counted_bible_exclusions:
                excluded_in_bible += 1
                counted_bible_exclusions.add(matched_bible_key)
            processed_candidates.add(candidate_key)
            return

        candidate_entries = sorted(matched_entries, key=_recent_sort_key)
        recent_entry = next(
            (
                entry for entry in candidate_entries
                if entry.get("store_classification") in ALLOWED_DOOR_TYPES
                and _source_priority(entry) < 99
                and entry.get("status") in RECENT_OPENING_STATUSES
                and _is_within_recent_days(_parse_source_date(entry.get("source_date")), checked_date, recent_days)
            ),
            None,
        )
        if recent_entry is not None:
            row = _recent_row(brand_name, store, recent_entry, checked_date)
            row_key = _row_key(row)
            if row_key not in recent_row_keys:
                recent_rows.append(row)
                recent_row_keys.add(row_key)
                recent_by_brand[brand_name] += 1
                if row["SOURCE URL"]:
                    source_links_used.add(row["SOURCE URL"])
            processed_candidates.add(candidate_key)
            return

        best_entry = _best_entry(matched_entries)
        if best_entry is None:
            return

        classification = best_entry.get("store_classification")
        if classification not in ALLOWED_DOOR_TYPES:
            excluded_non_fss_fsf += 1
            processed_candidates.add(candidate_key)
            return

        # TO VERIFY is only for candidates whose opening date is still
        # unknown. A known date that didn't qualify above (outside the
        # recent window, or reported by a source too weak to promote) is a
        # resolved fact, not an open question - it must never sit in TO
        # VERIFY. It simply isn't a recent opening to report.
        if any(_parse_source_date(entry.get("source_date")) is not None for entry in matched_entries):
            excluded_old_openings += 1
            processed_candidates.add(candidate_key)
            return

        reason = _candidate_reason(best_entry)
        if reason is None:
            return

        row = _verify_row(brand_name, store, best_entry, checked_date, reason)
        row_key = _row_key(row)
        if row_key not in verify_row_keys:
            verify_rows.append(row)
            verify_row_keys.add(row_key)
            verify_by_brand[brand_name] += 1
            if row["SOURCE URL"]:
                source_links_used.add(row["SOURCE URL"])
        processed_candidates.add(candidate_key)

    for brand_result in results:
        if brand_result.get("status") != "ok":
            continue
        brand_name = brand_result["brand"]

        for store in brand_result.get("stores", []):
            matched_entries = [
                entry for entry in entries
                if _entry_matches_store(entry, brand_name, store)
                and entry.get("status") in VERIFYABLE_STATUSES
            ]
            process_candidate(brand_name, store, matched_entries)

    for entry in entries:
        if entry.get("status") not in VERIFYABLE_STATUSES:
            continue
        brand_name = selected_brands[brand_match_key(entry.get("brand"))]
        process_candidate(brand_name, _store_from_entry(entry), [entry])

    summary = PipelineSummary(
        brands_checked=len(selected_brands),
        recent_openings_found=len(recent_rows),
        to_verify_count=len(verify_rows),
        excluded_non_fss_fsf=excluded_non_fss_fsf,
        excluded_in_bible=excluded_in_bible,
        excluded_old_openings=excluded_old_openings,
        recent_openings_by_brand=dict(sorted(recent_by_brand.items())),
        to_verify_by_brand=dict(sorted(verify_by_brand.items())),
        source_links_used=tuple(sorted(source_links_used)),
    )
    return recent_rows, verify_rows, summary


def _write_sheet(workbook: openpyxl.Workbook, title: str, columns: list[str], rows: list[dict]) -> None:
    worksheet = workbook.create_sheet(title=title)
    worksheet.freeze_panes = "A2"
    worksheet.append(columns)
    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    for row in rows:
        worksheet.append([row.get(column) for column in columns])

    worksheet.auto_filter.ref = worksheet.dimensions

    if "SOURCE URL" in columns:
        hyperlink_col = columns.index("SOURCE URL") + 1
        for row_index in range(2, worksheet.max_row + 1):
            cell = worksheet.cell(row=row_index, column=hyperlink_col)
            if cell.value:
                cell.hyperlink = str(cell.value)
                cell.style = "Hyperlink"

    for col_index, column in enumerate(columns, start=1):
        max_length = len(column)
        for row_index in range(2, worksheet.max_row + 1):
            value = worksheet.cell(row=row_index, column=col_index).value
            if value is None:
                continue
            max_length = max(max_length, len(str(value)))
        worksheet.column_dimensions[get_column_letter(col_index)].width = min(max_length + 2, 60)


def write_recent_openings_workbook(recent_rows: list[dict], verify_rows: list[dict], output_path: Path | str) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    _write_sheet(workbook, RECENT_OPENINGS_SHEET, RECENT_OPENINGS_COLUMNS, recent_rows)
    _write_sheet(workbook, TO_VERIFY_SHEET, TO_VERIFY_COLUMNS, verify_rows)
    workbook.save(output_path)
    workbook.close()
    return output_path
