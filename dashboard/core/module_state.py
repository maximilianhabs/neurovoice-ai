"""Take-Management fuer die Modul-Seiten (siehe docs/backlog.md P1) -- mehrere Aufnahmen pro
Teilaufgabe, session-persistent (ueberlebt Navigation zwischen Seiten), manuelle Auswahl des
"besten" Versuchs (Nutzer-Entscheidung 2026-08-15: KEINE Mittelung ueber Versuche).

WICHTIGER BUGFIX-KONTEXT (2026-08-15): Vorherige Modul-Implementierung zeigte Ergebnisse nur
an, wenn der Upload-/Mikrofon-Widget in DIESEM Rerun einen frischen Wert hatte. Beim Navigieren
zu einer anderen Seite und zurueck ist der Widget-Wert wieder None (Streamlits Upload-Widgets
behalten ihren Wert nicht dauerhaft ueber Remounts), wodurch die UI faelschlich wie
"Datei verloren" wirkte -- Datei UND Analyse waren tatsaechlich noch vorhanden, wurden nur
nicht mehr angezeigt. Fix: IMMER aus `st.session_state` rendern, nie aus dem Widget-Rueckgabewert
direkt.

P4 (2026-08-15): jede Aenderung (add/delete/select) wird zusaetzlich per
core/session_store.py auf Platte gespiegelt -- ueberlebt damit auch einen Browser-Reload,
nicht nur die Navigation zwischen Modulseiten innerhalb derselben Sitzung."""

import os
import uuid
from datetime import datetime, timezone

import streamlit as st

from core.recording_setup import get_recording_setup
from core.session_store import get_session_id, save_session_snapshot
from core.versioning import build_analysis_metadata


def get_takes(module: str, subtask: str) -> list[dict]:
    st.session_state.setdefault("module_results", {})
    st.session_state["module_results"].setdefault(module, {})
    st.session_state["module_results"][module].setdefault(subtask, [])
    return st.session_state["module_results"][module][subtask]


def _persist() -> None:
    save_session_snapshot(get_session_id())


def add_take(module: str, subtask: str, take: dict) -> None:
    takes = get_takes(module, subtask)
    take["take_id"] = uuid.uuid4().hex[:12]  # Analysis-ID fuer Reproduzierbarkeit
    take["take_number"] = len(takes) + 1
    take["selected"] = len(takes) == 0  # erster Versuch automatisch als "bester" markiert
    take["recorded_at"] = datetime.now(timezone.utc).isoformat()
    take["analysis_metadata"] = build_analysis_metadata(take.get("recording_path"))
    # Aufnahmebedingungen JE TAKE festhalten, nicht nur je Sitzung: wechselt jemand mitten in
    # der Sitzung das Mikrofon, behaelt jede Aufnahme, was zu ihrem Zeitpunkt galt.
    take["recording_setup"] = get_recording_setup()
    takes.append(take)
    _persist()


def delete_take(module: str, subtask: str, index: int) -> None:
    takes = get_takes(module, subtask)
    removed = takes.pop(index)
    # Datei von der Platte entfernen -- liegt in derived/_uploads/ (Session-Aufnahmen), keine
    # geschuetzten Rohdaten aus data/raw/ (siehe Projektprinzip "Original nie ueberschreiben").
    path = removed.get("recording_path")
    if path and os.path.exists(path):
        os.remove(path)
    if removed.get("selected") and takes:
        takes[0]["selected"] = True
    _persist()


def select_take(module: str, subtask: str, index: int) -> None:
    takes = get_takes(module, subtask)
    for i, t in enumerate(takes):
        t["selected"] = i == index
    _persist()


def selected_take(module: str, subtask: str) -> dict | None:
    takes = get_takes(module, subtask)
    for t in takes:
        if t.get("selected"):
            return t
    return takes[-1] if takes else None
