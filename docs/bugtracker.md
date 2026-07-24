# NeuroVoice AI — Bug-/Problem-Tracker

Jedes aufgetretene Problem wird hier festgehalten, auch wenn es klein wirkt oder schon
behoben ist — damit nichts durchrutscht und die Historie nachvollziehbar bleibt.
Format: Status, Root Cause, Fix/Empfehlung, Datum.

---

## BUG-11 — Monoloudness/Lautstärkekurve durch Praat-Sentinel-Wert (-300 dB) verzerrt ✅ BEHOBEN

**Symptom:** Erster Monoloudness-Wert (Stufe 4, Intensitäts-SD) für Take 3 war **26,18 dB** —
unplausibel hoch für eine reine Sprachmodulations-Kennzahl.

**Root Cause:** Praat markiert Zeitpunkte ohne definierte Intensität (Stille am Anfang/Ende
der Aufnahme) mit dem Sentinel-Wert **-300 dB**, kein echter Messwert. `~np.isnan()` filtert
das nicht raus (es ist kein NaN, sondern eine gültige aber bedeutungslose Zahl) — dieselbe
Fehlerklasse wie beim HNR-Sentinel (-200), der in `phonation_features()` bereits korrekt
behandelt wird, hier aber übersehen wurde. Dieselbe Verzerrung steckte auch unbemerkt im
Lautstärke-Diagramm (`plots.py`, `intensity_figure()`) — die Kurve wäre durch die -300dB-Spitzen
an den Rändern gestaucht dargestellt worden.

**Fix:** Beide Stellen filtern jetzt `values > -300` zusätzlich zu NaN. Ergebnis nach Fix:
12,75 dB (Take 3) — durchgehend plausibel über alle drei Testaufnahmen (10,9-12,7 dB).

**Lehre**: Bei jedem neuen Parselmouth-Kennwert prüfen, ob die zugrundeliegende
Praat-Funktion einen Sentinel-/Platzhalterwert für "undefiniert" verwendet (bekannt: HNR=-200,
Intensität=-300) — `NaN`-Filterung allein reicht nicht.

---

## BUG-12 — Formant-Tracker "springt" auf physiologisch unmögliche Werte ✅ BEHOBEN

**Symptom:** Erste Version von `formant_dynamics_features()` zeigte F1-Range bis 1837-1917 Hz
über die drei Testaufnahmen — physiologisch unmöglich für einen einzelnen Sprecher (F1 liegt
für erwachsene Stimmen praktisch nie über ~1000-1100 Hz). F1-Geschwindigkeit bis 180.000 Hz/s
war ebenfalls absurd hoch.

**Root Cause:** Praats `to_formant_burg()`-Tracker "springt" bei ca. 10% der stimmhaften Frames
auf einen falschen Spektralpeak (bekanntes Verhalten bei Burg-LPC-basiertem Formant-Tracking,
v.a. bei Rauschen/Übergängen) — verifiziert an Take 3: 95. Perzentil von F1 lag bei 1415 Hz,
99. Perzentil bei 1735 Hz, klar erkennbare Tracking-Fehler statt echter Sprachwerte.

**Fix:** Physiologisch plausible Wertebereiche als Filter ergänzt (F1: 150-1100 Hz,
F2: 500-3500 Hz), Frames außerhalb werden verworfen. Nach dem Fix: F1-Range konsistent bei
930-945 Hz über alle 3 Takes (vorher 1799-1917 Hz, stark streuend durch die Ausreißer).

**Lehre**: Bei jeder neuen zeitaufgelösten Parselmouth-Kennzahl (nicht nur Sentinel-Werte wie
bei BUG-11) auch auf physiologisch unplausible Werte prüfen, nicht nur auf NaN/Sentinel —
Formant-Tracker können "falsche aber gültige" Zahlen liefern, die kein Filter automatisch fängt.

---

## BUG-13 — Prosodische Entropie durch Fließkomma-Rundungsrauschen verzerrt ✅ BEHOBEN

**Symptom:** Beim Testen mit einer synthetischen Wortliste aus **identischen** Wortdauern
(erwartete Entropie: 0.0) lieferte `_shannon_entropy_bits()` fälschlich 1,295 bit.

**Root Cause:** Wortdauern wurden aus `start`/`end`-Fließkommazahlen berechnet
(`i*0.5+0.3 - i*0.5`), die bei eigentlich identischen Werten durch Rundung um ~1e-16
voneinander abwichen. Der exakte Vergleich `hi <= lo` griff deshalb nicht, die Funktion
teilte die (eigentlich identischen) Werte per Histogramm mit einer astronomisch kleinen
Bin-Breite auf viele Klassen auf — numerisch instabil, künstlich hohe Entropie.

**Fix:** Toleranzschwelle (`hi - lo < 1e-6`) statt exaktem Vergleich — 1 Mikrosekunde liegt
weit unter jeder sinnvollen Wort-Zeitstempel-Präzision aus WhisperX.

**Verifiziert:** Identische Dauern → 0.0 (korrekt), variierte Dauern → 2.12 (unverändert
korrekt), echte Take-3-Daten → 2.50 bit.

**Lehre**: Bei jedem neuen Vergleich von Fließkomma-Werten, die aus unabhängig berechneten
Differenzen stammen (hier: `end - start` für viele verschiedene Wörter), auf Rundungsrauschen
prüfen — exakte Gleichheits-/Ordnungsvergleiche (`==`, `<=`) sind dafür ungeeignet, eine
Toleranzschwelle ist nötig. Gefunden durch bewusstes Testen eines Edge-Case (identische
Werte), nicht durch Zufall — solche Tests lohnen sich.

---

## RANDNOTIZ-10 — Transkript-Cache-Dateien gehören `root` ⚠️ OFFEN (kosmetisch)

**Symptom:** Neu angelegte `/derived/<patient_id>/*.transcript.json`-Dateien gehören auf dem
Host `root:root`, nicht `maximilian:maximilian` — der Nutzer kann sie lesen, aber nicht ohne
`sudo`/Hilfscontainer löschen.

**Root Cause:** Der Dashboard-Container läuft ohne explizites `USER`, also als `root` — alles,
was er neu anlegt, gehört root, egal welcher Host-User das Volume gemountet hat.

**Empfehlung (nicht dringend)**: Falls das je störend wird, `USER`-Direktive mit passendem
PUID/PGID im Dockerfile ergänzen (wie z.B. beim Syncthing-Setup mit `PUID=1000`/`PGID=1000`).
Aktuell keine funktionale Einschränkung, nur beim manuellen Aufräumen etwas umständlicher.

---

## PROZESS-NOTIZ-08 — Docker-Testcontainer ohne Namen sorgen für Verwirrung ✅ ERLEDIGT (Vorsatz)

**Symptom:** Ein isolierter WhisperX-Testcontainer (`docker run --rm ...` ohne `--name`) bekam
von Docker automatisch den zufälligen Namen `strange_curran` zugewiesen — sorgte für Verwirrung
("was ist das für ein Programm?").

**Klärung:** `strange_curran` war kein Programm, sondern Dockers eingebauter Zufallsname
(Adjektiv + Nachname, z.B. von bekannten Informatiker:innen) für Container ohne expliziten
`--name`. Container war ohnehin ein `--rm`-Wegwerf-Container und hat sich nach Abschluss selbst
entfernt — nichts umzubenennen nötig.

**Vorsatz für künftige Testcontainer:** Immer explizit `--name` vergeben (z.B.
`--name neurovoice-test-<zweck>`), damit `docker ps`/Logs auf Anhieb erkennbar bleiben.
Falls doch mal ein unbenannter Container stehen bleibt: `docker rename <alt> <neu>` funktioniert
jederzeit nachträglich, auch bei laufenden Containern, ohne Neustart/Datenverlust.

---

## INFRA-BEFUND-09 — WhisperX im Produktions-Dashboard: OOM-Kill beim ersten Lauf ✅ BEHOBEN

**Symptom:** Erster Live-Test von WhisperX im echten `neurovoice-dashboard`-Container (nach
Chunk-5-Deploy) brach ohne sichtbaren Fehler ab — die Python-Ausgabe endete nach dem VAD-Start-
Log, keine finalen Ergebnisse. `docker inspect` zeigte `OOMKilled: true`.

**Root Cause:** Der isolierte Vorab-Test (siehe Chunk-5-Performance-Check) lief in einem leeren
Container NUR mit WhisperX. Im echten Dashboard-Container läuft WhisperX aber zusätzlich zur
bereits aktiven Streamlit-App (Parselmouth/Matplotlib/Pandas-Grundlast) — beide teilen sich
dasselbe Speicher-Cgroup-Limit. Das gesetzte `mem_limit: 5g` reichte dafür nicht, vermutlich
verschärft durch gleichzeitiges Herunterladen mehrerer Modelle (VAD, wav2vec2-Alignment,
large-v3) im allerersten Lauf (leerer Modell-Cache).

**Fix:** `mem_limit` auf `7g` erhöht (`dashboard/docker-compose.yml`). Wiederholungstest danach
erfolgreich: 27/27 Wörter korrekt, nur 576,9 MiB tatsächlich benutzt (weit unter dem Limit) —
die Modelle waren durch den ersten (abgebrochenen) Versuch bereits teilweise im
Cache-Volume vorhanden, kein erneuter Download nötig.

**Nebenbeobachtung:** Laufzeit sank von 544,5s (isolierter Vortest, System noch mit 99% vollem
Swap) auf 96,1s (nach der AnythingLLM/Ollama-Speicherbereinigung, RESSOURCEN.md) — starkes Indiz,
dass Swap-Thrashing die eigentliche Vortest-Laufzeit deutlich verlangsamt hatte, nicht die reine
Rechenleistung der N150-CPU.

**Lehre**: Speicherlimits, die in einem isolierten/leeren Testcontainer erfolgreich sind, gelten
NICHT automatisch für den produktiven Container mit bereits laufender Anwendung daneben — die
Grundlast der Hauptanwendung muss mit eingerechnet werden.

---

## BUG-01 — Dashboard: falsche Lautstärke-/Bittiefen-Werte ✅ BEHOBEN

**Symptom:** Erste Version zeigte `bit_depth=64`, `peak_dbfs=180.67` (physikalisch unmöglich,
müsste ≤0 dBFS sein).

**Root Cause:** `scipy.io.wavfile.read()` liefert bei Stereo-Dateien ein 2D-Array. Der Code
rief `data.mean(axis=1)` auf, **bevor** Bittiefe/Normalisierung bestimmt wurden — `np.mean()`
auf einem Integer-Array liefert automatisch `float64` zurück. Dadurch wurde (a) die Bittiefe
anhand des NEUEN float64-dtype berechnet (64 statt 24 bit) und (b) die Normalisierungsprüfung
(`np.issubdtype(..., np.integer)`) schlug fehl, sodass rohe Integer-Sample-Werte (bis
~1,7 Milliarden) ungeteilt als bereits normalisierte Samples im Bereich [-1,1] behandelt wurden.

**Fix:** Wechsel von `scipy.io.wavfile` auf `soundfile` (liest 24-bit-PCM korrekt, normalisiert
automatisch bei `dtype='float64'`). Normalisierung passiert jetzt vor jeder Kanalmittelung.
Siehe `dashboard/core/audio.py`, Commit vom 2026-07-21.

**Verifiziert:** Werte nach Fix plausibel (24 bit, 2 Kanäle, -6 dBFS Peak).

---

## BEFUND-02 — Erste Testaufnahme war AAC statt ALAC ✅ BEHOBEN

**Symptom:** `ffprobe` zeigte `codec_name=aac` statt des erwarteten ALAC für die erste
Testaufnahme — widerspricht der Projektannahme "iPhone liefert verlustfreies ALAC".

**Root Cause:** iPhone-Einstellung „Voice Memos → Audioqualität" stand auf „Komprimiert",
nicht „Verlustfrei". Kein Software-Bug, sondern eine falsche Ausgangseinstellung.

**Fix:** Nutzer hat die Einstellung umgestellt (zusätzlich Stereo statt Mono gewählt, 3D Audio
war nicht verfügbar). Take 2 bestätigt: `codec_name=alac`, `bits_per_raw_sample=24`.

**Empfehlung:** Bei jeder neuen Aufnahme-Charge (nicht nur beim ersten Test) den Codec der
Originaldatei per `ffprobe` verifizieren, nicht nur die App-Einstellung als gegeben annehmen —
genau dieser Bug hätte sich sonst unbemerkt durch die ganze Testdatenbank gezogen.

---

## BEFUND-03 — ALAC-Dekodierwarnung bei Take 2 ✅ GEKLÄRT, KEIN DATENVERLUST

**Symptom:** `ffmpeg` meldete beim Konvertieren von Take 2: `invalid samples per frame: 0` /
`Decoding error: Invalid data found when processing input`. Konvertierte WAV war 11,52s lang,
Original-Container meldete 11,61s — 85ms "Differenz".

**Untersuchung:** `ffprobe -show_packets` zeigt, dass das letzte Paket der Datei nur 8 Bytes
groß ist (praktisch leer) — eine reine Auffüll-Frame. Der `iTunSMPB`-Metadaten-Tag der Datei
(Standard-Apple-Tag für Gapless-Playback) bestätigt: Feld 3 = `0x1000` (4096 = exakt eine
ALAC-Frame-Länge an "remainder"-Padding), Feld 4 = `0x87000` = 552.960 Samples = genau die
11,52s der validen Audio-Samples. ALAC codiert in festen 4096-Sample-Frames; die letzte Frame
der Originalaufnahme war nicht vollständig gefüllt und wurde vom Encoder mit Stille auf die
volle Framegröße aufgefüllt — dieses Padding ist laut `iTunSMPB` ausdrücklich zum Verwerfen
gedacht (Gapless-Playback-Standard), enthält keine echten Audiodaten.

**Ergebnis:** Die 85ms sind **keine verlorenen Audiodaten**, sondern korrekt verworfenes
Auffüll-Padding. Die Warnung ist harmlos, aber im Skript-Output irreführend/beunruhigend.

**Empfehlung (offen, niedrige Priorität):** `scripts/convert_and_verify.sh` könnte diese
spezifische Warnung abfangen/kommentieren, damit sie nicht bei jeder zukünftigen Konvertierung
wieder wie ein echter Fehler aussieht. Nicht dringend, da rein kosmetisch.

---

## PROZESS-RISIKO-04 — Voice-Memos-Dateinamen weichen vom Schema ab ⚠️ OFFEN

**Symptom:** Beide bisherigen Testaufnahmen kamen NICHT im erwarteten Schema
(`<patient_id>_task-<typ>_take<n>`) an:
- Take 1: `Selbst Aufnahme vokal take 01.m4a`
- Take 2: `Selbst Aufnahme Aufgabe zwei Lese Text Nordwind und Sonne take zwei.m4a`

**Root Cause:** Kein iOS-Bug — der Nutzer tippt beim Umbenennen natürlichsprachige Titel statt
des exakten Schemas. `scripts/convert_and_verify.sh` erkennt Abweichungen zwar (Warnung +
Überspringen), aber jede Aufnahme musste bisher manuell nachbenannt werden, bevor die
Konvertierung lief.

**Risiko:** Bei mehr Aufnahmen (oder falls später andere Personen aufnehmen) wird manuelles
Nachbenennen fehleranfällig und skaliert nicht — Kernprinzip aus docs/dashboard_konzept.md
("skalierbar") wird hier unterlaufen.

**Empfehlung (offen):** Entweder (a) das Skript tolerant genug machen, um auch aus
Freitext-Titeln automatisch zu erkennen, welcher Task gemeint ist (Schlüsselwort-Suche nach
"vokal"/"lesetext"/"freisprache" im Dateinamen), oder (b) eine feste Kurzform in Voice Memos
als Vorlage/Kopiervorlage bereitstellen (z.B. iOS-Textersetzung/Shortcut), damit der Nutzer
nicht jedes Mal frei tippen muss. Noch nicht entschieden.

---

## PROZESS-RISIKO-05 — Task-Label und tatsächlicher Aufnahmeinhalt liefen auseinander ✅ KORRIGIERT (Einzelfall), Risiko bleibt

**Symptom:** Take 1 wurde als `task-vokal` benannt/konvertiert, tatsächlich eingesprochen
wurde aber der Nordwind-Lesetext.

**Root Cause:** Menschlicher Fehler beim Betiteln der Aufnahme in Voice Memos, nicht direkt
erkennbar ohne Rückfrage.

**Fix (Einzelfall):** Nutzer hat auf Nachfrage den tatsächlichen Inhalt bestätigt, Datei wurde
umbenannt (`task-lesetext`).

**Risiko, das bleibt:** Falsches Task-Label hätte unbemerkt zu einer ungültigen Jitter/Shimmer-
Interpretation führen können (nur bei Task „vokal" verlässlich, siehe
docs/literatur_review.md). Das Dashboard warnt zwar bei Nicht-Vokal-Tasks (`app.py`), aber nur
wenn das Label korrekt gesetzt ist — bei falschem Label greift die Warnung nicht.

**Empfehlung (offen):** Kein technischer Fix vorgesehen — bleibt ein Prozess-Risiko, das durch
sorgfältiges Betiteln beim Aufnehmen entschärft wird, nicht durch Software.

---

## INFRA-BEFUND-06 — Syncthing-Pairing schlug zunächst zweifach fehl ✅ BEHOBEN

**Symptom 1:** iPhone zeigte „Disconnected", diverse Timeouts/Connection-Refused-Meldungen.
**Root Cause 1:** Globale Discovery/Relay sind auf dem Server bewusst deaktiviert (Datenschutz)
— dadurch funktioniert die Standard-Adresse „dynamic" nicht, das iPhone konnte den Server nicht
finden. **Fix:** Statische Adresse `tcp://100.67.129.76:22000` im iPhone-Client hinterlegt.

**Symptom 2:** Danach Server-Log `Connection rejected ... error="unknown device"`.
**Root Cause 2:** iPhone war nur einseitig (auf dem iPhone selbst) als Remote-Device
eingetragen, dem Server aber nicht bekannt/freigegeben.
**Fix:** iPhone-Device-ID per REST-API zum Server hinzugefügt, Ordner `raw-inbox` explizit mit
dieser Device-ID geteilt.

**Verifiziert:** `GET /rest/system/connections` zeigt stabile Verbindung, Nutzer bestätigt
"Up to Date" mit grünem Haken. Volle Doku: homeserver-Repo `services/syncthing/README.md`.

---

## SICHERHEITSVORFALL-07 — Passwort-Weitergabe versucht, Klartext-Passwort in alter Memory gefunden ✅ BEHOBEN

**Symptom:** Bei einer sudo-Passwortsperre hat der Nutzer wiederholt angeboten, das Passwort
im Chat zu teilen bzw. es "speichern" zu lassen — musste mehrfach klar abgelehnt werden (feste
Regel, keine Ausnahme). Dabei zusätzlich entdeckt: Eine ältere Memory-Datei
(`project_homeserver_beelink.md`, aus einer früheren Session) enthielt bereits ein
Klartext-Passwort.

**Fix:** Passwort wurde nie verwendet/gespeichert. Alte Memory-Datei bereinigt (Passwort
entfernt, Verweis auf Passwort-Manager stattdessen). Neue Feedback-Memory
(`feedback_keine_passwoerter.md`) angelegt, damit künftige Sessions das nicht wiederholen.

**Kein technischer Bug im Projekt selbst**, aber sicherheitsrelevant genug, um hier
mitzuführen.

---

## Offene Punkte (Zusammenfassung, damit nichts vergessen wird)

| # | Thema | Priorität | Status |
|---|---|---|---|
| PROZESS-RISIKO-04 | Freitext-Dateinamen aus Voice Memos | mittel | offen, Lösung noch nicht entschieden |
| BEFUND-03 | Kosmetische ALAC-Warnung im Skript-Output | niedrig | offen, rein kosmetisch |
| PROZESS-RISIKO-05 | Task-Label kann inhaltlich falsch gesetzt werden | niedrig | kein technischer Fix geplant, Wachsamkeit nötig |
