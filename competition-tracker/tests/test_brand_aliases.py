from brand_aliases import brand_match_key, canonical_brand_name


def test_known_aliases_resolve_to_canonical_name():
    assert canonical_brand_name("MFK") == "Maison Francis Kurkdjian"
    assert canonical_brand_name("PDM") == "Parfums de Marly"
    assert canonical_brand_name("JHAG") == "Juliette Has A Gun"
    assert canonical_brand_name("L'ARTISAN PARFUMEUR") == "L'Artisan Parfumeur"
    assert canonical_brand_name("PENHALIGON'S") == "Penhaligon's"


def test_alias_and_canonical_name_share_the_same_match_key():
    assert brand_match_key("MFK") == brand_match_key("Maison Francis Kurkdjian")
    assert brand_match_key("PDM") == brand_match_key("Parfums de Marly")
    assert brand_match_key("penhaligon's") == brand_match_key("Penhaligon’s")


def test_unknown_brand_passes_through_unchanged():
    assert canonical_brand_name("Diptyque") == "Diptyque"
    assert canonical_brand_name("Some Unlisted Brand") == "Some Unlisted Brand"


def test_empty_and_none_are_handled():
    assert canonical_brand_name("") == ""
    assert canonical_brand_name(None) is None
