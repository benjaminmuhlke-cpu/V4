import pytest

from coverage_audit import AUDIT_COLUMNS, build_audit_row
from region_mapping import REGIONS


def _brand_config(**overrides):
    base = {
        "name": "Test Brand", "slug": "test", "scraper_type": "static_html",
        "store_locator_url": "https://example.com", "confidence": "moyenne", "notes": "",
    }
    base.update(overrides)
    return base


def _result(**overrides):
    base = {
        "brand": "Test Brand", "slug": "test", "status": "ok", "partial": False,
        "regions": {r: 0 for r in REGIONS}, "total": 0, "stores": [],
        "scrape_stats": {"raw_count": 10, "included_count": 10, "blocklist_excluded_count": 0,
                          "ambiguous_count": 0, "name_ambiguous_count": 0},
    }
    base.update(overrides)
    return base


def test_audit_columns_derived_from_regions():
    for region in REGIONS:
        assert f"{region}_STATUS" in AUDIT_COLUMNS


# --- OVERALL_STATUS: decoupled from confidence -------------------------------

def test_overall_status_complete_regardless_of_moyenne_confidence():
    row = build_audit_row(_brand_config(confidence="moyenne"), _result(status="ok", partial=False))
    assert row["OVERALL_STATUS"] == "complete"


def test_overall_status_partial_when_scrape_flagged_partial():
    row = build_audit_row(_brand_config(confidence="haute"), _result(status="ok", partial=True))
    assert row["OVERALL_STATUS"] == "partial"


def test_overall_status_failed_and_manual():
    failed = build_audit_row(_brand_config(), _result(status="error"))
    assert failed["OVERALL_STATUS"] == "failed"

    manual_config = _brand_config(scraper_type="manual")
    manual_result = _result(status="manual", scrape_stats=None)
    assert build_audit_row(manual_config, manual_result)["OVERALL_STATUS"] == "manual"


# --- FSS_FILTER_RELIABLE: name-ambiguity only, not geo-ambiguity -------------

def test_fss_filter_reliable_true_for_haute_confidence_regardless_of_stats():
    row = build_audit_row(_brand_config(confidence="haute"), _result(
        scrape_stats={"raw_count": 10, "included_count": 10, "blocklist_excluded_count": 0,
                      "ambiguous_count": 8, "name_ambiguous_count": 8},
    ))
    assert row["FSS_FILTER_RELIABLE"] is True


def test_fss_filter_reliable_false_for_manuelle_confidence():
    row = build_audit_row(_brand_config(confidence="manuelle"), _result())
    assert row["FSS_FILTER_RELIABLE"] is False


def test_fss_filter_reliable_ignores_geo_ambiguity_not_caused_by_name_mismatch():
    # All 10 stores matched the brand name fine (name_ambiguous_count=0) but
    # hit unmapped countries (ambiguous_count=10, geo-only) - the filter
    # itself is completely reliable, this must not be dragged down to False.
    row = build_audit_row(_brand_config(confidence="moyenne"), _result(
        scrape_stats={"raw_count": 10, "included_count": 10, "blocklist_excluded_count": 0,
                      "ambiguous_count": 10, "name_ambiguous_count": 0},
    ))
    assert row["FSS_FILTER_RELIABLE"] is True


def test_fss_filter_reliable_false_when_name_ambiguity_ratio_high():
    row = build_audit_row(_brand_config(confidence="moyenne"), _result(
        scrape_stats={"raw_count": 4, "included_count": 3, "blocklist_excluded_count": 1,
                      "ambiguous_count": 3, "name_ambiguous_count": 3},
    ))
    assert row["FSS_FILTER_RELIABLE"] is False


def test_fss_filter_reliable_false_for_aggregate_only_source_below_haute():
    # included_count=None is the sentinel for "no per-store filter ever ran"
    # (Diptyque-style country-totals-only sources) - there's nothing to
    # vouch for here below "haute" confidence, regardless of any ratio.
    row = build_audit_row(_brand_config(confidence="moyenne"), _result(
        scrape_stats={"raw_count": 28, "included_count": None, "blocklist_excluded_count": 0,
                      "ambiguous_count": 0, "name_ambiguous_count": 0},
    ))
    assert row["FSS_FILTER_RELIABLE"] is False
