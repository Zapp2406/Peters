import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mietspiegel.strassen import Strassenverzeichnis, normalize


def test_normalize_umlaute():
    assert normalize("Aachener Straße") == "aachener strasse"


def test_komplett_typ_unabhaengig_von_hausnummer():
    sv = Strassenverzeichnis()
    for hnr in (1, 50, 999):
        abschnitt, status = sv.finde_wohnlage("Aachener Straße", hnr)
        assert status == "ok"
        assert abschnitt.wohnlage == "mittel"
        assert abschnitt.gebiet == "W"


def test_ungerade_gerade_aufteilung():
    sv = Strassenverzeichnis()
    # Achillesstraße, Pankow: ungerade 1-107 -> mittel; gerade 14-110 -> mittel; gerade 112-120 -> einfach
    a, status = sv.finde_wohnlage("Achillesstraße", 15)
    assert status == "ok"
    assert a.wohnlage == "mittel"
    assert a.hausnr_typ == "U"

    b, status = sv.finde_wohnlage("Achillesstraße", 116)
    assert status == "ok"
    assert b.wohnlage == "einfach"
    assert b.hausnr_typ == "G"


def test_mehrdeutiger_bezirk_ohne_angabe():
    sv = Strassenverzeichnis()
    # Ackerstraße existiert in Span und Mitt
    _, status = sv.finde_wohnlage("Ackerstraße", 10)
    assert status == "mehrdeutig_bezirk"


def test_strasse_nicht_gefunden():
    sv = Strassenverzeichnis()
    _, status = sv.finde_wohnlage("Diese Straße Gibt Es Nicht Xyz", 1)
    assert status == "nicht_gefunden"


def test_autocomplete_findet_strasse():
    sv = Strassenverzeichnis()
    treffer = sv.suche_strassen("aachener")
    assert "Aachener Straße" in treffer
