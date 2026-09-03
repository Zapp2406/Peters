# Berliner Mietspiegel-Tool

Web-Tool zum Abgleich von Nettokaltmieten mit dem Berliner Mietspiegel 2026:
Straßenverzeichnis mit allen Wohnlagen, Orientierungswerte-Tabelle, die
Merkmalgruppen-Checkliste ("Orientierungshilfe für die Spanneneinordnung",
Nr. 11 des Mietspiegels) und ein Upload für komplette Mieterlisten mit
automatischer Mieterhöhungs-Auswertung.

Ersetzt/digitalisiert das bisher im Hausverwaltungsprogramm verbaute
Mietspiegel-Modul als eigenständiges, nachvollziehbares Tool.

## Funktionsumfang

- **Straßenverzeichnis**: 13.528 Straßenabschnitte, alle Berliner Bezirke,
  mit Wohnlage (einfach/mittel/gut) und Gebiet (Ost/West, für die
  Baualtersklasse 1973–1990 relevant). Autocomplete inkl. Behandlung von
  Straßen mit unterschiedlichen Wohnlagen je Hausnummernbereich
  (gerade/ungerade/fortlaufend).
- **Orientierungswerte-Tabelle**: 189 Zeilen (Unter-/Mittel-/Oberwert nach
  Baualtersklasse, Wohnungsgröße und Wohnlage).
- **Merkmalgruppen-Checkliste**: alle wohnwerterhöhenden/-mindernden
  Merkmale aus Bad/WC, Küche, Wohnung, Gebäude und Wohnumfeld. Zählung des
  Überwiegens je Gruppe (±20 Prozentpunkte je Gruppe) nach der im Mietspiegel
  beschriebenen Methode.
- **Einzelabfrage**: Adresse + Baujahr + Größe + optionale Merkmale + Ist-Miete
  → berechnete Vergleichsmiete, Differenz, Mieterhöhungspotential unter
  Berücksichtigung der Kappungsgrenze.
- **Mieterlisten-Upload** (.xlsx/.csv): komplette Bestandsliste in einem
  Rutsch auswerten, Ergebnis als Tabelle und als Excel-Export.

## Wichtiger Hinweis

Dieses Tool ist eine **Rechenhilfe, keine Rechtsberatung**. Die
Orientierungshilfe für die Spanneneinordnung (Nr. 11) ist laut BGH
(Urteil vom 20.04.2005, VIII ZR 110/04) **nicht Teil des qualifizierten
Mietspiegels**. Für eine wirksame Mieterhöhung nach § 558 BGB sind zusätzlich
zu prüfen:

- Textform und ordnungsgemäße Begründung des Erhöhungsverlangens
- 12-Monats-Sperrfrist seit der letzten Mieterhöhung
- Zustimmungsfrist des Mieters (Ablauf des 2. Monats nach Zugang)
- die aktuell gültige Kappungsgrenzen-Verordnung Berlins (im Tool als
  konfigurierbarer Parameter hinterlegt, Standard 15 % – **vor Versand
  eines Erhöhungsverlangens den aktuellen Rechtsstand prüfen**)

## Installation

```bash
cd mietspiegel-tool
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Die App läuft danach unter <http://127.0.0.1:5000>.

## Tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

Die Kernberechnung ist gegen das offizielle Beispiel aus Nr. 10.4 B) des
Mietspiegels (mittlere Wohnlage, 1919–1949, 60 m², Zeile 81: Mittelwert
7,30 €/m² → mit +20 % Merkmal-Nettoergebnis 7,75 €/m²) sowie gegen die
Größen-Grenzfälle der Tabelle ("von X bis unter Y m²") abgesichert.

## Mieterliste hochladen: Spaltenformat

Die Spaltenüberschriften werden tolerant erkannt (Groß-/Kleinschreibung,
Umlaute egal). Erkannt werden u. a.:

| Pflicht/optional | Spalte (Beispiele) |
|---|---|
| Pflicht | Straße |
| Pflicht | Hausnummer |
| Pflicht | Wohnfläche / qm |
| Pflicht | Baujahr |
| optional | Bezirk (nur nötig, wenn eine Straße in mehreren Bezirken existiert) |
| optional | Nettokaltmiete (aktuell, monatlich, gesamt) |
| optional | Einheit, Mieter (nur zur Anzeige) |
| optional | `<gruppe>_plus` / `<gruppe>_minus` je Merkmalgruppe (`bad`, `kueche`, `wohnung`, `gebaeude`, `wohnumfeld`) — Anzahl der zutreffenden Merkmale, falls schon aus dem Hausverwaltungsprogramm bekannt |

Ohne Merkmal-Spalten wird automatisch der Mittelwert der Mietspiegeltabelle
angesetzt. Eine Beispieldatei liegt unter `sample_mieterliste.csv`.

## Projektstruktur

```
mietspiegel-tool/
├── app.py                  Flask-Anwendung (Routen/API)
├── data/
│   ├── strassen.json       Straßenverzeichnis + Wohnlagen (Mietspiegel 2026)
│   ├── tabelle.json        Orientierungswerte-Tabelle (Mietspiegel 2026)
│   └── merkmale.json       Merkmalgruppen (Nr. 11 Orientierungshilfe)
├── mietspiegel/
│   ├── strassen.py         Adress- → Wohnlage-Lookup
│   ├── tabelle.py          Baujahr/Größe/Wohnlage → Orientierungswert
│   ├── merkmale.py         Laden der Merkmalgruppen
│   ├── berechnung.py       Spanneneinordnung, Vergleich, Kappungsgrenze
│   └── mieterliste.py      Excel/CSV-Import und Massenberechnung
├── templates/index.html    UI (Einzelabfrage + Upload)
├── static/{style.css,app.js}
├── tests/                  pytest-Suite
└── sample_mieterliste.csv  Beispiel-Upload
```

## Datenquellen

Straßenverzeichnis, Orientierungswerte-Tabelle und Merkmalgruppen stammen
aus dem amtlichen Berliner Mietspiegel 2026 (bereitgestellte Auszüge).
Bei einer neuen Mietspiegel-Ausgabe müssen die drei Dateien in `data/`
aktualisiert werden.
