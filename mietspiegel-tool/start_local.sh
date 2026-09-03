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
  pip install --quiet -r requirements.txt
else
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

PORT="${MIETSPIEGEL_PORT:-5000}"
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
