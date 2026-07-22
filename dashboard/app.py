"""NeuroVoice AI — Analyse-Dashboard. Lokale Streamlit-App, siehe docs/dashboard_konzept.md."""

import json
import os

import pandas as pd
import parselmouth
import streamlit as st

from core.audio import (
    articulation_features,
    basic_stats,
    formant_features,
    list_patients,
    list_recordings,
    phonation_features,
    prosody_features,
)
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

# --- Prosodie (Stufe 4 aus docs/backlog.md) ---
st.subheader("Prosodie")

prosody = prosody_features(recording.path)

prosody_rows = [
    ("Monopitch (F0-SD)", features["f0_sd_hz"], "Hz", "= F0-Standardabweichung oben — niedrige Werte können auf eine eintönige Sprechweise hindeuten"),
    ("Monoloudness (Intensitäts-SD)", prosody["monoloudness_intensity_sd_db"], "dB", "Lautstärke-Variabilität — niedrige Werte können auf eine gleichbleibende, wenig modulierte Lautstärke hindeuten"),
]
prosody_df = pd.DataFrame(prosody_rows, columns=["Feature", "Wert", "Einheit", "Erklärung"])
prosody_df["Wert"] = prosody_df["Wert"].apply(lambda v: f"{v:.2f}" if v is not None else "–")
st.dataframe(prosody_df, use_container_width=True, hide_index=True)

st.caption(
    "Rhythmus (nPVI) erscheint weiter unten im Transkriptions-Bereich, da er die "
    "Wort-Zeitstempel aus der Transkription braucht. Referenzwerte für Monopitch/Monoloudness "
    "sind noch nicht hinterlegt (siehe docs/backlog.md, offene Frage zu Normwerten)."
)

# --- Artikulationssauberkeit (Stufe 5 aus docs/backlog.md) ---
st.subheader("Artikulationssauberkeit")

st.info(
    "ℹ️ Erkennt akustisch **Verschluss-Löse-Muster** (kurzer Energieeinbruch + scharfer "
    "Wiederanstieg), wie sie bei Plosiven (p/b, t/d, k/g) typisch sind — **keine phonetische "
    "Erkennung einzelner Laute**. Ziel ist eine grobe Gradmesser-Kennzahl für "
    "Artikulationspräzision (weniger/unschärfere/längere Verschlüsse können auf eingeschränkte "
    "Zungen-/Lippenbeweglichkeit hindeuten), nicht die Identifikation, welcher Laut gemeint war."
)

articulation = articulation_features(recording.path)

art_rows = [
    ("Anzahl erkannter Verschluss-Ereignisse", articulation["n_stop_events"], "", "Grobes Maß für artikulatorische Aktivität"),
    ("Ø Verschlussdauer", articulation["mean_closure_duration_s"] * 1000 if articulation["mean_closure_duration_s"] else None, "ms", "Deutsch: Lenis ~5-20ms, Fortis ~40-60ms (Literatur) — längere Werte können auf unscharfe Artikulation hindeuten"),
    ("Ø Burst-Schärfe", articulation["mean_burst_sharpness_db_s"], "dB/s", "Wie schnell der Pegel nach dem Verschluss wieder ansteigt — schwächere Werte = weniger scharfe Löseartikulation"),
]
art_df = pd.DataFrame(art_rows, columns=["Feature", "Wert", "Einheit", "Erklärung"])
art_df["Wert"] = art_df["Wert"].apply(lambda v: f"{v:.1f}" if v is not None else "–")
st.dataframe(art_df, use_container_width=True, hide_index=True)

st.caption(
    "Noch keine Referenzwerte aus dysarthrischen Aufnahmen vorhanden — aktuell nur an "
    "gesunden Testaufnahmen kalibriert (siehe docs/backlog.md). Werte über mehrere Takes "
    "derselben Person/desselben Texts sind gut vergleichbar (Baseline), sagen aber noch "
    "nichts über pathologische Abweichungen aus."
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
        CONFIDENCE_WARN_THRESHOLD = 0.75
        words_html = []
        for w in transcript["words"]:
            score = w.get("score")
            if score is not None and score < CONFIDENCE_WARN_THRESHOLD:
                words_html.append(
                    f'<span style="background:#fde68a;border-bottom:2px solid #d97706;'
                    f'padding:0 2px;border-radius:2px;" '
                    f'title="Konfidenz {score:.2f} — unsicher erkannt, ggf. Wort prüfen">{w["word"]}</span>'
                )
            else:
                words_html.append(w["word"])
        transcript_html = " ".join(words_html)

        st.markdown(
            f"""
            <div style="background:#fffbea;border-left:5px solid #3182ce;border-radius:8px;
                        padding:1rem 1.3rem;margin:0.4rem 0 0.6rem;">
              <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;
                          color:#3182ce;font-weight:700;margin-bottom:0.5rem;">
                🤖 KI-Transkription (WhisperX, Modell large-v3)
              </div>
              <div style="font-size:1.3rem;line-height:1.7;color:#1a202c;">
                {transcript_html}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            "⚠️ Automatisch erkannt, keine manuelle Korrektur — einzelne Wörter können falsch "
            "erfasst sein. Gelb unterstrichene Wörter haben eine Erkennungs-Konfidenz unter 75% "
            "(Maus drüberhalten zeigt den genauen Wert) — hier lohnt sich ein Abgleich mit dem Audio."
        )

        from core.speech_metrics import compute_speech_metrics

        metrics = compute_speech_metrics(transcript["words"], total_duration_s=stats["duration_s"])
        scores = [w["score"] for w in transcript["words"] if w.get("score") is not None]
        mean_confidence = sum(scores) / len(scores) if scores else None
        low_confidence_count = sum(1 for s in scores if s < CONFIDENCE_WARN_THRESHOLD)

        c1, c2 = st.columns(2)
        c1.metric("Ø Erkennungs-Konfidenz", f"{mean_confidence:.0%}" if mean_confidence is not None else "–")
        c2.metric("Unsichere Wörter (<75%)", low_confidence_count)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Wörter", metrics["n_words"])
        m2.metric("Sprechrate (Netto)", f"{metrics['net_speech_rate_wpm']:.0f} Wörter/min" if metrics["net_speech_rate_wpm"] else "–")
        m3.metric("Sprechrate (Artikulation)", f"{metrics['articulation_rate_wpm']:.0f} Wörter/min" if metrics["articulation_rate_wpm"] else "–")
        m4.metric("Flüssigkeits-Score", f"{metrics['fluency_score']:.2f}" if metrics["fluency_score"] is not None else "–")

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Pausen (≥250ms)", metrics["pause_count"])
        p2.metric("Ø Pausendauer", f"{metrics['mean_pause_duration_s']:.2f} s" if metrics["mean_pause_duration_s"] else "–")
        p3.metric("Max. Pausendauer", f"{metrics['max_pause_duration_s']:.2f} s" if metrics["max_pause_duration_s"] else "–")
        p4.metric("Rhythmus (nPVI)", f"{metrics['rhythm_npvi']:.1f}" if metrics["rhythm_npvi"] is not None else "–")

        with st.expander("Wort-Zeitstempel (Detailtabelle)"):
            words_df = pd.DataFrame(transcript["words"])
            st.dataframe(words_df, use_container_width=True, hide_index=True)

        st.caption(
            "Sprechrate/Pausen basieren auf Wort-Zeitstempeln aus der Transkription (WhisperX), "
            "nicht auf reiner akustischer Stille-Erkennung — präziser, da bekannt ist, WAS "
            "zwischen den Pausen gesprochen wurde. Details: docs/backlog.md, Stufe 3 / Chunk 3. "
            "Rhythmus (nPVI, Stufe 4): normalisierter Pairwise Variability Index über die "
            "Wortdauern — hohe Werte = stark wechselnde Wortdauern (\"lebendiger\" Rhythmus), "
            "niedrige Werte = gleichförmiger/eintöniger. Näherung auf Wortebene, da keine "
            "Silbensegmentierung vorliegt."
        )
