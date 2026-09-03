"""Berliner Mietspiegel-Tool: Web-Oberfläche für Einzelabfrage und Mieterlisten-Upload."""
from __future__ import annotations

import io
import os

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file

from mietspiegel.berechnung import DEFAULT_KAPPUNGSGRENZE, MietspiegelRechner
from mietspiegel.merkmale import MERKMALE
from mietspiegel.mieterliste import BaujahrFehltError, ergebnisse_zu_dataframe, verarbeite_mieterliste
from mietspiegel.strassen import Strassenverzeichnis
from mietspiegel.tabelle import Mietspiegeltabelle

app = Flask(__name__)
# Spaltenreihenfolge der Mieterlisten-Ergebnisse bewusst gesetzt (Original-
# Spalten zuerst, "Miete alt"/"Miete neu" nebeneinander) - Flasks Standard,
# JSON-Keys alphabetisch zu sortieren, würde das wieder zerstören.
app.json.sort_keys = False

_strassenverzeichnis = Strassenverzeichnis()
_tabelle = Mietspiegeltabelle()
_rechner = MietspiegelRechner(_strassenverzeichnis, _tabelle)


@app.get("/")
def index():
    return render_template(
        "index.html", merkmalgruppen=MERKMALE["gruppen"], kappungsgrenze=DEFAULT_KAPPUNGSGRENZE
    )


@app.get("/api/strassen")
def api_strassen_suche():
    q = request.args.get("q", "")
    return jsonify(_strassenverzeichnis.suche_strassen(q))


@app.get("/api/bezirke")
def api_bezirke():
    strasse = request.args.get("strasse", "")
    return jsonify(_strassenverzeichnis.bezirke_fuer_strasse(strasse))


@app.post("/api/berechnung")
def api_berechnung():
    payload = request.get_json(force=True)
    gruppen_counts = {
        gid: (int(v.get("plus", 0)), int(v.get("minus", 0)))
        for gid, v in (payload.get("merkmale") or {}).items()
    }
    ist_miete = payload.get("ist_nettokaltmiete_gesamt")
    ergebnis = _rechner.berechne(
        strasse=payload["strasse"],
        hausnummer=int(payload["hausnummer"]),
        groesse_qm=float(payload["groesse_qm"]),
        baujahr=int(payload["baujahr"]),
        ist_nettokaltmiete_gesamt=float(ist_miete) if ist_miete not in (None, "") else None,
        bezirk=payload.get("bezirk") or None,
        gruppen_counts=gruppen_counts,
        kappungsgrenze=float(payload.get("kappungsgrenze", DEFAULT_KAPPUNGSGRENZE)),
    )
    # Reine Anzeige-/Verwaltungsfelder ohne Einfluss auf die Berechnung -
    # analog zu den Zusatzfeldern beim Mieterlisten-Upload (mietspiegel/
    # mieterliste.py: ZUSATZFELDER).
    for feld in ("plz", "einheit", "mieter", "letzte_mietaenderung", "mietbeginn"):
        wert = payload.get(feld)
        ergebnis.eingabe[feld] = wert if wert not in (None, "") else None
    return jsonify(ergebnis.to_dict())


@app.post("/api/mieterliste/upload")
def api_mieterliste_upload():
    if "datei" not in request.files:
        return jsonify({"fehler": "Keine Datei hochgeladen (Feld 'datei')."}), 400
    datei = request.files["datei"]
    kappungsgrenze = float(request.form.get("kappungsgrenze", DEFAULT_KAPPUNGSGRENZE))
    baujahr_override = request.form.get("baujahr_override") or None
    baujahr_override = int(baujahr_override) if baujahr_override else None
    try:
        ergebnisse = verarbeite_mieterliste(
            datei.read(),
            datei.filename,
            rechner=_rechner,
            kappungsgrenze=kappungsgrenze,
            baujahr_override=baujahr_override,
        )
    except BaujahrFehltError as exc:
        # Eigenes Flag statt nur Freitext, damit das Frontend gezielt ein
        # Eingabefeld für das Baujahr anbieten kann, statt nur eine Fehler-
        # meldung anzuzeigen.
        return jsonify({"fehler": str(exc), "baujahr_fehlt": True}), 400
    except ValueError as exc:
        return jsonify({"fehler": str(exc)}), 400

    df = ergebnisse_zu_dataframe(ergebnisse)
    # Ergebnis-Datei serverseitig zwischenspeichern (einfacher In-Memory-Cache für den Export-Download)
    app.config["LETZTES_ERGEBNIS"] = df
    return jsonify(
        {
            "anzahl": len(ergebnisse),
            "zeilen": df.where(df.notna(), None).to_dict(orient="records"),
            # Schlanke Rohdaten je Zeile (gleiche Reihenfolge wie "zeilen"),
            # nur die Felder, die das Frontend für die Unter-/Mittel-/
            # Oberwert-Dropdown-Auswahl bei "Miete neu" ohne erneuten
            # Server-Aufruf braucht - bewusst kein voller e.to_dict() je
            # Zeile, das würde original_daten & Co. doppelt übertragen.
            "ergebnisse": [
                {
                    "unterwert_qm": e.unterwert_qm,
                    "mittelwert_qm": e.mittelwert_qm,
                    "oberwert_qm": e.oberwert_qm,
                    "groesse_qm": e.groesse_qm,
                    "ist_nettokaltmiete_gesamt": e.ist_nettokaltmiete_gesamt,
                    "kappungsgrenze": e.kappungsgrenze,
                }
                for e in ergebnisse
            ],
        }
    )


@app.get("/api/mieterliste/export")
def api_mieterliste_export():
    df = app.config.get("LETZTES_ERGEBNIS")
    if df is None:
        return jsonify({"fehler": "Keine Berechnung vorhanden. Bitte zuerst eine Mieterliste hochladen."}), 400
    puffer = io.BytesIO()
    with pd.ExcelWriter(puffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Mietspiegel-Vergleich")
    puffer.seek(0)
    return send_file(
        puffer,
        as_attachment=True,
        download_name="mietspiegel_vergleich.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    port = int(os.environ.get("MIETSPIEGEL_PORT", os.environ.get("FLASK_RUN_PORT", 5001)))
    # debug=False: der Werkzeug-Reloader startet den Prozess sonst doppelt neu,
    # was den Start verzögert (siehe start_local.sh, das auf den Server wartet,
    # bevor es den Browser öffnet) und ist für dieses lokale Endnutzer-Tool
    # ohnehin nicht nötig.
    app.run(debug=False, host="127.0.0.1", port=port)
