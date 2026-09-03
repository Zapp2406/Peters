"""Test gegen das offizielle Beispiel aus Nr. 10.4 B) des Berliner Mietspiegels 2026:
Mittlere Wohnlage, 1919-1949 bezugsfertig, 60 m², Zeile 81.
Unterwert 5,90 / Mittelwert 7,30 / Oberwert 9,55 €/m².
3 Merkmalgruppen ueberwiegend +, 2 ueberwiegend - => Nettoergebnis +20%
=> Vergleichsmiete 7,30 + 20% * (9,55-7,30) = 7,75 €/m².
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mietspiegel.berechnung import spanneneinordnung
from mietspiegel.tabelle import Mietspiegeltabelle


def test_offizielles_beispiel_spanneneinordnung():
    gruppen_counts = {
        "bad": (1, 0),
        "kueche": (1, 0),
        "wohnung": (1, 0),
        "gebaeude": (0, 1),
        "wohnumfeld": (0, 1),
    }
    ergebnisse, netto, vergleichsmiete = spanneneinordnung(5.90, 7.30, 9.55, gruppen_counts)
    assert netto == 20
    assert vergleichsmiete == 7.75


def test_ohne_merkmale_ergibt_mittelwert():
    _, netto, vergleichsmiete = spanneneinordnung(5.90, 7.30, 9.55, {})
    assert netto == 0
    assert vergleichsmiete == 7.30


def test_alle_gruppen_negativ_ergibt_unterwert():
    counts = {g: (0, 1) for g in ["bad", "kueche", "wohnung", "gebaeude", "wohnumfeld"]}
    _, netto, vergleichsmiete = spanneneinordnung(5.90, 7.30, 9.55, counts)
    assert netto == -100
    assert vergleichsmiete == 5.90


def test_alle_gruppen_positiv_ergibt_oberwert():
    counts = {g: (1, 0) for g in ["bad", "kueche", "wohnung", "gebaeude", "wohnumfeld"]}
    _, netto, vergleichsmiete = spanneneinordnung(5.90, 7.30, 9.55, counts)
    assert netto == 100
    assert vergleichsmiete == 9.55


def test_tabelle_findet_offizielle_zeile_81():
    tabelle = Mietspiegeltabelle()
    kategorie = tabelle.bezugsfertigkeit_kategorie(1935, gebiet="W")
    assert kategorie == "1919 bis 1949"
    zeile = tabelle.finde_zeile("mittel", kategorie, 60)
    assert zeile is not None
    assert zeile.zeile == 81
    assert zeile.unterwert == 5.90
    assert zeile.mittelwert == 7.30
    assert zeile.oberwert == 9.55


def test_bezugsfertigkeit_ost_west_split():
    tabelle = Mietspiegeltabelle()
    assert tabelle.bezugsfertigkeit_kategorie(1980, gebiet="O") == "1973 bis 1990 Ost*"
    assert tabelle.bezugsfertigkeit_kategorie(1980, gebiet="W") == "1973 bis 1985 West"
    assert tabelle.bezugsfertigkeit_kategorie(1988, gebiet="W") == "1986 bis 1990 West"
    assert tabelle.bezugsfertigkeit_kategorie(2030, gebiet="W") is None
