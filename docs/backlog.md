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

## Normwert-Ampel-Visualisierung ✅ UMGESETZT (2026-07-22)

Konzept-Artifact (2026-07-21) vollständig ins Produktions-Dashboard übernommen. Hierarchie
nach **Auswertbarkeit beim Lesetext** (Nutzer-Entscheidung: "wir werden hauptsächlich Texte/
Wörter vorlesen lassen"), nicht nur nach Literatur-Robustheit:

- [x] `core/reference_ranges.py` — Ampel-Zonen für Sprechrate/HNR/Jitter/Shimmer (aus allg.
      Stimmklinik-Literatur + IReST-Studie), `verdict_for_value()` für Farbe+Label
- [x] `core/plots.py`: `gauge_figure()` (Halbkreis-Tacho mit Matplotlib Wedges + Nadel),
      `radar_figure()` (Polar-Profil)
- [x] "Werte auf einen Blick": Primärgruppe groß (Sprechrate, HNR, Monopitch,
      Artikulationsschärfe, CPPS) + Radar-Profil; Sekundärgruppe klein/muted (Jitter,
      Shimmer, Vokalraum-Fläche — bewusst nach unten trotz guter Literatur-Basis)
- [x] Konsolidierte "Tabellarische Übersicht" (ersetzt 3 verstreute Einzeltabellen) —
      alle 14 Parameter mit Wert, Erklärung, Referenz/Normwert, Auswertbarkeit
- [x] "Glossar"-Abschnitt (F0, Formanten, Jitter, Shimmer, HNR, CPP, Monopitch/
      Monoloudness, nPVI, Artikulationsschärfe, VSA, Fluency-Score)
- Verifiziert headless via `streamlit.testing.v1.AppTest` (mit UND ohne gecachtes
  Transkript) — keine Exceptions, Werte/Verdicts stimmen mit bekannten Take-3-Referenzen
  überein (Sprechrate 133 WPM → "grenzwertig", HNR 8,67dB → "auffällig").

**Offen**: Ampel-Grenzwerte stammen aus allgemeiner Literatur/IReST, noch nicht aus der
Saarbrücker Voice Database projektspezifisch gezogen (bestehende offene Frage, s.u.).

## Phase 2 — Feature-Extraktion (nach stabiler Aufnahme-Pipeline)

Tool-Basis: **Parselmouth** (Phonation/Spektral/Prosodie) + **WhisperX** (Transkript +
Wort-Zeitstempel, siehe Phase 2b Chunks). **Reorganisiert 2026-07-21**: Nutzerwunsch war,
"so viele logopädische Parameter wie möglich" zu erfassen — Reihenfolge bleibt einfach→komplex,
aber Stufe 3 nutzt jetzt bewusst die Wort-Zeitstempel aus der Transkription (Chunk 3) statt
reiner akustischer Pausenerkennung, weil das präziser ist (siehe dort).

### Stufe 1 — Phonation/Stimmbandarbeit, gehaltener Vokal ✅ ERWEITERT (2026-07-22)
- [x] F0 (Mittelwert, SD)
- [x] Jitter
- [x] Shimmer
- [x] HNR/NHR
- [x] CPPS (siehe Stufe 6)
- [ ] Referenzwerte/Normalisierung nach Geschlecht (Saarbrücken Voice Database) noch nicht hinterlegt — Werte werden angezeigt, aber noch nicht eingeordnet ("normal" vs. "auffällig")
- [x] **F0-Perzentile (5./95.)** — `phonation_dynamics_features()`, robuster gegen Ausreißer als
      reine SD. Verifiziert an allen 3 Takes (78-86Hz / 130-150Hz).
- [x] **Pitch Slope (Fatigue-Marker)** — linearer Trend der F0-Kontur über die Zeit. Alle 3 Takes
      zeigen konsistent negativen Trend (-1,17 bis -1,97 Hz/s) — reproduzierbares Muster, auch
      wenn bei 10-12s-Snippets als Fatigue-Indikator noch unsicher (eher für längere
      Freisprache-Aufnahmen gedacht).
- [x] **Voice Breaks** — Praats Standard-"Voice report", `phonation_dynamics_features()`.
      **Wichtiger Befund beim Implementieren**: wie Jitter/Shimmer nur bei gehaltenem Vokal
      sauber interpretierbar — bei Fließsprache erzeugen normale Wortpausen/stimmlose
      Konsonanten zwangsläufig viele "Breaks" (24 Ereignisse, 26% bei Take 3 — kein
      Alarmsignal). Deshalb in der Tabelle als "nur bei gehaltenem Vokal" markiert, nicht als
      primäre Ampel-Kennzahl.

### Stufe 2 — Spektralanalyse/Klangfarbe/Artikulationsort (Zunge, harter/weicher Gaumen)
- [x] Formanten F1-F3 — im Dashboard umgesetzt (siehe Phase 2b oben), F1↔Zungenhöhe, F2↔Zungenposition vorne/hinten (siehe docs/literatur_review.md)
- [ ] MFCCs (allgemeine Klangfarbe)
- [ ] Vowel Space Area / Formant-Ratios (mit Vorsicht — Literatur uneinheitlich, siehe Review)
- [ ] Ort-der-Artikulation-Differenzierung bei Konsonanten (velar/harter+weicher Gaumen vs. alveolar/Zungenspitze, spektrale Bursts — siehe Literatur-Review)
- [x] **Zeitaufgelöste Formantanalyse** ✅ UMGESETZT (2026-07-22) — `formant_dynamics_features()`
      ergänzt den bisherigen Ganzaufnahme-Mittelwert um Formant-Streuung (F1/F2-IQR über
      stimmhafte Frames, Proxy für genutzten Vokalraum) und Formant-Geschwindigkeit
      (F1-Änderungsrate, Proxy für Zungen-/Kieferbeweglichkeit, funktioniert ohne Vokal-
      Identität). **Bewusst KEIN Ersatz für echte Vokalraum-Fläche** (bräuchte feste Eckvokale
      i/a/u) — ehrliche Annäherung, siehe Docstring. Bug unterwegs gefunden+behoben: Praats
      Formant-Tracker "sprang" bei ~10% der Frames auf physiologisch unmögliche Werte
      (F1 bis 1869Hz) — Plausibilitätsfilter (F1: 150-1100Hz, F2: 500-3500Hz) behebt das,
      siehe docs/bugtracker.md BUG-12. Verifiziert an allen 3 Takes: F1-Range konsistent
      930-945Hz nach Fix.

### Stufe 3 — Sprechrate/Pausen/Flüssigkeit **(= Speech-to-Text Chunk 3, siehe Phase 2b)**
Nutzt die Wort-Zeitstempel aus der Transkription für granulare Pausenanalyse zwischen Wörtern,
statt reiner akustischer Stille-Erkennung — präziser, weil man weiß, WAS zwischen den Pausen
gesprochen wurde. Details/Status siehe Phase 2b, Chunk 3.
- [x] Sprechrate (Wörter pro Minute, netto + artikulationsbezogen) — im Dashboard umgesetzt
- [x] Pausenstatistik zwischen Wörtern (Anzahl, Ø/Max-Dauer) aus Wort-Zeitstempeln — im Dashboard umgesetzt
- [x] Flüssigkeits-Score (Anteil der Sprechspanne ohne echte Pausen) — im Dashboard umgesetzt
- [ ] Diadochokinetische Rate (separater Task "pa-ta-ka" nötig — jetzt als fixes Modul in der
      Task-Batterie vorgesehen, siehe "Task-Batterie" unten, nicht mehr nur offene Frage)
- [x] **Mikro-/Makropausen-Verteilung** (Audit 2026-07-22, umgesetzt 2026-07-22) — Pausen nach
      Dauer klassifiziert (Schwelle 500ms): Mikropausen (normale Atem-/Wortgrenzen) vs.
      Makropausen (auffällige Zögerungen/Wortsuche), getrennt ausgewertet in
      `compute_speech_metrics()`. Verifiziert mit synthetischer Wortliste + headless gegen Take 3.
- [ ] **Filled Pauses ("äh", "mhm") und Selbstkorrekturen/Wortabbrüche** (Audit 2026-07-22) —
      ⚠️ **Wichtiger Vorbehalt vor Zusage**: WhisperX/Whisper-Modelle neigen bekanntermaßen dazu,
      Füllwörter/Disfluencies beim Transkribieren zu glätten/wegzulassen (Trainingsdaten-bedingt) —
      muss erst an einer echten Spontansprache-Aufnahme geprüft werden, ob das übliche
      Transkript sie überhaupt enthält, bevor wir das als zuverlässiges Feature versprechen.
      Bislang keine Spontansprache-Aufnahme vorhanden (siehe Task-Batterie unten).

### Stufe 4 — Prosodie/Sprechweise ✅ IM DASHBOARD UMGESETZT (2026-07-21)
- [x] Monopitch-Maß (SD F0 über Äußerung) — wiederverwendet aus Stufe 1 (Phonation-Tabelle), keine doppelte Berechnung
- [x] Monoloudness (SD Intensität) — `prosody_features()`, verifiziert an allen 3 Testaufnahmen (10,9-12,7 dB)
- [x] Rhythmus (nPVI) — `speech_metrics.py`, Näherung auf Wortebene (keine Silbensegmentierung), Teil der Sprechfluss-Metriken
- **Bug unterwegs gefunden+behoben**: Praat-Sentinel -300dB (Stille) verzerrte den ersten Monoloudness-Wert massiv (26,18 statt 12,75 dB) — betraf auch die Lautstärkekurve. Siehe docs/bugtracker.md BUG-11.
- [ ] **Intonationskontur-Analyse** (Audit 2026-07-22) — aktuell wird F0-Variabilität nur als
      EIN Wert (SD über die gesamte Aufnahme) betrachtet, der eigentliche Spannungsbogen
      (steigend/fallend pro Phrase/Satz) fehlt. Braucht Segmentierung in Phrasen (z.B. über
      Satzzeichen im Transkript oder Pausen-Grenzen) + Trend-/Krümmungsanalyse pro Segment.
- [x] **Prosodische Entropie** ✅ UMGESETZT (2026-07-22) — Shannon-Entropie über die
      Wortdauer-Verteilung (`_shannon_entropy_bits()`), ergänzt nPVI um eine
      Gesamtverteilungs-Sicht statt nur benachbarter Wortpaare. Verifiziert an Take 3
      (2,50 bit). Bug beim Testen gefunden+behoben: Fließkomma-Rundungsrauschen bei nahezu
      identischen Wortdauern führte zu künstlich hoher Entropie — Toleranzschwelle statt
      exaktem Vergleich behebt das, siehe docs/bugtracker.md.

### Stufe 5 — Artikulationssauberkeit (Plosive/Konsonanten) ✅ ERSTE VERSION IM DASHBOARD (2026-07-21)
- [x] **Verschlussdauer (Closure Duration) bei Plosiven statt VOT** — `articulation_features()`,
      akustische Verschluss-/Burst-Erkennung über die Intensitätskontur (find_peaks auf
      Praat-Intensität, Prominence-Filter). **Bewusst KEINE phonetische Lauterkennung** —
      generischer Gradmesser für Artikulationsschärfe (Anzahl/Dauer/Burst-Schärfe der
      erkannten Verschluss-Ereignisse), motiviert durch das Dysarthrie-Fernziel des Projekts
      (Nutzerwunsch 2026-07-21: "Schweregrad einordnen, nicht Inhalt entschlüsseln").
      Verifiziert an allen 3 Testaufnahmen: 32-33 Ereignisse, Ø-Verschlussdauer 31-37ms,
      Ø-Burst-Schärfe 252-270 dB/s — sehr konsistent über unabhängige Lesungen desselben
      Texts (gute Baseline-Reproduzierbarkeit). **Noch keine dysarthrische Vergleichsaufnahme
      vorhanden** — aktuell nur an gesunder Sprache kalibriert, siehe Dysarthrie-Konzept unten.

**Audit 2026-07-22: "größter blinder Fleck" des Projekts** — die physiologischen Zungen-/
Lippenmotorik-Marker fehlen noch komplett:
- [x] **Voice Onset Time (VOT) bei Plosiven** ✅ UMGESETZT (2026-07-22) — als Zusatzmaß zur
      Verschlussdauer in `articulation_features()` ergänzt, baut auf der bestehenden
      Burst-Erkennung auf (kein neuer Detektionsschritt nötig). Verifiziert an allen 3
      Testaufnahmen: 23,6-33,1ms, 28-29 von 32-33 Ereignissen messbar — plausibel für
      unaspirierte deutsche Plosive.
- [x] **Vokalzentralisierung (Annäherung)** ✅ TEILWEISE UMGESETZT (2026-07-22) — echte
      Vokalzentralisierung bräuchte bekannte Vokal-Identität (welcher Zeitpunkt = welcher
      Vokal), die wir nicht haben. Als ehrliche Annäherung stattdessen "Formant-Streuung"
      (F1/F2-IQR über alle stimmhaften Frames) in Stufe 2 umgesetzt — zeigt, wie viel
      vokalischer Raum insgesamt genutzt wird, ohne zu wissen welcher Vokal wo war.
- [x] **Formant-Dynamik (F1-Geschwindigkeit)** ✅ UMGESETZT (2026-07-22) — `formant_dynamics_features()`
      in Stufe 2, F1-Änderungsrate (Hz/s) als Näherung für Zungen-/Kieferbeweglichkeit.
      Funktioniert ohne Vokal-Identität, da reine Geschwindigkeit gemessen wird, nicht Position.
- [ ] **Diadochokinese-Rate (DDK-Zyklen/Sekunde, "pa-ta-ka")** — braucht den neuen DDK-Task aus
      der Task-Batterie (siehe unten). Berechnung selbst wäre einfach (Silbenzyklen pro Sekunde
      aus Intensitäts-/Burst-Erkennung, ähnlich der bestehenden Verschluss-Erkennung).
- [ ] **Koartikulation** — vage im Audit benannt, noch nicht konkretisiert. Müsste erst als
      messbare Kennzahl definiert werden (z.B. Formant-Übergangsrate zwischen Nachbarlauten),
      bevor es umsetzbar ist — vorerst nur als Idee vermerkt.

### Stufe 6 — CPP als robusteres Alternativmaß zu Jitter/Shimmer bei Fließsprache ✅ IM DASHBOARD UMGESETZT (2026-07-21)
- [x] Cepstral Peak Prominence (CPPS, geglättet) für Freisprache/Lesetext — `cpp_features()`,
      Praat `To PowerCepstrogram` + `Get CPPS` (Hillenbrand/Heman-Ackah-Konvention). Verifiziert
      an allen 3 Testaufnahmen: 7,1-8,2 dB, konsistent über unabhängige Lesungen. Wichtig:
      CPPS-Werte sind stark parameterabhängig — nicht ungeprüft mit Werten aus anderen
      Tools/Studien vergleichen (gleiches Prinzip wie MDVP- vs. Praat-Normwerte).

### Stufe 7 — Linguistik & Kognition (komplett neu, Audit 2026-07-22)

Bisher liegt nur der rohe Transkript-Text vor (Chunk 1-5) — noch KEINE strukturierte
sprachstatistische oder semantische Auswertung. Braucht deutsches NLP-Tooling (z.B. spaCy
`de_core_news_*`-Modell), das noch nicht Teil des Projekts ist — eigener Technik-Stack, nicht
einfach mit Parselmouth/WhisperX erledigt.

- [ ] Lexikalische Diversität (MTLD, Type-Token-Ratio) — aus dem Transkript-Text ableitbar,
      technisch überschaubar, sobald ein Tokenizer vorhanden ist
- [ ] Syntaktische Komplexität (mittlere Satzlänge/MLU, POS-Tag-Dichte) — braucht POS-Tagging
      (spaCy o.ä.), noch nicht evaluiert für Deutsch
- [ ] Semantische Kohärenz / Informationsdichte — deutlich komplexer als die anderen beiden
      Punkte, vermutlich Embedding-basiert (siehe SSL-Embeddings unten), noch nicht spezifiziert

## Task-Batterie: standardisiertes Aufnahme-Protokoll (Konzept, Audit 2026-07-22)

**Wichtigste konzeptionelle Erkenntnis aus dem Audit**: Weg von der unkontrollierten
Einzelaufnahme, hin zu einem festen Satz von Aufnahme-Modulen — jedes Modul zielt auf andere
Feature-Familien ab, damit nicht ein einzelner Task-Typ (aktuell: nur Lesetext) für alles
herhalten muss.

1. **Gehaltener Vokal ("aaa")** — bereits im ursprünglichen Konzept vorgesehen, bisher aber
   kaum genutzt (alle 3 Testaufnahmen sind Lesetext). Reiner Phonationsstatus (Jitter/Shimmer).
2. **Diadochokinese (DDK, "pa-ta-ka")** — ⚠️ NEU, noch nicht im Aufnahme-Konzept enthalten.
   Braucht eigenen Task-Typ + eigene Analyse (DDK-Rate, siehe Stufe 5). Muss noch in
   `docs/lesetext_nordwind_sonne.md`-artige Dokumentation + Aufnahme-Anleitung aufgenommen werden.
3. **Standardisierter Lesetext ("Nordwind und Sonne")** — ✅ bereits etabliert, Hauptquelle für
   Prosodie/Sprechfluss/Artikulation.
4. **Spontansprache / Bildbeschreibung** — ⚠️ NEU, noch nicht im Aufnahme-Konzept enthalten.
   Notwendig für Stufe 7 (Linguistik/Kognition) und die Filled-Pauses-Erkennung (Stufe 3) — ein
   vorgelesener Text enthält naturgemäß keine spontanen Disfluencies oder freie Wortwahl.

**Nächster konkreter Schritt**: Aufnahme-Konzept (README.md) um Task-Typen 2 und 4 erweitern,
inkl. konkretem Bildmaterial für die Bildbeschreibung (noch auszuwählen) und PATAKA-Anleitung.

## Patienten-Testprotokoll mit 3 Aufgaben (Konzept, 2026-07-22)

Konkretisierung der Task-Batterie-Module 1-3 zu einem tatsächlich nutzbaren Ablauf: die
Person bekommt klare, unmissverständliche Anweisungen und erzeugt eigenständig **3 kurze
Aufnahmen mit dem iPhone**, jede Aufgabe zielt auf einen anderen Teil der Analyse ab.
**Reine Konzeptarbeit — keine Implementierung, kein neuer Code.**

### Aufgabe 1 — Gehaltener Vokal
- **Anweisung (Entwurf)**: "Atme normal ein und sprich dann 'AAAAA' in gleichbleibender
  Lautstärke und Tonhöhe, bis du sanft ausatmest — ca. 5 Sekunden."
- **Warum genau /a/**: Deckt sich mit der Saarbrücker Voice Database (SVD) — dort werden
  exakt /a/, /i/, /u/ als gehaltene Vokale erhoben (siehe docs/literatur_review.md). Passung
  zur SVD-Konvention macht die bislang offene Frage "Referenzwerte aus SVD ziehen" später
  einfacher.
- **Ausbaustufe**: Wenn zusätzlich /i/ und /u/ als kurze Wiederholung derselben Aufgabe
  aufgenommen werden (3 statt 1 Vokal-Take), wird endlich die bislang blockierte **echte
  Vokalraum-Fläche (VSA)** möglich — bisher immer als "nicht möglich, braucht mehrere
  Vokale" vermerkt (siehe Stufe 2). Das wäre ein direkter Zusatznutzen dieses Protokolls.

### Aufgabe 2 — Diadochokinese (DDK)
- **Anweisung (Entwurf)**: "Sprich so schnell und gleichmäßig wie möglich nacheinander:
  zuerst nur 'pa-pa-pa-pa...' (ca. 5s), dann nur 'ta-ta-ta-ta...' (ca. 5s), dann nur
  'ka-ka-ka-ka...' (ca. 5s)."
- **Wichtiger Design-Punkt**: **Einzelsilben getrennt** (pa / ta / ka), nicht nur die
  kombinierte Folge "pa-ta-ka" — jede Einzelsilbe testet einen anderen Artikulator isoliert:
  - "pa-pa-pa" → Lippenschluss
  - "ta-ta-ta" → Zungenspitze/harter Gaumen (alveolar)
  - "ka-ka-ka" → Zungenrücken/weicher Gaumen (velar)
  Das erlaubt später eine **artikulatorspezifische Schweregrad-Einordnung** statt nur einem
  Gesamtwert — direkt nützlich für das Dysarthrie-Fernziel ("wo genau liegt das Problem").
- **Optionale Ergänzung**: zusätzlich die klassische Wechselfolge "pa-ta-ka-pa-ta-ka..."
  (ca. 10s) für die koordinierte Rate über alle drei Artikulationsorte hinweg (DDK-Rate,
  siehe Stufe 5).
- Führt zu bis zu 4 Kurzaufnahmen für diese eine Aufgabe (pa/ta/ka einzeln + kombiniert) —
  falls das zu viel wird, ggf. nur die kombinierte Folge nehmen; Priorisierung noch offen.

### Aufgabe 3 — Standardisierter Lesetext
- Bereits etabliert: "Nordwind und Sonne", erster Satz, ~10-12s (docs/lesetext_nordwind_sonne.md).
  Keine Änderung nötig, nur als dritte feste Aufgabe im Protokoll bestätigt.

### Klargestellt (2026-07-22): reines Audio, kein Video
Nutzer hat bestätigt: **nur Audio**, kein Video-Modul. Die Video-Option (Audio-Extraktion +
mögliche künftige visuelle Lippen-/Zungenanalyse) ist damit vom Tisch, nicht mehr offen.

### Unterstützte Audioformate je Gerät (muss den Patient:innen klar kommuniziert werden)
- **iPhone (Voice Memos App)**: Einstellung "Verlustfrei" → ALAC in `.m4a` (empfohlen,
  unsere Standard-Annahme bisher). Einstellung "Komprimiert" → AAC in `.m4a` (funktioniert
  technisch auch, aber nicht mehr verlustfrei — siehe docs/bugtracker.md BEFUND-02).
- **Android (Standard-"Recorder"-Apps, z.B. Google/Samsung)**: Typischerweise AAC in `.m4a`
  oder `.3gp`, geräteabhängig unterschiedlich. Unsere Pipeline ist ffmpeg-basiert und sollte
  das technisch verarbeiten können — **aber bisher noch NIE mit einer echten
  Android-Aufnahme getestet**. Vor jeder Zusage an Android-Nutzer:innen erst mit einer
  realen Beispieldatei verifizieren (gleiches Vorgehen wie schon bei anderen
  Format-Annahmen im Projekt — nicht einfach annehmen, sondern mit `ffprobe` prüfen).
- **Allgemein**: Ziel-Formate für einen künftigen Upload sind WAV oder M4A (AAC/ALAC) —
  finale, für Laien verständliche Formulierung noch offen.

### Weitere offene Punkte
- **Namensschema erweitern**: Aktuelles Schema (`task-vokal`, `task-lesetext`) müsste um
  `task-vokal-a/i/u` und `task-ddk-pa/ta/ka/pataka` ergänzt werden.
- **Patienten-Instruktionstext**: Obige Entwürfe (Aufgaben 1-3 + Geräte-/Formathinweis) sind
  ein erster Wurf, noch nicht final abgestimmt (Tonfall, exakte Wortwahl, evtl. mit
  Bebilderung/Audio-Beispiel für Laien).

## Self-Supervised-Learning-Embeddings (neue Initiative, Audit 2026-07-22)

WavLM/HuBERT/wav2vec2 liefern 512-1024-dimensionale Embeddings als "Blackbox-Signatur" für
subtile Muster, die klassische Akustik-Features verpassen könnten.

**Bewusst als eigenständiges, größeres Vorhaben markiert, nicht als "kleines Zusatzfeature"**:
- Zusätzlicher, eigenständiger Modell-Stack (ähnlich schwer wie WhisperX/torch, Chunk 5 hat
  gezeigt, dass sowas den 10GB-Server durchaus fordert — Performance-Check nötig, siehe Chunk 5).
- **Offene Grundsatzfrage vor jeder Umsetzung**: Embeddings allein sind erstmal nur Zahlenvektoren
  ohne Aussagekraft — sie brauchen entweder (a) einen Vergleichsmaßstab (z.B. Embedding-Distanz
  zwischen Aufnahmen derselben Person über Zeit) oder (b) einen trainierten Klassifikator
  (den wir mangels Patientendaten nicht haben). Ohne eine dieser beiden Verwendungen ist die
  bloße Extraktion wenig wert — **erst diese Frage klären, dann implementieren**.

## Longitudinale & klinische Aggregat-Metriken (neue Initiative, Audit 2026-07-22)

- [ ] **Δ-Metriken** (ΔF0, ΔSprechrate, ΔJitter über 30/60/90 Tage) — Berechnung selbst simpel
      (Differenz zwischen Session N und N-k), aber **aktuell keine longitudinalen Daten
      vorhanden** (nur 3 Testaufnahmen von einem Tag). Infrastruktur kann schon jetzt vorbereitet
      werden, sinnvoll nutzbar erst mit echten Mehrfach-Sessions über Zeit.
- [ ] **Klinische Indizes (Parkinson Speech Index, Dysarthria Severity Score)** — ⚠️ **Deutlicher
      Vorbehalt**: Das sind zusammengesetzte Scores mit Gewichtungen einzelner Sub-Parameter.
      Ohne Validierung gegen echte, gelabelte Patientendaten wäre ein selbst erfundenes
      Gewichtungsschema eine unbelegte klinische Aussage — genau das Prinzip, das wir im Projekt
      bereits mehrfach vermieden haben (siehe docs/literatur_review.md "Diskrepanz automatisierte
      Metriken vs. klinischer Eindruck"). **Nicht vor echten Validierungsdaten umsetzen.**

## Online-Verfügbarkeit & Self-Service-Upload (Konzept, Stand 2026-07-22)

Nutzerwunsch: Die Applikation soll irgendwann "online" laufen. Zwei unterschiedliche Ausbaustufen,
beide bewusst nur als Konzept/Idee festgehalten, noch nicht umzusetzen:

### Stufe A — Fernzugriff auf die bestehende Beelink-Installation
- Über Tailscale ist das im Grunde **bereits heute möglich** — jedes Gerät im eigenen Tailnet
  erreicht `100.67.129.76:8501` von überall, nicht nur im Heimnetz. Kein Zusatzaufwand nötig,
  nur bewusst machen, dass "online von unterwegs" schon funktioniert, solange Tailscale aktiv ist.
- Alternative: Deployment auf dem **Hetzner-Server** (neuro-vibe.de, `deploy@178.105.255.72`),
  wo bereits EEG-Navigator/CWCMS/EDF-Analyzer öffentlich (mit Passwortschutz) laufen.
  ⚠️ **Ressourcen-Check (2026-07-22)**: Hetzner hat nur **3,7GB RAM, 2 Kerne, 6,7GB freien
  Speicherplatz** (82% Disk belegt) — deutlich knapper als der Beelink (10GB RAM, 4 Kerne).
  Unser Dashboard-Image ist mit WhisperX/Torch bereits 14,6GB groß und hat auf dem Beelink
  ein 7GB-RAM-Limit gebraucht (siehe docs/bugtracker.md INFRA-BEFUND-09) — **das passt so
  nicht auf den aktuellen Hetzner-Server**, weder RAM- noch Disk-mäßig. Optionen bei Bedarf:
  (a) Hetzner-Server aufrüsten (mehr RAM/Disk), oder (b) nur die leichten Analyse-Features
  (ohne WhisperX/Transkription) dort deployen und die Transkription weiter auf dem Beelink
  laufen lassen, oder (c) beim Beelink-Deployment bleiben und nur Tailscale-Fernzugriff nutzen.

### Stufe B — Self-Service-Upload für fremde Nutzer:innen (größerer Produkt-Pivot)
Fernziel: Nutzer:innen laden ihre eigene iPhone-Aufnahme selbst hoch und bekommen die Analyse,
statt dass alles über die feste Ordnerstruktur (`data/raw/<patient_id>/...`) läuft.

- [ ] Klare Formatanforderungen kommunizieren, BEVOR hochgeladen wird (z.B. WAV oder ALAC/M4A
      verlustfrei, 48kHz, Mono/Stereo — muss noch exakt festgelegt werden, orientiert an dem,
      was `convert_and_verify.sh`/das Dashboard aktuell verarbeiten können)
- [ ] Upload-UI (Streamlit `st.file_uploader` wäre der naheliegende Baustein) statt/zusätzlich
      zur bisherigen Ordner-Auswahl
- [ ] Serverseitige Validierung + automatische Konvertierung hochgeladener Dateien (heutige
      `convert_and_verify.sh`-Logik müsste in die App selbst wandern statt nur als SSH-Skript
      zu laufen)
- ⚠️ **Datenschutz-Dimension wird hier deutlich größer**: Sobald fremde Personen eigene
  Aufnahmen hochladen, wird die bisher zurückgestellte Frage nach echter Pseudonymisierung/
  Zuordnungstabelle (siehe "Offene fundamentale Fragen" unten) sofort relevant — nicht mehr
  nur eine Frage für später. Vor einer echten Umsetzung nochmal explizit durchdenken.
- **Explizit nur Konzeptarbeit für jetzt** — kein Implementierungsauftrag.

## Später (explizit nicht Teil des aktuellen Auftrags)

- Whisper-Transkription
- OpenSMILE/eGeMAPS als Ergänzung/Vergleich zu Parselmouth
- ML-Klassifikation / longitudinale Trend-Modelle
- Lokales LLM für Verlaufsberichte
- Externes USB-Mikro als Aufnahmequelle
- Echte Pseudonymisierungs-/Zuordnungstabelle (sobald echte Testpersonen dazukommen — siehe auch
  Self-Service-Upload-Konzept oben, das genau diese Frage akut machen würde)

## Sprache: Deutsch (Muttersprache) — Konsequenzen für die Pipeline

- **Lesetext**: "Nordwind und Sonne" (docs/lesetext_nordwind_sonne.md) — Standard-IPA-Referenztext,
  phonetisch repräsentativ, ermöglicht später auch Vergleich mit anderssprachigen Aufnahmen/Literatur,
  da der Text in nahezu jeder Sprache in einer Standardversion existiert.
- **Referenz-/Normwerte**: Saarbrücken Voice Database (SVD) — 2225 deutsche Sprecher:innen (869 gesund,
  1356 pathologisch), gehaltene Vokale /a/,/i/,/u/ in normal/hoch/tief/steigend-fallend. Als deutsche
  Normwert-Basis für Stufe-1-Phonation-Features nutzbar, statt eigene Normwerte mühsam zu erheben.
- **Fortis/Lenis im Deutschen ≠ Englisch**: siehe Stufe 5 oben — Verschlussdauer statt VOT/Aspiration
  ist das primäre Unterscheidungsmerkmal deutscher Plosive.

## Fernziel: Werkzeug für Patient:innen mit Sprechstörungen (bulbäre Dysarthrie) — Konzept 2026-07-21

Nutzerwunsch: Ein Werkzeug, das hilft, Patient:innen mit **bulbärer Dysarthrie** zu verstehen —
Sprache undeutlich, Zunge kaum/nicht nutzbar, aber Stimmbildung (Kehlkopf) noch intakt.

**Priorisierte Reihenfolge (Entscheidung 2026-07-21)**: Erst **Schweregrad einordnen**
("wie stark ist die Artikulation beeinträchtigt"), NICHT versuchen, den gesprochenen Inhalt
zu entschlüsseln — deutlich realistischer als offene Spracherkennung bei schwerer Dysarthrie.

- **Ehrlicher Ausgangspunkt**: WhisperX/Whisper ist auf normale, flüssige Sprache trainiert.
  Bei schwerer Dysarthrie ist mit sehr hoher Wortfehlerrate zu rechnen (daher existieren
  dedizierte Korpora wie TORGO/UASpeech — beide Englisch, kein bekannter deutscher
  Vergleichskorpus). Unsere bisherigen Tests (27/27 Wörter) beweisen nur Funktionsfähigkeit
  bei gesunder Sprache, sagen nichts über die Zielgruppe aus.
- **Stufenverschiebung für diese Zielgruppe**: Bei "Stimmbildung intakt, Zunge eingeschränkt"
  werden die **artikulatorischen** Stufen (2: Formanten/Vokalraum, 5: Artikulationsschärfe)
  aussagekräftiger als Stufe 1 (Phonation) — Vokalraum-Zentralisierung und reduzierte
  Verschluss-Schärfe sind die erwarteten akustischen Fingerabdrücke.
- [x] Stufe 5 (Artikulationsschärfe) als erster Baustein umgesetzt — siehe oben.
- [ ] **Notwendiger nächster Schritt**: Mindestens eine echte oder bewusst nachgeahmte
      dysarthrische Testaufnahme besorgen — ohne Vergleichsdaten ist jede Kalibrierung reine
      Spekulation. Optionen: bewusst mit eingeschränkter Zungenbewegung sprechen, oder mit
      einem öffentlichen (englischen) Dysarthrie-Korpus grob vortesten.
- [ ] Geschlossenes-Vokabular-Modus (Keyword-Spotting gegen eine begrenzte Zielwortliste)
      als realistischere Alternative zu offener Transkription bei sehr schwerer Dysarthrie —
      noch nicht begonnen, eigenständiger Baustein.
- [ ] Prosodie-basierte Zusatzinformation (Silbenzahl/Rhythmus aus Stufe 3, auch wenn Wörter
      selbst unverständlich sind) als Ergänzung, nicht Ersatz.
- **Bewusst zurückgestellt**: Patienten-individuelle Modell-Kalibrierung, Fine-Tuning auf
  dysarthrischer Sprache (deutsche Trainingsdaten fehlen, eigene Erhebung wäre nötig — echte
  Patientenpopulation, eigene ethische/Einwilligungsfragen, deutlich über private
  Testaufnahmen hinaus) — beides erst relevant, wenn Schweregrad-Einordnung steht.

## Offene fundamentale Fragen (aus Konzeptphase, zu klären bevor Phase 2 beginnt)

- Wie werden Referenzbereiche/Normwerte pro Sprecher:in (Geschlecht, Alter) gepflegt?
- Wird ein "pa-ta-ka"-Task für Diadochokinese ergänzt, oder bleibt es bei den 3 Task-Typen?
- Wie wird mit der Diskrepanz zwischen automatisierten Metriken und klinisch-perzeptivem Höreindruck
  umgegangen (Konfidenzangaben statt reiner Zahlen)?
