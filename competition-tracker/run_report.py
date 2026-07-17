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
from coverage_audit import (
    AUDIT_COLUMNS, FAILURE_COLUMNS, build_coverage_audit, build_manual_follow_up, build_source_failures,
)
from diff_existing import (
    build_bible_index, compare_with_existing, filter_bible_rows,
    find_new_stores, find_possible_closures, find_regional_total_differences,
    load_bible_competition, load_existing_export, write_rows_csv,
)
from draft_regional_email import generate_draft
from email_sender import send_report_email
from brand_aliases import brand_match_key
from fss_filter_quality import (
    FILTER_QUALITY_COLUMNS, VALIDATION_SAMPLE_COLUMNS, bible_fss_fsf_total,
    build_filter_quality_row, build_validation_sample, compute_precision_from_verdicts,
    load_previous_verdicts,
)
from online_research import (
    CACHE_PATH_DEFAULT, FALLBACK_COLUMNS, brands_needing_fallback, build_fallback_rows,
    clear_brand_entries, fallback_summary_by_brand, load_cache, save_cache,
)
from pdf_reference import (
    build_ambiguities_rows, extract_pdf_pages, parse_reference_data,
    save_reference_json, write_ambiguities_csv,
)
from photos import download_store_photos
from recent_openings import RECENT_OPENING_COLUMNS, STILL_TO_VERIFY_COLUMNS, find_recent_openings
from report import build_html_report, rows_for_export, write_csv, write_xlsx
from three_source_comparison import build_three_source_rows, write_three_source_csv

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REFERENCE_JSON_PATH = DATA_DIR / "reference" / "competition_distribution_reference.json"


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
    parser.add_argument(
        "--skip-online-fallback", action="store_true",
        help="Ne pas générer data/online_fallback_sources.csv ni recouper avec le cache de recherche.",
    )
    parser.add_argument(
        "--refresh-online-research", action="store_true",
        help=(
            "Vide le cache de recherche en ligne (data/online_research_cache.json) pour les marques "
            "de ce run avant de générer le rapport - une vraie recherche live n'est pas possible depuis "
            "ce script (pas de clé d'API de recherche configurée) ; ce flag prépare juste le cache à "
            "être réalimenté lors d'une prochaine session de recherche."
        ),
    )
    return parser.parse_args()


def _load_bible(path: Path) -> dict:
    """Door-level index of the real BIBLE .xlsx (read-only, never
    modified) - built once, reused for new-store/closure/regional-diff
    detection, the FSS filter-quality assessment, and the three-source
    comparison."""
    raw_rows = load_bible_competition(path)
    kept_rows, stats = filter_bible_rows(raw_rows)
    print(
        f"BIBLE '{path.name}' (onglet Competition) : {stats['total_loaded']} ligne(s) chargée(s), "
        f"{stats['excluded_online']} exclue(s) (online), "
        f"{stats['excluded_no_door_count']} exclue(s) (DOOR COUNT vide/0), "
        f"{stats['retained']} conservée(s) pour comparaison."
    )
    return build_bible_index(kept_rows)


def _run_fss_classification_quality(brands: list[dict], results: list[dict], bible_index: dict) -> dict[str, str]:
    """data/fss_validation_sample.csv + data/fss_filter_quality.csv for every
    brand with a dedicated fss_classification_rules.yaml entry. Reads any
    prior run's filled-in MANUAL_VERDICT column (if the file already exists)
    to compute precision before overwriting it with this run's fresh sample.
    Returns {brand name -> FILTER_STATUS} so _run_bible_comparison() can
    gate closure detection on it (never RELIABLE until a human has verified
    a sample - see fss_filter_quality.determine_filter_status).
    """
    validation_path = DATA_DIR / "fss_validation_sample.csv"
    previous_verdicts = load_previous_verdicts(validation_path)

    all_sample_rows = []
    quality_rows = []
    filter_statuses: dict[str, str] = {}

    for result in results:
        if result.get("fss_classified_records") is None:
            continue
        brand_name = result["brand"]
        source_brand = next((b for b in brands if b["name"] == brand_name), None)
        source_url = source_brand.get("store_locator_url") if source_brand else None

        sample_rows = build_validation_sample(
            brand_name, result["fss_classified_records"], source_url, bible_index=bible_index,
        )
        all_sample_rows.extend(sample_rows)

        reviewed, false_positives, false_negatives = compute_precision_from_verdicts(previous_verdicts, brand_name)
        quality_row = build_filter_quality_row(
            brand_name, result["stats"], bible_index,
            precision_sample_size=reviewed, false_positives=false_positives, false_negatives=false_negatives,
            confidence_label=result.get("confidence"),
        )
        quality_rows.append(quality_row)
        filter_statuses[brand_match_key(brand_name)] = quality_row["FILTER_STATUS"]

    write_rows_csv(all_sample_rows, validation_path, fieldnames=VALIDATION_SAMPLE_COLUMNS)
    write_rows_csv(quality_rows, DATA_DIR / "fss_filter_quality.csv", fieldnames=FILTER_QUALITY_COLUMNS)
    if quality_rows:
        print(
            f"{len(quality_rows)} marque(s) évaluée(s) pour la qualité du filtre FSS/FSF -> "
            f"data/fss_filter_quality.csv, {len(all_sample_rows)} ligne(s) d'échantillon -> data/fss_validation_sample.csv"
        )
        for row in quality_rows:
            print(f"  [{row['FILTER_STATUS']:18s}] {row['BRAND']}: {row['INCLUDED_FSS_FSF']} FSS/FSF inclus, {row['NOTES']}")

    return filter_statuses


def _run_recent_openings(results: list[dict], bible_index: dict) -> None:
    """data/recent_openings.csv + data/recent_openings_still_to_verify.csv -
    see recent_openings.py's module docstring for the two discovery routes
    and the exact qualification rules. Purely a reporting layer over the
    online research cache + the already-built BIBLE index; no new scraping
    or classification logic here."""
    cache = load_cache(CACHE_PATH_DEFAULT)
    opened_rows, to_verify_rows = find_recent_openings(cache, bible_index, results)
    write_rows_csv(opened_rows, DATA_DIR / "recent_openings.csv", fieldnames=RECENT_OPENING_COLUMNS)
    write_rows_csv(to_verify_rows, DATA_DIR / "recent_openings_still_to_verify.csv", fieldnames=STILL_TO_VERIFY_COLUMNS)
    print(f"{len(opened_rows)} ouverture(s) récente(s) confirmée(s), absente(s) de la BIBLE -> data/recent_openings.csv")
    if to_verify_rows:
        print(f"{len(to_verify_rows)} boutique(s) référencée(s) sans date d'ouverture -> data/recent_openings_still_to_verify.csv")


def _run_bible_comparison(results: list[dict], bible_index: dict, fss_filter_statuses: dict[str, str] | None = None) -> list[dict]:
    """Door-level comparison against an already-built BIBLE index. Writes
    the three dedicated output files and returns regional_diff_rows.
    fss_filter_statuses (brand -> FILTER_STATUS, from fss_filter_quality.py)
    disables closure detection for any brand not yet marked RELIABLE."""
    new_stores_rows = find_new_stores(results, bible_index)
    n_new = write_rows_csv(new_stores_rows, BASE_DIR / "new_stores_not_in_bible.csv")
    print(f"{n_new} nouvelle(s) boutique(s) absente(s) de la BIBLE -> new_stores_not_in_bible.csv")

    closure_rows, skipped = find_possible_closures(results, bible_index, fss_filter_statuses)
    n_closures = write_rows_csv(closure_rows, BASE_DIR / "possible_closures.csv")
    print(f"{n_closures} fermeture(s) possible(s) (TO VERIFY, jamais confirmée) -> possible_closures.csv")
    for skip in skipped:
        print(f"  (détection de fermeture ignorée pour {skip['brand']} : {skip['reason']})")

    regional_diff_rows = find_regional_total_differences(results, bible_index)
    write_rows_csv(regional_diff_rows, BASE_DIR / "regional_total_differences.csv")
    print(f"{len(regional_diff_rows)} écart(s) de total régional -> regional_total_differences.csv")

    return regional_diff_rows


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


def _run_coverage_audit(brands: list[dict], results: list[dict], today) -> list[dict]:
    """data/brand_coverage_audit.csv + data/manual_follow_up.csv - purely a
    reporting layer over brands.yaml + the scrape results already
    computed, no new scraping logic."""
    audit_rows = build_coverage_audit(brands, results, checked_date=today)
    write_rows_csv(audit_rows, DATA_DIR / "brand_coverage_audit.csv", fieldnames=AUDIT_COLUMNS)
    print(f"{len(audit_rows)} marque(s) auditée(s) -> data/brand_coverage_audit.csv")

    follow_up_rows = build_manual_follow_up(audit_rows)
    write_rows_csv(follow_up_rows, DATA_DIR / "manual_follow_up.csv", fieldnames=AUDIT_COLUMNS)
    print(f"{len(follow_up_rows)} marque(s) nécessitant un suivi manuel -> data/manual_follow_up.csv")

    return audit_rows


def _run_online_fallback(audit_rows: list[dict], refresh: bool, today) -> dict[str, dict]:
    """data/online_fallback_sources.csv, read from the locally-cached
    research file (see online_research.py's module docstring for why this
    isn't a live search) - scoped to brands the coverage audit actually
    flags as needing follow-up. Returns the per-brand fallback summary used
    by brand_source_failures.csv."""
    brands_to_check = brands_needing_fallback(audit_rows)
    cache_path = CACHE_PATH_DEFAULT
    cache = load_cache(cache_path)

    if refresh and brands_to_check:
        cache = clear_brand_entries(cache, brands_to_check)
        save_cache(cache, cache_path)
        print(f"--refresh-online-research : cache vidé pour {len(brands_to_check)} marque(s) - à réalimenter.")

    fallback_rows = build_fallback_rows(cache, brands_to_check)
    write_rows_csv(fallback_rows, DATA_DIR / "online_fallback_sources.csv", fieldnames=FALLBACK_COLUMNS)
    print(
        f"{len(fallback_rows)} source(s) de recherche en ligne (cache) pour {len(brands_to_check)} "
        f"marque(s) nécessitant un suivi -> data/online_fallback_sources.csv"
    )

    return fallback_summary_by_brand(cache, brands_to_check)


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
            bible_index = _load_bible(existing_path)
            fss_filter_statuses = _run_fss_classification_quality(brands, results, bible_index)
            discrepancies = _run_bible_comparison(results, bible_index, fss_filter_statuses)
            _run_recent_openings(results, bible_index)
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

    audit_rows = _run_coverage_audit(brands, results, today)

    fallback_summary = {}
    if args.skip_online_fallback:
        print("--skip-online-fallback : recherche en ligne ignorée.")
    else:
        fallback_summary = _run_online_fallback(audit_rows, args.refresh_online_research, today)

    failure_rows = build_source_failures(brands, results, fallback_summary, checked_date=today)
    write_rows_csv(failure_rows, DATA_DIR / "brand_source_failures.csv", fieldnames=FAILURE_COLUMNS)
    if failure_rows:
        print(f"{len(failure_rows)} marque(s) en échec de scraping -> data/brand_source_failures.csv")

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
