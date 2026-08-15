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
from core.interpretation import age_caveats_for, build_rows, build_tiles, flatten_take
from core.module_state import add_take, delete_take, get_takes, select_take
from core.plots import intensity_figure, spectrogram_figure, waveform_figure
from core.shared import kpi_tile, quality_tiles, transcribe_with_progress

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

st.markdown(
    '<div class="dw-card-subtle"><b>Erzähle frei von deinem letzten Urlaub oder einem '
    'Hobby</b>, ca. <b>30 Sekunden</b>.<br><br>'
    'Falls dir nichts einfällt: Welches Hobby hast du? Seit wann? Was gefällt dir daran?</div>',
    unsafe_allow_html=True,
)
st.write("")

takes = get_takes(MODULE, SUBTASK)

add_label = "Weiteren Versuch aufnehmen" if takes else "Aufnahme starten"
source_mode = st.radio("Quelle", ["Mikrofon aufnehmen", "Datei hochladen (WAV)"], horizontal=True)
if source_mode == "Mikrofon aufnehmen":
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

    articulation = take["articulation"]
    formant_dyn = take["formant_dynamics"]
    prosody = take["prosody"]
    cpp = take["cpp"]
    intonation = take["intonation"]

    st.subheader("Ergebnisse")
    flat = flatten_take(take)
    tile_keys = ["mean_burst_sharpness_db_s", "cpps_db"]
    tiles = build_tiles({k: flat[k] for k in tile_keys if k in flat})
    tile_cols = st.columns(len(tiles)) if tiles else []
    for col, tile in zip(tile_cols, tiles):
        with col:
            kpi_tile(tile["label"], tile["value_text"], tile["sub_text"], tile["zone"], tile["description"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Monoloudness", f"{_fmt(prosody['monoloudness_intensity_sd_db'])} dB")
    c2.metric(
        "Formant-Streuung (F1/F2-IQR)",
        f"{_fmt(formant_dyn['f1_iqr_hz'], 0)}/{_fmt(formant_dyn['f2_iqr_hz'], 0)} Hz",
    )
    c3.metric("Intonationskontur", f"{intonation['n_phrases']} Phrasen" if intonation["n_phrases"] else "–")

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

            if speech_metrics["net_speech_rate_wpm"] is not None:
                rate_tiles = build_tiles({"net_speech_rate_wpm": speech_metrics["net_speech_rate_wpm"]})
                rt_col, _, _ = st.columns(3)
                with rt_col:
                    t = rate_tiles[0]
                    kpi_tile(t["label"], t["value_text"], t["sub_text"], t["zone"], t["description"])

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Wörter", speech_metrics["n_words"])
            m2.metric("Sprechrate (Netto)", f"{_fmt(speech_metrics['net_speech_rate_wpm'], 0)} Wörter/min")
            m3.metric("Sprechrate (Artikulation)", f"{_fmt(speech_metrics['articulation_rate_wpm'], 0)} Wörter/min")
            m4.metric("Flüssigkeits-Score", f"{_fmt(speech_metrics['fluency_score'], 2)}")

            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Pausen (≥250ms)", speech_metrics["pause_count"])
            p2.metric("Ø Pausendauer", f"{_fmt(speech_metrics['mean_pause_duration_s'], 2)} s")
            p3.metric("Max. Pausendauer", f"{_fmt(speech_metrics['max_pause_duration_s'], 2)} s")
            p4.metric("Rhythmus (nPVI)", f"{_fmt(speech_metrics['rhythm_npvi'], 1)}")

            q1, q2, q3 = st.columns(3)
            q1.metric(
                "Mikropausen (250-500ms)",
                f"{speech_metrics['micro_pause_count']} · Ø {_fmt(speech_metrics['mean_micro_pause_duration_s'], 2)}s",
            )
            q2.metric(
                "Makropausen (≥500ms)",
                f"{speech_metrics['macro_pause_count']} · Ø {_fmt(speech_metrics['mean_macro_pause_duration_s'], 2)}s",
            )
            q3.metric(
                "Lexikalische Diversität (TTR / MTLD)",
                f"{_fmt(lexical['ttr'], 2)} / {_fmt(lexical['mtld'], 1)}",
            )

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
    with st.expander("Alle Werte im Detail"):
        flat = flatten_take(take)
        rows = build_rows(flat)
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            for caveat in age_caveats_for(flat):
                st.caption(caveat, help="Alters-/Geschlechts-Hinweis")

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
