# NeuroVoice AI — Lokales Sprachbiomarker-System

Lokale, datenschutzkonforme Plattform zur Aufzeichnung und Analyse von Sprache/Stimme
für neurologische Verlaufskontrolle (Parkinson, Dysarthrie, etc.). Kein Diagnose-KI-Ersatz,
sondern objektive Sprachbiomarker über Zeit (longitudinal) — analog zu einer EEG-Verlaufsanalyse,
nur auf Basis akustischer Sprachmerkmale statt Hirnstromkurven.

## Status

🟡 Konzeptphase — Phase 1 (Aufnahme-Pipeline) in Umsetzung, noch kein Nutzer außer Testaufnahmen des Entwicklers.

## Phasen

- **Phase 1 (aktuell)**: Audioaufnahme-Pipeline. iPhone (Voice Memos, ALAC lossless) → Syncthing → Server
  (Beelink, Ubuntu) → verlustfreie Konvertierung zu WAV via ffmpeg → verifiziert (Checksumme + ffprobe) →
  pseudonymisiert abgelegt.
- **Phase 2+**: Feature-Extraktion (siehe [docs/backlog.md](docs/backlog.md) und
  [docs/literatur_review.md](docs/literatur_review.md)), beginnend mit den etablierten, einfachen
  Phonation-Features (F0/Jitter/Shimmer/HNR am gehaltenen Vokal), dann schrittweise Ausbau Richtung
  Spektral-/Artikulations-/Prosodie-/Zeitstruktur-Features (eGeMAPS-Umfang als Zielhorizont).
- **Später (nicht Teil des aktuellen Auftrags)**: Whisper-Transkription, ML-Klassifikation,
  lokales LLM für Berichte.

## Hardware

- Server: Beelink Mini-PC, Intel N150, 12GB RAM, 512GB SSD, Ubuntu Linux
- Aufnahmegerät: iPhone (Voice Memos, Lossless/ALAC, bis 24bit/48kHz)
- Perspektivisch: externes USB-Mikro (z.B. Rode NT-USB Mini) für höhere Qualität

## Aufnahme-Konzept

- Dauer: **10 Sekunden Snippets (Standard, bewusst kurz gehalten gegen Datenmüll)**
- Task-Typen: Freisprache, gehaltener Vokal ("aaa"), Lesetext
  (wichtig: unterschiedliche Feature-Familien sind nur bei bestimmten Task-Typen zuverlässig
  extrahierbar — siehe Literaturrecherche, Abschnitt "Einschränkungen")
  - Lesetext "Nordwind und Sonne" passt nicht komplett in 10s — für den Start reicht der erste
    Satz ("Einst stritten sich Nordwind und Sonne, wer von ihnen beiden wohl der Stärkere wäre...")
- Sprechabstand konstant halten (~15-20cm), unteres iPhone-Mikro nicht verdecken

## Ordnerstruktur (Daten)

```
data/raw/<patient_id>/YYYY-MM-DD_HHMM_task-<typ>_take<n>.wav
```

`patient_id` ist pseudonymisiert (DSGVO-tauglich von Anfang an). Aktuell nur Testaufnahmen des
Entwicklers selbst, echte Zuordnungstabelle noch nicht relevant/konzipiert.

## Übertragung iPhone → Server

Syncthing (P2P, verschlüsselt, kein Cloud-Zwischenspeicher) — Zielarchitektur von Anfang an,
kein Zwischenschritt über SMB/eigene Web-App.

## Repo-Struktur

- `docs/` — Konzept, Backlog, Literaturrecherche, [Bug-/Problem-Tracker](docs/bugtracker.md)
- `raw-inbox/` — Syncthing-Zielordner (unveränderte .m4a-Dateien, noch nicht konvertiert/einsortiert)
- `data/raw/` — finale Ablage nach Konvertierung + Umbenennung
- `scripts/` — Konvertierungs-/Verifikations-Skripte
- `dashboard/` — Streamlit-Analyse-Dashboard (siehe docs/dashboard_konzept.md)

## Lokal starten (Mac/Windows, per Docker)

Das komplette Analyse-Dashboard lässt sich vollständig lokal betreiben — keine Cloud, kein
externer Server nötig, alle Daten bleiben auf dem eigenen Rechner. Primär entwickelt und
getestet für **Apple Silicon (M1–M5)**, läuft aber auch unter Windows (Docker Desktop mit
WSL2-Backend) und auf Intel-Macs — der Host-Betriebssystem-Unterschied ist für den Container
selbst irrelevant, Docker startet überall denselben Linux-Container, nur die
CPU-Architektur (arm64 vs. amd64) wird beim Bauen automatisch passend berücksichtigt.

```bash
cd dashboard
docker compose -f docker-compose.local.yml up -d --build
```

Danach im Browser: **http://localhost:8501**

### Systemanforderungen (Disclaimer)

- Docker Desktop installiert und gestartet (Mac oder Windows)
- **Empfohlen: mind. 8 GB RAM für Docker Desktop freigegeben** — die Spracherkennung
  (WhisperX, Modell „large-v3") braucht das; mit weniger RAM kann der Hintergrund-Worker-
  Container abstürzen (`OOMKilled`)
- **Mind. ~10 GB freier Speicherplatz** (Python-Abhängigkeiten + Sprachmodell)
- **Internetzugang beim allerersten Start** — lädt einmalig ein ca. 3 GB großes
  Spracherkennungsmodell herunter (danach lokal zwischengespeichert, kein erneuter Download
  bei künftigen Starts)
- Mikrofonzugriff im Browser (Chrome/Safari/Edge) für eigene Aufnahmen
- Moderne Rechner der letzten Jahre erfüllen das in der Regel problemlos — auf älterer/
  schwächerer Hardware kann besonders die Transkription spürbar länger dauern

Zwei Container starten gemeinsam: das eigentliche Dashboard (Web-Oberfläche) und ein
getrennter Hintergrund-Worker, der die Spracherkennung übernimmt, damit die Oberfläche
währenddessen nicht blockiert (siehe
[docs/konzept_p9_hintergrundjob_lokal.md](docs/konzept_p9_hintergrundjob_lokal.md)).

Alle Daten (Aufnahmen, abgeleitete Ergebnisse, das heruntergeladene Sprachmodell) liegen in
Docker-eigenen, persistenten Volumes — sie überstehen ein `docker compose down`/`up`, werden
aber NICHT automatisch irgendwohin gesichert. Wer direkten Dateizugriff auf einem eigenen
Host-Ordner statt eines Docker-Volumes möchte, kann `NEUROVOICE_HOST_DATA_DIR`/
`NEUROVOICE_HOST_DERIVED_DIR` per `.env`-Datei setzen (siehe Kommentare in
`dashboard/docker-compose.local.yml`).
