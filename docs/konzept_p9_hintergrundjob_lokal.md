# Konzept: P9 — Transkription als Hintergrund-Job + lokale Docker-Nutzung (Mac/Windows)

## Nachtrag 2026-08-16: lokaler Docker-Workflow pausiert — Server bleibt primärer Testweg

Nach dem echten lokalen Testlauf (arm64-Build erfolgreich, Container liefen) zeigte sich beim
Transkribieren ein reales Problem: Docker Desktop auf diesem Mac hat nur 8GB VM-Speicher
zugeteilt (bei insgesamt 16GB physischem RAM), und der Worker allein brauchte beim
gleichzeitigen Laden von WhisperX large-v3 + deutschem Alignment-Modell ~6GB — zu knapp, wenn
parallel noch andere lokale Docker-Projekte laufen (hier: `nz-dienstplan`). Ergebnis: der
Worker-Container stürzte ab/startete neu (`RestartCount: 1`), ein Job blieb verwaist bei 60%
"running" stehen, ein zweiter zeigte "Job nicht gefunden". **Kein Software-Bug** — der Server
hat 12GB RAM exklusiv plus ein festes 7GB-Limit nur für den Worker, ohne Konkurrenz durch
andere Projekte, deshalb lief es dort bisher immer sauber.

**Nutzer-Entscheidung 2026-08-16**: lokale Docker-Nutzung als aktiven Entwicklungs-/Test-
Workflow PAUSIEREN — die andere lokal laufenden Docker-Projekte (nz-dienstplan) und die
NeuroVoice-Container selbst wurden gestoppt (Named Volumes mit Modell-Cache bleiben aber
erhalten). **Primärer Arbeitsablauf ab sofort wieder: Server-Deploy via SSH/scp**, wie vor P9.
Der Code für die lokale Docker-Variante (`docker-compose.local.yml`, Dockerfile-Fixes,
README-Doku) bleibt vollständig im Repo erhalten und funktionsfähig — wird aber NICHT mehr bei
jeder kleinen Änderung parallel mitgezogen/getestet. Stattdessen: **einmal am Ende, wenn die
Software einen stabilen/finalen Stand erreicht hat**, wird die lokale Docker-Variante für
Nutzer:innen mit anderen Betriebssystemen (Mac/Windows/Linux ohne Zugriff auf den eigenen
Server) fertig poliert und verifiziert — als bewusster, separater Abschlussschritt, nicht als
laufende Nebenspur.

Status: **Konzept, NICHT umgesetzt** (2026-08-16, Nutzer-Auftrag: "mache als nächstes P9 —
bereite ein Konzept vor, Ziel ist, dass User das Tool lokal auf Mac oder Windows laufen lassen
können, z.B. über Docker"). Siehe `docs/backlog.md` P9 und `docs/bugtracker.md` RANDNOTIZ-13
für die ursprüngliche Problembeschreibung.

## Zwei Probleme, ein Umbau

Bisher zwei getrennt wirkende Anliegen, die sich beim Durchdenken als DASSELBE
Architekturproblem herausstellen:

1. **P9 selbst**: WhisperX blockiert aktuell die komplette Streamlit-Sitzung für 1-2 Minuten
   (`core/shared.py::transcribe_with_progress()` läuft zwar schon in einem Hintergrund-Thread,
   aber INNERHALB derselben Skript-Ausführung — die Seite bleibt bis zum Ende in einer
   `while`-Schleife mit `time.sleep()` gefangen, kein Navigieren, kein Reagieren möglich).
2. **Neues Ziel**: Nutzer:innen sollen NeuroVoice AI komplett lokal auf ihrem eigenen Mac/
   Windows-Rechner betreiben können (z.B. per `docker compose up`), unabhängig vom
   Beelink-Server/Tailscale — reines Self-Hosting, Daten verlassen nie die eigene Maschine.

Eine echte Hintergrund-Job-Architektur (statt eines blockierenden Thread-in-Skript-Tricks)
löst P9 UND macht die App gleichzeitig robuster für einen leistungsschwächeren lokalen
Rechner (Laptop im Akkubetrieb, weniger Kerne als der Server) — deshalb hier als EIN Konzept
behandelt, nicht zwei getrennte.

## Warum der aktuelle Fix (P8-Fortschrittsleiste) nicht reicht

`transcribe_with_progress()` (siehe `core/shared.py`) macht die Wartezeit ehrlicher (echte
Prozent-Schätzung statt unbestimmtem Spinner), löst aber nicht das eigentliche Problem: die
WhisperX-Inferenz ist CPU-intensiv genug, um auf einem 4-Kern-Rechner (Beelink N150, aber genauso
ein durchschnittlicher Laptop) praktisch alle Kerne für die Dauer zu beanspruchen — die
Streamlit-Session selbst bleibt bis zum Ende der `while`-Poll-Schleife in EINER Skriptausführung
gefangen (kein Seitenwechsel möglich, "bitte nicht wegnavigieren" ist die aktuelle
Sofortmaßnahme, keine echte Lösung). Bei mehreren gleichzeitigen Nutzer:innen auf demselben
Server (aktuell nicht der Fall, aber relevant sobald das Tool geteilt wird) würde das zusätzlich
andere Sitzungen ausbremsen.

## Vorgeschlagene Architektur: datei-basierte Job-Queue + Streamlit-Fragment-Polling

Bewusst OHNE neue Infrastruktur (kein Redis/RabbitMQ/Celery) — passt zum Projekt-Prinzip
"so einfach wie möglich, lokal, kein zusätzlicher Betriebsaufwand" und zum bereits etablierten
Muster in `core/session_store.py` (Zustand als JSON-Dateien unter `NEUROVOICE_DERIVED_DIR`).

**Neue Bausteine:**

- **`core/job_queue.py`** (neu) — kleine Helper-Funktionen `submit_job(kind, payload) -> job_id`,
  `get_job_status(job_id) -> dict`, `write_job_result(job_id, result)`. Jobs als JSON-Dateien
  unter `/derived/_jobs/<job_id>.json` mit Feldern `status` (`pending`/`running`/`done`/`error`),
  `kind` (z.B. `"transcription"`), `payload` (z.B. `audio_path`), `progress` (0-100, optional),
  `result`/`error_message`. Gleiches Namensschema wie `_sessions`/`_subjects`/`_uploads` —
  konsistent mit dem Rest des Speicherschemas.
- **`worker.py`** (neu, eigener Container-Prozess) — Endlosschleife: alle ~1s `/derived/_jobs/`
  nach `status=pending` durchsuchen, ältesten Job nehmen, `status=running` setzen, je nach `kind`
  die passende Funktion aufrufen (aktuell nur `core.transcription.transcribe()`, aber bewusst
  generisch benannt — spätere Kandidaten: Feature-Extraktion bei sehr langen Aufnahmen), Ergebnis
  in den bestehenden Transkript-Cache UND in die Job-Datei schreiben, `status=done`/`error`.
- **`views/vorlesen.py` / `views/spontansprache.py`** (Umbau) — statt der bisherigen
  `while`-Poll-Schleife: Klick auf "Transkribieren" ruft `submit_job()` auf und merkt sich die
  `job_id` in `st.session_state`, danach rendert ein
  `@st.fragment(run_every="1s")`-Block (natives Streamlit-Primitiv seit 1.35, aktuell im
  Projekt bereits per `requirements.txt` vorausgesetzt) NUR diesen kleinen Teil der Seite neu und
  liest den Job-Status — der Rest der Seite (Navigation, andere Tabs/Module) bleibt die ganze
  Zeit voll interaktiv. Job-Zustand liegt auf Platte, übersteht also auch einen Reload/Wechsel
  auf eine andere Seite und zurück (analog zu `session_store.py`'s bestehendem
  Reload-Überlebens-Prinzip).

**Ablauf aus Nutzer:innen-Sicht:** Klick auf "Transkribieren" → Seite bleibt sofort bedienbar,
kleine Fortschrittsanzeige läuft nebenbei weiter (auch wenn man zwischendurch auf eine andere
Modul-Seite wechselt und zurückkommt) → Ergebnis erscheint automatisch, sobald der Worker fertig
ist, ohne dass man an der Seite "festhängen" muss.

**Warum nicht `multiprocessing`/`ProcessPoolExecutor` direkt im Streamlit-Prozess?** Würde das
Problem nur pro Sitzung lösen (Skript kehrt zurück, während der Pool im Hintergrund rechnet),
aber der Streamlit-Serverprozess selbst würde weiterhin die volle CPU-Last mit anderen
Anfragen/Sitzungen teilen müssen (kein eigenes Ressourcen-Limit). Ein getrennter Worker-Container
kann über Docker (`cpus:`/`mem_limit:` in `docker-compose.yml`) unabhängig gedrosselt werden,
ohne den UI-Container zu beeinträchtigen — sauberer bei künftiger Mehrnutzer-Situation, und exakt
dasselbe Muster funktioniert identisch lokal auf einem Laptop.

## Docker-Compose: lokale Variante für Mac/Windows

Der aktuelle `dashboard/docker-compose.yml` ist server-spezifisch fest verdrahtet und würde so
auf keinem fremden Rechner laufen:

| Aktuell (Beelink-spezifisch) | Problem für lokale Nutzung |
|---|---|
| `<TAILSCALE-IP>:8501:8501` (Tailscale-IP-Bind) | Diese IP existiert nur auf dem Server — lokal müsste `127.0.0.1:8501:8501` gebunden werden |
| `/home/maximilian/neurovoice-data/raw:/data:ro` (Host-Bind-Mount, fester Pfad) | Auf einem fremden Rechner existiert dieser Pfad nicht |
| `mem_limit: 7g` | Kalibriert, um NICHT die anderen Dienste auf dem 10GB-Server zu verdrängen (Dienstwerk, EEG-Navigator) — für einen dedizierten lokalen Rechner irrelevant/zu niedrig |

**Vorschlag:** ein zweites Compose-File `docker-compose.local.yml` (oder `docker-compose.override.yml`,
Docker-Compose-Konvention für lokale Overrides) mit:
- Port-Bind auf `127.0.0.1:8501:8501` (kein Tailscale nötig, einfach `localhost:8501` im Browser)
- Named Volumes statt Host-Bind-Mounts für `/data`/`/derived` (Docker verwaltet den Speicherort
  selbst, keine Host-Pfad-Annahme) — optional per `.env`-Variable `NEUROVOICE_HOST_DATA_DIR`
  überschreibbar für Nutzer:innen, die direkten Dateizugriff wollen
- `mem_limit` konfigurierbar/dokumentiert statt hart auf 7g fixiert (Empfehlung im README:
  "mind. 8GB RAM-Limit in Docker Desktop empfohlen, WhisperX large-v3 braucht das")
- **Zweiter Service `neurovoice-worker`** (siehe oben), teilt sich Volumes mit dem
  UI-Container, läuft aber als eigener Prozess/Container

Der bestehende `docker-compose.yml` (Server-Variante) bleibt unverändert bestehen — die lokale
Variante ist rein additiv, kein Breaking Change für den Beelink-Produktivbetrieb.

## Offene Fragen / Risiken, die vor der Umsetzung geklärt werden sollten

1. **Apple Silicon (arm64) — ✅ VOLLSTÄNDIG VERIFIZIERT (2026-08-16), finaler Build
   erfolgreich.** Nach beiden Fixes unten lief ein kompletter, cache-freier Neubau
   (`--no-cache-dir`) in **ca. 21 Minuten** erfolgreich durch. Im fertigen Image bestätigt:
   `torch 2.8.0+cpu` (kein CUDA), `whisperx` importierbar, `parselmouth 0.4.7` funktionsfähig,
   `core.job_queue` funktionsfähig. Nachfolgende Builds nutzen den Docker-Layer-Cache und
   sind deutlich schneller (Sekunden statt Minuten), solange sich Dockerfile/requirements.txt
   nicht ändern.

   Unterwegs zwei echte Funde gemacht, beide behoben: der native
   arm64-Testbuild auf einem M-Series-Mac (2026-08-16) zeigte zunächst: `praat-parselmouth` hat KEIN
   vorgebautes Wheel für `linux/arm64` (nur für `linux/amd64` und macOS) — pip versucht,
   es aus dem Quellcode zu bauen, was im schlanken Basis-Image (`python:3.11-slim-bookworm`,
   kein Compiler) fehlschlug. **Fix**: `build-essential`/`cmake` im Dockerfile ergänzt, damit
   arm64 den C++-Code kompilieren kann (amd64 nutzt weiterhin das fertige Wheel, Pakete dort
   ungenutzt aber harmlos).
   **Zweiter, wichtigerer Fund unterwegs: CUDA-Fehlgriff bei Torch auf arm64.** Der
   Build-Dauer-Verdacht ("das dauert ungewöhnlich lange, deutlich länger als der
   Server-Rebuild") führte zu einer genaueren Prüfung des Torch-Installationsschritts — und
   DAS war der eigentliche Haupttreiber, nicht (nur) die Parselmouth-Kompilierung: ein
   normales `pip install torch` OHNE Angabe des PyTorch-CPU-Index-Repositorys zieht auf
   `linux/arm64` versehentlich die KOMPLETTE CUDA/NVIDIA-Toolkit-Kette mit (`cuda-toolkit`,
   `nvidia-cudnn`, `nvidia-cublas`, `triton` etc. — mehrere hundert MB voellig nutzloser
   GPU-Pakete auf einem Mac ohne NVIDIA-GPU). Ursache: das amd64-spezifische
   `--index-url https://download.pytorch.org/whl/cpu` wurde vorher nur fuer amd64 genutzt (in
   der (irrigen) Annahme, das normale PyPI-Wheel sei auf arm64 ohnehin schon CPU-only) --
   empirisch widerlegt: `pip install --dry-run --index-url .../whl/cpu torch` liefert AUCH
   fuer arm64 ein sauberes `torch-X.Y.Z+cpu`-Wheel ohne jede CUDA-Abhaengigkeit. **Fix**: das
   CPU-Index-Repository jetzt IMMER nutzen, unabhaengig von der Architektur, kein
   TARGETARCH-Unterschied mehr noetig (einfacher UND korrekter als vorher).
   **Build-Dauer-Befund (2026-08-16, fuer die Akte)**: mit dem CUDA-Fix sank der
   Torch-Download-Anteil von der vollen CUDA-Kette auf ein einzelnes ~155MB-Wheel. Die
   Parselmouth-Kompilierung selbst bleibt trotzdem der laengste Einzelschritt -- in einem
   vollstaendig frischen (`--no-cache-dir`, kein Docker-Layer-Cache) Testbuild lief sie
   ueber 10 Minuten am Stueck (pip meldet alle 60s "still running..." waehrenddessen, kein
   Fehler/Haenger, nur echte Kompilierzeit fuer Praats umfangreichen C/C++-Code). **Praktische
   Konsequenz fuers README**: den EINMALIGEN Erstbuild auf Apple Silicon als "kann spuerbar
   laenger dauern als gewohnt (zweistellige Minutenzahl moeglich, ueberwiegend wegen der
   einmaligen Parselmouth-Kompilierung aus dem Quellcode), das ist normal, kein Haenger"
   ankuendigen -- nachfolgende Starts nutzen den Docker-Layer-Cache und sind schnell.
## Konzept: Cleanup — nur installieren, was wirklich gebraucht wird

**Nachtrag 2026-08-16, Nutzer-Auftrag** ("ein Konzept mit Cleanup, das nur behält, was wir
wirklich brauchen, unnötige z.B. NVIDIA-Pakete löschen"): Beim Nachprüfen des bereits
deployten Server-Images (`pip list | grep nvidia`) stellte sich heraus, dass der erste
CUDA-Fix (siehe oben, "Torch selbst pinnen") NICHT ausreichte — 13 `nvidia-*-cu12`-Pakete
plus `triton` waren trotzdem installiert, mehrere GB reine GPU-Bibliotheken auf einem Server
ohne GPU.

**Root Cause (zweite Stufe des CUDA-Problems):** `whisperx` verlangt zusätzlich zu `torch`
auch `torchaudio`/`torchvision`. Die wurden vorher NICHT über das CPU-Index-Repository
vorinstalliert — nur `torch` allein. Beim nachfolgenden `pip install -r requirements.txt`
löste pip `torchaudio`/`torchvision` deshalb über den NORMALEN PyPI-Index auf, und deren
Standard-Wheels für Linux hängen ihrerseits von den `nvidia-*-cu12`-Paketen ab (PyTorch linkt
CUDA seit einigen Versionen dynamisch über separate pip-Pakete statt es einzubauen) — die
komplette CUDA-Kette kam so durch die Hintertür zurück, obwohl `torch` selbst korrekt
CPU-only war.

**Fix**: `torch`, `torchaudio` UND `torchvision` gemeinsam, mit zu whisperx' eigenen
Anforderungen passenden Versions-Pins, über das CPU-Index-Repository installieren (siehe
Dockerfile). Per `pip install --dry-run` gegenverifiziert: liefert ausschließlich
`torch-2.8.0+cpu`/`torchaudio-2.8.0`/`torchvision-0.23.0` plus reine CPU-Abhängigkeiten,
KEIN einziges `nvidia-*`-Paket mehr.

**Allgemeines Prinzip für künftige Dependency-Änderungen** (damit diese Fehlerklasse nicht
wiederkehrt): Wenn ein Paket (wie `torch`) über ein alternatives Index-Repository installiert
wird, um eine bestimmte Variante (hier: CPU-only) zu erzwingen, reicht das NICHT automatisch
für Pakete, die DAVON ABHÄNGEN (`torchaudio`/`torchvision`) — die müssen explizit im selben
Schritt über dasselbe Repository mitinstalliert werden, sonst löst der nächste `pip install`
sie über den Standard-Index auf und kann die eigentlich vermiedene Variante durch die
Hintertür zurückholen. Als Verifikations-Routine nach JEDER Dependency-Änderung an
torch/whisperx: `docker exec <container> pip list | grep -i nvidia` sollte leer sein.

**Cleanup-Zustand nach dem Fix** (Docker-Hygiene, allgemein, nicht nur für diesen Fall):
- Docker-Build-Cache aus fehlgeschlagenen/veralteten Build-Versuchen wird nach jedem
  bestätigt erfolgreichen Rebuild bereinigt (`docker builder prune -f`) — nicht während eines
  noch laufenden Builds (kann diesen stören).
- Nur das jeweils aktuelle, getaggte Image pro Dienst wird behalten — Test-/Zwischen-Tags
  (wie `neurovoice-arm64-verify2` in dieser Session) werden nach erfolgreicher Verifikation
  wieder gelöscht, nicht als Altlast liegen gelassen.
- Images anderer Projekte (`anonymisator`, `edf-analyzer`, etc.) werden dabei NIE angefasst —
  Cleanup ist immer auf die gerade betroffenen Test-/Zwischenartefakte beschränkt.

**✅ VOLLSTÄNDIG VERIFIZIERT, beide Plattformen (2026-08-16):**
- **Server (amd64)**: `pip list | grep -iE 'nvidia|cuda'` leer, Image 15,1GB → 5,22GB,
  `triton` (722,9MB) bewusst als legitime Direkt-Abhängigkeit von `whisperx` belassen, ~42GB
  Alt-Cache bereinigt.
- **Lokal (Apple Silicon, arm64)**: `pip list | grep -iE 'nvidia|cuda'` ebenfalls leer — hier
  fehlt sogar `triton` komplett (dessen Paket-Metadaten schließen arm64 offenbar aus, da
  primär für x86-GPU-Setups gedacht). Image 4,69GB → 3,84GB. Kompletter Neubau ohne Cache:
  ca. 14 Minuten (schneller als der allererste arm64-Build mit 21 Minuten, da keine großen
  CUDA-Wheels mehr heruntergeladen werden mussten — die Parselmouth-Kompilierung bleibt der
  dominante Zeitfaktor, siehe oben).

2. **Windows/Intel-Mac**: unkritischer, da Docker Desktop dort ohnehin dasselbe `linux/amd64`-
   Image wie der Server nutzt — der Host-Betriebssystem-Unterschied ist für den Container selbst
   irrelevant, `praat-parselmouth` bringt für Linux-amd64 bereits vorgebaute Wheels mit (bereits
   heute im Server-Image bewiesen funktionsfähig).
3. **Erster Start lädt ~3GB WhisperX-large-v3-Modell herunter** — braucht Internetzugang beim
   allerersten Lauf und kann je nach Verbindung dauern. Sollte im README UND idealerweise als
   In-App-Hinweis ("Erster Start: Sprachmodell wird heruntergeladen, das kann einige Minuten
   dauern") sichtbar gemacht werden, damit es nicht wie ein Hänger wirkt (dieselbe Lehre wie bei
   RANDNOTIZ-13). Zusätzlich denkbar: `DEFAULT_MODEL` (`core/transcription.py`) über eine
   Umgebungsvariable konfigurierbar machen, damit Nutzer:innen mit schwächerer Hardware/
   langsamerer Leitung ein kleineres Modell (z.B. `medium`) wählen können — Trade-off Genauigkeit
   gegen Geschwindigkeit/Downloadgröße, aktuell hart auf `"large-v3"` fixiert (bewusste
   Genauigkeits-Vorgabe vom 2026-07-21, siehe Docstring `core/transcription.py`) — diese Vorgabe
   nicht heimlich aufweichen, sondern als NUTZER-WAHL anbieten, Standard bleibt `large-v3`.
4. **Kein Multi-User-Zugriffsschutz.** Eine lokale Installation läuft typischerweise für eine
   einzelne Person — das bereits in `ROAD_TO_PUBLIC.md` dokumentierte Fehlen eines Auth-Layers
   ist dafür unkritisch (nur `localhost` erreichbar), aber falls jemand den Port trotzdem nach
   außen öffnet (Portweiterleitung o.ä.), gilt derselbe Vorbehalt wie beim Server — gehört in die
   README-Sicherheitshinweise, kein Code-Fix hier nötig.

## Umsetzungsschritte (grob geschätzt, in dieser Reihenfolge — "kein kleiner Schritt", daher
in Teilschritte zerlegt)

1. `core/job_queue.py` + `worker.py` bauen, lokal gegen eine echte Audiodatei testen (Job wird
   erstellt, Worker holt ihn ab, Ergebnis landet korrekt im Cache).
2. `views/vorlesen.py`/`views/spontansprache.py` auf `st.fragment(run_every=...)`-Polling
   umstellen, `transcribe_with_progress()` (bisherige Thread-Variante) ablösen.
3. Zweiten Service im bestehenden Server-`docker-compose.yml` ergänzen (Worker läuft ab jetzt
   auch auf dem Beelink mit), Server-Regression: alle 7 Seiten + eine echte Transkription
   end-to-end testen, dass currently laufender Betrieb nicht bricht.
4. `docker-compose.local.yml` bauen + README-Abschnitt "Lokal starten" schreiben (Synergie mit
   dem ohnehin fälligen README-Rewrite aus `ROAD_TO_PUBLIC.md`/P16).
5. arm64-Kompatibilität verifizieren (Punkt 1 oben), Ergebnis dokumentieren — falls arm64 nicht
   sauber läuft, das im README klar kommunizieren statt es zu verschweigen.
6. Optional: `NEUROVOICE_WHISPER_MODEL`-Umgebungsvariable für Modellgröße.

Nichts davon ist umgesetzt — dies ist ausschließlich das Konzept zur Freigabe/Diskussion.
