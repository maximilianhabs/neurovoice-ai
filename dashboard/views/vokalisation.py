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

Take-Management (P1, siehe core/module_state.py): mehrere Aufnahmen pro Teilaufgabe moeglich,
manuelle Auswahl des besten Versuchs, session-persistent -- Ergebnisse werden IMMER aus
st.session_state gerendert, nicht aus dem Widget-Rueckgabewert (siehe Bugfix-Kontext in
core/module_state.py).
"""

import os

import streamlit as st

from core.audio import cpp_features, formant_features, phonation_dynamics_features, phonation_features, save_uploaded_wav
from core.module_state import add_take, delete_take, get_takes, select_take
from core.plots import gauge_figure
from core.reference_ranges import hnr_zones, jitter_zones, shimmer_zones, verdict_for_value

DERIVED_DIR = os.environ.get("NEUROVOICE_DERIVED_DIR", "/derived")
MODULE = "vokalisation"


def _fmt(value, decimals=1):
    """Sicheres Formatieren -- Bugfix 2026-08-15: mehrere Werte (z.B. voice_breaks_degree_pct,
    einzelne Formanten) koennen UNABHAENGIG voneinander None sein, auch wenn ein verwandter
    Wert vorhanden ist. Ein rohes f"{...:.1f}" auf einem davon crasht dann mit
    TypeError, wie ein echter Test hier aufgedeckt hat -- IMMER ueber diesen Helper formatieren,
    nie direkt."""
    return f"{value:.{decimals}f}" if value is not None else "–"

SUB_TASKS = {
    "vokal": {"label": "Vokal /a/ (Pflicht)", "vowel": "AAAAA", "required": True},
    "vokali": {"label": "Vokal /i/ (optional)", "vowel": "IIIII", "required": False},
    "vokalu": {"label": "Vokal /u/ (optional)", "vowel": "UUUUU", "required": False},
}

st.markdown(
    """
    <div class="dw-eyebrow">Modul 1 von 4 · Guide</div>
    <div class="dw-hero-title">🗣️ Vokalisation</div>
    <div class="dw-subtitle">Gehaltener Vokal — einfachste Aufgabe, keine Artikulationskoordination nötig</div>
    """,
    unsafe_allow_html=True,
)

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

        takes = get_takes(MODULE, task_key)

        # --- Neue Aufnahme hinzufuegen (immer moeglich, auch wenn schon Versuche existieren) ---
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
                phon = phonation_features(recording.path)
                dyn = phonation_dynamics_features(recording.path)
                cpp = cpp_features(recording.path)
                form = formant_features(recording.path)
                add_take(MODULE, task_key, {
                    "recording_path": recording.path,
                    "filename": recording.filename,
                    "audio_bytes": uploaded.getvalue(),
                    "phonation": phon,
                    "dynamics": dyn,
                    "cpp": cpp,
                    "formants": form,
                })
                st.success(f"Aufgenommen: {recording.filename}")
                st.rerun()  # Widget-Key aendert sich (len(takes)+1) -> sauberer neuer leerer Recorder

        # --- Alle bisherigen Versuche IMMER aus session_state rendern (Bugfix 2026-08-15:
        # nicht vom aktuellen Widget-Wert abhaengig machen, sonst "verschwinden" Ergebnisse
        # beim Zurueck-Navigieren, obwohl Datei+Analyse noch da sind). ---
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

            phon, dyn, cpp, form = take["phonation"], take["dynamics"], take["cpp"], take["formants"]

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
            c1.metric("F0 (Mittel)", f"{_fmt(phon['f0_mean_hz'], 0)} Hz")
            c2.metric(
                "Voice Breaks",
                f"{dyn['voice_breaks_count'] if dyn['voice_breaks_count'] is not None else '–'} · "
                f"{_fmt(dyn['voice_breaks_degree_pct'], 1)}%",
            )
            c3.metric(
                "Formanten F1/F2/F3",
                f"{_fmt(form['f1_mean_hz'], 0)}/{_fmt(form['f2_mean_hz'], 0)}/{_fmt(form['f3_mean_hz'], 0)} Hz",
            )

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
    "Alles optional außer /a/ — du kannst jederzeit weiter zum nächsten Modul, ohne etwas zu verlieren."
)
