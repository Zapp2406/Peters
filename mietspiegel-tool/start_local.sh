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
  echo "Hinweis: 'tesseract' und/oder 'poppler' nicht gefunden - der OCR-Import"
  echo "für gescannte PDF-Mieterlisten steht dann nicht zur Verfügung (Excel/CSV"
  echo "und Text-PDFs funktionieren trotzdem). Zum Nachrüsten:"
  echo "  brew install tesseract tesseract-lang poppler"
fi

PORT="${MIETSPIEGEL_PORT:-5001}"
URL="http://127.0.0.1:${PORT}"

# Browser nach kurzer Wartezeit im Hintergrund öffnen, sobald der Server steht
( sleep 2
  if command -v open >/dev/null 2>&1; then
    open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$URL"
  fi
) &

echo "Mietspiegel-Tool startet unter $URL"
echo "Zum Beenden dieses Fenster schließen oder Strg+C drücken."
export FLASK_RUN_PORT="$PORT"
python app.py
