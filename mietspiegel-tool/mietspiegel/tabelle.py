"""Lookup der Orientierungswerte (Unter-/Mittel-/Oberwert) der Mietspiegeltabelle."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "tabelle.json"


@dataclass
class TabellenZeile:
    zeile: int
    bezugsfertigkeit: str
    groesse_von: Optional[float]
    groesse_bis: Optional[float]
    unterwert: float
    mittelwert: float
    oberwert: float
    wohnlage: str


class Mietspiegeltabelle:
    def __init__(self, path: Path = DATA_FILE):
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        self._zeilen = [
            TabellenZeile(
                zeile=e["zeile"],
                bezugsfertigkeit=e["bezugsfertigkeit"],
                groesse_von=e.get("groesseVonQm"),
                groesse_bis=e.get("groesseBisQm"),
                unterwert=e["unterwert"],
                mittelwert=e["mittelwert"],
                oberwert=e["oberwert"],
                wohnlage=e["wohnlage"],
            )
            for e in raw
        ]

    def bezugsfertigkeit_kategorie(self, baujahr: int, gebiet: str) -> Optional[str]:
        """Ordnet ein Baujahr (+ Ost/West-Berlin) der Bezugsfertigkeits-Kategorie
        der Mietspiegeltabelle zu. gebiet: 'O' oder 'W'."""
        if baujahr <= 1918:
            return "Bis 1918"
        if baujahr <= 1949:
            return "1919 bis 1949"
        if baujahr <= 1964:
            return "1950 bis 1964"
        if baujahr <= 1972:
            return "1965 bis 1972"
        if baujahr <= 1990:
            if gebiet == "O":
                return "1973 bis 1990 Ost*"
            return "1973 bis 1985 West" if baujahr <= 1985 else "1986 bis 1990 West"
        if baujahr <= 2001:
            return "1991 bis 2001**"
        if baujahr <= 2009:
            return "2002 bis 2009"
        if baujahr <= 2015:
            return "2010 bis 2015"
        if baujahr <= 2019:
            return "2016 bis 2019"
        if baujahr <= 2024:
            return "2020 bis 2024"
        return None  # außerhalb des Mietspiegels (Neubau ohne Mietpreisbindung pruefen)

    def finde_zeile(
        self, wohnlage: str, bezugsfertigkeit: str, groesse_qm: float
    ) -> Optional[TabellenZeile]:
        kandidaten = [
            z
            for z in self._zeilen
            if z.wohnlage == wohnlage and z.bezugsfertigkeit == bezugsfertigkeit
        ]
        # Konvention der Mietspiegeltabelle: "von X bis unter Y m²"
        # (von inklusive, bis exklusiv) - siehe Beispiel Nr. 10.4: 60 m² faellt in
        # Zeile 81 (von 60, bis leer), nicht in Zeile 80 (von 45, bis 60).
        for z in kandidaten:
            von_ok = z.groesse_von is None or groesse_qm >= z.groesse_von
            bis_ok = z.groesse_bis is None or groesse_qm < z.groesse_bis
            if von_ok and bis_ok:
                return z
        return None
