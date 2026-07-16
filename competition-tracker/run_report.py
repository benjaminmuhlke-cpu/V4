#!/usr/bin/env python3
"""CLI entry point: python run_report.py [--brands mfk,diptyque]

Scrapes brands.yaml, classifies FSS vs wholesale, computes deltas/trend vs
the last snapshot, diffs against the existing Competition export (if
configured), downloads new-store photos, drafts a regional-team email for
whatever's still blocked, writes the CSV/XLSX report, and emails it.
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
from diff_existing import compare_with_existing, load_existing_export
from draft_regional_email import generate_draft
from email_sender import send_report_email
from photos import download_store_photos
from report import build_html_report, rows_for_export, write_csv, write_xlsx

BASE_DIR = Path(__file__).parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Veille concurrentielle FSS/FSF")
    parser.add_argument(
        "--brands", type=str, default=None,
        help="Slugs séparés par des virgules (ex: mfk,diptyque) pour ne rafraîchir qu'une partie de la liste.",
    )
    return parser.parse_args()


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
    export_csv = os.environ.get("COMPETITION_EXPORT_CSV")
    if export_csv and Path(export_csv).exists():
        existing = load_existing_export(export_csv)
        discrepancies = compare_with_existing(results, existing)
        print(f"{len(discrepancies)} écart(s) avec l'export Competition existant.")
    elif export_csv:
        print(f"COMPETITION_EXPORT_CSV défini ({export_csv}) mais introuvable - recoupement ignoré.")
    else:
        print("COMPETITION_EXPORT_CSV non défini dans .env - recoupement avec l'export existant ignoré.")

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
