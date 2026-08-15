# NeuroVoice AI — Backlog

Stand: 2026-07-21

## Grundprinzip

Alle Feature-Familien werden mittelfristig angegangen, aber **skaliert von einfach zu komplex** —
nicht alles auf einmal. Reihenfolge orientiert sich daran, wie gut ein Feature etabliert/validiert
ist und wie einfach es aus einem einzelnen Task-Typ zuverlässig extrahierbar ist.

## Konzept: Modul-basierte, geführte Analyse — Umsetzungsplan (2026-08-15)

Grundlegender Konzeptwechsel (Nutzer-Feedback beim eigenen Testen): weg von einer einzelnen Seite,
die für jede Aufnahme ALLE Kennwerte zeigt (viele "–"/nicht auswertbar, je nach Task-Typ), hin zu
**einem eigenen, geführten Modul pro Aufgabentyp** — jedes Modul zeigt nur, was aus dieser Aufgabe
tatsächlich analysierbar ist. Ist die konsequente UI-Umsetzung der bereits bestehenden
"Task-Batterie"/"Patienten-Testprotokoll"-Konzepte weiter unten, keine Kehrtwende.

### Finale Konzept-Entscheidungen

- **4 Module, Reihenfolge einfach→schwer** (kein Zwang, freie Navigation, Module überspringbar,
  jedes Modul optional):
  1. **Vokalisation** — /a/ gehalten (Pflicht, ASHA-Standard: mind. 2s, 3 Wiederholungen),
     optional /i/+/u/ (für spätere VSA), optional MPT ("so lange wie möglich", offene Dauer,
     beste von 3 Versuchen)
  2. **Vorlesen** — Standardtext "Nordwind und Sonne"
  3. **Spontansprache** — Ziel ~30s, gestufter Prompt ("Letzter Urlaub/Hobby" →
     Eskalations-Nachfragen "Welches Hobby? Seit wann? Warum?", als Hilfetext im Modul)
  4. **Diadochokinese** — pa/ta/ka einzeln + kombiniert
- **Take-Management**: jeder Versuch numerisch nummeriert (Versuch 1/2/3...), je Proband:in +
  Modul (+ Unteraufgabe, z.B. separat je Vokal). Vergleichsansicht über alle Versuche eines
  Moduls. **Keine Mittelung** — Nutzer:in wählt manuell den besten Versuch aus, der in den
  Gesamtbericht einfließt.
- **Mikrofonaufnahme direkt im Browser** (höchste Priorität, siehe Roadmap unten) —
  zusätzlich zu Datei-Upload, für den "Laptop zum Patienten mitnehmen"-Anwendungsfall.
- **Gesamtbericht im Laborwert-Stil**: pro Parameter Wert | Normbereich | Status (im
  Normbereich/leicht auffällig/auffällig) | Kontext-Kommentar (mit welchen Erkrankungen diese
  Auffälligkeit typischerweise assoziiert wird — rein beschreibend, ausdrücklich KEINE
  Diagnose/kein Score, siehe bereits bestehender "Klinische Indizes"-Vorbehalt oben). Alters-/
  Geschlechtsabhängigkeit ist laut Literatur real (Jitter/Shimmer/HNR/F0), aber zu umfangreich
  für einen Schritt — zweistufig: erstmal Hinweistext bei bekannten Alterseffekten, echte
  altersgebänderte Normwerte später (bräuchte SVD-Auswertung oder Referenztabellen).
- **Aphasie-/Paraphasie-Modell** (phonematisch/semantisch, kognitive Dysphasie) — explizit
  eigenständiges, deutlich späteres Vorhaben, braucht Sprachinhalts-/Fehleranalyse statt
  Akustik. Nicht Teil dieser Umsetzung.
- **Bestehende Testdatenbank/freie Auswahl bleibt erhalten** (Entwickler-/Testmodus), wird
  nach und nach durch echte Modul-Aufnahmen ersetzt, nicht sofort entfernt.

### Priorisierte Umsetzungs-Roadmap

- [x] **P0 — Mikrofonaufnahme im Browser** ✅ UMGESETZT (2026-08-15) — `st.sidebar.audio_input()`
      als dritte Eingabeoption neben "Vorhandene Aufnahmen"/"Datei hochladen" im bestehenden
      Sidebar-Flow (Phase A), teilt sich Task-Auswahl + `save_uploaded_wav()` mit dem
      Datei-Upload-Pfad (identischer Code, keine Dopplung). `sample_rate=48000` explizit
      gesetzt (Default 16kHz ist für Spracherkennung optimiert, nicht für unsere
      Analysequalität) — Signatur vor dem Schreiben direkt am laufenden Container geprüft
      (Streamlit 1.61.1, `sample_rate: int | None = 16000` bestätigt). Kein neues Paket nötig.
      Verifiziert: Regressionstest über alle 8 bestehenden Aufnahmen ohne Exception,
      Mikrofon-Modus zeigt Task-Dropdown + korrekten Hinweistext ohne Aufnahme, HTTP 200 nach
      Deploy. **Echter Mikrofon-Test im Browser deckte einen echten Blocker auf** (siehe
      docs/bugtracker.md BUG-15): Browser verweigern Mikrofonzugriff grundsätzlich auf
      unverschlüsselten HTTP-Origins — App lief nur über `http://100.67.129.76:8501`.
      **Fix**: `tailscale serve --bg http://100.67.129.76:8501` — automatisches HTTPS
      innerhalb des Tailnets (kein öffentlicher Zugriff, kein eigenes Zertifikats-Handling
      nötig). Neue Adresse: **`https://homeserver.tailaecdbb.ts.net`**. Setup brauchte
      einmalig `tailscale set --operator=maximilian` (NOPASSWD-Pattern) + einmalige
      Freischaltung von "Serve" im Tailscale-Admin-Konto (Nutzer-Bestätigung über
      login.tailscale.com). HTTP 200 über die neue HTTPS-Adresse bestätigt. **Echter
      Mikrofon-Test durch den Nutzer erfolgreich** (2026-08-15) — Aufnahme, Anzeige,
      Auswertung funktionieren, Qualität "hervorragend" (MacBook-Mikrofon). Zwei
      Nachbesserungspunkte dabei gefunden:
  - [ ] **Kosmetische Fehlermeldung nach Aufnahmeende** ("An error has occurred") — nicht
        blockierend, App bleibt funktional, siehe docs/bugtracker.md RANDNOTIZ-12. Zurückgestellt,
        im Blick behalten bei der UI-Überarbeitung direkt darunter.
  - [x] **UI-Überarbeitung Aufnahme-Bereich** ✅ UMGESETZT (siehe unten) — Recorder war in der
        schmalen Sidebar kaum bedienbar (winzige Buttons, keine Instruktion). Aus der Sidebar
        in den breiten Hauptbereich verschoben + task-spezifischer Instruktionstext direkt
        über dem Aufnahme-/Upload-Feld.
- [x] **P1 — Take-Management** ✅ UMGESETZT (2026-08-15, vorgezogen — behebt direkt BUG-16) —
      `core/module_state.py`: Nummerierung je Modul+Unteraufgabe, manuelle Auswahl des besten
      Versuchs, Löschen einzelner Versuche (Datei + Eintrag). Ergebnisse werden jetzt IMMER
      aus `st.session_state` gerendert, nicht mehr vom aktuellen Widget-Rückgabewert abhängig
      — das war der eigentliche Grund für den gemeldeten "Dateien gehen beim Navigieren
      verloren"-Bug (siehe docs/bugtracker.md BUG-16). In Vokalisation + Vorlesen umgesetzt
      und verifiziert (Auswahl-Wechsel + Löschen inkl. Datei-Löschung per `AppTest`
      durchgeklickt). Dabei zusätzlich BUG-17 gefunden+behoben (Absturz bei unabhängig
      fehlenden Formant-/Voice-Breaks-Teilwerten).
      **Noch offen**: Vergleichsansicht (alle Versuche NEBENEINANDER mit Kennwerten, aktuell
      nur Liste mit Radio-Auswahl + Metadaten) — reicht fürs Erste, echter Seite-an-Seite-
      Vergleich wäre ein weiterer kleiner Ausbauschritt.
- [x] **P2 — Modul-Grundgerüst** ✅ UMGESETZT (2026-08-15) — Umbau von Single-Page auf
      Multi-Page (`st.navigation`/`st.Page`, wie beim EDF-Analyzer). Neue Struktur:
      `app.py` nur noch schlanker Navigations-Einstiegspunkt (`st.set_page_config`/
      `apply_global_style()` zentral hier), `dashboard/views/` mit einer Datei je Seite.
      **Vokalisation komplett als Vorlage gebaut** (`views/vokalisation.py`): 3 Tabs
      (/a/ Pflicht, /i/+/u/ optional), je Tab eigene Instruktion + Mikrofon-/Upload-Wahl,
      berechnet Phonation/Dynamics/CPP/Formanten direkt nach Aufnahme, Ergebnisse landen in
      `st.session_state["module_results"]["vokalisation"]` (nur Sitzungs-Zustand, keine
      Persistenz — das ist P4). **Take-Management (P1) bewusst noch NICHT enthalten** — eine
      Aufnahme pro Teilaufgabe, erneutes Aufnehmen überschreibt die Anzeige (keine
      Mehrfachversuche/Vergleich/Auswahl "bester Versuch" bislang).
      Bestehende Single-Page-Funktionalität komplett unverändert nach `views/testdaten.py`
      verschoben ("Entwicklermodus"/"Testdaten & freie Auswahl" in der Navigation) — nichts
      verloren, wie vom Nutzer gefordert. `views/gesamtbericht.py` als vorläufige
      Rohdaten-Anzeige des Sitzungs-Zustands (`st.json`), echte Laborwert-Aufbereitung ist P5.
      Verifiziert: alle 6 Seiten einzeln headless ohne Exception, Navigation zwischen Seiten
      via `AppTest.switch_page()` ohne Exception, HTTP 200 nach Deploy.
  - [x] **Ampel-Gauges statt nackter Zahlen** ✅ NACHGEBESSERT (2026-08-15, Nutzer-Feedback
        beim Testen) — Jitter/Shimmer/HNR/CPPS zeigen jetzt dieselben Referenzbereich-Gauges
        wie der Testdaten-Modus (`core/plots.py::gauge_figure()` +
        `core/reference_ranges.py`), statt reiner `st.metric()`-Zahlen. Verifiziert per
        PNG-Export gegen echte Testdatei (Jitter 0,6% korrekt im grünen Normbereich).
- [x] **P3 — Modul 2 „Vorlesen" komplett gebaut** ✅ UMGESETZT (2026-08-15) —
      `views/vorlesen.py`, nach dem Vokalisation-Muster: Standardtext als Instruktion,
      Mikrofon-/Upload-Aufnahme, sofortige akustische Kennwerte (Artikulationsschärfe-Gauge,
      CPPS-Gauge, Formant-Streuung, Monoloudness, Intonationskontur) OHNE Transkript nötig.
      **Zusätzlich**: eigener Transkriptions-Schritt (WhisperX-Button mit Cache, wie im
      Testdaten-Modus) schaltet danach Sprechrate-Gauge + Pausen + Lexikalische Diversität
      frei — bewusst getrennt, da Transkription spürbar dauert und nicht bei jeder Aufnahme
      automatisch laufen soll. Verifiziert: alle 6 Seiten + Navigation zwischen ihnen ohne
      Exception, alle Kennwerte gegen echte Testdatei geprüft (Werte konsistent mit früher
      im Testdaten-Modus gemessenen Referenzwerten für dieselbe Datei — CPPS 7,1dB,
      Monoloudness 11,9dB, 2 Intonations-Phrasen, Sprechrate 140 WPM), Gauge-Rendering per
      PNG-Export bestätigt, HTTP 200 nach Deploy.
      Platzhalter für die restlichen 2 Module (`views/spontansprache.py`, `views/ddk.py`)
      weiterhin klar als "🚧 im Aufbau" markiert, folgen nach demselben Muster.
- [x] **P3 — Modul 3 „Spontansprache" komplett gebaut** ✅ UMGESETZT (2026-08-15) —
      `views/spontansprache.py`, identisches Muster zu Vorlesen (Take-Management, Ampel-
      Gauges, geschätzte Fortschrittsleiste bei Transkription), aber gestufter Prompt
      ("Urlaub/Hobby" + Eskalations-Nachfragen) statt Textvorlage, Ziel ~30s. Lexikalische
      Diversität (TTR/MTLD) hier besonders hervorgehoben, da bei ~30s aussagekräftiger als
      beim kurzen Lesetext-Satz — mit explizitem Hinweis, dass MTLD trotzdem noch nicht die
      Textlänge erreicht, für die es entwickelt wurde. Verifiziert: alle 6 Seiten +
      Navigation ohne Exception, akustische Kennwerte gegen echte Testdatei geprüft, Cache-
      Transkript-Pfad (Text-Anzeige, Sprechrate, TTR/MTLD) mit synthetischem Transkript
      durchgetestet (kein 1-2-minütiger Warte-Zyklus nötig für den UI-Test), HTTP 200 nach
      Deploy.
- [x] **P3 — Modul 4 „Diadochokinese" komplett gebaut** ✅ UMGESETZT (2026-08-15) —
      `views/ddk.py`, 2 Tabs wie Vokalisation (DDK kombiniert = Pflicht, DDK einzeln =
      optional), letztes Modul im Guide (motorisch anspruchsvollste Aufgabe). Kein
      Transkriptions-Schritt (keine linguistische Auswertung bei DDK nötig) — Ergebnis sofort
      nach Aufnahme verfügbar: DDK-Rate (informative Gauge, kein etablierter Normbereich),
      Regelmäßigkeit (CV), Ø Zyklus-Intervall, Artikulationsschärfe-Gauge. Verifiziert: alle
      6 Seiten + Navigation ohne Exception, Werte gegen echte Testdatei geprüft (18
      Ereignisse, CV 0,37 — identisch zu den bereits früher in dieser Session gemessenen
      Referenzwerten für dieselbe Datei), HTTP 200 nach Deploy.
      **Damit ist P3 vollständig abgeschlossen — alle 4 Guide-Module sind fertig gebaut.**
      Verbleibend aus der ursprünglichen Roadmap: P4 (persistentes Speicherschema), P5
      (Laborwert-Stil-Interpretation), P6 (Recording-Quality-Check), P7 (Audit-Parameter),
      P8 (Live-Aufnahmedauer-Farbfeedback, zurückgestellt), P9 (Transkription als
      Hintergrund-Job, zurückgestellt) sowie eine echte Vergleichsansicht mehrerer Versuche
      nebeneinander (aktuell nur Liste mit Radio-Auswahl).
- [x] **P4 — Persistentes Speicherschema + Gesamtbericht** ✅ UMGESETZT (2026-08-15) — neues
      `core/session_store.py`: Sitzungs-Zustand wird bei jeder Take-Änderung (add/delete/select
      in `core/module_state.py`) nach `derived/_sessions/<session_id>.json` geschrieben.
      Session-ID lebt in der URL (`?session=...`, `st.query_params`), NICHT in einem Login-/
      Patientensystem (gibt es noch nicht) — ein Reload derselben URL lädt die Sitzung
      zurück, `app.py` ruft `load_session_snapshot()` zentral vor `pg.run()` auf. Schema
      (Anknüpfung an Punkt 23 aus dem externen Audit, "Strukturiertes Analyse-Schema"):
      `schema_version`, `session_id`, `created_at`/`updated_at`, je Take zusätzlich
      `take_id` (Analysis-ID) + `recorded_at` (Zeitstempel) — bewusst OHNE rohe Audio-Bytes im
      JSON (die liegen schon als WAV unter `derived/_uploads/`, nur per `recording_path`
      referenziert, beim Laden neu von der Platte gelesen statt redundant gespeichert).
      `views/gesamtbericht.py` zeigt jetzt die Sitzungs-ID + strukturierte Roh-Kennwerte des
      jeweils gewählten "besten" Versuchs je Teilaufgabe (Normbereiche/Kontext-Kommentare
      bleiben P5). **Verifiziert per komplettem Schreib-Lese-Zyklus**: `add_take()` in einem
      Wegwerf-Skript aufgerufen (echte Persistenz-Logik, kein Mock), JSON-Datei-Inhalt
      geprüft (korrekt ohne `audio_bytes`), dann in einer KOMPLETT NEUEN `AppTest`-Instanz
      nur mit der Session-ID aus der URL geladen — Vokalisation UND Gesamtbericht rendern
      fehlerfrei, `audio_bytes` wird korrekt neu von der Platte gelesen (835686 Bytes echte
      WAV-Datei, obwohl beim Schreiben ein Platzhalter gespeichert war — beweist, dass
      tatsächlich neu gelesen wird statt der alte Wert einfach durchgereicht wird), F0-Wert
      exakt identisch zum Original. Regressionstest über alle 6 Seiten ohne Exception,
      HTTP 200 nach Deploy.
- [ ] **P5 — Laborwert-Stil-Interpretation**: Normbereiche + Kontext-Kommentare, erweitert
      `docs/literatur_review.md` um Krankheits-Assoziationen je Parameter.
- [ ] **P6 — Recording-Quality-Check** (bereits Prio 1 im externen Audit oben) — passt hier
      besonders gut als vorgeschalteter Schritt in jedem Modul, gerade wegen variabler
      Laptop-Mikrofonqualität.
- [ ] **P7 — Audit-Parameter einbauen**: RAP/PPQ5/APQ11, MPT, echte VSA-Formel, F0-Tremor
      (bereits im externen Audit oben priorisiert) — technisch unabhängig, können parallel zu
      P2/P3 einlaufen, sobald das jeweilige Modul (Vokalisation) steht.
- [ ] **P8 — Live-Aufnahmedauer-Farbfeedback** (Nutzer-Idee 2026-08-15, bewusst zurückgestellt,
      nur UX-Politur): während der Mikrofonaufnahme farblich anzeigen, wie lange schon
      aufgenommen wird — grün bis zur Zielsekunde (z.B. 3s für Vokale), ab ~4-5s orange, ab
      ~10s rot ("weil's unnötig ist" — Signal, dass die Aufnahme beendet werden kann/sollte).
      **Technisch unklar/zu prüfen**: `st.audio_input` liefert aktuell keinen Live-Callback
      während der Aufnahme läuft (nur das fertige Ergebnis nach Stop) — eine reine
      CSS-Lösung (wie der bestehende dezente Aufnahme-Hinweis) kann vermutlich keine
      Zeit-abhängige Farbe erzeugen, nur einen statischen "läuft"-Zustand. Bräuchte
      eventuell eigene JS-Komponente statt des nativen Widgets — erst bei Umsetzung klären.
- [ ] **P9 — Transkription als Hintergrund-Job** (Nutzer-Feedback 2026-08-15, siehe
      docs/bugtracker.md RANDNOTIZ-13) — WhisperX blockiert aktuell die komplette Browser-
      Sitzung für 1-2 Minuten, fühlt sich wie ein Absturz an. Echte Lösung bräuchte einen
      Hintergrund-Worker/eine Job-Queue statt des synchronen Aufrufs im Streamlit-Skript —
      **bewusst kein kleiner Schritt**, größerer Architektur-Umbau. Sofort-Maßnahme (bereits
      umgesetzt): Button-/Spinner-Text setzt jetzt klare Erwartung ("reagiert währenddessen
      nicht, das ist normal").
  - [x] **Geschätzte Fortschrittsleiste** ✅ UMGESETZT (2026-08-15, Nutzer-Wunsch) —
        `core/shared.py::transcribe_with_progress()`: Transkription läuft in einem
        Hintergrund-Thread, Hauptthread pollt alle 0,5s und aktualisiert eine `st.progress()`-
        Leiste basierend auf Audiodauer × empirischem Faktor, gedeckelt bei 90% bis der
        Thread tatsächlich fertig ist (verhindert falsches "100%, läuft aber noch"). **Kein
        echter Fortschritts-Callback aus WhisperX verfügbar** — bewusst nur eine Schätzung,
        UI sagt das auch so ("Schätzung kann abweichen"). Löst NICHT das eigentliche
        Blockier-Problem (App reagiert trotzdem nicht, das bleibt P9/RANDNOTIZ-13) — nur
        ehrlicheres Warten statt unbestimmtem Spinner. In `views/vorlesen.py` UND
        `views/testdaten.py` einheitlich eingebaut. Empirischer Faktor bei der Umsetzung
        direkt kalibriert: 38s für 11,5s Audio (~3,3x Echtzeit) bei einem frischen Testlauf,
        deutlich schneller als frühere Messungen (83-96s für ~10-12s Audio, ~7-9x) — auf 5x
        als Kompromiss gesetzt, Deckelung fängt Abweichungen ab. Verifiziert: Thread-/Timing-
        Logik gegen echte Datei erfolgreich getestet (Transkription lief korrekt im
        Hintergrund, kein Blockieren des Pollings), Regressionstest über alle 6 Seiten ohne
        Exception, HTTP 200 nach Deploy.

### Benchmark-Datensätze (Recherche 2026-08-15, nur Referenz — Lizenzen vor Nutzung prüfen)

Priorisiert nach Sprache (Deutsch/Englisch deutlich wertvoller als andere Sprachen für unser
Projekt):

- **Saarbrücker Voice Database (SVD)** — Deutsch, bereits als primäre Referenz geplant (869
  gesund, 1356 pathologisch, /a/,/i/,/u/ in 4 Tonlagen)
- **Oxford/UCI Parkinson Voice Dataset** — Englisch, klassisch, 23 Parkinson + 8 gesund,
  gehaltene Vokale + Sätze
- **MDVR-KCL** — Englisch, Mobilgerät-Aufnahmen, früh+fortgeschritten Parkinson + gesund
- **VOC-ALS** — Sprache unklar/zu prüfen, 51 gesund + 102 ALS unterschiedlicher
  Dysarthrie-Schwere, Vokale + Silbenwiederholung/DDK
- Nachrangig (nicht Deutsch/Englisch, trotzdem als Vergleichsquelle vermerkt): **NeuroVoz**
  (Spanisch, Parkinson, Vokale+DDK+Spontansprache inkl. GRBAS), **VD Dataset**,
  **Parkinson Speech Dataset** (Türkisch)

## Phase 1 — Aufnahme-Pipeline (aktuell)

- [x] Syncthing auf Beelink-Server installiert (Docker, Tailscale-only, Discovery/Relay deaktiviert) — siehe homeserver-Repo LOG.md 2026-07-21
- [x] ffmpeg auf Server installiert
- [x] Syncthing auf iPhone eingerichtet (Möbius Sync), Pairing mit Server abgeschlossen und verifiziert (siehe homeserver-Repo LOG.md + services/syncthing/README.md für Troubleshooting)
- [x] Ordnerstruktur angelegt: `~/neurovoice-data/raw-inbox` (Syncthing-Ziel) getrennt von `~/neurovoice-data/raw/<patient_id>/...` (final) — auf dem Server, nicht im Git-Repo
- [x] Konvertierungsskript: `.m4a` (ALAC) → `.wav`, verlustfrei (Dekodierung, kein Re-Encoding) — `scripts/convert_and_verify.sh`, deployed auf Server
- [x] Verifikationsskript: `ffprobe`-Check (Codec/Samplerate/Bittiefe) + Checksumme vor/nach Transfer — im selben Skript enthalten
- [x] Erste Testaufnahme komplett durch die Pipeline (Vokal-Task, später zu Lesetext korrigiert, da tatsächlicher Inhalt der Nordwind-Satz war — Namenskonvention beim Umbenennen in Voice Memos auf Leerzeichen statt Unterstriche achten)
- [x] **Testdatenbank erweitert (2026-07-24)** — 5 neue Kurzaufnahmen über Möbius Sync
      integriert (unterwegs, Tailscale-Route `homeserver-fern`): Spontansprache (Wandertour-
      Beschreibung), DDK kombiniert ("pataka" schnell wiederholt), DDK einzeln (pa/ta/ka
      sequentiell in einer Aufnahme statt 3 getrennten Dateien — Wortliste zur Ort-der-
      Artikulation-Differenzierung fehlt weiterhin), gehaltene Vokale /i/ und /u/ (ergänzen
      das bereits vorhandene /a/ aus dem Lesetext). Dateien kamen mit unbrauchbaren Namen
      an (z.B. "Pataka gesund.m4a") — vor Konvertierung ins Schema `<patient_id>_task-<typ>_
      take<n>` umbenannt: `spontan`, `ddkgemischt`, `ddkeinzeln`, `vokali`, `vokalu`. Alle 8
      Aufnahmen (3 alt + 5 neu) headless via AppTest ohne Exception durchlaufen. Restliche
      offene Wortliste für Ort-der-Artikulation steht weiter aus.
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
- [ ] Vokalraum-Plot (F1/F2) für Vokal-Task — braucht mehrere unterschiedliche Vokale, jetzt
      als getrennte Aufnahmen statt einer kombinierten Aufnahme (Konzept angepasst). **Stand
      2026-07-24**: /i/ und /u/ liegen jetzt als eigene Testaufnahmen vor (`vokali`/`vokalu`,
      formant_features() liefert für beide plausible F1/F2-Werte), aber /a/ fehlt weiterhin
      als isolierte gehaltene Vokal-Aufnahme (bisherige "vokal"-Aufnahme stellte sich als
      Lesetext heraus, siehe Projekt-Historie) — echte Vokalraum-Fläche (VSA) braucht alle
      3 Eckvokale, bewusst NICHT mit nur 2 von 3 Punkten vorgetäuscht. Nächster Schritt:
      eine gehaltene /a/-Aufnahme (`vokala`), dann VSA per Dreiecksformel umsetzbar.
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

## Design-System-Transfer vom EDF-Analyzer ✅ UMGESETZT (2026-08-15)

Übertragung des Apple-artigen Redesigns (siehe EDF-Analyzer-Repo, `[[project_edf_ui_redesign]]`)
auf NeuroVoice AI — gleiche Design-Tokens, damit alle eigenen Streamlit-Apps optisch
zusammengehören. Bewusst als EIN Schritt umgesetzt statt phasenweise wie beim EDF-Analyzer
(dort ~10 Seiten, hier nur 1 Seite — Aufwand/Nutzen-Verhältnis anders).

- [x] `core/design_tokens.py` — Farb-/Radius-/Typografie-/Spacing-Konstanten, Werte identisch
      zum EDF-Analyzer übernommen (Apple Blue `#0071e3` Akzent, Off-White `#f5f5f7`, near-black
      Text `#1d1d1f`)
- [x] `core/shared.py::apply_global_style()` — CSS-Variablen + Utility-Klassen
      (`.dw-eyebrow`/`.dw-hero-title`/`.dw-subtitle`/`.dw-card`). Bewusst KEIN eigenes
      Font-Hosting (anders als EDF-Analyzer mit lokalem Inter) — nur Systemschriften
      (-apple-system/SF Pro), kein CDN-Request, passt zum Datenschutz-Prinzip des Projekts
- [x] `.streamlit/config.toml` neu angelegt — Theme-Werte gespiegelt + `maxUploadSize=25`
      als zweite, unabhängige Schranke zusätzlich zur eigenen Prüfung in `save_uploaded_wav()`
- [x] `core/reference_ranges.py` — GOOD/WARNING/CRITICAL/NEUTRAL auf dieselben kanonischen
      Töne wie der EDF-Analyzer umgestellt (SUCCESS/WARNING/DANGER/TEXT_SECONDARY aus
      design_tokens), fachliche Bedeutung unverändert
- [x] `core/plots.py` — Wellenform/Intensitätskurve/Gauge/Radar auf Tokens umgestellt.
      **Bewusst NICHT angefasst**: die F0-/Formant-Overlay-Farben im Spektrogramm — die sind
      funktional gegen die "afmhot"-Colormap kontrastgewählt, keine Marken-/Chrome-Farbe
      (gleiche Begründung wie beim EDF-Analyzer, der sein dunkles EEG-Viewer-Theme aus
      demselben Grund unberührt ließ)
- [x] `app.py` — Titel auf Eyebrow+Hero-Title+Subtitle-Muster umgestellt statt `st.title()`

**Verifiziert**: `py_compile` über alle geänderten Dateien sauber, Regressionstest über alle
8 bestehenden Aufnahmen headless via AppTest ohne Exception, HTTP 200 nach Deploy. Gauge-/
Radar-/Wellenform-/Intensitäts-Diagramme als PNG aus dem Container exportiert und visuell
geprüft (Ampelfarben grün/orange/rot statt der alten Töne, Apple-Blau statt vorherigem Blau,
Daten unverändert/nicht korrumpiert durch die Farbänderung).

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
- [x] **MFCCs (allgemeine Klangfarbe)** ✅ UMGESETZT (2026-07-22) — `mfcc_features()`, Praats
      natives "To MFCC"-Kommando, nur stimmhafte Frames. **Wichtiger Befund**: MFCC 1-4
      streuen zwischen den 3 Testaufnahmen deutlich mehr als andere Kennzahlen (z.B.
      Formanten) — vermutlich Aufnahmebedingungen (Mikrofonabstand/Raumakustik), nicht echte
      Sprechunterschiede. MFCCs sind literaturbekannt kanal-/mikrofonempfindlich — Werte
      v.a. innerhalb derselben Session vergleichbar, im Dashboard entsprechend markiert.
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
- [x] **Diadochokinetische Rate** ✅ UMGESETZT (2026-07-24) — siehe Stufe 5 unten
      (`ddk_rate_features()`), jetzt mit echten DDK-Testaufnahmen möglich.
- [x] **Mikro-/Makropausen-Verteilung** (Audit 2026-07-22, umgesetzt 2026-07-22) — Pausen nach
      Dauer klassifiziert (Schwelle 500ms): Mikropausen (normale Atem-/Wortgrenzen) vs.
      Makropausen (auffällige Zögerungen/Wortsuche), getrennt ausgewertet in
      `compute_speech_metrics()`. Verifiziert mit synthetischer Wortliste + headless gegen Take 3.
- [ ] **Filled Pauses ("äh", "mhm") und Selbstkorrekturen/Wortabbrüche** (Audit 2026-07-22) —
      ⚠️ **Wichtiger Vorbehalt vor Zusage**: WhisperX/Whisper-Modelle neigen bekanntermaßen dazu,
      Füllwörter/Disfluencies beim Transkribieren zu glätten/wegzulassen (Trainingsdaten-bedingt) —
      muss erst an einer echten Spontansprache-Aufnahme geprüft werden, ob das übliche
      Transkript sie überhaupt enthält, bevor wir das als zuverlässiges Feature versprechen.
      **Vorbehalt bestätigt (2026-07-24)**: erste echte Spontansprache-Aufnahme transkribiert
      komplett füllwortfrei, obwohl das bei freier Rede untypisch ist — siehe
      docs/bugtracker.md RANDNOTIZ-11. Feature bleibt deshalb weiter zurückgestellt.

### Stufe 4 — Prosodie/Sprechweise ✅ IM DASHBOARD UMGESETZT (2026-07-21)
- [x] Monopitch-Maß (SD F0 über Äußerung) — wiederverwendet aus Stufe 1 (Phonation-Tabelle), keine doppelte Berechnung
- [x] Monoloudness (SD Intensität) — `prosody_features()`, verifiziert an allen 3 Testaufnahmen (10,9-12,7 dB)
- [x] Rhythmus (nPVI) — `speech_metrics.py`, Näherung auf Wortebene (keine Silbensegmentierung), Teil der Sprechfluss-Metriken
- **Bug unterwegs gefunden+behoben**: Praat-Sentinel -300dB (Stille) verzerrte den ersten Monoloudness-Wert massiv (26,18 statt 12,75 dB) — betraf auch die Lautstärkekurve. Siehe docs/bugtracker.md BUG-11.
- [x] **Intonationskontur-Analyse** ✅ ERSTER WURF UMGESETZT (2026-07-22) —
      `intonation_contour_features()`, Segmentierung rein akustisch über Lücken in der
      stimmhaften Pitch-Kontur (kein Transkript nötig, anders als ursprünglich angenommen),
      linearer F0-Trend pro Phrase klassifiziert als steigend/fallend/flach. Verifiziert an
      allen 3 Takes: 2-4 Phrasen, überwiegend fallender Trend (konsistent mit dem bereits
      gefundenen negativen Gesamt-Pitch-Slope). **Bewusst nur erster Wurf**: linearer Trend,
      keine Krümmungsanalyse — das wäre ein größerer Ausbauschritt, noch offen.
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
- [x] **Diadochokinese-Rate (DDK-Zyklen/Sekunde, "pa-ta-ka")** ✅ UMGESETZT (2026-07-24) —
      `ddk_rate_features()` in `core/audio.py`, nutzt bewusst dieselbe (unveränderte)
      Verschluss-/Burst-Erkennung wie `articulation_features()` (Täler in der
      Intensitätskontur, gleiche Prominence-/Plausibilitätsschwellen), liefert Rate
      (Zyklen/Sekunde) UND Regelmäßigkeit (Variationskoeffizient der Zyklus-Intervalle —
      unregelmäßige DDK-Raten gelten in der Literatur als möglicher Hinweis auf ataktische
      Dysarthrie). Verifiziert an den neuen DDK-Testaufnahmen: `ddkgemischt` 3,4 Hz/CV 0,37,
      `ddkeinzeln` 2,3 Hz/CV 0,69 (höherer CV plausibel erklärbar — die "einzeln"-Aufnahme
      enthält mehrere Teilblöcke mit Pausen dazwischen statt eines durchgehenden Zyklus,
      siehe Caveat in der Dashboard-Tabelle). Kontrollen (Lesetext ~2,8 Hz, Vokal-Aufnahmen
      korrekt "–" wegen zu weniger Zyklen) unauffällig. Headless via AppTest über alle 8
      Aufnahmen ohne Exception bestätigt.
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

- [x] **Lexikalische Diversität (TTR, MTLD)** ✅ UMGESETZT (2026-07-24) — neues Modul
      `core/linguistics.py`, bewusst OHNE spaCy: nutzt die von WhisperX ohnehin schon
      segmentierten Wörter als Tokens (regex-Normalisierung auf Kleinbuchstaben/
      Satzzeichen-frei), kein neuer NLP-Stack nötig. TTR = Types/Tokens, MTLD bidirektional
      (vorwärts+rückwärts gemittelt, Standardschwelle 0.72 nach McCarthy & Jarvis 2010).
      Verifiziert headless via AppTest an allen 3 Testaufnahmen (identisch, da alle den
      gleichen Nordwind-Satz vorlesen: TTR 0,96, MTLD 204,1) sowie an synthetischen
      Testfällen (repetitiver Text → niedrige TTR/MTLD, komplett unterschiedliche Wörter →
      hohe TTR/MTLD, Satzzeichen-/Groß-Kleinschreibung verfälscht TTR nicht). **Wichtiger
      Vorbehalt, im Dashboard vermerkt**: MTLD wurde für deutlich längere Texte entwickelt
      (Literatur empfiehlt >100 Wörter) — bei unseren ~10s-Snippets (~15-30 Wörter) bleibt
      die TTR meist durchgehend über der Schwelle, wodurch MTLD auf einen Wert nahe der
      Tokenzahl "deckelt" (kein Bug, bekannte Grenze des Verfahrens bei kurzen Texten).
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

## Externes wissenschaftliches Audit 2026-08-15

Nutzer hat eine ausführliche externe Fachkritik eingebracht (multimodales 8-Ebenen-Konzept,
Praat-Erweiterungen, Recording-Quality-Pflichtmodul, Longitudinal-Fokus, ML-Architektur).
Jeder Kritikpunkt wurde **gegen den tatsächlichen Code geprüft**, nicht blind übernommen —
wichtiges Ergebnis: ein erheblicher Teil der "Korrekturen" betraf Dinge, die wir nie so gebaut
hatten bzw. die bei uns bereits richtig sind.

### Geprüfte "Korrekturen" — Ergebnis: bei uns bereits korrekt bzw. nie so vorhanden

- **HNR-Interpretation**: Kritik unterstellte eine "verdrehte" Interpretation (hohes HNR =
  Rauschen). **Bei uns nie so gewesen** — Glossar (`app.py`) sagt korrekt "Höher = klarere
  Stimme", `hnr_zones()` bewertet >20dB als gut, <15dB als auffällig. Kein Fix nötig.
- **Jitter/Shimmer als zentrale Biomarker**: Kritik empfiehlt, sie nicht als globale
  Hauptmarker zu behandeln, CPP zu bevorzugen. **Bereits so umgesetzt** seit dem
  Normwert-Ampel-Konzept (2026-07-21/22): Jitter/Shimmer laufen klein/muted unter "braucht
  gehaltenen Vokal", CPP läuft groß/vorne unter "immer auswertbar" (Stufe 6, `cpp_features()`).
- **Sprechrate vs. Artikulationsrate trennen**: **Bereits umgesetzt** —
  `speech_metrics.py::compute_speech_metrics()` liefert `net_speech_rate_wpm` UND
  `articulation_rate_wpm` getrennt, seit Chunk 3 (2026-07-21).
- **Phänotyp/Score statt Diagnose, keine unvalidierten Gewichtungsscores**: **Bereits
  Projekt-Prinzip**, siehe "Klinische Indizes"-Eintrag oben (Vorbehalt seit 2026-07-22) und
  README ("Kein Diagnose-KI-Ersatz"). Kein aktuelles ML-Modell im Projekt, das eine
  Fehlinterpretation überhaupt zulassen würde.
- **"Acoustic Nasality Index" statt echter "Nasalance"**: Kritik bezieht sich auf ein
  einfaches <500Hz/>500Hz-Energieverhältnis als Nasalitätsmaß. **Bei uns nie implementiert**
  — wir haben aktuell KEIN Nasalitäts-/Resonanz-Feature. Wichtiger Hinweis für den Fall, dass
  das mal gebaut wird: dann von Anfang an als "Acoustic Nasality Index" benennen, nicht als
  "Nasalance" (echte Nasalance bräuchte kalibrierte Instrumentalmessung).
- **Patient-Level-Split für ML (keine Aufnahmen derselben Person in Train UND Test)**:
  aktuell nicht relevant (kein ML-Modell vorhanden), aber wichtiger Grundsatz für den Tag,
  an dem eines gebaut wird — hier vermerkt, nicht vergessen.

### Echte, neu identifizierte Lücken — priorisiert nach Aufwand

**Prio 1 — kleine Schritte, kein neuer Tech-Stack (nutzen vorhandene Praat-Infrastruktur):**
- [ ] **RAP, PPQ5, APQ11** — feinere Jitter-/Shimmer-Untermaße. Technisch trivial: nutzen
      denselben `point_process` (`"To PointProcess (periodic, cc)"`), der in
      `phonation_features()` schon für Jitter/Shimmer local existiert — nur zusätzliche
      `praat.call(point_process, "Get jitter (rap)"/"Get jitter (ppq5)", ...)`-Aufrufe nötig.
- [ ] **Maximum Phonation Time (MPT)** — wie lange kann ein gehaltener Vokal ohne Unterbrechung
      gehalten werden. Einfach aus stimmhafter Dauer der Vokal-Aufnahmen ableitbar (gleiche
      Grundlage wie `phonation_dynamics_features()`s Voice-Breaks-Erkennung), kein neues Modell.
      Braucht Vokal-Task mit klarer Instruktion "so lange wie möglich halten" — aktuelle
      Vokal-Aufnahmen (vokali/vokalu, 2026-07-24) waren nicht auf maximale Dauer instruiert,
      neue MPT-spezifische Aufnahme sinnvoll.
- [ ] **Vokalraum-Fläche (VSA), echte Dreiecksformel** — bereits als offener Punkt vermerkt
      (siehe Stufe 2 oben), jetzt technisch möglich seit /a/(aus Lesetext)/i//u/ als separate
      Aufnahmen vorliegen (2026-07-24) — fehlt nur noch die Umsetzung selbst, keine neuen Daten.
- [ ] **Recording Quality Check** (vereinfachte Vorstufe zum vorgeschlagenen "RQI 0-100"):
      SNR-Näherung, Clipping-Anteil, Stille-Anteil — aus bereits vorhandenen `basic_stats()`-
      Rohdaten ableitbar (Peak/RMS dBFS sind schon da), kein neuer Tech-Stack. **Wichtig, aber
      bewusst nicht als hartes Cutoff-Gate umsetzen** (Prinzip aus
      [[feedback_signalverarbeitung_kennwerte]]: erst an echten Aufnahmen kalibrieren, bevor
      etwas als "schlecht" markiert wird) — erst informativ anzeigen, Schwellen später schärfen.

**Prio 2 — moderater Aufwand, baut auf vorhandenen Daten/Funktionen auf:**
- [ ] **F0-Tremor-Analyse** (FFT/PSD der F0-Zeitreihe, Tremor-Peak-Frequenz/-Amplitude/-Power)
      statt nur F0-SD — nutzt dieselbe F0-Zeitreihe wie `phonation_dynamics_features()`, aber
      neue Analyse (Detrending + Spektralanalyse der Tonhöhenkurve selbst, nicht des Audios).
      Interessant für Parkinson- vs. essenziellen-Tremor-Differenzierung laut Kritik.
- [ ] **Formant-Übergangsraten bei definierten Vokalwechseln** (z.B. /a/→/i/, F2-Slope in
      Hz/ms) — Erweiterung von `formant_dynamics_features()`, das bisher nur globale
      Geschwindigkeit über eine ganze Aufnahme misst, nicht gezielt an einem Vokalübergang.
      Bräuchte eine neue Aufgabe (z.B. "aaa-iii-aaa" in einer Aufnahme) statt reiner
      Einzelvokale.
- [ ] **Standardisiertes Aufnahmeprotokoll erweitern**: MPT-Task, Sätze mit gezielt
      unterschiedlichen Artikulationsorten (bilabial/alveolar/velar/Frikative) — ergänzt das
      bereits bestehende Patienten-Testprotokoll-Konzept oben (Aufgabe 1-3).

**Prio 3 — neuer Tech-Stack, größerer Aufwand:**
- [ ] **openSMILE eGeMAPSv02** als standardisierter Feature-Block (ergänzt, ersetzt nicht die
      eigenen Parselmouth-Features) — neue Python-Abhängigkeit, muss gegen die
      Server-Ressourcen geprüft werden (siehe Chunk-5-Lehre bei WhisperX).
- [ ] **Speech-Intelligibility-Score (WER/CER)** — ASR-Text (WhisperX, bereits vorhanden) gegen
      erwarteten Text vergleichen (bei standardisierten Aufgaben wie Lesetext/DDK bekannt).
      Braucht Referenztext-Hinterlegung pro Task + Editierdistanz-Berechnung.
- [ ] **Silero VAD** als Ersatz/Ergänzung zur bisherigen Intensitäts-basierten Stimm-/Pause-
      Erkennung — leichtgewichtig, lokal/ONNX-fähig, aber neue Abhängigkeit, Nutzen gegenüber
      der bestehenden Lösung (Intensitätsschwellen aus Praat) noch nicht belegt.
- [ ] **wav2vec2/WavLM-Embeddings** — bereits als eigenständige Initiative oben vermerkt
      ("Self-Supervised-Learning-Embeddings"), Grundsatzfrage weiterhin ungeklärt.

**Prio 4 — strukturell, braucht Longitudinal-Daten bzw. DB-Umbau:**
- [ ] **Strukturiertes Analyse-Schema statt reiner Tabelle** (Analysis-ID, Recording-Hash,
      Feature-Versionierung, Zeitstempel) — für Reproduzierbarkeit, falls das Projekt über
      die eigene Testphase hinauswächst. Aktuell nicht dringend (1 Proband, kein Reporting-
      Bedarf über eine Sitzung hinaus).
- [ ] **Longitudinal-Tracking/Δ-Metriken** — bereits oben vermerkt, wartet weiterhin auf echte
      Mehrfach-Sessions über Zeit (aktuell alle 8 Testaufnahmen von 2 Tagen, kein echter
      Verlauf).

### Nicht übernommen / bewusst zurückgestellt

ML-Klassifikation (XGBoost/SHAP), Deep-Learning-Embeddings als Klassifikator, "Hypokinetic/
Bulbar/Ataxic Score"-Konstrukte — passen zum "Später"-Abschnitt unten (explizit nicht Teil
des aktuellen Auftrags) UND zum bereits bestehenden Vorbehalt bei "Klinische Indizes" oben:
ohne echte, gelabelte Patientendaten wäre jede Gewichtung/jeder Score unbelegt. Die Grund-
Philosophie der externen Kritik (Ebene A "Messung" / B "Phänotyp" / C "Ätiologie" strikt
trennen) deckt sich mit unserem bisherigen Vorgehen, ändert aber nichts an der Priorisierung.

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
- [x] **Upload-UI, Phase A Schritt 1** ✅ UMGESETZT (2026-08-14) — Sidebar-Umschalter
      "Vorhandene Aufnahmen" vs. "Datei hochladen (WAV)", `st.file_uploader` + neue Funktion
      `save_uploaded_wav()` in `core/audio.py` (bewusst als reine, von Streamlit getrennte
      Funktion, da AppTest `file_uploader`-Interaktion nicht unterstützt). Validiert: leere
      Datei, ungültiges/kein WAV, >25MB, Pfad-Traversal im Dateinamen (sanitisiert) — alle
      4 Fehlerfälle + Erfolgsfall isoliert getestet. Uploads landen in eigenem Namespace
      `derived/_uploads/` (NICHT im read-only `/data`-Mount, NICHT vermischt mit echten
      Testaufnahmen). Task-Typ ist bei Uploads noch `"unbekannt"` (nutzt den bereits
      bestehenden Fallback aus `list_recordings()`) — echte Task-Typ-Abfrage ist der nächste
      Schritt. Regressionstest: alle 8 bestehenden Aufnahmen weiterhin ohne Exception via
      AppTest, End-to-End-Test (Upload → basic_stats/phonation_features) auf echter Datei
      erfolgreich, Daten bit-identisch nach Upload-Roundtrip. Ein kosmetischer Bug beim
      Testen gefunden+behoben (Einheiten-Mismatch in der Größenlimit-Fehlermeldung, siehe
      docs/bugtracker.md BUG-14).
- [x] **Task-Typ-Abfrage, Phase A Schritt 2** ✅ UMGESETZT (2026-08-15) — Dropdown
      "Was wurde aufgenommen?" beim Upload (`UPLOAD_TASK_LABELS` in `core/audio.py`: Lesetext/
      Vokal a-i-u/DDK kombiniert/DDK einzeln/Spontansprache/Unbekannt), `save_uploaded_wav()`
      um `task`-Parameter erweitert — validiert gegen die feste Liste, fällt bei unbekanntem
      Wert sicher auf `"unbekannt"` zurück (verifiziert: gültiger Task, ungültiger Task,
      kein Task angegeben). Damit greift die Ampel-/Fit-Logik bei Uploads jetzt genauso wie
      bei den eigenen Testaufnahmen. Regressionstest bestanden (alle 8 Aufnahmen weiterhin
      ohne Exception).
- [ ] Serverseitige Validierung + automatische Konvertierung hochgeladener Dateien (heutige
      `convert_and_verify.sh`-Logik müsste in die App selbst wandern statt nur als SSH-Skript
      zu laufen)
- ⚠️ **Datenschutz-Dimension wird hier deutlich größer**: Sobald fremde Personen eigene
  Aufnahmen hochladen, wird die bisher zurückgestellte Frage nach echter Pseudonymisierung/
  Zuordnungstabelle (siehe "Offene fundamentale Fragen" unten) sofort relevant — nicht mehr
  nur eine Frage für später. Vor einer echten Umsetzung nochmal explizit durchdenken.
- **Explizit nur Konzeptarbeit für jetzt** — kein Implementierungsauftrag.

### Konkretisierung Stufe B (Konzept, 2026-07-22): Tailscale-Freigabe + 10s-Upload-Pipeline

Nutzer-Präzisierung: Zugriff soll NICHT komplettes öffentliches Internet sein, sondern gezielt
**einzelne Personen über Tailscale** — die bekommen Zugriff aufs Tool, aber nicht automatisch
auf die anderen Heimnetz-Dienste (Immich, Paperless etc.).

**Zugriffsmodell (zu prüfen)**: Tailscale bietet eine "Share"-Funktion, mit der einzelne
Geräte/Nodes gezielt mit fremden Tailscale-Konten geteilt werden können, ohne die Person ins
eigene Tailnet aufzunehmen (anders als "jeder im eigenen Tailnet erreicht alles"). Muss noch
verifiziert werden, ob sich das so granular auf einen einzelnen Dienst/Port einschränken lässt
oder nur auf ganze Geräte — falls nur ganze Geräte teilbar sind, wäre ein dediziertes,
isoliertes Gerät/Container nur für NeuroVoice sauberer als das gesamte Beelink-Gerät zu teilen.

**Upload-Pipeline-Skizze (Konzept, kein Code)**:
1. `st.file_uploader` (WAV/M4A) statt/zusätzlich zur Ordner-Auswahl in der Sidebar
2. **Dauer-Validierung**: Toleranzbereich um die Ziel-Dauer 10s (z.B. 7-13s) — außerhalb davon
   klare Fehlermeldung statt stiller Fehlanalyse ("Bitte eine Aufnahme zwischen 7 und 13
   Sekunden hochladen, aktuell: X Sekunden")
3. **Task-Typ-Abfrage**: Bei eigenen Uploads ist (anders als bei der bisherigen Ordnerstruktur)
   nicht bekannt, ob es ein Vokal/Lesetext/DDK-Task war — müsste aktiv erfragt werden (z.B.
   Auswahlfeld), damit die Ampel-Einordnung (Tier A/B/"nur Vokal") korrekt angewendet wird und
   nicht z.B. Jitter/Shimmer bei einem Lesetext-Upload fälschlich mit Ampel gezeigt wird
4. Automatische Konvertierung + Verifikation (heutige `convert_and_verify.sh`-Logik direkt in
   die App integriert statt SSH-Skript)
5. Analyse mit den bestehenden Funktionen (`phonation_features()`, `formant_features()` etc.)
   — technisch keine neue Analyse-Logik nötig, nur ein neuer Zugangsweg zu den Daten
6. **Aufbewahrung bewusst anders als bei den eigenen Testaufnahmen**: Fremde Uploads NICHT
   automatisch dauerhaft in `data/raw/` ablegen — eher temporär verarbeiten und nach der
   Session löschen, außer die Person stimmt einer dauerhaften Speicherung aktiv zu (Konsens-
   Frage, noch nicht ausformuliert)

**Weiterhin offen**: exakte Formatliste, finaler Instruktionstext, Einwilligungstext vor
Upload, ob überhaupt ein Klarname/Pseudonym abgefragt wird oder komplett anonym verarbeitet wird.

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
