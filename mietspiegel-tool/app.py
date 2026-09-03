"""Berliner Mietspiegel-Tool: Web-Oberfläche für Einzelabfrage und Mieterlisten-Upload."""
from __future__ import annotations

import io

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file

from mietspiegel.berechnung import DEFAULT_KAPPUNGSGRENZE, MietspiegelRechner
from mietspiegel.merkmale import MERKMALE
from mietspiegel.mieterliste import ergebnisse_zu_dataframe, verarbeite_mieterliste
from mietspiegel.strassen import Strassenverzeichnis
from mietspiegel.tabelle import Mietspiegeltabelle

app = Flask(__name__)

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
    return jsonify(ergebnis.to_dict())


@app.post("/api/mieterliste/upload")
def api_mieterliste_upload():
    if "datei" not in request.files:
        return jsonify({"fehler": "Keine Datei hochgeladen (Feld 'datei')."}), 400
    datei = request.files["datei"]
    kappungsgrenze = float(request.form.get("kappungsgrenze", DEFAULT_KAPPUNGSGRENZE))
    try:
        ergebnisse = verarbeite_mieterliste(
            datei.read(), datei.filename, rechner=_rechner, kappungsgrenze=kappungsgrenze
        )
    except ValueError as exc:
        return jsonify({"fehler": str(exc)}), 400

    df = ergebnisse_zu_dataframe(ergebnisse)
    # Ergebnis-Datei serverseitig zwischenspeichern (einfacher In-Memory-Cache für den Export-Download)
    app.config["LETZTES_ERGEBNIS"] = df
    return jsonify(
        {
            "anzahl": len(ergebnisse),
            "zeilen": df.where(df.notna(), None).to_dict(orient="records"),
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
    app.run(debug=True, host="127.0.0.1", port=5000)
