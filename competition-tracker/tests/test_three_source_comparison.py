from pdf_reference import parse_reference_data
from three_source_comparison import (
    STATUS_MANUAL_REVIEW, STATUS_MATCH, STATUS_MINOR, STATUS_PDF_CONTRADICTION,
    STATUS_SIGNIFICANT, STATUS_WEBSITE_PARTIAL, build_three_source_rows, write_three_source_csv,
)

KNOWN_BRANDS = ["Parfums de Marly", "Amouage", "Diptyque"]

PDM_PAGE = {
    "page_number": 12, "has_images": False,
    "text": (
        "PARFUMS DE MARLY\nWorldwide FSS total: 24 boutiques\nUpdated: February 2026\n"
        "Regional breakdown:\nEMEA: 12\nUK: 2\nNOAM: 6\nLATAM: 1\nCHINA: 2\nAPAC: 1\n"
    ),
}
AMOUAGE_OVERVIEW_PAGE = {
    "page_number": 40, "has_images": False,
    "text": "AMOUAGE\nGlobal overview\nWorldwide total: 20 boutiques\n",
}
AMOUAGE_REGIONAL_PAGE = {
    "page_number": 44, "has_images": False,
    "text": "AMOUAGE\nRegional detail\nWorldwide: 30 boutiques total\nEMEA: 15\nNOAM: 8\nAPAC: 7\n",
}


def _bible_index(region_totals):
    return {"region_totals": region_totals}


def test_pdm_worldwide_row_is_minor_difference():
    pdf_records = parse_reference_data([PDM_PAGE], KNOWN_BRANDS)
    results = [{
        "brand": "Parfums de Marly", "status": "ok", "confidence": "moyenne", "partial": False,
        "regions": {"EMEA": 13, "UK": 2, "NOAM": 6, "LATAM": 1, "CHINA": 2, "APAC": 1}, "total": 25,
    }]
    bible_index = _bible_index({"parfums de marly": {"EMEA": 12, "UK": 2, "NOAM": 6, "LATAM": 1, "CHINA": 2, "APAC": 1}})

    rows = build_three_source_rows(results, bible_index, pdf_records)
    worldwide = next(r for r in rows if r["BRAND"] == "Parfums de Marly" and r["REGION"] == "WORLDWIDE")
    assert worldwide["WEBSITE_TOTAL"] == 25
    assert worldwide["BIBLE_TOTAL"] == 24
    assert worldwide["PDF_REFERENCE_TOTAL"] == 24
    assert worldwide["PDF_REFERENCE_DATE"] == "February 2026"
    assert worldwide["PDF_PAGE"] == "12"
    assert worldwide["STATUS"] == STATUS_MINOR


def test_pdm_uk_region_matches_exactly():
    pdf_records = parse_reference_data([PDM_PAGE], KNOWN_BRANDS)
    results = [{
        "brand": "Parfums de Marly", "status": "ok", "confidence": "haute", "partial": False,
        "regions": {"EMEA": 12, "UK": 2, "NOAM": 6, "LATAM": 1, "CHINA": 2, "APAC": 1}, "total": 24,
    }]
    bible_index = _bible_index({"parfums de marly": {"EMEA": 12, "UK": 2, "NOAM": 6, "LATAM": 1, "CHINA": 2, "APAC": 1}})

    rows = build_three_source_rows(results, bible_index, pdf_records)
    uk_row = next(r for r in rows if r["BRAND"] == "Parfums de Marly" and r["REGION"] == "UK")
    assert uk_row["STATUS"] == STATUS_MATCH
    assert uk_row["WEBSITE_VS_BIBLE"] == 0
    assert uk_row["WEBSITE_VS_PDF"] == 0
    assert uk_row["BIBLE_VS_PDF"] == 0


def test_amouage_worldwide_row_is_pdf_contradiction():
    pdf_records = parse_reference_data([AMOUAGE_OVERVIEW_PAGE, AMOUAGE_REGIONAL_PAGE], KNOWN_BRANDS)
    results = [{
        "brand": "Amouage", "status": "ok", "confidence": "moyenne", "partial": False,
        "regions": {"EMEA": 16, "UK": 0, "NOAM": 8, "LATAM": 0, "CHINA": 0, "APAC": 7}, "total": 31,
    }]
    bible_index = _bible_index({"amouage": {"EMEA": 14, "UK": 0, "NOAM": 8, "LATAM": 0, "CHINA": 0, "APAC": 6}})

    rows = build_three_source_rows(results, bible_index, pdf_records)
    worldwide = next(r for r in rows if r["BRAND"] == "Amouage" and r["REGION"] == "WORLDWIDE")
    assert worldwide["STATUS"] == STATUS_PDF_CONTRADICTION
    assert worldwide["PDF_REFERENCE_TOTAL"] is None  # never reconciled to one number
    assert "20, 30" in worldwide["NOTES"] or "[20, 30]" in worldwide["NOTES"]
    assert worldwide["PDF_PAGE"] == "40, 44"


def test_significant_difference_detected():
    results = [{
        "brand": "Diptyque", "status": "ok", "confidence": "haute", "partial": False,
        "regions": {"EMEA": 38, "UK": 9, "NOAM": 40, "LATAM": 0, "CHINA": 43, "APAC": 42}, "total": 172,
    }]
    bible_index = _bible_index({"diptyque": {"EMEA": 10, "UK": 12, "NOAM": 39, "LATAM": 0, "CHINA": 37, "APAC": 22}})

    rows = build_three_source_rows(results, bible_index, [])
    emea_row = next(r for r in rows if r["BRAND"] == "Diptyque" and r["REGION"] == "EMEA")
    assert emea_row["STATUS"] == STATUS_SIGNIFICANT
    assert emea_row["WEBSITE_VS_BIBLE"] == 28


def test_website_partial_when_scraper_failed():
    results = [{"brand": "Diptyque", "status": "error", "error": "HTTP 403", "confidence": "haute", "partial": False,
                "regions": {r: 0 for r in ("EMEA", "UK", "NOAM", "LATAM", "CHINA", "APAC")}, "total": 0}]
    bible_index = _bible_index({"diptyque": {"EMEA": 10, "UK": 12, "NOAM": 39, "LATAM": 0, "CHINA": 37, "APAC": 22}})

    rows = build_three_source_rows(results, bible_index, [])
    emea_row = next(r for r in rows if r["BRAND"] == "Diptyque" and r["REGION"] == "EMEA")
    assert emea_row["STATUS"] == STATUS_WEBSITE_PARTIAL
    assert emea_row["WEBSITE_TOTAL"] is None  # a failed scrape's 0 is not treated as a real value


def test_website_partial_when_confidence_manuelle():
    results = [{"brand": "Diptyque", "status": "ok", "confidence": "manuelle", "partial": False,
                "regions": {"EMEA": 5, "UK": 0, "NOAM": 0, "LATAM": 0, "CHINA": 0, "APAC": 0}, "total": 5}]
    bible_index = _bible_index({"diptyque": {"EMEA": 10, "UK": 0, "NOAM": 0, "LATAM": 0, "CHINA": 0, "APAC": 0}})

    rows = build_three_source_rows(results, bible_index, [])
    emea_row = next(r for r in rows if r["BRAND"] == "Diptyque" and r["REGION"] == "EMEA")
    assert emea_row["STATUS"] == STATUS_WEBSITE_PARTIAL


def test_website_partial_when_scrape_flagged_partial():
    results = [{"brand": "Diptyque", "status": "ok", "confidence": "haute", "partial": True,
                "regions": {"EMEA": 5, "UK": 0, "NOAM": 0, "LATAM": 0, "CHINA": 0, "APAC": 0}, "total": 5}]
    bible_index = _bible_index({"diptyque": {"EMEA": 10, "UK": 0, "NOAM": 0, "LATAM": 0, "CHINA": 0, "APAC": 0}})

    rows = build_three_source_rows(results, bible_index, [])
    emea_row = next(r for r in rows if r["BRAND"] == "Diptyque" and r["REGION"] == "EMEA")
    assert emea_row["STATUS"] == STATUS_WEBSITE_PARTIAL


def test_manual_review_when_only_one_source_has_a_value():
    # BIBLE only, nothing scraped this run and no PDF - can't meaningfully compare.
    results = []
    bible_index = _bible_index({"nishane": {"EMEA": 9, "UK": 1, "NOAM": 0, "LATAM": 0, "CHINA": 0, "APAC": 2}})

    rows = build_three_source_rows(results, bible_index, [])
    emea_row = next(r for r in rows if r["BRAND"] == "nishane" and r["REGION"] == "EMEA")
    assert emea_row["STATUS"] == STATUS_MANUAL_REVIEW


def test_rows_with_nothing_in_any_source_are_skipped():
    results = [{"brand": "Diptyque", "status": "ok", "confidence": "haute", "partial": False,
                "regions": {"EMEA": 0, "UK": 0, "NOAM": 0, "LATAM": 0, "CHINA": 0, "APAC": 0}, "total": 0}]
    rows = build_three_source_rows(results, None, [])
    # LATAM is genuinely 0/0/None everywhere -> not worth a row.
    assert not any(r["REGION"] == "LATAM" and r["BRAND"] == "Diptyque" for r in rows)


def test_write_three_source_csv_writes_and_removes(tmp_path):
    path = tmp_path / "three_source_comparison.csv"
    rows = [{
        "BRAND": "X", "REGION": "EMEA", "WEBSITE_TOTAL": 1, "BIBLE_TOTAL": 1, "PDF_REFERENCE_TOTAL": None,
        "WEBSITE_VS_BIBLE": 0, "WEBSITE_VS_PDF": None, "BIBLE_VS_PDF": None,
        "PDF_REFERENCE_DATE": None, "PDF_PAGE": None, "STATUS": "MATCH", "NOTES": "ok",
    }]
    n = write_three_source_csv(rows, path)
    assert n == 1
    assert path.exists()

    n2 = write_three_source_csv([], path)
    assert n2 == 0
    assert not path.exists()
