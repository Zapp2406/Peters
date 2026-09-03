import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mietspiegel.mieterliste import ergebnisse_zu_dataframe, verarbeite_mieterliste

CSV = (
    "Einheit;Straße;Hausnummer;Wohnfläche;Baujahr;Nettokaltmiete\n"
    "WE 1;Aachener Straße;10;60;1935;300\n"
    "WE 2;Achillesstraße;15;45;1980;350\n"
)


def test_csv_upload_end_zu_ende():
    ergebnisse = verarbeite_mieterliste(CSV.encode("utf-8"), "test.csv")
    assert len(ergebnisse) == 2
    assert ergebnisse[0].fehler is None
    assert ergebnisse[0].wohnlage == "mittel"
    assert ergebnisse[0].vergleichsmiete_gesamt == 7.30 * 60

    df = ergebnisse_zu_dataframe(ergebnisse)
    assert len(df) == 2
    assert "Erhöhungspotential €" in df.columns


def test_fehlende_pflichtspalte_wirft_fehler():
    schlecht = "Straße;Hausnummer\nAachener Straße;10\n"
    try:
        verarbeite_mieterliste(schlecht.encode("utf-8"), "test.csv")
        assert False, "sollte ValueError werfen"
    except ValueError as exc:
        assert "Baujahr" in str(exc) or "groesse_qm" in str(exc)
