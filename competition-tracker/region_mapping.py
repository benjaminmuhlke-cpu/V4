"""Country -> region lookup (EMEA / UK / NOAM / LATAM / CHINA / APAC).

Region taxonomy matches the BIBLE Excel tracker columns.
"""

UK = "UK"
NOAM = "NOAM"
LATAM = "LATAM"
CHINA = "CHINA"
APAC = "APAC"
EMEA = "EMEA"

REGIONS = [EMEA, UK, NOAM, LATAM, CHINA, APAC]

# Countries with names/aliases as they tend to appear on store-locator sites.
# Keys are lowercased for lookup; see normalize_country().
_COUNTRY_REGION = {
    "united kingdom": UK,
    "uk": UK,
    "great britain": UK,
    "england": UK,
    "scotland": UK,
    "wales": UK,
    "northern ireland": UK,
    "united states": NOAM,
    "usa": NOAM,
    "us": NOAM,
    "united states of america": NOAM,
    "canada": NOAM,
    "mexico": LATAM,
    "brazil": LATAM,
    "argentina": LATAM,
    "chile": LATAM,
    "colombia": LATAM,
    "peru": LATAM,
    "uruguay": LATAM,
    "panama": LATAM,
    "costa rica": LATAM,
    "dominican republic": LATAM,
    "ecuador": LATAM,
    "venezuela": LATAM,
    "china": CHINA,
    "hong kong": CHINA,
    "macau": CHINA,
    "macao": CHINA,
    "japan": APAC,
    "south korea": APAC,
    "korea, south": APAC,
    "korea": APAC,
    "taiwan": APAC,
    "singapore": APAC,
    "malaysia": APAC,
    "indonesia": APAC,
    "thailand": APAC,
    "vietnam": APAC,
    "philippines": APAC,
    "india": APAC,
    "australia": APAC,
    "new zealand": APAC,
    "cambodia": APAC,
}

# Every remaining ISO country in Europe / Middle East / Africa defaults to EMEA
# via the fallback list below (kept short and explicit rather than a giant
# ISO-3166 table we don't need for ~20 brands worth of store locators).
_EMEA_COUNTRIES = {
    "france", "germany", "italy", "spain", "portugal", "switzerland",
    "austria", "belgium", "netherlands", "luxembourg", "ireland",
    "sweden", "norway", "denmark", "finland", "iceland",
    "poland", "czechia", "czech republic", "slovakia", "hungary",
    "romania", "bulgaria", "greece", "croatia", "slovenia", "serbia",
    "cyprus", "malta", "estonia", "latvia", "lithuania",
    "united arab emirates", "uae", "saudi arabia", "qatar", "kuwait",
    "bahrain", "oman", "jordan", "lebanon", "israel", "turkey", "türkiye",
    "egypt", "morocco", "tunisia", "algeria", "south africa", "nigeria",
    "andorra", "monaco", "san marino", "russia", "ukraine",
}
for _country in _EMEA_COUNTRIES:
    _COUNTRY_REGION[_country] = EMEA

# Some store-locator APIs (Stockist in particular) return ISO-3166 alpha-2
# codes instead of full country names, inconsistently even within the same
# brand's data. Map the codes we've actually seen rather than pulling in a
# full ISO table for a handful of brands.
_ISO2_REGION = {
    "gb": UK, "uk": UK,
    "us": NOAM, "ca": NOAM,
    "mx": LATAM, "br": LATAM, "ar": LATAM, "cl": LATAM, "co": LATAM, "pe": LATAM,
    "cn": CHINA, "hk": CHINA, "mo": CHINA,
    "jp": APAC, "kr": APAC, "tw": APAC, "sg": APAC, "my": APAC, "id": APAC,
    "th": APAC, "vn": APAC, "ph": APAC, "in": APAC, "au": APAC, "nz": APAC,
    "fr": EMEA, "de": EMEA, "it": EMEA, "es": EMEA, "pt": EMEA, "ch": EMEA,
    "at": EMEA, "be": EMEA, "nl": EMEA, "lu": EMEA, "ie": EMEA,
    "se": EMEA, "no": EMEA, "dk": EMEA, "fi": EMEA, "is": EMEA,
    "pl": EMEA, "cz": EMEA, "sk": EMEA, "hu": EMEA, "ro": EMEA, "bg": EMEA,
    "gr": EMEA, "hr": EMEA, "si": EMEA, "rs": EMEA, "cy": EMEA, "mt": EMEA,
    "ee": EMEA, "lv": EMEA, "lt": EMEA,
    "ae": EMEA, "sa": EMEA, "qa": EMEA, "kw": EMEA, "bh": EMEA, "om": EMEA,
    "jo": EMEA, "lb": EMEA, "il": EMEA, "tr": EMEA, "eg": EMEA, "ma": EMEA,
    "tn": EMEA, "dz": EMEA, "za": EMEA, "ng": EMEA, "ad": EMEA, "mc": EMEA,
    "ru": EMEA, "ua": EMEA,
}
_COUNTRY_REGION.update(_ISO2_REGION)


def normalize_country(name: str) -> str:
    return " ".join(name.strip().lower().split())


def get_region(country_name: str) -> str | None:
    """Return one of REGIONS, or None if the country isn't recognized."""
    if not country_name:
        return None
    return _COUNTRY_REGION.get(normalize_country(country_name))
