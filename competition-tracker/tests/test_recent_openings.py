from diff_existing import build_bible_index
from recent_openings import find_recent_openings

BIBLE_ROWS = [
    {"BRAND": "Parfums de Marly", "COUNTRY": "France", "CITY": "Paris",
     "DOOR NAME": "Parfums de Marly Le Marais", "DOOR TYPE": "FSS", "DOOR COUNT": 1},
]


def _cache(entries):
    return {"entries": entries}


def _entry(**overrides):
    entry = {
        "brand": "Amouage",
        "region": "NOAM",
        "country": "United States",
        "city": "Beverly Hills",
        "store_name": "Amouage Beverly Hills - The Wadi",
        "address": "311 North Beverly Drive, Beverly Hills, CA 90210",
        "url": "https://amouage.com/pages/store-locator",
        "source_type": "official_site",
        "source_date": "2026-06-18",
        "store_classification": "FSS",
        "confidence": "high",
        "evidence": "Official locator lists the address.",
        "status": "CONFIRMED",
    }
    entry.update(overrides)
    return entry


def test_dated_confirmed_opening_absent_from_bible_is_included():
    bible_index = build_bible_index(BIBLE_ROWS)
    opened, to_verify = find_recent_openings(_cache([_entry()]), bible_index)
    assert len(opened) == 1
    assert opened[0]["BRAND"] == "Amouage"
    assert opened[0]["OPENING_EVIDENCE_DATE"] == "2026-06-18"
    assert to_verify == []


def test_dated_confirmed_opening_already_in_bible_is_excluded():
    bible_index = build_bible_index(BIBLE_ROWS)
    entry = _entry(
        brand="Parfums de Marly", country="France", city="Paris",
        store_name="Parfums de Marly Le Marais",
    )
    opened, to_verify = find_recent_openings(_cache([entry]), bible_index)
    assert opened == []
    assert to_verify == []  # already tracked, dated - nothing left to report


def test_undated_entry_goes_to_still_to_verify_even_when_already_in_bible():
    """Mirrors MFK Miami: a real, confirmed door already in the BIBLE but
    with no dated opening evidence - must not be silently dropped just
    because it's already tracked."""
    bible_index = build_bible_index([
        {"BRAND": "MFK", "COUNTRY": "United States", "CITY": "Miami",
         "DOOR NAME": "MFK Miami Design District", "DOOR TYPE": "FSS", "DOOR COUNT": 1},
    ])
    entry = _entry(
        brand="MFK", country="United States", city="Miami",
        store_name="Maison Francis Kurkdjian - Miami Design District",
        source_date=None,
    )
    opened, to_verify = find_recent_openings(_cache([entry]), bible_index)
    assert opened == []
    assert len(to_verify) == 1
    assert to_verify[0]["STATUS"] == "TO VERIFY"
    assert to_verify[0]["BRAND"] == "MFK"


def test_undated_entry_absent_from_bible_also_goes_to_still_to_verify():
    bible_index = build_bible_index([])
    entry = _entry(source_date=None)
    opened, to_verify = find_recent_openings(_cache([entry]), bible_index)
    assert opened == []
    assert len(to_verify) == 1
    assert to_verify[0]["ALREADY_IN_BIBLE"] is False


def test_bare_to_verify_status_without_date_is_never_promoted():
    bible_index = build_bible_index([])
    entry = _entry(status="TO VERIFY", source_date=None)
    opened, to_verify = find_recent_openings(_cache([entry]), bible_index)
    assert opened == []
    assert len(to_verify) == 1


def test_non_fss_classification_is_out_of_scope_entirely():
    bible_index = build_bible_index([])
    entry = _entry(store_classification="wholesale")
    opened, to_verify = find_recent_openings(_cache([entry]), bible_index)
    assert opened == []
    assert to_verify == []  # not a monobrand door - not our concern here


def test_probable_status_with_date_still_counts_as_an_opening():
    bible_index = build_bible_index([])
    entry = _entry(status="PROBABLE")
    opened, to_verify = find_recent_openings(_cache([entry]), bible_index)
    assert len(opened) == 1
    assert opened[0]["STATUS"] == "PROBABLE"


def test_discovery_route_a_when_scraper_independently_found_the_door():
    bible_index = build_bible_index([])
    entry = _entry(store_name="Parfums de Marly, Boutique Marais", brand="Parfums de Marly",
                    country="France", city="Paris")
    results = [{
        "brand": "Parfums de Marly", "status": "ok",
        "stores": [{"name": "Parfums de Marly, Boutique Marais"}],
    }]
    opened, _ = find_recent_openings(_cache([entry]), bible_index, results)
    assert len(opened) == 1
    assert opened[0]["DISCOVERY_ROUTE"].startswith("A")


def test_discovery_route_b_when_scraper_never_returned_the_door():
    bible_index = build_bible_index([])
    entry = _entry()
    results = [{"brand": "Amouage", "status": "ok", "stores": [{"name": "Some Other Door"}]}]
    opened, _ = find_recent_openings(_cache([entry]), bible_index, results)
    assert len(opened) == 1
    assert opened[0]["DISCOVERY_ROUTE"].startswith("B")


def test_missing_store_name_or_brand_is_skipped_defensively():
    bible_index = build_bible_index([])
    entries = [_entry(store_name=None), _entry(brand=None)]
    opened, to_verify = find_recent_openings(_cache(entries), bible_index)
    assert opened == []
    assert to_verify == []
