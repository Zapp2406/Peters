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
    "wohnnutzflaeche": "groesse_qm",
    "nutzflaeche": "groesse_qm",
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
    "plz": "plz",
    "postleitzahl": "plz",
    "letztemietaenderung": "letzte_mietaenderung",
    "letztemieterhoehung": "letzte_mietaenderung",
    "mietaenderungzum": "letzte_mietaenderung",
    "mietbeginn": "mietbeginn",
    "vertragsbeginn": "mietbeginn",
    "einzugsdatum": "mietbeginn",
}

# Felder, die als eigene, verlässlich benannte Spalte übernommen werden
# (zusätzlich zu den direkt für die Berechnung genutzten wie strasse/
# hausnummer/groesse_qm/baujahr/ist_nettokaltmiete_gesamt), aber selbst
# nicht in die Mietspiegel-Berechnung eingehen - nur zur Anzeige.
ZUSATZFELDER = ["plz", "einheit", "mieter", "letzte_mietaenderung", "mietbeginn"]

for _gid in GRUPPEN_IDS:
    SPALTEN_ALIASE[f"{_gid}plus"] = f"{_gid}_plus"
    SPALTEN_ALIASE[f"{_gid}minus"] = f"{_gid}_minus"

PFLICHTFELDER = ["strasse", "hausnummer", "groesse_qm"]


class BaujahrFehltError(ValueError):
    """Die Datei enthält keine Baujahr-Spalte. Kann durch eine einmalige,
    manuelle Angabe für das gesamte Gebäude behoben werden (baujahr_override)."""


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


def _mappe_spalten(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Benennt erkannte Spalten auf ihren internen Feldnamen um. Zeigen zwei
    Original-Spalten auf denselben internen Namen (z.B. sowohl 'Miete' als
    auch 'Nettokaltmiete' in derselben Datei), wird nur die erste umbenannt -
    alles andere würde zu doppelten Spaltenbezeichnungen und damit zu
    mehrdeutigen row.get(...)-Zugriffen (Series statt Skalar) führen.
    Gibt zusätzlich die vorgenommene Umbenennung zurück (Original-Spaltenname
    -> interner Feldname), damit der Aufrufer weiß, welche Original-Spalten
    bereits über ein erkanntes Feld abgedeckt sind."""
    umbenennung: dict[str, str] = {}
    bereits_vergeben: set[str] = set()
    for spalte in df.columns:
        key = _normiere_spaltenname(spalte)
        ziel = SPALTEN_ALIASE.get(key)
        if ziel and ziel not in bereits_vergeben:
            umbenennung[spalte] = ziel
            bereits_vergeben.add(ziel)
    return df.rename(columns=umbenennung), umbenennung


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
    baujahr_override: Optional[int] = None,
) -> list[Ergebnis]:
    """baujahr_override: wird verwendet, wenn die Datei keine Baujahr-Spalte
    enthält (oder einzelne Zeilen dort leer sind) - z.B. eine manuelle,
    einmalige Angabe für das ganze Gebäude, falls das Baujahr nicht in der
    Mieterliste steht. Fehlt die Baujahr-Spalte komplett und wird kein
    baujahr_override übergeben, wird BaujahrFehltError ausgelöst, damit die
    aufrufende Stelle gezielt danach fragen kann."""
    df_original = lade_dataframe(datei_bytes, dateiname)
    df, umbenennung = _mappe_spalten(df_original.copy())
    df_original = df_original.reset_index(drop=True)
    df = df.reset_index(drop=True)
    # Original-Spaltennamen, deren Inhalt bereits über ein erkanntes Feld
    # (Straße, Lage, Kaltmiete, ...) abgedeckt ist - diese sollen nicht noch
    # einmal redundant unter ihrem rohen Original-Namen angezeigt werden.
    bereits_abgedeckt = set(umbenennung.keys())

    if "baujahr" not in df.columns:
        if baujahr_override is None:
            raise BaujahrFehltError(
                "Die Mieterliste enthält keine Baujahr-Spalte. Bitte das "
                "Baujahr für das Gebäude einmalig angeben."
            )
        df["baujahr"] = baujahr_override

    fehlende = [f for f in PFLICHTFELDER if f not in df.columns]
    if fehlende:
        raise ValueError(
            "Pflichtspalten fehlen in der Mieterliste: "
            f"{', '.join(fehlende)}. Erwartet werden u.a. Straße, Hausnummer, "
            "Wohnfläche (qm), optional Nettokaltmiete."
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

        baujahr_wert = row.get("baujahr")
        if pd.isna(baujahr_wert):
            if baujahr_override is None:
                raise BaujahrFehltError(
                    f"Zeile {idx + 1}: kein Baujahr angegeben. Bitte das Baujahr "
                    "für das Gebäude einmalig angeben."
                )
            baujahr_wert = baujahr_override

        ergebnis = rechner.berechne(
            strasse=str(row["strasse"]).strip(),
            hausnummer=int(row["hausnummer"]),
            groesse_qm=float(row["groesse_qm"]),
            baujahr=int(baujahr_wert),
            ist_nettokaltmiete_gesamt=ist_miete,
            bezirk=bezirk,
            gruppen_counts=_gruppen_counts_aus_zeile(row),
            kappungsgrenze=kappungsgrenze,
        )
        for feld in ZUSATZFELDER:
            wert = row.get(feld) if feld in df.columns else None
            ergebnis.eingabe[feld] = _zu_python_wert(wert) if pd.notna(wert) else None
        # Komplette Original-Zeile mitführen, aber ohne die Spalten, die
        # bereits über ein erkanntes Feld (Straße, Lage, Kaltmiete, ...)
        # abgedeckt sind - sonst erscheinen dieselben Daten doppelt.
        ergebnis.original_daten = {
            str(spalte): (None if pd.isna(wert) else _zu_python_wert(wert))
            for spalte, wert in df_original.loc[idx].items()
            if spalte not in bereits_abgedeckt
        }
        ergebnisse.append(ergebnis)
    return ergebnisse


# Gebäude-Ebene: für alle Einheiten eines Gebäudes identisch, wird im
# Frontend als gemeinsamer "Kopf" gruppiert dargestellt.
GEBAEUDE_SPALTEN = [
    "Straße",
    "Hausnummer",
    "PLZ",
    "Bezirk",
    "Baujahr",
    "Wohnlage (Mietspiegel)",
    "Bezugsfertigkeit-Kategorie",
]

# Feste Felder je Einheit (Wohnung), wie im Frontend als eigene Tabellenspalten
# direkt nach dem Gebäude-Kopf angezeigt.
EINHEIT_SPALTEN = [
    "Lage",
    "Wohn-/Nutzfläche m²",
    "Kaltmiete €",
    "Mietername",
    "Letzte Mietänderung",
    "Mietbeginn",
]

MIETSPIEGEL_SPALTEN = [
    "Unterwert €/m²",
    "Mittelwert €/m²",
    "Oberwert €/m²",
    "Spannenmerkmale-Nettoprozent",
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
                "Straße": e.strasse,
                "Hausnummer": e.hausnummer,
                "PLZ": e.eingabe.get("plz"),
                "Bezirk": e.bezirk,
                "Baujahr": e.eingabe.get("baujahr"),
                "Wohnlage (Mietspiegel)": e.wohnlage,
                "Bezugsfertigkeit-Kategorie": e.bezugsfertigkeit_kategorie,
                "Lage": e.eingabe.get("einheit"),
                "Wohn-/Nutzfläche m²": e.groesse_qm,
                "Kaltmiete €": e.ist_nettokaltmiete_gesamt,
                "Mietername": e.eingabe.get("mieter"),
                "Letzte Mietänderung": e.eingabe.get("letzte_mietaenderung"),
                "Mietbeginn": e.eingabe.get("mietbeginn"),
                "Unterwert €/m²": e.unterwert_qm,
                "Mittelwert €/m²": e.mittelwert_qm,
                "Oberwert €/m²": e.oberwert_qm,
                "Spannenmerkmale-Nettoprozent": e.netto_merkmal_prozent,
                "Miete neu (Mietspiegel, mit Spannenmerkmalen) €": e.vergleichsmiete_gesamt,
                "Mieterhöhung €": e.erhoehungspotential_gesamt,
                "Mieterhöhung %": e.erhoehungspotential_prozent,
                "Status": e.status,
                "Fehler": e.fehler,
            }
        )
        zeilen.append(zeile)
    df = pd.DataFrame(zeilen)
    # Gebäude-Felder, feste Einheiten-Felder, übrige Original-Spalten aus der
    # Datei, dann die Mietspiegel-Vergleichsspalten - in dieser Reihenfolge.
    spaltenreihenfolge = GEBAEUDE_SPALTEN + EINHEIT_SPALTEN + original_spalten + MIETSPIEGEL_SPALTEN
    return df.reindex(columns=[s for s in spaltenreihenfolge if s in df.columns])
