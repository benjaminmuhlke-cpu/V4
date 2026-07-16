"""Etape 5: build the HTML email body + the CSV/XLSX attachment (same
column layout as the BIBLE tracker: BRAND | EMEA | UK | NOAM | LATAM | CHINA
| APAC | TOTAL | SOURCE | DATE), ready to copy-paste.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import openpyxl

from region_mapping import REGIONS

# REGIONS is already [EMEA, UK, NOAM, LATAM, CHINA, APAC], matching the
# tracker's own column order.
EXPORT_COLUMNS = ["BRAND", *REGIONS, "TOTAL", "SOURCE", "DATE"]

CONFIDENCE_LABELS = {"haute": "Haute", "moyenne": "Moyenne", "manuelle": "Manuelle"}
STATUS_LABELS = {"ok": "OK", "manual": "Manuel", "error": "Echec"}


def rows_for_export(results: list[dict], for_date: date | None = None) -> list[dict]:
    for_date = for_date or date.today()
    rows = []
    for r in results:
        row = {"BRAND": r["brand"], "SOURCE": r["source"] if r["status"] != "manual" else f"{r['source']} (manuel)",
               "DATE": for_date.isoformat()}
        if r["status"] == "ok":
            for region in REGIONS:
                row[region] = r["regions"].get(region, 0)
            row["TOTAL"] = r["total"]
        elif r["status"] == "manual":
            for region in REGIONS:
                row[region] = ""
            row["TOTAL"] = r.get("known_total", "")
        else:  # error
            for region in REGIONS:
                row[region] = ""
            row["TOTAL"] = "ECHEC"
        rows.append(row)
    return rows


def write_csv(rows: list[dict], path: Path) -> Path:
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_xlsx(rows: list[dict], path: Path) -> Path:
    path = Path(path)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Competition"
    ws.append(EXPORT_COLUMNS)
    for row in rows:
        ws.append([row[col] for col in EXPORT_COLUMNS])
    wb.save(path)
    return path


def _fmt_delta(value: int | None) -> str:
    if value is None:
        return ""
    if value > 0:
        return f" (+{value})"
    if value < 0:
        return f" ({value})"
    return " (=)"


def build_html_report(
    results: list[dict],
    deltas: dict,
    trend: list[tuple[str, int]],
    discrepancies: list[dict],
    for_date: date | None = None,
) -> str:
    for_date = for_date or date.today()
    header_cols = "".join(f"<th>{r}</th>" for r in REGIONS)

    body_rows = []
    for r in results:
        delta = deltas.get(r["slug"], {})
        total_delta_str = _fmt_delta(delta.get("total_delta"))
        confidence_label = CONFIDENCE_LABELS.get(r["confidence"], r["confidence"])
        status_label = STATUS_LABELS.get(r["status"], r["status"])

        if r["status"] == "ok":
            region_cells = "".join(f"<td>{r['regions'].get(region, 0)}</td>" for region in REGIONS)
            total_cell = f"{r['total']}{total_delta_str}"
        elif r["status"] == "manual":
            region_cells = "<td>-</td>" * len(REGIONS)
            total_cell = f"{r.get('known_total') or '?'} (ref.)"
        else:
            region_cells = "<td>-</td>" * len(REGIONS)
            total_cell = f"ECHEC : {r.get('error', '')}"

        body_rows.append(
            f"<tr><td>{r['brand']}</td>{region_cells}<td>{total_cell}</td>"
            f"<td>{confidence_label}</td><td>{status_label}</td></tr>"
        )

    trend_html = "<p><em>Pas assez d'historique pour une tendance (au moins 2 relevés requis).</em></p>"
    if trend:
        top = [f"{name} ({'+' if growth >= 0 else ''}{growth})" for name, growth in trend[:5] if growth != 0]
        if top:
            trend_html = "<p><strong>Tendance (depuis le premier relevé)</strong> : " + ", ".join(top) + "</p>"
        else:
            trend_html = "<p><em>Aucun changement de total depuis le premier relevé.</em></p>"

    discrepancy_html = "<p><em>Aucun écart avec l'export Competition existant.</em></p>"
    if discrepancies:
        items = "".join(
            f"<li>{d['brand']} - {d['field']} : {d['note']} "
            f"(existant : {d['existing_value']}, nouveau : {d['new_value']})</li>"
            for d in discrepancies
        )
        discrepancy_html = f"<p><strong>Écarts vs export Competition existant</strong></p><ul>{items}</ul>"

    return f"""
<html>
<body style="font-family: sans-serif; font-size: 14px;">
<h2>Veille concurrentielle FSS/FSF - {for_date.isoformat()}</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
<tr><th>Marque</th>{header_cols}<th>Total</th><th>Confiance</th><th>Statut</th></tr>
{''.join(body_rows)}
</table>
{trend_html}
{discrepancy_html}
<p style="color: #666; font-size: 12px;">
Voir la pièce jointe pour le CSV/XLSX prêt à copier dans la BIBLE, et
_a_verifier.csv pour le détail des classifications douteuses (mono-marque
vs wholesale, pays non résolu).
</p>
</body>
</html>
""".strip()
