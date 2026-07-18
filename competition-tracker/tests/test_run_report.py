import sys

from run_report import parse_args


def test_all_ten_brand_slugs_are_accepted(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_report.py",
            "--brands",
            "pdm,amouage,creed,matiere_premiere,mfk,byredo,nishane,ex_nihilo,bdk,initio",
            "--existing-file",
            ".\\BIBLE KP & FM Distribution List.xlsx",
        ],
    )
    args = parse_args()
    assert args.brands == "pdm,amouage,creed,matiere_premiere,mfk,byredo,nishane,ex_nihilo,bdk,initio"


def test_include_classifier_diagnostics_defaults_to_off(monkeypatch):
    monkeypatch.setattr(
        sys, "argv",
        ["run_report.py", "--brands", "pdm", "--existing-file", "BIBLE.xlsx"],
    )
    args = parse_args()
    assert args.include_classifier_diagnostics is False


def test_include_classifier_diagnostics_flag_is_recognized(monkeypatch):
    monkeypatch.setattr(
        sys, "argv",
        ["run_report.py", "--brands", "pdm", "--existing-file", "BIBLE.xlsx", "--include-classifier-diagnostics"],
    )
    args = parse_args()
    assert args.include_classifier_diagnostics is True
