from datetime import date

import openpyxl

from recent_openings import (
    RECENT_OPENINGS_COLUMNS,
    RECENT_OPENINGS_SHEET,
    TO_VERIFY_COLUMNS,
    TO_VERIFY_SHEET,
    build_recent_openings_rows,
    write_recent_openings_workbook,
)


def _brand_result(brand="Maison Francis Kurkdjian", slug="mfk", stores=None, status="ok"):
    return {
        "brand": brand,
        "slug": slug,
        "status": status,
        "stores": stores or [],
    }


def _store(name="Maison Francis Kurkdjian Houston", address="4444 Westheimer Rd", city="Houston", country="United States"):
    return {
        "name": name,
        "address": address,
        "city": city,
        "country": country,
        "region": "NOAM",
    }


def _entry(**overrides):
    base = {
        "brand": "Maison Francis Kurkdjian",
        "region": "NOAM",
        "country": "United States",
        "city": "Houston",
        "store_name": "Maison Francis Kurkdjian Houston",
        "address": "4444 Westheimer Rd",
        "url": "https://example.com/opening",
        "source_title": "Opening News",
        "source_domain": "example.com",
        "source_type": "industry_publication",
        "source_date": "2026-07-01",
        "store_classification": "FSS",
        "confidence": "medium",
        "status": "CONFIRMED",
        "verification_notes": "Verified",
        "evidence": "Evidence",
    }
    base.update(overrides)
    return base


def test_store_already_in_bible_is_excluded():
    results = [_brand_result(stores=[_store()])]
    bible_index = {
        "by_door_key": {
            ("maison francis kurkdjian", "united states", "houston", "maison francis kurkdjian houston"): [{}],
        }
    }
    recent_rows, verify_rows, summary = build_recent_openings_rows(
        results,
        bible_index,
        {"entries": [_entry()]},
        checked_date=date(2026, 7, 17),
    )
    assert recent_rows == []
    assert verify_rows == []
    assert summary.recent_openings_found == 0
    assert summary.excluded_in_bible == 1


def test_scraper_door_name_differs_from_bible_but_entry_name_matches_it():
    """Mirrors Parfums de Marly Le Marais: the live locator scrape names the
    door differently ("Boutique Marais") than the BIBLE does ("LE MARAIS"),
    but the research entry's own store_name matches the BIBLE exactly. The
    pair must be recognized as already tracked either way, not reported as
    a new opening just because the scraper's own wording didn't match."""
    results = [_brand_result(
        brand="Parfums de Marly", slug="pdm",
        stores=[_store(
            name="Parfums de Marly, Boutique Marais",
            address="45, rue Vieille du Temple",
            city="Paris", country="France",
        )],
    )]
    bible_index = {
        "by_door_key": {
            ("parfums de marly", "france", "paris", "parfums de marly le marais"): [{}],
        }
    }
    entry = _entry(
        brand="Parfums de Marly", region="EMEA", country="France", city="Paris",
        store_name="Parfums de Marly Le Marais",
        address="45 rue Vieille du Temple, 75004 Paris, France",
        source_type="official_brand_store_page", source_date="2026-06-20",
    )
    recent_rows, verify_rows, summary = build_recent_openings_rows(
        results, bible_index, {"entries": [entry]}, checked_date=date(2026, 7, 17),
    )
    assert recent_rows == []
    assert verify_rows == []
    assert summary.excluded_in_bible == 1


def test_department_store_is_excluded():
    recent_rows, verify_rows, summary = build_recent_openings_rows(
        [_brand_result(stores=[_store()])],
        {"by_door_key": {}},
        {"entries": [_entry(store_classification="department store")]},
        checked_date=date(2026, 7, 17),
    )
    assert recent_rows == []
    assert verify_rows == []
    assert summary.excluded_non_fss_fsf == 1


def test_perfumery_is_excluded():
    recent_rows, verify_rows, summary = build_recent_openings_rows(
        [_brand_result(stores=[_store()])],
        {"by_door_key": {}},
        {"entries": [_entry(store_classification="wholesale")]},
        checked_date=date(2026, 7, 17),
    )
    assert recent_rows == []
    assert verify_rows == []
    assert summary.excluded_non_fss_fsf == 1


def test_opening_source_within_60_days_is_included():
    recent_rows, verify_rows, summary = build_recent_openings_rows(
        [_brand_result(stores=[_store()])],
        {"by_door_key": {}},
        {"entries": [_entry(source_date="2026-07-10")]},
        checked_date=date(2026, 7, 17),
    )
    assert len(recent_rows) == 1
    assert verify_rows == []
    assert recent_rows[0]["OPENING DATE"] == "2026-07-10"
    assert summary.recent_openings_found == 1


def test_old_announcement_is_excluded_not_to_verify():
    """A known opening date outside the recent window is a resolved fact,
    not an open question - it must be excluded outright, never parked in
    TO VERIFY (TO VERIFY is reserved for unknown-date candidates only)."""
    recent_rows, verify_rows, summary = build_recent_openings_rows(
        [_brand_result(stores=[_store()])],
        {"by_door_key": {}},
        {"entries": [_entry(source_date="2026-04-01")]},
        checked_date=date(2026, 7, 17),
    )
    assert recent_rows == []
    assert verify_rows == []
    assert summary.to_verify_count == 0
    assert summary.excluded_old_openings == 1


def test_known_old_date_from_a_source_below_priority_threshold_is_still_excluded_not_to_verify():
    """Even when the source itself is too weak to promote to RECENT
    OPENINGS, a known-but-old date must not be reported as if the date
    were unknown."""
    recent_rows, verify_rows, summary = build_recent_openings_rows(
        [_brand_result(stores=[_store()])],
        {"by_door_key": {}},
        {"entries": [_entry(source_date="2026-04-01", source_type="unlisted_source_type")]},
        checked_date=date(2026, 7, 17),
    )
    assert recent_rows == []
    assert verify_rows == []
    assert summary.excluded_old_openings == 1


def test_unknown_opening_date_goes_to_to_verify():
    recent_rows, verify_rows, summary = build_recent_openings_rows(
        [_brand_result(stores=[_store()])],
        {"by_door_key": {}},
        {"entries": [_entry(source_date=None)]},
        checked_date=date(2026, 7, 17),
    )
    assert recent_rows == []
    assert len(verify_rows) == 1
    assert verify_rows[0]["REASON TO VERIFY"] == "opening source has no date"
    assert summary.to_verify_count == 1


def test_duplicate_boutiques_are_removed():
    recent_rows, verify_rows, summary = build_recent_openings_rows(
        [_brand_result(stores=[_store(), _store()])],
        {"by_door_key": {}},
        {"entries": [_entry(), _entry(source_title="Backup Source")]},
        checked_date=date(2026, 7, 17),
    )
    assert len(recent_rows) == 1
    assert verify_rows == []
    assert summary.recent_openings_found == 1


def test_recent_official_announcement_absent_from_bible_is_included_without_store_locator_match():
    results = [_brand_result(brand="Byredo", slug="byredo", stores=[])]
    recent_rows, verify_rows, summary = build_recent_openings_rows(
        results,
        {"by_door_key": {}},
        {"entries": [_entry(
            brand="Byredo",
            region="APAC",
            country="Hong Kong",
            city="Hong Kong",
            store_name="Byredo Gough Street",
            address="2-10 Gough Street, Hong Kong",
            url="https://example.com/byredo",
            source_title="Byredo Opens New Boutique",
            source_type="official_brand_newsroom",
            source_date="2026-07-10",
            store_classification="FSS",
            confidence="high",
            verification_notes="Official opening post",
        )]},
        checked_date=date(2026, 7, 17),
    )
    assert len(recent_rows) == 1
    assert verify_rows == []
    assert recent_rows[0]["BRAND"] == "Byredo"
    assert summary.recent_openings_by_brand == {"Byredo": 1}


def test_credible_mall_or_landlord_announcement_is_included():
    results = [_brand_result(stores=[])]
    recent_rows, verify_rows, summary = build_recent_openings_rows(
        results,
        {"by_door_key": {}},
        {"entries": [_entry(
            city="Miami",
            store_name="Maison Francis Kurkdjian - Miami Design District",
            address="176 NE 41st St, Miami, FL",
            url="https://example.com/mall",
            source_title="Miami Design District",
            source_type="official_mall_landlord_directory",
            source_date="2026-07-05",
            store_classification="FSS",
            confidence="high",
            verification_notes="Official landlord directory",
        )]},
        checked_date=date(2026, 7, 17),
    )
    assert len(recent_rows) == 1
    assert verify_rows == []
    assert summary.recent_openings_found == 1


def test_workbook_has_both_sheets_and_required_columns(tmp_path):
    output_path = tmp_path / "recent_openings.xlsx"
    write_recent_openings_workbook([{
        "BRAND": "Maison Francis Kurkdjian",
        "REGION": "NOAM",
        "COUNTRY": "United States",
        "CITY": "Houston",
        "DOOR NAME": "Maison Francis Kurkdjian Houston",
        "FULL ADDRESS": "4444 Westheimer Rd",
        "DOOR TYPE": "FSS",
        "OPENING DATE": "2026-07-01",
        "SOURCE": "Opening News",
        "SOURCE URL": "https://example.com/opening",
        "DATE CHECKED": "2026-07-17",
        "NOTES": "Verified",
    }], [{
        "BRAND": "Creed",
        "REGION": "EMEA",
        "COUNTRY": "France",
        "CITY": "Paris",
        "DOOR NAME": "Creed Paris",
        "FULL ADDRESS": "38 Avenue Pierre 1er de Serbie",
        "REASON TO VERIFY": "opening source has no date",
        "SOURCE": "Listing",
        "SOURCE URL": "https://example.com/verify",
        "DATE CHECKED": "2026-07-17",
        "NOTES": "Check",
    }], output_path)

    workbook = openpyxl.load_workbook(output_path)
    try:
        assert workbook.sheetnames == [RECENT_OPENINGS_SHEET, TO_VERIFY_SHEET]
        recent_sheet = workbook[RECENT_OPENINGS_SHEET]
        verify_sheet = workbook[TO_VERIFY_SHEET]
        assert [cell.value for cell in recent_sheet[1]] == RECENT_OPENINGS_COLUMNS
        assert [cell.value for cell in verify_sheet[1]] == TO_VERIFY_COLUMNS
        assert recent_sheet.freeze_panes == "A2"
        assert recent_sheet.auto_filter.ref == recent_sheet.dimensions
    finally:
        workbook.close()


def test_hyperlinks_are_clickable(tmp_path):
    output_path = tmp_path / "recent_openings.xlsx"
    write_recent_openings_workbook([{
        "BRAND": "Maison Francis Kurkdjian",
        "REGION": "NOAM",
        "COUNTRY": "United States",
        "CITY": "Houston",
        "DOOR NAME": "Maison Francis Kurkdjian Houston",
        "FULL ADDRESS": "4444 Westheimer Rd",
        "DOOR TYPE": "FSS",
        "OPENING DATE": "2026-07-01",
        "SOURCE": "Opening News",
        "SOURCE URL": "https://example.com/opening",
        "DATE CHECKED": "2026-07-17",
        "NOTES": "Verified",
    }], [], output_path)

    workbook = openpyxl.load_workbook(output_path)
    try:
        cell = workbook[RECENT_OPENINGS_SHEET]["J2"]
        assert cell.value == "https://example.com/opening"
        assert cell.hyperlink is not None
        assert cell.hyperlink.target == "https://example.com/opening"
    finally:
        workbook.close()
