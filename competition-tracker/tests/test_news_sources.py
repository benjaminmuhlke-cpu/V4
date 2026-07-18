from news_sources import CATEGORIES, load_news_sources, slugify, source_priorities

EXPECTED_NAMES = {
    "FashionNetwork", "The Moodie Davitt Report", "TRBusiness",
    "Global Travel Retail Magazine", "The Business of Fashion", "Journal du Luxe",
    "Global Cosmetics News", "CPP-LUXURY.COM", "Global Cosmetics Industry",
    "The Fragrance Foundation", "Cosmetics Business", "Retail Beauty",
    "Retail Scope", "Retail in Asia", "Vogue Business",
}

REQUIRED_FIELDS = (
    "name", "website", "linkedin", "category", "priority", "geographic_focus",
    "covers_travel_retail", "covers_luxury", "covers_beauty_fragrance",
    "search_method", "notes",
)


def test_every_curated_news_source_loads_from_configuration():
    sources = load_news_sources()
    names = {s["name"] for s in sources}
    assert names == EXPECTED_NAMES


def test_every_source_has_the_required_fields():
    for source in load_news_sources():
        for field in REQUIRED_FIELDS:
            assert field in source, f"{source.get('name')} is missing '{field}'"
        assert source["category"] in CATEGORIES
        assert source["priority"] in (1, 2, 3)


def test_slugify_is_deterministic_and_matches_recent_openings_gating():
    from recent_openings import CURATED_NEWS_SOURCE_TYPES

    for source in load_news_sources():
        assert slugify(source["name"]) in CURATED_NEWS_SOURCE_TYPES


def test_source_priorities_match_the_documented_tiers():
    priorities = source_priorities()
    assert priorities[slugify("FashionNetwork")] == 2
    assert priorities[slugify("Journal du Luxe")] == 3
    assert priorities[slugify("The Moodie Davitt Report")] == 2
