"""Laden der Merkmalgruppen (wohnwerterhoehend/-mindernd) aus Nr. 11 der Orientierungshilfe."""
from __future__ import annotations

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "merkmale.json"

with open(DATA_FILE, encoding="utf-8") as _f:
    MERKMALE = json.load(_f)

GRUPPEN_IDS = [g["id"] for g in MERKMALE["gruppen"]]


def gruppe(gruppe_id: str) -> dict:
    for g in MERKMALE["gruppen"]:
        if g["id"] == gruppe_id:
            return g
    raise KeyError(gruppe_id)
