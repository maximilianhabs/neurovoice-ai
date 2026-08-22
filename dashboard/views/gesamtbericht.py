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
from core.recording_setup import describe_recording_setup
from core.report_export import build_excel_report, build_pdf_report, collect_report_data
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

    # Dysarthrie-Marker ZUERST (Nutzer-Wunsch 2026-08-22, docs/konzept_wertung.md): das ist die
    # Zusammenfassung des Berichts, kein Anhang. Referenz ist die juengste fruehere Sitzung
    # derselben Person -- ohne eine solche wird bewusst KEIN Ersatzmassstab verwendet.
    from core.session_store import load_previous_session_values
    from core.shared import render_dysarthrie_marker
    from core.wertung import dysarthrie_marker

    aktuelle_werte: dict = {}
    for subtasks in results.values():
        for takes in subtasks.values():
            gewaehlt = next((t for t in takes if t.get("selected")), takes[-1] if takes else None)
            if gewaehlt:
                for k, v in flatten_take(gewaehlt).items():
                    aktuelle_werte.setdefault(k, v)

    referenz = load_previous_session_values(
        st.session_state.get("subject_id"), get_session_id()
    )
    marker_ergebnis = dysarthrie_marker(aktuelle_werte, referenz["werte"]) if referenz else {
        "boxen": [], "marker_gesamt": 0, "marker_auffaellig": 0,
        "hoechste_stufe": None, "betroffene_boxen": [],
    }
    render_dysarthrie_marker(marker_ergebnis, referenz)
    st.divider()

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
            meta = selected.get("analysis_metadata") or {}
            if meta:
                st.caption(
                    f"Analyse-Version {meta.get('feature_schema_version', '–')} · "
                    f"Abtastrate {meta.get('audio_sampling_rate_hz', '–')} Hz · "
                    f"analysiert {meta.get('analysis_timestamp', '–')}  \n"
                    f"{describe_recording_setup(selected.get('recording_setup'))}"
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

    # P14 (docs/backlog.md, Nutzer-Feedback 2026-08-15): Export NUR auf Knopfdruck, nicht
    # automatisch bei jedem Seitenaufruf -- deshalb zweistufig: "erstellen" schreibt die Bytes
    # erst nach Klick in st.session_state, "herunterladen" liefert sie aus. Beide Formate
    # nutzen dieselbe collect_report_data()-Struktur, die wiederum dieselben
    # core.interpretation-Funktionen wie die Ansicht oben nutzt.
    st.divider()
    st.subheader("Export")
    st.caption(
        "Excel- und PDF-Report werden erst hier, auf Knopfdruck, erzeugt -- nicht automatisch "
        "bei jedem Laden dieser Seite."
    )
    file_stem = f"neurovoice_report_{subject_id or 'proband'}_{session_id}"

    col_excel, col_pdf = st.columns(2)
    with col_excel:
        if st.button("Excel-Report erstellen", icon=":material/grid_on:"):
            data = collect_report_data(session_id)
            st.session_state["_excel_report_bytes"] = build_excel_report(data)
        if "_excel_report_bytes" in st.session_state:
            st.download_button(
                "Excel-Report herunterladen",
                data=st.session_state["_excel_report_bytes"],
                file_name=f"{file_stem}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    with col_pdf:
        if st.button("PDF-Report erstellen", icon=":material/picture_as_pdf:"):
            data = collect_report_data(session_id)
            st.session_state["_pdf_report_bytes"] = build_pdf_report(data)
        if "_pdf_report_bytes" in st.session_state:
            st.download_button(
                "PDF-Report herunterladen",
                data=st.session_state["_pdf_report_bytes"],
                file_name=f"{file_stem}.pdf",
                mime="application/pdf",
            )
