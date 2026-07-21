# NeuroVoice AI — Backlog

Stand: 2026-07-21

## Grundprinzip

Alle Feature-Familien werden mittelfristig angegangen, aber **skaliert von einfach zu komplex** —
nicht alles auf einmal. Reihenfolge orientiert sich daran, wie gut ein Feature etabliert/validiert
ist und wie einfach es aus einem einzelnen Task-Typ zuverlässig extrahierbar ist.

## Phase 1 — Aufnahme-Pipeline (aktuell)

- [x] Syncthing auf Beelink-Server installiert (Docker, Tailscale-only, Discovery/Relay deaktiviert) — siehe homeserver-Repo LOG.md 2026-07-21
- [x] ffmpeg auf Server installiert
- [ ] Syncthing auf iPhone einrichten, Pairing mit Server (Device-ID des Servers: `2NZZMYW-PJG4XLE-DILEQIU-65W4Z5T-DAY6YST-ZUSDIMN-6OMPFSR-T5WZBAV`)
- [x] Ordnerstruktur angelegt: `~/neurovoice-data/raw-inbox` (Syncthing-Ziel) getrennt von `~/neurovoice-data/raw/<patient_id>/...` (final) — auf dem Server, nicht im Git-Repo
- [x] Konvertierungsskript: `.m4a` (ALAC) → `.wav`, verlustfrei (Dekodierung, kein Re-Encoding) — `scripts/convert_and_verify.sh`, deployed auf Server
- [x] Verifikationsskript: `ffprobe`-Check (Codec/Samplerate/Bittiefe) + Checksumme vor/nach Transfer — im selben Skript enthalten
- [ ] Testdatenbank: 5-6 Aufnahmen (Freisprache, Vokal, Lesetext), sauber benannt & verifiziert
- [x] Lesetext festgelegt: "Nordwind und Sonne" (Standard-IPA-Referenztext, siehe docs/lesetext_nordwind_sonne.md)

## Phase 2 — Feature-Extraktion (nach stabiler Aufnahme-Pipeline)

Tool-Basis: **Parselmouth** (Python-Wrapper um Praat, klinischer Goldstandard).

### Stufe 1 — Phonation, gehaltener Vokal (am einfachsten, am besten etabliert)
- [ ] F0 (Mittelwert, SD)
- [ ] Jitter
- [ ] Shimmer
- [ ] HNR/NHR
- [ ] Erste Referenzwerte/Normalisierung nach Geschlecht recherchieren & hinterlegen

### Stufe 2 — Spektralanalyse/Klangfarbe
- [ ] Formanten F1-F3 (gehaltener Vokal zunächst, später Vokale in Fließsprache)
- [ ] MFCCs
- [ ] Vowel Space Area / Formant-Ratios (mit Vorsicht — Literatur uneinheitlich, siehe Review)

### Stufe 3 — Zeitliche Struktur/Sprechfluss (Freisprache + Lesetext)
- [ ] Sprechrate (Net Speech Rate)
- [ ] Pausenerkennung + Pausenmuster (Anzahl, Dauer)
- [ ] Diadochokinetische Rate (separater Task "pa-ta-ka" nötig — noch nicht in Aufnahme-Konzept enthalten)

### Stufe 4 — Prosodie
- [ ] Monopitch-Maß (SD F0 über Äußerung, Freisprache/Lesetext)
- [ ] Monoloudness (SD Intensität)
- [ ] Rhythmus/PVI

### Stufe 5 — Artikulation (komplexer, ggf. spätere Iteration)
- [ ] **Verschlussdauer (Closure Duration) bei Plosiven statt VOT** — im Deutschen wird Fortis/Lenis
      (p/b, t/d, k/g) primär über Verschlussdauer signalisiert, nicht über Aspiration/VOT wie im
      Englischen (fortis-Verschluss ca. 4x länger als lenis). VOT bleibt ein Zusatzmaß, ist aber nicht
      das primäre deutsche Unterscheidungsmerkmal.
- [ ] Ort-der-Artikulation-Differenzierung (velar vs. alveolar, spektrale Bursts)

### Stufe 6 — CPP als robusteres Alternativmaß zu Jitter/Shimmer bei Fließsprache
- [ ] Cepstral Peak Prominence für Freisprache/Lesetext (da Jitter/Shimmer dort unzuverlässig sind)

## Später (explizit nicht Teil des aktuellen Auftrags)

- Whisper-Transkription
- OpenSMILE/eGeMAPS als Ergänzung/Vergleich zu Parselmouth
- ML-Klassifikation / longitudinale Trend-Modelle
- Lokales LLM für Verlaufsberichte
- Web-App/UI für geführte Angehörigen-Nutzung
- Externes USB-Mikro als Aufnahmequelle
- Echte Pseudonymisierungs-/Zuordnungstabelle (sobald echte Testpersonen dazukommen)

## Sprache: Deutsch (Muttersprache) — Konsequenzen für die Pipeline

- **Lesetext**: "Nordwind und Sonne" (docs/lesetext_nordwind_sonne.md) — Standard-IPA-Referenztext,
  phonetisch repräsentativ, ermöglicht später auch Vergleich mit anderssprachigen Aufnahmen/Literatur,
  da der Text in nahezu jeder Sprache in einer Standardversion existiert.
- **Referenz-/Normwerte**: Saarbrücken Voice Database (SVD) — 2225 deutsche Sprecher:innen (869 gesund,
  1356 pathologisch), gehaltene Vokale /a/,/i/,/u/ in normal/hoch/tief/steigend-fallend. Als deutsche
  Normwert-Basis für Stufe-1-Phonation-Features nutzbar, statt eigene Normwerte mühsam zu erheben.
- **Fortis/Lenis im Deutschen ≠ Englisch**: siehe Stufe 5 oben — Verschlussdauer statt VOT/Aspiration
  ist das primäre Unterscheidungsmerkmal deutscher Plosive.

## Offene fundamentale Fragen (aus Konzeptphase, zu klären bevor Phase 2 beginnt)

- Wie werden Referenzbereiche/Normwerte pro Sprecher:in (Geschlecht, Alter) gepflegt?
- Wird ein "pa-ta-ka"-Task für Diadochokinese ergänzt, oder bleibt es bei den 3 Task-Typen?
- Wie wird mit der Diskrepanz zwischen automatisierten Metriken und klinisch-perzeptivem Höreindruck
  umgegangen (Konfidenzangaben statt reiner Zahlen)?
