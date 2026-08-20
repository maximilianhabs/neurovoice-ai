# Konzept: Zuverlässigkeit — offene Befunde abarbeiten und Wiederauftreten verhindern

**Stand 2026-08-20.** Anlass: Nutzer-Wunsch nach einem Konzept, „um die Bugs abzuarbeiten, dass
diese Fehler nicht mehr passieren", mit zwei ausdrücklich benannten Punkten: die Pausenmaße
stimmen erkennbar nicht, und **das Transkribieren muss sicher immer funktionieren**.

Dieses Dokument war ursprünglich ein reiner Plan. **Etappe 1 ist seit 2026-08-20 umgesetzt
und auf dem Server verifiziert** (Abschnitt 2); die Etappen 2–5 stehen weiterhin aus. Es benennt zuerst die Ursache, warum solche
Fehler überhaupt bis zur Nutzung durchrutschen — sonst arbeitet man elf Befunde ab und der
zwölfte entsteht auf demselben Weg.

---

## 1. Warum die Fehler durchrutschen

Drei strukturelle Gründe, jeder am konkreten Bestand belegbar.

### A. Es gibt keine automatisierten Tests

`CONTRIBUTING.md` sagt es selbst: „Kein formales Testsuite (Stand jetzt)". Geprüft wird
manuell und per Ad-hoc-`AppTest`-Skripten, die nach Gebrauch verworfen werden.

Das erklärt die Fehlerklasse direkt. RANDNOTIZ-17 (Pausenmaße liefern in **allen** Aufnahmen
`pause_count: 0` und `fluency_score: 1,00`) wäre von einem einzigen Test gefangen worden, der
eine Aufnahme mit drei eingebauten Zwei-Sekunden-Pausen durchschickt und `pause_count == 3`
erwartet. Dasselbe gilt für BUG-11 (Praat-Sentinel −300 dB), BUG-13 (Rundungsrauschen) und
RANDNOTIZ-15 (SNR bei gehaltenen Vokalen): allesamt Fälle, in denen die Software fehlerfrei
lief und trotzdem eine falsche Zahl anzeigte.

### B. Kein Prüfmaßstab für die Messwerte selbst

Bisher werden Werte gegen **Plausibilität** und **Literatur** geprüft. Das ist nützlich, aber
es fängt nur, was auffällig falsch aussieht. Ein Maß, das immer denselben harmlos wirkenden
Wert liefert, fällt dabei nicht auf — `fluency_score: 1,00` sieht aus wie ein Befund, ist aber
in Wahrheit ein konstanter Rückgabewert.

Für ein Biomarker-Werkzeug ist „läuft ohne Exception" kein Qualitätsmaß. Was fehlt, ist die
Prüfung gegen ein Signal, **dessen wahre Antwort wir selbst konstruiert haben**.

### C. Der Bugtracker ist kein verlässlicher Index mehr

Beim Erstellen dieses Konzepts gefunden:

- **Doppelt vergebene ID**: `RANDNOTIZ-13` existiert zweimal mit völlig verschiedenen Themen
  (Zeile 225: „App reagiert während Transkription nicht"; Zeile 760: „DDK-Rate/CV-Auffälligkeiten").
- **Veralteter Eintrag**: RANDNOTIZ-13 (Zeile 225) steht als OFFEN und schlägt als „echte Lösung"
  einen Umbau zu Hintergrund-Jobs vor. Dieser Umbau ist längst erfolgt (P9,
  `core/job_queue.py` + `worker.py` + `render_transcription_job()`); der Eintrag hätte
  geschlossen werden müssen.
- **Zusammenfassungstabelle stimmt nicht**: „Offene Punkte, damit nichts vergessen wird" listet
  drei Einträge. Tatsächlich offen sind elf.

Wer nicht zuverlässig weiß, was offen ist, kann es auch nicht abarbeiten.

---

## 2. Etappe 1 — die zwei benannten Punkte ✅ UMGESETZT 2026-08-20

### 2.1 Transkription bruchsicher machen

Die Architektur ist in Ordnung (Job-Queue, getrennter Worker, Cache, Fortschritt per
`st.fragment`). Die Zuverlässigkeitslücken liegen in den Randfällen. Vier konkrete Fehlerpfade,
alle am Code belegt:

**F1 — Fertige Transkription wird weggeworfen (RANDNOTIZ-16).**
`worker.py` ruft nach erfolgreicher Transkription `save_transcript_cache(audio_path, …)`.
`core/transcription.py::transcript_cache_path()` legt die Datei **neben die Audiodatei**;
`/data` ist laut `docker-compose.yml` bewusst read-only. Ergebnis: ein bis zwei Minuten
Rechenzeit sind erbracht, dann stirbt der Job an `OSError: Read-only file system` und das
Ergebnis ist verloren. Genau das ist beim iPhone-Paar-Durchlauf passiert.
→ *Fix*: einheitlich nach `/derived/<patient_id>/` schreiben (die Formel, die
`views/testdaten.py` bereits verwendet), das dortige Duplikat entfernen, atomar schreiben
(temporäre Datei + `os.replace`), und das Schreiben so kapseln, dass ein Cache-Fehler die
Transkription **nicht** verwirft.

**F2 — Toter Worker führt zu endlosem Drehen.**
Ist `neurovoice-worker` nicht gestartet, bleibt der Job auf `pending`. `render_transcription_job()`
kennt kein Zeitlimit und zeigt weiter Fortschritt an — ohne Fehler, ohne Hinweis.
→ *Fix*: Worker schreibt einen Heartbeat; die UI meldet nach einer Karenzzeit ohne
Statusfortschritt klar „Worker antwortet nicht" samt „Erneut versuchen".

**F3 — `restart: unless-stopped` startet nach einem expliziten Stop nicht wieder.**
Heute real erlebt: der Syncthing-Container war 13 Stunden aus, weil er einmal explizit
gestoppt wurde — `unless-stopped` respektiert das über Neustarts hinweg. Dashboard und Worker
haben dieselbe Policy und dieselbe Anfälligkeit; die nächtliche Abschaltung des Servers macht
das zu einem wiederkehrenden Risiko.
→ *Fix*: für `neurovoice-worker` und `neurovoice-dashboard` auf `restart: always` (wie es die
Immich-Container bereits haben), plus ein Health-Check.

**F4 — Job stirbt mitten im Lauf (z.B. OOM, vgl. INFRA-BEFUND-09).**
Status bleibt auf `running` stehen, gleiche Endlos-Anzeige wie F2. Vom Heartbeat aus F2
miterledigt.

### 2.2 Pausenmaße: erst klären, bis dahin nicht so tun als ob

Der Verdacht steht in RANDNOTIZ-17: `core/speech_metrics.py` leitet Pausen aus den Lücken
zwischen WhisperX-Wortzeitstempeln ab. Forced Alignment dehnt Wortgrenzen aneinander, sodass
die Lücken systematisch null werden — gemessen würde dann das Verfahren, nicht die Sprechweise.

1. **Prüfen** mit einem konstruierten Signal (siehe Etappe 2): Sprache mit exakt drei
   eingefügten Zwei-Sekunden-Stillen. Bleibt `pause_count` null, ist die Ursache bestätigt.
2. **Bestätigt** → Pausen energiebasiert direkt aus dem Signal bestimmen statt aus
   Alignment-Zeitstempeln.
3. **Bis dahin**: `fluency_score`, `pause_count` und die Mikro-/Makropausen-Aufteilung in der
   UI als nicht validiert kennzeichnen oder ausblenden. Sie werden derzeit angezeigt, als wären
   sie belastbar — das ist der eigentliche Schaden, nicht die fehlende Funktion.

### 2.3 Bugtracker in Ordnung bringen

Doppelte ID auflösen, RANDNOTIZ-13 (Zeile 225) als durch P9 erledigt schließen,
Zusammenfassungstabelle zur einzigen Wahrheit über den offenen Bestand machen und vollständig
befüllen. Aufwand: eine halbe Stunde. Ohne diesen Schritt ist jede Priorisierung Raten.

---

## 3. Etappe 2 — das Fundament: Prüfung gegen konstruierte Wahrheit

Der Kern des Konzepts. Das Schwesterprojekt EDF-Analyzer hat dieses Fundament bereits
(`tests/test_analytic_groundtruth.py`, `tests/test_eeg_groundtruth.py`), NeuroVoice nie.
Dessen Leitsatz gilt hier unverändert:

> Was hier NICHT passiert: eine Formel neben der Implementierung nachbauen und beide
> vergleichen. Das zeigte nur, dass zwei Rechnungen übereinstimmen. Geprüft wird gegen Werte,
> die aus der Theorie oder aus der Konstruktion des Eingangssignals folgen.

Für jedes Kernmaß ein synthetisches Signal mit bekannter Antwort:

| Maß | Konstruiertes Signal | Erwartung |
|---|---|---|
| F0 | Sinus bekannter Frequenz | genau diese Frequenz |
| Jitter | exakt periodisches Signal; dann bekannte Periodenschwankung | ≈ 0; dann der konstruierte Wert |
| Shimmer | Amplitudenmodulation bekannter Tiefe | die konstruierte Tiefe |
| HNR | Ton plus Rauschen bekannter Leistung | das konstruierte Verhältnis |
| Formanten | synthetischer Vokal mit gesetzten Polen | die gesetzten Polfrequenzen |
| VSA / FCR | Formantwerte per Hand eingesetzt | analytisch nachgerechnet |
| **Pausen** | **Sprache mit exakt N eingefügten Stillen** | **`pause_count == N`** |
| **DDK** | **Impulsfolge mit exakt N Zyklen bei bekannter Rate** | **`n_cycles == N`, Rate bekannt** |
| **SNR** | **Rauschen bekannter Leistung, auf Vokal und auf Sprache** | **beide Male derselbe SNR** |

Die drei fett gesetzten Zeilen beantworten dabei zugleich drei offene Randnotizen: **17**
(Pausen), **13b** (DDK-Zyklen-Ambiguität) und **15** (SNR bei gehaltenen Vokalen). Dieselbe
Infrastruktur, die künftige Fehler verhindert, klärt also die aktuell offenen mit.

Dazu, nach dem Muster des Schwesterprojekts:

- **`tools/preflight.sh`** — bildet die CI lokal nach, vor jedem Push von Hand ausführbar.
- **GitHub Actions** — das Repo ist öffentlich, Actions sind kostenlos. Bisher existiert kein
  `.github/` im NeuroVoice-Repo.
- **Feste Seeds** für alle Zufallsreihen. Ein Test, der gelegentlich rot wird, wird irgendwann
  ignoriert — und ist dann schlimmer als keiner.

---

## 4. Etappe 3 — Regressionsschutz auf dem eigenen Referenzkorpus

Mit `IPH-KTRL-01` und `IPH-SIM-01` liegt erstmals ein **Paar auf identischer Aufnahmekette**
vor, dazu die SVD-Referenzfälle. Daraus wird ein Regressionstest: erwartete Werte einmal
eingefroren, Abweichung über Toleranz schlägt fehl.

Das greift genau in die heute gebaute Analyse-Versionierung: ändert sich ein Wert
**absichtlich**, wird `FEATURE_SCHEMA_VERSION` erhöht und die Referenz neu eingefroren.
Ändert er sich unabsichtlich, wird der Test rot. Damit wird die Versionsnummer von einer
Fleißaufgabe zu etwas, das sich selbst durchsetzt.

---

## 5. Etappe 4 — Datenintegrität an der Quelle

Zwei Prozess-Risiken sind heute erneut real geworden:

- **PROZESS-RISIKO-04** (Freitext-Dateinamen aus Sprachmemos): dreimal am Transportweg
  gescheitert, Benennung manuell nachgezogen.
- **PROZESS-RISIKO-05** (Task-Label und tatsächlicher Inhalt laufen auseinander): bisher nur
  durch manuelle Prüfung abgesichert.

Beide verschwinden weitgehend mit dem **M4A-Upload direkt in der App** (Backlog
„Self-Service-Upload, Schritt 4"): die Aufgabe wird beim Hochladen ausgewählt, der Inhalt
serverseitig konvertiert, kein Sync-Ordner und keine Dateinamen mehr im Spiel. `ffmpeg` liegt
bereits im Container.

Ergänzend als automatische Plausibilitätsprüfung beim Upload, aus der heutigen manuellen
Prüfung ableitbar: Stimmhaftigkeitsanteil über 85 % bei behauptetem gehaltenem Vokal, unter
75 % bei DDK, dazwischen bei Fließsprache — passt das nicht zusammen, Warnung statt stiller
Fehlablage.

---

## 6. Reihenfolge und Aufwand

| Etappe | Inhalt | Nutzen | Aufwand |
|---|---|---|---|
| 1 | Transkription bruchsicher, Pausenmaße ehrlich kennzeichnen, Tracker aufräumen | beseitigt die zwei benannten Probleme sofort | klein |
| 2 | Ground-Truth-Tests + CI + preflight | verhindert die ganze Fehlerklasse künftig | mittel, größter Hebel |
| 3 | Regressionstest auf Referenzkorpus | schützt bestehende Werte vor stiller Drift | klein, baut auf 2 auf |
| 4 | M4A-Upload + Inhalts-Plausibilitätsprüfung | beseitigt zwei Prozess-Risiken und den Transportweg | mittel |
| 5 | Restbestand: RANDNOTIZ-10/11/12/14, BEFUND-03 | Kosmetik | klein |

Etappe 2 vor Etappe 3, weil der Regressionstest ohne Testinfrastruktur keinen Ort hat.
Etappe 1 zuerst, weil sie das benannte Leid unmittelbar beendet.

---

## 7. Was bewusst nicht passiert

- **Kein Architektur-Umbau.** Job-Queue und Worker-Trennung funktionieren; nur die Randfälle
  fehlen.
- **Keine Vollabdeckung.** Ziel sind Tests für die Maße, die eine Zahl in den Bericht schreiben
  — nicht für jede Hilfsfunktion.
- **Keine neuen Parameter, solange die vorhandenen nicht abgesichert sind.** Die letzten
  Sessions haben Verständlichkeit, Geschlechtsschätzung, Spektralneigung und FCR ergänzt. Ein
  weiteres Maß hinzuzufügen, während drei bestehende nachweislich fragwürdig rechnen, vergrößert
  die Angriffsfläche, statt das Werkzeug besser zu machen.

## 8. Entschiedene Fragen

- **Pausenmaße während der Klärung**: ✅ entschieden 2026-08-20 — **sichtbar lassen, aber
  deutlich als „nicht validiert" kennzeichnen**. Umgesetzt in Kachel, Tabelle und Glossar.

---

## Anhang: Verifikation von Etappe 1 (2026-08-20, auf dem Server)

| Prüfung | Ergebnis |
|---|---|
| Cache-Pfad `/data/...` → schreibbares Ziel | `/derived/IPH-KTRL-01/….transcript.json` |
| Cache-Pfad `/derived/_uploads/...` unverändert | ja — 27 bestehende Caches bleiben gültig |
| **Echter Worker-Job auf dem vorher abstürzenden `/data`-Pfad** | **nach 42 s fertig, 27 Wörter, Cache geschrieben** |
| Atomares Schreiben, keine `.tmp`-Reste | keine |
| `worker_alive()` bei laufendem Worker | True |
| `worker_alive()` nach `docker stop` + 65 s | False |
| `worker_alive()` nach Neustart | True |
| Fehlende/kaputte Heartbeat-Datei | True (kein Fehlalarm) |
| Restart-Policy Worker/Dashboard | `always` |
| Pausenmaße in Tabelle/Kachel/Glossar | 4/4 als „nicht validiert" markiert |
| Jitter als Gegenprobe | unmarkiert, Status „im Normbereich" |
| Alle 7 Seiten laden ohne Exception | ja, HTTP 200 |
