#!/bin/bash
# Einmalig per Doppelklick ausführen: legt ein Start-Icon (Alias) für
# MietspiegelTool.app auf dem Schreibtisch an. Der Alias bleibt gültig,
# solange der Projektordner an diesem Ort liegen bleibt.
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_PATH="$DIR/MietspiegelTool.app"

if [ ! -d "$APP_PATH" ]; then
  echo "Fehler: MietspiegelTool.app wurde nicht gefunden unter:"
  echo "  $APP_PATH"
  read -n 1 -s -r -p "Taste drücken zum Beenden..."
  exit 1
fi

osascript <<EOF
tell application "Finder"
  if not (exists (alias file "MietspiegelTool" of desktop)) then
    make alias file to (POSIX file "$APP_PATH" as alias) at desktop
    set name of result to "MietspiegelTool"
  end if
end tell
EOF

echo "Fertig: Auf dem Schreibtisch liegt jetzt das Icon \"MietspiegelTool\"."
echo "Doppelklick darauf startet das Tool im Browser."
read -n 1 -s -r -p "Taste drücken zum Schließen..."
