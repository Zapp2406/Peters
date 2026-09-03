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
- **Spannenmerkmale** (vormals "wohnwerterhöhende/-mindernde Merkmale"): alle
  Merkmale aus Bad/WC, Küche, Wohnung, Gebäude und Wohnumfeld vollständig und
  direkt sichtbar (kein Ein-/Ausklappen). Zählung des Überwiegens je Gruppe
  (±20 Prozentpunkte je Gruppe) nach der im Mietspiegel beschriebenen Methode.
- **Einzelabfrage**: Adresse + Baujahr + Größe + optionale Spannenmerkmale +
  Ist-Miete → Kennzahlen (Unter-/Mittel-/Oberwert), Lageplan (OpenStreetMap),
  und direkt nebeneinander **Miete alt / Miete neu nach Mietspiegel /
  Mieterhöhung**. "Miete neu" ist per Dropdown wählbar (Unterwert, Mittelwert
  [Standard], Oberwert, sowie der mit den Spannenmerkmalen berechnete Wert) -
  Miete neu und Mieterhöhung werden bei Auswahl sofort neu berechnet.
- **Lageplan**: eingebettete OpenStreetMap-Karte mit Marker an der berechneten
  Adresse. Das Geocoding läuft direkt im Browser über die öffentliche
  Nominatim-API von OpenStreetMap - die eingegebene Adresse wird dafür an
  `nominatim.openstreetmap.org` übertragen (kein eigener Server involviert).
  Erfordert eine Internetverbindung; ohne Verbindung erscheint ein Hinweis
  statt der Karte, der Rest des Tools funktioniert weiterhin.
- **Mieterlisten-Upload** (.xlsx, .csv **oder .pdf**): komplette Bestandsliste
  in einem Rutsch auswerten. Alle Original-Spalten aus der Datei (Mieter,
  Einheit, Lage, Größe, Kaltmiete, ...) werden vollständig und unverändert
  in die Ergebnistabelle übernommen und um die Mietspiegel-Werte ergänzt -
  inklusive Dropdown je Zeile für "Miete neu". Export als Excel-Datei.
- **PDF-Import mit OCR-Fallback**: Text-PDFs (z. B. Direktexport aus dem
  Hausverwaltungsprogramm) werden direkt als Tabelle erkannt. Für gescannte/
  eingescannte PDFs greift automatisch eine OCR-Texterkennung.

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

## Lokal starten (macOS, Doppelklick)

1. Projektordner (dieses `mietspiegel-tool`-Verzeichnis) irgendwohin auf dem
   Mac ablegen, z. B. `~/Programme/mietspiegel-tool`.
2. **Einmalig**: `MietspiegelTool.app` (im Projektordner) mit **Rechtsklick →
   Öffnen** starten und den Sicherheitshinweis bestätigen (das Bundle ist
   nicht signiert, macOS Gatekeeper fragt beim ersten Start einmal nach).
   Danach genügt ein normaler Doppelklick.
3. **Start-Icon auf dem Schreibtisch anlegen**: Doppelklick auf
   `install_desktop_icon.command` (einmalig, ebenfalls per Rechtsklick →
   Öffnen bestätigen). Legt automatisch ein Alias-Icon "MietspiegelTool" auf
   dem Schreibtisch an. Alternativ manuell: `MietspiegelTool.app` im Finder
   mit Rechtsklick → **Alias erstellen**, den Alias auf den Schreibtisch
   ziehen. Der Alias bleibt nur gültig, solange der Projektordner an diesem
   Ort liegen bleibt — bei einem Umzug des Ordners den Alias neu anlegen
   (Skript erneut ausführen).
4. Beim ersten Start wird automatisch eine Python-Umgebung angelegt und alle
   Abhängigkeiten installiert (dauert einmalig ca. 1 Minute, Python 3 muss
   installiert sein: <https://www.python.org/downloads/> oder
   `brew install python3`). Ein Terminal-Fenster öffnet sich mit dem
   Server-Log; der Browser öffnet automatisch <http://127.0.0.1:5001>,
   sobald der Server wirklich bereit ist (das Skript wartet aktiv darauf,
   statt eine feste Zeit zu schlafen - bei einer Erstinstallation kann das
   je nach Rechner 10-30 Sekunden dauern).
   (Port 5001 statt 5000, weil macOS' AirPlay-Receiver Port 5000 belegt und
   dort mit 403 Forbidden antwortet — falls das dennoch passiert: Systemeinstellungen
   → AirDrop & Handoff → "AirPlay-Empfänger" deaktivieren, oder einen anderen
   Port über `MIETSPIEGEL_PORT=5555 ./start_local.sh` erzwingen.)
5. **Beenden**: Terminal-Fenster schließen oder darin Strg+C drücken.

Alternativ ganz ohne App-Bundle direkt im Terminal:

```bash
cd mietspiegel-tool
./start_local.sh
```

## Installation auf einer Synology NAS (später)

Das Tool ist als Docker-Image vorbereitet und lässt sich über die Synology
**Container Manager**-App installieren, sobald der lokale Test abgeschlossen ist:

1. Projektordner per SSH/File Station auf die NAS kopieren (oder das
   GitHub-Repo dort klonen).
2. In der Synology **Container Manager**-App: **Projekt** → **Erstellen** →
   Pfad zum `mietspiegel-tool`-Ordner auswählen (enthält `docker-compose.yml`)
   → Container Manager baut das Image automatisch aus dem `Dockerfile`.
3. Alternativ per SSH auf der NAS:
   ```bash
   cd /volume1/docker/mietspiegel-tool
   docker compose up -d
   ```
4. Port `5001` ist im `docker-compose.yml` auf den NAS-Host gemappt — bei
   Bedarf (z. B. wenn 5001 schon belegt ist) in `docker-compose.yml` auf
   einen freien Port ändern, etwa `"8091:5001"`.
5. Danach ist das Tool unter `http://<NAS-IP>:5001` (bzw. dem gewählten Port)
   im lokalen Netzwerk erreichbar — für alle im Haushalt/Büro, nicht nur
   lokal auf einem Rechner.

Das Docker-Setup (`Dockerfile` + `docker-compose.yml`) läuft mit `gunicorn`
und genau einem Worker-Prozess (bewusst so gewählt, siehe Kommentar im
`Dockerfile` — das zuletzt hochgeladene Mieterlisten-Ergebnis für den
Excel-Export wird aktuell im Prozessspeicher gehalten).

### Manueller Docker-Test (ohne Synology)

```bash
cd mietspiegel-tool
docker compose up --build
```

Danach ist die App unter <http://127.0.0.1:5001> erreichbar,
`docker compose down` beendet sie wieder.

## Tests

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt   # zusätzlich: pytest, reportlab (nur für PDF-Testdaten)
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
| optional | Einheit / Lage, Mieter (nur zur Anzeige) |
| optional | `<gruppe>_plus` / `<gruppe>_minus` je Merkmalgruppe (`bad`, `kueche`, `wohnung`, `gebaeude`, `wohnumfeld`) — Anzahl der zutreffenden Spannenmerkmale, falls schon aus dem Hausverwaltungsprogramm bekannt |

Ohne Merkmal-Spalten wird automatisch der Mittelwert der Mietspiegeltabelle
angesetzt. **Alle weiteren Spalten der Datei** (auch nicht erkannte, z. B.
Mieternamen, Vertragsdaten, interne Notizen) werden unverändert in die
Ergebnistabelle übernommen. Eine Beispieldatei liegt unter
`sample_mieterliste.csv`.

### PDF-Listen und OCR

- **Text-PDFs** (z. B. direkter Export aus dem Hausverwaltungsprogramm)
  funktionieren ohne weitere Installation (nutzt `pdfplumber`, reines Python).
- **Gescannte/eingescannte PDFs** benötigen zusätzlich die Systemwerkzeuge
  `tesseract` (inkl. deutschem Sprachpaket) und `poppler`:
  - macOS: `brew install tesseract tesseract-lang poppler`
  - Docker/Synology: bereits im `Dockerfile` enthalten, keine weitere Aktion nötig
  - `start_local.sh` prüft bei jedem Start automatisch, ob beide Werkzeuge
    vorhanden sind. Fehlen sie und ist Homebrew installiert, bietet das
    Skript an, sie direkt zu installieren (Rückfrage im Terminal-Fenster,
    Enter/"j" genügt) - Text-PDFs, Excel und CSV funktionieren auch ohne
    diese beiden Werkzeuge uneingeschränkt weiter.
- OCR-Ergebnisse sind ein **Best-Effort**: Wörter werden anhand ihrer Position
  im Bild zu Zeilen/Spalten rekonstruiert. Bei einfachen, klar gerasterten
  Tabellen funktioniert das zuverlässig, bei komplexen Layouts bitte das
  Ergebnis vor Weiterverwendung stichprobenartig prüfen.

## Projektstruktur

```
mietspiegel-tool/
├── app.py                  Flask-Anwendung (Routen/API)
├── start_local.sh          Lokaler Start ohne Docker (venv + Browser)
├── MietspiegelTool.app/    macOS-App-Bundle (Doppelklick-Start, siehe oben)
├── install_desktop_icon.command  Legt einmalig ein Start-Icon auf dem Schreibtisch an
├── Dockerfile              Produktions-Image (gunicorn, inkl. tesseract/poppler)
├── docker-compose.yml      Für lokalen Docker-Test und Synology Container Manager
├── requirements.txt        Python-Abhängigkeiten (Betrieb)
├── requirements-dev.txt    Zusätzlich für Tests (pytest, reportlab)
├── data/
│   ├── strassen.json       Straßenverzeichnis + Wohnlagen (Mietspiegel 2026)
│   ├── tabelle.json        Orientierungswerte-Tabelle (Mietspiegel 2026)
│   └── merkmale.json       Merkmalgruppen (Nr. 11 Orientierungshilfe)
├── mietspiegel/
│   ├── strassen.py         Adress- → Wohnlage-Lookup
│   ├── tabelle.py          Baujahr/Größe/Wohnlage → Orientierungswert
│   ├── merkmale.py         Laden der Merkmalgruppen
│   ├── berechnung.py       Spanneneinordnung, Vergleich, Kappungsgrenze
│   ├── mieterliste.py      Excel/CSV/PDF-Import und Massenberechnung
│   └── pdf_import.py       PDF-Tabellenextraktion (pdfplumber) + OCR-Fallback
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
