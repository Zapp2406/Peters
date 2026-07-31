# Gebrauchsanweisung: Upload-Post Plugin für Claude Code

## Was macht das Plugin?

Das Plugin `upload-post` bindet den Dienst [upload-post.com](https://upload-post.com) an
Claude Code an. Damit lassen sich Bilder, Videos und Texte direkt aus einer Unterhaltung
heraus auf mehrere Social-Media-Plattformen gleichzeitig veröffentlichen (z. B. Instagram,
TikTok, Facebook, LinkedIn, YouTube Shorts, X/Twitter, Threads, Pinterest), ohne jede
Plattform einzeln über ihre eigene App bedienen zu müssen.

## Status in diesem Projekt

- Marketplace `anthropics/claude-plugins-community` ist registriert (`.claude/settings.json`)
- Plugin `upload-post` ist aktiviert
- Beide Änderungen wurden im Branch `claude/install-upload-post-plugin-sg8bhj` committet
  (siehe Pull Request #2)

## Voraussetzungen vor der ersten Nutzung

1. Konto bei upload-post.com anlegen, falls noch nicht vorhanden.
2. Die gewünschten Social-Media-Profile dort verbinden (z. B. Instagram Business-Konto,
   TikTok-Konto, LinkedIn-Seite, YouTube-Kanal ...).
3. Einen API-Key auf upload-post.com generieren.
4. Den API-Key beim ersten Einsatz des Plugins in Claude Code hinterlegen, sobald danach
   gefragt wird. Der Key wird dabei nicht im Klartext ins Repository geschrieben.

## Verwendung

Sobald das Plugin aktiv ist, genügt eine normale Anweisung im Chat, zum Beispiel:

- "Poste dieses Bild auf Instagram und LinkedIn mit folgendem Text: ..."
- "Lade dieses Video als TikTok- und YouTube-Short hoch, Titel: ..."
- "Zeig mir, welche Social-Media-Konten aktuell verbunden sind."
- "Plane diesen Beitrag für morgen 9 Uhr."

Claude erkennt die Absicht und ruft die passenden Funktionen des Plugins auf.

## Wichtige Hinweise

- Das Plugin läuft innerhalb einer interaktiven Claude-Code-Sitzung (CLI, Desktop-App
  oder claude.ai/code). `/plugin`-Befehle lassen sich nicht aus einer automatisierten
  GitHub-PR-Session heraus ausführen — deshalb wurde die Aktivierung hier direkt über
  `.claude/settings.json` vorgenommen.
- Die genauen verfügbaren Befehle/Skills können je nach Plugin-Version variieren. Am besten
  in einer laufenden Sitzung mit `/help` oder der Frage "Welche Upload-Post-Funktionen sind
  verfügbar?" die aktuelle Liste abrufen.
- Veröffentlichte Inhalte sind sofort live auf den jeweiligen Plattformen — Inhalte vor dem
  Absenden immer noch einmal prüfen.

## Fehlerbehebung

- **Plugin erscheint nicht in Claude Code:** `/plugin marketplace update` ausführen oder
  Claude Code neu starten, damit die Konfiguration aus `.claude/settings.json` geladen wird.
- **Verbindungsfehler zu einer Plattform:** Verbindung auf upload-post.com erneut autorisieren.
- **API-Key abgelaufen oder ungültig:** neuen Key generieren und in der Plugin-Konfiguration
  hinterlegen.
