"""Proband:innen-Verwaltung (P10, docs/backlog.md "Proband:innen-Erfassung am
Sitzungsanfang") -- zweistufige ID-Struktur: eine neue, pseudonyme `subject_id` gilt ueber
BELIEBIG VIELE Sitzungen derselben Person hinweg (1:n), zusaetzlich zur bestehenden
technischen `session_id` (P4, core/session_store.py), die weiterhin EINE Sitzung kennzeichnet.

Bewusst KEIN Name, KEINE Initialen -- nur ID + Alter. Eine Re-Identifizierung (welche ID
gehoert zu welcher echten Person) obliegt der behandelnden Person ausserhalb der App.
"""

import json
import os
import random
from datetime import datetime, timezone

import streamlit as st

from core.session_store import save_session_snapshot

DERIVED_DIR = os.environ.get("NEUROVOICE_DERIVED_DIR", "/derived")
SUBJECTS_DIR = os.path.join(DERIVED_DIR, "_subjects")

# Kein 0/O/1/I/l -- Verwechslungsgefahr beim Abschreiben/Diktieren der ID vermeiden.
ID_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
ID_LENGTH = 4


def _subject_file(subject_id: str) -> str:
    os.makedirs(SUBJECTS_DIR, exist_ok=True)
    # Defensiv sanitisieren, gleiches Pfad-Traversal-Prinzip wie bei save_uploaded_wav()/
    # core/session_store.py -- auch wenn subject_id normalerweise aus generate_subject_id() kommt.
    safe_id = "".join(c for c in subject_id if c.isalnum() or c == "-")[:64] or "unknown"
    return os.path.join(SUBJECTS_DIR, f"{safe_id}.json")


def list_subjects() -> list[dict]:
    """Liest alle bekannten Proband:innen-Indizes, neueste Aktivitaet zuerst -- Grundlage fuer
    die "Bekannte:r Proband:in fortsetzen"-Auswahl auf der Startseite."""
    if not os.path.isdir(SUBJECTS_DIR):
        return []
    subjects = []
    for fname in os.listdir(SUBJECTS_DIR):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(SUBJECTS_DIR, fname), encoding="utf-8") as f:
                subjects.append(json.load(f))
        except (json.JSONDecodeError, OSError):
            continue
    subjects.sort(key=lambda s: s.get("last_session_at", ""), reverse=True)
    return subjects


def generate_subject_id(prefix: str = "NV") -> str:
    """Erzeugt eine neue, pseudonyme Proband:innen-ID, kollisionsgeprueft gegen bereits
    vergebene IDs. Bei 32^4 ~ 1 Million moeglichen Kombinationen ist mehr als ein Versuch
    praktisch nie noetig."""
    existing = {s["subject_id"] for s in list_subjects()}
    for _ in range(50):
        candidate = f"{prefix}-{''.join(random.choices(ID_ALPHABET, k=ID_LENGTH))}"
        if candidate not in existing:
            return candidate
    raise RuntimeError("Konnte keine kollisionsfreie Proband-ID erzeugen (sehr unwahrscheinlich).")


def bind_subject_to_session(session_id: str, subject_id: str, age: int) -> None:
    """Ordnet die aktuelle Sitzung einer Proband:innen-ID zu: speichert subject_id/Alter in
    st.session_state (fuer die laufende Sitzung + Anzeige auf jeder Seite, siehe
    core/shared.py::render_subject_badge()), persistiert sofort die Sitzungsdatei
    (core/session_store.py -- auch wenn noch keine Aufnahme existiert) UND aktualisiert den
    Proband:innen-Index (derived/_subjects/<id>.json)."""
    st.session_state["subject_id"] = subject_id
    st.session_state["subject_age"] = age
    save_session_snapshot(session_id)

    now = datetime.now(timezone.utc).isoformat()
    path = _subject_file(subject_id)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            record = json.load(f)
    else:
        record = {"subject_id": subject_id, "created_at": now, "session_ids": []}

    if session_id not in record["session_ids"]:
        record["session_ids"].append(session_id)
    record["last_session_at"] = now
    record["last_age"] = age
    record["n_sessions"] = len(record["session_ids"])

    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


def require_subject_or_stop() -> None:
    """Blockiert die Seite, wenn noch keine Proband:innen-ID zugeordnet ist (Pflichtschritt,
    Nutzer-Entscheidung 2026-08-15) -- analog zum EDF-Analyzer-Muster `get_edf_or_stop()`. Muss
    ganz oben in jeder Modul-/Report-Seite aufgerufen werden, VOR jeder anderen Ausgabe. Die
    Zuordnung selbst passiert auf views/start.py."""
    if st.session_state.get("subject_id"):
        return
    st.warning(
        "Noch keine Proband:in zugeordnet. Bitte zuerst auf der Startseite eine neue ID "
        "anlegen oder eine bestehende fortsetzen.",
        icon=":material/person_add:",
    )
    if st.button("Zur Startseite", icon=":material/arrow_back:"):
        st.switch_page("views/start.py")
    st.stop()
