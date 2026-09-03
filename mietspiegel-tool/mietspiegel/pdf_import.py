"""PDF-Import für Mieterlisten.

Zwei Stufen:
1. Text-PDF (z.B. Export aus dem Hausverwaltungsprogramm): Tabellen werden
   direkt aus dem eingebetteten Text extrahiert (pdfplumber, keine
   Systemabhängigkeiten).
2. Gescanntes/Bild-PDF ohne Text: OCR-Fallback (pytesseract + pdf2image).
   Benötigt die Systemwerkzeuge `tesseract` und `poppler` (siehe README) -
   diese werden nur beim tatsächlichen Bedarf importiert, damit ein reiner
   Text-PDF-Import auch ohne diese Werkzeuge funktioniert.
"""
from __future__ import annotations

import io
from typing import Optional

import pandas as pd

TESSERACT_HINWEIS = (
    "OCR benötigt die Systemwerkzeuge 'tesseract' und 'poppler'. "
    "Installation auf macOS: brew install tesseract tesseract-lang poppler. "
    "Im Docker-Image (Synology) sind sie bereits enthalten."
)


def lade_dataframe_aus_pdf(datei_bytes: bytes) -> pd.DataFrame:
    df = _extrahiere_tabellen_pdfplumber(datei_bytes)
    if df is not None and not df.empty:
        return df

    df = _extrahiere_per_ocr(datei_bytes)
    if df is not None and not df.empty:
        return df

    raise ValueError(
        "Aus der PDF-Datei konnte keine Tabelle extrahiert werden - weder als "
        "eingebetteter Text noch per OCR. Bitte prüfen, ob die PDF eine "
        "erkennbare Tabellenstruktur hat, oder stattdessen als Excel/CSV "
        "exportieren."
    )


def _extrahiere_tabellen_pdfplumber(datei_bytes: bytes) -> Optional[pd.DataFrame]:
    import pdfplumber

    header: Optional[list[str]] = None
    zeilen: list[list] = []
    with pdfplumber.open(io.BytesIO(datei_bytes)) as pdf:
        for seite in pdf.pages:
            for tabelle in seite.extract_tables() or []:
                if not tabelle:
                    continue
                erste_zeile = [str(h or "").strip() for h in tabelle[0]]
                start = 0
                if header is None:
                    # Erste Tabelle im Dokument: erste Zeile ist die Kopfzeile.
                    header = erste_zeile
                    start = 1
                elif erste_zeile == header:
                    # Mehrseitige PDFs wiederholen die Kopfzeile oft auf jeder
                    # Seite (z.B. Hausverwaltungsprogramm-Exporte) - sonst
                    # würde sie als Datenzeile fehlinterpretiert.
                    start = 1
                zeilen.extend(tabelle[start:])
    if not header or not zeilen:
        return None
    breite = len(header)
    normiert = [(list(row) + [None] * breite)[:breite] for row in zeilen]
    return pd.DataFrame(normiert, columns=header)


def _extrahiere_per_ocr(datei_bytes: bytes) -> Optional[pd.DataFrame]:
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
        from pytesseract import Output
    except ImportError as exc:
        raise ValueError(
            f"OCR-Bibliotheken nicht installiert ({exc}). {TESSERACT_HINWEIS}"
        ) from exc

    try:
        bilder = convert_from_bytes(datei_bytes, dpi=300)
    except Exception as exc:
        raise ValueError(f"PDF konnte nicht gerastert werden. {TESSERACT_HINWEIS} ({exc})") from exc

    header: Optional[list[str]] = None
    alle_zeilen: list[list[str]] = []
    for bild in bilder:
        try:
            daten = pytesseract.image_to_data(bild, lang="deu+eng", output_type=Output.DATAFRAME)
        except Exception as exc:
            raise ValueError(f"OCR (tesseract) fehlgeschlagen. {TESSERACT_HINWEIS} ({exc})") from exc
        zeilen = _rekonstruiere_tabelle_aus_ocr(daten)
        if not zeilen:
            continue
        if header is None:
            header, rest = zeilen[0], zeilen[1:]
            alle_zeilen.extend(rest)
        else:
            start = 1 if zeilen[0] == header else 0
            alle_zeilen.extend(zeilen[start:])

    if not header or not alle_zeilen:
        return None
    breite = len(header)
    normiert = [(row + [""] * breite)[:breite] for row in alle_zeilen]
    return pd.DataFrame(normiert, columns=header)


def _rekonstruiere_tabelle_aus_ocr(daten: pd.DataFrame) -> list[list[str]]:
    """Best-effort Tabellenrekonstruktion aus pytesseract image_to_data:
    Wörter werden nach Zeile gruppiert (block/par/line), innerhalb einer
    Zeile nach x-Position sortiert und anhand größerer horizontaler Lücken
    in Spalten aufgeteilt. Funktioniert zuverlässig bei klaren, gleichmäßig
    gerasterten Tabellen - bei komplexen Layouts ggf. manuell nachbessern."""
    daten = daten[daten["text"].notna()]
    daten = daten[daten["text"].astype(str).str.strip() != ""]
    if daten.empty:
        return []

    zeilen: list[list[str]] = []
    for _, gruppe in daten.groupby(["block_num", "par_num", "line_num"], sort=True):
        gruppe = gruppe.sort_values("left")
        woerter = list(zip(gruppe["left"], gruppe["width"], gruppe["text"]))
        if not woerter:
            continue
        durchschnitt_breite = sum(w for _, w, _ in woerter) / len(woerter)
        luecken_schwelle = max(durchschnitt_breite * 2.5, 25)

        spalten: list[str] = []
        aktuelle_spalte: list[str] = []
        letztes_ende = None
        for left, width, text in woerter:
            if letztes_ende is not None and (left - letztes_ende) > luecken_schwelle:
                spalten.append(" ".join(aktuelle_spalte))
                aktuelle_spalte = []
            aktuelle_spalte.append(str(text))
            letztes_ende = left + width
        if aktuelle_spalte:
            spalten.append(" ".join(aktuelle_spalte))
        zeilen.append(spalten)
    return zeilen
