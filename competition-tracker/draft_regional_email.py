"""Etape 5bis: draft (never send) an email to the regional teams listing
exactly what stayed blocked after scraping - a technical failure, or a brand
with no reliable scraper at all. This is the tool's answer to Etape 3 of the
original brief ("si les informations ne sont pas disponibles sur Internet,
envoyer un mail aux regions") - it prepares the text, a human reviews and
sends it.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).parent
DRAFTS_DIR = BASE_DIR / "drafts"


def build_gaps(results: list[dict]) -> list[dict]:
    gaps = []
    for r in results:
        if r["status"] == "error":
            gaps.append({"brand": r["brand"], "reason": f"Echec technique du scraper : {r['error']}"})
        elif r["status"] == "manual":
            ref = f" (dernier chiffre connu : {r['known_total']})" if r.get("known_total") else ""
            gaps.append({"brand": r["brand"], "reason": f"Pas de scraper fiable identifie{ref}"})
    return gaps


def generate_draft(
    results: list[dict],
    recipients: list[str],
    for_date: date | None = None,
    output_dir: Path = DRAFTS_DIR,
) -> Path | None:
    """Write a plain-text draft email ready to copy into a mail client.
    Returns None (and writes nothing) if there are no gaps to report."""
    gaps = build_gaps(results)
    if not gaps:
        return None

    for_date = for_date or date.today()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"regional_email_{for_date.isoformat()}.txt"

    lines = [
        f"To: {', '.join(recipients)}",
        f"Subject: Suivi concurrence FSS/FSF - points a verifier ({for_date.isoformat()})",
        "",
        "Bonjour,",
        "",
        "Dans le cadre du suivi de la distribution des marques concurrentes, les points",
        "suivants n'ont pas pu etre confirmes automatiquement et necessitent une",
        "verification aupres des equipes regionales :",
        "",
    ]
    for gap in gaps:
        lines.append(f"- {gap['brand']} : {gap['reason']}")
    lines += [
        "",
        "Merci de confirmer le nombre de boutiques en propre (FSS/FSF) par region",
        "pour ces marques des que possible.",
        "",
        "Merci !",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
