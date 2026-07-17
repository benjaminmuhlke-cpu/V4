"""JS-rendered store locators - last resort per the project's own rule:
check for a JSON endpoint behind the widget before reaching for a headless
browser. So far every js_widget brand in brands.yaml is a Stockist widget,
which exposes exactly such an endpoint (confirmed via its widget.js bundle:
`GET https://stockist.co/api/v1/{tag}/locations/search?latitude=..&longitude=..&radius=..`).
Stockist has no "list everything" endpoint, only radius search, so global
coverage means querying a grid of major-city coordinates and de-duplicating
by location id.
"""

from __future__ import annotations

import time

import requests

from scrapers.static import USER_AGENT, REQUEST_DELAY_SECONDS, TIMEOUT_SECONDS, ScraperError

STOCKIST_SEARCH_URL = "https://stockist.co/api/v1/{tag}/locations/search"
STOCKIST_SEARCH_RADIUS_KM = 250
# Stockist widgets are commonly configured with max_results=100 (confirmed
# in JHAG's and Parfums de Marly's widget.js); a single grid point returning
# close to that many locations means real matches were likely cut off, not
# that we exhaustively found everything near that point.
STOCKIST_LIKELY_CAP = 90

# One point per major retail metro area, wide enough to reach every region in
# the brief's taxonomy (EMEA / UK / NOAM / LATAM / CHINA / APAC) at a 250km
# radius. Not exhaustive - a brand with a store between grid points and more
# than 250km from all of them would be missed; the delta report and
# _a_verifier.csv are there to catch anything that looks off.
WORLD_CITY_GRID = [
    ("London", 51.5074, -0.1278), ("Paris", 48.8566, 2.3522), ("Milan", 45.4642, 9.19),
    ("Madrid", 40.4168, -3.7038), ("Berlin", 52.52, 13.405), ("Zurich", 47.3769, 8.5417),
    ("Amsterdam", 52.3676, 4.9041), ("Stockholm", 59.3293, 18.0686),
    ("Dubai", 25.2048, 55.2708), ("Riyadh", 24.7136, 46.6753), ("Doha", 25.2854, 51.531),
    ("Istanbul", 41.0082, 28.9784), ("Cairo", 30.0444, 31.2357), ("Casablanca", 33.5731, -7.5898),
    ("Johannesburg", -26.2041, 28.0473),
    ("New York", 40.7128, -74.006), ("Los Angeles", 34.0522, -118.2437), ("Miami", 25.7617, -80.1918),
    ("Chicago", 41.8781, -87.6298), ("Dallas", 32.7767, -96.797),
    ("Toronto", 43.6532, -79.3832), ("Vancouver", 49.2827, -123.1207),
    ("Mexico City", 19.4326, -99.1332), ("Sao Paulo", -23.5505, -46.6333),
    ("Buenos Aires", -34.6037, -58.3816), ("Bogota", 4.711, -74.0721), ("Santiago", -33.4489, -70.6693),
    ("Beijing", 39.9042, 116.4074), ("Shanghai", 31.2304, 121.4737), ("Guangzhou", 23.1291, 113.2644),
    ("Hong Kong", 22.3193, 114.1694),
    ("Tokyo", 35.6762, 139.6503), ("Seoul", 37.5665, 126.978), ("Taipei", 25.033, 121.5654),
    ("Singapore", 1.3521, 103.8198), ("Bangkok", 13.7563, 100.5018), ("Kuala Lumpur", 3.139, 101.6869),
    ("Jakarta", -6.2088, 106.8456), ("Sydney", -33.8688, 151.2093), ("Melbourne", -37.8136, 144.9631),
    ("Mumbai", 19.076, 72.8777), ("Delhi", 28.7041, 77.1025),
]


def scrape_stockist(widget_tag: str, referer_url: str) -> tuple[list[dict], bool]:
    """Query the Stockist JSON API across WORLD_CITY_GRID and return the
    de-duplicated union of locations found.

    Returns (records, partial). Each record is
    {"name", "address", "city", "country", "count": 1, "source"} - country
    may be None (Stockist doesn't always fill it in), resolved downstream in
    aggregate.py same as MFK. partial is True if any single grid point came
    back at/near STOCKIST_LIKELY_CAP results, meaning some matches near that
    point were probably clipped rather than genuinely absent - closure
    detection should not trust a scrape flagged this way.
    """
    seen_ids: set[int] = set()
    records: list[dict] = []
    failures = 0
    partial = False

    for city_label, lat, lon in WORLD_CITY_GRID:
        time.sleep(REQUEST_DELAY_SECONDS)
        try:
            response = requests.get(
                STOCKIST_SEARCH_URL.format(tag=widget_tag),
                params={"latitude": lat, "longitude": lon, "radius": STOCKIST_SEARCH_RADIUS_KM},
                headers={"User-Agent": USER_AGENT, "Referer": referer_url},
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            failures += 1
            continue

        locations = payload.get("locations", [])
        if len(locations) >= STOCKIST_LIKELY_CAP:
            partial = True

        for loc in locations:
            loc_id = loc.get("id")
            if loc_id in seen_ids:
                continue
            seen_ids.add(loc_id)
            records.append({
                "name": loc.get("name"),
                "address": loc.get("address_line_1"),
                "city": loc.get("city"),
                "country": loc.get("country"),
                "count": 1,
                "source": f"stockist:{widget_tag} (near {city_label})",
                "source_location_id": loc_id,
            })

    if not records:
        raise ScraperError(
            f"Stockist widget '{widget_tag}' returned zero locations across "
            f"{len(WORLD_CITY_GRID)} grid points ({failures} failed) - check the tag is still valid"
        )
    return records, partial


def scrape_dynamic_playwright(url: str, item_selector: str, name_selector: str | None = None) -> list[dict]:
    """Genuine last resort: render the page and read the DOM. Only use this
    when a brand's JS widget has no JSON API behind it (checked its network
    tab / JS bundle and found nothing to call directly).

    item_selector: CSS selector for one store's container element.
    name_selector: optional CSS selector (relative to each item) for the
    store name; defaults to the item's own text if omitted.

    Returns a list of {"name": str, "text": str, "count": 1, "source": url}.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ScraperError(
            "playwright is not installed - run `pip install playwright && playwright install chromium`"
        ) from exc

    records = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(url, timeout=30_000, wait_until="networkidle")
            page.wait_for_selector(item_selector, timeout=15_000)
            for item in page.query_selector_all(item_selector):
                name_el = item.query_selector(name_selector) if name_selector else item
                name = name_el.inner_text().strip() if name_el else None
                records.append({
                    "name": name,
                    "text": item.inner_text().strip(),
                    "count": 1,
                    "source": url,
                })
        finally:
            browser.close()

    if not records:
        raise ScraperError(f"Playwright render of {url} found no elements matching '{item_selector}'")
    return records
