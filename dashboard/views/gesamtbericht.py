"""Gesamtbericht — aggregiert Ergebnisse aus allen Modulen dieser Sitzung. Persistentes
Speicherschema (P4) ist umgesetzt (siehe core/session_store.py) -- der Sitzungs-Zustand
übersteht jetzt auch einen Browser-Reload, solange dieselbe URL (mit ?session=...) verwendet
wird. Echte Laborwert-Stil-Interpretation (Normbereiche, Kontext-Kommentare) ist P5, noch
nicht umgesetzt -- hier vorerst nur strukturierte Roh-Kennwerte je Modul."""

import streamlit as st

from core.session_store import get_session_id

st.markdown(
    """
    <div class="dw-eyebrow">Zusammenfassung</div>
    <div class="dw-hero-title">📊 Gesamtbericht</div>
    <div class="dw-subtitle">Persistente Sitzung — echte Interpretation folgt (P5)</div>
    """,
    unsafe_allow_html=True,
)

session_id = get_session_id()
st.caption(
    f"Sitzungs-ID: `{session_id}` — diese Seite unter derselben URL erneut öffnen (auch nach "
    "Browser-Neuladen), um die Ergebnisse wiederzufinden. Ein neuer Tab ohne diesen Link "
    "startet eine neue, leere Sitzung."
)

results = st.session_state.get("module_results", {})
if not any(results.values()):
    st.info(
        "Noch keine Modul-Ergebnisse in dieser Sitzung. Nimm mindestens ein Modul auf, dann "
        "erscheinen hier die Kennwerte. Der vollständige Laborwert-Stil-Gesamtbericht "
        "(Normbereiche, Kontext-Kommentare) ist noch nicht gebaut — siehe docs/backlog.md P5."
    )
else:
    st.caption(
        "⚠️ Roh-Kennwerte des jeweils ausgewählten „besten“ Versuchs je Teilaufgabe — noch "
        "keine Normbereiche/Kontext-Kommentare (P5)."
    )
    for module_name, subtasks in results.items():
        module_takes = {k: v for k, v in subtasks.items() if v}
        if not module_takes:
            continue
        st.subheader(module_name.capitalize())
        for subtask, takes in module_takes.items():
            selected = next((t for t in takes if t.get("selected")), takes[-1] if takes else None)
            if selected is None:
                continue
            st.markdown(f"**{subtask}** — Versuch {selected.get('take_number', '?')} "
                        f"(von {len(takes)}), aufgenommen {selected.get('recorded_at', '–')}")
            # audio_bytes bewusst ausschliessen -- rohe Bytes wuerden st.json() nur zumuellen,
            # nicht sinnvoll darstellbar.
            display = {k: v for k, v in selected.items() if k not in ("audio_bytes", "recording_path")}
            st.json(display, expanded=False)
