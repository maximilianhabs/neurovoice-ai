# NeuroVoice AI — Backlog

Stand: 2026-07-21

## Grundprinzip

Alle Feature-Familien werden mittelfristig angegangen, aber **skaliert von einfach zu komplex** —
nicht alles auf einmal. Reihenfolge orientiert sich daran, wie gut ein Feature etabliert/validiert
ist und wie einfach es aus einem einzelnen Task-Typ zuverlässig extrahierbar ist.

## Phase 1 — Aufnahme-Pipeline (aktuell)

- [x] Syncthing auf Beelink-Server installiert (Docker, Tailscale-only, Discovery/Relay deaktiviert) — siehe homeserver-Repo LOG.md 2026-07-21
- [x] ffmpeg auf Server installiert
- [x] Syncthing auf iPhone eingerichtet (Möbius Sync), Pairing mit Server abgeschlossen und verifiziert (siehe homeserver-Repo LOG.md + services/syncthing/README.md für Troubleshooting)
- [x] Ordnerstruktur angelegt: `~/neurovoice-data/raw-inbox` (Syncthing-Ziel) getrennt von `~/neurovoice-data/raw/<patient_id>/...` (final) — auf dem Server, nicht im Git-Repo
- [x] Konvertierungsskript: `.m4a` (ALAC) → `.wav`, verlustfrei (Dekodierung, kein Re-Encoding) — `scripts/convert_and_verify.sh`, deployed auf Server
- [x] Verifikationsskript: `ffprobe`-Check (Codec/Samplerate/Bittiefe) + Checksumme vor/nach Transfer — im selben Skript enthalten
- [x] Erste Testaufnahme komplett durch die Pipeline (Vokal-Task, später zu Lesetext korrigiert, da tatsächlicher Inhalt der Nordwind-Satz war — Namenskonvention beim Umbenennen in Voice Memos auf Leerzeichen statt Unterstriche achten)
- [ ] Restliche Testdatenbank auffüllen (aktuell: 1 von 5-6 Aufnahmen)
- [x] Lesetext festgelegt: "Nordwind und Sonne" (Standard-IPA-Referenztext, siehe docs/lesetext_nordwind_sonne.md)
- [x] iPhone-Einstellung "Voice Memos → Audioqualität" auf "Verlustfrei" umgestellt (erste Testdatei war noch AAC/komprimiert, siehe homeserver-Repo LOG.md)

## Phase 2b — Analyse-Dashboard (parallel zu Phase 2, siehe docs/dashboard_konzept.md)

Streamlit-App, analog zum bestehenden EDF-Analyzer-Projekt, lokal auf dem Beelink-Server
(nur Tailscale, kein öffentlicher Zugriff). Audio-Player + Wellenform/Spektrogramm/
Pitch-Kontur/Formant-Tracks/Intensitätskurve + wachsende Feature-Tabelle. Start sobald
Stufe 1 der Feature-Extraktion (F0/Jitter/Shimmer/HNR) steht — nicht erst nach vollem
Feature-Umfang.

- [x] Streamlit-Grundgerüst (Datei auswählen → Player → Wellenform) — läuft auf `100.67.129.76:8501`, Code in `dashboard/`
- [x] Spektrogramm-Ansicht (mit F0-Overlay)
- [x] Intensitätskurve (Lautstärke über Zeit)
- [x] Feature-Tabelle Stufe 1 (F0 Mittelwert/SD, Jitter, Shimmer, HNR) mit Warnhinweis bei Nicht-Vokal-Tasks
- [ ] Formant-Tracks (F1-F3) als eigenes Overlay (bisher nur F0 im Spektrogramm)
- [ ] Vokalraum-Plot (F1/F2) für Vokal-Task
- [x] Speech-to-Text-Transkription, Chunk 1: `dashboard/core/transcription.py`, WhisperX
      lokal (`large-v3`, Genauigkeit vor Geschwindigkeit, Nutzer-Vorgabe 2026-07-21), liefert
      Text + wortgenaue Zeitstempel (Alignment via wav2vec2). Nur gegen synthetische
      macOS-`say`-TTS-Aufnahme des Nordwind-Referenztexts verifiziert (27/27 Wörter korrekt,
      Zeitstempel plausibel) — noch NICHT gegen echte (ggf. dysarthrische) Sprache getestet,
      das ist ein reiner Mechanik-Nachweis. `whisperx` noch nicht in `requirements.txt`
      (bewusst, siehe Chunk 5 unten — erst nach Chunk 2-4 in Docker-Setup übernehmen).
  - [ ] Chunk 2: Wort-Alignment-Genauigkeit gegen echte Aufnahme stichprobenartig verifizieren
  - [ ] Chunk 3: `core/speech_metrics.py` — Sprechgeschwindigkeit, Pausen-Statistik, Flüssigkeits-Score aus Wortliste
  - [ ] Chunk 4: Dashboard-Integration (`app.py`, neue Sektion nach Feature-Tabelle)
  - [ ] Chunk 5: `requirements.txt`/`Dockerfile` für torch/whisperx anpassen, Modell-Cache als Volume einplanen (Beelink-Deploy)
- [ ] Später: Verlaufsansicht über mehrere Aufnahmen derselben Person (longitudinal)

**Deploy-Hinweis**: Code wird aktuell manuell per `scp` nach `~/neurovoice-dashboard/` auf den
Server kopiert (kein `git clone` dort) — bei Änderungen erneut kopieren + `docker compose up -d --build`.

## Phase 2 — Feature-Extraktion (nach stabiler Aufnahme-Pipeline)

Tool-Basis: **Parselmouth** (Python-Wrapper um Praat, klinischer Goldstandard).

### Stufe 1 — Phonation, gehaltener Vokal (am einfachsten, am besten etabliert)
- [ ] F0 (Mittelwert, SD)
- [ ] Jitter
- [ ] Shimmer
- [ ] HNR/NHR
- [ ] Erste Referenzwerte/Normalisierung nach Geschlecht recherchieren & hinterlegen

### Stufe 2 — Spektralanalyse/Klangfarbe
- [ ] Formanten F1-F3 (gehaltener Vokal zunächst, später Vokale in Fließsprache)
- [ ] MFCCs
- [ ] Vowel Space Area / Formant-Ratios (mit Vorsicht — Literatur uneinheitlich, siehe Review)

### Stufe 3 — Zeitliche Struktur/Sprechfluss (Freisprache + Lesetext)
- [ ] Sprechrate (Net Speech Rate)
- [ ] Pausenerkennung + Pausenmuster (Anzahl, Dauer)
- [ ] Diadochokinetische Rate (separater Task "pa-ta-ka" nötig — noch nicht in Aufnahme-Konzept enthalten)

### Stufe 4 — Prosodie
- [ ] Monopitch-Maß (SD F0 über Äußerung, Freisprache/Lesetext)
- [ ] Monoloudness (SD Intensität)
- [ ] Rhythmus/PVI

### Stufe 5 — Artikulation (komplexer, ggf. spätere Iteration)
- [ ] **Verschlussdauer (Closure Duration) bei Plosiven statt VOT** — im Deutschen wird Fortis/Lenis
      (p/b, t/d, k/g) primär über Verschlussdauer signalisiert, nicht über Aspiration/VOT wie im
      Englischen (fortis-Verschluss ca. 4x länger als lenis). VOT bleibt ein Zusatzmaß, ist aber nicht
      das primäre deutsche Unterscheidungsmerkmal.
- [ ] Ort-der-Artikulation-Differenzierung (velar vs. alveolar, spektrale Bursts)

### Stufe 6 — CPP als robusteres Alternativmaß zu Jitter/Shimmer bei Fließsprache
- [ ] Cepstral Peak Prominence für Freisprache/Lesetext (da Jitter/Shimmer dort unzuverlässig sind)

## Später (explizit nicht Teil des aktuellen Auftrags)

- Whisper-Transkription
- OpenSMILE/eGeMAPS als Ergänzung/Vergleich zu Parselmouth
- ML-Klassifikation / longitudinale Trend-Modelle
- Lokales LLM für Verlaufsberichte
- Web-App/UI für geführte Angehörigen-Nutzung
- Externes USB-Mikro als Aufnahmequelle
- Echte Pseudonymisierungs-/Zuordnungstabelle (sobald echte Testpersonen dazukommen)

## Sprache: Deutsch (Muttersprache) — Konsequenzen für die Pipeline

- **Lesetext**: "Nordwind und Sonne" (docs/lesetext_nordwind_sonne.md) — Standard-IPA-Referenztext,
  phonetisch repräsentativ, ermöglicht später auch Vergleich mit anderssprachigen Aufnahmen/Literatur,
  da der Text in nahezu jeder Sprache in einer Standardversion existiert.
- **Referenz-/Normwerte**: Saarbrücken Voice Database (SVD) — 2225 deutsche Sprecher:innen (869 gesund,
  1356 pathologisch), gehaltene Vokale /a/,/i/,/u/ in normal/hoch/tief/steigend-fallend. Als deutsche
  Normwert-Basis für Stufe-1-Phonation-Features nutzbar, statt eigene Normwerte mühsam zu erheben.
- **Fortis/Lenis im Deutschen ≠ Englisch**: siehe Stufe 5 oben — Verschlussdauer statt VOT/Aspiration
  ist das primäre Unterscheidungsmerkmal deutscher Plosive.

## Offene fundamentale Fragen (aus Konzeptphase, zu klären bevor Phase 2 beginnt)

- Wie werden Referenzbereiche/Normwerte pro Sprecher:in (Geschlecht, Alter) gepflegt?
- Wird ein "pa-ta-ka"-Task für Diadochokinese ergänzt, oder bleibt es bei den 3 Task-Typen?
- Wie wird mit der Diskrepanz zwischen automatisierten Metriken und klinisch-perzeptivem Höreindruck
  umgegangen (Konfidenzangaben statt reiner Zahlen)?
