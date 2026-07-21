"""NeuroVoice AI — Analyse-Dashboard. Lokale Streamlit-App, siehe docs/dashboard_konzept.md."""

import json
import os

import pandas as pd
import parselmouth
import streamlit as st

from core.audio import basic_stats, formant_features, list_patients, list_recordings, phonation_features
from core.plots import intensity_figure, spectrogram_figure, waveform_figure

DATA_DIR = os.environ.get("NEUROVOICE_DATA_DIR", "/data")
# Getrennt von DATA_DIR (das read-only bleibt) -- hier landen abgeleitete Ergebnisse wie
# Transkripte, damit sie NICHT bei jedem Aufruf neu berechnet werden muessen. Rohdaten
# bleiben unangetastet, siehe README.md "Repo-Struktur" / Projektprinzip "Original nie ueberschreiben".
DERIVED_DIR = os.environ.get("NEUROVOICE_DERIVED_DIR", "/derived")


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

st.set_page_config(page_title="NeuroVoice AI — Analyse-Dashboard", layout="wide", page_icon="🎙️")
st.title("🎙️ NeuroVoice AI — Analyse-Dashboard")

# --- Sidebar: Datei auswählen ---
patients = list_patients(DATA_DIR)
if not patients:
    st.warning(f"Keine Aufnahmen gefunden unter `{DATA_DIR}`.")
    st.stop()

patient_id = st.sidebar.selectbox("Patient/Proband", patients)
recordings = list_recordings(DATA_DIR, patient_id)
if not recordings:
    st.warning(f"Keine Aufnahmen für `{patient_id}` gefunden.")
    st.stop()

labels = [f"{r.date} · {r.task} · Take {r.take}" for r in recordings]
selected_idx = st.sidebar.selectbox("Aufnahme", range(len(recordings)), format_func=lambda i: labels[i])
recording = recordings[selected_idx]

st.sidebar.markdown(f"**Datei:** `{recording.filename}`")
st.sidebar.markdown(f"**Task-Typ:** `{recording.task}`")

# --- Player ---
with open(recording.path, "rb") as f:
    audio_bytes = f.read()
st.audio(audio_bytes, format="audio/wav")

# --- Grundkennwerte ---
stats = basic_stats(recording.path)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Dauer", f"{stats['duration_s']:.2f} s")
col2.metric("Samplerate", f"{stats['sample_rate']} Hz")
col3.metric("Bittiefe", f"{stats['bit_depth']} bit")
col4.metric("Kanäle", stats["channels"])
col5.metric("Peak-Lautstärke", f"{stats['peak_dbfs']:.1f} dBFS")

# --- Visualisierungen ---
sound = parselmouth.Sound(recording.path)

st.subheader("Wellenform")
st.pyplot(waveform_figure(sound), use_container_width=True)

st.subheader("Spektrogramm mit Tonhöhenverlauf (F0)")
st.pyplot(spectrogram_figure(sound), use_container_width=True)

st.subheader("Lautstärkeverlauf")
st.pyplot(intensity_figure(sound), use_container_width=True)

# --- Feature-Tabelle (Phonation, Stufe 1 aus docs/backlog.md) ---
st.subheader("Phonation-Features")

if recording.task != "vokal":
    st.info(
        "⚠️ Jitter/Shimmer sind laut Literaturrecherche (docs/literatur_review.md) nur bei "
        "**gehaltenem Vokal** zuverlässig — diese Aufnahme ist Task-Typ "
        f"**„{recording.task}“**, die Werte unten sind entsprechend nur eingeschränkt aussagekräftig."
    )

features = phonation_features(recording.path)
formants = formant_features(recording.path)

rows = [
    ("F0 Mittelwert", features["f0_mean_hz"], "Hz", "Mittlere Grundfrequenz (Tonhöhe)"),
    ("F0 Standardabweichung", features["f0_sd_hz"], "Hz", "Tonhöhen-Variabilität (\"Monopitch\"-Maß)"),
    ("Jitter (local)", features["jitter_local_pct"], "%", "Zyklus-zu-Zyklus-Schwankung der Grundfrequenz"),
    ("Shimmer (local)", features["shimmer_local_pct"], "%", "Zyklus-zu-Zyklus-Schwankung der Amplitude"),
    ("HNR (Mittelwert)", features["hnr_mean_db"], "dB", "Harmonics-to-Noise-Ratio (Stimmklangqualität)"),
    ("F1 Mittelwert", formants["f1_mean_hz"], "Hz", "1. Formant — korreliert mit Zungenhöhe (offen/geschlossen)"),
    ("F2 Mittelwert", formants["f2_mean_hz"], "Hz", "2. Formant — korreliert mit Zungenposition (vorne/hinten)"),
    ("F3 Mittelwert", formants["f3_mean_hz"], "Hz", "3. Formant — Klangfarbe/Artikulationsschärfe"),
]
df = pd.DataFrame(rows, columns=["Feature", "Wert", "Einheit", "Erklärung"])
df["Wert"] = df["Wert"].apply(lambda v: f"{v:.2f}" if v is not None else "–")
st.dataframe(df, use_container_width=True, hide_index=True)

st.caption(
    "Referenzwerte: Saarbrücken Voice Database (deutsch, 869 gesunde Sprecher:innen) — "
    "siehe docs/literatur_review.md. Formanten sind Mittelwerte über die gesamte Aufnahme, "
    "noch keine Vokalraum-Fläche (dafür braucht es mehrere unterschiedliche Vokale in einer "
    "Aufnahme, siehe docs/backlog.md). Weitere Feature-Stufen (Prosodie/Artikulationssauberkeit) "
    "folgen laut docs/backlog.md."
)

# --- Transkription + Sprechfluss (Chunk 3/4 aus docs/backlog.md) ---
st.subheader("Transkription & Sprechfluss")

try:
    import core.transcription  # noqa: F401  -- nur um ImportError frueh + eindeutig zu fangen

    transcription_available = True
except ImportError:
    transcription_available = False

if not transcription_available:
    st.info(
        "Transkription ist auf diesem Server noch nicht installiert (WhisperX/torch fehlen — "
        "siehe docs/backlog.md, Chunk 5). Läuft aktuell nur in der lokalen Testumgebung."
    )
else:
    cached_transcript = _load_cached_transcript(recording)

    if cached_transcript is not None:
        transcript = cached_transcript
        st.caption("✅ Transkript aus dem Cache geladen (bereits einmal berechnet, kein erneutes Warten nötig).")
        if st.button("🔁 Neu transkribieren (überschreibt den Cache)"):
            from core.transcription import transcribe

            with st.spinner("Transkribiere lokal … kann je nach Hardware 1-2 Minuten dauern"):
                transcript = transcribe(recording.path)
            _save_transcript_cache(recording, transcript)
    else:
        transcript = None
        if st.button("🎧 Transkription starten (dauert bei large-v3 spürbar lange, das ist normal — läuft danach nur noch einmal pro Datei)"):
            from core.transcription import transcribe

            with st.spinner("Transkribiere lokal … kann je nach Hardware 1-2 Minuten dauern"):
                transcript = transcribe(recording.path)
            _save_transcript_cache(recording, transcript)

    if transcript:
        st.markdown(f"**Text:** {transcript['text']}")

        from core.speech_metrics import compute_speech_metrics

        metrics = compute_speech_metrics(transcript["words"], total_duration_s=stats["duration_s"])

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Wörter", metrics["n_words"])
        m2.metric("Sprechrate (Netto)", f"{metrics['net_speech_rate_wpm']:.0f} Wörter/min" if metrics["net_speech_rate_wpm"] else "–")
        m3.metric("Sprechrate (Artikulation)", f"{metrics['articulation_rate_wpm']:.0f} Wörter/min" if metrics["articulation_rate_wpm"] else "–")
        m4.metric("Flüssigkeits-Score", f"{metrics['fluency_score']:.2f}" if metrics["fluency_score"] is not None else "–")

        p1, p2, p3 = st.columns(3)
        p1.metric("Pausen (≥250ms)", metrics["pause_count"])
        p2.metric("Ø Pausendauer", f"{metrics['mean_pause_duration_s']:.2f} s" if metrics["mean_pause_duration_s"] else "–")
        p3.metric("Max. Pausendauer", f"{metrics['max_pause_duration_s']:.2f} s" if metrics["max_pause_duration_s"] else "–")

        with st.expander("Wort-Zeitstempel (Detailtabelle)"):
            words_df = pd.DataFrame(transcript["words"])
            st.dataframe(words_df, use_container_width=True, hide_index=True)

        st.caption(
            "Sprechrate/Pausen basieren auf Wort-Zeitstempeln aus der Transkription (WhisperX), "
            "nicht auf reiner akustischer Stille-Erkennung — präziser, da bekannt ist, WAS "
            "zwischen den Pausen gesprochen wurde. Details: docs/backlog.md, Stufe 3 / Chunk 3."
        )
