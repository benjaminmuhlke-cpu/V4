"""Static-HTML scrapers (requests + BeautifulSoup).

One dedicated parser per brand's page shape - no generic "universal store
locator parser" abstraction, since each site lays its data out differently
and pretending otherwise just produces silent garbage.
"""

from __future__ import annotations

import time
import urllib.robotparser
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = "CompetitionTrackerBot/1.0 (personal competitive-intel tool; contact: benjaminmuhlke@gmail.com)"
REQUEST_DELAY_SECONDS = 1.5
TIMEOUT_SECONDS = 20

_robots_cache: dict[str, urllib.robotparser.RobotFileParser] = {}


class ScraperError(Exception):
    """Raised when a brand's scraper can't produce data - never fail silently."""


def _robots_allowed(url: str) -> bool:
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    parser = _robots_cache.get(origin)
    if parser is None:
        parser = urllib.robotparser.RobotFileParser()
        try:
            # Fetch with our own UA/timeout via requests rather than
            # RobotFileParser.read()'s built-in urllib call: sites with bot
            # protection 403 the default urllib UA, and robotparser treats a
            # 403 as "disallow everything" - which would wrongly block us
            # from an otherwise-permissive robots.txt.
            resp = requests.get(f"{origin}/robots.txt", headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            else:
                parser = None  # no readable robots.txt -> assume allowed
        except requests.RequestException:
            parser = None
        _robots_cache[origin] = parser
    if parser is None:
        return True
    return parser.can_fetch(USER_AGENT, url)


def polite_get(url: str) -> requests.Response:
    """Fetch a URL respecting robots.txt, with an explicit UA and a rate-limit delay."""
    if not _robots_allowed(url):
        raise ScraperError(f"robots.txt disallows fetching {url}")
    time.sleep(REQUEST_DELAY_SECONDS)
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise ScraperError(f"network error fetching {url}: {exc}") from exc
    if response.status_code != 200:
        raise ScraperError(f"unexpected HTTP {response.status_code} fetching {url}")
    return response


def scrape_diptyque(url: str) -> list[dict]:
    """Diptyque's 'all-addresses' page gives a direct per-country total under
    4 region headers (Europe / Middle East / Asia / North America) - no need
    to extract individual store addresses.

    Returns a list of {"country": str, "count": int, "name": None, "source": url}.
    """
    html = polite_get(url).text
    soup = BeautifulSoup(html, "html.parser")
    boxes = soup.find_all("div", class_="directory-box-inner")
    if not boxes:
        raise ScraperError(
            f"Diptyque page structure changed: no 'directory-box-inner' blocks found at {url}"
        )

    records = []
    for box in boxes:
        country_div = box.find("div", class_="country-name")
        if not country_div:
            continue
        for link in country_div.find_all("a"):
            sup = link.find("sup")
            count = int(sup.get_text(strip=True)) if sup else 0
            if sup:
                sup.extract()
            country = link.get_text(strip=True)
            records.append({"country": country, "count": count, "name": None, "source": url})

    if not records:
        raise ScraperError(f"Diptyque page parsed but yielded zero countries at {url}")
    return records


def scrape_mfk(url: str) -> list[dict]:
    """Maison Francis Kurkdjian's store locator (Salesforce Commerce Cloud) is
    server-rendered in full, but mixes monobrand boutiques with multi-brand
    wholesale resellers and has no per-store country field - only a
    freeform "postal code + city" string. FSS filtering and country
    resolution happen downstream in aggregate.py; this parser only extracts
    what the page actually contains.

    Returns a list of {"name": str, "address": str, "city_postal": str,
    "count": 1, "source": url}.
    """
    html = polite_get(url).text
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("li", class_="core-storelocator-item")
    if not items:
        raise ScraperError(
            f"MFK page structure changed: no 'core-storelocator-item' entries found at {url}"
        )

    records = []
    for item in items:
        name_el = item.find("h2", class_="core-storelocator-itemStore")
        name_btn = name_el.find("button") if name_el else None
        name = name_btn.get_text(strip=True) if name_btn else None
        if not name:
            continue

        address_spans = item.find_all("span", class_="core-storelocator-addressText")
        address = ", ".join(s.get_text(strip=True) for s in address_spans)

        city_span = item.find("span", class_="core-storelocator-city")
        city_postal = city_span.get_text(strip=True) if city_span else None

        records.append({
            "name": name,
            "address": address,
            "city_postal": city_postal,
            "count": 1,
            "source": url,
        })

    if not records:
        raise ScraperError(f"MFK page parsed but yielded zero stores at {url}")
    return records


def scrape_nishane(url: str) -> list[dict]:
    """NISHANE's own /boutiques/ page (Elementor info-box widgets), one box
    per boutique: a city/name title and a free-text address. "Coming Soon"
    locations aren't open yet and are dropped here - not a scraping
    ambiguity, just not a store yet.

    Returns a list of {"name": str, "address": str, "count": 1, "source": url}.
    """
    html = polite_get(url).text
    soup = BeautifulSoup(html, "html.parser")
    boxes = soup.find_all("div", class_="wd-info-box")
    if not boxes:
        raise ScraperError(f"NISHANE page structure changed: no 'wd-info-box' entries found at {url}")

    records = []
    for box in boxes:
        title = box.find(class_="info-box-title")
        content = box.find(class_="info-box-inner")
        city = title.get_text(strip=True) if title else None
        address = content.get_text(" ", strip=True) if content else ""
        if not city:
            continue
        if "coming soon" in address.lower():
            continue
        # The page's own title is just the city (e.g. "PARIS") since every
        # entry is already a NISHANE boutique - synthesize a proper name so
        # the brand-keyword filter and city->country resolution both work.
        records.append({"name": f"NISHANE {city}", "city": city, "address": address, "count": 1, "source": url})

    if not records:
        raise ScraperError(f"NISHANE page parsed but yielded zero open boutiques at {url}")
    return records


def scrape_caron(url: str) -> list[dict]:
    """Caron's "Our boutiques" page (Shopify "sn-text-image" sections), one
    section per boutique with a title (name, city) and a content block
    (address). The page also has a generic "Our store locator" section with
    the same markup but no address - dropped via the has-address check
    rather than a hardcoded title match.

    Returns a list of {"name": str, "address": str, "count": 1, "source": url}.
    """
    html = polite_get(url).text
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.find_all("div", class_="sn-text-image")
    if not blocks:
        raise ScraperError(f"Caron page structure changed: no 'sn-text-image' blocks found at {url}")

    records = []
    for block in blocks:
        title = block.find(class_="sn-text-image__title")
        content = block.find(class_="sn-text-image__content")
        name = title.get_text(strip=True) if title else None
        address = content.get_text(" ", strip=True) if content else ""
        # The page reuses the same markup for a non-store "international
        # store locator" teaser block; a real address always has a street
        # number / postal code in it, that teaser doesn't.
        if not name or not any(ch.isdigit() for ch in address):
            continue
        records.append({"name": name, "address": address, "count": 1, "source": url})

    if not records:
        raise ScraperError(f"Caron page parsed but yielded zero boutiques at {url}")
    return records
