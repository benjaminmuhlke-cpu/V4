import sys
from pathlib import Path

import run_report

EMPTY_BIBLE_INDEX = {"by_door_key": {}, "by_brand": {}, "region_totals": {}}

BRANDS = [
    {"name": "Parfums de Marly", "slug": "pdm", "store_locator_url": "https://pdm.example/locator"},
    {"name": "Nishane", "slug": "nishane", "store_locator_url": "https://nishane.example/locator"},
]


def _classified_record(name="Parfums de Marly Boutique Le Marais"):
    return {
        "raw_store_name": name,
        "raw_address": "1 Rue de la Paix, Paris",
        "city": "Paris",
        "country": "France",
        "official_source_url": "https://pdm.example/locator",
        "source_location_id": "1",
        "classification": "FSS",
        "classification_reason": "matches boutique_name_patterns",
        "rule_matched": "boutique_name_patterns",
        "confidence": "moyenne",
        "manual_review_required": False,
        "resolved_country": "France",
        "resolved_region": "EMEA",
    }


def _live_results():
    return [
        {
            "brand": "Parfums de Marly", "slug": "pdm", "status": "ok", "confidence": "haute",
            "stores": [{"name": "Parfums de Marly Boutique Le Marais", "city": "Paris", "country": "France", "region": "EMEA"}],
            "scrape_stats": {
                "raw_count": 3,
                "category_counts": {
                    "FSS": 1, "FSF": 0, "DEPARTMENT_STORE": 1, "PERFUMERY": 0,
                    "MULTIBRAND_RETAILER": 1, "CORNER_OR_CONCESSION": 0, "ONLINE": 0, "UNCLEAR": 0,
                },
            },
            "fss_classified_records": [_classified_record()],
        },
        {
            # No dedicated FSS classifier for this brand (generic path) -
            # must be skipped by the diagnostics, never crash on it.
            "brand": "Nishane", "slug": "nishane", "status": "ok", "confidence": "moyenne",
            "stores": [], "scrape_stats": None, "fss_classified_records": None,
        },
    ]


def _patch_common(monkeypatch, tmp_path, include_diagnostics=False):
    monkeypatch.setattr(run_report, "DATA_DIR", tmp_path)
    monkeypatch.setattr(run_report, "run_all", lambda brands, only_slugs=None: _live_results())
    monkeypatch.setattr(run_report, "load_bible_index", lambda path: EMPTY_BIBLE_INDEX)
    monkeypatch.setattr(run_report, "load_research_cache", lambda: {"entries": []})
    written = {}

    def fake_write_workbook(recent_rows, verify_rows, path):
        written["recent_rows"] = recent_rows
        written["verify_rows"] = verify_rows
        return Path(path)

    monkeypatch.setattr(run_report, "write_recent_openings_workbook", fake_write_workbook)

    argv = [
        "run_report.py", "--brands", "pdm,nishane",
        "--existing-file", str(tmp_path / "fake_bible.xlsx"),
        "--output", str(tmp_path / "recent_openings.xlsx"),
        "--no-email",
    ]
    if include_diagnostics:
        argv.append("--include-classifier-diagnostics")
    monkeypatch.setattr(sys, "argv", argv)
    return written


def test_default_run_does_not_generate_diagnostic_csvs(tmp_path, monkeypatch):
    _patch_common(monkeypatch, tmp_path, include_diagnostics=False)
    run_report.main()
    assert not (tmp_path / "fss_filter_quality.csv").exists()
    assert not (tmp_path / "fss_validation_sample.csv").exists()


def test_flag_generates_both_diagnostic_csvs(tmp_path, monkeypatch):
    _patch_common(monkeypatch, tmp_path, include_diagnostics=True)
    run_report.main()
    assert (tmp_path / "fss_filter_quality.csv").exists()
    assert (tmp_path / "fss_validation_sample.csv").exists()

    quality_csv = (tmp_path / "fss_filter_quality.csv").read_text(encoding="utf-8")
    assert "Parfums de Marly" in quality_csv
    assert "Nishane" not in quality_csv  # no dedicated classifier for it - skipped, not crashed on


def test_diagnostics_do_not_alter_recent_openings_rows(tmp_path, monkeypatch):
    without = _patch_common(monkeypatch, tmp_path, include_diagnostics=False)
    run_report.main()

    with_diagnostics = _patch_common(monkeypatch, tmp_path, include_diagnostics=True)
    run_report.main()

    assert without["recent_rows"] == with_diagnostics["recent_rows"]
    assert without["verify_rows"] == with_diagnostics["verify_rows"]

