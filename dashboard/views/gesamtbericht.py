"""Gesamtbericht — aggregiert Ergebnisse aus allen Modulen dieser Sitzung im Laborwert-Stil
(P5, siehe docs/backlog.md "Konzept: Modul-basierte, geführte Analyse"): Wert | Normbereich |
Status | Kontext-Kommentar je Parameter. Persistentes Speicherschema (P4) sorgt dafür, dass
die Sitzung auch einen Browser-Reload übersteht (core/session_store.py).

WICHTIG: Rein deskriptiv, KEINE Diagnose, KEIN Score (Nutzer-Vorgabe 2026-08-15) — der
Kontext-Kommentar sagt, mit welchen Erkrankungen ein Muster ASSOZIIERT wird, nie, dass der
Wert eine Erkrankung BEDEUTET. Inhaltliche Basis: docs/literatur_review.md.
"""

import pandas as pd
import streamlit as st

from core.interpretation import PARAMETER_INFO, interpret
from core.session_store import get_session_id

st.markdown(
    """
    <div class="dw-eyebrow">Zusammenfassung</div>
    <div class="dw-hero-title">📊 Gesamtbericht</div>
    <div class="dw-subtitle">Laborwert-Stil — deskriptiv, keine Diagnose</div>
    """,
    unsafe_allow_html=True,
)

session_id = get_session_id()
st.caption(
    f"Sitzungs-ID: `{session_id}` — diese Seite unter derselben URL erneut öffnen (auch nach "
    "Browser-Neuladen), um die Ergebnisse wiederzufinden. Ein neuer Tab ohne diesen Link "
    "startet eine neue, leere Sitzung."
)

st.info(
    "ℹ️ **Wichtig**: Diese Übersicht ist rein beschreibend. Ein „auffälliger“ Wert bedeutet "
    "NICHT automatisch eine Erkrankung — der Kontext-Kommentar zeigt nur, mit welchen "
    "Mustern eine Auffälligkeit in der Literatur assoziiert wird. Keine Diagnose, keine "
    "ärztliche Einschätzung ersetzt."
)

results = st.session_state.get("module_results", {})
if not any(results.values()):
    st.info("Noch keine Modul-Ergebnisse in dieser Sitzung. Nimm mindestens ein Modul auf.")
else:
    for module_name, subtasks in results.items():
        module_takes = {k: v for k, v in subtasks.items() if v}
        if not module_takes:
            continue
        st.subheader(module_name.capitalize())

        for subtask, takes in module_takes.items():
            selected = next((t for t in takes if t.get("selected")), takes[-1] if takes else None)
            if selected is None:
                continue

            # Alle Kennwert-Gruppen (phonation/dynamics/cpp/... je nach Modul unterschiedlich
            # benannt) zu einem flachen Dict zusammenfassen, um gegen PARAMETER_INFO zu suchen.
            flat: dict = {}
            for key, val in selected.items():
                if isinstance(val, dict):
                    flat.update(val)

            rows = []
            for param_key in PARAMETER_INFO:
                if param_key not in flat:
                    continue
                info = interpret(param_key, flat[param_key])
                if info is None:
                    continue
                value_str = f"{info['value']:.2f} {info['unit']}".strip() if info["value"] is not None else "–"
                rows.append({
                    "Parameter": info["label"],
                    "Wert": value_str,
                    "Normbereich": info["range"],
                    "Status": info["status"],
                    "Kontext (deskriptiv)": info["context"],
                })

            if not rows:
                continue

            st.markdown(
                f"**{subtask}** — Versuch {selected.get('take_number', '?')} von {len(takes)}, "
                f"aufgenommen {selected.get('recorded_at', '–')}"
            )
            df = pd.DataFrame(rows)
            st.dataframe(df, width="stretch", hide_index=True)

            age_caveats = {
                interpret(k, flat[k])["age_caveat"]
                for k in PARAMETER_INFO
                if k in flat and interpret(k, flat[k]) and interpret(k, flat[k])["age_caveat"]
            }
            for caveat in age_caveats:
                st.caption(f"⚠️ {caveat}")
