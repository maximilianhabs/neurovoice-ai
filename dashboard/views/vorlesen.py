"""Modul 2 von 4: Vorlesen — Standardtext, siehe docs/backlog.md "Konzept: Modul-basierte,
gefuehrte Analyse", P3. Baut auf dem Vokalisation-Muster (views/vokalisation.py) auf.

Reihenfolge einfach->schwer: nach Vokalisation, da Vorlesen zwar Artikulationskoordination
braucht, aber (anders als Spontansprache) keine eigene Sprachformulierung -- nur Reproduktion
eines vorgegebenen Textes.

Zwei Kennwert-Ebenen: (1) rein akustisch, sofort nach der Aufnahme verfuegbar (Artikulation,
Formant-Dynamik, Prosodie, CPP, MFCC); (2) transkript-basiert (Sprechrate, Pausen,
Lexikalische Diversitaet), braucht einen expliziten Transkriptions-Schritt (WhisperX,
dauert spuerbar, deshalb ein eigener Button statt automatisch bei jeder Aufnahme).

Take-Management (P1) bewusst noch nicht enthalten, wie bei Vokalisation.
"""

import json
import os

import streamlit as st

from core.audio import (
    articulation_features,
    cpp_features,
    formant_dynamics_features,
    intonation_contour_features,
    prosody_features,
    save_uploaded_wav,
)
from core.plots import gauge_figure
from core.reference_ranges import speech_rate_zones, verdict_for_value

DERIVED_DIR = os.environ.get("NEUROVOICE_DERIVED_DIR", "/derived")
LESETEXT = (
    "Einst stritten sich Nordwind und Sonne, wer von ihnen beiden wohl der Stärkere "
    "wäre, als ein Wanderer, der in einen warmen Mantel gehüllt war, des Weges daherkam."
)


def _transcript_cache_path(recording) -> str:
    patient_dir = os.path.join(DERIVED_DIR, recording.patient_id)
    os.makedirs(patient_dir, exist_ok=True)
    base = os.path.splitext(recording.filename)[0]
    return os.path.join(patient_dir, f"{base}.transcript.json")


def _load_cached_transcript(recording) -> dict | None:
    cache_path = _transcript_cache_path(recording)
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_transcript_cache(recording, transcript: dict) -> None:
    with open(_transcript_cache_path(recording), "w", encoding="utf-8") as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)


st.markdown(
    """
    <div class="dw-eyebrow">Modul 2 von 4 · Guide</div>
    <div class="dw-hero-title">📖 Vorlesen</div>
    <div class="dw-subtitle">Standardtext — Artikulationskoordination ohne eigene Sprachformulierung</div>
    """,
    unsafe_allow_html=True,
)

if "module_results" not in st.session_state:
    st.session_state["module_results"] = {}
st.session_state["module_results"].setdefault("vorlesen", {})

st.markdown(
    f'<div class="dw-card-subtle"><b>Lies den folgenden Satz laut und in normalem Tempo vor:</b>'
    f'<br><br>„{LESETEXT}"</div>',
    unsafe_allow_html=True,
)
st.write("")

source_mode = st.radio("Quelle", ["Mikrofon aufnehmen", "Datei hochladen (WAV)"], horizontal=True)
if source_mode == "Mikrofon aufnehmen":
    uploaded = st.audio_input("Aufnahme starten", sample_rate=48000)
    filename = "lesetext.wav"
else:
    uploaded = st.file_uploader("WAV-Datei (max. 25 MB)", type=["wav"])
    filename = uploaded.name if uploaded is not None else None

recording = None
if uploaded is not None:
    try:
        recording = save_uploaded_wav(DERIVED_DIR, filename, uploaded.getvalue(), task="lesetext")
    except ValueError as exc:
        st.error(str(exc))
    if recording is not None:
        st.success(f"Aufgenommen: {recording.filename}")
        st.audio(uploaded.getvalue(), format="audio/wav")
elif "vorlesen" in st.session_state["module_results"] and st.session_state["module_results"]["vorlesen"]:
    st.caption("✅ Bereits aufgenommen (siehe unten). Erneut aufnehmen, um zu ersetzen.")
else:
    st.info("Diese Aufgabe ist die Pflichtaufgabe des Moduls.")

if recording is not None:
    # --- Akustische Kennwerte: sofort verfuegbar, kein Transkript noetig ---
    articulation = articulation_features(recording.path)
    formant_dyn = formant_dynamics_features(recording.path)
    prosody = prosody_features(recording.path)
    cpp = cpp_features(recording.path)
    intonation = intonation_contour_features(recording.path)

    st.session_state["module_results"]["vorlesen"] = {
        "recording_path": recording.path,
        "articulation": articulation,
        "formant_dynamics": formant_dyn,
        "prosody": prosody,
        "cpp": cpp,
        "intonation": intonation,
    }

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
    c1.metric("Monoloudness", f"{prosody['monoloudness_intensity_sd_db']:.1f} dB" if prosody["monoloudness_intensity_sd_db"] else "–")
    c2.metric(
        "Formant-Streuung (F1/F2-IQR)",
        f"{formant_dyn['f1_iqr_hz']:.0f}/{formant_dyn['f2_iqr_hz']:.0f} Hz" if formant_dyn["f1_iqr_hz"] else "–",
    )
    c3.metric(
        "Intonationskontur",
        f"{intonation['n_phrases']} Phrasen" if intonation["n_phrases"] else "–",
    )

    # --- Transkript-basierte Kennwerte (Sprechrate/Pausen/Lexik) -- eigener Schritt ---
    st.divider()
    st.subheader("Sprechrate & Pausen (braucht Transkription)")
    cached_transcript = _load_cached_transcript(recording)

    try:
        import core.transcription  # noqa: F401

        transcription_available = True
    except ImportError:
        transcription_available = False

    if not transcription_available:
        st.info("Transkription (WhisperX) ist auf diesem Server nicht installiert.")
    else:
        transcript = cached_transcript
        if transcript is not None:
            st.caption("✅ Transkript aus dem Cache geladen.")
        elif st.button("🎧 Transkription starten (kann 1-2 Minuten dauern)"):
            from core.transcription import transcribe

            with st.spinner("Transkribiere lokal …"):
                transcript = transcribe(recording.path)
            _save_transcript_cache(recording, transcript)

        if transcript:
            from core.linguistics import lexical_diversity_features
            from core.speech_metrics import compute_speech_metrics

            import soundfile as sf

            duration_s = sf.info(recording.path).duration
            speech_metrics = compute_speech_metrics(transcript["words"], total_duration_s=duration_s)
            lexical = lexical_diversity_features(transcript["words"])

            st.session_state["module_results"]["vorlesen"]["speech_metrics"] = speech_metrics
            st.session_state["module_results"]["vorlesen"]["lexical"] = lexical

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
st.caption("Pflichtaufgabe des Moduls — du kannst jederzeit weiter zum nächsten Modul.")
