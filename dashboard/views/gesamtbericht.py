"""Gesamtbericht — aggregiert Ergebnisse aus allen Modulen dieser Sitzung im Laborwert-Stil
(P5, siehe docs/backlog.md "Konzept: Modul-basierte, geführte Analyse"): Wert | Normbereich |
Status | Kontext-Kommentar je Parameter. Persistentes Speicherschema (P4) sorgt dafür, dass
die Sitzung auch einen Browser-Reload übersteht (core/session_store.py).

WICHTIG: Rein deskriptiv, KEINE Diagnose, KEIN Score (Nutzer-Vorgabe 2026-08-15) — der
Kontext-Kommentar sagt, mit welchen Erkrankungen ein Muster ASSOZIIERT wird, nie, dass der
Wert eine Erkrankung BEDEUTET. Inhaltliche Basis: docs/literatur_review.md.
"""

import streamlit as st

from core.interpretation import build_glossary_entries, build_rows, flatten_take
from core.session_store import get_session_id
from core.shared import render_glossary, render_interpretation_table
from core.subject_store import require_subject_or_stop

require_subject_or_stop()

st.markdown(
    """
    <div class="dw-eyebrow">Zusammenfassung</div>
    <div class="dw-hero-title">Gesamtbericht</div>
    <div class="dw-subtitle">Laborwert-Stil — deskriptiv, keine Diagnose</div>
    """,
    unsafe_allow_html=True,
)

# P10 (docs/backlog.md): Proband:innen-Zuordnung MUSS auf dem Report sichtbar sein (Nutzer-
# Vorgabe), nicht nur als Sidebar-Badge -- direkt unter dem Titel, prominent.
subject_id = st.session_state.get("subject_id")
subject_age = st.session_state.get("subject_age")
st.markdown(
    f'<div class="dw-card-subtle"><b>Proband:in:</b> <code>{subject_id}</code> · '
    f'<b>Alter:</b> {subject_age if subject_age is not None else "–"}</div>',
    unsafe_allow_html=True,
)
st.write("")

session_id = get_session_id()
st.caption(
    f"Sitzungs-ID: `{session_id}` — diese Seite unter derselben URL erneut öffnen (auch nach "
    "Browser-Neuladen), um die Ergebnisse wiederzufinden. Ein neuer Tab ohne diesen Link "
    "startet eine neue, leere Sitzung."
)

st.info(
    "**Wichtig**: Diese Übersicht ist rein beschreibend. Ein „auffälliger“ Wert bedeutet "
    "NICHT automatisch eine Erkrankung — der Kontext-Kommentar zeigt nur, mit welchen "
    "Mustern eine Auffälligkeit in der Literatur assoziiert wird. Keine Diagnose, keine "
    "ärztliche Einschätzung ersetzt."
)

results = st.session_state.get("module_results", {})
if not any(results.values()):
    st.info("Noch keine Modul-Ergebnisse in dieser Sitzung. Nimm mindestens ein Modul auf.")
else:
    # P11: Glossar-Eintraege ueber ALLE Module/Teilaufgaben hinweg sammeln + deduplizieren
    # (per Parameter-Label) -- viele Parameter (Jitter/Shimmer/HNR/CPPS/...) tauchen in
    # mehreren Modulen auf, ein Glossar-Block je Teilaufgabe waere stark redundant. Stattdessen
    # EIN gemeinsames Glossar am Ende des gesamten Berichts.
    seen_labels: set[str] = set()
    all_glossary_entries: list[dict] = []

    for module_name, subtasks in results.items():
        module_takes = {k: v for k, v in subtasks.items() if v}
        if not module_takes:
            continue
        st.subheader(module_name.capitalize())

        for subtask, takes in module_takes.items():
            selected = next((t for t in takes if t.get("selected")), takes[-1] if takes else None)
            if selected is None:
                continue

            flat = flatten_take(selected)
            rows = build_rows(flat)
            if not rows:
                continue

            st.markdown(
                f"**{subtask}** — Versuch {selected.get('take_number', '?')} von {len(takes)}, "
                f"aufgenommen {selected.get('recorded_at', '–')}"
            )
            render_interpretation_table(rows)

            for entry in build_glossary_entries(flat):
                if entry["label"] not in seen_labels:
                    seen_labels.add(entry["label"])
                    all_glossary_entries.append(entry)

    if all_glossary_entries:
        st.divider()
        with st.expander(f"Glossar & Literatur ({len(all_glossary_entries)} Parameter)"):
            render_glossary(sorted(all_glossary_entries, key=lambda e: e["label"]))
