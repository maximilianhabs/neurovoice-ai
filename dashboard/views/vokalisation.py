"""Modul 1 von 4: Vokalisation — erstes vollstaendig gebautes Modul im neuen, gefuehrten
Guide (siehe docs/backlog.md "Konzept: Modul-basierte, gefuehrte Analyse", P2). Dient als
Vorlage fuer die restlichen 3 Module (Vorlesen/Spontansprache/DDK).

Reihenfolge einfach->schwer (literaturbasiert, siehe Konzept-Diskussion): Vokalisation zuerst,
da motorisch/kognitiv am wenigsten fordernd (keine Artikulationskoordination noetig).

Pflicht-Aufgabe: gehaltener Vokal /a/ (ASHA-Standard, auch Basis der Saarbruecker Voice
Database). /i/ und /u/ optional -- werden fuer eine echte Vokalraum-Flaeche (VSA,
core.audio.vowel_space_area(), P7/Audit 2026-08-15) genutzt, sobald alle 3 Eckvokale je einen
ausgewaehlten Versuch haben. MPT (Maximum Phonation Time) und eine explorative F0-Tremor-
Analyse (core.audio.mpt_features()/f0_tremor_features(), ebenfalls P7) werden je Take
automatisch mitberechnet.

Take-Management (P1, siehe core/module_state.py): mehrere Aufnahmen pro Teilaufgabe moeglich,
manuelle Auswahl des besten Versuchs, session-persistent -- Ergebnisse werden IMMER aus
st.session_state gerendert, nicht aus dem Widget-Rueckgabewert (siehe Bugfix-Kontext in
core/module_state.py).
"""

import os

import pandas as pd
import parselmouth
import streamlit as st

from core.audio import (
    cpp_features,
    f0_tremor_features,
    formant_features,
    mpt_features,
    phonation_dynamics_features,
    phonation_features,
    recording_quality_features,
    save_uploaded_wav,
    vowel_space_area,
)
from core.interpretation import build_glossary_entries, build_rows, build_tiles, flatten_take
from core.module_state import add_take, delete_take, get_takes, select_take, selected_take
from core.subject_store import require_subject_or_stop
from core.plots import intensity_figure, spectrogram_figure, vowel_space_figure, waveform_figure
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

require_subject_or_stop()
recording_start_blip()

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
    <div class="dw-hero-title">Vokalisation</div>
    <div class="dw-subtitle">Gehaltener Vokal — einfachste Aufgabe, keine Artikulationskoordination nötig</div>
    """,
    unsafe_allow_html=True,
)
st.info(
    "**Alle 3 Vokale empfohlen**: /i/ und /u/ sind optional, liefern aber robustere "
    "Mittelwerte UND ermöglichen erst die echte Vokalraum-Fläche (VSA) — am besten alle 3 "
    "nacheinander aufnehmen, nicht nur die Pflichtaufgabe /a/.",
    icon=":material/info:",
)

tabs = st.tabs([meta["label"] for meta in SUB_TASKS.values()])

for (task_key, meta), tab in zip(SUB_TASKS.items(), tabs):
    with tab:
        instr_col, scale_col = st.columns([4, 1])
        with instr_col:
            st.markdown(
                f'<div class="dw-card-subtle">'
                f'<span class="dw-instruction-meta">Halte den Vokal in gleichbleibender Tonhöhe '
                f'und Lautstärke für mindestens 2-3 Sekunden. Wenn möglich 3 Wiederholungen.</span>'
                f'<span class="dw-instruction-target">„{meta["vowel"]}“</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with scale_col:
            instruction_text_scale_control(key=task_key)
        st.write("")

        takes = get_takes(MODULE, task_key)

        # --- Neue Aufnahme hinzufuegen (immer moeglich, auch wenn schon Versuche existieren) ---
        add_label = "Weiteren Versuch aufnehmen" if takes else "Aufnahme starten"
        source_mode = st.radio(
            "Quelle", ["Mikrofon aufnehmen", "Datei hochladen (WAV)"],
            key=f"source_{task_key}", horizontal=True,
        )
        if source_mode == "Mikrofon aufnehmen":
            recording_duration_feedback_style(green_s=3, orange_s=5, red_s=10, key="vokal")
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
                mpt = mpt_features(recording.path)
                tremor = f0_tremor_features(recording.path)
                add_take(MODULE, task_key, {
                    "recording_path": recording.path,
                    "filename": recording.filename,
                    "audio_bytes": uploaded.getvalue(),
                    "phonation": phon,
                    "dynamics": dyn,
                    "cpp": cpp,
                    "formants": form,
                    "mpt": mpt,
                    "tremor": tremor,
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

            q = recording_quality_features(take["recording_path"])
            quality_tiles(q)

            with st.expander("Visualisierungen (Wellenform, Lautstärke, Spektrogramm)", expanded=True):
                sound = parselmouth.Sound(take["recording_path"])
                st.pyplot(waveform_figure(sound), width="stretch")
                st.pyplot(intensity_figure(sound), width="stretch")
                st.pyplot(spectrogram_figure(sound), width="stretch")
                st.caption(SPECTROGRAM_LEGEND_CAPTION)

            flat = flatten_take(take)

            tile_keys = ["jitter_local_pct", "shimmer_local_pct", "hnr_mean_db", "cpps_db"]
            tiles = build_tiles({k: flat[k] for k in tile_keys if k in flat})
            tile_cols = st.columns(len(tiles)) if tiles else []
            for col, tile in zip(tile_cols, tiles):
                with col:
                    kpi_tile(tile["label"], tile["value_text"], tile["sub_text"], tile["zone"], tile["description"], tile.get("range_text"))

            # Bucket H (docs/backlog.md, Nutzer-Feedback 2026-08-15): F0-Mittel/Voice-Breaks/
            # Formanten waren hier noch als rohe st.metric()-Zeile stehengeblieben, obwohl
            # Vorlesen/Spontansprache schon auf Kacheln umgestellt wurden.
            more_keys = ["f0_mean_hz", "voice_breaks_degree_pct", "f1_mean_hz", "f2_mean_hz", "f3_mean_hz"]
            more_tiles = build_tiles({k: flat[k] for k in more_keys if k in flat})
            more_rows = [more_tiles[i:i + 3] for i in range(0, len(more_tiles), 3)]
            for row in more_rows:
                cols = st.columns(3)
                for col, tile in zip(cols, row):
                    with col:
                        kpi_tile(tile["label"], tile["value_text"], tile["sub_text"], tile["zone"], tile["description"], tile.get("range_text"))

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

# --- Vokalraum-Fläche (VSA, P7/Audit) + Vokaltrapez-Plot (docs/konzept_visualisierungen.md,
# 3.1): VSA-Zahl braucht weiterhin alle 3 Eckvokale mit mind. einem Versuch, der Plot zeigt
# aber bereits ab 2 vorhandenen Vokalen etwas -- rechnet ueber die jeweils AUSGEWAEHLTEN
# besten Takes, deshalb erst hier am Modul-Ende, nicht innerhalb der einzelnen Tabs. ---
take_a = selected_take(MODULE, "vokal")
take_i = selected_take(MODULE, "vokali")
take_u = selected_take(MODULE, "vokalu")
vowel_points = {}
for key, take in (("a", take_a), ("i", take_i), ("u", take_u)):
    if take is not None:
        f = take.get("formants", {})
        vowel_points[key] = (f.get("f1_mean_hz"), f.get("f2_mean_hz"))

if len(vowel_points) >= 2:
    st.divider()
    st.markdown("**Vokalraum** — Formant-Positionen der aufgenommenen Eckvokale")
    plot_col, info_col = st.columns([3, 2])
    with plot_col:
        st.pyplot(vowel_space_figure(vowel_points), width="stretch")
    with info_col:
        st.caption(
            "Klassisches „Vokaltrapez“: F2 (vorne/hinten) waagerecht, F1 (offen/geschlossen) "
            "senkrecht, beide Achsen umgekehrt (Phonetik-Konvention). Ein kleines, "
            "zentrales Dreieck kann auf einen eingeschränkten Artikulationsraum hindeuten."
        )
        if take_a and take_i and take_u:
            vsa = vowel_space_area(
                take_a["formants"]["f1_mean_hz"], take_a["formants"]["f2_mean_hz"],
                take_i["formants"]["f1_mean_hz"], take_i["formants"]["f2_mean_hz"],
                take_u["formants"]["f1_mean_hz"], take_u["formants"]["f2_mean_hz"],
            )
            if vsa is not None:
                kpi_tile(
                    "Vokalraum-Fläche (VSA)", f"{vsa:,.0f} Hz²".replace(",", "."), "kein Normwert", "neutral",
                    "Fläche des Dreiecks aus F1/F2 der Eckvokale /a/,/i/,/u/ — kleinere Fläche kann auf Zentralisierung hindeuten.",
                )
        else:
            st.caption("Noch nicht alle 3 Eckvokale vorhanden — die Flächenzahl (VSA) erscheint erst dann.")

done = {k: v for k, v in st.session_state.get("module_results", {}).get(MODULE, {}).items() if v}
st.divider()
st.caption(
    f"**{len(done)} von {len(SUB_TASKS)} Teilaufgaben mit mind. einem Versuch** in dieser Sitzung. "
    "Alles optional außer /a/ — du kannst jederzeit weiter zum nächsten Modul, ohne etwas zu verlieren."
)
