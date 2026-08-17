# NeuroVoice AI — Lokales Sprachbiomarker-System

![Status](https://img.shields.io/badge/status-aktiv-brightgreen)
![Lizenz](https://img.shields.io/badge/Lizenz-GPL--3.0--or--later-blue)

Lokale, datenschutzkonforme Plattform zur Aufzeichnung und Analyse von Sprache/Stimme für die
**longitudinale Verlaufskontrolle** neurologischer Erkrankungen (z. B. Parkinson, Dysarthrie).
**Kein Diagnose-Ersatz** — die App stellt keine Diagnose und gibt keinen Krankheits-Score aus,
sondern liefert objektive, über Zeit vergleichbare Sprachbiomarker mit Literatur-Einordnung je
Wert, analog zu einer EEG-Verlaufsanalyse, nur auf Basis akustischer Sprachmerkmale statt
Hirnstromkurven.

## Status

🟢 Funktionsfähiges Analysewerkzeug, in aktivem Eigen-Test — noch kein Einsatz mit echten
Patient:innen außerhalb von Testaufnahmen des Entwicklers. Siehe [ROAD_TO_PUBLIC.md](ROAD_TO_PUBLIC.md)
für den aktuellen Stand Richtung öffentlicher Nutzung.

## Was die App tut

Ein geführtes Streamlit-Dashboard mit vier Aufnahme-Modulen, aufsteigend nach Aufwand, jedes
optional/überspringbar:

1. **Vokalisation** — gehaltener Vokal /a/ (Pflicht), optional /i//u/ (für den Vokalraum) und
   maximale Phonationsdauer (MPT).
2. **Vorlesen** — Standardtext "Nordwind und Sonne", automatisch transkribiert (lokal, siehe
   unten) für Sprechrate/Pausen-Kennwerte und lexikalische Diversität.
3. **Spontansprache** — freies Sprechen (~30s) zu einem gestuften Themen-Prompt.
4. **Diadochokinese (DDK)** — pa/ta/ka einzeln + kombiniert, für Artikulations-Rhythmus.

Jede Aufnahme kann mehrfach wiederholt werden (Take-Management); die beste Aufnahme wird manuell
ausgewählt — es wird **nichts automatisch gemittelt**. Pro Parameter zeigt die App Wert,
Normbereich, Status und einen Kontext-Kommentar mit Literaturquelle, klar nach Evidenzgrad
eingeordnet ("gut etabliert" / "in der Forschung diskutiert" / "eigene Heuristik" / "deskriptiv")
— siehe [docs/literatur_review.md](docs/literatur_review.md). Ein Gesamtbericht fasst alle
Module einer Sitzung zusammen und lässt sich als Excel/PDF exportieren.

Transkription (für Sprechrate/Pausen/Lexik) läuft komplett lokal über
[WhisperX](https://github.com/m-bain/whisperX) in einem eigenen Hintergrund-Prozess — keine
Cloud-API, keine Daten verlassen den eigenen Rechner/Server.

## Datenschutz-Prinzip

Bewusst **kein Name, keine Initialen** — jede Sitzung wird nur einer pseudonymen ID + Alter
zugeordnet (`core/subject_store.py`). Eine Re-Identifizierung liegt außerhalb der App bei der
aufnehmenden Person. **Wichtig**: die App hat aktuell **keinen eigenen Auth-Layer** — siehe
[SECURITY.md](SECURITY.md) für das Zugriffsmodell, bevor sie in einem Mehrbenutzer-/Netzwerk-
Kontext betrieben wird.

## Repo-Struktur

- `dashboard/` — das eigentliche Streamlit-Analyse-Dashboard (Code, Docker-Setup)
- `docs/` — Konzept, [Backlog](docs/backlog.md), [Literaturrecherche](docs/literatur_review.md),
  [Bug-/Problem-Tracker](docs/bugtracker.md)
- `raw-inbox/`, `data/raw/`, `scripts/` — optionaler Alternativ-Weg zur direkten Browser-
  Mikrofonaufnahme: Dateien per Syncthing/manuell einspielen und über `scripts/
  convert_and_verify.sh` verlustfrei nach WAV konvertieren, das Dashboard liest `data/raw/`
  read-only als zusätzliche Aufnahmequelle
- `ROAD_TO_PUBLIC.md` — Fahrplan/Checkliste Richtung öffentlicher Nutzung

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

### Systemanforderungen im Detail (Disclaimer)

Zwei Container starten gemeinsam: das Dashboard (Web-Oberfläche) und ein getrennter
Hintergrund-Worker, der die Spracherkennung (WhisperX) übernimmt, damit die Oberfläche
währenddessen nicht blockiert (siehe
[docs/konzept_p9_hintergrundjob_lokal.md](docs/konzept_p9_hintergrundjob_lokal.md)). Beide
laufen bei jeder Plattform als Linux-Container — Docker macht den Host-Betriebssystem-
Unterschied für den Container selbst irrelevant, nur die CPU-Architektur (arm64 vs. amd64)
bestimmt, welche Pakete heruntergeladen werden.

**Allgemein, unabhängig von der Plattform:**
- Internetzugang beim allerersten Start — danach läuft alles komplett offline/lokal weiter
- Mikrofonzugriff im Browser (Chrome/Safari/Edge) für eigene Aufnahmen
- Empfohlen: mind. 8 GB RAM für Docker Desktop/den Docker-Daemon freigegeben — WhisperX
  („large-v3") braucht das; mit weniger RAM kann der Worker-Container abstürzen (`OOMKilled`,
  siehe [docs/bugtracker.md](docs/bugtracker.md) INFRA-BEFUND-09, dort auf dem Server
  aufgetreten)

**Downloadgrößen (einmalig, danach zwischengespeichert):**

| Bestandteil | Größe | Wann |
|---|---|---|
| Python-Abhängigkeiten (Torch CPU, WhisperX-Ökosystem, Streamlit, Parselmouth, …) | ca. 1,5–2 GB Download | Beim Bauen des Docker-Images |
| WhisperX-Sprachmodell „large-v3" | ca. 3 GB | Beim ersten tatsächlichen Transkriptions-Lauf (nicht beim Bauen selbst) |
| Fertiges Docker-Image (ein Dienst; UI + Worker teilen sich dieselbe Basis) | ca. 3,8–5,2 GB auf der Platte, je nach Plattform | Nach dem Bauen |

**Empfohlener freier Speicherplatz insgesamt: mind. 15–20 GB** — das deckt Docker-Image,
Sprachmodell UND den temporären Bau-Zwischenspeicher ab (Docker legt beim Bauen selbst
vorübergehend mehr an, als am Ende übrig bleibt; mit `docker builder prune` danach wieder
freigebbar).

**Pro Plattform — empirisch gemessen, Stand 2026-08-16 (kompletter Neubau ohne
Docker-Cache):**

| Plattform | Muss Parselmouth kompiliert werden? | Gemessene Bauzeit (einmalig) |
|---|---|---|
| **Apple Silicon (M1–M5), primäres Zielsystem** | **Ja** — für `linux/arm64` gibt es kein fertiges Parselmouth-Paket, wird beim Bauen aus dem C/C++-Quellcode übersetzt (Praats eigener Code, das dauert den Großteil der Zeit) | **ca. 14 Minuten** (fast ausschließlich die Parselmouth-Kompilierung — alles andere lädt als fertiges CPU-Paket, keine unnötigen GPU-Pakete) |
| **Windows (Docker Desktop, WSL2-Backend)** | Nein — fertiges Paket vorhanden (dieselbe `linux/amd64`-Architektur wie unser Produktivserver) | Nicht separat gemessen, aber strukturell identisch zum Server-Rebuild — deutlich schneller als arm64, im niedrigen einstelligen Minutenbereich zu erwarten |
| **Intel-Mac (Docker Desktop)** | Nein — ebenfalls `linux/amd64`, wie Windows oben | Wie Windows oben |
| **Linux (Ubuntu o.ä.) via Docker** | Nein, sofern `amd64` (die meisten PCs/Server) | Wie Windows oben — das ist auch die auf unserem eigenen Produktivserver (Ubuntu, Intel N150) tatsächlich genutzte und geprüfte Variante |
| **Linux nativ, OHNE Docker** | Nein auf amd64 (analog zu oben) | Nicht separat getestet — dieses Projekt nutzt bisher ausschließlich Docker, auch auf dem eigenen Ubuntu-Server; ein nativer Lauf ohne Container sollte technisch funktionieren (dieselben `apt`/`pip`-Pakete), ist aber nicht verifiziert |

**Nachfolgende Starts sind schnell** (Sekunden statt Minuten) — Docker nutzt seinen
Layer-Cache, sofern sich der Code zwischen zwei Starts nicht ändert.

Alle Daten (Aufnahmen, abgeleitete Ergebnisse, das heruntergeladene Sprachmodell) liegen in
Docker-eigenen, persistenten Volumes — sie überstehen ein `docker compose down`/`up`, werden
aber NICHT automatisch irgendwohin gesichert. Wer direkten Dateizugriff auf einem eigenen
Host-Ordner statt eines Docker-Volumes möchte, kann `NEUROVOICE_HOST_DATA_DIR`/
`NEUROVOICE_HOST_DERIVED_DIR` per `.env`-Datei setzen (siehe Kommentare in
`dashboard/docker-compose.local.yml`).

### Verwendete Kernbibliotheken (Lizenzen)

NeuroVoice AI baut auf mehreren externen Open-Source-Projekten auf — hier die wichtigsten,
mit Lizenz laut deren eigenen Angaben (keine Rechtsberatung, nur Orientierung). Wegen der
GPL-3.0-Kernabhängigkeit Parselmouth steht dieses Repo selbst unter **GPL-3.0-or-later** (siehe
[LICENSE](LICENSE) und die Herleitung in [ROAD_TO_PUBLIC.md](ROAD_TO_PUBLIC.md)):

| Bibliothek | Zweck im Projekt | Lizenz |
|---|---|---|
| [Praat](https://www.fon.hum.uva.nl/praat/) / [Parselmouth](https://parselmouth.readthedocs.io/) | Akustische Kernanalyse (Jitter/Shimmer/HNR/Formanten/…) | GPL-3.0-or-later |
| [WhisperX](https://github.com/m-bain/whisperX) | Spracherkennung/Transkription mit Wort-Zeitstempeln | BSD-2-Clause |
| [PyTorch](https://pytorch.org/) | Numerisches Backend für WhisperX | BSD-3-Clause |
| [Streamlit](https://streamlit.io/) | Web-Oberfläche | Apache-2.0 |
| [pandas](https://pandas.pydata.org/) / [NumPy](https://numpy.org/) / [SciPy](https://scipy.org/) | Datenverarbeitung | BSD-3-Clause |
| [Matplotlib](https://matplotlib.org/) | Visualisierungen | Matplotlib-Lizenz (BSD-artig) |
| [soundfile](https://python-soundfile.readthedocs.io/) | Audio-Ein-/Ausgabe | BSD-3-Clause |
| [openpyxl](https://openpyxl.readthedocs.io/) | Excel-Report-Export | MIT |
| [fpdf2](https://py-pdf.github.io/fpdf2/) | PDF-Report-Export | LGPL-3.0-only |
| [ffmpeg](https://ffmpeg.org/) | Audio-Konvertierung | je nach Debian-Build LGPL/GPL-Mix, siehe Projektseite |

## Lizenz & Mitwirken

- **Lizenz**: [GNU GPL-3.0-or-later](LICENSE).
- **Sicherheit/Zugriffsmodell**: [SECURITY.md](SECURITY.md) — bitte vor dem eigenen Betrieb lesen.
- **Mitwirken**: [CONTRIBUTING.md](CONTRIBUTING.md).
- **Zitieren**: [CITATION.cff](CITATION.cff) (GitHub "Cite this repository").
- Dieses Projekt entstand mit Unterstützung von KI-Werkzeugen (Claude Code) bei Implementierung
  und Recherche — Inhalt, Testung und fachliche Bewertung verantwortet der Autor.
