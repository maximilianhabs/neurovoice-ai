"""Modul 4 von 4: Diadochokinese (DDK) — letztes und motorisch anspruchsvollstes Modul im
Guide, siehe docs/backlog.md "Konzept: Modul-basierte, geführte Analyse", P3. Baut auf dem
Vokalisation-Muster (views/vokalisation.py, 2 Tabs statt 3) auf, inkl. Take-Management
(core/module_state.py).

Reihenfolge einfach->schwer: letztes Modul, da schnelle koordinierte Silbenfolgen als
motorisch/kognitiv anspruchsvollste Aufgabe der Batterie gelten (siehe Konzept-Diskussion).

Kein Transkriptions-Schritt nötig (keine linguistische Auswertung bei DDK) -- reine Akustik,
Ergebnis sofort nach der Aufnahme verfügbar. DDK-Rate hat keinen etablierten Normbereich
(daher informative Gauge ohne Ampel-Zonen, wie CPPS).
"""

import os

import pandas as pd
import parselmouth
import streamlit as st

from core.audio import articulation_features, ddk_rate_features, recording_quality_features, save_uploaded_wav
from core.interpretation import build_glossary_entries, build_rows, build_tiles, flatten_take
from core.module_state import add_take, delete_take, get_takes, select_take
from core.plots import ddk_rhythm_figure, intensity_figure, spectrogram_figure, waveform_figure
from core.shared import (
    SPECTROGRAM_LEGEND_CAPTION,
    instruction_text_scale_control,
    kpi_tile,
    quality_tiles,
    recording_duration_feedback_style,
    recording_start_blip,
    render_glossary,
    render_interpretation_table,
)
from core.subject_store import require_subject_or_stop

require_subject_or_stop()
recording_start_blip()

# Ziel-Dauern je Teilaufgabe fuer P8 (Live-Aufnahmedauer-Farbfeedback) -- ddkgemischt zielt auf
# ca. 10s, ddkeinzeln auf ca. 15s (3x ~5s nacheinander pa/ta/ka).
DURATION_FEEDBACK_THRESHOLDS = {
    "ddkgemischt": {"green_s": 10, "orange_s": 15, "red_s": 20},
    "ddkeinzeln": {"green_s": 15, "orange_s": 20, "red_s": 30},
}

DERIVED_DIR = os.environ.get("NEUROVOICE_DERIVED_DIR", "/derived")
MODULE = "ddk"

SUB_TASKS = {
    "ddkgemischt": {
        "label": "DDK kombiniert (Pflicht)",
        "instruction": (
            '<span class="dw-instruction-meta">Sprich so schnell und gleichmäßig wie möglich, '
            'für ca. 10 Sekunden:</span>'
            '<span class="dw-instruction-target">„pa-ta-ka-pa-ta-ka...“</span>'
        ),
        "required": True,
    },
    "ddkeinzeln": {
        "label": "DDK einzeln (optional)",
        "instruction": (
            '<span class="dw-instruction-meta">Sprich nacheinander, jeweils ca. 5 Sekunden, so '
            'schnell und gleichmäßig wie möglich:</span>'
            '<span class="dw-instruction-target">„pa-pa-pa...“ → „ta-ta-ta...“ → „ka-ka-ka...“</span>'
        ),
        "required": False,
    },
}


def _fmt(value, decimals=1):
    return f"{value:.{decimals}f}" if value is not None else "–"


st.markdown(
    """
    <div class="dw-eyebrow">Modul 4 von 4 · Guide</div>
    <div class="dw-hero-title">Diadochokinese</div>
    <div class="dw-subtitle">Schnelle Silbenfolgen — motorisch anspruchsvollste Aufgabe der Batterie</div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs([meta["label"] for meta in SUB_TASKS.values()])

for (task_key, meta), tab in zip(SUB_TASKS.items(), tabs):
    with tab:
        instr_col, scale_col = st.columns([4, 1])
        with instr_col:
            st.markdown(f'<div class="dw-card-subtle">{meta["instruction"]}</div>', unsafe_allow_html=True)
        with scale_col:
            instruction_text_scale_control(key=task_key)
        st.write("")

        takes = get_takes(MODULE, task_key)

        add_label = "Weiteren Versuch aufnehmen" if takes else "Aufnahme starten"
        source_mode = st.radio(
            "Quelle", ["Mikrofon aufnehmen", "Datei hochladen (WAV)"],
            key=f"source_{task_key}", horizontal=True,
        )
        if source_mode == "Mikrofon aufnehmen":
            recording_duration_feedback_style(**DURATION_FEEDBACK_THRESHOLDS[task_key], key=task_key)
            uploaded = st.audio_input(add_label, sample_rate=48000, key=f"mic_{task_key}_{len(takes)}")
            filename = f"{task_key}.wav"
        else:
            uploaded = st.file_uploader("WAV-Datei (max. 25 MB)", type=["wav"], key=f"file_{task_key}_{len(takes)}")
            filename = uploaded.name if uploaded is not None else None

        if uploaded is not None:
            try:
                recording = save_uploaded_wav(DERIVED_DIR, filename, uploaded.getvalue(), task=task_key)
            except ValueError as exc:
                st.error(str(exc))
                recording = None
            if recording is not None:
                add_take(MODULE, task_key, {
                    "recording_path": recording.path,
                    "filename": recording.filename,
                    "audio_bytes": uploaded.getvalue(),
                    "ddk": ddk_rate_features(recording.path),
                    "articulation": articulation_features(recording.path),
                })
                st.success(f"Aufgenommen: {recording.filename}")
                st.rerun()

        if not takes:
            if meta["required"]:
                st.info("Diese Aufgabe ist die Pflichtaufgabe des Moduls.")
            else:
                st.caption("Optional — kann übersprungen werden.")
        else:
            st.divider()
            st.markdown(f"**{len(takes)} Versuch(e) aufgenommen** — bester Versuch fließt in den Gesamtbericht ein.")

            take_labels = [f"Versuch {t['take_number']}" for t in takes]
            selected_idx = next((i for i, t in enumerate(takes) if t.get("selected")), 0)
            chosen_idx = st.radio(
                "Bester Versuch", range(len(takes)), format_func=lambda i: take_labels[i],
                index=selected_idx, horizontal=True, key=f"choose_{task_key}",
            )
            if chosen_idx != selected_idx:
                select_take(MODULE, task_key, chosen_idx)
                st.rerun()

            take = takes[chosen_idx]
            st.audio(take["audio_bytes"], format="audio/wav")

            q = recording_quality_features(take["recording_path"])
            quality_tiles(q)

            with st.expander("Visualisierungen (Wellenform, Lautstärke, Spektrogramm)", expanded=True):
                sound = parselmouth.Sound(take["recording_path"])
                st.pyplot(waveform_figure(sound), width="stretch")
                st.pyplot(intensity_figure(sound), width="stretch")
                st.pyplot(spectrogram_figure(sound), width="stretch")
                st.caption(SPECTROGRAM_LEGEND_CAPTION)

            ddk = take["ddk"]
            articulation = take["articulation"]
            flat = flatten_take(take)

            # Bucket H (docs/backlog.md, Nutzer-Feedback 2026-08-15): Zyklen-Regelmäßigkeit
            # (CV) und Ø Zyklus-Intervall waren hier noch als rohe st.metric()-Zeile
            # stehengeblieben, obwohl sie schon PARAMETER_INFO-Einträge haben.
            tile_keys = ["ddk_rate_hz", "mean_burst_sharpness_db_s", "cycle_interval_cv", "mean_cycle_interval_s"]
            tiles = build_tiles({k: flat[k] for k in tile_keys if k in flat})
            tile_rows = [tiles[i:i + 3] for i in range(0, len(tiles), 3)]
            for row in tile_rows:
                cols = st.columns(3)
                for col, tile in zip(cols, row):
                    with col:
                        kpi_tile(tile["label"], tile["value_text"], tile["sub_text"], tile["zone"], tile["description"], tile.get("range_text"))

            st.caption(f"Zyklen erkannt: {ddk['n_cycles'] if ddk['n_cycles'] >= 3 else '–'}")
            if ddk["n_cycles"] < 3:
                st.caption("Zu wenige erkannte Zyklen für eine belastbare Rate/Regelmäßigkeit.")
            else:
                st.caption(
                    "Höherer Variationskoeffizient (CV) = unregelmäßigere Zyklen — gilt in der "
                    "Literatur als möglicher Hinweis auf ataktische Dysarthrie, nicht nur die reine Rate."
                )
                st.pyplot(ddk_rhythm_figure(ddk.get("cycle_times", []), ddk.get("duration_s")), width="stretch")
                st.caption(
                    "Oben: Zeitpunkte der erkannten Silbenzyklen. Unten: Abstand zwischen "
                    "aufeinanderfolgenden Zyklen als Balken (orange = deutlich vom Mittelwert "
                    "abweichend) — macht „stolpernde“, unregelmäßige Silbenfolgen sichtbar, die "
                    "der CV-Zahl allein verloren gehen."
                )

            with st.expander("Alle Werte im Detail"):
                rows = build_rows(flat)
                if rows:
                    render_interpretation_table(rows)

            with st.expander("Glossar & Literatur"):
                glossary_entries = build_glossary_entries(flat)
                if glossary_entries:
                    render_glossary(glossary_entries)

            with st.expander(f"Alle {len(takes)} Versuche verwalten"):
                for i, t in enumerate(takes):
                    dcol1, dcol2, dcol3 = st.columns([2, 3, 1])
                    dcol1.write(f"Versuch {t['take_number']}" + (" · ausgewählt" if t.get("selected") else ""))
                    dcol2.caption(t["filename"])
                    if dcol3.button("Löschen", key=f"del_{task_key}_{i}", icon=":material/delete:"):
                        delete_take(MODULE, task_key, i)
                        st.rerun()

done = {k: v for k, v in st.session_state.get("module_results", {}).get(MODULE, {}).items() if v}
st.divider()
st.caption(
    f"**{len(done)} von {len(SUB_TASKS)} Teilaufgaben mit mind. einem Versuch** in dieser Sitzung. "
    "Letztes Modul im Guide — danach geht's weiter zum Gesamtbericht."
)
