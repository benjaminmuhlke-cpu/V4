"""One normalization rule, used everywhere a brand/region/country/city/door
name needs to be compared: strip accents, lowercase, collapse punctuation
and whitespace. Same rule for every field so "Saint-Honore", "saint honoré"
and "SAINT  HONORE" all compare equal.
"""

from __future__ import annotations

import re
import unicodedata


def normalize(text) -> str:
    if text is None:
        return ""
    text = str(text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
