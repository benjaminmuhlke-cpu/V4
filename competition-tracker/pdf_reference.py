"""Etape 4ter (extended): "Competition Distribution.pdf" as an optional,
manually-researched reference source - complementary to the BIBLE, never a
replacement for it and never auto-trusted.

The PDF is read-only (pdfplumber never writes back), and its layout is
free-form prose/bullet points rather than a structured table, so extraction
here is a conservative, line-by-line heuristic parser: anything that
doesn't clearly match an expected pattern is recorded as "ambiguous"
(kind="ambiguous") rather than guessed at - see build_ambiguities_rows().
Contradictory values (e.g. two different worldwide totals for the same
brand on different pages) are never reconciled automatically; both are
kept, each with its own source page, and flagged.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from brand_aliases import brand_match_key
from normalize import normalize
from region_mapping import REGIONS

MONTH_NAMES = (
    "january|february|march|april|may|june|july|august|september|october|november|december|"
    "janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre"
)

_WORLDWIDE_TOTAL_RE = re.compile(
    r"(?i)\bworldwide\b[^\d]{0,25}(\d{1,4})\b|(\d{1,4})\b[^\d]{0,25}\bworldwide\b"
)
_REGIONAL_BREAKDOWN_RE = re.compile(
    r"(?i)^\s*(" + "|".join(REGIONS) + r")\b\s*[:\-–—]?\s*(\d{1,4})\b"
)
_UPDATE_DATE_RE = re.compile(
    rf"(?i)\b(?:updated?|last update|mise\s*à\s*jour|derni[eè]re?\s*mise\s*à\s*jour)\b[^\w]{{0,10}}"
    rf"([A-Za-zéûàè]+\s+\d{{4}})"
)
_BULLET_LINE_RE = re.compile(r"^\s*[-•*]\s*(.+)$")
_BULLET_CITY_NAME_RE = re.compile(r"^([A-Za-zÀ-ÿ .'\-]{2,40}?)\s*[:\-–—]\s*(.+)$")
# A line is worth flagging as "ambiguous" (not silently dropped) if it has a
# number and looks like it might be data, but matched none of the patterns
# above.
_LOOKS_LIKE_DATA_RE = re.compile(r"(?i)\d.*\b(fss|fsf|boutique|store|door|shop)s?\b|\b(fss|fsf|boutique|store|door|shop)s?\b.*\d")


def _new_record(**kwargs) -> dict:
    record = {
        "kind": None,
        "brand": None,
        "reference_date": None,
        "worldwide_fss_total": None,
        "region": None,
        "country": None,
        "city": None,
        "boutique_name": None,
        "source_page": None,
        "notes": None,
        "confidence": None,
        "photo_available": False,
        "photo_page": None,
    }
    record.update(kwargs)
    return record


def extract_pdf_pages(path: Path | str) -> list[dict]:
    """Read-only page-by-page text (+ whether the page contains any images)
    from the PDF. Never modifies the file - pdfplumber only reads.
    """
    import pdfplumber

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Reference PDF not found at {path}")

    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            has_images = bool(page.images)
            pages.append({"page_number": i, "text": text, "has_images": has_images})
    return pages


def _find_brand_header(line: str, known_brands: list[str]) -> str | None:
    """A line is a brand header if, once normalized/alias-resolved, it
    equals one of the known brand names and isn't just a brand name
    mentioned in passing inside a longer sentence (headers are short,
    standalone lines)."""
    stripped = line.strip()
    if not stripped or len(stripped) > 60:
        return None
    key = brand_match_key(stripped)
    for brand in known_brands:
        if key == brand_match_key(brand):
            return brand
    return None


def parse_reference_data(pages: list[dict], known_brands: list[str]) -> list[dict]:
    """Line-by-line heuristic extraction across all pages. Returns a flat
    list of records (kind: worldwide_total | regional_breakdown | boutique |
    ambiguous), each carrying its own source_page - never merged across
    pages, so contradictions stay visible rather than being averaged away.
    """
    records: list[dict] = []
    current_brand: str | None = None
    current_date: str | None = None
    segment_id = 0
    segment_dates: dict[int, str] = {}

    for page in pages:
        page_number = page["page_number"]
        has_images = page["has_images"]

        for raw_line in page["text"].splitlines():
            line = raw_line.strip()
            if not line:
                continue

            header_brand = _find_brand_header(line, known_brands)
            if header_brand:
                current_brand = header_brand
                current_date = None
                segment_id += 1
                continue

            date_match = _UPDATE_DATE_RE.search(line)
            if date_match:
                current_date = date_match.group(1).strip()
                segment_dates[segment_id] = current_date
                # A date line can appear on the same line as other data
                # (e.g. "Worldwide: 24 boutiques - Updated February 2026"),
                # so keep processing this line for the other patterns too.

            worldwide_match = _WORLDWIDE_TOTAL_RE.search(line)
            if worldwide_match and current_brand:
                total = int(worldwide_match.group(1) or worldwide_match.group(2))
                records.append(_new_record(
                    segment_id=segment_id,
                    kind="worldwide_total", brand=current_brand, reference_date=current_date,
                    worldwide_fss_total=total, source_page=page_number,
                    confidence="haute", notes=line,
                    photo_available=has_images, photo_page=page_number if has_images else None,
                ))
                continue

            regional_match = _REGIONAL_BREAKDOWN_RE.match(line)
            if regional_match and current_brand:
                region = regional_match.group(1).upper()
                count = int(regional_match.group(2))
                records.append(_new_record(
                    segment_id=segment_id,
                    kind="regional_breakdown", brand=current_brand, reference_date=current_date,
                    region=region, worldwide_fss_total=count, source_page=page_number,
                    confidence="haute", notes=line,
                    photo_available=has_images, photo_page=page_number if has_images else None,
                ))
                continue

            bullet_match = _BULLET_LINE_RE.match(line)
            if bullet_match and current_brand:
                city_name_match = _BULLET_CITY_NAME_RE.match(bullet_match.group(1))
                if city_name_match:
                    city, boutique_name = city_name_match.groups()
                    records.append(_new_record(
                        segment_id=segment_id,
                        kind="boutique", brand=current_brand, reference_date=current_date,
                        city=city.strip(), boutique_name=boutique_name.strip(), source_page=page_number,
                        confidence="moyenne", notes=line,
                        photo_available=has_images, photo_page=page_number if has_images else None,
                    ))
                    continue
                # Bulleted but not "City: Name" shaped - a bullet marker
                # under a known brand is deliberate enough to record rather
                # than drop; keep whatever text there is and flag the city
                # as unclear rather than guessing one.
                records.append(_new_record(
                    segment_id=segment_id,
                    kind="boutique", brand=current_brand, reference_date=current_date,
                    boutique_name=bullet_match.group(1).strip(), source_page=page_number,
                    confidence="basse", notes=f"ville non identifiée dans : {line}",
                    photo_available=has_images, photo_page=page_number if has_images else None,
                ))
                continue

            if current_brand and _LOOKS_LIKE_DATA_RE.search(line):
                records.append(_new_record(
                    segment_id=segment_id,
                    kind="ambiguous", brand=current_brand, reference_date=current_date,
                    source_page=page_number, confidence="basse",
                    notes=f"contenu non reconnu automatiquement : {line}",
                    photo_available=has_images, photo_page=page_number if has_images else None,
                ))

    # A date line can appear anywhere in its section (often after the totals
    # it describes), so backfill any record still missing a reference_date
    # from whatever date was found in the same brand-section, then drop the
    # internal segment_id - it's not part of the public record schema.
    for record in records:
        if record["reference_date"] is None:
            record["reference_date"] = segment_dates.get(record["segment_id"])
        del record["segment_id"]

    return records


def find_worldwide_total_contradictions(records: list[dict]) -> dict[str, list[dict]]:
    """Group worldwide_total records by brand; a brand with more than one
    distinct value is a contradiction - both/all values are returned, never
    reconciled to a single number.
    """
    by_brand: dict[str, list[dict]] = {}
    for record in records:
        if record["kind"] != "worldwide_total":
            continue
        by_brand.setdefault(brand_match_key(record["brand"]), []).append(record)

    contradictions = {}
    for key, brand_records in by_brand.items():
        distinct_values = {r["worldwide_fss_total"] for r in brand_records}
        if len(distinct_values) > 1:
            contradictions[brand_records[0]["brand"]] = brand_records
    return contradictions


def find_regional_breakdown_contradictions(records: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """Same idea as find_worldwide_total_contradictions but per (brand,
    region): e.g. two different pages both claiming an EMEA count for the
    same brand, with different numbers."""
    by_brand_region: dict[tuple[str, str], list[dict]] = {}
    for record in records:
        if record["kind"] != "regional_breakdown":
            continue
        key = (brand_match_key(record["brand"]), record["region"])
        by_brand_region.setdefault(key, []).append(record)

    contradictions = {}
    for key, region_records in by_brand_region.items():
        distinct_values = {r["worldwide_fss_total"] for r in region_records}
        if len(distinct_values) > 1:
            contradictions[(region_records[0]["brand"], key[1])] = region_records
    return contradictions


def validate_regional_breakdown_sum(records: list[dict], brand: str) -> dict:
    """Sum this brand's regional_breakdown records and compare against every
    worldwide_total candidate found for it (there may be more than one if
    the PDF contradicts itself - see find_worldwide_total_contradictions).

    Returns {"regional_sum": int|None, "worldwide_totals": [int, ...],
    "matches": {total: bool}, "regions_found": [str, ...]}.
    """
    key = brand_match_key(brand)
    regional = [r for r in records if r["kind"] == "regional_breakdown" and brand_match_key(r["brand"]) == key]
    worldwide = [r for r in records if r["kind"] == "worldwide_total" and brand_match_key(r["brand"]) == key]

    regional_sum = sum(r["worldwide_fss_total"] for r in regional) if regional else None
    worldwide_totals = sorted({r["worldwide_fss_total"] for r in worldwide})

    return {
        "regional_sum": regional_sum,
        "worldwide_totals": worldwide_totals,
        "matches": {total: (regional_sum == total) for total in worldwide_totals},
        "regions_found": sorted({r["region"] for r in regional}),
    }


def build_ambiguities_rows(records: list[dict]) -> list[dict]:
    """Everything a human should double-check before trusting the PDF data:
    unclear lines (kind="ambiguous"), and contradictions (multiple distinct
    values for the same brand/region) - both worldwide and regional level.
    """
    rows = []

    for record in records:
        if record["kind"] == "ambiguous":
            rows.append({
                "BRAND": record["brand"], "TYPE": "UNCLEAR", "VALUE": None,
                "PDF_PAGE": record["source_page"], "NOTE": record["notes"],
                "PDF_PHOTO_AVAILABLE": record["photo_available"], "PDF_PHOTO_PAGE": record["photo_page"],
            })
        elif record["kind"] == "boutique" and record["confidence"] == "basse":
            rows.append({
                "BRAND": record["brand"], "TYPE": "INCOMPLETE_BOUTIQUE_ENTRY", "VALUE": record["boutique_name"],
                "PDF_PAGE": record["source_page"], "NOTE": record["notes"],
                "PDF_PHOTO_AVAILABLE": record["photo_available"], "PDF_PHOTO_PAGE": record["photo_page"],
            })

    for brand, contradicting in find_worldwide_total_contradictions(records).items():
        for record in contradicting:
            rows.append({
                "BRAND": brand, "TYPE": "CONTRADICTION_WORLDWIDE_TOTAL", "VALUE": record["worldwide_fss_total"],
                "PDF_PAGE": record["source_page"],
                "NOTE": f"valeurs contradictoires trouvées pour cette marque : {sorted({r['worldwide_fss_total'] for r in contradicting})}",
                "PDF_PHOTO_AVAILABLE": record["photo_available"], "PDF_PHOTO_PAGE": record["photo_page"],
            })

    for (brand, region), contradicting in find_regional_breakdown_contradictions(records).items():
        for record in contradicting:
            rows.append({
                "BRAND": brand, "TYPE": f"CONTRADICTION_REGIONAL_{region}", "VALUE": record["worldwide_fss_total"],
                "PDF_PAGE": record["source_page"],
                "NOTE": f"valeurs contradictoires pour {region} : {sorted({r['worldwide_fss_total'] for r in contradicting})}",
                "PDF_PHOTO_AVAILABLE": record["photo_available"], "PDF_PHOTO_PAGE": record["photo_page"],
            })

    return rows


def save_reference_json(records: list[dict], path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_ambiguities_csv(rows: list[dict], path: Path | str) -> int:
    path = Path(path)
    if not rows:
        if path.exists():
            path.unlink()
        return 0
    fieldnames = ["BRAND", "TYPE", "VALUE", "PDF_PAGE", "NOTE", "PDF_PHOTO_AVAILABLE", "PDF_PHOTO_PAGE"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
