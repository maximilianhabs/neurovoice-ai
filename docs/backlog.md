# NeuroVoice AI — Backlog

Stand: 2026-07-21

## Grundprinzip

Alle Feature-Familien werden mittelfristig angegangen, aber **skaliert von einfach zu komplex** —
nicht alles auf einmal. Reihenfolge orientiert sich daran, wie gut ein Feature etabliert/validiert
ist und wie einfach es aus einem einzelnen Task-Typ zuverlässig extrahierbar ist.

## Phase 1 — Aufnahme-Pipeline (aktuell)

- [ ] Syncthing auf Beelink-Server installieren (Docker oder nativ)
- [ ] Syncthing auf iPhone einrichten, Pairing mit Server
- [ ] Ordnerstruktur anlegen: `raw-inbox/` (Syncthing-Ziel) getrennt von `data/raw/<patient_id>/...` (final)
- [ ] Konvertierungsskript: `.m4a` (ALAC) → `.wav`, verlustfrei (Container-Wechsel, kein Re-Encoding)
- [ ] Verifikationsskript: `ffprobe`-Check (Codec/Samplerate/Bittiefe) + Checksumme vor/nach Transfer
- [ ] Testdatenbank: 5-6 Aufnahmen (Freisprache, Vokal, Lesetext), sauber benannt & verifiziert
- [ ] Lesetext für "Lesetext"-Task-Typ auswählen/festlegen (phonetisch ausgewogen?)

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
- [ ] Voice Onset Time (VOT) bei Plosiven
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

## Offene fundamentale Fragen (aus Konzeptphase, zu klären bevor Phase 2 beginnt)

- Wie werden Referenzbereiche/Normwerte pro Sprecher:in (Geschlecht, Alter) gepflegt?
- Wird ein "pa-ta-ka"-Task für Diadochokinese ergänzt, oder bleibt es bei den 3 Task-Typen?
- Wie wird mit der Diskrepanz zwischen automatisierten Metriken und klinisch-perzeptivem Höreindruck
  umgegangen (Konfidenzangaben statt reiner Zahlen)?
