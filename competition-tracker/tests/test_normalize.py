from normalize import normalize


def test_case_and_whitespace():
    assert normalize("SAINT   HONORE   PARIS") == normalize("Saint Honore Paris")


def test_accents():
    assert normalize("Boutique Dubaï") == normalize("Boutique Dubai")
    assert normalize("Côte d'Ivoire") == normalize("Cote d Ivoire")


def test_punctuation():
    assert normalize("Saint-Honoré, Paris") == normalize("Saint Honore Paris")
    assert normalize("L'Artisan Parfumeur") == normalize("L Artisan Parfumeur")


def test_none_and_non_string():
    assert normalize(None) == ""
    assert normalize(123) == "123"


def test_curly_apostrophe():
    assert normalize("Côte d’Ivoire") == normalize("Cote d Ivoire")
