import json

import pytest

from pdf_reference import (
    build_ambiguities_rows, extract_pdf_pages, find_regional_breakdown_contradictions,
    find_worldwide_total_contradictions, parse_reference_data, save_reference_json,
    validate_regional_breakdown_sum, write_ambiguities_csv,
)

KNOWN_BRANDS = [
    "Diptyque", "Maison Francis Kurkdjian", "Juliette Has A Gun", "Maison Margiela",
    "Parfums de Marly", "Amouage", "Creed", "Nishane", "L'Artisan Parfumeur", "Penhaligon's", "Caron",
]

# Fabricated page text mirroring exactly the two brands called out in the
# brief: Parfums de Marly (clean, worldwide total = sum of the regional
# breakdown, dated February 2026) and Amouage (contradiction: global
# overview page says 20, a later regional-detail page says 30).
PDM_OVERVIEW_PAGE = {
    "page_number": 12,
    "has_images": False,
    "text": (
        "PARFUMS DE MARLY\n"
        "\n"
        "Worldwide FSS total: 24 boutiques\n"
        "Updated: February 2026\n"
        "\n"
        "Regional breakdown:\n"
        "EMEA: 12\n"
        "UK: 2\n"
        "NOAM: 6\n"
        "LATAM: 1\n"
        "CHINA: 2\n"
        "APAC: 1\n"
    ),
}
PDM_BOUTIQUES_PAGE = {
    "page_number": 13,
    "has_images": True,
    "text": (
        "PARFUMS DE MARLY - Boutiques\n"
        "\n"
        "- Paris: Parfums de Marly Saint-Honoré\n"
        "- London: Parfums de Marly Mayfair\n"
        "- New York: Parfums de Marly Madison Avenue\n"
    ),
}
AMOUAGE_OVERVIEW_PAGE = {
    "page_number": 40,
    "has_images": False,
    "text": (
        "AMOUAGE\n"
        "\n"
        "Global overview\n"
        "Worldwide total: 20 boutiques\n"
    ),
}
AMOUAGE_REGIONAL_PAGE = {
    "page_number": 44,
    "has_images": False,
    "text": (
        "AMOUAGE\n"
        "\n"
        "Regional detail\n"
        "Worldwide: 30 boutiques total\n"
        "EMEA: 15\n"
        "NOAM: 8\n"
        "APAC: 7\n"
    ),
}


@pytest.fixture
def pdm_and_amouage_records():
    pages = [PDM_OVERVIEW_PAGE, PDM_BOUTIQUES_PAGE, AMOUAGE_OVERVIEW_PAGE, AMOUAGE_REGIONAL_PAGE]
    return parse_reference_data(pages, KNOWN_BRANDS)


# --- Parfums de Marly: clean, consistent section -------------------------------

def test_pdm_worldwide_total_extracted(pdm_and_amouage_records):
    totals = [r for r in pdm_and_amouage_records if r["kind"] == "worldwide_total" and r["brand"] == "Parfums de Marly"]
    assert len(totals) == 1
    assert totals[0]["worldwide_fss_total"] == 24
    assert totals[0]["source_page"] == 12
    assert totals[0]["confidence"] == "haute"


def test_pdm_reference_date_captured_and_backfilled(pdm_and_amouage_records):
    pdm_records = [r for r in pdm_and_amouage_records if r["brand"] == "Parfums de Marly"]
    assert all(r["reference_date"] == "February 2026" for r in pdm_records)


def test_pdm_regional_breakdown_extracted_with_page_numbers(pdm_and_amouage_records):
    regional = [r for r in pdm_and_amouage_records if r["kind"] == "regional_breakdown" and r["brand"] == "Parfums de Marly"]
    by_region = {r["region"]: r["worldwide_fss_total"] for r in regional}
    assert by_region == {"EMEA": 12, "UK": 2, "NOAM": 6, "LATAM": 1, "CHINA": 2, "APAC": 1}
    assert all(r["source_page"] == 12 for r in regional)


def test_pdm_regional_breakdown_sums_to_worldwide_total(pdm_and_amouage_records):
    validation = validate_regional_breakdown_sum(pdm_and_amouage_records, "Parfums de Marly")
    assert validation["regional_sum"] == 24
    assert validation["worldwide_totals"] == [24]
    assert validation["matches"] == {24: True}


def test_pdm_boutique_names_extracted_with_page_and_photo_flag(pdm_and_amouage_records):
    boutiques = [r for r in pdm_and_amouage_records if r["kind"] == "boutique" and r["brand"] == "Parfums de Marly"]
    assert len(boutiques) == 3
    names = {(b["city"], b["boutique_name"]) for b in boutiques}
    assert ("Paris", "Parfums de Marly Saint-Honoré") in names
    assert ("London", "Parfums de Marly Mayfair") in names
    assert ("New York", "Parfums de Marly Madison Avenue") in names
    # These boutiques are on a page pdfplumber reported as containing images.
    assert all(b["source_page"] == 13 for b in boutiques)
    assert all(b["photo_available"] is True and b["photo_page"] == 13 for b in boutiques)


def test_pdm_has_no_contradictions(pdm_and_amouage_records):
    assert find_worldwide_total_contradictions(pdm_and_amouage_records).get("Parfums de Marly") is None
    assert not any(
        brand == "Parfums de Marly" for (brand, _region) in find_regional_breakdown_contradictions(pdm_and_amouage_records)
    )


# --- Amouage: the 20-vs-30 contradiction --------------------------------------

def test_amouage_worldwide_contradiction_detected(pdm_and_amouage_records):
    contradictions = find_worldwide_total_contradictions(pdm_and_amouage_records)
    assert "Amouage" in contradictions
    values_and_pages = {(r["worldwide_fss_total"], r["source_page"]) for r in contradictions["Amouage"]}
    assert values_and_pages == {(20, 40), (30, 44)}


def test_amouage_both_values_preserved_not_reconciled(pdm_and_amouage_records):
    totals = [r for r in pdm_and_amouage_records if r["kind"] == "worldwide_total" and r["brand"] == "Amouage"]
    assert len(totals) == 2  # both 20 and 30 are kept, neither dropped nor averaged
    assert {r["worldwide_fss_total"] for r in totals} == {20, 30}


def test_amouage_contradiction_appears_in_ambiguities_csv(pdm_and_amouage_records, tmp_path):
    rows = build_ambiguities_rows(pdm_and_amouage_records)
    contradiction_rows = [r for r in rows if r["BRAND"] == "Amouage" and r["TYPE"] == "CONTRADICTION_WORLDWIDE_TOTAL"]
    assert len(contradiction_rows) == 2
    pages = {r["PDF_PAGE"] for r in contradiction_rows}
    values = {r["VALUE"] for r in contradiction_rows}
    assert pages == {40, 44}
    assert values == {20, 30}

    path = tmp_path / "pdf_reference_ambiguities.csv"
    n = write_ambiguities_csv(rows, path)
    assert n == len(rows)
    assert path.exists()


def test_amouage_regional_breakdown_not_flagged_as_contradiction(pdm_and_amouage_records):
    # Only page 44 gives a regional split - one source per region, so no
    # region-level contradiction (only the worldwide-level one).
    region_contradictions = find_regional_breakdown_contradictions(pdm_and_amouage_records)
    assert not any(brand == "Amouage" for brand, _region in region_contradictions)


# --- Ambiguous/unclear content is surfaced, never silently guessed ------------

def test_unclear_bullet_line_is_flagged_not_guessed():
    pages = [{
        "page_number": 7, "has_images": False,
        "text": "CARON\nWorldwide total: 3 boutiques\n- some line with no clear city/name split\n",
    }]
    records = parse_reference_data(pages, KNOWN_BRANDS)
    unclear = [r for r in records if r["kind"] == "boutique" and r["confidence"] == "basse"]
    assert len(unclear) == 1
    assert unclear[0]["city"] is None
    assert "ville non identifiée" in unclear[0]["notes"]


def test_write_ambiguities_csv_removes_stale_file_when_empty(tmp_path):
    path = tmp_path / "ambiguities.csv"
    path.write_text("leftover from a previous run")
    n = write_ambiguities_csv([], path)
    assert n == 0
    assert not path.exists()


def test_save_reference_json_round_trips(tmp_path, pdm_and_amouage_records):
    path = tmp_path / "data" / "reference" / "competition_distribution_reference.json"
    saved_path = save_reference_json(pdm_and_amouage_records, path)
    assert saved_path == path
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert len(loaded) == len(pdm_and_amouage_records)
    assert loaded[0]["brand"] == "Parfums de Marly"


# --- Real PDF round-trip (generated on the fly, never a fixture file we edit) --

def test_extract_pdf_pages_reads_text_and_detects_images(tmp_path):
    fpdf = pytest.importorskip("fpdf")
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)
    pdf.add_page()
    pdf.cell(text="PARFUMS DE MARLY")
    pdf.add_page()
    pdf.cell(text="Worldwide FSS total: 24 boutiques")

    # Draw a tiny filled rectangle as image-like content isn't needed - we
    # only need at least one page with an embedded raster image to exercise
    # the has_images flag, so embed a 1x1 pixel PNG.
    import struct
    import zlib

    def _tiny_png() -> bytes:
        width = height = 1
        raw = b"\x00" + b"\xff\x00\x00"  # filter byte + one red pixel
        compressed = zlib.compress(raw)

        def chunk(tag, data):
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

        header = b"\x89PNG\r\n\x1a\n"
        ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        idat = chunk(b"IDAT", compressed)
        iend = chunk(b"IEND", b"")
        return header + ihdr + idat + iend

    png_path = tmp_path / "tiny.png"
    png_path.write_bytes(_tiny_png())
    pdf.image(str(png_path), x=10, y=10, w=5, h=5)

    pdf_path = tmp_path / "synthetic_reference.pdf"
    pdf.output(str(pdf_path))

    pages = extract_pdf_pages(pdf_path)
    assert len(pages) == 2
    assert "PARFUMS DE MARLY" in pages[0]["text"]
    assert "24" in pages[1]["text"]
    assert pages[1]["has_images"] is True
    assert pages[0]["has_images"] is False


def test_extract_pdf_pages_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        extract_pdf_pages(tmp_path / "does_not_exist.pdf")
