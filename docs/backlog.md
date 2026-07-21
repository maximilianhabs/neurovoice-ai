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
- [x] Formant-Tracks (F1-F3) als Overlay im Spektrogramm + Mittelwerte in der Feature-Tabelle
      (Stufe 2 aus Phase 2), verifiziert an Take 3 (F1≈729Hz, F2≈1776Hz, F3≈2733Hz, plausibel)
- [ ] Vokalraum-Plot (F1/F2) für Vokal-Task — braucht mehrere unterschiedliche Vokale in einer
      Aufnahme, aktuelles Aufnahme-Konzept liefert nur einen gehaltenen Vokal pro Take
- [x] Transkript-Caching: Ergebnis wird nach `/derived/<patient_id>/*.transcript.json`
      geschrieben (getrennt vom read-only `/data`-Mount), läuft nur noch einmal pro Datei
      statt bei jedem Dashboard-Aufruf neu — Button "Neu transkribieren" überschreibt bewusst
- [x] Speech-to-Text-Transkription, Chunk 1: `dashboard/core/transcription.py`, WhisperX
      lokal (`large-v3`, Genauigkeit vor Geschwindigkeit, Nutzer-Vorgabe 2026-07-21), liefert
      Text + wortgenaue Zeitstempel (Alignment via wav2vec2). Mittlerweile auch gegen echte
      Sprache verifiziert (Chunk 2) und live im Produktions-Dashboard deployed (Chunk 5).
  - [x] Chunk 2: Wort-Alignment gegen echte Aufnahme verifiziert (2026-07-21, Take 3 „selbst",
        realer Sprecher, kein TTS) — 27/27 Wörter korrekt, Konfidenz 0,74-0,99. Zeitstempel
        stichprobenartig gegen die Intensitätskurve geprüft (Parselmouth): Stille vor Sprechbeginn
        ~39 dB vs. aktive Sprache 65-75 dB vs. Stille danach ~48,6 dB — Übergänge passen sauber.
        Laufzeit ~83s für 12,2s Audio auf M1 (lokal getestet, nicht auf dem Beelink-Server —
        Performance-Risiko auf der schwächeren N150-CPU noch nicht geprüft, siehe Hinweis unten).
  - [x] Chunk 3: `core/speech_metrics.py` — Sprechgeschwindigkeit, Pausen-Statistik (granular
        zwischen Wörtern), Flüssigkeits-Score aus Wortliste. Verifiziert gegen Take 3: 0 echte
        Pausen (deckt sich mit dem früheren Intensitäts-Befund), Fluency-Score 1.0.
        **= identisch mit Stufe 3 in Phase 2** (ein Modul für beides)
  - [x] Chunk 4: Dashboard-Integration (`app.py`, neue Sektion "Transkription & Sprechfluss"
        mit Trigger-Button, `st.cache_data`, gracefully degradierend ohne WhisperX)
  - [x] Chunk 5: `requirements.txt`/`Dockerfile` für torch/whisperx angepasst, Modell-Cache als
        Volume eingerichtet, auf dem Beelink-Server deployed und **live verifiziert** (2026-07-21):
        27/27 Wörter korrekt im echten Produktions-Container, 96,1s Laufzeit, 576,9 MiB Speicher
        (weit unter Limit). Unterwegs ein echter Bug gefunden+behoben: erster Live-Lauf endete in
        einem OOM-Kill (5g-Limit reichte nicht, weil Streamlit-Grundlast mitzählt) — siehe
        docs/bugtracker.md INFRA-BEFUND-09. Limit auf 7g erhöht, seitdem stabil.
- [ ] Später: Verlaufsansicht über mehrere Aufnahmen derselben Person (longitudinal)

**Deploy-Hinweis**: Code wird aktuell manuell per `scp` nach `~/neurovoice-dashboard/` auf den
Server kopiert (kein `git clone` dort) — bei Änderungen erneut kopieren + `docker compose up -d --build`.

## Phase 2 — Feature-Extraktion (nach stabiler Aufnahme-Pipeline)

Tool-Basis: **Parselmouth** (Phonation/Spektral/Prosodie) + **WhisperX** (Transkript +
Wort-Zeitstempel, siehe Phase 2b Chunks). **Reorganisiert 2026-07-21**: Nutzerwunsch war,
"so viele logopädische Parameter wie möglich" zu erfassen — Reihenfolge bleibt einfach→komplex,
aber Stufe 3 nutzt jetzt bewusst die Wort-Zeitstempel aus der Transkription (Chunk 3) statt
reiner akustischer Pausenerkennung, weil das präziser ist (siehe dort).

### Stufe 1 — Phonation/Stimmbandarbeit, gehaltener Vokal ✅ IM DASHBOARD UMGESETZT
- [x] F0 (Mittelwert, SD)
- [x] Jitter
- [x] Shimmer
- [x] HNR/NHR
- [ ] Referenzwerte/Normalisierung nach Geschlecht (Saarbrücken Voice Database) noch nicht hinterlegt — Werte werden angezeigt, aber noch nicht eingeordnet ("normal" vs. "auffällig")

### Stufe 2 — Spektralanalyse/Klangfarbe/Artikulationsort (Zunge, harter/weicher Gaumen)
- [x] Formanten F1-F3 — im Dashboard umgesetzt (siehe Phase 2b oben), F1↔Zungenhöhe, F2↔Zungenposition vorne/hinten (siehe docs/literatur_review.md)
- [ ] MFCCs (allgemeine Klangfarbe)
- [ ] Vowel Space Area / Formant-Ratios (mit Vorsicht — Literatur uneinheitlich, siehe Review)
- [ ] Ort-der-Artikulation-Differenzierung bei Konsonanten (velar/harter+weicher Gaumen vs. alveolar/Zungenspitze, spektrale Bursts — siehe Literatur-Review)

### Stufe 3 — Sprechrate/Pausen/Flüssigkeit **(= Speech-to-Text Chunk 3, siehe Phase 2b)**
Nutzt die Wort-Zeitstempel aus der Transkription für granulare Pausenanalyse zwischen Wörtern,
statt reiner akustischer Stille-Erkennung — präziser, weil man weiß, WAS zwischen den Pausen
gesprochen wurde. Details/Status siehe Phase 2b, Chunk 3.
- [x] Sprechrate (Wörter pro Minute, netto + artikulationsbezogen) — im Dashboard umgesetzt
- [x] Pausenstatistik zwischen Wörtern (Anzahl, Ø/Max-Dauer) aus Wort-Zeitstempeln — im Dashboard umgesetzt
- [x] Flüssigkeits-Score (Anteil der Sprechspanne ohne echte Pausen) — im Dashboard umgesetzt
- [ ] Diadochokinetische Rate (separater Task "pa-ta-ka" nötig — noch nicht in Aufnahme-Konzept enthalten, offene Frage unten)

### Stufe 4 — Prosodie/Sprechweise ✅ IM DASHBOARD UMGESETZT (2026-07-21)
- [x] Monopitch-Maß (SD F0 über Äußerung) — wiederverwendet aus Stufe 1 (Phonation-Tabelle), keine doppelte Berechnung
- [x] Monoloudness (SD Intensität) — `prosody_features()`, verifiziert an allen 3 Testaufnahmen (10,9-12,7 dB)
- [x] Rhythmus (nPVI) — `speech_metrics.py`, Näherung auf Wortebene (keine Silbensegmentierung), Teil der Sprechfluss-Metriken
- **Bug unterwegs gefunden+behoben**: Praat-Sentinel -300dB (Stille) verzerrte den ersten Monoloudness-Wert massiv (26,18 statt 12,75 dB) — betraf auch die Lautstärkekurve. Siehe docs/bugtracker.md BUG-11.

### Stufe 5 — Artikulationssauberkeit (Plosive/Konsonanten)
- [ ] **Verschlussdauer (Closure Duration) bei Plosiven statt VOT** — im Deutschen wird Fortis/Lenis
      (p/b, t/d, k/g) primär über Verschlussdauer signalisiert, nicht über Aspiration/VOT wie im
      Englischen (fortis-Verschluss ca. 4x länger als lenis). VOT bleibt ein Zusatzmaß, ist aber nicht
      das primäre deutsche Unterscheidungsmerkmal.

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
