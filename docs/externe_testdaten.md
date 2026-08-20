# Externe Referenz-Testdaten — laufend gepflegte Sammlung

**Zweck**: unsere Algorithmen (Jitter/Shimmer/HNR/CPPS/Sprechrate/...) gegen extern gelabelte,
unabhängige Aufnahmen (bekannt gesund ODER bekannt pathologisch) testen — Robustheit prüfen
UND schauen, ob sich ähnliche Muster zeigen wie bei unseren eigenen simulierten Dysarthrie-
Durchläufen (siehe `docs/backlog.md` "Dysarthrie-Vergleichsstudie"). **Kein Ersatz für eine
echte klinische Validierungsstudie** — kleine Stichprobe, keine standardisierte Erhebung durch
uns selbst, aber besser als nur simulierte Daten.

## ⚠️ Wichtige Einschränkungen dieser Sammlung (Stand 2026-08-17)

- **TORGO ist Englisch.** Sprache ≠ Deutsch (unsere App ist auf Deutsch eingestellt) — nur für
  sprachunabhängige akustische Maße (Jitter/Shimmer/HNR/CPPS) verwendbar, NICHT für WER/CER
  oder lexikalische Maße. Diese Einschränkung gilt für JEDE Datei aus `EXT-TORGO-*`-Ordnern.
- **Sehr kurze Vokal-Aufnahmen** — alle bisher genutzten SVD-Vokale liegen bei 0,53–1,99s,
  keine erreicht 3 Sekunden. Deutlich kürzer als eine "so lange wie möglich halten"-Aufnahme
  unseres eigenen Vokalisation-Moduls — schränkt z.B. die Aussagekraft für MPT-artige Analysen
  ein, auch wenn Jitter/Shimmer/HNR bei diesen Kurzclips noch plausibel berechenbar bleiben.
- **Insgesamt heterogene Sammlung**: unterschiedliche Sprachen, Aufnahmejahre (1997–2002 bei
  SVD, unbekannt bei TORGO), Aufnahmegeräte, Aufgabentypen (Wort/Satz/Vokal) und Sampleraten
  (16kHz TORGO, 50kHz SVD, 48kHz unsere eigenen Aufnahmen) je nach Quelle — bewusst NICHT
  einheitlich, jede Datei einzeln in der Tabelle unten mit ihren jeweiligen Eckdaten vermerkt.

## Prozessregel: externe Aufnahmen IMMER von einer Person gegenlesen lassen

**Bevor eine extern beschaffte Datei als vertrauenswürdige Referenz gilt** (z.B. in die
App-Testdatenbank übernommen oder für einen Vergleich zitiert wird), muss sie von einem
Menschen gegengeprüft werden — mindestens:

1. **Sprache**: passt die gesprochene Sprache zur Quellenangabe (z.B. wirklich Deutsch bei
   SVD)? Automatisiert nur indirekt über Metadaten geprüft, nicht durch echtes Zuhören.
2. **Inhaltliche Plausibilität**: klingt es nach dem behaupteten Aufgabentyp (gehaltener Vokal
   vs. Wort vs. Satz)? Bisher nur per Signalanalyse (stimmhafter Anteil, Energie-Einbrüche)
   NÄHERUNGSWEISE geprüft, nicht durch Anhören verifiziert.
3. **Wahrgenommene Aufnahmequalität**: klingt es tatsächlich sauber/verrauscht/verzerrt? Unsere
   automatisierten Kennwerte (SNR-Schätzung, Clipping-Anteil) sind — wie RANDNOTIZ-15 zeigt —
   nicht für jeden Aufgabentyp verlässlich, ein menschliches Ohr bleibt die verlässlichere
   Referenz.

**Bisher NICHT durchgeführt** — alle Dateien in diesem Dokument wurden bisher nur automatisiert
(Signalanalyse) geprüft, nicht angehört. Jede Zeile in der Datei-Tabelle unten braucht noch ein
"gegengehört: ja/nein"-Vermerk, sobald das nachgeholt wurde.

**Speicherort**: `data/raw/external_reference/` — lokal, NICHT committed (per `.gitignore`
"data/raw/*" ausgeschlossen, wie alle Audiodaten in diesem Projekt). Wer diese Sammlung
fortsetzt, muss die Dateien über die untenstehenden Befehle selbst neu herunterladen.

## Zugriffswege (Stand 2026-08-17, mit reproduzierbaren Befehlen)

### 1. TORGO-Datenbank (Englisch, Dysarthrie + Kontrollgruppe) via Hugging Face

Kein Institutions-Antrag nötig (anders als der offizielle TORGO-Zugang über die Uni Toronto).
Einzelne Dateien direkt abrufbar:

```bash
curl -sL -o out.wav "https://huggingface.co/datasets/birgermoell/dysarthria/resolve/main/<pfad>"
```

Dateiliste (403 Dateien total) über die API:
```bash
curl -s "https://huggingface.co/api/datasets/birgermoell/dysarthria" | python3 -c "import json,sys; print([s['rfilename'] for s in json.load(sys.stdin)['siblings']])"
```
Ordner: `dysarthria_female/`, `dysarthria_male/`, `non_dysarthria_female/`, `non_dysarthria_male/`.

**Wichtige Einschränkung, siehe Testergebnis unten**: TORGO-Dateien sind kurze **Wörter/Sätze**
(Prompts), KEINE gehaltenen Vokale — passen nicht zu unserem Vokalisation-Modul. Englisch,
daher auch für WER/CER (auf Deutsch eingestellt) nicht nutzbar.

### 2. Saarbrücker Stimmdatenbank (SVD) — Deutsch, gehaltene Vokale /a/,/i/,/u/ + Satz

**NICHT über `stimmdb.coli.uni-saarland.de` direkt** — die Website wurde neu gebaut (Next.js),
der alte PHP-basierte Downloadweg (u.a. genutzt vom `svd-downloader`-Tool auf GitHub) ist tot
(404). Stattdessen über **Zenodo**, wo die Datenbank **nach Diagnose in einzelne ZIPs
aufgeteilt** ist (nicht nur als ein 38GB-Gesamtpaket!):

```bash
# Dateiliste mit Größen abrufen:
curl -s "https://zenodo.org/api/records/16874898" | python3 -c "
import json,sys
d = json.load(sys.stdin)
for f in d['files']:
    print(f['key'], f['size'])
"
# Einzelne Diagnose-ZIP herunterladen (Beispiel: kleine, dysarthrie-relevante Pathologie):
curl -sL -o Morbus_Parkinson.zip "https://zenodo.org/api/records/16874898/files/Morbus%20Parkinson.zip/content"
```

**Wichtig — kein Teilzugriff auf `healthy.zip` möglich**: die "gesund"-Sammlung ist mit 6GB in
EINER Datei, der Zenodo-Server unterstützt keine HTTP-Range-Requests (getestet: `Range`-Header
wird ignoriert, liefert immer die volle Datei) — kann also nicht partiell heruntergeladen
werden. **Für kleine "Normalbefund"-Referenzen aus SVD bräuchte es entweder den vollen 6GB-
Download oder einen anderen Zugangsweg** (offener Punkt, siehe unten).

Kleine, dysarthrie-relevante Diagnose-Pakete (bereits identifiziert, Größe siehe Klammer):
- `Morbus Parkinson.zip` (5,5 MB) — genutzt, siehe Testergebnis unten
- `Amyotrophe Lateralsklerose.zip` (14,2 MB) — genutzt, siehe Testergebnis unten
- `Dysarthrophonie.zip` (143,8 MB) — größer, noch nicht genutzt, viele Fälle mit
  "zentral-laryngaler Bewegungsstörung" (siehe `voice_data.csv`-Diagnosetexte)
- `Bulbärparalyse.zip` (25,5 MB) — noch nicht genutzt

Sprecher:innen-Index mit Diagnosen (zum gezielten Auswählen, bevor man ein ZIP zieht):
```bash
curl -sL -o voice_data.csv "https://stimmdb.coli.uni-saarland.de/data/voice_data.csv"
```
Spalten: `AufnahmeID,AufnahmeTyp(n=normal/p=pathologisch),AufnahmeDatum,Diagnose,SprecherID,
Geburtsdatum,Geschlecht,Pathologien`. Der Ordnername in den ZIPs entspricht der `AufnahmeID`,
NICHT der `SprecherID`.

**Format-Falle (wichtig!)**: SVD liefert `.nsp` (Kay/PENTAX CSL-Format), **kein WAV**. Unsere
Praat-Pipeline (`parselmouth`) kann `.nsp` NICHT direkt lesen (`Not an audio file`-Fehler).
Konvertierung nötig:
```bash
pip install nspfile
python3 -c "
import nspfile, soundfile as sf
rate, data = nspfile.read('1580/vowels/1580-a_n.nsp')
sf.write('1580-a_n.wav', data, rate)
"
```
Samplerate der SVD-Aufnahmen: 50000 Hz (deutlich höher als unsere eigenen 48kHz-Aufnahmen).

**Lizenz-Hinweis zu `nspfile`**: auf PyPI ohne deklarierte Lizenz gelistet (Stand 2026-08-17,
geprüft via PyPI-JSON-API). Wird von uns NICHT eingebunden (kein Eintrag in
`dashboard/requirements.txt`, nur diese Doku-Erwähnung als optionales Reproduktions-Tool für
eigene Recherchezwecke) — wer es selbst nutzen möchte, sollte die Lizenzlage vorher eigenständig
prüfen (z. B. direkt im Quellcode-Repository nach einer LICENSE-Datei suchen), bevor er/sie es
in einem eigenen Projekt einsetzt.

## Bisher heruntergeladene/getestete Dateien

| Datei (lokal) | Quelle | Sprache | Label | Dauer | Aufgabentyp | Für unsere Module geeignet? | Von Mensch gegengehört? |
|---|---|---|---|---|---|---|---|
| `torgo_english/normal_FC01_0047.wav` | HF/TORGO, `non_dysarthria_female/FC01_Session1_0047.wav` | **Englisch** | gesund (Studien-Label) | 5,3s | kurzes Wort/Satz (per Signalanalyse verifiziert: nur 35% stimmhaft, 17 Energie-Einbrüche in 5,3s — klar KEINE Vokalisation) | Nur bedingt Spontansprache, eigentlich nur Robustheitstest | ❌ nein |
| `svd_pathological/svd_parkinson_a_n.wav` | Zenodo/SVD, AufnahmeID 1580, SprecherID 1887 | Deutsch | Morbus Parkinson + Dysphonie (Diagnose: "Hypotone Komponente, vox senilis") | 0,72s (< 3s) | gehaltener Vokal /a/, normale Tonlage | Ja — genau unser Vokalisation-Aufgabentyp | ❌ nein |
| `svd_pathological/svd_parkinson_phrase.wav` | dieselbe Session | Deutsch | " | 2,31s | Satz "Guten Morgen, wie geht es Ihnen?" | Ja (Deutsch!) — aber noch nicht gegen Vorlesen/WER getestet (bräuchte WhisperX, läuft nur im Docker-Container) | ❌ nein |
| `svd_pathological/svd_als_a_n.wav` | Zenodo/SVD, AufnahmeID 1242, SprecherID 1630 | Deutsch | ALS + zentral-laryngale Bewegungsstörung | 1,57s (< 3s) | gehaltener Vokal /a/, normale Tonlage | Ja | ❌ nein |
| `svd_pathological/svd_als_phrase.wav` | dieselbe Session | Deutsch | " | 2,2s | Satz "Guten Morgen, wie geht es Ihnen?" | Ja — gegen WER/CER getestet, siehe eigener Abschnitt unten | ✅ **ja** (Nutzer 2026-08-17: "super dysarthrie beispiel", Sprache+Inhalt bestätigt) |
| `svd_pathological/svd_bulbar1_a_n.wav` | Zenodo/SVD, AufnahmeID 101, SprecherID 1301 | Deutsch | Bulbärparalyse (Verdacht) | 1,99s (< 3s) | gehaltener Vokal /a/, normale Tonlage | Ja | ❌ nein |
| `svd_healthy/svd_healthy_5_a_n.wav` | Zenodo/SVD, AufnahmeID 5, SprecherID 5 | Deutsch | gesund (Studien-Label, männlich) | 1,35s (< 3s) | gehaltener Vokal /a/, normale Tonlage | Ja — beste Qualität (HNR 27,4dB) | ❌ nein |
| `svd_healthy/svd_healthy_6_a_n.wav` | Zenodo/SVD, AufnahmeID 6, SprecherID 6 | Deutsch | gesund (Studien-Label, weiblich) | 0,80s (< 3s) | gehaltener Vokal /a/, normale Tonlage | Ja — zweitbeste Qualität (HNR 27,2dB) | ❌ nein |
| `torgo_english/healthy_MC04_..._0026.wav` | HF/TORGO, `non_dysarthria_male/MC04_...` | **Englisch** | gesund (Studien-Label) | 5,71s | kurzes Wort/Satz | Nur bedingt, Robustheitstest | ❌ nein |

## Testergebnis: Robustheit + inhaltlicher Vergleich (2026-08-17)

**Robustheit**: alle 4 SVD-Dateien (nach NSP→WAV-Konvertierung) liefen ohne Exception durch
`core/audio.py::phonation_features()`/`recording_quality_features()`. Die TORGO-Datei lief
ebenfalls ohne Absturz durch, aber wie oben beschrieben inhaltlich nicht sinnvoll auswertbar
für Jitter/Shimmer (falscher Aufgabentyp).

**Vergleich SVD-Vokale (/a/, normale Tonlage) gegen unsere eigenen 2 Normalbefund-Sessions**
(NV-BFU8, NV-Z8YW, siehe `docs/backlog.md`):

| Parameter | NV-BFU8 (eigen, gesund) | NV-Z8YW (eigen, gesund) | SVD Parkinson (extern, pathologisch) | SVD ALS (extern, pathologisch) |
|---|---|---|---|---|
| Jitter (local) | 0,59% | 0,64% | **0,50%** | **0,43%** |
| Shimmer (local) | 7,61% | 9,72% | **2,99%** | **5,19%** |
| HNR | 16,49dB | 12,49dB | **18,85dB** | **21,12dB** |
| F0 (Mittel) | 100,1Hz | 95,0Hz | 161,0Hz | 154,1Hz |

**Überraschender, aber erklärbarer Befund**: die SVD-Vokale der als "pathologisch" gelabelten
Parkinson-/ALS-Sprecher zeigen bei Jitter/Shimmer/HNR **BESSERE (unauffälligere) Werte** als
unsere eigenen "gesunden" Baseline-Aufnahmen! Das ist KEIN Widerspruch zu unseren früheren
Erkenntnissen, sondern bestätigt sie: bereits bei unserem eigenen simulierten Dysarthrie-
Vergleich (`docs/backlog.md`) zeigten sich Jitter/Shimmer/HNR bei gehaltenen Vokalen als
NICHT konsistent dosis-abhängig — die robusten Marker waren dort Sprechrate, Voice Breaks und
Wortdauer bei FLIESSENDER Sprache, nicht die isolierten Vokal-Perturbationsmaße. Dieser externe
Vergleich liefert dafür einen zweiten, unabhängigen Beleg: Dysarthrie bei Parkinson/ALS
äußert sich laut dieser Stichprobe eher NICHT in stark erhöhtem Jitter/Shimmer am gehaltenen
Vokal — passt zur Literatur, dass isolierte Phonationsmaße für hypokinetische/spastische
Dysarthrie ein schwächeres Signal liefern als Timing-/Prosodie-Maße.

**Randbefund, nicht weiter untersucht**: SNR-Schätzung unserer eigenen `recording_quality_
features()` fiel bei den SVD-Dateien sehr niedrig aus (1,2dB / 3,6dB) — plausibel echtes
Hintergrundrauschen der ~25 Jahre alten Klinik-Aufnahmen (nicht als Konvertierungsfehler
eingeordnet, Wellenform manuell gegengeprüft: sauberer Signalverlauf, keine Sprünge/Artefakte,
kein Clipping).

## Fokus Gesunde: Qualitätsbewertung mehrerer TORGO-Kontrollsprecher:innen (2026-08-17)

Auf Nutzer-Wunsch gezielt mehrere gesunde Referenzen getestet und über
`core/audio.py::recording_quality_features()` (SNR/Clipping/Stille) bewertet, um
herausragende Aufnahmen zu identifizieren. 6 verschiedene TORGO-Kontrollsprecher:innen (3w/4m,
je eine zufällige Datei pro Sprecher:in) + die bereits vorhandene FC01-Datei:

| Datei | Dauer | SNR (dB) | Clipping % | Stille % | F0 (Hz) | Einordnung |
|---|---|---|---|---|---|---|
| `healthy_MC04_..._0026.wav` | 5,71s | **35,6** | 2,6 | 15,8 | 166,9 | ✅ Beste SNR, aber etwas Clipping — leichter Abzug |
| `healthy_FC02_..._0048.wav` | 4,30s | **33,0** | 0,6 | 29,4 | 215,1 | ✅ **Beste Gesamtqualität** — hohe SNR, kaum Clipping |
| `healthy_FC03_..._0008.wav` | 1,42s | 22,1 | 0,0 | 0,0 | 217,0 | Ordentlich, aber sehr kurz |
| `normal_FC01_0047.wav` | 5,31s | 21,5 | 0,0 | 0,0 | 191,0 | Ordentlich (siehe oben, bereits dokumentiert) |
| `healthy_MC01_..._0025.wav` | 2,91s | 21,4 | 0,0 | 0,0 | 120,8 | Ordentlich |
| `healthy_MC03_..._0042.wav` | 1,61s | 20,6 | 0,0 | 0,0 | 100,4 | Ordentlich, kurz |
| `healthy_MC02_..._0045.wav` | 6,00s | **1,9** | 0,0 | 0,0 | **kein F0 erkennbar** | ❌ **Schlechtes Beispiel** — Maximalamplitude nur 0,07 (statt ~1,0), durchgängig zu leise Aufnahme, kein Konvertierungsfehler (Rohsamples manuell geprüft) |

**Empfehlung für "hervorragende Qualität"-Referenz**: `healthy_FC02_FC02_Session3_0048.wav`
(weiblich, F0 215Hz plausibel, SNR 33dB, praktisch kein Clipping) und `healthy_MC04_MC04_
Session1_0026.wav` (männlich, F0 167Hz plausibel, SNR 35,6dB, minimales Clipping) — beide
liefen ohne Exception durch `phonation_features()`, F0-Werte passen zum jeweils gelabelten
Geschlecht (Plausibilitäts-Gegenprobe bestanden).

**MC02 bewusst behalten statt gelöscht** — nützliches Negativbeispiel für künftige Tests
("erkennt unsere App/unser Qualitäts-Check eine zu leise Aufnahme zuverlässig als
Warnung?", noch nicht gezielt gegen die `quality_tiles()`-UI getestet).

**Weiterhin unverändert offen**: alle 7 getesteten Dateien sind kurze Wörter/Sätze, keine
gehaltenen Vokale (bestätigt auch hier: 33-47% stimmhaft, mehrere Energie-Einbrüche) — für
eine echte Vokalisation-Modul-Validierung fehlt weiterhin eine kleine, hochwertige GESUNDE
Referenz mit gehaltenem Vokal (SVD `healthy.zip` bleibt mit 6GB das Hindernis).

## Integration in die App-Testdatenbank (`views/testdaten.py`, 2026-08-17)

Auf Nutzer-Wunsch die besten Beispiele direkt im App-eigenen Testbereich nutzbar gemacht —
NICHT nur als Rohdatei in diesem Repo, sondern über `core/audio.py::list_patients()`/
`list_recordings()` (liest aus `NEUROVOICE_DATA_DIR`, auf dem Server
`~/neurovoice-data/raw/`, read-only in den Container gemountet) direkt in der App auswählbar.

**Wichtig — zwei unterschiedliche Orte**: dieses Dokument + `data/raw/external_reference/`
(lokal auf dem Mac, dieses Repo) sind der ARCHIV-/Recherche-Ort. Für die tatsächliche
App-Nutzung mussten die Dateien zusätzlich auf den **Server** kopiert werden
(`~/neurovoice-data/raw/`, dort liest der laufende Container sie), da lokale Dateien in diesem
Repo vom Server-Container nicht gesehen werden.

Neue Patient:innen-Ordner (Namensschema `EXT-<Quelle>-<Kennung>`, klar von echten/simulierten
Sessions unterscheidbar) + Dateinamen nach dem bestehenden Schema
`<Datum>_<Zeit>_task-<task>_take<n>.wav` (siehe `core/audio.py::FILENAME_RE`):

| Ordner | Datei | Task-Label | Herkunft |
|---|---|---|---|
| `EXT-TORGO-healthy-FC02` | `..._task-unbekannt_take1.wav` | Unbekannt (kein passender Task-Code — kurzes Wort, keine unserer 8 Kategorien) | TORGO, beste SNR-Qualität (33dB) |
| `EXT-TORGO-healthy-MC04` | `..._task-unbekannt_take1.wav` | Unbekannt | TORGO, höchste SNR (35,6dB, leichtes Clipping) |
| `EXT-SVD-Parkinson-1580` | `..._task-vokal_take1.wav` + `..._task-lesetext_take1.wav` | Gehaltener Vokal /a/ + Satz | SVD, Morbus Parkinson |
| `EXT-SVD-Bulbaer-101` | `..._task-vokal_take1.wav` | Gehaltener Vokal /a/ | SVD, Bulbärparalyse (beste verfügbare Signalqualität unter den 5 pathologischen Kandidaten) |
| `EXT-SVD-healthy-5` | `..._task-vokal_take1.wav` | Gehaltener Vokal /a/ | SVD, gesund (m), beste von 7 geprüften Kandidaten (Jitter 0,21%, HNR 27,4dB) |
| `EXT-SVD-healthy-6` | `..._task-vokal_take1.wav` | Gehaltener Vokal /a/ | SVD, gesund (w), zweitbeste von 7 (Jitter 0,33%, HNR 27,2dB) |

Verifiziert: `list_patients('/data')`/`list_recordings()` im Server-Container zeigen alle 6
neuen Ordner + 7 Dateien korrekt an, Task-Zuordnung stimmt.

**Warum "task-unbekannt" bei TORGO**: keiner unserer 8 Task-Codes
(`lesetext/vokal/vokali/vokalu/ddkgemischt/ddkeinzeln/spontan/unbekannt`) passt ehrlich zu
"kurzes einzelnes Wort" — eine Falsch-Etikettierung (z.B. als "spontan") wäre irreführender als
die ehrliche "unbekannt"-Kennzeichnung.

## Wichtiger Nebenbefund: unsere eigene SNR-Schätzung ist für gehaltene Vokale nicht aussagekräftig

Siehe `docs/bugtracker.md` RANDNOTIZ-15 für die volle Herleitung. Kurzfassung: Beim Vergleich
der SVD-Vokal-Dateien fiel auf, dass ALLE (Parkinson, 2×ALS, 2×Bulbärparalyse) einen sehr
niedrigen "SNR"-Wert (1,2–5,4dB) zeigten — verdächtig konsistent. Root Cause: unsere SNR-
Schätzung misst die Lautstärke-DYNAMIKSPANNE (90.–10. Perzentil), nicht den echten Rauschboden.
Ein gehaltener Vokal soll per Aufgabenstellung möglichst KONSTANT laut sein — die Dynamikspanne
ist dadurch systematisch klein, unabhängig von der tatsächlichen Aufnahmequalität. Bewiesen per
synthetischem Test: ein perfekter, rauschfreier künstlicher Vokal bekommt von unserer eigenen
Formel nur 0,2dB "SNR". **Das bedeutet: die "SNR (geschätzt)"-Kachel im Vokalisation-Modul
ist aktuell irreführend** — noch nicht gefixt, siehe Bugtracker für Lösungsvorschläge.

## Nachtrag: echte gesunde SVD-Vokale nachgeliefert (2026-08-17)

Die 6GB-Hürde wurde einmalig in Kauf genommen: `healthy.zip` komplett in ein TEMPORÄRES
Verzeichnis heruntergeladen (NICHT in diesem Repo/`data/raw/`), 7 Kandidaten (AufnahmeID 1-7,
alle Typ "n"/normal) extrahiert+konvertiert, per `phonation_features()` verglichen (bei
gehaltenen Vokalen ist HNR ein sinnvolleres Qualitätsmaß als unsere "SNR"-Schätzung, siehe
RANDNOTIZ-15 unten). Beste zwei: **AufnahmeID 5** (SprecherID 5, männlich, Jitter 0,21%,
Shimmer 1,56%, HNR 27,4dB) und **AufnahmeID 6** (SprecherID 6, weiblich, Jitter 0,33%,
Shimmer 2,19%, HNR 27,2dB) — beide technisch exzellent. `healthy.zip` danach vollständig
gelöscht (nur die 2 kleinen extrahierten WAVs behalten, `data/raw/external_reference/
svd_healthy/`, ~200KB statt 6GB). In die Testdatenbank integriert: `EXT-SVD-healthy-5`,
`EXT-SVD-healthy-6` (Task `vokal`).

**Finaler Vergleich, jetzt mit sauber aufgabentypischen (gehaltener Vokal) Referenzen aus
allen 3 Quellen:**

| Fall | F0 (Hz) | Jitter % | Shimmer % | HNR dB |
|---|---|---|---|---|
| SVD gesund #5 (m) | 125,9 | 0,21 | 1,56 | 27,4 |
| SVD gesund #6 (w) | 251,3 | 0,33 | 2,19 | 27,2 |
| SVD Parkinson | 161,0 | 0,50 | 2,99 | 18,8 |
| SVD ALS | 154,1 | 0,43 | 5,19 | 21,1 |
| Eigene NV-BFU8 (gesund) | 100,1 | 0,59 | 7,61 | 16,5 |
| Eigene NV-Z8YW (gesund) | 95,0 | 0,64 | 9,72 | 12,5 |

**Innerhalb SVD bestätigt sich jetzt das erwartete Muster** (gesund klar besser als
pathologisch bei Jitter/Shimmer/HNR) — mit dem vorherigen TORGO-Vergleich (falscher
Aufgabentyp, siehe oben) war das noch nicht sauber zu zeigen.

**Neuer, bisher nicht erklärter Befund**: unsere EIGENEN gesunden Aufnahmen (NV-BFU8/NV-Z8YW)
zeigen durchgehend SCHLECHTERE Jitter-/Shimmer-/HNR-Werte als sogar die SVD-*Patient:innen*
(Parkinson/ALS). Plausibelste Erklärung (nicht verifiziert, nur Hypothese): unterschiedliche
Aufnahmeketten — SVD nutzt kontrollierte Klinik-Laborausrüstung (dediziertes Mikrofon, EGG-
synchronisiert, ruhiger Raum), unsere Aufnahmen laufen über Browser-Mikrofon im Alltagsumfeld.
Jitter/Shimmer gelten in der Literatur als empfindlich gegenüber Aufnahmebedingungen. **Wichtiger
Interpretations-Vorbehalt**: unsere absoluten Jitter-/Shimmer-Werte könnten durch die
Aufnahmeumgebung systematisch leicht erhöht sein, unabhängig vom Gesundheitszustand der
sprechenden Person — noch nicht verifiziert, aber ein Punkt für die künftige
Interpretations-Vorsicht (siehe auch "Offene Grundsatzfrage" in `docs/backlog.md`).

## WER/CER-Test am ersten menschlich gegengehörten Dysarthrie-Fall (2026-08-17)

**`svd_als_phrase.wav`** (AufnahmeID 1242, ALS-Sprecher, Satz "Guten Morgen, wie geht es
Ihnen?") — vom Nutzer selbst angehört und bestätigt: "super dysarthrie beispiel". Erster
Fall in dieser Sammlung, der die neue Gegenlese-Prozessregel (siehe oben) tatsächlich
durchlaufen hat. Über den Worker-Container direkt mit WhisperX transkribiert und mit
`core/speech_intelligibility.py::compute_intelligibility_score()` ausgewertet:

- **Erkannter Text**: "Guten Morgen. Wie geht es Ihnen?" — inhaltlich exakt richtig.
- **WER: 0,0 % — CER: 0,0 %.**
- **Aber Ø Erkennungs-Konfidenz nur 52,3 %**, 5 von 6 Wörtern unter der 75%-Schwelle:
  "es" 5,4 %(!), "Ihnen?" 34,6 %, "geht" 45,8 %, "Wie" 62,7 %, "Guten" 73,5 %. Nur "Morgen."
  war mit 91,6 % sicher erkannt.

**Wichtiger methodischer Befund**: bei einem kurzen, hochgradig vorhersehbaren Satz (einer
Standard-Begrüßungsfloskel) kann WhisperX die richtigen Wörter offenbar aus dem Sprachmodell-
Kontext "erraten", selbst wenn das akustische Signal laut Konfidenzwerten kaum zu erkennen
war. **Reine WER/CER wäre hier also ein irreführend "perfektes" Ergebnis gewesen** — hätte
suggeriert, die Aufnahme sei völlig unauffällig verständlich, obwohl es sich um einen vom
Menschen bestätigten, eindrücklichen Dysarthrie-Fall handelt. **Die Erkennungs-Konfidenz
(bereits an anderer Stelle in der App vorhanden, siehe `views/vorlesen.py` "Ø Erkennungs-
Konfidenz"/"Unsichere Wörter") ist für kurze, prädiktive Sätze offenbar der empfindlichere
Indikator als WER/CER allein.** Für die Interpretations-Praxis: WER/CER und Konfidenz-Werte
immer GEMEINSAM betrachten, nicht WER/CER isoliert als "Verständlichkeits-Score" verwenden —
ergänzt/relativiert den ursprünglichen Ansatz aus `docs/backlog.md` "Speech-Intelligibility-
Score (WER/CER)", ohne ihn zu verwerfen (bei längeren, weniger vorhersehbaren Texten dürfte
WER/CER empfindlicher sein als bei diesem kurzen Standardsatz).

Datei jetzt vollständig in die Testdatenbank integriert: `EXT-SVD-ALS-1242` (Vokal + Satz,
auf dem Server verifiziert).

## Offene Punkte für die nächste Erweiterung

- [ ] **Höchste Priorität**: alle 9 Dateien in der Tabelle oben von einem Menschen gegenhören
      lassen (Sprache/Inhalt/Qualität, siehe Prozessregel oben) — bisher nur automatisiert per
      Signalanalyse geprüft, nicht angehört.
- [x] Gesunde SVD-Referenz ✅ NACHGELIEFERT (2026-08-17, siehe Nachtrag oben) — einmaliger
      voller `healthy.zip`-Download (6GB, temporär, danach vollständig gelöscht), 2 beste von
      7 Kandidaten behalten (~200KB).
- [ ] Der neue Befund "eigene Aufnahmen zeigen schlechtere Jitter/Shimmer als sogar SVD-
      Patient:innen" (siehe Nachtrag oben) ist nur eine Hypothese (Aufnahmekette/-umgebung) —
      noch nicht verifiziert. Müsste z.B. mit einem dedizierten externen USB-Mikrofon
      gegengetestet werden, um Browser-Mikrofon-Pipeline als Ursache zu bestätigen/auszuschließen.
- [ ] SVD-Satz-Dateien (`svd_parkinson_phrase.wav`/`svd_als_phrase.wav`) noch nicht gegen
      Sprechrate/WER getestet — braucht WhisperX (läuft nur im Docker-Container, nicht in
      diesem lokalen Skript-Kontext). Nächster Schritt: über `views/testdaten.py` (freie
      Dateiauswahl) auf dem Server hochladen und durchlaufen lassen.
- [ ] `Dysarthrophonie.zip` (143,8MB) und `Bulbärparalyse.zip` (25,5MB) noch nicht gezogen —
      mehr Fälle für eine breitere Stichprobe.
- [ ] TORGO-Datensatz enthält laut eigener Dokumentation auch gehaltene Vokal-Aufgaben (nicht
      nur Woerter/Saetze) — noch nicht gezielt danach gesucht, nur eine zufällige Datei
      getestet. Könnte bei gezielter Auswahl doch fürs Vokalisation-Modul nutzbar sein.
- [ ] `healthy_MC02_..._0045.wav` (zu leise, SNR 1,9dB) noch nicht gezielt gegen die
      `core/shared.py::quality_tiles()`-UI getestet — prüfen, ob die App diese schlechte
      Aufnahme zuverlässig als Warnung anzeigt (echter Negativ-Test für den Qualitäts-Check).
- [ ] `healthy_FC02_..._0048.wav` und `healthy_MC04_..._0026.wav` (beste Qualität, siehe
      Tabelle oben) noch nicht über die eigentliche App-UI (`views/testdaten.py`) hochgeladen
      und angeschaut — bisher nur per Skript gegen `core/audio.py` getestet.
