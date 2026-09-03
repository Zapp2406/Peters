import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mietspiegel.berechnung import MietspiegelRechner


def test_end_zu_end_ohne_ist_miete():
    rechner = MietspiegelRechner()
    ergebnis = rechner.berechne(
        strasse="Aachener Straße",
        hausnummer=10,
        groesse_qm=60,
        baujahr=1935,
    )
    assert ergebnis.fehler is None
    assert ergebnis.wohnlage == "mittel"
    assert ergebnis.mittelwert_qm == 7.30
    assert ergebnis.vergleichsmiete_qm == 7.30  # keine Merkmale -> Mittelwert


def test_end_zu_end_mit_ist_miete_und_erhoehungspotential():
    rechner = MietspiegelRechner()
    ergebnis = rechner.berechne(
        strasse="Aachener Straße",
        hausnummer=10,
        groesse_qm=60,
        baujahr=1935,
        ist_nettokaltmiete_gesamt=300.0,  # 5,00 €/m², deutlich unter Vergleichsmiete
        kappungsgrenze=0.15,
    )
    assert ergebnis.fehler is None
    assert ergebnis.vergleichsmiete_gesamt == 7.30 * 60
    assert ergebnis.max_miete_kappungsgrenze_gesamt == 345.0  # 300 * 1.15
    # Vergleichsmiete (438) > Kappungsgrenze (345) -> Kappungsgrenze deckelt
    assert ergebnis.max_zulaessige_neue_miete_gesamt == 345.0
    assert ergebnis.erhoehungspotential_gesamt == 45.0
    assert "Erhöhung" in ergebnis.status


def test_mehrdeutiger_bezirk_erfordert_angabe():
    rechner = MietspiegelRechner()
    ergebnis = rechner.berechne(strasse="Ackerstraße", hausnummer=10, groesse_qm=50, baujahr=2000)
    assert ergebnis.fehler is not None
    assert "Bezirk" in ergebnis.fehler
