"""Persistentes Speicherschema (P4, siehe docs/backlog.md "Konzept: Modul-basierte, geführte
Analyse") -- schreibt den Sitzungs-Zustand (st.session_state["module_results"]) bei jeder
Änderung nach Platte, damit er einen Browser-Reload übersteht. Streamlit's session_state
selbst überlebt das NICHT (ein harter Reload erzeugt eine neue Session/WebSocket-Verbindung,
Navigation zwischen Modulseiten dagegen schon).

Session-Identifikation über eine ID in der URL (st.query_params), NICHT über ein Login-/
Patienten-System (das gibt es noch nicht -- Uploads landen weiterhin alle im gemeinsamen
`_uploads`-Namespace, siehe core/audio.py). Ein Reload mit derselben URL laedt dieselbe
Sitzung zurueck, ein neuer Tab ohne den Query-Parameter bekommt eine neue Sitzung.

Schema Version 1: schema_version/session_id/created_at/updated_at + module_results OHNE rohe
Audio-Bytes (die liegen schon als WAV-Dateien unter derived/_uploads/, referenziert per
recording_path -- beim Laden werden die Bytes bei Bedarf neu von der Platte gelesen, statt sie
doppelt/redundant im JSON zu halten).
"""

import json
import os
import uuid
from datetime import datetime, timezone

import streamlit as st

SCHEMA_VERSION = 1
DERIVED_DIR = os.environ.get("NEUROVOICE_DERIVED_DIR", "/derived")
SESSIONS_DIR = os.path.join(DERIVED_DIR, "_sessions")


def get_session_id() -> str:
    """Liest die Session-ID aus der URL (?session=...) oder legt eine neue an und traegt sie
    in die URL ein, damit ein Reload dieselbe Sitzung wiederfindet."""
    sid = st.query_params.get("session")
    if not sid:
        sid = uuid.uuid4().hex[:12]
        st.query_params["session"] = sid
    return sid


def _session_file(session_id: str) -> str:
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    # Session-ID kommt aus unserer eigenen uuid4()-Erzeugung, aber defensiv trotzdem
    # sanitisieren -- gleiches Pfad-Traversal-Prinzip wie bei save_uploaded_wav().
    safe_id = "".join(c for c in session_id if c.isalnum())[:64] or "unknown"
    return os.path.join(SESSIONS_DIR, f"{safe_id}.json")


def save_session_snapshot(session_id: str) -> None:
    """Schreibt st.session_state['module_results'] nach Platte -- OHNE audio_bytes."""
    module_results = st.session_state.get("module_results", {})

    serializable = {}
    for module, subtasks in module_results.items():
        serializable[module] = {}
        for subtask, takes in subtasks.items():
            serializable[module][subtask] = [
                {k: v for k, v in take.items() if k != "audio_bytes"}
                for take in takes
            ]

    path = _session_file(session_id)
    existing_created_at = None
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                existing_created_at = json.load(f).get("created_at")
        except (json.JSONDecodeError, OSError):
            existing_created_at = None

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "session_id": session_id,
        # P10 (docs/backlog.md): Proband:innen-Zuordnung -- subject_id gilt ueber mehrere
        # Sitzungen hinweg (core/subject_store.py), Alter wird JE SITZUNG neu erfasst.
        "subject_id": st.session_state.get("subject_id"),
        "subject_age_at_session": st.session_state.get("subject_age"),
        # Punkt 20 (docs/backlog.md): Aufnahmebedingungen der Sitzung -- die je Take gestempelte
        # Kopie steckt ohnehin in `modules`, das hier ist der aktuelle Sitzungs-Stand, damit ein
        # Reload das Formular nicht leer zuruecklaesst.
        "recording_setup": st.session_state.get("recording_setup"),
        "created_at": existing_created_at or now,
        "updated_at": now,
        "modules": serializable,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_session_snapshot(session_id: str) -> None:
    """Laedt eine gespeicherte Sitzung zurueck in st.session_state, falls vorhanden UND
    st.session_state noch leer ist (verhindert, dass ein Laden waehrend derselben Sitzung
    frische, noch nicht gespeicherte Aenderungen ueberschreibt)."""
    path = _session_file(session_id)
    if not os.path.exists(path):
        return

    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        return

    # P10: subject_id/Alter IMMER uebernehmen, unabhaengig vom module_results-Fruehausstieg
    # unten -- leichtgewichtig, kein Risiko frische Take-Aenderungen zu ueberschreiben (anders
    # als module_results, das deshalb den strengeren Guard behaelt).
    if payload.get("subject_id") and not st.session_state.get("subject_id"):
        st.session_state["subject_id"] = payload["subject_id"]
    if payload.get("subject_age_at_session") is not None and st.session_state.get("subject_age") is None:
        st.session_state["subject_age"] = payload["subject_age_at_session"]
    if payload.get("recording_setup") and not st.session_state.get("recording_setup"):
        st.session_state["recording_setup"] = payload["recording_setup"]

    if st.session_state.get("module_results"):
        return

    module_results = {}
    for module, subtasks in payload.get("modules", {}).items():
        module_results[module] = {}
        for subtask, takes in subtasks.items():
            restored = []
            for take in takes:
                recording_path = take.get("recording_path")
                audio_bytes = b""
                if recording_path and os.path.exists(recording_path):
                    with open(recording_path, "rb") as af:
                        audio_bytes = af.read()
                restored.append({**take, "audio_bytes": audio_bytes})
            module_results[module][subtask] = restored

    st.session_state["module_results"] = module_results
    st.session_state["_session_loaded_at"] = payload.get("updated_at")


def load_previous_session_values(subject_id: str, current_session_id: str) -> dict | None:
    """Sucht die juengste FRUEHERE Sitzung derselben Proband:in und liefert deren Kennwerte
    flach, als Referenz fuer die Dysarthrie-Marker (core/wertung.py).

    Warum die Voraufnahme und nicht ein Normbereich: an den echten SVD-Faellen hat sich gezeigt,
    dass absolute Literaturgrenzen zu unempfindlich sind, um erkrankte von gesunden Sprecher:innen
    zu trennen -- waehrend der Gradient INNERHALB derselben Aufnahmekette eindeutig ist (siehe
    core/wertung.py-Modulkopf). Der Vergleich mit einer frueheren Aufnahme derselben Person bei
    gleichem Setup ist deshalb die belastbarste verfuegbare Referenz und zugleich der erklaerte
    Kernzweck des Projekts.

    Gibt None zurueck, wenn es keine fruehere Sitzung gibt -- der Aufrufer muss das sichtbar
    machen, statt stillschweigend auf eine schwaechere Referenz auszuweichen.
    """
    from core.interpretation import flatten_take

    if not subject_id:
        return None

    kandidaten = []
    if not os.path.isdir(SESSIONS_DIR):
        return None
    for name in os.listdir(SESSIONS_DIR):
        if not name.endswith(".json"):
            continue
        pfad = os.path.join(SESSIONS_DIR, name)
        try:
            with open(pfad, encoding="utf-8") as f:
                payload = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if payload.get("subject_id") != subject_id:
            continue
        if payload.get("session_id") == current_session_id:
            continue
        if not payload.get("modules"):
            continue
        kandidaten.append(payload)

    if not kandidaten:
        return None

    juengste = max(kandidaten, key=lambda p: p.get("updated_at") or "")

    werte: dict = {}
    for subtasks in juengste.get("modules", {}).values():
        for takes in subtasks.values():
            gewaehlt = next((t for t in takes if t.get("selected")), takes[-1] if takes else None)
            if gewaehlt:
                # Spaetere Module ueberschreiben frueher gesetzte Schluessel nicht -- der erste
                # gefundene Wert je Kennwert gewinnt, damit die Referenz stabil bleibt.
                for k, v in flatten_take(gewaehlt).items():
                    werte.setdefault(k, v)

    return {
        "session_id": juengste.get("session_id"),
        "aufgenommen_am": (juengste.get("created_at") or "")[:10],
        "werte": werte,
    } if werte else None
