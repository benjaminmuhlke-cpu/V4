from __future__ import annotations

from dataclasses import dataclass
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
    "official_mall_landlord_directory": 2,
    "official_mall_landlord_website": 2,
    "official_verified_brand_social_post": 3,
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


@dataclass(frozen=True)
class PipelineSummary:
    brands_checked: int
    recent_openings_found: int
    to_verify_count: int
    excluded_non_fss_fsf: int


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


def _recent_row(brand_result: dict, store: dict, entry: dict, checked_date: date) -> dict:
    notes = entry.get("verification_notes") or ""
    if entry.get("status") == "PROBABLE":
        notes = "PROBABLE - " + notes if notes else "PROBABLE"
    return {
        "BRAND": brand_result["brand"],
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


def _verify_row(brand_result: dict, store: dict, entry: dict, checked_date: date, reason: str) -> dict:
    return {
        "BRAND": brand_result["brand"],
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


def _append_deduped(rows: list[dict], row: dict, key_fields: tuple[str, ...]) -> None:
    row_key = tuple(normalize(row.get(field)) for field in key_fields)
    if any(tuple(normalize(existing.get(field)) for field in key_fields) == row_key for existing in rows):
        return
    rows.append(row)


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
    excluded_non_fss_fsf = 0

    entries = research_cache.get("entries", [])

    for brand_result in results:
        if brand_result.get("status") != "ok":
            continue

        for store in brand_result.get("stores", []):
            if _store_lookup_key(brand_result["brand"], store) in bible_index["by_door_key"]:
                continue

            matched_entries = [
                entry for entry in entries
                if _entry_matches_store(entry, brand_result["brand"], store)
                and entry.get("status") in VERIFYABLE_STATUSES
            ]
            if not matched_entries:
                continue

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
                _append_deduped(
                    recent_rows,
                    _recent_row(brand_result, store, recent_entry, checked_date),
                    ("BRAND", "COUNTRY", "CITY", "DOOR NAME"),
                )
                continue

            best_entry = _best_entry(matched_entries)
            if best_entry is None:
                continue

            classification = best_entry.get("store_classification")
            if classification not in ALLOWED_DOOR_TYPES:
                excluded_non_fss_fsf += 1
                continue

            if _source_priority(best_entry) >= 99:
                reason = "source type is below the accepted priority threshold"
            elif _parse_source_date(best_entry.get("source_date")) is None:
                reason = "opening source has no date"
            elif not _is_within_recent_days(_parse_source_date(best_entry.get("source_date")), checked_date, recent_days):
                continue
            else:
                reason = "source requires manual verification"

            _append_deduped(
                verify_rows,
                _verify_row(brand_result, store, best_entry, checked_date, reason),
                ("BRAND", "COUNTRY", "CITY", "DOOR NAME"),
            )

    summary = PipelineSummary(
        brands_checked=sum(1 for result in results if result.get("status") == "ok"),
        recent_openings_found=len(recent_rows),
        to_verify_count=len(verify_rows),
        excluded_non_fss_fsf=excluded_non_fss_fsf,
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
