"""Lookup der Wohnlage (Berliner Mietspiegel) anhand von Straße + Hausnummer."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "strassen.json"

_UMLAUT_MAP = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def normalize(text: str) -> str:
    """Gleiche Normalisierung wie das 'strasseSuche'-Feld der Quelldaten."""
    text = text.strip().lower()
    text = text.translate(_UMLAUT_MAP)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Strassenabschnitt:
    strasse: str
    ortsteil: Optional[str]
    bezirk: str
    gebiet: str  # "O" oder "W" (Ost-/West-Berlin, fuer Baualtersklassen 1973-1990 relevant)
    hausnr_typ: str  # K=komplett, U=ungerade, G=gerade, F=fortlaufend/gemischt
    hausnr_von: Optional[int]
    hausnr_bis: Optional[int]
    wohnlage: str


class Strassenverzeichnis:
    def __init__(self, path: Path = DATA_FILE):
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        self._eintraege = [
            Strassenabschnitt(
                strasse=e["strasse"],
                ortsteil=e.get("ortsteil"),
                bezirk=e["bezirk"],
                gebiet=e["gebiet"],
                hausnr_typ=e["hausnrTyp"],
                hausnr_von=e.get("hausnrVon"),
                hausnr_bis=e.get("hausnrBis"),
                wohnlage=e["wohnlage"],
            )
            for e in raw
        ]
        self._nach_suche: dict[str, list[Strassenabschnitt]] = {}
        for e, r in zip(self._eintraege, raw):
            self._nach_suche.setdefault(r["strasseSuche"], []).append(e)

    def suche_strassen(self, teilstring: str, limit: int = 20) -> list[str]:
        """Autocomplete: eindeutige Straßennamen, die den Suchbegriff enthalten."""
        q = normalize(teilstring)
        if not q:
            return []
        treffer: list[str] = []
        gesehen: set[str] = set()
        for key, eintraege in self._nach_suche.items():
            if q in key:
                name = eintraege[0].strasse
                if name not in gesehen:
                    gesehen.add(name)
                    treffer.append(name)
                    if len(treffer) >= limit:
                        break
        return sorted(treffer)

    def bezirke_fuer_strasse(self, strasse: str) -> list[str]:
        key = normalize(strasse)
        eintraege = self._nach_suche.get(key, [])
        return sorted({e.bezirk for e in eintraege})

    def finde_wohnlage(
        self, strasse: str, hausnummer: int, bezirk: Optional[str] = None
    ) -> tuple[Optional[Strassenabschnitt], str]:
        """
        Liefert (Abschnitt, Status).
        Status: 'ok', 'nicht_gefunden', 'mehrdeutig_bezirk', 'keine_hausnummer_passt'
        """
        key = normalize(strasse)
        kandidaten = self._nach_suche.get(key)
        if not kandidaten:
            return None, "nicht_gefunden"

        bezirke = sorted({e.bezirk for e in kandidaten})
        if bezirk:
            kandidaten = [e for e in kandidaten if e.bezirk == bezirk]
            if not kandidaten:
                return None, "nicht_gefunden"
        elif len(bezirke) > 1:
            return None, "mehrdeutig_bezirk"

        gerade = hausnummer % 2 == 0
        for e in kandidaten:
            if e.hausnr_typ == "K":
                return e, "ok"
            if e.hausnr_typ == "U" and not gerade:
                if _in_range(hausnummer, e.hausnr_von, e.hausnr_bis):
                    return e, "ok"
            if e.hausnr_typ == "G" and gerade:
                if _in_range(hausnummer, e.hausnr_von, e.hausnr_bis):
                    return e, "ok"
            if e.hausnr_typ == "F":
                if _in_range(hausnummer, e.hausnr_von, e.hausnr_bis):
                    return e, "ok"
        return None, "keine_hausnummer_passt"


def _in_range(nr: int, von: Optional[int], bis: Optional[int]) -> bool:
    if von is not None and nr < von:
        return False
    if bis is not None and nr > bis:
        return False
    return True
