"""Etape 4bis: download a photo for each newly-detected store, when the
scraper found one. This reduces manual work, it doesn't replace it - most
brands simply won't have an exploitable photo, and that's expected: those
get a placeholder note instead of an image.
"""

from __future__ import annotations

import re
from pathlib import Path

import requests

from scrapers.static import TIMEOUT_SECONDS, USER_AGENT

BASE_DIR = Path(__file__).parent
PHOTOS_DIR = BASE_DIR / "photos"


def _slugify(text: str) -> str:
    text = (text or "sans-nom").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "sans-nom"


def download_store_photos(brand_slug: str, new_stores: list[dict]) -> list[str]:
    """Download a photo for each new store that has an image_url, otherwise
    write a placeholder .txt. Returns the list of file paths written."""
    if not new_stores:
        return []

    brand_dir = PHOTOS_DIR / brand_slug
    brand_dir.mkdir(parents=True, exist_ok=True)
    written = []

    for store in new_stores:
        label = _slugify(store.get("city") or store.get("name"))
        image_url = store.get("image_url")

        if not image_url:
            placeholder = brand_dir / f"{label}.txt"
            placeholder.write_text(
                f"Photo à ajouter manuellement pour : {store.get('name')} ({store.get('city') or ''})\n"
                f"Aucune image trouvée sur le store locator de la marque.\n",
                encoding="utf-8",
            )
            written.append(str(placeholder))
            continue

        dest = brand_dir / f"{label}.jpg"
        try:
            response = requests.get(image_url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            dest.write_bytes(response.content)
            written.append(str(dest))
        except requests.RequestException as exc:
            placeholder = brand_dir / f"{label}.txt"
            placeholder.write_text(
                f"Photo à ajouter manuellement pour : {store.get('name')} ({store.get('city') or ''})\n"
                f"Le téléchargement a échoué ({exc}) - URL trouvée : {image_url}\n",
                encoding="utf-8",
            )
            written.append(str(placeholder))

    return written
