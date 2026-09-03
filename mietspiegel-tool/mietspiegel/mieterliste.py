"""Einlesen einer Mieterliste (xlsx/csv aus dem Hausverwaltungsprogramm) und
Massenberechnung gegen den Mietspiegel."""
from __future__ import annotations

import io
import re
from typing import Optional

import pandas as pd

from .berechnung import DEFAULT_KAPPUNGSGRENZE, Ergebnis, MietspiegelRechner
from .merkmale import GRUPPEN_IDS

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
}

for _gid in GRUPPEN_IDS:
    SPALTEN_ALIASE[f"{_gid}plus"] = f"{_gid}_plus"
    SPALTEN_ALIASE[f"{_gid}minus"] = f"{_gid}_minus"

PFLICHTFELDER = ["strasse", "hausnummer", "groesse_qm", "baujahr"]


def _normiere_spaltenname(name: str) -> str:
    name = str(name).strip().lower()
    name = name.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    name = re.sub(r"[^a-z0-9]+", "", name)
    return name


def lade_dataframe(datei_bytes: bytes, dateiname: str) -> pd.DataFrame:
    if dateiname.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(datei_bytes), sep=None, engine="python")
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
    df = lade_dataframe(datei_bytes, dateiname)
    df = _mappe_spalten(df)

    fehlende = [f for f in PFLICHTFELDER if f not in df.columns]
    if fehlende:
        raise ValueError(
            "Pflichtspalten fehlen in der Mieterliste: "
            f"{', '.join(fehlende)}. Erwartet werden u.a. Straße, Hausnummer, "
            "Wohnfläche (qm), Baujahr, optional Nettokaltmiete."
        )

    rechner = rechner or MietspiegelRechner()
    ergebnisse: list[Ergebnis] = []
    for _, row in df.iterrows():
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
        ergebnisse.append(ergebnis)
    return ergebnisse


def ergebnisse_zu_dataframe(ergebnisse: list[Ergebnis]) -> pd.DataFrame:
    zeilen = []
    for e in ergebnisse:
        zeilen.append(
            {
                "Einheit": e.eingabe.get("einheit"),
                "Mieter": e.eingabe.get("mieter"),
                "Straße": e.strasse or e.eingabe.get("strasse"),
                "Hausnr.": e.hausnummer or e.eingabe.get("hausnummer"),
                "Bezirk": e.bezirk,
                "Wohnlage": e.wohnlage,
                "Baujahr": e.eingabe.get("baujahr"),
                "qm": e.groesse_qm,
                "Unterwert €/m²": e.unterwert_qm,
                "Mittelwert €/m²": e.mittelwert_qm,
                "Oberwert €/m²": e.oberwert_qm,
                "Merkmal-Nettoprozent": e.netto_merkmal_prozent,
                "Vergleichsmiete €/m²": e.vergleichsmiete_qm,
                "Vergleichsmiete gesamt €": e.vergleichsmiete_gesamt,
                "Ist-Nettokaltmiete €": e.ist_nettokaltmiete_gesamt,
                "Differenz €": e.differenz_gesamt,
                "Differenz %": e.differenz_prozent,
                "Max. neue Miete (Kappungsgrenze) €": e.max_zulaessige_neue_miete_gesamt,
                "Erhöhungspotential €": e.erhoehungspotential_gesamt,
                "Erhöhungspotential %": e.erhoehungspotential_prozent,
                "Status": e.status,
                "Fehler": e.fehler,
            }
        )
    return pd.DataFrame(zeilen)
