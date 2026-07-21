# NeuroVoice Analyse-Dashboard — Konzept

Stand: 2026-07-21. Analog zum bestehenden EDF-Analyzer-Projekt (Streamlit-App für
EEG/EKG-Analyse) — gleiches Werkzeug, gleicher Grundworkflow: Aufnahme auswählen →
Kurven/Spektrum anzeigen → Kennwerte-Tabelle.

## Tech-Stack

**Streamlit**, lokal auf dem Beelink-Server, **nur über Tailscale erreichbar**
(kein öffentlicher Zugriff, passt zum Datenschutz-Grundgedanken des Projekts —
anders als der öffentlich erreichbare EDF-Analyzer mit Passwortschutz).

## Bausteine

### 1. Audio-Player
- WAV direkt im Browser abspielbar (natives HTML5-Audio via Streamlit `st.audio`)

### 2. Visualisierungen

| Visualisierung | Zeigt | Bibliothek |
|---|---|---|
| Wellenform | Amplitude über Zeit | matplotlib/plotly auf Basis der PCM-Samples |
| Spektrogramm | Zeit-Frequenz-Heatmap (Energie als Farbe) | Parselmouth/Praat oder librosa |
| Pitch-Kontur (F0) | Tonhöhenverlauf über Zeit | Parselmouth `Sound.to_pitch()` |
| Formant-Tracks (F1-F3) | Linien über dem Spektrogramm | Parselmouth `Sound.to_formant_burg()` |
| Intensitäts-/Lautstärkekurve | dB über Zeit | Parselmouth `Sound.to_intensity()` |
| Vokalraum-Plot (nur Vokal-Task) | F1 gegen F2 als Punktwolke | eigene Darstellung |

### 3. Feature-Tabelle
Tabellarisch mit Wert + Einheit + kurzer Erklärung, wächst mit dem Backlog aus Phase 2
(docs/backlog.md) mit: F0 Mittelwert/SD, Jitter, Shimmer, HNR, Formanten F1-F3,
Sprechrate, Pausenanzahl, später Prosodie-/Artikulationsmaße.

### 4. Perspektivisch (nicht Teil des ersten Wurfs)
Verlaufsansicht über mehrere Aufnahmen derselben Person (Trend statt Einzelwert) —
das ist der eigentliche longitudinale Zweck des Projekts, sinnvoll erst wenn genug
Testdaten vorhanden sind.

## Einordnung im Projektfahrplan

Dashboard baut direkt auf Phase 2 (Feature-Extraktion via Parselmouth) auf — ohne
extrahierte Features keine Tabelle/Kurven. Reihenfolge: Phase 1 (Aufnahme-Pipeline,
✅ Grundgerüst steht) → Phase 2 (Feature-Extraktion, Stufe 1 zuerst) → Dashboard
parallel zu Phase 2 aufbauen, sobald erste Features (Stufe 1: F0/Jitter/Shimmer/HNR)
verfügbar sind — dann direkt mit Wellenform+Pitch-Kontur+Tabelle starten und mit
jeder weiteren Feature-Stufe erweitern, statt auf den vollen Feature-Umfang zu warten.
