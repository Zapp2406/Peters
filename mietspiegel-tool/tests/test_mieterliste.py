import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mietspiegel.mieterliste import BaujahrFehltError, ergebnisse_zu_dataframe, verarbeite_mieterliste

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

    # "Einheit" wird als erkanntes Feld ("Lage") geführt, nicht mehr als
    # rohe Original-Spalte - Zugriff über eingabe statt original_daten.
    assert ergebnisse[0].eingabe["einheit"] == "WE 1"

    df = ergebnisse_zu_dataframe(ergebnisse)
    assert len(df) == 2
    assert "Mieterhöhung €" in df.columns
    assert "Straße" in df.columns
    assert "Lage" in df.columns
    assert list(df["Lage"]) == ["WE 1", "WE 2"]


def test_fehlende_pflichtspalte_wirft_fehler():
    schlecht = "Straße;Hausnummer\nAachener Straße;10\n"
    try:
        verarbeite_mieterliste(schlecht.encode("utf-8"), "test.csv")
        assert False, "sollte ValueError werfen"
    except ValueError as exc:
        assert "Baujahr" in str(exc) or "groesse_qm" in str(exc)


def test_kollidierende_spaltenaliase_werfen_keinen_fehler():
    """Regressionstest: Eine Datei mit sowohl 'Miete' als auch 'Nettokaltmiete'
    darf nicht zu doppelten Spaltennamen (und damit zu einer Series statt
    Skalar bei row.get(...)) führen."""
    csv = (
        "Straße;Hausnummer;Wohnfläche;Baujahr;Nettokaltmiete;Miete\n"
        "Aachener Straße;10;60;1935;300;999\n"
    )
    ergebnisse = verarbeite_mieterliste(csv.encode("utf-8"), "test.csv")
    assert len(ergebnisse) == 1
    assert ergebnisse[0].fehler is None
    # Die zuerst gemappte Spalte ("Nettokaltmiete") gewinnt, "Miete" bleibt
    # als eigene, unangetastete Original-Spalte erhalten.
    assert ergebnisse[0].ist_nettokaltmiete_gesamt == 300.0
    assert ergebnisse[0].original_daten["Miete"] == 999


def test_neue_zusatzfelder_werden_erkannt():
    """PLZ, Lage, Letzte Mietänderung und Mietbeginn landen als eigene,
    verlässlich benannte Felder statt in original_daten."""
    csv = (
        "Lage;Straße;Hausnummer;PLZ;Wohn/Nutzfläche;Baujahr;Kaltmiete;"
        "Mietername;Letzte Mietänderung;Mietbeginn\n"
        "1. OG links;Aachener Straße;10;10553;60;1935;300;Max Mustermann;"
        "2023-01-01;2020-05-01\n"
    )
    ergebnisse = verarbeite_mieterliste(csv.encode("utf-8"), "test.csv")
    e = ergebnisse[0]
    assert e.fehler is None
    assert e.eingabe["plz"] == 10553
    assert e.eingabe["einheit"] == "1. OG links"
    assert e.eingabe["mieter"] == "Max Mustermann"
    assert e.eingabe["letzte_mietaenderung"] == "2023-01-01"
    assert e.eingabe["mietbeginn"] == "2020-05-01"
    assert e.original_daten == {}  # alles erkannt, nichts Übriges

    df = ergebnisse_zu_dataframe(ergebnisse)
    for spalte in ["Straße", "Hausnummer", "PLZ", "Baujahr", "Lage",
                   "Wohn-/Nutzfläche m²", "Kaltmiete €", "Mietername",
                   "Letzte Mietänderung", "Mietbeginn"]:
        assert spalte in df.columns, spalte


def test_fehlendes_baujahr_wirft_baujahrfehlterror_und_override_funktioniert():
    csv = "Lage;Straße;Hausnummer;Wohn/Nutzfläche;Kaltmiete\n1. OG links;Aachener Straße;10;60;300\n"
    try:
        verarbeite_mieterliste(csv.encode("utf-8"), "test.csv")
        assert False, "sollte BaujahrFehltError werfen"
    except BaujahrFehltError:
        pass

    ergebnisse = verarbeite_mieterliste(csv.encode("utf-8"), "test.csv", baujahr_override=1935)
    assert len(ergebnisse) == 1
    assert ergebnisse[0].fehler is None
    assert ergebnisse[0].eingabe["baujahr"] == 1935
    assert ergebnisse[0].wohnlage == "mittel"
