"""Take-Management fuer die Modul-Seiten (siehe docs/backlog.md P1) -- mehrere Aufnahmen pro
Teilaufgabe, session-persistent (ueberlebt Navigation zwischen Seiten), manuelle Auswahl des
"besten" Versuchs (Nutzer-Entscheidung 2026-08-15: KEINE Mittelung ueber Versuche).

WICHTIGER BUGFIX-KONTEXT (2026-08-15): Vorherige Modul-Implementierung zeigte Ergebnisse nur
an, wenn der Upload-/Mikrofon-Widget in DIESEM Rerun einen frischen Wert hatte. Beim Navigieren
zu einer anderen Seite und zurueck ist der Widget-Wert wieder None (Streamlits Upload-Widgets
behalten ihren Wert nicht dauerhaft ueber Remounts), wodurch die UI faelschlich wie
"Datei verloren" wirkte -- Datei UND Analyse waren tatsaechlich noch vorhanden, wurden nur
nicht mehr angezeigt. Fix: IMMER aus `st.session_state` rendern, nie aus dem Widget-Rueckgabewert
direkt."""

import os

import streamlit as st


def get_takes(module: str, subtask: str) -> list[dict]:
    st.session_state.setdefault("module_results", {})
    st.session_state["module_results"].setdefault(module, {})
    st.session_state["module_results"][module].setdefault(subtask, [])
    return st.session_state["module_results"][module][subtask]


def add_take(module: str, subtask: str, take: dict) -> None:
    takes = get_takes(module, subtask)
    take["take_number"] = len(takes) + 1
    take["selected"] = len(takes) == 0  # erster Versuch automatisch als "bester" markiert
    takes.append(take)


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


def select_take(module: str, subtask: str, index: int) -> None:
    takes = get_takes(module, subtask)
    for i, t in enumerate(takes):
        t["selected"] = i == index


def selected_take(module: str, subtask: str) -> dict | None:
    takes = get_takes(module, subtask)
    for t in takes:
        if t.get("selected"):
            return t
    return takes[-1] if takes else None
