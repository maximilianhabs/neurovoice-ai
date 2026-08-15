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

## BUG-14 — Upload-Größenlimit: Fehlermeldung zeigt falsche Einheit (MiB vs. MB) ✅ BEHOBEN

**Symptom:** `save_uploaded_wav()` (neue Upload-Funktion, Phase A Schritt 1, 2026-08-14)
definierte `MAX_UPLOAD_BYTES = 25 * 1024 * 1024` (25 MiB = 26.214.400 Bytes), die
Fehlermeldung rechnete das aber mit `/1_000_000` (dezimal) um — bei einer 26MB-Testdatei
zeigte die Meldung fälschlich "Limit 26 MB" statt der beworbenen 25 MB.

**Root Cause:** Einheiten-Mismatch zwischen Binärpräfix (1024²) für die Konstante und
Dezimalpräfix (1000²) für die Anzeige — beim Test mit einer knapp über dem Limit liegenden
Datei fiel die Diskrepanz auf.

**Fix:** Konstante auf dezimal `25 * 1_000_000` umgestellt, passt jetzt exakt zur
Anzeige/zum UI-Label ("max. 25 MB"). Gefunden beim gezielten Testen der Fehlerfälle
(leere Datei, ungültiges WAV, Pfad-Traversal-Dateiname, Überschreitung des Limits) vor
dem Deploy — keine Auswirkung auf echte Nutzer, da noch nicht live genutzt.

---

## BUG-15 — Mikrofonaufnahme (`st.audio_input`) schlug fehl: App lief nur über HTTP ✅ BEHOBEN

**Symptom:** Beim echten Test durch den Nutzer im Browser (2026-08-15, erste Nutzung von P0
"Mikrofonaufnahme im Browser") erschien beim Klick auf den Aufnahme-Button "An error has
occurred, please try again" — keine Aufnahme möglich, auch keine sichtbare
Mikrofon-Berechtigungsabfrage.

**Root Cause:** Browser (Chrome/Firefox/Safari gleichermaßen) verweigern den Zugriff auf
`getUserMedia` (die zugrunde liegende Web-API für Mikrofon-/Kamerazugriff) grundsätzlich auf
unverschlüsselten Origins — Ausnahme ist nur `localhost`. Unser Dashboard lief bisher
ausschließlich über `http://100.67.129.76:8501` (kein HTTPS), eine private Tailscale-IP zählt
dabei NICHT als "sicherer Kontext". Kein App-Bug im engeren Sinn, sondern eine
Browser-Sicherheitsrichtlinie, die erst beim echten Mikrofon-Testversuch sichtbar wurde
(automatisierte Tests/AppTest können das nicht abdecken, da sie keinen echten Browser
verwenden).

**Fix:** `tailscale serve --bg http://100.67.129.76:8501` — stellt automatisches, gültiges
HTTPS innerhalb des eigenen Tailnets bereit (Zertifikat via Tailscale selbst, kein Public-
Internet-Zugriff, kein eigenes Zertifikats-Handling). Neue App-Adresse:
`https://homeserver.tailaecdbb.ts.net`. Setup brauchte zwei einmalige Freischaltungen:
(1) `sudo tailscale set --operator=maximilian` auf dem Server (NOPASSWD-freundlich, analog
zum Stromspar-Timer-Setup), (2) "Serve" im Tailscale-Admin-Konto bestätigen
(login.tailscale.com, nur mit Nutzer-Login möglich, einmalig pro Tailnet).

**Lehre für künftige Browser-Feature-Integrationen**: Mikrofon/Kamera/Standort/Clipboard-
Zugriff (alle `getUserMedia`-artigen Browser-APIs) brauchen einen sicheren Kontext (HTTPS
oder localhost) — bei jeder neuen Browser-API-Funktion vorher prüfen, ob die App aktuell
über HTTPS erreichbar ist, nicht erst beim ersten fehlgeschlagenen Nutzertest merken.

---

## RANDNOTIZ-12 — `st.audio_input`: kosmetische Fehlermeldung nach erfolgreicher Aufnahme ⚠️ OFFEN (nicht blockierend)

**Symptom:** Nach Testen der echten Mikrofonaufnahme über die neue HTTPS-Adresse (siehe
BUG-15) meldet der Nutzer: Aufnahme, Anzeige und Auswertung funktionieren einwandfrei
(Qualität "hervorragend"), aber am ENDE der Aufnahme erscheint zusätzlich zweimal "An error
has occurred, please try again". App bleibt voll funktional — eine neue Aufnahme lässt sich
direkt danach starten, keine Daten gehen verloren.

**Vermutete Ursache (nicht verifiziert, nur Recherche-Indiz)**: Mehrere ähnliche
GitHub-Issues zu `st.audio_input` beschreiben Fehler nach Aufnahmeende speziell bei
Deployments HINTER EINEM REVERSE-PROXY (genau das haben wir seit BUG-15 mit
`tailscale serve`) bzw. bei Aufnahmen über einer gewissen Länge. Nicht selbst reproduziert/
debuggt — kein Zugriff auf Browser-Konsole der echten Nutzer-Session.

**Status**: Bewusst zurückgestellt, da nicht blockierend. Wird im Zuge der UI-Überarbeitung
(Recorder aus der Sidebar in den Hauptbereich, siehe docs/backlog.md) im Auge behalten — falls
der Fehler dabei verschwindet oder sich auf bestimmte Aufnahmelängen/Browser eingrenzen lässt,
hier nachtragen.

---

## BUG-16 — Modul-Ergebnisse "verschwanden" beim Navigieren zwischen Seiten ✅ BEHOBEN

**Symptom:** Nutzer meldet beim Testen von Modul 1+2 (Vokalisation/Vorlesen, siehe P2/P3 in
docs/backlog.md): beim Hin- und Herspringen zwischen Modul-Seiten "gehen Dateien verloren" —
bereits aufgenommene/analysierte Vokale/Lesetexte sind nach dem Zurückkommen nicht mehr
sichtbar.

**Root Cause:** Die Ergebnis-Anzeige (Gauges/Metriken) wurde in `views/vokalisation.py` und
`views/vorlesen.py` NUR gerendert, wenn der Aufnahme-/Upload-Widget (`st.audio_input`/
`st.file_uploader`) in DIESEM Rerun einen frischen Rückgabewert hatte (`if uploaded is not
None:`). Beim Navigieren zu einer anderen Seite und zurück wird die Seite neu gemountet — der
Widget-Rückgabewert ist dann wieder `None` (Streamlits Upload-Widgets behalten ihren Wert
nicht dauerhaft über Remounts), obwohl die Datei auf der Platte UND die Analyse in
`st.session_state` nach wie vor vorhanden waren. Kein echter Datenverlust, nur eine UI, die
vorhandene Daten fälschlich nicht mehr anzeigte.

**Fix:** Neues Modul `core/module_state.py` — Ergebnisse werden ab sofort IMMER aus
`st.session_state["module_results"]` gerendert, nie in Abhängigkeit vom aktuellen
Widget-Rückgabewert. Gleichzeitig als Take-Management ausgebaut (P1 aus dem Umsetzungsplan,
vorgezogen, weil es genau diesen Bug behebt): mehrere Versuche pro Teilaufgabe möglich,
manuelle Auswahl des "besten" Versuchs (radio), Löschen einzelner Versuche (entfernt Eintrag
UND Datei von der Platte, da es sich um Session-Uploads in `derived/_uploads/` handelt, keine
geschützten Rohdaten). Nach jeder neuen Aufnahme `st.rerun()` mit hochgezähltem Widget-Key,
damit der Recorder danach sauber leer ist statt den alten Blob erneut zu verarbeiten.

**Verifiziert**: Session-State vor `AppTest.run()` mit vorhandenen Versuchen vorbelegt (simuliert
"von einer anderen Seite zurückkommen") — Ergebnisse erscheinen jetzt korrekt ohne dass der
Widget einen Wert haben muss. Auswahl-Radio + Lösch-Button per `AppTest` durchgeklickt:
Auswahl wechselt korrekt, Löschen entfernt Eintrag UND Datei von der Platte (verifiziert mit
`os.path.exists()`).

---

## BUG-17 — Absturz bei unabhängig fehlenden Formant-/Voice-Breaks-Teilwerten ✅ BEHOBEN

**Symptom:** Beim gezielten Testen des BUG-16-Fixes (Session-State mit echten Analyseergebnissen
vorbelegt) stürzte `views/vokalisation.py` mit `TypeError: unsupported format string passed to
NoneType.__format__` ab, sobald `voice_breaks_count` einen Wert hatte, aber
`voice_breaks_degree_pct` `None` war.

**Root Cause:** `f"{dyn['voice_breaks_count']} · {dyn['voice_breaks_degree_pct']:.1f}%"` wurde
nur durch `if dyn["voice_breaks_count"] is not None else "–"` abgesichert — das prüft aber nur
EINEN der beiden Werte, während `phonation_dynamics_features()` (`core/audio.py`) beide
unabhängig voneinander aus separaten Regex-Treffern parst und daher unabhängig `None` sein
können. Derselbe Fehlerklasse fand sich auch bei den einzelnen Formantwerten (F1/F2/F3, nur
F1 wurde geprüft) in `vokalisation.py` und bei der Formant-Streuung (F1/F2-IQR, nur F1
geprüft) in `views/vorlesen.py`. Der bereits existierende Testdaten-Modus (`views/
testdaten.py`) hatte dieses Problem nicht, weil er konsequent den sicheren `_fmt()`-Helper
nutzt — beim Neubau der Module-Seiten wurde dieses Muster übersehen.

**Fix:** `_fmt()`-Helper (identisch zum bereits bewährten Muster aus `testdaten.py`) in beide
Dateien ergänzt, alle betroffenen Formatierungen darauf umgestellt — jeder Wert wird jetzt
unabhängig sicher formatiert, nicht mehr über einen "verwandten" Wert mitabgesichert.

**Lehre**: Wenn ein Kennwert aus mehreren Regex-/Parsing-Treffern zusammengesetzt wird
(wie bei `phonation_dynamics_features()`), NIE annehmen, dass "wenn Wert A da ist, ist Wert B
auch da" — jeden Teilwert einzeln auf `None` prüfen. Durch gezieltes Testen mit echten
Analyseergebnissen (nicht nur mit leerem Ausgangszustand) gefunden, bevor der Nutzer erneut
darüber gestolpert wäre.

---

## RANDNOTIZ-13 — App reagiert während WhisperX-Transkription nicht ⚠️ OFFEN (bekannte Einschränkung)

**Symptom:** Nutzer meldet, dass die App beim Transkribieren in Modul 2 (Vorlesen) für die
Dauer der Transkription "hängen" blieb/nicht mehr reagierte.

**Einordnung**: Kein neuer Bug, sondern eine bereits aus früheren Sessions bekannte
Eigenschaft von WhisperX `large-v3` auf diesem Server (Beelink N150, 4 Kerne) — die
Transkription ist ein blockierender, rechenintensiver Aufruf innerhalb des synchronen
Streamlit-Skriptlaufs; für die Dauer (laut früheren Messungen ~1-2 Minuten) reagiert die
betroffene Browser-Sitzung nicht, und da die Transkription alle verfügbaren CPU-Kerne des
Containers beansprucht, kann sich das auch auf andere gleichzeitige Anfragen auf demselben
Server auswirken.

**Sofort-Maßnahme**: Button-Text in `views/vorlesen.py` und Spinner-Text setzen jetzt explizit
die Erwartung ("App reagiert währenddessen nicht, das ist normal" / "bitte nicht wegnavigieren,
sonst geht der Fortschritt verloren"), damit es nicht wie ein Absturz wirkt. Transkript-Cache
(bereits vorhanden) sorgt dafür, dass das pro Aufnahme nur EINMAL passiert.

**Echte Lösung wäre größerer Umbau** (nicht jetzt): Transkription als Hintergrund-Job statt
blockierendem Aufruf (z.B. eigener Worker-Prozess/Queue) — bewusst zurückgestellt, kein
kleiner Schritt. Als Backlog-Punkt vermerkt.

---

## BUG-18 — Recording-Quality-Check zählte reine Stille fälschlich als 0% ✅ BEHOBEN (vor Deploy gefunden)

**Symptom:** Beim Testen der neuen `recording_quality_features()` (P6) mit einer
synthetischen Testdatei (1s Stille + 1s Ton + 1s geklipptes Signal) zeigte die
Stille-Quote 0% statt der erwarteten ~33%.

**Root Cause:** Fenster mit RMS exakt 0 (reine Digitalstille) wurden VOR der
Stille-Berechnung per `frame_rms[frame_rms > 0]` herausgefiltert (um `log(0)` zu
vermeiden) — dadurch flossen sie gar nicht mehr in die Stille-Prozent-Rechnung ein.

**Fix:** Zwei getrennte Fenster-Reihen — `frame_db_all` (epsilon-geflooert mit
`np.maximum(frame_rms, 1e-10)`, zählt ALLES für die Stille-Quote) vs. `frame_rms_nonzero`
(nur für die SNR-Schätzung, da reine Digital-Nullen kein realer Rauschboden sind und die
Schätzung sonst absurd aufblähen würden — mit echtem Mikrofon-Grundrauschen praktisch nie
exakt Null, betrifft also v.a. synthetische Randfälle/angehängte Stille).

**Lehre**: Vor dem Deploy mit gezielt konstruierten synthetischen Testfällen (reine Stille,
reines Clipping, Mischfall) statt nur echten Aufnahmen getestet — echte Aufnahmen allein
hätten diesen Bug nicht zwingend aufgedeckt, da sie selten exakte Digitalstille enthalten
(Mikrofon-Grundrauschen). Deckt sich mit [[feedback_signalverarbeitung_kennwerte]]: gezielt
Grenzfälle/Sentinel-Werte testen, nicht nur den Regelfall.

---

## RANDNOTIZ-11 — WhisperX glättet Füllwörter aus erster Spontansprache-Testaufnahme weg ⚠️ OFFEN (Befund, kein Bug)

**Symptom:** Erste echte Spontansprache-Testaufnahme (2026-07-24, "Wandertour"-Beschreibung,
~11s) transkribiert sauber und vollständig ("Wir planen für unser Wochenende eine Wandertour...
Mit Pausen für Verpflegung, Essen und Trinken.") — OHNE jedes Füllwort wie "äh"/"ähm", obwohl
Spontansprache erfahrungsgemäß fast nie komplett füllwortfrei ist.

**Einordnung:** Bestätigt exakt den bereits im Backlog vorab notierten Vorbehalt (Stufe 3,
"Filled Pauses"): WhisperX/Whisper-Modelle sind darauf trainiert, Transkripte zu glätten, und
lassen Disfluencies bekanntermaßen oft weg. Aus dieser einen Aufnahme lässt sich nicht sicher
unterscheiden, ob (a) tatsächlich keine Füllwörter gesprochen wurden oder (b) welche gesprochen,
aber vom Modell verschluckt wurden — ohne Referenz-Höraufnahme nicht auflösbar.

**Konsequenz für Stufe 3 "Filled Pauses"**: Feature bleibt vorerst zurückgestellt. Bevor es
umgesetzt wird, müsste entweder (a) eine Aufnahme mit bewusst deutlich übertriebenen Füllwörtern
gemacht werden (Testfall: erkennt WhisperX sie überhaupt, wenn sie eindeutig da sind?), oder
(b) ein WhisperX-Parameter/Prompt geprüft werden, der Disfluency-Glättung reduziert.

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
