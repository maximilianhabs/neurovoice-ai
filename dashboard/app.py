"""NeuroVoice AI — Analyse-Dashboard. Navigations-Einstiegspunkt (Multi-Page, siehe
docs/backlog.md "Konzept: Modul-basierte, geführte Analyse"). Einzelne Seiten liegen unter
views/ -- st.set_page_config()/apply_global_style() laufen zentral hier, nicht nochmal in
den einzelnen Seiten aufrufen."""

import streamlit as st

from core.shared import apply_global_style

st.set_page_config(page_title="NeuroVoice AI — Analyse-Dashboard", layout="wide", page_icon="🎙️")
apply_global_style()

pg = st.navigation(
    {
        "Guide": [
            st.Page("views/vokalisation.py", title="1. Vokalisation", icon="🗣️"),
            st.Page("views/vorlesen.py", title="2. Vorlesen", icon="📖"),
            st.Page("views/spontansprache.py", title="3. Spontansprache", icon="💬"),
            st.Page("views/ddk.py", title="4. Diadochokinese", icon="🔁"),
            st.Page("views/gesamtbericht.py", title="Gesamtbericht", icon="📊"),
        ],
        "Sonstiges": [
            st.Page("views/testdaten.py", title="Testdaten & freie Auswahl", icon="🧪"),
        ],
    }
)
pg.run()
