"""Modul 3 von 4: Spontansprache — freies Erzählen, siehe docs/backlog.md "Konzept:
Modul-basierte, geführte Analyse", P3. Baut auf dem Vorlesen-Muster (views/vorlesen.py) auf,
inkl. Take-Management (core/module_state.py).

Reihenfolge einfach->schwer: nach Vorlesen, da Spontansprache zusätzlich zur
Artikulationskoordination noch eigene Sprachformulierung braucht (Wortfindung,
Satzplanung) -- anders als beim Vorlesen keine Textvorlage.

Zielwert ~30s (nicht 60s wie urspruenglich diskutiert -- Nutzer-Entscheidung 2026-08-15: zu
lang). Gestufter Prompt statt einer einzelnen offenen Frage, damit auch wortkarge Personen ins
Reden kommen.

Gleiche zwei Kennwert-Ebenen wie Vorlesen: (1) akustisch sofort verfuegbar, (2)
transkript-basiert inkl. Lexikalischer Diversitaet (TTR/MTLD) -- hier besonders relevant, da
MTLD erst bei laengeren Texten wirklich aussagekraeftig wird (siehe docs/backlog.md).
"""

import json
import os

import pandas as pd
import parselmouth
import streamlit as st

from core.audio import (
    articulation_features,
    cpp_features,
    formant_dynamics_features,
    intonation_contour_features,
    prosody_features,
    recording_quality_features,
    save_uploaded_wav,
)
from core.interpretation import build_glossary_entries, build_rows, build_tiles, flatten_take
from core.module_state import add_take, delete_take, get_takes, select_take
from core.plots import intensity_figure, radar_figure, spectrogram_figure, waveform_figure
from core.reference_ranges import speech_rate_zones
from core.shared import (
    SPECTROGRAM_LEGEND_CAPTION,
    instruction_text_scale_control,
    kpi_tile,
    quality_tiles,
    recording_duration_feedback_style,
    render_glossary,
    render_interpretation_table,
    transcribe_with_progress,
)
from core.subject_store import require_subject_or_stop

require_subject_or_stop()

DERIVED_DIR = os.environ.get("NEUROVOICE_DERIVED_DIR", "/derived")
MODULE = "spontansprache"
SUBTASK = "spontan"
CONFIDENCE_WARN_THRESHOLD = 0.75


def _fmt(value, decimals=1):
    return f"{value:.{decimals}f}" if value is not None else "–"


def _transcript_cache_path(recording_path: str) -> str:
    return os.path.splitext(recording_path)[0] + ".transcript.json"


def _load_cached_transcript(recording_path: str) -> dict | None:
    cache_path = _transcript_cache_path(recording_path)
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_transcript_cache(recording_path: str, transcript: dict) -> None:
    with open(_transcript_cache_path(recording_path), "w", encoding="utf-8") as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)


st.markdown(
    """
    <div class="dw-eyebrow">Modul 3 von 4 · Guide</div>
    <div class="dw-hero-title">Spontansprache</div>
    <div class="dw-subtitle">Freies Erzählen — Artikulation + eigene Sprachformulierung</div>
    """,
    unsafe_allow_html=True,
)

instr_col, scale_col = st.columns([4, 1])
with instr_col:
    st.markdown(
        '<div class="dw-card-subtle"><b>Erzähle frei von deinem letzten Urlaub oder einem '
        'Hobby</b>, ca. <b>30 Sekunden</b>.<br><br>'
        'Falls dir nichts einfällt: Welches Hobby hast du? Seit wann? Was gefällt dir daran?</div>',
        unsafe_allow_html=True,
    )
with scale_col:
    instruction_text_scale_control(key="spontan")
st.write("")

takes = get_takes(MODULE, SUBTASK)

add_label = "Weiteren Versuch aufnehmen" if takes else "Aufnahme starten"
source_mode = st.radio("Quelle", ["Mikrofon aufnehmen", "Datei hochladen (WAV)"], horizontal=True)
if source_mode == "Mikrofon aufnehmen":
    recording_duration_feedback_style(green_s=35, orange_s=45, red_s=60, key="spontan")
    uploaded = st.audio_input(add_label, sample_rate=48000, key=f"mic_spontan_{len(takes)}")
    filename = "spontan.wav"
else:
    uploaded = st.file_uploader("WAV-Datei (max. 25 MB)", type=["wav"], key=f"file_spontan_{len(takes)}")
    filename = uploaded.name if uploaded is not None else None

if uploaded is not None:
    try:
        recording = save_uploaded_wav(DERIVED_DIR, filename, uploaded.getvalue(), task="spontan")
    except ValueError as exc:
        st.error(str(exc))
        recording = None
    if recording is not None:
        add_take(MODULE, SUBTASK, {
            "recording_path": recording.path,
            "filename": recording.filename,
            "audio_bytes": uploaded.getvalue(),
            "articulation": articulation_features(recording.path),
            "formant_dynamics": formant_dynamics_features(recording.path),
            "prosody": prosody_features(recording.path),
            "cpp": cpp_features(recording.path),
            "intonation": intonation_contour_features(recording.path),
        })
        st.success(f"Aufgenommen: {recording.filename}")
        st.rerun()

if not takes:
    st.info("Diese Aufgabe ist die Pflichtaufgabe des Moduls.")
else:
    st.divider()
    st.markdown(f"**{len(takes)} Versuch(e) aufgenommen** — bester Versuch fließt in den Gesamtbericht ein.")

    take_labels = [f"Versuch {t['take_number']}" for t in takes]
    selected_idx = next((i for i, t in enumerate(takes) if t.get("selected")), 0)
    chosen_idx = st.radio(
        "Bester Versuch", range(len(takes)), format_func=lambda i: take_labels[i],
        index=selected_idx, horizontal=True,
    )
    if chosen_idx != selected_idx:
        select_take(MODULE, SUBTASK, chosen_idx)
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

    st.subheader("Ergebnisse")
    flat = flatten_take(take)
    tile_keys = [
        "mean_burst_sharpness_db_s", "cpps_db", "monoloudness_intensity_sd_db",
        "f1_iqr_hz", "f2_iqr_hz", "n_phrases",
    ]
    tiles = build_tiles({k: flat[k] for k in tile_keys if k in flat})
    tile_rows = [tiles[i:i + 3] for i in range(0, len(tiles), 3)]
    for row in tile_rows:
        cols = st.columns(3)
        for col, tile in zip(cols, row):
            with col:
                kpi_tile(tile["label"], tile["value_text"], tile["sub_text"], tile["zone"], tile["description"])

    # --- Transkript-basierte Kennwerte + der transkribierte Text selbst ---
    st.divider()
    st.subheader("Transkription, Sprechrate, Pausen & Lexik")

    try:
        import core.transcription  # noqa: F401

        transcription_available = True
    except ImportError:
        transcription_available = False

    if not transcription_available:
        st.info("Transkription (WhisperX) ist auf diesem Server nicht installiert.")
    else:
        cached_transcript = _load_cached_transcript(take["recording_path"])
        transcript = cached_transcript
        if transcript is not None:
            st.caption("Transkript aus dem Cache geladen.")
        elif st.button(
            "Transkription starten (dauert je nach Hardware 1-2 Minuten — App reagiert "
            "währenddessen nicht, das ist normal)",
            icon=":material/graphic_eq:",
        ):
            import soundfile as sf

            duration_s = sf.info(take["recording_path"]).duration
            transcript = transcribe_with_progress(take["recording_path"], duration_s)
            _save_transcript_cache(take["recording_path"], transcript)
            take["transcript"] = transcript
            st.rerun()

        if transcript:
            words_html = []
            for w in transcript["words"]:
                score = w.get("score")
                if score is not None and score < CONFIDENCE_WARN_THRESHOLD:
                    words_html.append(
                        f'<span style="background:#fde68a;border-bottom:2px solid #d97706;'
                        f'padding:0 2px;border-radius:2px;" '
                        f'title="Konfidenz {score:.2f} — unsicher erkannt">{w["word"]}</span>'
                    )
                else:
                    words_html.append(w["word"])
            st.markdown(
                f'<div class="dw-card"><div style="font-size:1.2rem;line-height:1.7;">'
                f'{" ".join(words_html)}</div></div>',
                unsafe_allow_html=True,
            )
            st.caption("Gelb unterstrichene Wörter: Erkennungs-Konfidenz unter 75%.")

            from core.linguistics import lexical_diversity_features
            from core.speech_metrics import compute_speech_metrics
            import soundfile as sf

            duration_s = sf.info(take["recording_path"]).duration
            speech_metrics = compute_speech_metrics(transcript["words"], total_duration_s=duration_s)
            lexical = lexical_diversity_features(transcript["words"])
            take["speech_metrics"] = speech_metrics
            take["lexical"] = lexical

            # --- Erkennungs-Konfidenz (war im alten Testdaten-Modus vorhanden, beim
            # Modul-Umbau versehentlich weggelassen -- Nutzer-Feedback 2026-08-15) ---
            scores = [w["score"] for w in transcript["words"] if w.get("score") is not None]
            mean_confidence = sum(scores) / len(scores) if scores else None
            low_confidence_count = sum(1 for s in scores if s < CONFIDENCE_WARN_THRESHOLD)

            kc1, kc2 = st.columns(2)
            kc1.metric("Ø Erkennungs-Konfidenz", f"{mean_confidence:.0%}" if mean_confidence is not None else "–")
            kc2.metric("Unsichere Wörter (<75%)", low_confidence_count)

            def _tile_group(title: str, keys: list[str], source: dict) -> None:
                group_tiles = build_tiles({k: source[k] for k in keys if k in source})
                if not group_tiles:
                    return
                st.markdown(f"**{title}**")
                rows = [group_tiles[i:i + 3] for i in range(0, len(group_tiles), 3)]
                for row in rows:
                    cols = st.columns(3)
                    for col, t in zip(cols, row):
                        with col:
                            kpi_tile(t["label"], t["value_text"], t["sub_text"], t["zone"], t["description"])

            _tile_group(
                "Sprechrate", ["n_words", "net_speech_rate_wpm", "articulation_rate_wpm",
                               "fluency_score", "mean_word_duration_s"],
                speech_metrics,
            )
            _tile_group(
                "Pausen", ["pause_count", "mean_pause_duration_s", "max_pause_duration_s",
                           "rhythm_npvi", "micro_pause_count", "mean_micro_pause_duration_s",
                           "macro_pause_count", "mean_macro_pause_duration_s"],
                speech_metrics,
            )
            _tile_group("Lexik", ["ttr", "mtld"], lexical)

            with st.expander("Profil auf einen Blick (Radar)"):
                lo, hi, _ = speech_rate_zones()
                radar_axes, radar_values = [], []
                if speech_metrics["net_speech_rate_wpm"] is not None:
                    radar_axes.append("Sprechrate")
                    radar_values.append(max(0.0, min(1.0, (speech_metrics["net_speech_rate_wpm"] - lo) / (hi - lo))))
                if speech_metrics["fluency_score"] is not None:
                    radar_axes.append("Flüssigkeit")
                    radar_values.append(max(0.0, min(1.0, speech_metrics["fluency_score"])))
                if speech_metrics["rhythm_npvi"] is not None:
                    radar_axes.append("Rhythmus")
                    radar_values.append(max(0.0, min(1.0, speech_metrics["rhythm_npvi"] / 100)))
                if lexical["ttr"] is not None:
                    radar_axes.append("Lexik. Diversität")
                    radar_values.append(max(0.0, min(1.0, lexical["ttr"])))
                if len(radar_axes) >= 3:
                    st.pyplot(radar_figure(radar_axes, radar_values), width="content")
                    st.caption(
                        "Zusätzliche, rein visuelle Verdichtung der Werte oben (normalisiert 0–1) "
                        "— ersetzt nicht die genauen Zahlen/Status in den Kacheln, nur eine "
                        "zusätzliche Muster-Wahrnehmung auf einen Blick. Keine Diagnose."
                    )
                else:
                    st.caption("Noch zu wenige Werte für ein aussagekräftiges Profil.")

            with st.expander("Wort-Zeitstempel (Detailtabelle)"):
                words_df = pd.DataFrame(transcript["words"])
                if {"start", "end"}.issubset(words_df.columns):
                    words_df["duration_s"] = words_df["end"] - words_df["start"]
                st.dataframe(words_df, width="stretch", hide_index=True)

            st.caption(
                f"{speech_metrics['n_words']} Wörter erkannt — MTLD ist erst ab deutlich "
                "längeren Texten wirklich robust, bei ~30s-Snippets nur eingeschränkt "
                "aussagekräftig. Mikro-/Makropausen (Schwelle 500ms): Mikropausen eher "
                "normale Atem-/Wortgrenzen, Makropausen eher auffällige Zögerungen."
            )

    st.divider()
    flat = flatten_take(take)
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
            if dcol3.button("Löschen", key=f"del_spontan_{i}", icon=":material/delete:"):
                delete_take(MODULE, SUBTASK, i)
                st.rerun()

st.divider()
st.caption("Pflichtaufgabe des Moduls — du kannst jederzeit weiter zum nächsten Modul, ohne etwas zu verlieren.")
