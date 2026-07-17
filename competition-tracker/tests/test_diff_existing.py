import csv

import openpyxl
import pytest

from diff_existing import (
    build_bible_index, compare_with_existing, filter_bible_rows,
    find_new_stores, find_possible_closures, find_regional_total_differences,
    load_bible_competition, load_existing_export, write_rows_csv,
)

HEADERS = ["BRAND", "REGION", "COUNTRY", "CITY", "DOOR NAME", "DOOR TYPE", "OFF/Online", "RETAILER", "DOOR COUNT"]

# A small synthetic "Competition" worksheet exercising every exclusion rule
# and normalization edge case (accents/case/punctuation) the real BIBLE can
# contain, without needing the real file.
SYNTHETIC_ROWS = [
    # kept: normal offline doors
    ["Diptyque", "EMEA", "France", "Paris", "Diptyque Saint-Honoré", "Flagship", "Offline", "Diptyque", 1],
    ["Diptyque", "EMEA", "France", "Lyon", "Diptyque Lyon", "Boutique", "Offline", "Diptyque", 1],
    ["Diptyque", "UK", "United Kingdom", "London", "Diptyque Marylebone", "Boutique", "Offline", "Diptyque", 1],
    ["Diptyque", "NOAM", "United States", "New York", "Diptyque SoHo", "Boutique", "Offline", "Diptyque", 1],
    ["Caron", "EMEA", "France", "Paris", "Boutique Saint-Honoré", "Boutique", "Offline", "Caron", 1],
    # excluded: OFF/Online == Online
    ["Diptyque", "EMEA", "France", "Paris", "Diptyque Website", "Ecommerce", "Online", "Diptyque", 1],
    # excluded: CITY == ONLINE
    ["Diptyque", "EMEA", "France", "ONLINE", "Diptyque E-shop", "Ecommerce", "Offline", "Diptyque", 1],
    # excluded: RETAILER contains retail.com (case-insensitive)
    ["Diptyque", "EMEA", "France", "Paris", "Marketplace listing", "Marketplace", "Offline", "SomeRetail.COM", 1],
    # excluded: blank/zero DOOR COUNT
    ["Diptyque", "EMEA", "France", "Marseille", "Diptyque Marseille", "Boutique", "Offline", "Diptyque", 0],
    ["Diptyque", "EMEA", "France", "Nice", "Diptyque Nice", "Boutique", "Offline", "Diptyque", None],
]


def make_bible_xlsx(tmp_path, rows=None):
    rows = SYNTHETIC_ROWS if rows is None else rows
    path = tmp_path / "fake_bible.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Competition"
    ws.append(HEADERS)
    for row in rows:
        ws.append(row)
    wb.save(path)
    return path


# --- loading + filtering -----------------------------------------------------

def test_load_bible_competition_reads_all_rows(tmp_path):
    path = make_bible_xlsx(tmp_path)
    rows = load_bible_competition(path)
    assert len(rows) == len(SYNTHETIC_ROWS)
    assert rows[0]["BRAND"] == "Diptyque"
    assert rows[0]["DOOR NAME"] == "Diptyque Saint-Honoré"


def test_load_bible_competition_missing_sheet_raises(tmp_path):
    path = tmp_path / "empty.xlsx"
    wb = openpyxl.Workbook()
    wb.active.title = "NotCompetition"
    wb.save(path)
    with pytest.raises(ValueError):
        load_bible_competition(path)


def test_load_bible_competition_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_bible_competition(tmp_path / "does_not_exist.xlsx")


def test_filter_bible_rows_excludes_online_and_zero_count(tmp_path):
    rows = load_bible_competition(make_bible_xlsx(tmp_path))
    kept, stats = filter_bible_rows(rows)

    assert stats["total_loaded"] == 10
    assert stats["excluded_online"] == 3  # OFF/Online=Online, CITY=ONLINE, retail.com
    assert stats["excluded_no_door_count"] == 2  # 0 and blank
    assert stats["retained"] == 5
    assert len(kept) == 5
    kept_names = {row["DOOR NAME"] for row in kept}
    assert "Diptyque Website" not in kept_names
    assert "Diptyque E-shop" not in kept_names
    assert "Marketplace listing" not in kept_names
    assert "Diptyque Marseille" not in kept_names
    assert "Diptyque Nice" not in kept_names


def test_filter_bible_rows_never_writes_to_disk(tmp_path):
    path = make_bible_xlsx(tmp_path)
    mtime_before = path.stat().st_mtime
    rows = load_bible_competition(path)
    filter_bible_rows(rows)
    assert path.stat().st_mtime == mtime_before


# --- index -------------------------------------------------------------------

def _kept_rows(tmp_path):
    rows = load_bible_competition(make_bible_xlsx(tmp_path))
    kept, _ = filter_bible_rows(rows)
    return kept


def test_build_bible_index_region_totals(tmp_path):
    index = build_bible_index(_kept_rows(tmp_path))
    assert index["region_totals"]["diptyque"] == {
        "EMEA": 2, "UK": 1, "NOAM": 1, "LATAM": 0, "CHINA": 0, "APAC": 0,
    }
    assert index["region_totals"]["caron"]["EMEA"] == 1
    assert len(index["by_brand"]["diptyque"]) == 4


def test_build_bible_index_door_key_matches_regardless_of_formatting(tmp_path):
    index = build_bible_index(_kept_rows(tmp_path))
    key = ("diptyque", "france", "paris", "diptyque saint honore")
    assert key in index["by_door_key"]


# --- new stores ----------------------------------------------------------------

def test_find_new_stores_detects_unmatched_scraped_store(tmp_path):
    index = build_bible_index(_kept_rows(tmp_path))
    results = [{
        "brand": "Diptyque", "status": "ok",
        "stores": [
            {"name": "Diptyque Saint-Honoré", "city": "Paris", "country": "France", "region": "EMEA"},
            {"name": "Diptyque Nouvelle Boutique", "city": "Marseille", "country": "France", "region": "EMEA"},
        ],
    }]
    new_rows = find_new_stores(results, index)
    assert len(new_rows) == 1
    assert new_rows[0]["DOOR NAME"] == "Diptyque Nouvelle Boutique"


def test_find_new_stores_normalizes_before_matching(tmp_path):
    index = build_bible_index(_kept_rows(tmp_path))
    results = [{
        "brand": "DIPTYQUE", "status": "ok",
        "stores": [{"name": "diptyque saint-honore", "city": "  PARIS  ", "country": "france", "region": "EMEA"}],
    }]
    assert find_new_stores(results, index) == []


def test_find_new_stores_skips_aggregate_only_brands(tmp_path):
    index = build_bible_index(_kept_rows(tmp_path))
    results = [{"brand": "Diptyque", "status": "ok", "stores": []}]
    assert find_new_stores(results, index) == []


# --- possible closures: always TO VERIFY, never a confirmed closure ------------

def _reliable_diptyque_result(stores):
    return {
        "brand": "Diptyque", "status": "ok", "confidence": "haute", "partial": False,
        "stores": stores,
    }


def test_find_possible_closures_flags_missing_door_as_to_verify(tmp_path):
    index = build_bible_index(_kept_rows(tmp_path))
    # Only 3 of the 4 real Diptyque doors were found by the scraper this time.
    results = [_reliable_diptyque_result([
        {"name": "Diptyque Saint-Honoré", "city": "Paris", "country": "France"},
        {"name": "Diptyque Lyon", "city": "Lyon", "country": "France"},
        {"name": "Diptyque SoHo", "city": "New York", "country": "United States"},
    ])]
    closures, skipped = find_possible_closures(results, index)
    assert skipped == []
    assert len(closures) == 1
    assert closures[0]["DOOR NAME"] == "Diptyque Marylebone"
    assert closures[0]["STATUS"] == "TO VERIFY"
    assert "verif" in closures[0]["STATUS"].lower().replace("é", "e")


def test_find_possible_closures_never_uses_a_confirmed_status_string(tmp_path):
    index = build_bible_index(_kept_rows(tmp_path))
    # 3 of 4 real doors found (75% coverage, above the skip threshold) so
    # closure detection actually runs instead of being skipped as incomplete.
    results = [_reliable_diptyque_result([
        {"name": "Diptyque Saint-Honoré", "city": "Paris", "country": "France"},
        {"name": "Diptyque Lyon", "city": "Lyon", "country": "France"},
        {"name": "Diptyque SoHo", "city": "New York", "country": "United States"},
    ])]
    closures, skipped = find_possible_closures(results, index)
    assert skipped == []
    assert len(closures) == 1
    statuses = {row["STATUS"] for row in closures}
    assert statuses == {"TO VERIFY"}
    assert "closed" not in statuses and "confirmed" not in statuses


@pytest.mark.parametrize("overrides,expected_reason_snippet", [
    ({"status": "error"}, "échoué"),
    ({"status": "manual"}, "manuelle"),
    ({"confidence": "manuelle"}, "manuelle"),
    ({"partial": True}, "tronqu"),
])
def test_find_possible_closures_skips_unreliable_scrapes(tmp_path, overrides, expected_reason_snippet):
    index = build_bible_index(_kept_rows(tmp_path))
    result = _reliable_diptyque_result([{"name": "Diptyque Lyon", "city": "Lyon", "country": "France"}])
    result.update(overrides)
    closures, skipped = find_possible_closures([result], index)
    assert closures == []
    assert len(skipped) == 1
    assert expected_reason_snippet in skipped[0]["reason"]


def test_find_possible_closures_skips_incomplete_coverage(tmp_path):
    index = build_bible_index(_kept_rows(tmp_path))
    # BIBLE has 4 Diptyque doors; scraper only found 1 (25% coverage) -> skip.
    result = _reliable_diptyque_result([{"name": "Diptyque Lyon", "city": "Lyon", "country": "France"}])
    closures, skipped = find_possible_closures([result], index)
    assert closures == []
    assert len(skipped) == 1
    assert "incomplète" in skipped[0]["reason"]


def test_find_possible_closures_skips_brand_with_no_store_detail(tmp_path):
    index = build_bible_index(_kept_rows(tmp_path))
    result = {"brand": "Diptyque", "status": "ok", "confidence": "haute", "partial": False, "stores": []}
    closures, skipped = find_possible_closures([result], index)
    assert closures == []
    assert len(skipped) == 1


def test_find_possible_closures_ignores_brand_absent_from_bible(tmp_path):
    index = build_bible_index(_kept_rows(tmp_path))
    result = {"brand": "Nishane", "status": "error", "confidence": "haute", "partial": False, "stores": []}
    closures, skipped = find_possible_closures([result], index)
    assert closures == []
    assert skipped == []  # nothing to skip - Nishane isn't even in the BIBLE fixture


# --- regional total differences ------------------------------------------------

def test_find_regional_total_differences_reports_only_nonzero_diffs(tmp_path):
    index = build_bible_index(_kept_rows(tmp_path))
    results = [{
        "brand": "Diptyque", "status": "ok",
        "regions": {"EMEA": 3, "UK": 1, "NOAM": 1, "LATAM": 0, "CHINA": 0, "APAC": 0},
    }]
    diffs = find_regional_total_differences(results, index)
    assert len(diffs) == 1
    assert diffs[0]["REGION"] == "EMEA"
    assert diffs[0]["DOOR COUNT (BIBLE)"] == 2
    assert diffs[0]["SCRAPED COUNT"] == 3
    assert diffs[0]["DIFF"] == 1


def test_find_regional_total_differences_skips_brand_absent_from_bible(tmp_path):
    index = build_bible_index(_kept_rows(tmp_path))
    results = [{"brand": "Nishane", "status": "ok", "regions": {"EMEA": 5, "UK": 0, "NOAM": 0, "LATAM": 0, "CHINA": 0, "APAC": 0}}]
    assert find_regional_total_differences(results, index) == []


# --- write_rows_csv ------------------------------------------------------------

def test_write_rows_csv_writes_and_removes(tmp_path):
    path = tmp_path / "out.csv"
    n = write_rows_csv([{"a": 1, "b": 2}], path)
    assert n == 1
    assert path.exists()
    with path.open() as f:
        assert list(csv.DictReader(f)) == [{"a": "1", "b": "2"}]

    n2 = write_rows_csv([], path)
    assert n2 == 0
    assert not path.exists()


# --- legacy CSV backward compatibility ------------------------------------------

def test_legacy_csv_compare_still_works(tmp_path):
    path = tmp_path / "legacy_export.csv"
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["BRAND", "EMEA", "UK", "NOAM", "LATAM", "CHINA", "APAC", "TOTAL", "SOURCE", "DATE"])
        writer.writerow(["Diptyque", "38", "9", "40", "0", "43", "42", "172", "manual", "2026-01-01"])

    existing = load_existing_export(path)
    results = [{"brand": "Diptyque", "status": "ok", "total": 172,
                "regions": {"EMEA": 38, "UK": 9, "NOAM": 40, "LATAM": 0, "CHINA": 43, "APAC": 42}}]
    assert compare_with_existing(results, existing) == []
