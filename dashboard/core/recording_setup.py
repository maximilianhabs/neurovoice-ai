"""Strukturierte Aufnahmebedingungen je Sitzung (docs/backlog.md, Punkt 20 aus dem externen
KI-Review 2026-08-20, umgesetzt 2026-08-20).

WARUM: unterschiedliche Aufnahmeketten beeinflussen Perturbationsmasse (Jitter/Shimmer/HNR)
nachweislich -- unser eigener Befund beim SVD-Vergleich (docs/externe_testdaten.md): unsere
GESUNDEN Eigenaufnahmen schnitten dort schlechter ab als die SVD-Patient:innen. Die naheliegende
Erklaerung ist die Aufnahmekette (Mikrofon/Abstand/Raum), nicht die Stimme -- belegen liess sich
das bisher nicht, weil die Bedingungen nie mitgeschrieben wurden. Ohne diese Felder bleibt hinter
jedem Perturbationswert der Verdacht, dass das Mikrofon gemessen wird und nicht der Sprecher.

WIE (bewusste Zurueckhaltung, siehe Backlog-Vorgabe "nur wenn es die Aufnahme-UX nicht
verkompliziert"): einmal pro Sitzung auf der Startseite in einem eingeklappten Abschnitt,
komplett optional, KEIN Pflichtfeld und KEIN zusaetzlicher Schritt im Aufnahme-Fluss der 4
Module. Wer nichts angibt, merkt von der Funktion nichts.

Gestempelt wird der Zustand JE TAKE (core/module_state.py::add_take()), nicht nur je Sitzung --
wechselt jemand mitten in der Sitzung das Mikrofon, behaelt jede Aufnahme, was zu ihrem
Zeitpunkt galt. Nicht ausgefuellte Felder werden weggelassen statt mit einem Platzhalter
gefuellt: ein leeres Feld heisst "unbekannt", und das soll spaeter auch als unbekannt lesbar
sein, statt eine Bedingung vorzutaeuschen."""

from __future__ import annotations

import streamlit as st

SESSION_KEY = "recording_setup"

NOT_SPECIFIED = "nicht angegeben"

MICROPHONE_TYPES = [
    NOT_SPECIFIED,
    "Headset",
    "USB-Standmikrofon",
    "Ansteckmikrofon (Lavalier)",
    "Eingebautes Laptop-/Tablet-Mikrofon",
    "Smartphone",
    "Studiomikrofon (XLR/Interface)",
    "Sonstiges",
]

MIC_DISTANCES = [
    NOT_SPECIFIED,
    "unter 10 cm",
    "10-30 cm",
    "30-50 cm",
    "ueber 50 cm",
]

ROOM_CONDITIONS = [
    NOT_SPECIFIED,
    "Ruhiger Raum",
    "Normaler Praxis-/Bueroraum",
    "Halliger Raum",
    "Hoerbare Stoergeraeusche",
]

_FIELD_LABELS = {
    "microphone_type": "Mikrofon",
    "microphone_model": "Modell",
    "mic_distance": "Abstand",
    "room_condition": "Raum",
}


def get_recording_setup() -> dict:
    """Aktuell in dieser Sitzung eingestellte Aufnahmebedingungen -- nur die tatsaechlich
    ausgefuellten Felder. Leeres Dict, wenn nichts angegeben wurde."""
    setup = st.session_state.get(SESSION_KEY) or {}
    return {k: v for k, v in setup.items() if v and v != NOT_SPECIFIED}


def set_recording_setup(setup: dict) -> None:
    st.session_state[SESSION_KEY] = {k: v for k, v in setup.items() if v and v != NOT_SPECIFIED}


def describe_recording_setup(setup: dict | None) -> str:
    """Einzeilige Zusammenfassung fuer Anzeige/Report. Gibt bewusst einen klaren
    'nicht dokumentiert'-Hinweis zurueck statt eines leeren Strings -- eine fehlende Angabe ist
    beim spaeteren Vergleich eine echte Information, kein Nichts."""
    setup = setup or {}
    parts = [f"{label}: {setup[key]}" for key, label in _FIELD_LABELS.items() if setup.get(key)]
    return " · ".join(parts) if parts else "Aufnahmebedingungen nicht dokumentiert"


def render_recording_setup_editor() -> None:
    """Eingeklappter, optionaler Abschnitt fuer die Startseite (views/start.py)."""
    current = st.session_state.get(SESSION_KEY) or {}
    summary = describe_recording_setup(current)

    with st.expander(f"Aufnahmebedingungen (optional) — {summary}", expanded=False):
        st.caption(
            "Freiwillig, aber hilfreich: Mikrofon, Abstand und Raum beeinflussen Jitter, Shimmer "
            "und HNR messbar. Sind sie dokumentiert, lassen sich spätere Aufnahmen gezielt mit "
            "vergleichbaren Bedingungen gegenüberstellen — sonst bleibt offen, ob ein "
            "veränderter Wert an der Stimme oder an der Aufnahmekette liegt."
        )

        col1, col2 = st.columns(2)
        mic_type = col1.selectbox(
            "Mikrofon-Typ", MICROPHONE_TYPES,
            index=MICROPHONE_TYPES.index(current.get("microphone_type", NOT_SPECIFIED))
            if current.get("microphone_type", NOT_SPECIFIED) in MICROPHONE_TYPES else 0,
        )
        mic_model = col2.text_input(
            "Gerät/Modell (optional)", value=current.get("microphone_model", ""),
            placeholder="z. B. Jabra Evolve 40",
        )

        col3, col4 = st.columns(2)
        distance = col3.selectbox(
            "Abstand zum Mikrofon", MIC_DISTANCES,
            index=MIC_DISTANCES.index(current.get("mic_distance", NOT_SPECIFIED))
            if current.get("mic_distance", NOT_SPECIFIED) in MIC_DISTANCES else 0,
        )
        room = col4.selectbox(
            "Raumsituation", ROOM_CONDITIONS,
            index=ROOM_CONDITIONS.index(current.get("room_condition", NOT_SPECIFIED))
            if current.get("room_condition", NOT_SPECIFIED) in ROOM_CONDITIONS else 0,
        )

        if st.button("Aufnahmebedingungen übernehmen", icon=":material/save:"):
            set_recording_setup({
                "microphone_type": mic_type,
                "microphone_model": mic_model.strip(),
                "mic_distance": distance,
                "room_condition": room,
            })
            # Gilt ab jetzt fuer neue Aufnahmen -- bereits gespeicherte Takes behalten bewusst,
            # was zu ihrem Zeitpunkt galt (sonst waere die Angabe nachtraeglich erfunden).
            st.success(
                "Gespeichert. Gilt für alle ab jetzt aufgenommenen Versuche — bereits "
                "vorhandene Aufnahmen behalten ihre bisherige Angabe.",
                icon=":material/check:",
            )
            st.rerun()
