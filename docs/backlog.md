# NeuroVoice AI — Backlog

Stand: 2026-07-21

## Grundprinzip

Alle Feature-Familien werden mittelfristig angegangen, aber **skaliert von einfach zu komplex** —
nicht alles auf einmal. Reihenfolge orientiert sich daran, wie gut ein Feature etabliert/validiert
ist und wie einfach es aus einem einzelnen Task-Typ zuverlässig extrahierbar ist.

## ⚠️ Immer beachten beim Testen (Live-URL)

**Für Browser-Tests mit Mikrofon NIEMALS die rohe Tailscale-IP `<TAILSCALE-IP>:8501` geben.**
Browser verweigern `getUserMedia` (Mikrofonzugriff) auf unverschlüsseltem HTTP/IP-Origins.
Stattdessen immer: **`https://<TAILSCALE-HOSTNAME>`** (HTTPS via `tailscale serve`,
seit BUG-15/2026-08-15 eingerichtet, dauerhaft aktiv auf dem Server). Die IP-Adresse
funktioniert weiterhin für alles außer Mikrofon. Siehe auch G1 unten (dieselbe Wurzelursache,
aber für Fremd-Nutzer ohne unsere Tailscale-Infrastruktur — dort noch ungelöst).

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
      unverschlüsselten HTTP-Origins — App lief nur über `http://<TAILSCALE-IP>:8501`.
      **Fix**: `tailscale serve --bg http://<TAILSCALE-IP>:8501` — automatisches HTTPS
      innerhalb des Tailnets (kein öffentlicher Zugriff, kein eigenes Zertifikats-Handling
      nötig). Neue Adresse: **`https://<TAILSCALE-HOSTNAME>`**. Setup brauchte
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
- [x] **P5 — Laborwert-Stil-Interpretation** ✅ UMGESETZT (2026-08-15) —
      `docs/literatur_review.md` um Abschnitt "Krankheits-Assoziationen je Parameter" erweitert
      (deskriptiv, angelehnt an die klassische Dysarthrie-Typologie nach Darley/Aronson/Brown
      1969), neues `core/interpretation.py` mit `PARAMETER_INFO` (Label/Einheit/Normbereich-
      Funktion falls vorhanden/Kontext-Kommentar/Alters-Hinweis) für 11 Kern-Parameter über
      alle Module (Monopitch, Jitter, Shimmer, HNR, CPPS, Sprechrate, Artikulationsschärfe,
      Monoloudness, DDK-Rate, DDK-Regelmäßigkeit, Pausenzahl). `views/gesamtbericht.py`
      rendert jetzt pro Modul+Teilaufgabe eine echte Laborwert-Tabelle (Wert | Normbereich |
      Status | Kontext) statt Roh-JSON, plus expliziter Hinweis-Banner ("rein beschreibend,
      keine Diagnose") und Alters-/Geschlechts-Caveat wo einschlägig. **Bewusst rein
      deskriptiv** (Nutzer-Vorgabe) — Kontext-Kommentare sagen, womit ein Muster ASSOZIIERT
      wird, nie was es BEDEUTET. Nur Parameter mit etablierten Zonen (Jitter/Shimmer/HNR/
      Sprechrate) bekommen einen Ampel-Status, alle anderen zeigen "kein Normwert" mit
      Kontext. Verifiziert: `interpret()` isoliert getestet (inkl. unbekannter Parameter,
      `None`-Werte), End-to-End über echten Schreib-Lese-Zyklus (Vokalisation + DDK) — alle
      Werte/Status/Normbereiche korrekt, identisch zu früher in dieser Session gemessenen
      Referenzwerten, Alters-Caveat erscheint korrekt. Regressionstest über alle 6 Seiten
      ohne Exception, HTTP 200 nach Deploy.
  - [x] **Nachbesserung (2026-08-15, Nutzer-Feedback)**: Visualisierungen (Wellenform/
        Lautstärke/Spektrogramm mit F0+Formant-Tracks) — die es nur im alten Testdaten-Modus
        gab — in alle 4 Guide-Module zurückgebracht (`waveform_figure`/`intensity_figure`/
        `spectrogram_figure` aus `core/plots.py`, wiederverwendet). Interpretations-Tabelle
        (P5) läuft jetzt NICHT mehr nur im Gesamtbericht, sondern DIREKT auf jeder Modul-
        Seite, wo aufgenommen/analysiert wird ("Was bedeuten diese Werte?" direkt unter den
        Kennwerten). `core/interpretation.py` um `description`-Feld ("Was es misst") pro
        Parameter erweitert + 4 neue Parameter (Formant F1/F2, Intonationskontur-Phrasen,
        TTR) ergänzt, damit die Tabelle die tatsächlich pro Modul gezeigten Kennwerte
        abdeckt. Duplizierte Zeilen-Bau-Logik zwischen den Modulen und
        `views/gesamtbericht.py` in geteilte Helper (`flatten_take()`, `build_rows()`,
        `age_caveats_for()`) extrahiert. Verifiziert: End-to-End mit echten Daten — Tabelle
        erscheint auf der Vokalisation-Seite mit allen 6 Spalten inkl. neuer "Was es misst"-
        Spalte, Werte identisch zu Referenzwerten, Regressionstest über alle 6 Seiten ohne
        Exception, HTTP 200 nach Deploy.
- [x] **P6 — Recording-Quality-Check** ✅ UMGESETZT (2026-08-15) — neue
      `recording_quality_features()` in `core/audio.py` (kein neuer Tech-Stack, nutzt
      dieselbe soundfile-Basis wie `basic_stats()`): Clipping-Anteil (% Samples nahe
      Vollaussteuerung), Stille-Anteil (% Fenster unter -40dBFS, grobe Startschwelle) und
      eine SNR-Näherung (90.–10. Perzentil der Fenster-Lautstärke). **Bewusst rein
      informativ, kein hartes Cutoff-Gate** (Prinzip aus
      [[feedback_signalverarbeitung_kennwerte]]: Schwellen erst an echten Aufnahmen
      kalibrieren) — in allen 4 Guide-Modulen direkt nach dem Aufnahme-Player als
      3-Metriken-Zeile mit erklärendem Caption, kein Aussortieren. Echter Bug beim Testen
      VOR dem Deploy gefunden+behoben (siehe docs/bugtracker.md BUG-18): reine Digitalstille
      wurde durch einen `frame_rms > 0`-Filter fälschlich als 0% Stille statt 100% gezählt —
      gefunden durch gezielt konstruierte synthetische Testfälle (Stille/Clipping/Misch),
      nicht nur echte Aufnahmen. Verifiziert: synthetische Grenzfälle (reine Stille → 100%,
      leere Datei → alle `None`, Mischfall → korrekte ~33%) UND echte Testdateien (kein
      Clipping, plausible Stille-/SNR-Werte 19-34%/24-32dB), End-to-End über echten
      Schreib-Lese-Zyklus mit Anzeige auf der Modul-Seite bestätigt. Regressionstest über
      alle 6 Seiten ohne Exception, HTTP 200 nach Deploy.
  - [x] **Nachbesserung (2026-08-15, Nutzer-Feedback)**: Transkript-Detailinformationen, die
        im ursprünglichen Testdaten-Modus vorhanden waren (Wort-Konfidenz, Wortdauer,
        abgeleitete Sprech-/Pausenparameter), waren beim Modul-Umbau in `views/vorlesen.py`
        und `views/spontansprache.py` versehentlich auf eine reduzierte Anzeige (nur
        Sprechrate-Gauge + 2 Metriken) zusammengeschrumpft. Wiederhergestellt + erweitert:
        Ø Erkennungs-Konfidenz + Anzahl unsicherer Wörter (<75%), volle
        `compute_speech_metrics()`-Ausgabe (Wörter, Netto-/Artikulations-Sprechrate,
        Flüssigkeits-Score, Pausenzahl, Ø/Max-Pausendauer, Rhythmus/nPVI, Mikro-/
        Makropausen-Aufschlüsselung), `lexical_diversity_features()` (TTR/MTLD), sowie eine
        Wort-Zeitstempel-Detailtabelle (`start`/`end`/`score` + neu berechnete `duration_s`-
        Spalte) in einem Expander. Dieselbe `duration_s`-Spalte auch in `views/testdaten.py`
        ergänzt, wo die Wort-Zeitstempeltabelle bereits existierte, aber ohne Dauer-Spalte.
        Verifiziert: End-to-End auf dem Server mit einer echten, aus dem Cache geladenen
        Transkription (kein neuer WhisperX-Lauf nötig) — alle Metriken korrekt (27 Wörter,
        140/165 WPM, Flüssigkeits-Score 1.00, nPVI 45.2, TTR 0.96/MTLD 204.1), Wort-Tabelle
        mit korrekt berechneter `duration_s` (z.B. "Einst" 0.381s), identisch für Vorlesen
        UND Spontansprache getestet. Regressionstest über alle 6 Seiten ohne Exception,
        HTTP 200 nach Deploy.
- [x] **P7 — Audit-Parameter einbauen** ✅ UMGESETZT (2026-08-15) — RAP/PPQ5/APQ11, MPT, echte
      VSA-Formel, F0-Tremor, alle in `views/vokalisation.py` verdrahtet (dem bislang einzigen
      Modul mit gehaltenem Vokal — die anderen Module brauchen diese Parameter nicht).
  - **RAP/PPQ5/APQ11**: `core/audio.py::phonation_features()` erweitert — nutzt denselben
    `point_process` wie Jitter/Shimmer local, nur zusätzliche `praat.call(...)`-Aufrufe
    ("Get jitter (rap)"/"(ppq5)", "Get shimmer (apq11)"), keine neue Infrastruktur. Bewusst
    OHNE Ampel-Zonen (`zones_func: None` in `PARAMETER_INFO`) — kein projektintern
    verifizierter Cutoff, siehe neuer Punkt P12 unten.
  - **MPT (Maximum Phonation Time)**: neue `core/audio.py::mpt_features()` — längste
    zusammenhängende stimmhafte Passage aus der Pitch-Kontur (eigene Berechnung, nicht über
    Praats Voice-Report-Bruchzählung). Logik VOR dem Deploy an einer synthetischen
    Voiced/Unvoiced-Maske verifiziert (2,5s längste Serie korrekt erkannt).
  - **F0-Tremor**: neue `core/audio.py::f0_tremor_features()` — FFT/Periodogramm der
    (detrendeten, auf Gleichabstand interpolierten) F0-Zeitreihe im 3-15Hz-Band. Rein
    explorativ, ausdrücklich keine Tremor-Klassifikation/-Diagnose. Kern-Algorithmus VOR dem
    Deploy an einer synthetischen 6Hz-Sinus-Tremor-Zeitreihe verifiziert (Peak exakt bei
    6,0Hz erkannt, Amplitude-Schätzung durch Hanning-Fenster-Dämpfung ca. halb so groß wie
    die wahre Amplitude — bewusst nur als Eigenvergleichs-Näherung dokumentiert, kein
    kalibriertes Absolutmaß).
  - **Echte VSA-Formel**: neue `core/audio.py::vowel_space_area()` — Dreiecksformel
    (Shoelace) aus den Formant-Mittelwerten der 3 Eckvokale /a/,/i/,/u/. Arbeitet (anders als
    die übrigen Audio-Funktionen) NICHT auf einer einzelnen Datei, sondern kombiniert die
    jeweils AUSGEWÄHLTEN besten Takes aller 3 Vokal-Teilaufgaben — Aufruf deshalb aus
    `views/vokalisation.py` am Modul-Ende (nach der Tab-Schleife), zeigt sich erst, wenn alle
    3 Eckvokale mindestens einen Versuch haben. Formel isoliert mit realistischen
    Formant-Werten gegengeprüft (272.500 Hz² bei typischen /a/,/i/,/u/-Werten — plausible
    Größenordnung).
  - **Verifiziert**: End-to-End auf dem Server mit echten Aufnahmen (alle 3 Vokal-Slots
    befüllt) — Jitter RAP 0,30%/PPQ5 0,40%/Shimmer APQ11 3,71%/MPT 2,35s/F0-Tremor 3,83Hz
    alle korrekt in der Detail-Tabelle, VSA-Kachel erscheint nach Befüllen aller 3 Slots.
    Regressionstest über alle 6 Seiten ohne Exception, HTTP 200 nach Deploy.
- [x] **P8 — Live-Aufnahmedauer-Farbfeedback** ✅ UMGESETZT (2026-08-15) — Rahmen der
      Mikrofonaufnahme faerbt sich waehrend der laufenden Aufnahme zeitabhaengig gruen →
      orange → rot ein (Signal "kann/sollte beendet werden").
      **Technische Loesung, die die offene Frage klaert**: `st.audio_input()` liefert weiterhin
      keinen Live-Callback waehrend der Aufnahme, ABER eine reine CSS-`@keyframes`-Animation
      braucht das auch nicht — sie startet automatisch, sobald der Stop-Button erscheint
      (derselbe `:has(button[aria-label*="Stop" i])`-Trick wie beim bestehenden dezenten
      Aufnahme-Hinweis) und laeuft danach rein clientseitig, ohne Streamlit-Rerun/Python-Timer.
      Keine eigene JS-Komponente noetig. Neue `core/shared.py::
      recording_duration_feedback_style(green_s, orange_s, red_s, key)` — je Modul/Task-Typ
      eigene Ziel-Dauern (Vokal 3/5/10s, Lesetext 10/15/25s, Spontansprache 35/45/60s, DDK
      kombiniert 10/15/20s, DDK einzeln 15/20/30s), `key`-Parameter verhindert, dass
      unterschiedliche Instanzen auf derselben Seite (z.B. die 2 DDK-Tabs) sich gegenseitig
      ueberschreiben (CSS-`@keyframes`-Namen sind sonst global). Eingebaut in alle 4
      Guide-Module + `testdaten.py` (dort nach Task-Typ aus der Sidebar-Auswahl gemappt).
      Verifiziert: CSS-Injektion mit korrektem, task-spezifischem Animationsnamen in allen 4
      Modulen + `testdaten.py` bestaetigt (inkl. beider unterschiedlicher DDK-Tab-Keys
      gleichzeitig vorhanden), Regressionstest ueber alle 6 Seiten ohne Exception, HTTP 200
      nach Deploy. **NICHT visuell im echten Browser gegengeprueft** (kein Mikrofonzugriff im
      Sandbox-Browser, wie schon beim bestehenden Aufnahme-Hinweis) — bitte beim naechsten
      echten Testen eine Aufnahme laufen lassen und den Farbverlauf pruefen.
- [x] **P9 — Transkription als Hintergrund-Job** ✅ UMGESETZT + SERVER-VERIFIZIERT
      (2026-08-16, Nutzer-Feedback 2026-08-15, siehe docs/bugtracker.md RANDNOTIZ-13) —
      WhisperX blockierte vorher die komplette Browser-Sitzung für 1-2 Minuten. Konzept siehe
      `docs/konzept_p9_hintergrundjob_lokal.md`: datei-basierte Job-Queue
      (`core/job_queue.py`) + eigener Worker-Container (`worker.py`) + `st.fragment
      (run_every="1s")`-Polling (`core/shared.py::render_transcription_job()`) statt
      blockierender Thread-Schleife. `views/vorlesen.py`/`views/spontansprache.py`
      umgestellt (`views/testdaten.py` bewusst unverändert, nutzt weiter die alte
      `transcribe_with_progress()`, siehe dessen Docstring). Server-`docker-compose.yml` um
      `neurovoice-worker`-Dienst erweitert (geteilte Volumes, eigenes `mem_limit: 7g`, UI
      jetzt nur noch `2g`).
      **Verifiziert auf dem echten Produktiv-Server (2026-08-16)**: beide Container laufen
      (`neurovoice-dashboard` + `neurovoice-worker`), AppTest-Regression über alle 7 Seiten
      ohne Exceptions, HTTP 200, UND ein ECHTER Cross-Container-Test (Job von der UI
      übermittelt, vom SEPARATEN Worker-Container über das geteilte `/derived`-Volume
      abgeholt, echte WhisperX-Transkription gelaufen, Ergebnis zurückgeschrieben) —
      bestätigt, dass die Job-Queue-Architektur nicht nur simuliert, sondern im echten
      Mehr-Container-Deployment funktioniert.
      **Zweites Ziel (lokale Docker-Nutzung Mac/Windows, primär Apple Silicon) — ✅ ARM64
      VERIFIZIERT (2026-08-16)**: nativer Build auf einem M-Series-Mac erfolgreich
      abgeschlossen (kompletter Neubau ohne Cache, ca. 21 Minuten), `torch 2.8.0+cpu` (kein
      CUDA), `whisperx`, `parselmouth 0.4.7` (aus dem Quellcode kompiliert) und
      `core.job_queue` alle im fertigen Image funktionsfähig bestätigt. Zwei echte Funde
      dabei, beide behoben: (1) `praat-parselmouth` hat kein arm64-Wheel — Fix:
      `build-essential`/`cmake` im Dockerfile, kompiliert jetzt aus dem Quellcode (dauert
      allein ca. 15 Min., der größte Zeitanteil). (2) Wichtiger: ein normales `pip install
      torch` OHNE das PyTorch-CPU-Index-Repository zog auf arm64 versehentlich die komplette
      CUDA/NVIDIA-Toolkit-Kette mit (mehrere hundert MB nutzlose GPU-Pakete, war der
      eigentliche Haupttreiber des "ungewöhnlich langsamen Builds", nicht nur die
      Parselmouth-Kompilierung) — behoben, indem das CPU-Index-Repository jetzt
      architektur-unabhängig IMMER genutzt wird. Details siehe
      `docs/konzept_p9_hintergrundjob_lokal.md`. README um ausführliche
      Systemanforderungen/Downloadgrößen-Tabelle je Plattform (Apple Silicon/Windows/Intel-
      Mac/Linux) sowie eine Übersicht der verwendeten Kernbibliotheken mit Lizenzen ergänzt.
      Docker-Build-Cache nach Abschluss bereinigt (~14GB durch die vorherigen
      Fehlversuche angesammelt, entfernt).
      **Nachtrag 2026-08-16, lokaler Testlauf**: beim echten Transkribieren im lokalen Docker-
      Setup fiel auf, dass Docker Desktop auf diesem Mac (16GB RAM, 8GB VM-Limit) für WhisperX
      large-v3 + Alignment-Modell zu knapp bemessen ist, besonders mit anderen parallel
      laufenden lokalen Docker-Projekten — Worker-Container stürzte ab/startete neu, ein Job
      blieb verwaist hängen. Kein Software-Bug (auf dem Server mit 12GB exklusiv + 7GB-Limit
      lief es immer sauber), aber ein echter Ressourcen-Engpass auf schwächerer lokaler
      Hardware. **Nutzer-Entscheidung**: lokaler Docker-Workflow als aktive Test-/Entwicklungs-
      Nebenspur PAUSIERT (andere lokale Docker-Projekte + NeuroVoice-Container gestoppt,
      Modell-Cache-Volume bleibt erhalten) — primärer Arbeitsablauf wieder Server-Deploy via
      SSH/scp wie vor P9. Die lokale Docker-Variante bleibt vollständig im Repo, wird aber erst
      als bewusster Abschlussschritt poliert, wenn die Software einen stabilen/finalen Stand
      erreicht hat (Details siehe `docs/konzept_p9_hintergrundjob_lokal.md`, Nachtrag oben im
      Dokument).
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

- [x] **P10 — Proband:innen-Erfassung am Sitzungsanfang** ✅ UMGESETZT (2026-08-15) — aktuell
      startet eine Sitzung direkt mit der ersten
      Aufnahme, ohne dass irgendwo erfasst wird, WER untersucht wird. Für die spätere
      longitudinale Auswertung (Verlauf über mehrere Sitzungen hinweg, das ist der ganze Sinn
      des Projekts) muss ein Report eindeutig einem Subjekt zuordenbar sein.

  ### Grundsatzentscheidungen (mit Nutzer geklärt, 2026-08-15)

  1. **Proband:innen-ID gilt über mehrere Sitzungen hinweg** (nicht nur eine einzelne
     Aufnahme-Runde) — echte longitudinale Verknüpfung ist das Ziel, nicht nur eine
     Sitzungs-Kennzeichnung.
  2. **Pflichtschritt, kein Überspringen** — jede Sitzung (auch der bestehende Testdaten-/
     Entwicklermodus) bekommt automatisch eine ID zugewiesen, niemand kann ganz ohne
     Zuordnung starten.

  ### Konzept: zweistufige ID-Struktur

  - **`subject_id`** (NEU) — pseudonyme Proband:innen-Kennung, gilt über beliebig viele
    Sitzungen derselben Person hinweg. Kurzes, leicht abzuschreibendes/diktierbares Format,
    z.B. `NV-XXXX` (4 alphanumerische Zeichen aus einem auf Verwechslungsgefahr geprüften
    Alphabet, kein `0`/`O`/`1`/`I`/`l`). Kollisionsprüfung gegen bereits vergebene IDs beim
    Generieren.
  - **`session_id`** (bereits vorhanden, `core/session_store.py`, P4) — bleibt technische,
    URL-basierte Kennung EINER Sitzung, unverändert. Eine `subject_id` kann also mehrere
    `session_id`s haben (1:n).
  - **Kein Name, keine Initialen** — bewusst NUR die pseudonyme ID + Alter, nichts
    Namentliches. Eine Re-Identifizierung (welche ID gehört zu welcher echten Person) obliegt
    der behandelnden Person außerhalb der App (eigene Zuordnungstabelle, falls überhaupt
    nötig) — die App selbst speichert nichts, was direkt auf eine Person schließen lässt.
  - **Alter wird JE SITZUNG neu erfasst**, nicht einmalig auf Proband:innen-Ebene gespeichert
    — vermeidet das Problem "Alter müsste über Jahre hinweg aktualisiert werden" komplett,
    da bei jeder neuen Sitzung ohnehin neu (oder per Vorbefüllung bestätigt) eingegeben wird.
  - **Datum/Uhrzeit**: automatisch im Hintergrund erfasst (kein Eingabefeld) — deckt sich mit
    dem bereits vorhandenen `created_at` in `core/session_store.py`.

  ### Konzept: Startseite (neue erste Nav-Seite, vor "1. Vokalisation")

  Zwei große, klar getrennte Optionen:
  1. **"Neue:r Proband:in"** — Button "ID generieren" erzeugt eine neue `subject_id`, zeigt
     sie groß zum Abschreiben/Notieren an (die Person, die die App bedient, muss sich die ID
     selbst irgendwo notieren — die App bietet dafür keinen eigenen Speicherort außerhalb
     ihrer selbst an). Feld "Alter" (Pflicht, Zahleneingabe). Button "Sitzung starten".
  2. **"Bekannte:r Proband:in fortsetzen"** — Auswahl/Suche aus bereits bekannten
     `subject_id`s (zeigt Anzahl bisheriger Sitzungen + Datum der letzten Sitzung als
     Orientierung). Feld "Alter" (Pflicht, ggf. mit letztem bekannten Wert vorbefüllt, aber
     neu bestätigt). Button "Sitzung starten".

  ### Konzept: Datenmodell

  - `derived/_sessions/<session_id>.json` (bestehend) — erweitert um `subject_id` und
    `subject_age_at_session`.
  - `derived/_subjects/<subject_id>.json` (NEU) — schlanker Index: `subject_id`,
    `created_at`, Liste der zugehörigen `session_id`s. Grundlage für die Auswahlliste auf der
    Startseite UND für eine spätere echte Verlaufsansicht/Export (P14).

  ### Konzept: technische Umsetzung (grob)

  - Neue `views/start.py` als erste Seite in `app.py`s `st.navigation()`.
  - Zentrale Gate-Funktion (analog `core/shared.py::get_edf_or_stop()`-Muster beim
    EDF-Analyzer) prüft vor `pg.run()`, ob eine `subject_id` in der Sitzung gesetzt ist —
    falls nicht, werden alle anderen Seiten blockiert/auf die Startseite umgeleitet.
  - Testdaten-/Entwicklermodus bekommt automatisch eine synthetische Test-ID (z.B.
    `TEST-XXXX`) zugewiesen, damit der bestehende Entwickler-Workflow nicht manuell
    unterbrochen wird, aber trotzdem konsequent "kein Modus ohne ID" gilt.

  ### Offene Detailfragen (Umsetzungs-Ebene, nicht mehr grundsätzlich)

  - Migration bestehender Sessions ohne `subject_id` — vermutlich einfach als "nicht
    zugeordnet" markieren, kein Zwang zur nachträglichen Zuordnung.
  - Datenschutz-Detail: Speicherung bleibt wie bisher unverschlüsselt auf der Platte (kein
    neues Verschlüsselungs-Feature in diesem Schritt) — falls das zum Problem wird, gehört es
    eher in den separaten Public-Release-Fahrplan als hierher.
  - Exakte ID-Alphabet-/Formatwahl (Länge, Zeichensatz) — Vorschlag oben ist ein erster Wurf,
    kein endgültiger Beschluss.

  ### Umsetzung (2026-08-15, nach Nutzer-Freigabe "setze das so um")

  Konzept 1:1 wie oben umgesetzt, plus explizite Nutzer-Vorgabe aus der Freigabe: die
  zugeordnete Proband:in muss auf JEDER Seite sichtbar bleiben (nicht nur auf der Startseite)
  UND explizit im Gesamtbericht erscheinen.

  - **`core/subject_store.py`** (NEU): `generate_subject_id()` (Format `NV-XXXX`, Alphabet
    ohne `0`/`O`/`1`/`I`/`l`, kollisionsgeprüft gegen `derived/_subjects/`),
    `list_subjects()` (Index-Liste, neueste Aktivität zuerst), `bind_subject_to_session()`
    (schreibt `subject_id`/Alter in `st.session_state`, persistiert sofort die Sitzungsdatei
    UND aktualisiert `derived/_subjects/<id>.json`), `require_subject_or_stop()` (Gate-Funktion
    analog zum EDF-Analyzer-Muster `get_edf_or_stop()`).
  - **`core/session_store.py`** erweitert: Payload trägt jetzt `subject_id` +
    `subject_age_at_session`. `load_session_snapshot()` übernimmt beide IMMER (auch wenn
    `module_results` schon gefüllt ist und der bestehende Guard dafür früh aussteigt) — sonst
    würde die Proband:innen-Zuordnung beim erneuten Laden verloren gehen.
  - **`views/start.py`** (NEU): erste Seite im Guide. Zwei Tabs — "Neue:r Proband:in"
    (ID-Generator-Button + Pflichtfeld Alter) und "Bekannte:r Proband:in fortsetzen"
    (Auswahlliste aus `list_subjects()`, zeigt Anzahl bisheriger Sitzungen + letztes Datum).
    Ist die Sitzung bereits zugeordnet, zeigt die Seite das direkt an + einen Weiter-Button.
  - **`app.py`**: `views/start.py` als erste Seite in `st.navigation()`. Neue zentrale
    `core/shared.py::render_subject_badge()` einmal VOR `pg.run()` aufgerufen — Sidebar-Inhalt
    außerhalb der Seiten-Funktion bleibt über Seitenwechsel hinweg bestehen, erfüllt damit die
    "auf jeder Seite"-Vorgabe ohne Wiederholung in jeder einzelnen View.
  - **`require_subject_or_stop()`** ganz oben in allen 4 Guide-Modulen + `views/gesamtbericht.py`
    eingebaut (vor jeder anderen Ausgabe) — blockiert mit klarer Meldung + Link zur Startseite,
    solange keine ID zugeordnet ist.
  - **`views/gesamtbericht.py`**: zusätzlich zur Sidebar-Badge eine prominente Zeile direkt im
    Report-Inhalt selbst ("Proband:in: `NV-XXXX` · Alter: NN"), wie explizit gefordert.
  - **`views/testdaten.py`**: bekommt automatisch eine `TEST-XXXX`-ID zugewiesen (eigenes
    Präfix, damit Test-IDs in der Auswahlliste klar von echten Proband:innen-IDs
    unterscheidbar bleiben) — kein manueller Schritt nötig, damit der Entwickler-Workflow
    nicht unterbrochen wird, aber "Pflicht, kein Überspringen" gilt konsequent auch hier.

  **Bug gefunden + behoben (vor Deploy final verifiziert)**: die automatische TEST-ID-Zuweisung
  in `testdaten.py` zeigte im allerersten Aufruf eine LEERE Sidebar-Badge — `render_subject_badge()`
  läuft in `app.py` VOR `pg.run()`, sieht das gerade erst in `testdaten.py` gesetzte
  `subject_id` also erst im nächsten Rerun. Fix: `st.rerun()` direkt nach der automatischen
  Zuordnung (guard verhindert eine Endlosschleife, da `subject_id` danach gesetzt ist).

  **Verifiziert**: End-to-End auf dem Server — Gate blockiert korrekt mit Warnung + Startseite-
  Link, ID-Generierung funktioniert, vollständiger Bind-Flow (ID + Alter → Sitzung starten)
  bestätigt per direktem Session-Datei-Inhalt (`subject_id`/`subject_age_at_session` korrekt
  persistiert), Sidebar-Badge UND Gesamtbericht-Zeile zeigen die zugeordnete ID nach einem
  simulierten Seiten-Reload korrekt an, "Bekannte:r Proband:in fortsetzen"-Liste zeigt
  vorherige IDs korrekt, Testdaten-Modus bekommt automatisch eine TEST-ID inkl. sichtbarer
  Badge (nach dem Rerun-Fix). Regressionstest über alle 7 Seiten (inkl. neuer Startseite) ohne
  Exception, HTTP 200 nach Deploy.

  **Nebenbefund beim Aufräumen**: mehrere frühere Verifikations-Durchgänge dieser Session
  (P7/Design-Bereinigung) hatten Test-Dateien in `derived/_uploads/` hinterlassen, die mein
  Cleanup-Muster nicht erfasst hatte (Suchmuster prüfte den an `save_uploaded_wav()`
  übergebenen Namen, nicht den tatsächlich gespeicherten Dateinamen mit
  Zeitstempel-Präfix) — die eindeutig identifizierbaren wurden nachträglich entfernt. Übrige,
  nicht eindeutig als Testartefakt erkennbare Dateien in `_uploads/` bewusst NICHT gelöscht
  (könnten eigene manuelle Testaufnahmen des Nutzers sein) — bei Gelegenheit gemeinsam
  durchsehen.

## Konzept: Design-Bereinigung — weg von Tacho-Gauges/Emojis, hin zu nüchternen Kacheln (2026-08-15)

**Nutzer-Feedback:** Emojis wirken unseriös, die Halbkreis-Tacho-Gauges (`core/plots.py::
gauge_figure()`) wirken zu "dashboardartig"/verspielt. Referenz-Vorbild ist explizit die
Kachel-Ansicht des EDF-Analyzers (`kpi_tile()`), die dort als "schicker" empfunden wurde:
Wert nüchtern in einer Karte, farblich markiert nur der Rand/Status (nicht die ganze Fläche),
Kontext-Erklärung dabei. Zusätzlich soll die Aufnahmequalität (Clipping/Stille/SNR) genauso
interpretiert/farblich codiert werden statt als reine Zahl.

**Wichtig: NeuroVoice AI hat das exakt gleiche Redesign schon einmal beim EDF-Analyzer
durchlaufen** (siehe Memory [[project_edf_ui_redesign]], 6 Phasen, abgeschlossen 2026-08-09).
Ein Teil der Grundlagen wurde bereits am 2026-08-14 bewusst 1:1 herübergezogen
(`core/design_tokens.py`, `core/reference_ranges.py` mit denselben Ampelfarben/Hex-Werten wie
dort) — das Fundament existiert also schon, es fehlen nur die konkreten Komponenten
(`kpi_tile()`, `status_dot()`, Material-Icons) und deren Einbau in die 4 Guide-Module.

### Ist-Stand (2026-08-15, geprüft)

- **Emojis**: `app.py` (7), `views/testdaten.py` (9), `views/spontansprache.py` (6),
  `views/vorlesen.py` (6), `views/ddk.py` (4), `views/vokalisation.py` (4),
  `views/gesamtbericht.py` (2) — 38 Fundstellen app-weit.
- **Tacho-Gauges** (`gauge_figure()`, matplotlib-Halbkreis mit Nadel): aktuell in allen 4
  Guide-Modulen + `testdaten.py` für Jitter/Shimmer/HNR/CPPS/Sprechrate/Artikulationsschärfe/
  DDK-Rate/Monopitch/Vokalraum-Fläche.
- **Bereits vorhanden und direkt weiterverwendbar**: `core/interpretation.py`
  (`PARAMETER_INFO`, `interpret()`, `flatten_take()`, `build_rows()`) liefert für praktisch
  jeden Gauge-Parameter schon Label/Einheit/Beschreibung/Normbereich-Funktion/Status/Kontext-
  Kommentar — das ist inhaltlich bereits die "Laborwert"-Logik, die die Kacheln nur noch
  ANDERS darstellen müssen (Kachel statt Tabellenzeile), keine neue Datengrundlage nötig.
- **Recording-Quality-Check** (`core/audio.py::recording_quality_features()`, P6): liefert
  `clipping_pct`/`silence_pct`/`snr_estimate_db`, aktuell nur als 3× `st.metric()` ohne jede
  Bewertung — genau der vom Nutzer benannte Lücken-Punkt.

### Baustein A — Kachel-Komponente statt Tacho-Gauge

Neue `core/shared.py::kpi_tile(label, value_text, sub_text, zone, description=None)` — Design
1:1 vom EDF-Analyzer übernommen (Border-Top-Akzent-Stil, `min-height` für gleich hohe Reihen),
Zonen (`success`/`warning`/`danger`/`info`/`neutral`) mappen auf dieselben
`core/design_tokens.py`-Farben, die `core/reference_ranges.py` schon nutzt — keine neue
Farbpalette nötig. Pro Modul-Seite ersetzt eine Kachel-Reihe (`st.columns` + `kpi_tile()`) die
bisherige Gauge-Reihe:
- `value_text` = Wert + Einheit (z.B. "0,6 %"), `sub_text` = Normbereich oder Status-Label
  ("im Normbereich" / "grenzwertig" / "auffällig" / "kein Normwert").
- `description` = der bereits vorhandene `PARAMETER_INFO[...]["description"]`-Text ("Was es
  misst"), knapp unter dem Wert — löst gleichzeitig die zusätzliche Nutzer-Vorgabe "mit
  Erklärung" mit, ohne neuen Text schreiben zu müssen.
- Parameter OHNE Normbereich (viele DDK-/Prosodie-Werte) bekommen Zone `neutral`/`info` statt
  gar keiner Farbe — Pendant zur bisherigen "informativen Nadel ohne Farbwertung".
- Die bereits bestehende, ausführlichere Interpretations-TABELLE (`build_rows()`, mit voller
  Kontext-Spalte) bleibt zusätzlich erhalten, aber wandert konzeptuell zur "Detail-Ansicht"
  (z.B. in einen Expander "Alle Werte im Detail") — die Kacheln sind der neue "Auf-einen-
  Blick"-Layer direkt unter der Aufnahme, die Tabelle bleibt für alle, die mehr wissen wollen.
- `gauge_figure()` selbst wird NICHT sofort gelöscht (erst wenn alle Aufrufstellen migriert
  sind und klar ist, ob irgendwo doch noch eine Nadel-Darstellung sinnvoll bleibt) — reine
  Karteileiche vermeiden, aber kein verfrühtes Löschen laufenden Codes.

### Baustein B — Recording-Quality-Check: Interpretation + Farbcodierung

Neue Zonen-Funktion in `core/reference_ranges.py` (analog zu `hnr_zones()`/`jitter_zones()`),
je Metrik von `recording_quality_features()`:
- **Clipping-Anteil**: 0% gut, >0-0,5% grenzwertig (vereinzelte Spitzen), >0,5% auffällig
  (hörbare Verzerrung wahrscheinlich) — pragmatische Schwelle, nicht literaturbasiert (anders
  als Jitter/HNR/etc.), muss im Kontext-Text klar als technische Faustregel gekennzeichnet
  werden, nicht als klinischer Normbereich verkauft werden.
- **Stille-Anteil**: kontextabhängig vom Task (bei Vokal-Haltetönen erwartungsgemäß ~0%, bei
  Spontansprache mit Pausen normal auch 15-30%) — **kein fester Grenzwert über alle Module**,
  eher ein modul-spezifischer Korridor oder ein reiner Plausibilitäts-Hinweis ("passt zur
  erwarteten Aufgabe" / "ungewöhnlich viel Stille — Aufnahme evtl. zu kurz beendet oder zu
  lang mitgeschnitten"). Braucht bei der Umsetzung eine bewusste Entscheidung, ob pro
  Task-Typ unterschiedliche Korridore gepflegt werden (Mehraufwand) oder ein grober,
  konservativer Gesamt-Korridor reicht.
- **SNR-Schätzung**: >25dB gut, 15-25dB grenzwertig (Hintergrundgeräusch hörbar, Kennwerte
  ggf. verzerrt), <15dB auffällig (Zuverlässigkeit der akustischen Kennwerte in Frage
  gestellt) — Faustregel aus allgemeiner Signalverarbeitung, keine stimmklinische Literatur-
  Referenz vorhanden (im Kontext-Text als solche kennzeichnen, Prinzip wie bei den
  DDK-Referenzbereichen in `core/reference_ranges.py`, die auch schon so gekennzeichnet
  sind).
- Anzeige: dieselbe `kpi_tile()`-Komponente wie Baustein A statt der aktuellen 3×
  `st.metric()`-Zeile — macht die Recording-Quality-Kacheln optisch ununterscheidbar von den
  akustischen Kennwert-Kacheln (konsistent, ein einziges visuelles Vokabular für "Wert +
  Bewertung + Erklärung" app-weit, statt zwei parallelen Stilen).
- **Bewusst weiterhin kein hartes Cutoff-Gate** (Prinzip aus P6/BUG-18 bleibt: informativ,
  nichts wird deshalb ausgeblendet oder blockiert) — nur jetzt mit Ampel-Farbe statt nackter
  Zahl.

### Baustein C — Emoji-Bereinigung (Material-Icons)

Gleiches Muster wie beim EDF-Analyzer, 1:1 übertragbar:
- Sidebar-/Seiten-Icons: `st.Page(icon=...)` + `st.title()` von Emoji auf
  `:material/...:`-Shortcodes (z.B. `record_voice_over` für Vokalisation, `menu_book` für
  Vorlesen, `chat` für Spontansprache, `repeat` für DDK).
- `st.info/warning/error/success`: `icon=`-Parameter statt Emoji im Text.
- Take-Management-Symbole (vermutlich ✅/🗑️/▶️ für Auswahl/Löschen/Abspielen, genauer Ist-
  Stand bei Umsetzung prüfen) auf `icon=`-Parameter der jeweiligen Buttons umstellen.

### Pitfalls aus dem EDF-Analyzer-Redesign (unbedingt beachten, damit dieselben Fehler nicht
wiederholt werden — siehe [[project_edf_ui_redesign]])

1. **Zwei unterschiedliche Icon-Kontexte, nicht austauschbar**: In eigenem HTML
   (`unsafe_allow_html=True`) braucht es `<span class="material-symbols-outlined">name</span>`
   (+ einmalig den Material-Symbols-Font global laden). In Streamlit-eigenen Text-Widgets
   (`st.title`, `st.button`, `st.expander`, `st.Page(icon=...)`) gilt der native
   `:material/name:`-Shortcode-Text. Werden die beiden vertauscht, rendert entweder rohes
   HTML als Klartext oder der Shortcode bleibt als Text sichtbar statt als Icon.
2. **`st.dataframe()`-Zellen, `format_func` in Dropdowns/Tabs**: rendern KEIN HTML und
   verstehen KEINEN Shortcode — dort muss Klartext (ggf. mit Emoji als einzig praktikabler
   Option) bleiben oder auf reinen Text ohne Icon umgestellt werden. Beim EDF-Analyzer führte
   das Ignorieren dieser Regel zu einer echten Regression (Dropdown zeigte rohen Text
   "ecg_heart EKG" statt eines Icons) — vor der Umsetzung hier gezielt prüfen, ob
   Take-Auswahl-Radios/Dropdowns in `core/module_state.py`/den Modul-Seiten betroffen sind.
3. **Eigene `<style>`-Blöcke**: `@import url(...)` INNERHALB des `<style>`-Tags verwenden,
   nicht ein separates `<link rel="stylesheet">`-Element — Letzteres wurde beim EDF-Analyzer
   von `st.markdown(unsafe_allow_html=True)` als Klartext statt als Style gerendert.
4. **Nicht alles auf einmal migrieren**: EDF-Analyzer lief in 6 klar getrennten Phasen
   (Fundament → Navigation → Status-Komponenten → Kacheln → Plot-Theme → Seite-für-Seite-
   Rollout), jede einzeln verifiziert und deployt. Für NeuroVoice AI sinnvolle Aufteilung:
   zuerst `kpi_tile()`+Zonen-Funktionen bauen und an EINEM Modul (z.B. Vokalisation, kleinste
   Seite) verifizieren, dann erst auf die übrigen 3 Module + `testdaten.py` ausrollen, Emoji-
   Bereinigung als eigener, unabhängiger letzter Schritt.
5. **Reale End-to-End-Verifikation ist hier sogar LEICHTER möglich als beim EDF-Analyzer**
   (dort war Datei-Upload nicht automatisierbar) — NeuroVoice AI hat bereits den etablierten
   `AppTest`+Session-Snapshot-Verifikationsweg aus P1-P6/BUG-19, der echte Kachel-Werte gegen
   Referenzwerte prüfen kann, nicht nur "kein Crash". Sollte konsequent genutzt werden statt
   sich auf reine Kompilierungs-/Server-Start-Checks zu verlassen.
6. **Konsolidierung, kein Parallelbetrieb**: beim EDF-Analyzer sind während der Migration
   mehrfach unabhängig gewachsene Kachel-/Card-Implementierungen gefunden worden
   (`_kpi_card()`, `_metric_card()`, `_tile()` — alle strukturell dasselbe, aber leicht
   unterschiedlich). Bei NeuroVoice AI vorsorglich VOR dem Bau prüfen, ob es in den 4 Modul-
   Dateien bereits eigene Kachel-artige Ad-hoc-`st.markdown(f"<div style=...")`-Blöcke gibt
   (z.B. für die Take-Management-Anzeige), die im selben Zug auf `kpi_tile()` migriert werden
   sollten, statt eine zweite Variante daneben entstehen zu lassen.

### Noch offen / bei Umsetzung zu entscheiden

- Reihenfolge Kachel-Reihe vs. Diagramme (Wellenform/Intensität/Spektrogramm) vs.
  Detail-Tabelle auf der Modul-Seite — noch nicht festgelegt, User-Feedback beim ersten
  umgesetzten Modul einholen, bevor auf die restlichen 3 ausgerollt wird.
- Genaue Grenzwerte für Clipping/Stille/SNR (Baustein B) sind bewusst pragmatische
  Faustregeln, keine Literaturwerte — vor Public-Release-Reife ggf. an echten
  Testaufnahmen/Praxis-Erfahrung nachjustieren.
- Schicksal von `radar_figure()` (`core/plots.py`, aktuell ungenutzt/wo eingesetzt?) bei
  Gelegenheit mit prüfen, ob das dieselbe "Dashboard-Optik" hat, die der Nutzer ablehnt.

**Status: ✅ UMGESETZT (2026-08-15, Nutzer-Freigabe "Setze das so um, gutes Konzept").**

- **Baustein A** — `core/shared.py::kpi_tile()` (Border-Top-Akzent-Kachel, CSS-Klassen
  `.dw-tile*`) ersetzt `gauge_figure()` app-weit in allen 4 Guide-Modulen + `testdaten.py`.
  Datengrundlage bleibt `core/interpretation.py::PARAMETER_INFO`, neue `build_tiles()`-
  Funktion (+ `zone`-Feld in `interpret()`, neue `zone_for_value()` in
  `core/reference_ranges.py`) liefert dieselben Werte wie die bisherige Tabelle, nur als
  Kachel-Datensatz. Die ausführliche Interpretations-Tabelle bleibt erhalten, wandert aber in
  einen Expander ("Alle Werte im Detail") — Kacheln sind jetzt der "Auf-einen-Blick"-Layer,
  Tabelle die Detail-Ebene. `gauge_figure()` selbst bewusst NICHT gelöscht (Karteileiche,
  aber kein Aufrufer mehr übrig — spätere Aufräum-Gelegenheit).
- **Baustein B** — neue `clipping_zones()`/`snr_zones()` in `core/reference_ranges.py`
  (pragmatische Faustregeln, explizit als solche gekennzeichnet, keine klinische Norm) +
  geteilte `core/shared.py::quality_tiles(q)`-Funktion (ersetzt 3× `st.metric()` in allen 4
  Modulen durch dieselbe Kachel-Optik). Stille-Anteil bewusst OHNE feste Ampel (taskabhängig,
  wie im Konzept vorgesehen), nur Clipping + SNR bekommen eine echte Zonen-Farbe.
- **Baustein C** — alle verbleibenden Emojis app-weit entfernt (`app.py` Sidebar-Icons +
  Tab-Icon auf `:material/...:`-Shortcodes, Take-Management-Buttons auf `icon=`-Parameter,
  Status-Captions/Cache-Hinweise ohne Emoji-Präfix). Kein einziger Treffer mehr bei
  systematischer Emoji-Suche über `app.py`/`core/*.py`/`views/*.py`.

**Verifiziert**: Regressionstest über alle 6 Seiten ohne Exception, End-to-End mit echten
Aufnahmen für Vokalisation (Jitter 0,62%/Shimmer 4,56%/HNR 22,34dB — alle korrekt grün, CPPS
11,66dB neutral, SNR 24,3dB korrekt gelb/"Hintergrundgeräusch hörbar"), DDK (DDK-Rate 3,40 Hz,
identisch zum früher gemessenen Referenzwert 3,4 Hz) und Testdaten-Modus (Sprechrate
140,38 WPM grün, CPPS 7,09dB — beide identisch zu früheren Referenzwerten für dieselbe
Datei) — Kachel-HTML jeweils direkt aus dem AppTest-Markdown-Output geprüft, nicht nur "kein
Crash". HTTP 200 nach Deploy.

**Bewusst nicht (mehr) umgesetzt**: die feinere Bedeutungsnuance einzelner alter Gauge-
Captions (z.B. "HNR … eingeschränkt bei Fließsprache" auf der Testdaten-Schnellansicht) ist
in der konsolidierten Kachel-Beschreibung nicht mehr enthalten — bewusster Trade-off für ein
einheitliches Kachel-Vokabular app-weit statt bespoke Text je Aufrufstelle, deckt sich mit
Pitfall 6 aus dem Konzept (keine parallelen Varianten). Bei Bedarf könnte das über ein
optionales `note`-Argument in `kpi_tile()` nachgerüstet werden.

- [x] **Nachbesserung (2026-08-15, Nutzer-Testing nach der Design-Bereinigung)** ✅ UMGESETZT
      — vier konkrete Funde beim ersten echten Durchklicken:
  1. **Interpretations-Tabelle schnitt Text ab**: `st.dataframe()` (glide-data-grid) zeigt
     lange Zellen ("Was es misst"/Kontext) mit Ellipsis ohne Volltext-Zugriff. Fix: neue
     `core/shared.py::render_interpretation_table()` nutzt `st.table()` (umbricht normal statt
     abzuschneiden) + CSS-Feinschliff, an allen 6 Aufrufstellen (4 Module + Gesamtbericht +
     `testdaten.py`'s eigene Tabellarische-Übersicht) vereinheitlicht.
  2. **Aufnahmequalität "erschließt sich nicht"**: `quality_tiles()` bekam eine eigene
     umrandete Sektion (`st.container(border=True)`) mit Überschrift "Aufnahmequalität
     prüfen" + eine zusammenfassende Bewertung ÜBER den 3 Einzel-Kacheln (schlechteste Zone
     von Clipping/SNR gewinnt) — bei "danger" ein `st.warning()` mit konkreter Empfehlung,
     die Aufnahme zu wiederholen, bei "warning" ein dezenterer `st.info()`-Hinweis, sonst ein
     ruhiges "Unauffällig".
  3. **Keine Textgrößen-Steuerung in den 4 Guide-Modulen**: gab es bisher nur im Testdaten-
     Modus (`TEXT_SCALE`-Slider). In `core/shared.py::instruction_text_scale_control()`
     extrahiert (Konsolidierung statt 5. Duplikat) und in alle 4 Module + `testdaten.py`
     eingebaut — Instruktionstext ("Lies den folgenden Satz…"/"Halte den Vokal…") jetzt
     überall vergrößerbar, wichtig für Patient:innen mit Leseschwäche.
  4. **Formant-Tracks im Spektrogramm unerklärt**: F0/F1/F2/F3-Overlays (farbcodiert) hatten
     keine Legende/Erklärung. Neue `core/shared.py::SPECTROGRAM_LEGEND_CAPTION`-Konstante
     (was F0/F1/F2/F3 bedeuten, welche Farbe welcher Track ist) unter jedem Spektrogramm in
     allen 5 Stellen (4 Module + `testdaten.py`).

  Verifiziert: End-to-End mit echter Aufnahme (Vokalisation) — Textgrößen-Regler in der
  Sidebar vorhanden, Formant-Caption vorhanden, Qualitäts-Überschrift + korrekter
  "grenzwertig"-Hinweis bei SNR 24,3dB (identisch zur vorherigen Zonen-Berechnung), volle
  Kontext-Texte (z.B. HNR-Kontext, 172 Zeichen) im `st.table()`-DataFrame bestätigt statt nur
  angenommen. Regressionstest über alle 6 Seiten ohne Exception, HTTP 200 nach Deploy.

- [x] **P11 — Kompakte Übersicht + ausführliches Evidenz-Glossar trennen** ✅ UMGESETZT
      (2026-08-15) — die bisherige Interpretations-Tabelle (alle 6 Spalten in einer Tabelle)
      ist aufgeteilt in:
  1. **Kompakte Übersicht** (`core/interpretation.py::build_rows()`, jetzt nur noch Parameter/
     Wert/Normbereich/Status — die 2 langen Textspalten entfernt) über `render_interpretation_table()`
     im "Alle Werte im Detail"-Expander.
  2. **Ausführliches Evidenz-Glossar** (neue `build_glossary_entries()` + `core/shared.py::
     render_glossary()`) in einem eigenen "Glossar & Literatur"-Expander direkt darunter: pro
     Parameter Label, "Was es misst", Kontext (deskriptiv), eine **Evidenz-Einordnung** (4
     Kategorien statt Sterne — bewusst gröber/ehrlicher als eine Pseudo-Genauigkeits-Bewertung:
     "gut etabliert" / "in der Forschung diskutiert" / "eigene Heuristik / explorativ" /
     "deskriptiv, kein Krankheits-Marker") und ein kurzer Literaturverweis.
  - **Literaturarbeit**: alle 35 `PARAMETER_INFO`-Einträge in `core/interpretation.py` um
    `evidence`+`literature` erweitert, gegründet auf `docs/literatur_review.md` (Feature-
    Kategorien-Abschnitte 1-6 + Quellenliste) — z.B. Jitter/Shimmer/HNR/Monopitch/Monoloudness/
    Pausenmuster/Sprechrate als "gut etabliert" eingestuft (Standard-Stimmklinik-/Sprechfluss-
    Literatur), CPPS/Formant-Streuung/DDK-Regelmäßigkeit/VSA als "in der Forschung diskutiert"
    (vielversprechend, aber laut Literatur uneinheitlich validiert bzw. eigene Anpassung einer
    etablierten Grundidee), Artikulationsschärfe/Flüssigkeits-Score/Pausen-Substatistiken/
    F0-Tremor als "eigene Heuristik" (projekteigene Berechnung ohne etablierten Cutoff),
    Formant-Rohwerte/Wortzahl/Phrasenzahl als rein "deskriptiv". RAP/PPQ5/APQ11/MPT als "gut
    etabliert" (Teil der klassischen MDVP-Konvention bzw. klassisches Stimm-/Atemreserve-Maß),
    aber mit dem Hinweis, dass hier kein projektintern verifizierter Cutoff hinterlegt ist
    (Verweis auf P12).
  - **Gesamtbericht** (`views/gesamtbericht.py`): Glossar wird NICHT pro Teilaufgabe wiederholt
    (starke Redundanz, da z.B. Jitter/Shimmer/HNR in mehreren Modulen auftauchen), sondern über
    alle Module/Teilaufgaben hinweg gesammelt, nach Label dedupliziert und alphabetisch sortiert
    in EINEM gemeinsamen Glossar-Expander am Ende des Berichts gezeigt.
  - Alte `age_caveats_for()`-Funktion entfernt (tote Code — der Alters-/Geschlechts-Hinweis
    erscheint jetzt direkt im jeweiligen Glossar-Eintrag statt als separate Caption-Liste).
  - **Verifiziert**: End-to-End mit echter Aufnahme — kompakte Tabelle zeigt korrekt nur 4
    Spalten (12 Zeilen), "Glossar & Literatur"-Expander getrennt vorhanden, alle 12
    Glossar-Blöcke mit korrektem Label/Evidenz-Badge/Quellenangabe bestätigt (z.B. "Monopitch"
    → "gut etabliert" → (Dys)Prosody-in-PD-Quelle). Regressionstest über alle 7 Seiten ohne
    Exception, HTTP 200 nach Deploy.
- [x] **P12 — Fehlende Referenzwerte/Normbereiche recherchieren** ✅ UMGESETZT (2026-08-15,
      hohe Priorität, gründliche Websuche mit `WebSearch`) — systematisch alle Parameter mit
      `zones_func: None` durchgegangen. Details + alle Quellen siehe
      `docs/literatur_review.md`, Abschnitt "Referenzwerte-Recherche P12".
  - **6 neue Ampel-Zonen ergänzt** (`core/reference_ranges.py`): `ddk_rate_zones()` (5-8Hz
    normal, Literaturwerte gesunder Erwachsener 5-7 Silben/s AMR bzw. 6,57±0,84 Silben/s SMR;
    Ataxie-Studie 3,20 vs. 5,61 Silben/s), `mpt_zones()` (≥15s normal, konservative
    weibliche/untere Literaturgrenze da kein Geschlecht erfasst wird), `rap_zones()`/
    `ppq5_zones()`/`apq11_zones()` (klassische MDVP-Normwerte 0,68%/0,84%/3,07% — mit
    explizitem MDVP-vs-Praat-Vorbehalt, da beide Tools nachweislich systematisch
    unterschiedliche Absolutwerte liefern), `cpps_zones()` (Praat-spezifische Cutoffs 14,45dB
    Vokal / 9,33dB Fließsprache aus derselben Quelle — nutzt den strengeren Vokal-Cutoff, mit
    explizitem Hinweis, dass die Ampel bei Fließsprache-Aufnahmen dadurch strenger ausfallen
    kann als literaturbasiert gerechtfertigt).
  - **4 Parameter bewusst OHNE neue Zone gelassen** (Recherche durchgeführt, aber keine
    belastbare Einzelzahl mit Quelle gefunden — ehrlich dokumentiert statt erfunden):
    Monopitch/F0-SD (nur grober 12-40Hz-Bereich ohne klare Einzelquelle), DDK-Regelmäßigkeit/CV
    (qualitativ als Ataxie-Marker bestätigt, kein Zahlen-Cutoff), Monoloudness/Intensitäts-SD
    (nur allgemeine Lautstärke-Pegel gefunden, kein SD-Wert), Vokalraum-Fläche/VSA (extrem
    methodenabhängig, keine akzeptierte Hz²-Schwelle). Kontext-/Literatur-Text in
    `PARAMETER_INFO` trotzdem um die Rechercheergebnisse angereichert.
  - **Formant F1/F2 (Rohwerte)/Intonationskontur-Phrasenzahl/TTR bewusst unverändert**: diese
    sind strukturell nicht normalisierbar (F1/F2 hängen von der unbekannten Vokal-Identität
    ab, Phrasenzahl/TTR hängen von Aufnahmedauer/Textlänge ab) — kein Rechercheergebnis hätte
    daran etwas geändert, bereits vorher korrekt als "deskriptiv" eingeordnet.
  - **Verifiziert**: End-to-End mit echten Aufnahmen auf dem Server — alle 6 neuen Zonen
    liefern plausible Status (z.B. RAP 0,30% → „im Normbereich", APQ11 3,71% → „grenzwertig",
    CPPS 11,66dB → „grenzwertig", DDK-Rate 3,40Hz → „auffällig", MPT 2,35s → „auffällig", alle
    konsistent mit den definierten Grenzen). Regressionstest über alle 7 Seiten ohne Exception,
    HTTP 200 nach Deploy.
- [ ] **P13 — Zu fachsprachliche Parameter-Bezeichnungen vereinfachen** (Nutzer-Feedback
      2026-08-15, NICHT umgesetzt) — konkret genannt: "Artikulationsschärfe", "DDK-Rate",
      "DDK-Regelmäßigkeit (CV)", "Ø Zyklus-Intervall" seien zu fachmännisch für Patient:innen/
      Laien. Braucht eine bewusste Namensfindung (nicht einfach spontan umbenennen, da die
      Begriffe auch in `docs/literatur_review.md`/internen Notizen verankert sind) — ggf. mit
      Nutzer gemeinsam Alternativbegriffe festlegen, dann konsistent in
      `core/interpretation.py::PARAMETER_INFO["label"]` UND den Modul-Seiten (DDK-Tab-
      Beschriftungen etc.) durchziehen. Betrifft möglicherweise weitere Parameter über die 4
      genannten hinaus — bei Umsetzung einmal komplett durchgehen, nicht nur die 4 Beispiele.
- [x] **P14 — Excel-/PDF-Report-Export im Gesamtbericht** ✅ UMGESETZT (2026-08-16, Nutzer-
      Feedback 2026-08-15, analog EDF-Analyzer) — auf der Gesamtbericht-Seite (`views/gesamtbericht.py`)
      soll es einen Button geben, der ON DEMAND (nicht automatisch) einen Export erzeugt,
      sowohl als Excel-Tabelle als auch als PDF-Report. Größerer Feature-Aufwand:
  - Excel: vermutlich `openpyxl`/`pandas.to_excel()`, neue Dependency falls nicht schon
    vorhanden — prüfen, ob `openpyxl` bereits in `requirements.txt` steht.
  - PDF: braucht eine Report-Vorlage (Layout, Logo/Titel, evtl. Diagramme eingebettet) —
    beim EDF-Analyzer existiert dafür bereits eine PDF-Report-Pipeline
    ([[project_edf_report_audit]]), die als Vorbild/Wiederverwendungs-Kandidat dienen könnte
    (gleicher Tech-Stack? prüfen).
  - Sollte den `st.session_state["module_results"]`-Sitzungszustand (bester Take je
    Teilaufgabe, inkl. Metadaten wie Aufnahmezeitpunkt) vollständig abbilden, nicht nur die
    aktuell sichtbare Tabelle.
  - Hängt an P10 (Proband:innen-Erfassung) — ein Report ohne Zuordnung zu einem Subjekt ist
    für die longitudinale Auswertung nur bedingt nützlich, beide Punkte sollten bei der
    Umsetzung zusammen gedacht werden, auch wenn P10 technisch nicht Voraussetzung ist.
  - **Stand 2026-08-16**: `core/report_export.py` implementiert (Excel via `openpyxl`, PDF via
    `fpdf2`, beide bauen ausschließlich auf `core/interpretation.py::flatten_take()`/
    `build_rows()`/`build_glossary_entries()` auf, kein eigener Normwert-Text), zwei
    On-Demand-Buttons in `views/gesamtbericht.py` ("erstellen" → "herunterladen",
    zweistufig, damit nichts automatisch bei jedem Seitenaufruf erzeugt wird), Dependencies
    zu `requirements.txt` hinzugefügt, Docker-Image auf dem Server neu gebaut. **Verifiziert
    2026-08-16 auf dem Produktiv-Container** (nicht nur lokal): `collect_report_data()` +
    `build_excel_report()`/`build_pdf_report()` liefen direkt im Container gegen synthetische
    Sitzungsdaten durch, beide Formate valide (Excel via `openpyxl.load_workbook()` prüfbar,
    PDF mit korrektem `%PDF`-Header), AppTest-Smoke-Test der Startseite ohne Exceptions,
    HTTP 200 auf `/_stcore/health`.
- [x] **P15 — Referenzwerte im Glossar: typische Werte Gesunde/Dysarthrie/psychomotorische
      Verlangsamung + echte Primärliteratur** ✅ VOLLSTÄNDIG UMGESETZT (2026-08-16,
      Nutzer-Feedback 2026-08-16) — das Glossar (`build_glossary_entries()`/`render_glossary()`)
      soll pro Parameter, auch wenn kein harter Ampel-Cutoff existiert, eine QUANTITATIVE
      Einordnung liefern: typische Werte/Schwankungsbreite bei Gesunden, UND — soweit in der
      Literatur beschrieben — typische Werte/Richtung bei Dysarthrie bzw. bei psychomotorisch
      verlangsamtem Sprechen. Rein deskriptiv bleiben (kein Cutoff-Anspruch), aber konkrete
      Zahlen statt nur Prosatext. Zusätzlich: für viele Parameter fehlten echte Primärquellen
      (Publikationen mit Autor:innen/Jahr/Journal) — vorher oft nur Sekundärquellen-
      Zusammenfassungen referenziert. Größerer Rechercheaufwand, deshalb in Teilen umgesetzt:
  - **Stand 2026-08-16**: neues Feld `PARAMETER_INFO["typical_values"]`, durchgereicht via
    `interpret()`/`build_glossary_entries()`, angezeigt in `render_glossary()` UND in beiden
    Report-Formaten (`core/report_export.py`, Excel-Spalte + PDF-Absatz) — eine
    Datenquelle für alle drei Darstellungen.
  - **9 Parameter mit echter, primärquellen-basierter Recherche fertig** (die klinisch
    zentralsten, direkt zu Dysarthrie UND psychomotorischer Verlangsamung passend): Jitter,
    Shimmer, HNR, CPPS, MPT, DDK-Rate, Sprechrate, F0-Streuung (Monopitch), Vokalraum-Fläche
    (VSA). Konkrete Beispiele: DDK-Rate Gesunde 6,4/6,1/5,7 Silben/s vs. ataktische Dysarthrie
    3,8/3,9/3,4 Silben/s (Kent et al. 1979); VSA Gesunde ~310.517Hz² vs. Parkinson-Dysarthrie
    ~247.867Hz² (zwei unabhängige Studien, vorher hatte P12 explizit "keine Zahl gefunden"
    dokumentiert); Sprechrate bewusst OHNE einzelne Zahl dargestellt, da die Richtung bei
    Parkinson nicht einheitlich ist (manche Studien zeigen paradoxe Beschleunigung/
    "Festination", nicht nur Verlangsamung) — echte Literatur-Uneinigkeit transparent gemacht
    statt eine erfundene Konsens-Zahl zu behaupten (z.B. bei MPT: zwei Quellen mit
    unterschiedlichen Normwerten nebeneinander gezeigt, 25-35s Iowa-Sekundärquelle vs.
    21,4s malaysische Primärstudie).
  - Verifiziert: Regression über alle 40 `PARAMETER_INFO`-Einträge (`interpret()` liefert
    überall das neue Feld, auch `None` wo nicht vorhanden), AppTest über alle 7 Seiten sauber,
    Excel-/PDF-Export mit neuem Feld getestet.
  - **Teil 2 fertig (2026-08-16, gleicher Tag)**: verbleibende 13 Parameter recherchiert —
    RAP/PPQ5/APQ11, Artikulationsrate, Ø Pausendauer, Pausen (Anzahl), TTR, MTLD, Rhythmus
    (nPVI), Formant-Streuung F1/F2, DDK-Regelmäßigkeit (CV), Monoloudness. **22 von 40
    Parametern** haben jetzt `typical_values` (alle mit Evidenz "gut etabliert"/"in der
    Forschung diskutiert" — die übrigen 18 sind bewusst "eigene Heuristik"/"deskriptiv" ohne
    Literaturvergleichswert, dafür gibt es keinen sinnvollen zu recherchieren). Bemerkenswerte
    Funde: Ø Pausendauer bei Parkinson real nur moderat länger (0,396s vs. 0,345s bei
    Kontrollen, PLOS One 2025) — kein dramatischer Unterschied, wie man intuitiv erwarten
    könnte; TTR zeigte in einer Studie KEINEN signifikanten Unterschied Parkinson vs.
    Kontrollen (ehrliche Gegenposition zur naheliegenden Annahme, lexikalische Diversität ist
    primär ein sprachlich-kognitives, kein primär motorisches Maß). Bei mehreren Parametern
    (F1/F2-Streuung, RAP/PPQ5, nPVI) ehrlich dokumentiert, dass kein Wert für UNSERE exakte
    Kennzahl-Variante gefunden wurde, nur für verwandte Maße — keine erfundene Übertragung.
    Regression über alle 40 Parameter + AppTest über alle 7 Seiten erneut sauber, server-
    deployt und verifiziert.
- [x] **P16 — Interne Entwicklungs-Referenzen aus nutzersichtbaren Texten entfernen**
      ✅ UMGESETZT (2026-08-16, Nutzer-Feedback 2026-08-16) — `PARAMETER_INFO`-Texte
      (`context`/`literature`/`typical_values`) enthielten an vielen Stellen interne
      Entwicklungs-Markierungen wie "**P12-Recherche 2026-08-15**", "**P12**",
      "**P12-Nachtrag**", die nur für die eigene Nachvollziehbarkeit während der Entwicklung
      gedacht waren. Alle 10 Fundstellen in `PARAMETER_INFO` bereinigt (komplett durchgegangen,
      nicht nur Stichproben) — der fachliche Inhalt (was die Recherche ergeben hat) bleibt
      vollständig erhalten, nur die Entwicklungs-Meta-Markierung fällt weg. Auch die bei P15
      neu hinzugekommene interne Datierung im `vsa_hz2`-Eintrag ("nachträglich gefunden,
      2026-08-16") entfernt. Docstrings/Kommentare in `core/reference_ranges.py`/
      `core/interpretation.py` selbst bewusst NICHT angefasst — das sind reine
      Code-Kommentare, nicht auf der Oberfläche sichtbar, kein P16-Ziel.
      Verifiziert: Regression über alle 40 Parameter bestätigt keine `**P`-Marker mehr in
      `context`/`literature`/`typical_values`, projektweite Suche in `views/`+`core/` findet
      keine weiteren Fundstellen, AppTest über alle 7 Seiten sauber.

## Konzept: Modul-Detailseiten Nachbesserung — Sammel-Feedback nach P10-Testlauf (2026-08-15)

Nutzer hat nach der P10-Umsetzung erstmals wieder alle Module durchgeklickt (erste echte
3-Vokal-Aufnahme a/i/u, Vorlesen, Spontansprache) und ein dichtes Bündel an Beobachtungen
gemeldet. Hier dedupliziert/systematisiert, in Buckets nach Aufwand/Zusammenhang.
**Status: ✅ UMGESETZT (2026-08-15, nach Freigabe "Ja, macht das genauso") — Buckets A-E.
Bucket B mit Einschränkung siehe dort. Bucket F brauchte keine Aktion (siehe unten).**

### Bucket A — Kleine, risikoarme UI-Fixes ✅ UMGESETZT

- [x] **A1 — Hinweis: alle 3 Vokale empfohlen.** `views/vokalisation.py` zeigt jetzt einen
      `st.info()`-Hinweis direkt unter der Hero-Überschrift: /i/+/u/ sind optional, aber
      empfohlen (robustere Mittelwerte + echte VSA erst mit allen 3 Eckvokalen möglich).
- [x] **A2 — Textgrößen-Regler verschoben.** `instruction_text_scale_control()` (core/
      shared.py) nutzt jetzt `st.select_slider()` im Hauptbereich statt `st.sidebar.
      select_slider()`, per `key`-Parameter mehrfach instanzierbar (z.B. je Vokal-/DDK-Tab).
      Aufrufstelle in allen 4 Modulen + `testdaten.py` in eine `st.columns([4,1])`-Zeile direkt
      neben die jeweilige Instruktions-Card verschoben (schmale rechte Spalte).
      Verifiziert: Sidebar-Regler-Liste leer, Hauptbereichs-Regler korrekt vorhanden (3× bei
      Vokalisation/DDK wegen Tabs, 1× bei Vorlesen/Spontansprache/Testdaten).

### Bucket B — Mehrere Lesetext-Varianten ⚠️ UMGESETZT MIT EINSCHRÄNKUNG

- [x] **B1 — 3 Lesetexte, ABER nur einer davon ist echter IPA-Referenztext.**
      `views/vorlesen.py::LESETEXTE` jetzt ein Dict mit 3 Einträgen (`nordwind`/`bauer`/`wald`),
      je ~27 Wörter, Hauptsatz+Nebensatz-Struktur analog zum Original. Zufallsauswahl einmal
      pro Sitzung (`st.session_state["lesetext_choice"]`, bleibt über alle Versuche derselben
      Sitzung konsistent für Take-Vergleichbarkeit), zusätzlich manuelles Umschalten über einen
      Expander "Anderen Text wählen". Gewählter Text wird als `lesetext_key` im Take gespeichert
      (Reproduzierbarkeit) und beim ausgewählten Versuch als Caption angezeigt.
      **WICHTIG/Einschränkung**: nur "Nordwind und Sonne" ist der etablierte IPA-Referenztext
      (`docs/lesetext_nordwind_sonne.md`). "Der Bauer und die Tiere"/"Der Waldspaziergang" sind
      selbst verfasste, NUR praktische Alternativtexte (vergleichbare Länge/neutrale, einfache
      Satzstruktur) — bewusst NICHT als gleichwertig validierte phonetische Referenztexte
      ausgegeben, das wird in Code-Kommentar UND UI-Caption explizit offengelegt. Die im
      Konzept vorgesehene "eigene Recherche/Quellenlage" nach echten etablierten deutschen
      Alternativtexten wurde NICHT gemacht (kein Zugriff auf Fachliteratur-Datenbanken) — falls
      echte validierte Alternativtexte gefunden werden, sollten sie diese ersetzen.

### Bucket C — Fehlende Kacheln/Kontext für bereits vorhandene Werte ✅ UMGESETZT

- [x] **C1 — Monoloudness/Formant-Streuung/Intonationskontur als Kacheln.** Neue
      `PARAMETER_INFO`-Einträge für `f1_iqr_hz`/`f2_iqr_hz` (core/interpretation.py) ergänzt.
      `views/vorlesen.py` + `views/spontansprache.py`: die alte `c1/c2/c3`-`st.metric()`-Zeile
      entfernt, alle 6 akustischen Werte (Artikulationsschärfe/CPPS/Monoloudness/Formant-
      Streuung F1+F2/Intonationskontur) laufen jetzt einheitlich über `build_tiles()` in einer
      gemeinsamen Kachel-Reihe unter "Ergebnisse".
- [x] **C2 — Ø Wortdauer.** Neues `mean_word_duration_s` in `core/speech_metrics.py::
      compute_speech_metrics()` (nutzt die für nPVI ohnehin schon berechneten
      `word_durations`, kein neuer Datenpfad) + `PARAMETER_INFO`-Eintrag, erscheint als eigene
      Kachel in der neuen "Sprechrate"-Gruppe (siehe D1).

### Bucket D — Transkript-Metrik-Wand ✅ UMGESETZT

- [x] **D1 — Kachel-Umbau mit Gruppierung.** Die ehemalige `m1-m4`/`p1-p4`/`q1-q3`-
      `st.metric()`-Wand in `views/vorlesen.py` + `views/spontansprache.py` ist durch 3
      gruppierte Kachel-Reihen ersetzt ("Sprechrate": Wörter/Netto-/Artikulationsrate/
      Flüssigkeits-Score/Ø Wortdauer: "Pausen": Anzahl/Ø-/Max-Dauer/Rhythmus/Mikro-/
      Makropausen inkl. deren Ø-Dauern; "Lexik": TTR/MTLD), je mit Überschrift + automatischem
      Erklärungstext aus `PARAMETER_INFO`. Dafür 12 neue `PARAMETER_INFO`-Einträge ergänzt
      (u.a. `n_words`, `articulation_rate_wpm`, `fluency_score`, `rhythm_npvi`,
      `mean_pause_duration_s`, `max_pause_duration_s`, `micro_pause_count`/`macro_pause_count`
      + deren Ø-Dauern, `mtld`).

### Bucket E — Spinnennetz-/Radardiagramm ✅ UMGESETZT (gedämpfte Variante)

- [x] **E1 — Optionales Radar-Profil in eigenem Expander.** `core/plots.py::radar_figure()`
      (bereits gedämpft: EIN Akzentton, dünne Kontur, `alpha=0.22`-Füllung, aus einem früheren
      Design-Tokens-Umbau — keine Anpassung nötig) jetzt zusätzlich in `views/vorlesen.py` +
      `views/spontansprache.py`, in einem eigenen Expander "Profil auf einen Blick (Radar)"
      NACH den Kacheln (nicht als Ersatz). 4 Achsen: Sprechrate (normalisiert über
      `speech_rate_zones()`), Flüssigkeit (`fluency_score`, schon 0-1), Rhythmus
      (`rhythm_npvi/100`, geclippt), Lexikalische Diversität (`ttr`, schon 0-1) — bewusst nur
      Werte mit sinnvoll herleitbarer 0-1-Normalisierung, nicht alle Transkript-Werte. Mit
      explizitem Caption-Hinweis ("zusätzliche Verdichtung, keine Diagnose, ersetzt nicht die
      Kacheln").

### Bucket F — keine Aktion nötig (siehe Konzept-Text oben)

**Verifiziert (2026-08-15)**: End-to-End auf dem Server — A1-Hinweis + verschobene
Textgrößen-Regler (Sidebar leer, Hauptbereich korrekt befüllt, 3× bei Vokalisation/DDK wegen
Tabs) bestätigt, "Anderen Text wählen"-Expander vorhanden, mit echter Aufnahme+Cache-
Transkript alle 25 erwarteten Kacheln (Qualität+Akustik+Sprechrate+Pausen+Lexik) inkl. aller
C1/D1-Werte und der 3 Gruppentitel bestätigt, Radar-Expander erreicht ohne Exception.
Regressionstest über alle 7 Seiten ohne Exception, HTTP 200 nach Deploy.

## Live-Test-Nachbesserung + 2 neue Konzepte (2026-08-15)

Beim ersten Live-Testen von P10-P12 gemeldet, hier gesammelt:

- [x] **Bug: Textgrößen-Einstellung fiel beim Tab-Wechsel zurück** ✅ BEHOBEN — jeder Vokal-/
      DDK-Tab hatte einen EIGENEN, unabhängigen Widget-Zustand
      (`st.select_slider(key=f"text_scale_{key}")`), dadurch sprang die Größe beim Wechsel
      zwischen /a/,/i/,/u/ wieder auf "Normal" zurück, obwohl sie auf einem anderen Tab schon
      gesetzt war. Fix: EIN gemeinsamer `st.session_state["text_scale"]`-Wert über die ganze
      Sitzung (auch seitenübergreifend), `key`-Parameter dient nur noch der Erzeugung
      eindeutiger Button-Widget-IDs. Gleichzeitig auf `st.button()`-Gruppe statt
      `st.select_slider()` umgestellt (Nutzer-Feedback: "kein Regler, eher Buttons").
      Verifiziert: Klick auf "Groß" setzt `session_state["text_scale"]` korrekt, CSS-Skalierung
      greift, Slider vollständig ersetzt (9 Buttons statt 3 Slider über die 3 Vokal-Tabs).
- [x] **Instruktions-Karten: Sprech-Ziel war kleiner/dünner als der Meta-Text** ✅ BEHOBEN —
      z.B. bei DDK stand "**Sprich so schnell und gleichmäßig wie möglich**" fett, aber
      „pa-ta-ka..." (das eigentlich zu Sprechende) normal — genau umgekehrt zur Priorität.
      Neue CSS-Klassen `.dw-instruction-meta` (normal, gedämpfte Farbe) und
      `.dw-instruction-target` (fett, 1,35em, primäre Textfarbe) in `core/shared.py`.
      Durchgezogen in allen 4 Guide-Modulen + `testdaten.py`s Upload-Instruktionen
      (Vokalisation, Vorlesen, DDK kombiniert+einzeln, Lesetext/Vokal/DDK im Testdaten-Modus).
      Spontansprache unverändert gelassen (kein fester Text zum Vorsprechen, Instruktion IST
      der Inhalt). Verifiziert: beide CSS-Klassen korrekt im HTML vorhanden.

- [x] **Audio-Piep bei Aufnahmestart** ✅ UMGESETZT (2026-08-16) — zusätzlich zum bestehenden
      visuellen Hinweis (roter Rahmen-Tint) signalisiert jetzt ein kurzer, leiser Ton, dass
      die Aufnahme läuft. Neue `core/shared.py::recording_start_blip()`: `MutationObserver`
      auf `window.parent.document`, der das Erscheinen eines Stop-Buttons
      (`aria-label*="Stop"`) erkennt und dabei einen 880Hz-Sinuston (~120ms, sanfte Gain-
      Hüllkurve, Pegel 0,12) über die Web Audio API abspielt — synthetisch erzeugt, kein
      Audio-Datei-Asset. Einmal pro Seite aufgerufen (nicht pro Tab), Guard-Flag auf `document`
      verhindert doppelte Observer bei Streamlit-Reruns, `WeakSet` verhindert Mehrfach-Piepser
      für denselben Button. Eingebaut in alle 4 Guide-Module + `testdaten.py`.
  - **Abweichung vom ursprünglichen Konzept**: `st.components.v1.html()` war zur Umsetzungszeit
    bereits als "wird nach 2026-06-01 entfernt" markiert (Streamlit-Deprecation-Warnung beim
    Testen entdeckt) — auf die empfohlene Nachfolge-API `st.iframe()` mit HTML-String
    umgestellt (unterstützt laut Doku explizit JavaScript-Ausführung + Same-Origin-Zugriff,
    verhält sich für diesen Zweck identisch).
  - **NICHT auditiv/visuell im Sandbox-Browser verifizierbar** — der Sandbox-Browser kann die
    Tailscale-Origin gar nicht erreichen (`ERR_BLOCKED_BY_CLIENT`), unabhängig vom fehlenden
    Mikrofonzugriff. Verifiziert wurde nur: `AppTest`-Regression über alle 7 Seiten ohne
    Exception, keine Deprecation-Warnung mehr im Server-Log, HTTP 200 nach Deploy. **Bitte
    beim nächsten echten Test bestätigen** — insbesondere Lautstärke/Charakter des Tons und
    Autoplay-Verhalten in Safari (dort strenger als Chrome/Firefox).

- [ ] **Konzept: Zukunfts-Parameter — Geschlecht/Alter/Nervosität aus der Stimme** (Nutzer-
      Interesse 2026-08-15, "perspektivisch entwickeln", NICHT priorisiert/terminiert) —
      Literaturrecherche siehe `docs/literatur_review.md`, Abschnitt "Perspektivische
      Zusatzparameter". Kurzfassung:
  - **Geschlechtserkennung**: solide Evidenzlage (92-99% Genauigkeit in Studien), technisch
    einfach umsetzbar, da F0/Formanten/MFCCs bereits berechnet werden — nur Klassifikations-
    Logik auf vorhandenen Werten fehlt. Voraussichtlich der am leichtesten umsetzbare der
    3 Zukunfts-Parameter, FALLS gewünscht.
  - **Alterserkennung**: moderate Evidenzlage (nur grobe Altersgruppen, ~62% Trefferquote bei
    Erwachsenen) — fraglich sinnvoll, da Alter im Rahmen von P10 ohnehin schon manuell erfasst
    wird. Eher als Konsistenz-/Plausibilitäts-Check denkbar als als Haupt-Feature.
  - **Nervosität/Stress**: uneinheitliche Evidenzlage — Stress allgemein zeigt grobe
    Prosodie-Korrelate (F0/Intensität hoch, Sprechdauer runter), aber für Angst/Nervosität
    speziell wurden in einem systematischen Review KEINE konsistenten akustischen Muster über
    Studien hinweg gefunden. Würde nur eine unsichere, explorative Zusatzinfo liefern.
  - **"Lügenerkennung"**: **wissenschaftlich widerlegt** (Voice Stress Analysis, US National
    Research Council 2003: Erkennungsraten nicht über Zufallsniveau; Feldtest nur 15%
    Trefferquote). **Empfehlung: NICHT umsetzen** — würde dem Projektprinzip "ehrlich über die
    Grenzen der Methode" widersprechen und Nutzer:innen in die Irre führen.
  - Keine Umsetzungs-Priorität/Zeitplan festgelegt — reine Wissens-/Machbarkeits-Notiz für
    später, auf expliziten Wunsch des Nutzers.

## Sammel-Feedback zweiter Live-Testlauf (2026-08-15) — noch NICHT umgesetzt

Nutzer hat nach P11/P12 weiter getestet. Hier dedupliziert/systematisiert, in Buckets. **Status:
reines Backlog, nichts umgesetzt** — Umsetzung erst nach Freigabe, dann Stück für Stück.

### Bucket G — Lokale HTTPS-Lösung für Endnutzer (WICHTIG, generischer als bisher gedacht)

- [x] **G1 — Mikrofonzugriff muss auch OHNE Tailscale lokal funktionieren** ✅ UMGESETZT
      (2026-08-17). Konzept mit 5 Optionen (mkcert/Caddy/selbstsigniert/Tailscale-optional/
      Domain+Let's-Encrypt) + Analyse + Empfehlung siehe
      [docs/konzept_g1_mikrofon_ohne_tailscale.md](konzept_g1_mikrofon_ohne_tailscale.md).
      Umgesetzt: (1) README-Hinweis, dass `http://localhost:8501` bereits ohne HTTPS
      funktioniert (`localhost` ist laut W3C-Spec immer ein sicherer Kontext, deckt den
      Solo-Fall komplett ab); (2) optionales `https`-Compose-Profil mit Caddy als Reverse
      Proxy (`dashboard/Caddyfile.local`, `dashboard/docker-compose.local.yml`) für den
      Mehrgeräte-Fall, inkl. README-Anleitung zum einmaligen CA-Import je Plattform. Beim
      Verifizieren (Standalone-Caddy-Test, ohne die schweren WhisperX-Container zu bauen)
      einen echten Konfigurationsfehler gefunden+behoben: `tls internal` allein ließ den
      TLS-Handshake auf dem hostnamenlosen `:8443`-Listener fehlschlagen, gefixt mit
      `tls internal { on_demand }`.

      Ursprüngliche Klarstellung vom Nutzer: es geht NICHT nur um Komfort (kürzere URL) — Menschen, die die Applikation
      tatsächlich NUTZEN (nicht nur wir selbst), sollen sie lokal auf ihrem eigenen MacBook
      oder einem eigenen Server betreiben können, ohne von unserer privaten Tailscale-
      Infrastruktur abhängig zu sein. Browser verweigern `getUserMedia` (Mikrofonzugriff)
      grundsätzlich auf unverschlüsseltem HTTP — das betrifft JEDEN, der die App lokal
      startet, nicht nur unseren aktuellen Beelink-Server.
  - **Zu prüfende Lösungsansätze** (noch keine Entscheidung getroffen):
    1. **`mkcert`** — erzeugt eine lokal vertrauenswürdige CA + Zertifikat für `localhost`/
       die eigene LAN-IP, komplett offline, kein Domain-/DNS-Aufwand. Müsste als Teil der
       Setup-Doku (README/Deployment-Guide) dokumentiert werden — jede:r Betreiber:in
       generiert sich eigene lokale Zertifikate.
    2. **Caddy mit automatischem HTTPS** für `localhost` (Caddy kann seit einiger Zeit lokal
       vertrauenswürdige Zertifikate für `localhost` selbst ausstellen, ähnlich mkcert intern)
       — evtl. der geringste Konfigurationsaufwand, wenn Caddy ohnehin schon als Reverse-Proxy
       im Deployment-Stack verwendet wird.
    3. **Dokumentations-Lösung statt Code-Änderung**: ggf. reicht eine klare Anleitung im
       README ("Für Mikrofonzugriff lokal: `mkcert -install` + `mkcert localhost` ausführen,
       dann `streamlit run --server.sslCertfile=... --server.sslKeyFile=...`") — evtl. keine
       App-Code-Änderung nötig, nur Betriebsanleitung.
  - Betrifft potenziell den gesamten Public-Release-Fahrplan (falls die App irgendwann von
    Fremden selbst gehostet werden soll) — deutlich höhere Priorität als ursprünglich
    eingeordnet, da kein reines Komfort-Thema.

### Bucket H — Fehlende Kacheln in Vokalisation + DDK ✅ UMGESETZT (2026-08-16)

- [x] **H1 — Vokalisation: F0 (Mittel), Voice Breaks, Formanten F1/F2/F3 jetzt Kacheln.** Neue
      `PARAMETER_INFO`-Einträge `f0_mean_hz`, `voice_breaks_count`, `voice_breaks_degree_pct`,
      `f3_mean_hz` ergänzt (F1/F2 gab es schon). `voice_breaks_degree_pct` bekommt eine neue,
      bewusst pragmatische `voice_breaks_zones()` (Praat-Dokumentation nennt 0% als
      Normativwert für gesunde gehaltene Vokale, aber keinen graduierten Cutoff — Zonen-
      Grenzen deshalb als "eigene Heuristik" gekennzeichnet, nicht als zitierbare Einzelquelle
      wie bei P12). `views/vokalisation.py`: alte `c1/c2/c3`-`st.metric()`-Zeile entfernt,
      zweite Kachel-Reihe ergänzt.
- [x] **H2 — DDK: Zyklen-Regelmäßigkeit (CV) und Ø Zyklus-Intervall jetzt Kacheln.** Neuer
      `PARAMETER_INFO`-Eintrag `mean_cycle_interval_s` (bewusst OHNE eigene Zone — inhaltlich
      redundant zur DDK-Rate, um nicht zweimal dieselbe Information unterschiedlich zu
      bewerten). `cycle_interval_cv` (schon vorhanden, ohne Zone) + `mean_cycle_interval_s` in
      `views/ddk.py`s `tile_keys` ergänzt, `st.metric()`-Zeile entfernt, "Zyklen erkannt"
      bleibt als einfache Caption (reiner Datenqualitäts-Indikator, kein klinischer Parameter).

### Bucket I — Kacheln zeigen Normbereich/Einheit nicht direkt sichtbar genug ✅ UMGESETZT (2026-08-16)

- [x] **I1 — Normbereich jetzt direkt auf der Kachel sichtbar.** `core/interpretation.py::
      build_tiles()` liefert jetzt zusätzlich `range_text` (nur gesetzt, wenn ein echter
      `zones_func` existiert — bei "kein Normwert"-Parametern bewusst leer). Neuer
      `range_text`-Parameter in `core/shared.py::kpi_tile()`, eigene neutral eingefärbte Zeile
      "Norm: 5-8Hz" unterhalb des Status-Labels (nicht in der Status-Farbe, da Fakt statt
      Bewertung). Wirkt sich automatisch auf alle Kacheln app-weit aus, kein Modul-für-Modul-
      Umbau nötig. Verifiziert: Kacheln MIT Zone (Jitter/Shimmer/HNR/CPPS/DDK-Rate/Sprechrate)
      zeigen die Range korrekt, Kacheln OHNE Zone bleiben ohne Range-Zeile.

### Bucket J — Weitere Einzelpunkte

- [ ] **J1 — Idee: Lesetext vorlesen lassen (Text-to-Speech)** für sehschwache Nutzer:innen,
      die den Text dann eher nachsprechen als lesen. Neue Funktionalität, braucht eigene
      Recherche (welche TTS-Engine lokal, ohne Cloud-Abhängigkeit — passt zum
      Datenschutz-Prinzip des Projekts, ähnlich wie die WhisperX-Entscheidung für lokale
      Transkription statt Cloud-API).
- [ ] **J2 — Radar-Diagramm bei Vorlesen (Sprechrate/Flüssigkeit/Lexik/Rhythmus) "nicht
      wirklich gelungen"** — Nutzer-Feedback nach dem ersten echten Anschauen: aktuelle
      Umsetzung (`core/plots.py::radar_figure()`, siehe Bucket E oben) überzeugt nicht, braucht
      eine andere Darstellung. Noch keine konkrete Alternative festgelegt — die schon in
      Bucket E notierte Design-Sorge ("darf nicht wieder wie ein Dashboard wirken") hat sich
      damit bestätigt. Mögliche Alternativen zu prüfen: horizontale Balken-Vergleichsreihe
      statt Polygon, Sparkline-Zeile, oder ganz auf das Radar verzichten und nur bei den
      Kacheln bleiben.
- [x] **J3 — Transkriptions-Modell jetzt sichtbar** ✅ UMGESETZT (2026-08-16, nachgebessert
      2026-08-16) — kleine Eyebrow-Zeile "Transkription: WhisperX (Modell large-v3)" direkt über
      dem Transkript-Text in `views/vorlesen.py` + `views/spontansprache.py` ergänzt (liest
      `core.transcription.DEFAULT_MODEL` zentral aus, keine hartkodierte Versionsnummer).
      **Nachbesserung**: stand ursprünglich nur NACH abgeschlossener Transkription — Nutzer-
      Feedback beim zweiten Testlauf: soll schon VOR dem Start sichtbar sein, damit klar ist,
      was gleich passiert (und dass es dauert). Jetzt zentral in
      `core/shared.py::render_transcription_job()` als Caption ganz oben (vor Button/
      Fortschrittsanzeige/Cache-Treffer) — gilt automatisch für alle Aufrufer.
- [x] **J4 — Proband:innen-ID/Alter nachträglich editierbar.** Neue `rename_subject()` in
      `core/subject_store.py` (verschiebt die Index-Datei, kollisionsgeprüft). Sidebar-Badge
      (`core/shared.py::render_subject_badge()`) bekam zwei Buttons "Bearbeiten"/"Neu", die zur
      Startseite springen und dort per Flag den passenden Modus zeigen. `views/start.py` neu in
      3 Zustände: normal/Bearbeiten (Formular mit ID+Alter, Speichern/Abbrechen)/Verwerfen-
      Bestätigung. Bewusste Einschränkung: ältere, bereits abgeschlossene Sitzungsdateien unter
      anderen `session_id`s behalten die alte ID im Snapshot — nur Tippfehler-Korrektur, keine
      volle Historien-Migration.
- [x] **J5 — Proband:in verwerfen/neu beginnen ohne Server-Reload.** "Neu"-Button (Sidebar) →
      Bestätigungsdialog auf `views/start.py` → löscht `subject_id`/`subject_age`/
      `module_results` aus `st.session_state` UND den `session`-Query-Parameter (sonst würde
      `load_session_snapshot()` beim nächsten Rerun die alte Zuordnung zurückholen) → frische
      `session_id` wird beim nächsten `get_session_id()`-Aufruf gemintet. Nicht-destruktiv:
      bereits gespeicherte Aufnahmen/Analysen bleiben auf dem Server, über "Bekannte:r
      Proband:in fortsetzen" wieder erreichbar.
- [x] **J6 — Piepton-Zuverlässigkeit gehärtet** ✅ ECHTER ROOT CAUSE GEFUNDEN + BEHOBEN
      (2026-08-17). Erster Versuch (2026-08-16, `setInterval`-Poll als Netz zum
      MutationObserver) hatte das eigentliche Problem NICHT behoben — Nutzer bestätigte beim
      nächsten Test weiterhin "nur bei Vokalisation ein Ton". Tatsächlicher Fund per
      DOM-Inspektion im laufenden lokalen Docker-Stack (`docker-compose.local.yml`, Browser-
      Tool): das `doc.__nvBlipInstalled`-Flag lebt zwar auf dem äußeren, über Seitenwechsel
      hinweg bestehenden Streamlit-Dokument (Single-Page-App) — der eigentliche
      `MutationObserver`/`setInterval` läuft aber IM IFRAME SELBST. Wechselt man die Seite,
      zerstört Streamlit das alte Iframe samt seinem Observer, das neue Iframe sieht aber
      "schon installiert" und registriert nichts Neues — ab dem ersten Seitenwechsel lauscht
      nirgendwo mehr ein lebender Observer. Fix (`core/shared.py::recording_start_blip()`):
      kein dauerhaftes Flag mehr, stattdessen bei jedem Iframe-Lauf alten (ggf. toten)
      Observer/Timer abmelden und einen frischen installieren. Verifiziert per simuliertem
      "Stop"-Button (kein echtes Mikrofon nötig): auf Vorlesen UND Spontansprache nach echtem
      Seitenwechsel feuert der Trigger jetzt nachweisbar (`AudioContext` wird erzeugt bzw.
      Button wird korrekt markiert). Deployed auf den Server, HTTP 200 verifiziert.
- [x] **J7 — Glossar aus Excel/PDF-Report entfernt.** Nutzer-Feedback: Report soll nur die
      reinen Werte enthalten, keine Erklärtexte/Literatur. `core/report_export.py`:
      `collect_report_data()` sammelt kein Glossar mehr, Excel-Sheet "Glossar" entfernt,
      PDF-Abschnitt "Glossar & Literatur" entfernt. Die Live-Ansicht (`views/gesamtbericht.py`)
      zeigt das Glossar weiterhin unverändert (baut es unabhängig vom Report selbst auf).

**Bereits (teilweise) vorhanden, zur Klarstellung**: die allgemeine Forderung "mehr Kontext/
Literatur bei den Werten" ist strukturell bereits durch P11 (Kompakte Übersicht + Glossar) und
P12 (Referenzwerte) angegangen — der verbleibende Rückstand ist NICHT fehlende Recherche,
sondern fehlende SICHTBARKEIT der bereits recherchierten Werte direkt auf der Kachel (siehe
Bucket I) sowie die in Bucket H aufgelisteten, noch nicht auf Kacheln umgestellten Parameter.

## Road to Public — Konzept (2026-08-16, NICHT umgesetzt)

Vollständiges Konzept liegt als [`ROAD_TO_PUBLIC.md`](../ROAD_TO_PUBLIC.md) im Repo-Root
(analog zum bereits abgeschlossenen Fahrplan bei `anonymisator` und `edf-analyzer`) — Repo
bleibt **privat**, nichts davon wurde umgesetzt. Kurzfassung der wichtigsten Funde:
- README ist seit dem allerersten Commit (21.07.) nicht mehr aktualisiert — beschreibt einen
  Stand, der mit der heutigen App kaum noch etwas zu tun hat. Größter Einzelpunkt.
- `LICENSE`/`CITATION.cff`/`SECURITY.md` fehlen komplett (anders als bei beiden
  Schwesterprojekten zu deren jeweiligem Public-Zeitpunkt).
- Reale Tailscale-IP/Hostname in `docs/backlog.md`/`docs/bugtracker.md`/
  `dashboard/docker-compose.yml` — braucht eine Nutzer-Entscheidung (bereinigen vs. bewusst
  akzeptieren, wie beim EDF-Analyzer).
- Kein Auth-Layer vorhanden (anders als EDF-Analyzer) — kein Sicherheitsleck für die
  Repo-Veröffentlichung selbst, aber muss in `SECURITY.md` explizit stehen, gerade weil die App
  seit P10 echte Proband:innen-IDs+Alter sammelt.
- **Lizenzfrage anders als bei den Geschwistern**: `praat-parselmouth` ist eine harte,
  überall genutzte GPL-3.0-Abhängigkeit (nicht optional wie `py-ecg-detectors` beim
  EDF-Analyzer) — spricht eher für GPL-3.0 statt Apache-2.0 für NeuroVoice AI selbst, reine
  Einordnung, keine Rechtsberatung, Entscheidung liegt beim Nutzer.
- Volle Commit-Historie bereits sauber geprüft (83 Commits) — keine Audio-/Session-/
  Proband:innen-Dateien jemals committet, `.gitignore` hat von Anfang an funktioniert.

## Sammelblock: Visualisierungsideen (2026-08-16, NICHT umgesetzt)

Eigener Sammelort für kreative Darstellungs-Ideen, die noch nicht ausgereift/priorisiert genug
für ein eigenes P-Item sind — bei Bedarf von hier in einen konkreten Bucket überführen.
Hängt lose mit J2 (Radar-Redesign) zusammen, aber bewusst als eigener, wachsender Block
gedacht statt an ein einzelnes Item gebunden zu sein.

- [x] **V1 — Histogramm der Wortdauern** ✅ UMGESETZT (2026-08-16) — bei Spontansprache UND
      Vorlesen die einzelnen Wortdauern als Histogramm mit Mittelwert-Linie
      (`core/plots.py::word_duration_histogram_figure()`). Teil des Visualisierungskonzepts,
      siehe `docs/konzept_visualisierungen.md`.
- [x] **V2 — Sechs weitere Visualisierungen aus dem Konzept** ✅ ALLE UMGESETZT (2026-08-16) —
      siehe `docs/konzept_visualisierungen.md` für Details/Screenshots-Beschreibungen:
      Vokaltrapez (F1/F2-Dreieck der Eckvokale, macht VSA sichtbar), Sprechfluss-Zeitstrahl
      (Sprech-/Pausensegmente farbcodiert), DDK-Rhythmus-Spur (Silben-Onsets + Intervall-
      Balken), gebündeltes Perturbations-Diagramm (alle 5 Jitter-/Shimmer-Maße mit Normwert-
      Referenzlinie, nutzt neues `core/reference_ranges.py::good_zone_bounds()`), Sprechrate/
      Pausenzeit-Balken (Artikulations- vs. Pausenzeit gestapelt). Alle server-verifiziert
      (AppTest + HTTP 200 nach jedem Schritt), einzeln committed.
      **Teil 2 — großes Nutzer-Feedback 2026-08-16 mit ~35 weiteren Visualisierungsideen
      (Speech-Motor-Landscape-Konzept)**: ausführlich gesichtet und triagiert, siehe
      `docs/konzept_visualisierungen.md` Abschnitt "Teil 2" für die vollständige Einordnung —
      mehrere Ideen (synchronisierte Speech-Rail-Zeitachse, Patient-vs-Norm-Z-Score-Profil,
      Vokal-Trajektorie über Zeit) sind mit vorhandenen Daten umsetzbar und als neue V-Punkte
      unten aufgenommen; andere (Phänotyp-Klassifikation, SHAP-Erklärungen, Motor-Space via
      PCA/UMAP über Patientenkohorten) verletzen explizit die bestehenden Projekt-Prinzipien
      (keine Diagnose/Score, kein ML ohne echte gelabelte Patientendaten) und werden NICHT
      verfolgt; wieder andere (Longitudinal-Trajektorien, artikulatorische Mundraum-Animation)
      brauchen Daten, die es noch nicht gibt (Mehrfach-Sitzungen, EMA/Acoustic-to-
      Articulatory-Inversion).
- [ ] **V3 — Patient-vs-Norm-Profil (alle Parameter)** (Nutzer-Feedback 2026-08-16, NICHT
      umgesetzt) — Generalisierung des bereits gebauten `perturbation_bundle_figure()`-Musters
      (Wert als Vielfaches des Normwert-Cutoffs, Referenzlinie bei 1,0) auf ALLE 22 Parameter
      mit `typical_values`/Cutoff aus P15, nicht nur die 5 Jitter-/Shimmer-Maße. Geringster
      Aufwand der Teil-2-Ideen, da `good_zone_bounds()` bereits die komplette Infrastruktur
      liefert — siehe `docs/konzept_visualisierungen.md` Teil 2, Punkt A.2. Empfohlen als
      nächster Schritt, falls diese Runde weitergeführt wird.
- [ ] **V4 — Vokal-Trajektorie über Zeit ("Vowel Flight")** (Nutzer-Feedback 2026-08-16, NICHT
      umgesetzt) — F1/F2-Bewegung WÄHREND einer Äußerung statt nur der Mittelwert-Punkte im
      bestehenden Vokaltrapez. Braucht `formant_features()`/`formant_dynamics_features()`
      erweitert um Frame-für-Frame-F1/F2-Rohdaten (aktuell nur aggregiert) — dieselben Werte
      werden intern in `spectrogram_figure()` schon einmal berechnet, nur nicht persistiert.
      Siehe `docs/konzept_visualisierungen.md` Teil 2, Punkt A.3. Öffnet danach auch
      Vokalraum-Dichtekarte/Trajektorie-Ellipse (Punkt B) als Folgeschritte.
- [ ] **V5 — Speech Rail (synchronisierte Multi-Track-Zeitachse)** (Nutzer-Feedback 2026-08-16,
      NICHT umgesetzt) — Audio-Wellenform, Wörter, F0, Intensität, Formanten, Pausen auf EINER
      gemeinsamen Zeitachse statt in getrennten Plots, ähnlich einem Genome-Browser. Vom
      Nutzer selbst als wichtigste Einzelvisualisierung eingestuft. Größter Aufwand der
      Teil-2-Ideen, im Kern eine Zusammenführung/Erweiterung des bereits gebauten
      `pause_timeline_figure()` mit bereits vorhandenen F0-/Intensitäts-/Formant-Daten. Siehe
      `docs/konzept_visualisierungen.md` Teil 2, Punkt A.1.
- [ ] **V6 — Tremor-Modulationsspektrum** (Nutzer-Feedback 2026-08-16, NICHT umgesetzt) —
      `f0_tremor_features()` berechnet intern bereits ein Spektrum der F0-Zeitreihe, gibt aber
      nur die Peak-Frequenz zurück. Additive Erweiterung (Muster wie bei den DDK-`cycle_times`,
      P9-Umbau), zeigt das volle Frequenz-×-Power-Spektrum statt nur eines Einzelwerts. Siehe
      `docs/konzept_visualisierungen.md` Teil 2, Punkt A.4.
- [ ] **Konzept: Interaktive Visualisierungen (Plotly statt matplotlib)** (Nutzer-Feedback
      2026-08-16, NICHT umgesetzt, nur als Entscheidungspunkt vermerkt) — Hover-Tooltips,
      Zeitbereich markieren mit synchronem Reagieren aller Plots (Idee aus dem Teil-2-Feedback)
      bräuchten einen Wechsel von `st.pyplot()` (statische Bilder) zu einer JS-basierten
      Chart-Bibliothek (z.B. Plotly via `st.plotly_chart()`) — eine grundsätzliche Tech-Stack-
      Entscheidung, die VOR größeren neuen Zeitachsen-Visualisierungen wie V5 getroffen werden
      sollte, siehe `docs/konzept_visualisierungen.md` Teil 2, Punkt B.

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

- [x] Streamlit-Grundgerüst (Datei auswählen → Player → Wellenform) — läuft auf `<TAILSCALE-IP>:8501`, Code in `dashboard/`
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
- [x] **RAP, PPQ5, APQ11** ✅ UMGESETZT (P7, 2026-08-15) — Stand 2026-08-16 beim Aufräumen
      dieser Liste als stale erkannt: war hier noch als offen markiert, ist aber seit P7 fertig
      (`jitter_rap_pct`/`jitter_ppq5_pct`/`shimmer_apq11_pct` in `core/audio.py`).
- [x] **Maximum Phonation Time (MPT)** ✅ UMGESETZT (P7, 2026-08-15) — dito, `mpt_s` in
      `core/audio.py` existiert bereits, war hier nur nicht mehr synchron.
- [x] **Vokalraum-Fläche (VSA), echte Dreiecksformel** ✅ UMGESETZT — `vowel_space_area()` in
      `core/audio.py` existiert bereits (`vsa_hz2` in `PARAMETER_INFO`), war hier nur nicht
      mehr synchron. Kein Ampel-Cutoff (siehe P12-Recherche zu `vsa_hz2`), aber die Berechnung
      selbst ist fertig.
- [x] **Recording Quality Check** ✅ UMGESETZT (P6, 2026-08-15) — SNR/Clipping/Stille-Anteil,
      bewusst informativ ohne hartes Cutoff-Gate wie hier gefordert. War hier nur nicht mehr
      synchron.

**Prio 2 — moderater Aufwand, baut auf vorhandenen Daten/Funktionen auf:**
- [x] **F0-Tremor-Analyse** ✅ UMGESETZT — `f0_tremor_features()` in `core/audio.py`
      (`tremor_freq_hz` in `PARAMETER_INFO`, rein explorativ/nicht klinisch validiert). War
      hier nur nicht mehr synchron.
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
- [x] **Speech-Intelligibility-Score (WER/CER)** ✅ UMGESETZT (2026-08-17, Nutzer-Idee: "das
      Sprachmodell versagt bei Dysarthrie" objektivieren) — neues
      `core/speech_intelligibility.py::compute_intelligibility_score()`, vergleicht die
      WhisperX-Transkription gegen den bekannten Lesetext (`views/vorlesen.py::LESETEXTE`,
      Referenztext-Zuordnung war über `lesetext_key` je Take schon vorhanden). Eigene
      Levenshtein-Editierdistanz (keine neue Abhängigkeit), WER (Wortebene) + CER
      (Zeichenebene, feinere Auflösung). Bewusst OHNE eigenen Normbereich — Websuche 2026-08-17
      ergab zu große Streuung zwischen ASR-Systemen/Studien für einen seriösen Cutoff (gesunde
      Sprache ~6-27% WER, dysarthrische Sprache ~62-135% je nach Studie/System), stattdessen
      als Kontext-Text hinterlegt. Neue `PARAMETER_INFO`-Einträge `wer_pct`/`cer_pct` —
      erscheinen dadurch automatisch auch im Gesamtbericht/Export/Glossar (kein Zusatzaufwand
      an diesen Stellen nötig, bestehende `flatten_take()`/`build_rows()`-Pipeline greift).
      Nur im Vorlesen-Modul (einziger Task mit bekanntem Referenztext) — bei Spontansprache
      nicht anwendbar, bewusst nicht eingebaut. Verifiziert: Formel-Selbsttest (4 Fälle: perfekt/
      leicht gestört/unverständlich/leer, alle plausibel) + voller AppTest-Durchlauf mit
      gefaketem Transkript (kein echtes Mikrofon nötig) zeigt korrekte WER/CER-Werte in der UI,
      kein Exception. Deployed, HTTP 200 verifiziert.
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
  erreicht `<TAILSCALE-IP>:8501` von überall, nicht nur im Heimnetz. Kein Zusatzaufwand nötig,
  nur bewusst machen, dass "online von unterwegs" schon funktioniert, solange Tailscale aktiv ist.
- Alternative: Deployment auf dem **Hetzner-Server** (neuro-vibe.de, `deploy@<ANDERER-SERVER-IP>`),
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

## Dysarthrie-Vergleichsstudie (eigene Testläufe, ab 2026-08-17)

Nutzer nimmt mehrere Session-Paare auf (klare Artikulation vs. bewusst simulierte Dysarthrie),
um zu prüfen, welche Parameter zuverlässig reagieren. **Reiner Sanity-Check mit einer einzigen
Testperson, kein klinischer Validierungsdatensatz** — dient der Priorisierung, welche
Parameter bei der Interpretation im Vordergrund stehen sollten, nicht als Beleg für
diagnostische Aussagekraft.

### Durchlauf 1 (NV-BFU8 klar vs. NV-4A4T simuliert, 2026-08-17) — Ergebnis

**Konsistent im erwarteten Muster verschlechtert** (Fokus-Parameter für die Interpretation):
- **Sprechrate** (Vorlesen 170→107 WPM, Spontan 155→101 WPM) — stärkstes, klassischstes
  Dysarthrie-Signal in diesem Testlauf.
- **Ø Wortdauer** (0,27→0,47s bzw. 0,29→0,48s) — Wörter fast doppelt so lang.
- **Jitter/Shimmer** (durchgehend höher bei /a/ und /i/, weniger deutlich bei /u/).
- **HNR** (deutlich niedriger bei /a/: 16,5→9,5 dB).
- **Voice Breaks** (0→1, neu aufgetreten bei /a/).
- **DDK-Regelmäßigkeit (CV)** (0,51→0,67, mehr Unregelmäßigkeit).

**Widersprüchlich/nicht ins Muster passend (vermutlich Artefakte, nicht bei der Interpretation
priorisieren, bis mehr Durchläufe vorliegen):**
- **DDK-Rate** stieg (1,84→2,47 Hz) statt zu fallen — gegenläufig zur Erwartung.
- **F0-Tremor-Frequenz** sprang auf physiologisch unplausible 12,14 Hz (vorher 3,81 Hz) —
  vermutlich Artefakt der neu aufgetretenen Voice Breaks, kein echtes Tremor-Signal.
- **/u/-Vokal** zeigte insgesamt deutlich weniger Verschlechterung als /a/ und /i/ — noch
  unklar, ob das an der Simulation lag oder ein generelles Muster ist.

**Nächste Schritte**: weitere Durchläufe geplant (derselbe Nutzer, mehrere Wiederholungen),
um zu prüfen, ob sich das Muster bestätigt, bevor eine feste "Fokus-Parameter-Liste" für die
Berichts-Interpretation festgeschrieben wird.

### Offene Grundsatzfrage: über die reine Deskription hinaus? (NICHT umgesetzt, nur vermerkt)

Nutzer-Aussage 2026-08-17: über die rein deskriptive Reportseite hinaus soll es perspektivisch
**"eine Art der Beurteilung bzw. Interpretation"** geben. **Wichtiger Konflikt mit dem
bestehenden Projektprinzip** ("keine Diagnose, kein unvalidierter Score" — siehe
`CONTRIBUTING.md`, `docs/literatur_review.md`, wiederholt in mehreren Backlog-Einträgen
bekräftigt): jede Form von "Beurteilung" muss sehr genau definiert werden, um diese Grenze
nicht zu verletzen.

**Mögliche, mit dem Projektprinzip vereinbare Zwischenstufen** (Diskussionsgrundlage, keine
Entscheidung):
1. **Muster-Zusammenfassung statt Einzelwert-Liste**: "N von M literaturbasiert etablierten
   Parametern zeigen eine Auffälligkeit in dieselbe Richtung" — rein deskriptiv-aggregierend,
   kein neuer Score, nur eine andere Darstellung bereits vorhandener Einzelbefunde.
2. **Konsistenz-Hinweis**: ob sich mehrere Parameter, die laut Literatur ZUSAMMENHÄNGEN (z.B.
   die ganze Jitter/Shimmer-Familie), gemeinsam oder nur vereinzelt auffällig zeigen — Hinweis
   auf Plausibilität, keine Bewertung der Schwere.
3. **EXPLIZIT NICHT vereinbar**: ein einzelner Gesamt-Score/Wahrscheinlichkeitswert
   ("X % Dysarthrie-Wahrscheinlichkeit") ohne echte, extern validierte Kohortenstudie
   dahinter — das wäre unvalidierte Diagnostik, siehe `CONTRIBUTING.md` Projektprinzip.

**Nächster Schritt**: mit dem Nutzer klären, welche der Zwischenstufen (falls überhaupt)
gewünscht ist, sobald mehrere Vergleichsdurchläufe vorliegen — bewusst noch nicht umgesetzt.

## Geschlechtsschätzung aus der Stimme ✅ UMGESETZT (2026-08-17)

Nutzer-Wunsch: F0-basierte Schätzung, ob eine Aufnahme eher männlich oder weiblich klingt, mit
Konfidenzangabe in Prozent — sollte laut Nutzer in die Auswertung mit einfließen. Hintergrund-
recherche bereits vorhanden (siehe `docs/literatur_review.md` "Perspektivische
Zusatzparameter" — Geschlechtserkennung hat mit 92-99% Genauigkeit in Studien die solideste
Evidenzlage der dort geprüften Zukunfts-Parameter).

**Umsetzung**: neues `core/voice_demographics.py::estimate_voice_gender()` — Sigmoid-Heuristik
auf Basis publizierter F0-Referenzbereiche (Männer ~100-146Hz, Frauen ~188-221Hz),
Entscheidungsgrenze bei 165Hz. Bewusst NUR F0-basiert (v1), nicht formant-kombiniert, da F0 im
Gegensatz zu Formanten vokal-unabhängig vergleichbar ist (funktioniert gleich für /a/, /i/,
/u/) — Formant-Kombination für höhere Genauigkeit als mögliche spätere Erweiterung vermerkt.
Konfidenz gedeckelt bei 50-97% (nie 100% Sicherheit behauptet), F0 außerhalb 60-400Hz gilt als
"nicht bestimmbar" (Schutz gegen Pitch-Erkennungs-Artefakte). Anzeige über neues
`core/shared.py::render_voice_gender_estimate()` in `views/vokalisation.py`, bewusst NICHT als
normale Kachel (kein "Normbereich"-Konzept anwendbar), mit explizitem Grenzen-Hinweis
(unzuverlässig bei Kinderstimmen, manchen Trans-Stimmen, kurzen/verrauschten Aufnahmen).

Verifiziert per manuellem Formel-Test gegen die echten F0-Werte beider Testsessions (alle
Werte plausibel, 80-86% männlich bei F0 91-108Hz) + AppTest-Regressionslauf (kein Exception)
auf dem Server, deployed.

**Noch offen**: Alterserkennung und Nervositäts-Erkennung aus der Stimme bleiben unpriorisiert
(siehe bestehender Backlog-Eintrag oben, moderate bzw. inkonsistente Evidenzlage).

### Visualisierung ergänzt ✅ UMGESETZT (2026-08-17)

Nutzer-Wunsch: die Geschlechtsschätzung soll nicht nur als Text/Prozentzahl erscheinen,
sondern auch visuell — und soll ab jetzt fester Bestandteil der App bleiben (nicht nur
Experiment). Neues `core/plots.py::voice_gender_estimate_figure()` — horizontaler
"Spektrum"-Balken: zeigt die beiden literaturbasierten F0-Referenzbereiche (männlich/weiblich)
als farbige Bänder, die Entscheidungsgrenze (165Hz, gestrichelt) UND den tatsächlich
gemessenen F0-Wert als Marker (Dreieck+Punkt) auf einen Blick — macht sichtbar, WIE WEIT der
Wert von der Grenze entfernt liegt (= Grundlage der Konfidenzangabe), statt nur das
Endergebnis als nackte Zahl zu zeigen. Bei "nicht bestimmbar" (F0 außerhalb des plausiblen
Bereichs) zeigt die Funktion einen neutralen Hinweistext statt der Skala.

Anzeige-Skala bewusst enger gezogen (60-260Hz Standardfall, dehnt sich nur bei extremen
Messwerten mit aus) als der volle Plausibilitätsbereich (60-400Hz) — sonst wirken die
Referenzbänder auf einen schmalen Streifen gequetscht. `BOUNDARY_HZ`/`PLAUSIBLE_MIN_HZ`/
`PLAUSIBLE_MAX_HZ` in `core/voice_demographics.py` von privaten (`_`-Prefix) auf öffentliche
Konstanten umbenannt, da jetzt modulübergreifend gebraucht (keine doppelten Zahlen an zwei
Stellen pflegen).

Verifiziert: manuelle Bild-Kontrolle für 4 F0-Fälle (klar männlich/an der Grenze/klar
weiblich/nicht bestimmbar) — dabei zwei Layout-Probleme gefunden und behoben (Werte am
Rand überlappten mit den Achsen-Ticks, "Grenze"-Beschriftung überlappte mit der Legende).
Voller AppTest-Durchlauf mit echter synthetischer Aufnahme zeigt 4 Bilder (Wellenform/
Lautstärke/Spektrogramm + neuer Gender-Plot), kein Exception. Deployed, HTTP 200 verifiziert.

### Reproduzierbarkeitstest: 2. Normalbefund (NV-Z8YW vs. NV-BFU8, 2026-08-17)

Zweiter "Normalbefund" (anderer Lesetext) zum Test, wie stabil die Werte bei derselben Person
ohne simulierte Pathologie sind — Ergebnis siehe `docs/bugtracker.md` RANDNOTIZ-13 für die
Details der zwei auffälligen, aber reproduzierbaren Muster (CPPS bei Fließsprache, DDK-Rate
"gemischt"). Kurzfassung: Jitter, F0-Tremor, Sprechrate (Vorlesen) und DDK-Rate selbst
reproduzieren sich gut zwischen beiden Sessions — spricht grundsätzlich für eine verlässliche
Messung. Shimmer, MPT (v.a. /u/) und Spontansprache-Sprechrate zeigen größere Schwankung,
plausibel als normale Tag-/Text-Variabilität. Die zwei reproduzierbar "auffälligen" Muster
(CPPS Fließsprache, DDK-Rate) sind als offene, dokumentierte Beobachtungen vermerkt — nicht
als Bugs gefixt, siehe RANDNOTIZ-13 für Details und nächste Schritte.

### Durchlauf 2 (NV-VAE5, "schwerer ausgeprägt", 2026-08-17) — konsolidierter Stand nach 4 Sessions

Vergleich gegen beide Normalbefunde (NV-BFU8, NV-Z8YW) und die leichtere Simulation (NV-4A4T).

**Robusteste Fokus-Parameter (Dosis-Effekt über 4 Sessions bestätigt):**
- **Sprechrate Spontansprache**: sauberer, monotoner Abfall über alle 4 Sessions
  (155→121→101→93 WPM), kippt bei der schwereren Simulation erstmals auf "auffällig" statt
  nur "grenzwertig". Bisher der zuverlässigste Einzelmarker.
- **Voice Breaks**: 0% bei beiden Normalbefunden (bis auf einen kleinen Ausreißer), 33,99%
  (/i/) bzw. 10,27% (/a/) bei der schwereren Simulation — deutlich stärker als bei der
  leichteren Simulation (nur 13,54% bei /a/). Zweiter robuster Dosis-Effekt.
- **Ø Wortdauer**: steigt konsistent mit dem Schweregrad (0,27-0,29s → 0,47-0,53s).

**Nicht konsistent dosis-abhängig, weniger verlässlich für die Schweregrad-Einordnung:**
- Jitter/Shimmer/HNR/CPPS bei den Vokalen (Session 4 teils näher an der Baseline als Session 3).
- DDK-Rate/DDK-Regelmäßigkeit (CV) — vermutlich durch die in RANDNOTIZ-13 vermutete
  Zählweise-Unsicherheit überlagert.

**Vorläufige Fokus-Parameter-Liste für die künftige Berichts-Interpretation** (Zwischenstand,
weitere Durchläufe folgen laut Nutzer noch): Sprechrate (v.a. Spontansprache), Voice Breaks,
Ø Wortdauer. Siehe auch die oben unter "Offene Grundsatzfrage" skizzierten, mit dem
Projektprinzip vereinbaren Interpretations-Zwischenstufen (Muster-Zusammenfassung/
Konsistenz-Hinweis) — diese Fokus-Liste wäre die inhaltliche Grundlage dafür, sobald
entschieden ist, ob/wie das umgesetzt wird.

Siehe auch `docs/bugtracker.md` RANDNOTIZ-14 zum ein drittes Mal beobachteten (aber wohl
kosmetischen) Export-Button-Verdacht trotz BUG-25-Fix.
