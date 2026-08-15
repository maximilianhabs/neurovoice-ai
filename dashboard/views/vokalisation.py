"""Modul 1 von 4: Vokalisation — erstes vollstaendig gebautes Modul im neuen, gefuehrten
Guide (siehe docs/backlog.md "Konzept: Modul-basierte, gefuehrte Analyse", P2). Dient als
Vorlage fuer die restlichen 3 Module (Vorlesen/Spontansprache/DDK).

Reihenfolge einfach->schwer (literaturbasiert, siehe Konzept-Diskussion): Vokalisation zuerst,
da motorisch/kognitiv am wenigsten fordernd (keine Artikulationskoordination noetig).

Pflicht-Aufgabe: gehaltener Vokal /a/ (ASHA-Standard, auch Basis der Saarbruecker Voice
Database). /i/ und /u/ optional (fuer eine spaetere Vokalraum-Flaeche, noch nicht berechnet --
siehe docs/backlog.md, echte VSA-Formel ist P7, hier noch nicht umgesetzt). MPT (Maximum
Phonation Time) ebenfalls optional, noch nicht als eigene Kennzahl berechnet (P1 im externen
Audit, folgt spaeter).

Take-Management (Mehrfachversuche, Vergleichsansicht, manuelle Auswahl des besten Versuchs)
ist bewusst NOCH NICHT Teil dieses Moduls -- das ist P1 im Umsetzungsplan, ein eigener,
spaeterer Schritt. Hier: eine Aufnahme pro Teilaufgabe, erneutes Aufnehmen ueberschreibt die
vorherige (kein Datenverlust auf Platte, nur die Anzeige zeigt den letzten Stand).
"""

import os

import streamlit as st

from core.audio import cpp_features, formant_features, phonation_dynamics_features, phonation_features, save_uploaded_wav
from core.plots import gauge_figure
from core.reference_ranges import hnr_zones, jitter_zones, shimmer_zones, verdict_for_value

DERIVED_DIR = os.environ.get("NEUROVOICE_DERIVED_DIR", "/derived")

SUB_TASKS = {
    "vokal": {
        "label": "Vokal /a/ (Pflicht)",
        "vowel": "AAAAA",
        "required": True,
    },
    "vokali": {
        "label": "Vokal /i/ (optional)",
        "vowel": "IIIII",
        "required": False,
    },
    "vokalu": {
        "label": "Vokal /u/ (optional)",
        "vowel": "UUUUU",
        "required": False,
    },
}

st.markdown(
    """
    <div class="dw-eyebrow">Modul 1 von 4 · Guide</div>
    <div class="dw-hero-title">🗣️ Vokalisation</div>
    <div class="dw-subtitle">Gehaltener Vokal — einfachste Aufgabe, keine Artikulationskoordination nötig</div>
    """,
    unsafe_allow_html=True,
)

if "module_results" not in st.session_state:
    st.session_state["module_results"] = {}
st.session_state["module_results"].setdefault("vokalisation", {})

tabs = st.tabs([meta["label"] for meta in SUB_TASKS.values()])

for (task_key, meta), tab in zip(SUB_TASKS.items(), tabs):
    with tab:
        st.markdown(
            f'<div class="dw-card-subtle">'
            f'<b>Halte den Vokal „{meta["vowel"]}“</b> in gleichbleibender Tonhöhe und Lautstärke '
            f'für <b>mindestens 2-3 Sekunden</b>. Wenn möglich 3 Wiederholungen.'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.write("")

        source_mode = st.radio(
            "Quelle", ["Mikrofon aufnehmen", "Datei hochladen (WAV)"],
            key=f"source_{task_key}", horizontal=True,
        )
        if source_mode == "Mikrofon aufnehmen":
            uploaded = st.audio_input("Aufnahme starten", sample_rate=48000, key=f"mic_{task_key}")
            filename = f"{task_key}.wav"
        else:
            uploaded = st.file_uploader("WAV-Datei (max. 25 MB)", type=["wav"], key=f"file_{task_key}")
            filename = uploaded.name if uploaded is not None else None

        if uploaded is not None:
            try:
                recording = save_uploaded_wav(DERIVED_DIR, filename, uploaded.getvalue(), task=task_key)
            except ValueError as exc:
                st.error(str(exc))
                recording = None
            if recording is not None:
                st.success(f"Aufgenommen: {recording.filename}")
                st.audio(uploaded.getvalue(), format="audio/wav")

                phon = phonation_features(recording.path)
                dyn = phonation_dynamics_features(recording.path)
                cpp = cpp_features(recording.path)
                form = formant_features(recording.path)

                st.session_state["module_results"]["vokalisation"][task_key] = {
                    "recording_path": recording.path,
                    "phonation": phon,
                    "dynamics": dyn,
                    "cpp": cpp,
                    "formants": form,
                }

                # Ampel-Gauges statt nackter Zahlen (Nutzer-Feedback 2026-08-15) -- nutzt
                # dieselben Referenzbereiche/Farben wie der Testdaten-Modus (core/plots.py,
                # core/reference_ranges.py), damit beide Ansichten konsistent bleiben.
                g1, g2, g3, g4 = st.columns(4)
                with g1:
                    lo, hi, zones = jitter_zones()
                    value = phon["jitter_local_pct"]
                    st.pyplot(gauge_figure("Jitter (local)", value, "%", lo, hi, zones), width="stretch")
                    if value is not None:
                        _, verdict = verdict_for_value(value, lo, hi, zones)
                        st.caption(verdict)
                with g2:
                    lo, hi, zones = shimmer_zones()
                    value = phon["shimmer_local_pct"]
                    st.pyplot(gauge_figure("Shimmer (local)", value, "%", lo, hi, zones), width="stretch")
                    if value is not None:
                        _, verdict = verdict_for_value(value, lo, hi, zones)
                        st.caption(verdict)
                with g3:
                    lo, hi, zones = hnr_zones()
                    value = phon["hnr_mean_db"]
                    st.pyplot(gauge_figure("HNR", value, "dB", lo, hi, zones), width="stretch")
                    if value is not None:
                        _, verdict = verdict_for_value(value, lo, hi, zones)
                        st.caption(verdict)
                with g4:
                    st.pyplot(gauge_figure("CPPS", cpp["cpps_db"], "dB", 0, 20), width="stretch")
                    st.caption("informativ, parameterabhängig")

                c1, c2, c3 = st.columns(3)
                c1.metric("F0 (Mittel)", f"{phon['f0_mean_hz']:.0f} Hz" if phon["f0_mean_hz"] else "–")
                c2.metric(
                    "Voice Breaks",
                    f"{dyn['voice_breaks_count']} · {dyn['voice_breaks_degree_pct']:.1f}%"
                    if dyn["voice_breaks_count"] is not None else "–",
                )
                c3.metric(
                    "Formanten F1/F2/F3",
                    f"{form['f1_mean_hz']:.0f}/{form['f2_mean_hz']:.0f}/{form['f3_mean_hz']:.0f} Hz"
                    if form["f1_mean_hz"] else "–",
                )
        elif task_key in st.session_state["module_results"]["vokalisation"]:
            st.caption("✅ Bereits aufgenommen (siehe Zusammenfassung unten). Erneut aufnehmen, um zu ersetzen.")
        elif meta["required"]:
            st.info("Diese Aufgabe ist die Pflichtaufgabe des Moduls.")
        else:
            st.caption("Optional — kann übersprungen werden.")

done = st.session_state["module_results"]["vokalisation"]
st.divider()
st.caption(
    f"**{len(done)} von {len(SUB_TASKS)} Teilaufgaben erledigt** in dieser Sitzung "
    f"({', '.join(SUB_TASKS[k]['label'] for k in done)} falls vorhanden). "
    "Alles optional außer /a/ — du kannst jederzeit weiter zum nächsten Modul."
)
