"""Einlesen einer Mieterliste (xlsx/csv/pdf aus dem Hausverwaltungsprogramm)
und Massenberechnung gegen den Mietspiegel."""
from __future__ import annotations

import io
import re
from typing import Optional

import pandas as pd

from .berechnung import DEFAULT_KAPPUNGSGRENZE, Ergebnis, MietspiegelRechner
from .merkmale import GRUPPEN_IDS
from .pdf_import import lade_dataframe_aus_pdf

# Spaltenname (normalisiert, klein, ohne Sonderzeichen) -> interner Feldname
SPALTEN_ALIASE: dict[str, str] = {
    "strasse": "strasse",
    "straße": "strasse",
    "str": "strasse",
    "hausnummer": "hausnummer",
    "hausnr": "hausnummer",
    "nr": "hausnummer",
    "bezirk": "bezirk",
    "wohnung": "einheit",
    "einheit": "einheit",
    "we": "einheit",
    "lage": "einheit",
    "mieter": "mieter",
    "mietername": "mieter",
    "wohnflaeche": "groesse_qm",
    "wohnflaechem2": "groesse_qm",
    "flaeche": "groesse_qm",
    "qm": "groesse_qm",
    "groesse": "groesse_qm",
    "baujahr": "baujahr",
    "bezugsfertigkeit": "baujahr",
    "nettokaltmiete": "ist_nettokaltmiete_gesamt",
    "nettokaltmieteist": "ist_nettokaltmiete_gesamt",
    "kaltmiete": "ist_nettokaltmiete_gesamt",
    "miete": "ist_nettokaltmiete_gesamt",
    "mietealt": "ist_nettokaltmiete_gesamt",
}

for _gid in GRUPPEN_IDS:
    SPALTEN_ALIASE[f"{_gid}plus"] = f"{_gid}_plus"
    SPALTEN_ALIASE[f"{_gid}minus"] = f"{_gid}_minus"

PFLICHTFELDER = ["strasse", "hausnummer", "groesse_qm", "baujahr"]


def _zu_python_wert(wert):
    """Wandelt numpy-/pandas-Skalare (z.B. numpy.int64, pandas.Timestamp) in
    JSON-serialisierbare Python-Standardtypen um."""
    if isinstance(wert, pd.Timestamp):
        return wert.isoformat()
    if hasattr(wert, "item"):
        return wert.item()
    return wert


def _normiere_spaltenname(name: str) -> str:
    name = str(name).strip().lower()
    name = name.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    name = re.sub(r"[^a-z0-9]+", "", name)
    return name


def lade_dataframe(datei_bytes: bytes, dateiname: str) -> pd.DataFrame:
    name = dateiname.lower()
    if name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(datei_bytes), sep=None, engine="python")
    if name.endswith(".pdf"):
        return lade_dataframe_aus_pdf(datei_bytes)
    return pd.read_excel(io.BytesIO(datei_bytes))


def _mappe_spalten(df: pd.DataFrame) -> pd.DataFrame:
    umbenennung = {}
    for spalte in df.columns:
        key = _normiere_spaltenname(spalte)
        if key in SPALTEN_ALIASE:
            umbenennung[spalte] = SPALTEN_ALIASE[key]
    return df.rename(columns=umbenennung)


def _gruppen_counts_aus_zeile(row: pd.Series) -> dict[str, tuple[int, int]]:
    counts = {}
    for gid in GRUPPEN_IDS:
        plus = row.get(f"{gid}_plus")
        minus = row.get(f"{gid}_minus")
        plus = int(plus) if pd.notna(plus) else 0
        minus = int(minus) if pd.notna(minus) else 0
        counts[gid] = (plus, minus)
    return counts


def verarbeite_mieterliste(
    datei_bytes: bytes,
    dateiname: str,
    rechner: Optional[MietspiegelRechner] = None,
    kappungsgrenze: float = DEFAULT_KAPPUNGSGRENZE,
) -> list[Ergebnis]:
    df_original = lade_dataframe(datei_bytes, dateiname)
    df = _mappe_spalten(df_original.copy())
    df_original = df_original.reset_index(drop=True)
    df = df.reset_index(drop=True)

    fehlende = [f for f in PFLICHTFELDER if f not in df.columns]
    if fehlende:
        raise ValueError(
            "Pflichtspalten fehlen in der Mieterliste: "
            f"{', '.join(fehlende)}. Erwartet werden u.a. Straße, Hausnummer, "
            "Wohnfläche (qm), Baujahr, optional Nettokaltmiete."
        )

    rechner = rechner or MietspiegelRechner()
    ergebnisse: list[Ergebnis] = []
    for idx, row in df.iterrows():
        if pd.isna(row.get("strasse")):
            continue
        ist_miete = row.get("ist_nettokaltmiete_gesamt")
        ist_miete = float(ist_miete) if pd.notna(ist_miete) else None
        bezirk = row.get("bezirk")
        bezirk = str(bezirk).strip() if pd.notna(bezirk) else None

        ergebnis = rechner.berechne(
            strasse=str(row["strasse"]).strip(),
            hausnummer=int(row["hausnummer"]),
            groesse_qm=float(row["groesse_qm"]),
            baujahr=int(row["baujahr"]),
            ist_nettokaltmiete_gesamt=ist_miete,
            bezirk=bezirk,
            gruppen_counts=_gruppen_counts_aus_zeile(row),
            kappungsgrenze=kappungsgrenze,
        )
        ergebnis.eingabe["einheit"] = row.get("einheit") if "einheit" in df.columns else None
        ergebnis.eingabe["mieter"] = row.get("mieter") if "mieter" in df.columns else None
        # Komplette Original-Zeile unverändert mitführen (alle Spalten aus der
        # hochgeladenen Datei, auch nicht erkannte), damit nichts verloren geht.
        ergebnis.original_daten = {
            str(spalte): (None if pd.isna(wert) else _zu_python_wert(wert))
            for spalte, wert in df_original.loc[idx].items()
        }
        ergebnisse.append(ergebnis)
    return ergebnisse


BERECHNETE_SPALTEN = [
    "Wohnlage (Mietspiegel)",
    "Bezugsfertigkeit-Kategorie",
    "Unterwert €/m²",
    "Mittelwert €/m²",
    "Oberwert €/m²",
    "Spannenmerkmale-Nettoprozent",
    "Miete alt (Ist) €",
    "Miete neu (Mietspiegel, mit Spannenmerkmalen) €",
    "Mieterhöhung €",
    "Mieterhöhung %",
    "Status",
    "Fehler",
]


def ergebnisse_zu_dataframe(ergebnisse: list[Ergebnis]) -> pd.DataFrame:
    original_spalten: list[str] = []
    zeilen = []
    for e in ergebnisse:
        for spalte in e.original_daten:
            if spalte not in original_spalten:
                original_spalten.append(spalte)
        zeile = dict(e.original_daten)
        zeile.update(
            {
                "Wohnlage (Mietspiegel)": e.wohnlage,
                "Bezugsfertigkeit-Kategorie": e.bezugsfertigkeit_kategorie,
                "Unterwert €/m²": e.unterwert_qm,
                "Mittelwert €/m²": e.mittelwert_qm,
                "Oberwert €/m²": e.oberwert_qm,
                "Spannenmerkmale-Nettoprozent": e.netto_merkmal_prozent,
                "Miete alt (Ist) €": e.ist_nettokaltmiete_gesamt,
                "Miete neu (Mietspiegel, mit Spannenmerkmalen) €": e.vergleichsmiete_gesamt,
                "Mieterhöhung €": e.erhoehungspotential_gesamt,
                "Mieterhöhung %": e.erhoehungspotential_prozent,
                "Status": e.status,
                "Fehler": e.fehler,
            }
        )
        zeilen.append(zeile)
    df = pd.DataFrame(zeilen)
    # Original-Spalten (in Reihenfolge der Datei) zuerst, danach die
    # berechneten Spalten in fester, logischer Reihenfolge - insbesondere
    # "Miete alt" und "Miete neu" direkt nebeneinander.
    spaltenreihenfolge = original_spalten + BERECHNETE_SPALTEN
    return df.reindex(columns=[s for s in spaltenreihenfolge if s in df.columns])
