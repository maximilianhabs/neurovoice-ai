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
from core.subject_store import bind_subject_to_session, generate_subject_id, list_subjects

st.markdown(
    """
    <div class="dw-eyebrow">Sitzung starten</div>
    <div class="dw-hero-title">Proband:in zuordnen</div>
    <div class="dw-subtitle">Pflichtschritt — jede Aufnahme wird einer pseudonymen ID zugeordnet, nie einem Namen.</div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("subject_id"):
    st.success(
        f"Diese Sitzung ist bereits **{st.session_state['subject_id']}** zugeordnet "
        f"(Alter {st.session_state.get('subject_age', '–')})."
    )
    if st.button("Weiter zu Modul 1 (Vokalisation)", icon=":material/arrow_forward:"):
        st.switch_page("views/vokalisation.py")
    st.divider()
    st.caption(
        "Um eine andere Proband:in zuzuordnen, die App in einem neuen Browser-Tab ohne "
        "Sitzungs-Link öffnen (erzeugt eine neue, eigene Sitzung)."
    )
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
