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

from core.audio import articulation_features, ddk_rate_features, save_uploaded_wav
from core.interpretation import age_caveats_for, build_rows, flatten_take
from core.module_state import add_take, delete_take, get_takes, select_take
from core.plots import gauge_figure, intensity_figure, spectrogram_figure, waveform_figure

DERIVED_DIR = os.environ.get("NEUROVOICE_DERIVED_DIR", "/derived")
MODULE = "ddk"

SUB_TASKS = {
    "ddkgemischt": {
        "label": "DDK kombiniert (Pflicht)",
        "instruction": (
            "<b>Sprich so schnell und gleichmäßig wie möglich</b> „pa-ta-ka-pa-ta-ka...“ — "
            "für ca. <b>10 Sekunden</b>."
        ),
        "required": True,
    },
    "ddkeinzeln": {
        "label": "DDK einzeln (optional)",
        "instruction": (
            "<b>Sprich nacheinander</b>, jeweils ca. 5 Sekunden: erst „pa-pa-pa...“, dann "
            "„ta-ta-ta...“, dann „ka-ka-ka...“ — jeweils so schnell und gleichmäßig wie möglich."
        ),
        "required": False,
    },
}


def _fmt(value, decimals=1):
    return f"{value:.{decimals}f}" if value is not None else "–"


st.markdown(
    """
    <div class="dw-eyebrow">Modul 4 von 4 · Guide</div>
    <div class="dw-hero-title">🔁 Diadochokinese</div>
    <div class="dw-subtitle">Schnelle Silbenfolgen — motorisch anspruchsvollste Aufgabe der Batterie</div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs([meta["label"] for meta in SUB_TASKS.values()])

for (task_key, meta), tab in zip(SUB_TASKS.items(), tabs):
    with tab:
        st.markdown(f'<div class="dw-card-subtle">{meta["instruction"]}</div>', unsafe_allow_html=True)
        st.write("")

        takes = get_takes(MODULE, task_key)

        add_label = "Weiteren Versuch aufnehmen" if takes else "Aufnahme starten"
        source_mode = st.radio(
            "Quelle", ["Mikrofon aufnehmen", "Datei hochladen (WAV)"],
            key=f"source_{task_key}", horizontal=True,
        )
        if source_mode == "Mikrofon aufnehmen":
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

            with st.expander("Visualisierungen (Wellenform, Lautstärke, Spektrogramm)", expanded=True):
                sound = parselmouth.Sound(take["recording_path"])
                st.pyplot(waveform_figure(sound), width="stretch")
                st.pyplot(intensity_figure(sound), width="stretch")
                st.pyplot(spectrogram_figure(sound), width="stretch")

            ddk = take["ddk"]
            articulation = take["articulation"]

            g1, g2 = st.columns(2)
            with g1:
                st.pyplot(gauge_figure("DDK-Rate", ddk["ddk_rate_hz"], "Hz", 0, 8), width="stretch")
                st.caption("informativ, kein etablierter Normbereich")
            with g2:
                st.pyplot(
                    gauge_figure("Artikulationsschärfe", articulation["mean_burst_sharpness_db_s"], "dB/s", 100, 400),
                    width="stretch",
                )
                st.caption("experimentell, nur Eigenvergleich")

            mean_interval_ms = ddk["mean_cycle_interval_s"] * 1000 if ddk["mean_cycle_interval_s"] is not None else None
            c1, c2, c3 = st.columns(3)
            c1.metric("Zyklen erkannt", ddk["n_cycles"] if ddk["n_cycles"] >= 3 else "–")
            c2.metric("Regelmäßigkeit (CV)", _fmt(ddk["cycle_interval_cv"], 2))
            c3.metric("Ø Zyklus-Intervall", f"{_fmt(mean_interval_ms, 0)} ms")
            if ddk["n_cycles"] < 3:
                st.caption("Zu wenige erkannte Zyklen für eine belastbare Rate/Regelmäßigkeit.")
            else:
                st.caption(
                    "Höherer Variationskoeffizient (CV) = unregelmäßigere Zyklen — gilt in der "
                    "Literatur als möglicher Hinweis auf ataktische Dysarthrie, nicht nur die reine Rate."
                )

            st.markdown("**Was bedeuten diese Werte?**")
            flat = flatten_take(take)
            rows = build_rows(flat)
            if rows:
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
                for caveat in age_caveats_for(flat):
                    st.caption(f"⚠️ {caveat}")

            with st.expander(f"Alle {len(takes)} Versuche verwalten"):
                for i, t in enumerate(takes):
                    dcol1, dcol2, dcol3 = st.columns([2, 3, 1])
                    dcol1.write(f"Versuch {t['take_number']}" + (" ⭐ ausgewählt" if t.get("selected") else ""))
                    dcol2.caption(t["filename"])
                    if dcol3.button("🗑️ Löschen", key=f"del_{task_key}_{i}"):
                        delete_take(MODULE, task_key, i)
                        st.rerun()

done = {k: v for k, v in st.session_state.get("module_results", {}).get(MODULE, {}).items() if v}
st.divider()
st.caption(
    f"**{len(done)} von {len(SUB_TASKS)} Teilaufgaben mit mind. einem Versuch** in dieser Sitzung. "
    "Letztes Modul im Guide — danach geht's weiter zum Gesamtbericht."
)
