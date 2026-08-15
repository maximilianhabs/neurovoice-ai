"""Gesamtbericht — aggregiert Ergebnisse aus allen Modulen dieser Sitzung. Noch nicht gebaut
(braucht persistentes Speicherschema, siehe docs/backlog.md P4/P5). Zeigt vorerst nur, was
in dieser Browser-Sitzung bereits in st.session_state["module_results"] gesammelt wurde
(verschwindet bei Neuladen -- persistente Speicherung ist P4)."""

import streamlit as st

st.markdown(
    """
    <div class="dw-eyebrow">Zusammenfassung</div>
    <div class="dw-hero-title">📊 Gesamtbericht</div>
    <div class="dw-subtitle">Noch im Aufbau — vorerst nur Sitzungs-Zwischenstand</div>
    """,
    unsafe_allow_html=True,
)

results = st.session_state.get("module_results", {})
if not any(results.values()):
    st.info(
        "Noch keine Modul-Ergebnisse in dieser Sitzung. Der vollständige Laborwert-Stil-"
        "Gesamtbericht (Normbereiche, Kontext-Kommentare, persistente Speicherung über "
        "Sitzungen hinweg) ist noch nicht gebaut — siehe docs/backlog.md P4/P5."
    )
else:
    st.caption(
        "⚠️ Nur Sitzungs-Zwischenstand (verschwindet bei Neuladen) — persistente Speicherung "
        "folgt in P4. Roh-Kennwerte, noch keine Normbereiche/Kontext-Kommentare (P5)."
    )
    for module_name, module_data in results.items():
        if not module_data:
            continue
        st.subheader(module_name.capitalize())
        st.json(module_data)
