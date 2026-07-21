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

- Dauer: 30 Sekunden Snippets
- Task-Typen: Freisprache, gehaltener Vokal ("aaa"), Lesetext
  (wichtig: unterschiedliche Feature-Familien sind nur bei bestimmten Task-Typen zuverlässig
  extrahierbar — siehe Literaturrecherche, Abschnitt "Einschränkungen")
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

- `docs/` — Konzept, Backlog, Literaturrecherche
- `raw-inbox/` — Syncthing-Zielordner (unveränderte .m4a-Dateien, noch nicht konvertiert/einsortiert)
- `data/raw/` — finale Ablage nach Konvertierung + Umbenennung
- `scripts/` — Konvertierungs-/Verifikations-Skripte
