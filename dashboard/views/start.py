"""Startseite (P10, docs/backlog.md "Proband:innen-Erfassung am Sitzungsanfang") -- erster
Pflichtschritt jeder Sitzung: eine pseudonyme Proband:innen-ID zuweisen, bevor irgendein
Modul zugaenglich ist (core/subject_store.py::require_subject_or_stop() blockiert die
anderen Seiten, solange das nicht passiert ist).

Zwei Wege: neue ID generieren (Erstkontakt) oder eine bestehende ID fortsetzen (Folge-
Sitzung/Verlaufskontrolle) -- die ID selbst gilt ueber beliebig viele Sitzungen hinweg,
anders als die rein technische session_id (P4), die nur diese eine Sitzung kennzeichnet.
Bewusst KEIN Name/keine Initialen, nur ID + Alter (siehe core/subject_store.py-Docstring).
"""

import streamlit as st

from core.session_store import get_session_id
from core.subject_store import bind_subject_to_session, generate_subject_id, list_subjects, rename_subject

st.markdown(
    """
    <div class="dw-eyebrow">Sitzung starten</div>
    <div class="dw-hero-title">Proband:in zuordnen</div>
    <div class="dw-subtitle">Pflichtschritt — jede Aufnahme wird einer pseudonymen ID zugeordnet, nie einem Namen.</div>
    """,
    unsafe_allow_html=True,
)

editing = st.session_state.get("_subject_edit_mode", False)
confirming_discard = st.session_state.get("_confirm_discard_subject", False)

if st.session_state.get("subject_id") and confirming_discard:
    st.warning(
        f"Wirklich eine neue Zuordnung beginnen? **{st.session_state['subject_id']}** wird für "
        f"diesen Browser-Tab beendet. Bereits gespeicherte Aufnahmen/Analysen bleiben auf dem "
        f"Server erhalten und lassen sich über „Bekannte:r Proband:in fortsetzen“ wieder öffnen.",
        icon=":material/warning:",
    )
    col_confirm, col_cancel = st.columns(2)
    if col_confirm.button("Ja, neue:r Proband:in", icon=":material/person_add:", type="primary"):
        st.session_state.pop("subject_id", None)
        st.session_state.pop("subject_age", None)
        st.session_state.pop("module_results", None)
        st.session_state.pop("pending_new_id", None)
        st.session_state.pop("_confirm_discard_subject", None)
        st.session_state.pop("_subject_edit_mode", None)
        if "session" in st.query_params:
            del st.query_params["session"]
        st.rerun()
    if col_cancel.button("Abbrechen", icon=":material/close:"):
        st.session_state.pop("_confirm_discard_subject", None)
        st.rerun()

elif st.session_state.get("subject_id") and editing:
    current_id = st.session_state["subject_id"]
    current_age = st.session_state.get("subject_age") or 0
    st.info(f"**{current_id}** wird bearbeitet.", icon=":material/edit:")
    new_id = st.text_input("Proband:innen-ID", value=current_id)
    new_age = st.number_input("Alter (Jahre)", min_value=0, max_value=120, step=1, value=int(current_age))
    col_save, col_cancel = st.columns(2)
    if col_save.button("Speichern", icon=":material/save:", type="primary"):
        try:
            saved_id = rename_subject(current_id, new_id.strip())
        except ValueError as exc:
            st.error(str(exc))
        else:
            bind_subject_to_session(get_session_id(), saved_id, int(new_age), is_rename=True)
            st.session_state.pop("_subject_edit_mode", None)
            st.success(f"Gespeichert: **{saved_id}**, Alter {int(new_age)}.")
            st.rerun()
    if col_cancel.button("Abbrechen", icon=":material/close:"):
        st.session_state.pop("_subject_edit_mode", None)
        st.rerun()

elif st.session_state.get("subject_id"):
    st.success(
        f"Diese Sitzung ist bereits **{st.session_state['subject_id']}** zugeordnet "
        f"(Alter {st.session_state.get('subject_age', '–')})."
    )
    col_next, col_edit, col_new = st.columns(3)
    if col_next.button("Weiter zu Modul 1 (Vokalisation)", icon=":material/arrow_forward:"):
        st.switch_page("views/vokalisation.py")
    if col_edit.button("Bearbeiten", icon=":material/edit:"):
        st.session_state["_subject_edit_mode"] = True
        st.rerun()
    if col_new.button("Neue:r Proband:in", icon=":material/person_add:"):
        st.session_state["_confirm_discard_subject"] = True
        st.rerun()
else:
    tab_new, tab_existing = st.tabs(["Neue:r Proband:in", "Bekannte:r Proband:in fortsetzen"])

    with tab_new:
        st.caption("Erzeugt eine neue, zufällige, pseudonyme ID — kein Name, keine Initialen.")
        if st.button("ID generieren", icon=":material/badge:"):
            st.session_state["pending_new_id"] = generate_subject_id()

        pending_id = st.session_state.get("pending_new_id")
        if pending_id:
            st.markdown(f"### `{pending_id}`")
            st.caption("Bitte notieren — diese ID wird für alle zukünftigen Sitzungen derselben Person benötigt.")
            age_new = st.number_input("Alter (Jahre)", min_value=0, max_value=120, step=1, key="age_new")
            if st.button("Sitzung starten", key="start_new", icon=":material/play_arrow:"):
                bind_subject_to_session(get_session_id(), pending_id, int(age_new))
                del st.session_state["pending_new_id"]
                st.switch_page("views/vokalisation.py")

    with tab_existing:
        subjects = list_subjects()
        if not subjects:
            st.caption("Noch keine bekannten Proband:innen vorhanden.")
        else:
            labels = [
                f"{s['subject_id']} — {s.get('n_sessions', 1)} Sitzung(en), zuletzt "
                f"{s.get('last_session_at', '–')[:10]}"
                for s in subjects
            ]
            idx = st.selectbox("Proband:in wählen", range(len(subjects)), format_func=lambda i: labels[i])
            chosen = subjects[idx]
            age_existing = st.number_input(
                "Alter (Jahre)", min_value=0, max_value=120, step=1,
                value=int(chosen.get("last_age") or 0), key="age_existing",
            )
            if st.button("Sitzung starten", key="start_existing", icon=":material/play_arrow:"):
                bind_subject_to_session(get_session_id(), chosen["subject_id"], int(age_existing))
                st.switch_page("views/vokalisation.py")
