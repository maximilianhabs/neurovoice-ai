"""NeuroVoice AI — Analyse-Dashboard. Lokale Streamlit-App, siehe docs/dashboard_konzept.md."""

import os

import pandas as pd
import parselmouth
import streamlit as st

from core.audio import basic_stats, list_patients, list_recordings, phonation_features
from core.plots import intensity_figure, spectrogram_figure, waveform_figure

DATA_DIR = os.environ.get("NEUROVOICE_DATA_DIR", "/data")

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

rows = [
    ("F0 Mittelwert", features["f0_mean_hz"], "Hz", "Mittlere Grundfrequenz (Tonhöhe)"),
    ("F0 Standardabweichung", features["f0_sd_hz"], "Hz", "Tonhöhen-Variabilität (\"Monopitch\"-Maß)"),
    ("Jitter (local)", features["jitter_local_pct"], "%", "Zyklus-zu-Zyklus-Schwankung der Grundfrequenz"),
    ("Shimmer (local)", features["shimmer_local_pct"], "%", "Zyklus-zu-Zyklus-Schwankung der Amplitude"),
    ("HNR (Mittelwert)", features["hnr_mean_db"], "dB", "Harmonics-to-Noise-Ratio (Stimmklangqualität)"),
]
df = pd.DataFrame(rows, columns=["Feature", "Wert", "Einheit", "Erklärung"])
df["Wert"] = df["Wert"].apply(lambda v: f"{v:.2f}" if v is not None else "–")
st.dataframe(df, use_container_width=True, hide_index=True)

st.caption(
    "Referenzwerte: Saarbrücken Voice Database (deutsch, 869 gesunde Sprecher:innen) — "
    "siehe docs/literatur_review.md. Weitere Feature-Stufen (Spektral/Prosodie/Artikulation) "
    "folgen laut docs/backlog.md."
)
