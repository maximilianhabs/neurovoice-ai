"""Modul 2 von 4: Vorlesen — Standardtext, siehe docs/backlog.md "Konzept: Modul-basierte,
gefuehrte Analyse", P3. Baut auf dem Vokalisation-Muster (views/vokalisation.py) auf, inkl.
Take-Management (core/module_state.py).

Reihenfolge einfach->schwer: nach Vokalisation, da Vorlesen zwar Artikulationskoordination
braucht, aber (anders als Spontansprache) keine eigene Sprachformulierung -- nur Reproduktion
eines vorgegebenen Textes.

Zwei Kennwert-Ebenen: (1) rein akustisch, sofort nach der Aufnahme verfuegbar (Artikulation,
Formant-Dynamik, Prosodie, CPP, MFCC); (2) transkript-basiert (Sprechrate, Pausen,
Lexikalische Diversitaet + der transkribierte Text selbst), braucht einen expliziten
Transkriptions-Schritt (WhisperX, dauert spuerbar auf diesem Server -- siehe
docs/bugtracker.md zur bekannten Blockier-Problematik waehrend der Transkription).
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
from core.interpretation import age_caveats_for, build_rows, flatten_take
from core.module_state import add_take, delete_take, get_takes, select_take
from core.plots import gauge_figure, intensity_figure, spectrogram_figure, waveform_figure
from core.reference_ranges import speech_rate_zones, verdict_for_value
from core.shared import transcribe_with_progress

DERIVED_DIR = os.environ.get("NEUROVOICE_DERIVED_DIR", "/derived")
MODULE = "vorlesen"
SUBTASK = "lesetext"
LESETEXT = (
    "Einst stritten sich Nordwind und Sonne, wer von ihnen beiden wohl der Stärkere "
    "wäre, als ein Wanderer, der in einen warmen Mantel gehüllt war, des Weges daherkam."
)
CONFIDENCE_WARN_THRESHOLD = 0.75


def _fmt(value, decimals=1):
    """Sicheres Formatieren -- siehe views/vokalisation.py fuer den Bugfix-Kontext (ein echter
    Test deckte auf, dass mehrere zusammengehoerige Werte UNABHAENGIG voneinander None sein
    koennen)."""
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
    <div class="dw-eyebrow">Modul 2 von 4 · Guide</div>
    <div class="dw-hero-title">📖 Vorlesen</div>
    <div class="dw-subtitle">Standardtext — Artikulationskoordination ohne eigene Sprachformulierung</div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="dw-card-subtle"><b>Lies den folgenden Satz laut und in normalem Tempo vor:</b>'
    f'<br><br>„{LESETEXT}"</div>',
    unsafe_allow_html=True,
)
st.write("")

takes = get_takes(MODULE, SUBTASK)

add_label = "Weiteren Versuch aufnehmen" if takes else "Aufnahme starten"
source_mode = st.radio("Quelle", ["Mikrofon aufnehmen", "Datei hochladen (WAV)"], horizontal=True)
if source_mode == "Mikrofon aufnehmen":
    uploaded = st.audio_input(add_label, sample_rate=48000, key=f"mic_lesetext_{len(takes)}")
    filename = "lesetext.wav"
else:
    uploaded = st.file_uploader("WAV-Datei (max. 25 MB)", type=["wav"], key=f"file_lesetext_{len(takes)}")
    filename = uploaded.name if uploaded is not None else None

if uploaded is not None:
    try:
        recording = save_uploaded_wav(DERIVED_DIR, filename, uploaded.getvalue(), task="lesetext")
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
    qc1, qc2, qc3 = st.columns(3)
    qc1.metric("Clipping", f"{_fmt(q['clipping_pct'], 1)} %")
    qc2.metric("Stille-Anteil", f"{_fmt(q['silence_pct'], 0)} %")
    qc3.metric("SNR (geschätzt)", f"{_fmt(q['snr_estimate_db'], 1)} dB")
    st.caption(
        "Aufnahmequalität — grobe Heuristik, noch nicht an echten Aufnahmen kalibriert. "
        "Rein informativ, kein automatisches Aussortieren."
    )

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
    g1, g2 = st.columns(2)
    with g1:
        st.pyplot(
            gauge_figure("Artikulationsschärfe", articulation["mean_burst_sharpness_db_s"], "dB/s", 100, 400),
            width="stretch",
        )
        st.caption("experimentell, nur Eigenvergleich")
    with g2:
        st.pyplot(gauge_figure("CPPS", cpp["cpps_db"], "dB", 0, 20), width="stretch")
        st.caption("informativ, parameterabhängig")

    c1, c2, c3 = st.columns(3)
    c1.metric("Monoloudness", f"{_fmt(prosody['monoloudness_intensity_sd_db'])} dB")
    c2.metric(
        "Formant-Streuung (F1/F2-IQR)",
        f"{_fmt(formant_dyn['f1_iqr_hz'], 0)}/{_fmt(formant_dyn['f2_iqr_hz'], 0)} Hz",
    )
    c3.metric("Intonationskontur", f"{intonation['n_phrases']} Phrasen" if intonation["n_phrases"] else "–")

    # --- Transkript-basierte Kennwerte + der transkribierte Text selbst ---
    st.divider()
    st.subheader("Transkription, Sprechrate & Pausen")

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
            st.caption("✅ Transkript aus dem Cache geladen.")
        elif st.button("🎧 Transkription starten (dauert je nach Hardware 1-2 Minuten — App reagiert währenddessen nicht, das ist normal)"):
            import soundfile as sf

            duration_s = sf.info(take["recording_path"]).duration
            transcript = transcribe_with_progress(take["recording_path"], duration_s)
            _save_transcript_cache(take["recording_path"], transcript)
            take["transcript"] = transcript
            st.rerun()

        if transcript:
            # --- Transkribierter Text mit Konfidenz-Hervorhebung (war im alten Testdaten-Modus
            # vorhanden, beim Modul-Umbau versehentlich weggelassen -- Nutzer-Feedback 2026-08-15) ---
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

            if speech_metrics["net_speech_rate_wpm"] is not None:
                lo, hi, zones = speech_rate_zones()
                value = speech_metrics["net_speech_rate_wpm"]
                sg1, sg2 = st.columns(2)
                with sg1:
                    st.pyplot(gauge_figure("Sprechrate", value, "WPM", lo, hi, zones), width="stretch")
                    _, verdict = verdict_for_value(value, lo, hi, zones)
                    st.caption(verdict)
                with sg2:
                    st.metric("Pausen (Anzahl)", speech_metrics["pause_count"])
                    st.metric(
                        "Lexikalische Diversität (TTR)",
                        f"{lexical['ttr']:.2f}" if lexical["ttr"] is not None else "–",
                    )

    st.divider()
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
            if dcol3.button("🗑️ Löschen", key=f"del_lesetext_{i}"):
                delete_take(MODULE, SUBTASK, i)
                st.rerun()

st.divider()
st.caption("Pflichtaufgabe des Moduls — du kannst jederzeit weiter zum nächsten Modul, ohne etwas zu verlieren.")
