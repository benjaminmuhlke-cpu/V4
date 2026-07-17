"""Brand name aliasing: different sources spell the same brand differently
(the BIBLE calls Maison Francis Kurkdjian "MFK", the PDF might too) -
resolve to brands.yaml's canonical name before any cross-source matching.
"""

from __future__ import annotations

import json
from pathlib import Path

from normalize import normalize

BASE_DIR = Path(__file__).parent
ALIASES_PATH = BASE_DIR / "brand_aliases.json"


def load_aliases() -> dict[str, str]:
    data = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
    return {normalize(alias): canonical for alias, canonical in data["aliases"].items()}


_ALIASES = load_aliases()


def canonical_brand_name(name: str) -> str:
    """Resolve an alias to brands.yaml's display name. Unknown names pass
    through unchanged (stripped) rather than raising - a brand with no
    alias entry is not an error, it just means the sources already agree.
    """
    if not name:
        return name
    return _ALIASES.get(normalize(name), str(name).strip())


def brand_match_key(name: str) -> str:
    """Normalized key for cross-source brand matching (BIBLE / PDF /
    website), aliases resolved first."""
    return normalize(canonical_brand_name(name))
