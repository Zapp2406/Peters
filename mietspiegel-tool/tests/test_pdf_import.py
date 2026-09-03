"""Tests für den PDF-Import (Tabellenextraktion aus Text-PDFs).
Benötigt reportlab zur Erzeugung der Test-PDF (siehe requirements-dev.txt)."""
import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

reportlab = pytest.importorskip("reportlab")

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from mietspiegel.mieterliste import verarbeite_mieterliste
from mietspiegel.pdf_import import lade_dataframe_aus_pdf


def _baue_test_pdf() -> bytes:
    puffer = io.BytesIO()
    doc = SimpleDocTemplate(puffer, pagesize=A4)
    daten = [
        ["Einheit", "Straße", "Hausnummer", "Wohnfläche", "Baujahr", "Nettokaltmiete"],
        ["WE 1", "Aachener Straße", "10", "60", "1935", "300"],
        ["WE 2", "Achillesstraße", "15", "45", "1980", "350"],
    ]
    tabelle = Table(daten)
    tabelle.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    doc.build([tabelle])
    return puffer.getvalue()


def test_pdf_tabelle_wird_extrahiert():
    pdf_bytes = _baue_test_pdf()
    df = lade_dataframe_aus_pdf(pdf_bytes)
    assert len(df) == 2
    assert "Straße" in df.columns
    assert df.iloc[0]["Straße"] == "Aachener Straße"


def test_pdf_upload_end_zu_ende():
    pdf_bytes = _baue_test_pdf()
    ergebnisse = verarbeite_mieterliste(pdf_bytes, "mieterliste.pdf")
    assert len(ergebnisse) == 2
    assert ergebnisse[0].fehler is None
    assert ergebnisse[0].wohnlage == "mittel"
    assert ergebnisse[0].original_daten["Einheit"] == "WE 1"
