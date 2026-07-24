"""NeuroVoice AI — Analyse-Dashboard. Lokale Streamlit-App, siehe docs/dashboard_konzept.md."""

import json
import os

import pandas as pd
import parselmouth
import streamlit as st

from core.audio import (
    articulation_features,
    basic_stats,
    cpp_features,
    formant_dynamics_features,
    formant_features,
    intonation_contour_features,
    list_patients,
    list_recordings,
    mfcc_features,
    phonation_dynamics_features,
    phonation_features,
    prosody_features,
)
from core.plots import gauge_figure, intensity_figure, radar_figure, spectrogram_figure, waveform_figure
from core.reference_ranges import FIT_LABELS, hnr_zones, speech_rate_zones, verdict_for_value

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


def _fmt(value, decimals=2):
    return f"{value:.{decimals}f}" if value is not None else "–"


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

# --- 1. Visualisierungen (zuerst, siehe Normwert-Konzept 2026-07-21) ---
sound = parselmouth.Sound(recording.path)

st.subheader("Wellenform")
st.pyplot(waveform_figure(sound), width='stretch')

st.subheader("Spektrogramm mit Tonhöhenverlauf (F0) + Formant-Tracks")
st.pyplot(spectrogram_figure(sound), width='stretch')

st.subheader("Lautstärkeverlauf")
st.pyplot(intensity_figure(sound), width='stretch')

# --- Alle Kennwerte einmal berechnen (Basis für Gauges, Tabelle und Glossar-Kontext) ---
features = phonation_features(recording.path)
formants = formant_features(recording.path)
cpp = cpp_features(recording.path)
prosody = prosody_features(recording.path)
articulation = articulation_features(recording.path)
dynamics = phonation_dynamics_features(recording.path)
formant_dynamics = formant_dynamics_features(recording.path)
mfcc = mfcc_features(recording.path)
intonation = intonation_contour_features(recording.path)
cached_transcript = _load_cached_transcript(recording)
speech_metrics = None
lexical = None
if cached_transcript is not None:
    from core.speech_metrics import compute_speech_metrics
    from core.linguistics import lexical_diversity_features

    speech_metrics = compute_speech_metrics(cached_transcript["words"], total_duration_s=stats["duration_s"])
    lexical = lexical_diversity_features(cached_transcript["words"])

# --- 2. Werte auf einen Blick (Konzept 2026-07-21: hierarchisch nach Auswertbarkeit beim Lesetext) ---
st.subheader("Werte auf einen Blick")
st.caption(
    "Sortiert nach Auswertbarkeit beim Lesetext — unserem hauptsächlichen Aufnahme-Typ —, "
    "nicht nur nach Literatur-Robustheit: Werte, die aus jeder Aufnahme berechenbar sind, "
    "stehen groß und vorne. Werte, die einen gehaltenen Vokal brauchen, stehen klein und "
    "zurückhaltend weiter unten, auch wenn sie in der Literatur gut belegt sind."
)

st.markdown("**Immer auswertbar**")
g1, g2, g3, g4, g5 = st.columns(5)

with g1:
    if speech_metrics and speech_metrics["net_speech_rate_wpm"] is not None:
        lo, hi, zones = speech_rate_zones()
        value = speech_metrics["net_speech_rate_wpm"]
        st.pyplot(gauge_figure("Sprechrate", value, "WPM", lo, hi, zones), width='stretch')
        _, verdict = verdict_for_value(value, lo, hi, zones)
        st.caption(verdict)
    else:
        st.pyplot(
            gauge_figure("Sprechrate", na=True, na_reason="Noch nicht transkribiert — siehe unten"),
            width='stretch',
        )

with g2:
    lo, hi, zones = hnr_zones()
    value = features["hnr_mean_db"]
    st.pyplot(gauge_figure("HNR", value, "dB", lo, hi, zones), width='stretch')
    _, verdict = verdict_for_value(value, lo, hi, zones) if value is not None else (None, "–")
    st.caption(f"{verdict} · eingeschränkt bei Fließsprache")

with g3:
    st.pyplot(gauge_figure("Monopitch (F0-SD)", features["f0_sd_hz"], "Hz", 0, 80), width='stretch')
    st.caption("informativ, kein fester Normwert")

with g4:
    st.pyplot(
        gauge_figure("Artikulationsschärfe", articulation["mean_burst_sharpness_db_s"], "dB/s", 100, 400),
        width='stretch',
    )
    st.caption("experimentell, nur Eigenvergleich")

with g5:
    st.pyplot(gauge_figure("CPPS", cpp["cpps_db"], "dB", 0, 20), width='stretch')
    st.caption("informativ, parameterabhängig")

# --- Radar-Profil ---
radar_axes, radar_values = [], []
if speech_metrics and speech_metrics["net_speech_rate_wpm"] is not None:
    lo, hi, _ = speech_rate_zones()
    radar_axes.append("Sprechrate")
    radar_values.append(max(0.0, min(1.0, (speech_metrics["net_speech_rate_wpm"] - lo) / (hi - lo))))
lo, hi, _ = hnr_zones()
radar_axes.append("HNR")
radar_values.append(max(0.0, min(1.0, ((features["hnr_mean_db"] or 0) - lo) / (hi - lo))))
radar_axes.append("Monopitch")
radar_values.append(max(0.0, min(1.0, (features["f0_sd_hz"] or 0) / 80)))
radar_axes.append("Artikulation")
radar_values.append(max(0.0, min(1.0, (articulation["mean_burst_sharpness_db_s"] or 0) / 400)))

if len(radar_axes) >= 3:
    rc1, rc2 = st.columns([1, 1.4])
    with rc1:
        st.pyplot(radar_figure(radar_axes, radar_values), width='stretch')
    with rc2:
        st.markdown("**Profil auf einen Blick**")
        st.caption(
            "Ausgefülltes, symmetrisches Vieleck nahe außen = unauffällig in allen vier "
            "Dimensionen. Keine Diagnose, nur Orientierung — Achsen sind normalisiert (0-1), "
            "nicht direkt mit den Rohwerten oben vergleichbar."
        )

st.markdown("**Braucht gehaltenen Vokal** — bei Lesetext meist nicht auswertbar")
s1, s2, s3 = st.columns(3)
with s1:
    st.pyplot(
        gauge_figure("Jitter (local)", na=True, na_reason="Nur bei gehaltenem Vokal zuverlässig"),
        width='stretch',
    )
with s2:
    st.pyplot(
        gauge_figure("Shimmer (local)", na=True, na_reason="Nur bei gehaltenem Vokal zuverlässig"),
        width='stretch',
    )
with s3:
    st.pyplot(
        gauge_figure("Vokalraum-Fläche", na=True, na_reason="Braucht mehrere Vokale pro Aufnahme, noch nicht möglich"),
        width='stretch',
    )

if recording.task != "vokal":
    st.info(
        "⚠️ Diese Aufnahme ist Task-Typ "
        f"**„{recording.task}“** (kein gehaltener Vokal) — Jitter/Shimmer/VSA sind deshalb "
        "oben bewusst als „nicht auswertbar“ markiert, statt eine irreführende Ampel zu zeigen."
    )

# --- 3. Tabellarische Übersicht ---
st.subheader("Tabellarische Übersicht")
st.caption("Alle Parameter dieser Aufnahme mit Erklärung und Referenzwert.")

table_rows = [
    ("Sprechrate (netto)",
     f"{_fmt(speech_metrics['net_speech_rate_wpm'], 0)} WPM" if speech_metrics else "noch nicht transkribiert",
     "Wörter pro Minute, bezogen auf die Gesamtdauer", "IReST Deutsch ø179 WPM (Vorlesen)", "immer"),
    ("HNR", f"{_fmt(features['hnr_mean_db'])} dB",
     "Verhältnis harmonischer Stimmklang zu Rauschanteil",
     ">20 klar · 15–20 grenzwertig · <15 auffällig", "eingeschraenkt"),
    ("F0 Mittelwert", f"{_fmt(features['f0_mean_hz'])} Hz", "Mittlere Tonhöhe der Stimme",
     "geschlechtsabhängig (~85–155Hz M, ~165–255Hz W)", "immer"),
    ("Monopitch (F0-SD)", f"{_fmt(features['f0_sd_hz'])} Hz", "Tonhöhen-Variabilität über die Aufnahme",
     "kein fester Normwert — Richtung: niedrig = auffällig bei PD", "immer"),
    ("F0 5./95. Perzentil",
     f"{_fmt(dynamics['f0_p5_hz'], 0)}–{_fmt(dynamics['f0_p95_hz'], 0)} Hz",
     "Streuung der Tonhöhe, robuster gegen Ausreißer als reine SD",
     "kein fester Normwert hinterlegt", "immer"),
    ("Pitch Slope",
     f"{_fmt(dynamics['pitch_slope_hz_per_s'], 2)} Hz/s",
     "Linearer Trend der Tonhöhe über die Zeit — möglicher Fatigue-Marker bei längeren Aufnahmen",
     "kein Normwert; bei kurzen ~10s-Snippets eher verrauscht", "immer"),
    ("Voice Breaks",
     f"{dynamics['voice_breaks_count']} · {_fmt(dynamics['voice_breaks_degree_pct'], 1)}%"
     if dynamics["voice_breaks_count"] is not None else "–",
     "Anzahl/Anteil unterbrochener Stimmgebung (Praat-Standardmaß)",
     "nur bei gehaltenem Vokal aussagekräftig — bei Lesetext durch normale Wortpausen/"
     "stimmlose Konsonanten erwartbar hoch, keine Auffälligkeit", "vokal"),
    ("Monoloudness", f"{_fmt(prosody['monoloudness_intensity_sd_db'])} dB",
     "Lautstärke-Variabilität über die Aufnahme", "kein fester Normwert hinterlegt", "immer"),
    ("Rhythmus (nPVI)", f"{_fmt(speech_metrics['rhythm_npvi'], 1)}" if speech_metrics else "noch nicht transkribiert",
     "Variabilität aufeinanderfolgender Wortdauern", "kein klinischer Normwert (eher sprachtypologisch)", "immer"),
    ("Prosodische Entropie",
     f"{_fmt(speech_metrics['prosodic_entropy_bits'], 2)} bit" if speech_metrics else "noch nicht transkribiert",
     "Vorhersehbarkeit des Sprechrhythmus (0=monoton, max. 3 bit=sehr unvorhersehbar) — "
     "ergänzt nPVI um die Gesamtverteilung statt nur Wortpaare",
     "kein Normwert, nur Eigenvergleich über Takes", "immer"),
    ("Pausen (Anzahl)", str(speech_metrics["pause_count"]) if speech_metrics else "noch nicht transkribiert",
     "Anzahl Sprechpausen ≥250ms", "kein Normwert, textlängenabhängig", "immer"),
    ("Lexikalische Diversität (TTR / MTLD)",
     f"{_fmt(lexical['ttr'], 2)} / {_fmt(lexical['mtld'], 1)}" if lexical and lexical["ttr"] is not None else "–",
     "Wie viele unterschiedliche Wörter im Verhältnis zur Textlänge benutzt werden — MTLD "
     "ist textlängen-robuster als die reine Type-Token-Ratio",
     "kein Normwert; MTLD wurde für deutlich längere Texte entwickelt, bei ~10s-Snippets "
     "nur eingeschränkt aussagekräftig", "immer"),
    ("Intonationskontur",
     f"{intonation['n_phrases']} Phrasen · {_fmt(intonation['pct_falling'], 0)}% fallend · "
     f"{_fmt(intonation['pct_rising'], 0)}% steigend" if intonation["n_phrases"] else "–",
     "Tonhöhen-Trend pro Sprechphrase (rein akustisch segmentiert, kein Transkript nötig) — "
     "erster einfacher Wurf: nur linearer Trend, keine Kurvenform",
     "kein Normwert, kleine Fallzahl pro Aufnahme (nur 2-4 Phrasen)", "immer"),
    ("Flüssigkeits-Score", _fmt(speech_metrics["fluency_score"]) if speech_metrics else "noch nicht transkribiert",
     "Anteil der Sprechspanne ohne auffällige Pausen", "eigene Heuristik, kein Normwert", "immer"),
    ("Artikulationsschärfe",
     f"{articulation['n_stop_events']} Ereign. · {_fmt(articulation['mean_burst_sharpness_db_s'], 0)} dB/s",
     "Klarheit/Anzahl erkannter Verschlusslaute", "eigene Heuristik, nur Eigenvergleich über Takes", "immer"),
    ("Voice Onset Time (VOT)",
     f"{_fmt(articulation['mean_vot_s'] * 1000, 1) if articulation['mean_vot_s'] else '–'} ms "
     f"({articulation['vot_count']} Ereign.)",
     "Zeit von Verschlusslösung bis Stimmbandeinsatz — Zusatzmaß zur Verschlussdauer",
     "im Deutschen meist kurz/unaspiriert, kein etablierter Cutoff für Praat-Messung", "immer"),
    ("Formanten F1–F3",
     f"{_fmt(formants['f1_mean_hz'], 0)} · {_fmt(formants['f2_mean_hz'], 0)} · {_fmt(formants['f3_mean_hz'], 0)} Hz",
     "Vokaltrakt-Resonanzen (Zungenposition)", "kein Normwert ohne bekannte Vokal-Identität", "immer"),
    ("Formant-Streuung (F1/F2-IQR)",
     f"{_fmt(formant_dynamics['f1_iqr_hz'], 0)} · {_fmt(formant_dynamics['f2_iqr_hz'], 0)} Hz",
     "Proxy für genutzten Vokalraum (kein Ersatz für echte Vokalraum-Fläche) — schmale Streuung "
     "kann auf Zentralisierung hindeuten", "kein Normwert, nur Eigenvergleich über Takes", "immer"),
    ("Formant-Geschwindigkeit (F1)",
     f"{_fmt(formant_dynamics['f1_velocity_mean_hz_s'], 0)} Hz/s",
     "Wie schnell sich F1 im zeitlichen Mittel ändert — Näherung für Zungen-/Kieferbeweglichkeit",
     "kein Normwert, nur Eigenvergleich über Takes", "immer"),
    ("CPPS", f"{_fmt(cpp['cpps_db'])} dB", "Alternatives Stimmklang-Maß, robuster bei Fließsprache",
     "parameterabhängig, kein fixer Cutoff hinterlegt", "immer"),
    ("MFCC 1-4 (Mittelwerte)",
     f"{_fmt(mfcc['mfcc_1_mean'], 0)} · {_fmt(mfcc['mfcc_2_mean'], 0)} · "
     f"{_fmt(mfcc['mfcc_3_mean'], 0)} · {_fmt(mfcc['mfcc_4_mean'], 0)}",
     "Allgemeine Klangfarbe (Mel-Frequency Cepstral Coefficients) — ⚠️ empfindlich gegenüber "
     "Mikrofonabstand/Raumakustik, v.a. innerhalb derselben Session vergleichbar",
     "kein Normwert, kanal-/mikrofonabhängig", "immer"),
    ("Jitter (local)", f"{_fmt(features['jitter_local_pct'])} %",
     "Tonhöhen-Perturbation von Zyklus zu Zyklus", "<1% normal (allg. Stimmklinik-Literatur)", "vokal"),
    ("Shimmer (local)", f"{_fmt(features['shimmer_local_pct'])} %",
     "Amplituden-Perturbation von Zyklus zu Zyklus", "<3–5% normal", "vokal"),
    ("Vokalraum-Fläche (VSA)", "noch nicht möglich", "Wie unterschiedlich verschiedene Vokale klingen",
     "braucht mehrere Vokale pro Aufnahme", "vokal"),
]

table_df = pd.DataFrame(table_rows, columns=["Parameter", "Wert", "Was es misst", "Referenz / Normwert", "fit"])
table_df["Auswertbar bei"] = table_df["fit"].map(FIT_LABELS)
table_df = table_df.drop(columns=["fit"])
st.dataframe(table_df, width='stretch', hide_index=True)

st.caption(
    "Referenzwerte für Jitter/Shimmer/HNR/Sprechrate aus allgemeiner stimmklinischer "
    "Literatur bzw. der IReST-Studie (siehe docs/literatur_review.md) — noch nicht aus der "
    "Saarbrücker Voice Database projektspezifisch gezogen. CPPS-Werte sind stark "
    "parameterabhängig (Fenstergrößen, Trendlinie) und nicht 1:1 mit anderen Tools vergleichbar. "
    "Formant-Streuung/-Geschwindigkeit sind zeitaufgelöste Annäherungen, kein Ersatz für eine "
    "echte Vokalraum-Messung — nur stimmhafte, physiologisch plausible Frames werden "
    "berücksichtigt (Praats Formant-Tracker kann sonst auf falsche Werte springen, siehe "
    "docs/backlog.md)."
)

# --- 4. Glossar ---
st.subheader("Glossar")

glossary = [
    ("F0", "Grundfrequenz — wie oft die Stimmbänder pro Sekunde schwingen. Wird als Tonhöhe wahrgenommen."),
    ("F0-Perzentile", "5. und 95. Perzentil der Tonhöhe über die Aufnahme — zeigt die Streuung robuster als die reine Standardabweichung, weniger anfällig für einzelne Ausreißer."),
    ("Pitch Slope", "Linearer Trend der Tonhöhe über die Zeit einer Aufnahme. Ein fallender Trend über eine längere Äußerung kann auf stimmliche Ermüdung hindeuten."),
    ("Voice Breaks", "Anzahl/Anteil an Stellen, an denen die Stimmgebung unterbrochen ist. Nur bei gehaltenem Vokal aussagekräftig — bei normaler Sprache durch Wortpausen und stimmlose Laute (s, f, ch) ohnehin häufig, ohne dass das pathologisch ist."),
    ("Mikro-/Makropausen", "Sprechpausen nach Dauer unterschieden (Schwelle 500ms). Mikropausen entsprechen meist normalen Atem-/Wortgrenzen, Makropausen eher auffälligen Zögerungen oder Wortsuche."),
    ("Formanten (F1, F2, F3)", "Resonanzfrequenzen des Vokaltrakts, die den Vokalklang formen. F1 hängt vor allem mit der Zungenhöhe zusammen, F2 mit der Zungenposition vorne/hinten, F3 mit der Klangschärfe."),
    ("Formant-Streuung", "Wie stark F1/F2 über die Aufnahme hinweg variieren (Interquartilsabstand). Kein Ersatz für die klassische Vokalraum-Fläche (die feste Eckvokale i/a/u bräuchte), aber ein Hinweis darauf, wie viel vokalischer Raum überhaupt genutzt wird."),
    ("Formant-Geschwindigkeit", "Wie schnell sich ein Formant (meist F1) über die Zeit ändert. Funktioniert ohne bekannte Vokal-Identität und dient als Näherung für Zungen-/Kieferbeweglichkeit."),
    ("Jitter", "Wie stark die Tonhöhe von einem Stimmzyklus zum nächsten schwankt — nur bei gehaltenem Vokal zuverlässig messbar."),
    ("Shimmer", "Wie stark die Lautstärke von einem Stimmzyklus zum nächsten schwankt — ebenfalls nur bei gehaltenem Vokal zuverlässig."),
    ("HNR", "Harmonics-to-Noise-Ratio — Verhältnis von klarem, harmonischem Stimmklang zu Rauschanteil. Höher = klarere Stimme."),
    ("CPP(S)", "Cepstral Peak Prominence (geglättet) — alternatives Stimmklang-Maß, das anders als Jitter/Shimmer auch bei fließender Sprache zuverlässig funktioniert."),
    ("Monopitch", "Wie wenig sich die Tonhöhe über eine Äußerung verändert. Sehr geringe Variation kann auf eintönige Sprechweise hindeuten."),
    ("Monoloudness", "Wie wenig sich die Lautstärke über eine Äußerung verändert."),
    ("nPVI (Rhythmus)", "Normalisierter Pairwise Variability Index — misst, wie unterschiedlich lang aufeinanderfolgende Wörter sind. Hoch = abwechslungsreicher Rhythmus."),
    ("Prosodische Entropie", "Wie vorhersehbar der Sprechrhythmus insgesamt ist (Shannon-Entropie über die Verteilung aller Wortdauern), nicht nur zwischen benachbarten Wörtern wie beim nPVI. Niedrig = monoton/gleichförmig, hoch = abwechslungsreich."),
    ("Artikulationsschärfe", "Wie klar/scharf Verschlusslaute (p, t, k, b, d, g) gebildet werden — erkannt über kurze Energieeinbrüche mit anschließendem scharfem Anstieg."),
    ("Voice Onset Time (VOT)", "Zeit zwischen der Lösung eines Verschlusslauts (z.B. bei p, t, k) und dem Einsetzen der Stimmbandschwingung danach. Im Deutschen meist kürzer/unaspirierter als im Englischen — die Verschlussdauer selbst gilt hier als aussagekräftiger."),
    ("MFCC", "Mel-Frequency Cepstral Coefficients — Standardmaß für die allgemeine Klangfarbe eines Signals. Empfindlich gegenüber Aufnahmebedingungen (Mikrofonabstand, Raumakustik), deshalb v.a. innerhalb derselben Aufnahme-Session vergleichbar."),
    ("Intonationskontur", "Der Tonhöhen-Verlauf innerhalb einzelner Sprechphrasen (z.B. steigend am Satzanfang, fallend am Ende). Wird hier durch Pausen in der Stimmgebung abgegrenzt, nicht durch das Transkript."),
    ("Type-Token-Ratio (TTR)", "Anteil unterschiedlicher Wörter (Types) an allen Wörtern (Tokens) im Transkript. Sinkt mit zunehmender Textlänge allein durch Wiederholungen häufiger Wörter (z.B. Artikel) — deshalb bei unterschiedlich langen Aufnahmen nicht direkt vergleichbar."),
    ("MTLD", "Measure of Textual Lexical Diversity — misst lexikalische Vielfalt textlängen-robuster als die reine TTR, indem der Text in Abschnitte bis zu einer TTR-Schwelle zerlegt wird. Wurde ursprünglich für deutlich längere Texte entwickelt als unsere ~10s-Snippets."),
    ("Vokalraum-Fläche (VSA)", "Wie unterschiedlich verschiedene Vokale (i, a, u) im Formant-Raum klingen. Braucht mehrere Vokale in einer Aufnahme."),
    ("Fluency-Score", "Anteil der Sprechspanne, der ohne auffällig lange Pausen gesprochen wird."),
]
gl_cols = st.columns(3)
for i, (term, definition) in enumerate(glossary):
    with gl_cols[i % 3]:
        st.markdown(f"**{term}**")
        st.caption(definition)

# --- 5. Transkription + Sprechfluss (Chunk 3/4 aus docs/backlog.md) ---
st.subheader("Transkription & Sprechfluss (Detailansicht)")

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

        detail_metrics = compute_speech_metrics(transcript["words"], total_duration_s=stats["duration_s"])
        scores = [w["score"] for w in transcript["words"] if w.get("score") is not None]
        mean_confidence = sum(scores) / len(scores) if scores else None
        low_confidence_count = sum(1 for s in scores if s < CONFIDENCE_WARN_THRESHOLD)

        c1, c2 = st.columns(2)
        c1.metric("Ø Erkennungs-Konfidenz", f"{mean_confidence:.0%}" if mean_confidence is not None else "–")
        c2.metric("Unsichere Wörter (<75%)", low_confidence_count)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Wörter", detail_metrics["n_words"])
        m2.metric("Sprechrate (Netto)", f"{detail_metrics['net_speech_rate_wpm']:.0f} Wörter/min" if detail_metrics["net_speech_rate_wpm"] else "–")
        m3.metric("Sprechrate (Artikulation)", f"{detail_metrics['articulation_rate_wpm']:.0f} Wörter/min" if detail_metrics["articulation_rate_wpm"] else "–")
        m4.metric("Flüssigkeits-Score", f"{detail_metrics['fluency_score']:.2f}" if detail_metrics["fluency_score"] is not None else "–")

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Pausen (≥250ms)", detail_metrics["pause_count"])
        p2.metric("Ø Pausendauer", f"{detail_metrics['mean_pause_duration_s']:.2f} s" if detail_metrics["mean_pause_duration_s"] else "–")
        p3.metric("Max. Pausendauer", f"{detail_metrics['max_pause_duration_s']:.2f} s" if detail_metrics["max_pause_duration_s"] else "–")
        p4.metric("Rhythmus (nPVI)", f"{detail_metrics['rhythm_npvi']:.1f}" if detail_metrics["rhythm_npvi"] is not None else "–")

        q1, q2 = st.columns(2)
        q1.metric(
            "Mikropausen (250-500ms)",
            f"{detail_metrics['micro_pause_count']} · Ø {detail_metrics['mean_micro_pause_duration_s']:.2f}s"
            if detail_metrics["mean_micro_pause_duration_s"] is not None
            else f"{detail_metrics['micro_pause_count']}",
        )
        q2.metric(
            "Makropausen (≥500ms)",
            f"{detail_metrics['macro_pause_count']} · Ø {detail_metrics['mean_macro_pause_duration_s']:.2f}s"
            if detail_metrics["mean_macro_pause_duration_s"] is not None
            else f"{detail_metrics['macro_pause_count']}",
        )

        with st.expander("Wort-Zeitstempel (Detailtabelle)"):
            words_df = pd.DataFrame(transcript["words"])
            st.dataframe(words_df, width='stretch', hide_index=True)

        st.caption(
            "Sprechrate/Pausen basieren auf Wort-Zeitstempeln aus der Transkription (WhisperX), "
            "nicht auf reiner akustischer Stille-Erkennung — präziser, da bekannt ist, WAS "
            "zwischen den Pausen gesprochen wurde. Mikro-/Makropausen (Schwelle 500ms) können "
            "auf unterschiedliche Ursachen hindeuten — Mikropausen eher normale Atem-/"
            "Wortgrenzen, Makropausen eher auffällige Zögerungen. Details: docs/backlog.md, "
            "Stufe 3 / Chunk 3."
        )
