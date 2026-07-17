from fss_classifier import classify_location, classify_locations

RULES = {
    "acme": {
        "boutique_name_patterns": ["acme boutique"],
        "flagship_name_patterns": ["acme flagship"],
        "exact_inclusions": ["Acme Historic Atelier"],
        "exact_exclusions": ["acme manufacture and visitor's centre"],
        "retailer_blocklist": ["mario's fine fragrances", "the gents place"],
        "department_store_patterns": ["nordstrom", "saks fifth avenue"],
        "perfumery_patterns": ["parfumerie", "profumeria"],
        "mall_or_location_exceptions": ["acme dubai mall kiosk"],
        "known_fss_addresses": ["1 rue de la paix, 75002 paris"],
        "known_non_fss_addresses": ["acme corner at the mall of america"],
    },
}


def _rec(name, address="", city="", country="", source="test"):
    return {"name": name, "address": address, "city": city, "country": country, "source": source}


def test_department_store_excluded():
    result = classify_location(_rec("Nordstrom Seattle"), "acme", RULES)
    assert result["classification"] == "DEPARTMENT_STORE"
    assert result["manual_review_required"] is False


def test_perfumery_excluded():
    result = classify_location(_rec("Parfumerie Steenmans"), "acme", RULES)
    assert result["classification"] == "PERFUMERY"


def test_exact_known_boutique_included():
    result = classify_location(_rec("Acme Historic Atelier"), "acme", RULES)
    assert result["classification"] == "FSS"
    assert result["confidence"] == "haute"
    assert result["manual_review_required"] is False


def test_ambiguous_mall_location_is_rescued_but_flagged_for_review():
    """A mall address can still be an FSS - the exception list rescues it
    from looking like generic mall noise, but a human still double-checks it."""
    result = classify_location(_rec("Acme Dubai Mall Kiosk"), "acme", RULES)
    assert result["classification"] == "FSS"
    assert result["manual_review_required"] is True


def test_brand_name_inside_a_wholesale_retailer_name_is_not_fss():
    """The brand's own name appearing inside a reseller's name must never be
    enough to call it FSS on its own."""
    result = classify_location(_rec("Mario's Fine Fragrances (Acme Corner)"), "acme", RULES)
    assert result["classification"] == "MULTIBRAND_RETAILER"


def test_accented_and_punctuated_names_still_match():
    result = classify_location(_rec("Acmé Boutique - Champs-Élysées!"), "acme", RULES)
    assert result["classification"] == "FSS"
    assert result["rule_matched"] == "boutique_name_patterns"


def test_flagship_pattern_classified_as_fsf():
    result = classify_location(_rec("Acme Flagship New York"), "acme", RULES)
    assert result["classification"] == "FSF"


def test_unmatched_location_is_unclear_never_guessed():
    result = classify_location(_rec("Random Concept Store"), "acme", RULES)
    assert result["classification"] == "UNCLEAR"
    assert result["manual_review_required"] is True


def test_brand_with_no_configured_rules_is_all_unclear():
    result = classify_location(_rec("Anything At All"), "unknown_brand", RULES)
    assert result["classification"] == "UNCLEAR"
    assert result["manual_review_required"] is True


def test_duplicate_locations_are_each_classified_independently():
    records = [_rec("Nordstrom Seattle"), _rec("Nordstrom Seattle"), _rec("Nordstrom Seattle")]
    results = classify_locations(records, "acme", RULES)
    assert len(results) == 3
    assert all(r["classification"] == "DEPARTMENT_STORE" for r in results)


def test_empty_records_list_from_a_failed_scraper_yields_no_classifications():
    assert classify_locations([], "acme", RULES) == []


def test_known_non_fss_address_is_corner_or_concession_and_flagged():
    result = classify_location(_rec("Acme Store", address="Acme Corner at the Mall of America"), "acme", RULES)
    assert result["classification"] == "CORNER_OR_CONCESSION"
    assert result["manual_review_required"] is True


def test_known_fss_address_overrides_a_generic_name():
    result = classify_location(_rec("Store #4471", address="1 Rue de la Paix, 75002 Paris"), "acme", RULES)
    assert result["classification"] == "FSS"
    assert result["rule_matched"] == "known_fss_addresses"


def test_online_marker_classified_as_online():
    result = classify_location(_rec("Acme Store", city="Online"), "acme", RULES)
    assert result["classification"] == "ONLINE"
