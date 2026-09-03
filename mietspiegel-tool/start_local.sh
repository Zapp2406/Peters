#!/bin/bash
# Startet das Mietspiegel-Tool lokal (macOS/Linux) ohne Docker.
# Legt beim ersten Start automatisch eine virtuelle Python-Umgebung an.
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 wurde nicht gefunden. Bitte Python 3 installieren:"
  echo "  https://www.python.org/downloads/  (oder: brew install python3)"
  read -n 1 -s -r -p "Taste drücken zum Beenden..."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "Erstelle Python-Umgebung (einmalig, dauert kurz)..."
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install --quiet --upgrade pip
else
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi
# Bei jedem Start prüfen, ob neue/aktualisierte Abhängigkeiten nachinstalliert
# werden müssen (schnell, falls schon alles vorhanden ist).
pip install --quiet -r requirements.txt

if ! command -v tesseract >/dev/null 2>&1 || ! command -v pdftoppm >/dev/null 2>&1; then
  echo "Für OCR bei gescannten PDF-Mieterlisten fehlen 'tesseract' und/oder 'poppler'"
  echo "(Excel/CSV und Text-PDFs funktionieren auch ohne die beiden)."
  if command -v brew >/dev/null 2>&1; then
    read -r -p "Jetzt automatisch installieren (brew install tesseract tesseract-lang poppler)? [J/n] " antwort
    antwort="${antwort:-j}"
    if [[ "$antwort" =~ ^[jJyY] ]]; then
      echo "Installiere tesseract + poppler (kann einige Minuten dauern)..."
      brew install tesseract tesseract-lang poppler \
        || echo "Installation fehlgeschlagen - Excel/CSV und Text-PDFs funktionieren trotzdem."
    else
      echo "Übersprungen. Später nachholen mit: brew install tesseract tesseract-lang poppler"
    fi
  else
    echo "Homebrew wurde nicht gefunden. Homebrew installieren: https://brew.sh"
    echo "Danach: brew install tesseract tesseract-lang poppler"
  fi
fi

PORT="${MIETSPIEGEL_PORT:-5001}"
URL="http://127.0.0.1:${PORT}"

# Browser erst öffnen, sobald der Server tatsächlich antwortet (statt fest
# 2 Sekunden zu warten - bei einer frischen Installation kann allein das
# pip install oben schon länger dauern, dann käme der Browser zu früh und
# zeigt "Verbindung abgelehnt").
( for _ in $(seq 1 60); do
    if curl -s -o /dev/null "$URL"; then
      if command -v open >/dev/null 2>&1; then
        open "$URL"
      elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$URL"
      fi
      break
    fi
    sleep 0.5
  done
) &

echo "Mietspiegel-Tool startet unter $URL"
echo "Zum Beenden dieses Fenster schließen oder Strg+C drücken."
export FLASK_RUN_PORT="$PORT"
python app.py
