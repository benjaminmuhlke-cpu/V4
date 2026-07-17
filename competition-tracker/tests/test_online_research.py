import pytest

from online_research import add_research_entry, build_fallback_rows, load_cache


def _valid_entry(**overrides):
    base = {
        "brand": "Penhaligon's", "region": "UK", "country": "United Kingdom", "city": "London",
        "store_name": "Penhaligon's Burlington Arcade", "address": "16-17 Burlington Arcade",
        "url": "https://www.penhaligons.com/uk/en/store-finder", "source_title": "Store Finder",
        "source_domain": "penhaligons.com", "source_type": "official_brand_website", "source_date": None,
        "store_classification": "FSS", "confidence": "high", "evidence": "Listed on official store finder",
        "status": "CONFIRMED", "verification_notes": "Official source, no ambiguity",
    }
    base.update(overrides)
    return base


def test_add_research_entry_rejects_missing_brand():
    cache = load_cache("/nonexistent/path/never/read.json")
    with pytest.raises(ValueError, match="brand"):
        add_research_entry(cache, _valid_entry(brand=None))


def test_add_research_entry_rejects_blank_brand():
    cache = load_cache("/nonexistent/path/never/read.json")
    with pytest.raises(ValueError, match="brand"):
        add_research_entry(cache, _valid_entry(brand=""))


def test_add_research_entry_rejects_bad_confidence():
    cache = load_cache("/nonexistent/path/never/read.json")
    with pytest.raises(ValueError):
        add_research_entry(cache, _valid_entry(confidence="very-high"))


def test_add_research_entry_accepts_valid_entry_and_is_retrievable():
    cache = load_cache("/nonexistent/path/never/read.json")
    cache = add_research_entry(cache, _valid_entry())
    rows = build_fallback_rows(cache, ["Penhaligon's"])
    assert len(rows) == 1
    assert rows[0]["STORE_NAME"] == "Penhaligon's Burlington Arcade"
    assert rows[0]["STATUS"] == "CONFIRMED"
