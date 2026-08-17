# Externe Referenz-Testdaten — laufend gepflegte Sammlung

**Zweck**: unsere Algorithmen (Jitter/Shimmer/HNR/CPPS/Sprechrate/...) gegen extern gelabelte,
unabhängige Aufnahmen (bekannt gesund ODER bekannt pathologisch) testen — Robustheit prüfen
UND schauen, ob sich ähnliche Muster zeigen wie bei unseren eigenen simulierten Dysarthrie-
Durchläufen (siehe `docs/backlog.md` "Dysarthrie-Vergleichsstudie"). **Kein Ersatz für eine
echte klinische Validierungsstudie** — kleine Stichprobe, keine standardisierte Erhebung durch
uns selbst, aber besser als nur simulierte Daten.

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

## Bisher heruntergeladene/getestete Dateien

| Datei (lokal) | Quelle | Label | Dauer | Aufgabentyp | Für unsere Module geeignet? |
|---|---|---|---|---|---|
| `torgo_english/normal_FC01_0047.wav` | HF/TORGO, `non_dysarthria_female/FC01_Session1_0047.wav` | gesund (Studien-Label) | 5,3s | kurzes Wort/Satz (per Signalanalyse verifiziert: nur 35% stimmhaft, 17 Energie-Einbrüche in 5,3s — klar KEINE Vokalisation) | Nur bedingt Spontansprache, eigentlich nur Robustheitstest |
| `svd_pathological/svd_parkinson_a_n.wav` | Zenodo/SVD, AufnahmeID 1580, SprecherID 1887 | Morbus Parkinson + Dysphonie (Diagnose: "Hypotone Komponente, vox senilis") | 0,72s | gehaltener Vokal /a/, normale Tonlage | Ja — genau unser Vokalisation-Aufgabentyp |
| `svd_pathological/svd_parkinson_phrase.wav` | dieselbe Session | " | 2,31s | Satz "Guten Morgen, wie geht es Ihnen?" | Ja (Deutsch!) — aber noch nicht gegen Vorlesen/WER getestet (bräuchte WhisperX, läuft nur im Docker-Container) |
| `svd_pathological/svd_als_a_n.wav` | Zenodo/SVD, AufnahmeID 1242, SprecherID 1630 | ALS + zentral-laryngale Bewegungsstörung | 1,57s | gehaltener Vokal /a/, normale Tonlage | Ja |
| `svd_pathological/svd_als_phrase.wav` | dieselbe Session | " | 2,2s | Satz "Guten Morgen, wie geht es Ihnen?" | Ja, noch nicht gegen Vorlesen/WER getestet |

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

## Offene Punkte für die nächste Erweiterung

- [ ] Kleine "gesund"-Referenz aus SVD fehlt noch (6GB-Datei nicht teilbar) — Alternativen zu
      prüfen: (a) einmalig den vollen `healthy.zip`-Download in Kauf nehmen und nur wenige
      Dateien behalten, (b) eine dritte Quelle mit kleinen gesunden DEUTSCHEN Vokal-Aufnahmen
      suchen, (c) beim SVD-Team direkt nach einem kleineren Einzeldatei-Zugang fragen.
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
