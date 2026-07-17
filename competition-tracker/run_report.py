#!/usr/bin/env python3
"""CLI entry point: python run_report.py [--brands mfk,diptyque]
                                          [--existing-file path/to/BIBLE.xlsx]
                                          [--reference-pdf path/to/Competition Distribution.pdf]
                                          [--no-email]

Scrapes brands.yaml, classifies FSS vs wholesale, computes deltas/trend vs
the last snapshot, diffs against the existing Competition tracker (BIBLE
xlsx door-level database, or the older regional-summary CSV), cross-checks
against the optional Competition Distribution PDF reference, downloads
new-store photos, drafts a regional-team email for whatever's still
blocked, writes the CSV/XLSX report, and emails it (unless --no-email).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

import yaml
from dotenv import load_dotenv

from aggregate import (
    compute_deltas, compute_store_deltas, compute_trend, load_blocklist,
    previous_snapshot, run_all, save_snapshot, write_a_verifier_csv,
)
from diff_existing import (
    build_bible_index, compare_with_existing, filter_bible_rows,
    find_new_stores, find_possible_closures, find_regional_total_differences,
    load_bible_competition, load_existing_export, write_rows_csv,
)
from draft_regional_email import generate_draft
from email_sender import send_report_email
from pdf_reference import (
    build_ambiguities_rows, extract_pdf_pages, parse_reference_data,
    save_reference_json, write_ambiguities_csv,
)
from photos import download_store_photos
from report import build_html_report, rows_for_export, write_csv, write_xlsx
from three_source_comparison import build_three_source_rows, write_three_source_csv

BASE_DIR = Path(__file__).parent
REFERENCE_JSON_PATH = BASE_DIR / "data" / "reference" / "competition_distribution_reference.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Veille concurrentielle FSS/FSF")
    parser.add_argument(
        "--brands", type=str, default=None,
        help="Slugs séparés par des virgules (ex: mfk,diptyque) pour ne rafraîchir qu'une partie de la liste.",
    )
    parser.add_argument(
        "--existing-file", type=str, default=None,
        help=(
            "Chemin vers le fichier de suivi existant à recouper : soit le BIBLE .xlsx "
            "(onglet 'Competition', comparaison porte par porte), soit l'ancien export .csv "
            "(BRAND|EMEA|UK|NOAM|LATAM|CHINA|APAC|TOTAL|SOURCE|DATE, compatibilité ascendante). "
            "Par défaut : la variable d'environnement COMPETITION_EXPORT_CSV si définie."
        ),
    )
    parser.add_argument(
        "--reference-pdf", type=str, default=None,
        help=(
            "Chemin vers 'Competition Distribution.pdf' (source complémentaire, manuellement "
            "recherchée - jamais traitée comme vérité automatique). Extrait un jeu de données de "
            "référence (data/reference/competition_distribution_reference.json), détecte les "
            "contradictions internes au PDF (pdf_reference_ambiguities.csv), et alimente "
            "three_source_comparison.csv (website vs BIBLE vs PDF)."
        ),
    )
    parser.add_argument(
        "--no-email", action="store_true",
        help="Ne pas envoyer l'email, même si les identifiants Gmail sont configurés dans .env.",
    )
    return parser.parse_args()


def _run_bible_comparison(results: list[dict], path: Path) -> tuple[list[dict], dict]:
    """Door-level comparison against the real BIBLE .xlsx. Writes the three
    dedicated output files and returns (regional_diff_rows, bible_index) -
    the index is reused for the three-source comparison if --reference-pdf
    is also given."""
    raw_rows = load_bible_competition(path)
    kept_rows, stats = filter_bible_rows(raw_rows)
    print(
        f"BIBLE '{path.name}' (onglet Competition) : {stats['total_loaded']} ligne(s) chargée(s), "
        f"{stats['excluded_online']} exclue(s) (online), "
        f"{stats['excluded_no_door_count']} exclue(s) (DOOR COUNT vide/0), "
        f"{stats['retained']} conservée(s) pour comparaison."
    )

    bible_index = build_bible_index(kept_rows)

    new_stores_rows = find_new_stores(results, bible_index)
    n_new = write_rows_csv(new_stores_rows, BASE_DIR / "new_stores_not_in_bible.csv")
    print(f"{n_new} nouvelle(s) boutique(s) absente(s) de la BIBLE -> new_stores_not_in_bible.csv")

    closure_rows, skipped = find_possible_closures(results, bible_index)
    n_closures = write_rows_csv(closure_rows, BASE_DIR / "possible_closures.csv")
    print(f"{n_closures} fermeture(s) possible(s) (TO VERIFY, jamais confirmée) -> possible_closures.csv")
    for skip in skipped:
        print(f"  (détection de fermeture ignorée pour {skip['brand']} : {skip['reason']})")

    regional_diff_rows = find_regional_total_differences(results, bible_index)
    write_rows_csv(regional_diff_rows, BASE_DIR / "regional_total_differences.csv")
    print(f"{len(regional_diff_rows)} écart(s) de total régional -> regional_total_differences.csv")

    return regional_diff_rows, bible_index


def _run_pdf_reference(brands: list[dict], path: Path) -> list[dict]:
    """Extract the optional PDF reference dataset - read-only, never the
    source of truth. Writes the JSON dataset and the ambiguities CSV."""
    try:
        pages = extract_pdf_pages(path)
    except ImportError as exc:
        print(f"pdfplumber n'est pas installé ({exc}) - PDF ignoré. Voir requirements.txt.")
        return []

    known_brand_names = [b["name"] for b in brands]
    pdf_records = parse_reference_data(pages, known_brand_names)
    ref_path = save_reference_json(pdf_records, REFERENCE_JSON_PATH)
    print(
        f"PDF '{path.name}' : {len(pages)} page(s) lue(s), {len(pdf_records)} valeur(s) extraite(s) "
        f"-> {ref_path.relative_to(BASE_DIR)}"
    )

    ambiguity_rows = build_ambiguities_rows(pdf_records)
    n_ambiguities = write_ambiguities_csv(ambiguity_rows, BASE_DIR / "pdf_reference_ambiguities.csv")
    print(f"{n_ambiguities} ambiguïté(s)/contradiction(s) dans le PDF -> pdf_reference_ambiguities.csv")

    return pdf_records


def _run_legacy_csv_comparison(results: list[dict], path: Path) -> list[dict]:
    existing = load_existing_export(path)
    discrepancies = compare_with_existing(results, existing)
    print(f"{len(discrepancies)} écart(s) avec l'export Competition existant (CSV, mode compatibilité).")
    return discrepancies


def main() -> int:
    load_dotenv()
    args = parse_args()
    only_slugs = args.brands.split(",") if args.brands else None
    today = date.today()

    brands = yaml.safe_load((BASE_DIR / "brands.yaml").read_text(encoding="utf-8"))
    print(f"Scraping {len(brands) if only_slugs is None else len(only_slugs)} marque(s)...")
    results = run_all(brands, only_slugs=only_slugs)

    for r in results:
        label = {"ok": "OK", "manual": "MANUEL", "error": "ECHEC"}[r["status"]]
        detail = f" - {r['error']}" if r["status"] == "error" else ""
        print(f"  [{label:6s}] {r['brand']}: {r.get('total')}{detail}")

    n_verify = write_a_verifier_csv(results)
    if n_verify:
        print(f"{n_verify} classification(s) douteuse(s) -> _a_verifier.csv")

    previous = previous_snapshot(before=today)
    deltas = compute_deltas(results, previous)
    store_deltas = compute_store_deltas(results, previous)
    save_snapshot(results, for_date=today)
    trend = compute_trend()

    total_new_stores = sum(len(v["new_stores"]) for v in store_deltas.values())
    if total_new_stores:
        print(f"{total_new_stores} nouvelle(s) boutique(s) détectée(s) depuis le dernier relevé.")
        for brand in results:
            new_stores = store_deltas[brand["slug"]]["new_stores"]
            if new_stores:
                written = download_store_photos(brand["slug"], new_stores)
                print(f"  {brand['brand']}: {len(written)} photo(s)/placeholder(s) -> photos/{brand['slug']}/")

    discrepancies = []
    bible_index = None
    existing_file = args.existing_file or os.environ.get("COMPETITION_EXPORT_CSV")
    if existing_file and Path(existing_file).exists():
        existing_path = Path(existing_file)
        suffix = existing_path.suffix.lower()
        if suffix == ".xlsx":
            discrepancies, bible_index = _run_bible_comparison(results, existing_path)
        elif suffix == ".csv":
            discrepancies = _run_legacy_csv_comparison(results, existing_path)
        else:
            print(f"--existing-file : extension '{suffix}' non reconnue (attendu .xlsx ou .csv) - recoupement ignoré.")
    elif existing_file:
        print(f"--existing-file défini ({existing_file}) mais introuvable - recoupement ignoré.")
    else:
        print("Pas de fichier existant fourni (--existing-file / COMPETITION_EXPORT_CSV) - recoupement ignoré.")

    pdf_records = []
    if args.reference_pdf and Path(args.reference_pdf).exists():
        pdf_records = _run_pdf_reference(brands, Path(args.reference_pdf))
    elif args.reference_pdf:
        print(f"--reference-pdf défini ({args.reference_pdf}) mais introuvable - PDF ignoré.")

    if bible_index is not None or pdf_records:
        three_source_rows = build_three_source_rows(results, bible_index, pdf_records)
        n_three_source = write_three_source_csv(three_source_rows, BASE_DIR / "three_source_comparison.csv")
        print(f"{n_three_source} ligne(s) de comparaison à 3 sources -> three_source_comparison.csv")

    recipients_raw = os.environ.get("REGIONAL_TEAM_RECIPIENTS", "")
    regional_recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    if regional_recipients:
        draft_path = generate_draft(results, regional_recipients, for_date=today)
        if draft_path:
            print(f"Brouillon d'email régional -> {draft_path}")

    rows = rows_for_export(results, for_date=today)
    csv_path = BASE_DIR / f"report_{today.isoformat()}.csv"
    xlsx_path = BASE_DIR / f"report_{today.isoformat()}.xlsx"
    write_csv(rows, csv_path)
    write_xlsx(rows, xlsx_path)
    print(f"Rapport écrit -> {csv_path.name}, {xlsx_path.name}")

    if args.no_email:
        print("--no-email : email non envoyé (rapport disponible en local ci-dessus).")
        return 0

    html_body = build_html_report(results, deltas, trend, discrepancies, for_date=today)

    gmail_address = os.environ.get("GMAIL_ADDRESS")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("REPORT_RECIPIENT")
    if not all([gmail_address, gmail_password, recipient]):
        print(
            "GMAIL_ADDRESS / GMAIL_APP_PASSWORD / REPORT_RECIPIENT manquant(s) dans .env "
            "- email non envoyé. Le rapport reste disponible en local (voir ci-dessus)."
        )
        return 0

    send_report_email(
        sender_address=gmail_address,
        app_password=gmail_password,
        recipient=recipient,
        subject=f"Veille concurrentielle FSS/FSF - {today.isoformat()}",
        html_body=html_body,
        attachment_path=xlsx_path,
    )
    print(f"Email envoyé à {recipient}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
