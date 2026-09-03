"""Gesamtberechnung: Adresse -> Wohnlage -> Orientierungswert -> Spanneneinordnung
-> Vergleich mit Ist-Miete -> Mieterhoehungspotential (§ 558 BGB + Kappungsgrenze).

WICHTIG: Dies ist eine Rechenhilfe, keine Rechtsberatung. Die Orientierungshilfe
fuer die Spanneneinordnung (Nr. 11 Mietspiegel) ist nicht Teil des qualifizierten
Mietspiegels. Kappungsgrenze und Formvorschriften (Textform, Wartefrist, Zustimmungs-
frist) sind gesondert zu pruefen.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .merkmale import GRUPPEN_IDS
from .strassen import Strassenverzeichnis
from .tabelle import Mietspiegeltabelle

DEFAULT_KAPPUNGSGRENZE = 0.15  # Berlin: abgesenkte Kappungsgrenze (Kappungsgrenzen-VO)


@dataclass
class MerkmalErgebnis:
    gruppe_id: str
    gruppe_name: str
    anzahl_plus: int
    anzahl_minus: int
    ueberwiegt: str  # "plus" | "minus" | "neutral"
    anteil_prozent: int  # -20, 0 oder +20


@dataclass
class Ergebnis:
    eingabe: dict
    fehler: Optional[str] = None
    hinweise: list[str] = field(default_factory=list)
    # Rohdaten der Original-Zeile aus einer hochgeladenen Mieterliste (alle
    # Original-Spalten, unabhängig davon ob sie für die Berechnung erkannt
    # wurden) - für die vollständige Übernahme in die Ergebnisanzeige.
    original_daten: dict = field(default_factory=dict)

    strasse: Optional[str] = None
    hausnummer: Optional[int] = None
    bezirk: Optional[str] = None
    wohnlage: Optional[str] = None
    gebiet: Optional[str] = None

    bezugsfertigkeit_kategorie: Optional[str] = None
    groesse_qm: Optional[float] = None

    unterwert_qm: Optional[float] = None
    mittelwert_qm: Optional[float] = None
    oberwert_qm: Optional[float] = None

    merkmale: list[MerkmalErgebnis] = field(default_factory=list)
    netto_merkmal_prozent: Optional[int] = None
    vergleichsmiete_qm: Optional[float] = None
    vergleichsmiete_gesamt: Optional[float] = None

    ist_nettokaltmiete_gesamt: Optional[float] = None
    ist_nettokaltmiete_qm: Optional[float] = None

    differenz_qm: Optional[float] = None
    differenz_gesamt: Optional[float] = None
    differenz_prozent: Optional[float] = None

    kappungsgrenze: float = DEFAULT_KAPPUNGSGRENZE
    max_miete_kappungsgrenze_gesamt: Optional[float] = None
    max_zulaessige_neue_miete_gesamt: Optional[float] = None
    erhoehungspotential_gesamt: Optional[float] = None
    erhoehungspotential_prozent: Optional[float] = None

    status: Optional[str] = None

    def to_dict(self) -> dict:
        d = dict(self.__dict__)
        d["merkmale"] = [m.__dict__ for m in self.merkmale]
        return d


def spanneneinordnung(
    unterwert: float,
    mittelwert: float,
    oberwert: float,
    gruppen_counts: dict[str, tuple[int, int]],
) -> tuple[list[MerkmalErgebnis], int, float]:
    """Wendet Nr. 10.3/11 der Orientierungshilfe an: je Merkmalgruppe zaehlt das
    einfache Ueberwiegen von + oder - Merkmalen; jede Gruppe traegt +/-20
    Prozentpunkte zum Nettoergebnis bei. Das Nettoergebnis wird auf die obere
    (bei positivem Ergebnis) bzw. untere (bei negativem Ergebnis) Teilspanne
    angewendet."""
    from .merkmale import gruppe as get_gruppe

    ergebnisse: list[MerkmalErgebnis] = []
    netto = 0
    for gid in GRUPPEN_IDS:
        anzahl_plus, anzahl_minus = gruppen_counts.get(gid, (0, 0))
        if anzahl_plus > anzahl_minus:
            ueberwiegt, anteil = "plus", 20
        elif anzahl_minus > anzahl_plus:
            ueberwiegt, anteil = "minus", -20
        else:
            ueberwiegt, anteil = "neutral", 0
        netto += anteil
        ergebnisse.append(
            MerkmalErgebnis(
                gruppe_id=gid,
                gruppe_name=get_gruppe(gid)["name"],
                anzahl_plus=anzahl_plus,
                anzahl_minus=anzahl_minus,
                ueberwiegt=ueberwiegt,
                anteil_prozent=anteil,
            )
        )

    netto = max(-100, min(100, netto))
    if netto > 0:
        vergleichsmiete = mittelwert + (netto / 100) * (oberwert - mittelwert)
    elif netto < 0:
        vergleichsmiete = mittelwert + (netto / 100) * (mittelwert - unterwert)
    else:
        vergleichsmiete = mittelwert
    vergleichsmiete = max(unterwert, min(oberwert, vergleichsmiete))
    return ergebnisse, netto, round(vergleichsmiete, 2)


class MietspiegelRechner:
    def __init__(
        self,
        strassenverzeichnis: Optional[Strassenverzeichnis] = None,
        tabelle: Optional[Mietspiegeltabelle] = None,
    ):
        self.strassen = strassenverzeichnis or Strassenverzeichnis()
        self.tabelle = tabelle or Mietspiegeltabelle()

    def berechne(
        self,
        strasse: str,
        hausnummer: int,
        groesse_qm: float,
        baujahr: int,
        ist_nettokaltmiete_gesamt: Optional[float] = None,
        bezirk: Optional[str] = None,
        gruppen_counts: Optional[dict[str, tuple[int, int]]] = None,
        kappungsgrenze: float = DEFAULT_KAPPUNGSGRENZE,
    ) -> Ergebnis:
        eingabe = dict(
            strasse=strasse,
            hausnummer=hausnummer,
            groesse_qm=groesse_qm,
            baujahr=baujahr,
            ist_nettokaltmiete_gesamt=ist_nettokaltmiete_gesamt,
            bezirk=bezirk,
        )
        ergebnis = Ergebnis(eingabe=eingabe, kappungsgrenze=kappungsgrenze)

        abschnitt, status = self.strassen.finde_wohnlage(strasse, hausnummer, bezirk)
        if status == "mehrdeutig_bezirk":
            bezirke = self.strassen.bezirke_fuer_strasse(strasse)
            ergebnis.fehler = (
                f"Straße '{strasse}' existiert in mehreren Bezirken ({', '.join(bezirke)}). "
                "Bitte Bezirk angeben."
            )
            return ergebnis
        if status == "nicht_gefunden":
            ergebnis.fehler = f"Straße '{strasse}' nicht im Straßenverzeichnis gefunden."
            return ergebnis
        if status == "keine_hausnummer_passt":
            ergebnis.fehler = f"Hausnummer {hausnummer} in '{strasse}' keinem Abschnitt zugeordnet."
            return ergebnis

        ergebnis.strasse = abschnitt.strasse
        ergebnis.hausnummer = hausnummer
        ergebnis.bezirk = abschnitt.bezirk
        ergebnis.wohnlage = abschnitt.wohnlage
        ergebnis.gebiet = abschnitt.gebiet
        ergebnis.groesse_qm = groesse_qm

        kategorie = self.tabelle.bezugsfertigkeit_kategorie(baujahr, abschnitt.gebiet)
        if kategorie is None:
            ergebnis.fehler = (
                f"Baujahr {baujahr} liegt außerhalb der Mietspiegeltabelle "
                "(Neubau ohne Mietpreisbindung/Mietspiegel-Erfassung pruefen)."
            )
            return ergebnis
        ergebnis.bezugsfertigkeit_kategorie = kategorie

        zeile = self.tabelle.finde_zeile(abschnitt.wohnlage, kategorie, groesse_qm)
        if zeile is None:
            ergebnis.fehler = "Keine passende Tabellenzeile fuer diese Größe gefunden."
            return ergebnis

        ergebnis.unterwert_qm = zeile.unterwert
        ergebnis.mittelwert_qm = zeile.mittelwert
        ergebnis.oberwert_qm = zeile.oberwert

        gruppen_counts = gruppen_counts or {}
        merkmale, netto, vergleichsmiete_qm = spanneneinordnung(
            zeile.unterwert, zeile.mittelwert, zeile.oberwert, gruppen_counts
        )
        ergebnis.merkmale = merkmale
        ergebnis.netto_merkmal_prozent = netto
        ergebnis.vergleichsmiete_qm = vergleichsmiete_qm
        ergebnis.vergleichsmiete_gesamt = round(vergleichsmiete_qm * groesse_qm, 2)

        if ist_nettokaltmiete_gesamt is not None:
            ergebnis.ist_nettokaltmiete_gesamt = ist_nettokaltmiete_gesamt
            ergebnis.ist_nettokaltmiete_qm = round(ist_nettokaltmiete_gesamt / groesse_qm, 2)

            ergebnis.differenz_gesamt = round(
                ergebnis.vergleichsmiete_gesamt - ist_nettokaltmiete_gesamt, 2
            )
            ergebnis.differenz_qm = round(ergebnis.vergleichsmiete_qm - ergebnis.ist_nettokaltmiete_qm, 2)
            ergebnis.differenz_prozent = round(
                (ergebnis.differenz_gesamt / ist_nettokaltmiete_gesamt) * 100, 1
            )

            kappungsgrenze_miete = round(ist_nettokaltmiete_gesamt * (1 + kappungsgrenze), 2)
            ergebnis.max_miete_kappungsgrenze_gesamt = kappungsgrenze_miete
            max_neu = round(min(ergebnis.vergleichsmiete_gesamt, kappungsgrenze_miete), 2)
            ergebnis.max_zulaessige_neue_miete_gesamt = max_neu
            potential = round(max_neu - ist_nettokaltmiete_gesamt, 2)
            ergebnis.erhoehungspotential_gesamt = max(0.0, potential)
            ergebnis.erhoehungspotential_prozent = round(
                (ergebnis.erhoehungspotential_gesamt / ist_nettokaltmiete_gesamt) * 100, 1
            )

            if ist_nettokaltmiete_gesamt >= ergebnis.vergleichsmiete_gesamt:
                ergebnis.status = "über Vergleichsmiete (keine Erhöhung möglich)"
            elif ergebnis.erhoehungspotential_gesamt <= 0:
                ergebnis.status = "im Rahmen (Kappungsgrenze bereits ausgeschöpft)"
            else:
                ergebnis.status = "Erhöhung bis zur Vergleichsmiete/Kappungsgrenze möglich"

            if kappungsgrenze_miete < ergebnis.vergleichsmiete_gesamt:
                ergebnis.hinweise.append(
                    f"Kappungsgrenze ({kappungsgrenze*100:.0f}% in 3 Jahren) begrenzt die Erhöhung "
                    "stärker als die Vergleichsmiete."
                )

        ergebnis.hinweise.append(
            "Orientierungshilfe (Nr. 11) ist nicht Teil des qualifizierten Mietspiegels; "
            "Formvorschriften (Textform, 12-Monats-Sperrfrist, Zustimmungsfrist) gesondert prüfen."
        )
        return ergebnis
