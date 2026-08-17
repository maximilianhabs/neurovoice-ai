# Road to Public — NeuroVoice AI

**Status: reines Konzept, NICHT umgesetzt.** Repo bleibt privat. Diese Datei beschreibt, was
zu tun ist, bevor `neurovoice-ai` von privat auf öffentlich geschaltet wird — analog zum bereits
abgeschlossenen Fahrplan bei [`anonymisator`](https://github.com/maximilianhabs/anonymisator)
und [`edf-analyzer`](https://github.com/maximilianhabs) (siehe dortige `ROAD_TO_PUBLIC.md`/
Public-Release-Notizen). Erstellt 2026-08-16, basierend auf der projektübergreifenden
8-Stufen-Checkliste dieses Nutzers, hier konkret gegen den NeuroVoice-AI-Code geprüft statt
pauschal übernommen.

Bestehende Commits werden **nie umgeschrieben, um Inhalte zu verfälschen** — nur ergänzt.
Historien-Bereinigung (falls nötig) wird als eigener, expliziter Schritt behandelt, nicht
nebenbei.

## Stufe 1 — Shitstorm-Risiko eliminieren (VOR allem anderen)

### 🔴 Konkrete Funde (2026-08-16, gegen den echten Code/Docs geprüft)

1. **Reale Tailscale-IP + Hostname in `docs/backlog.md` und `docs/bugtracker.md`**
   (`<TAILSCALE-IP>`, `<TAILSCALE-HOSTNAME>`) sowie die Hetzner-IP `<ANDERER-SERVER-IP>` an
   einer Stelle. Beide Dateien sind Teil des Repos und würden mit veröffentlicht. Analog zum
   bereits behobenen Fund beim EDF-Analyzer (dort: Ops-Abschnitt im README) — hier aber tiefer
   in der laufenden Projekt-Doku verteilt (Backlog/Bugtracker sind hier viel umfangreicher
   als bei den Schwesterprojekten, dementsprechend mehr Fundstellen). Auch
   `dashboard/docker-compose.yml` bindet die Tailscale-IP direkt (`<TAILSCALE-IP>:8501:8501`).
   **Fix**: entweder durch Platzhalter ersetzen (Doku-Referenzen) bzw. auf eine Umgebungsvariable
   umstellen (docker-compose.yml), oder bewusst als „kein Sicherheitsrisiko, nur interne
   Referenz“ stehen lassen (wie beim EDF-Analyzer für den alten Ops-Abschnitt entschieden) —
   **Nutzer-Entscheidung nötig**, wie bei den Schwesterprojekten.
2. **Kein Passwort-/Auth-Fund** (anders als beim EDF-Analyzer) — NeuroVoice AI hat aktuell
   **gar keinen Auth-Layer** (kein `core/auth.py`-Äquivalent). Das ist für die
   Repo-Veröffentlichung selbst unproblematisch (kein Secret im Code), aber relevant für
   `SECURITY.md`: muss explizit festhalten, dass der Tailscale-Zugriff die einzige
   Zugriffskontrolle ist, keine Mehrbenutzer-Authentifizierung/Rollen/Zugriffsprotokoll
   existiert — wichtig, weil die App seit P10 echte Proband:innen-IDs + Alter sammelt.
3. **Keine Kliniknamen/PHI im Code-Grep gefunden** — sauber, „Mainkofen“/„BKH“ kommen nicht vor.
4. **Volle Commit-Historie geprüft** (`git log --all --diff-filter=A --name-only`, 83 Commits):
   **keine** `.wav`/`.m4a`/Audio-Dateien jemals committet, **keine**
   `derived/_sessions`/`_subjects`/`_uploads`-Dateien jemals committet — die `.gitignore`
   (Audiodaten/`raw-inbox`/`data/raw` ausgeschlossen) hat von Anfang an funktioniert. Das ist
   ein echter Unterschied zu den Schwesterprojekten, wo Nachbesserungen nötig waren — hier
   bereits sauber, **keine Historien-Bereinigung (`git filter-repo`) nötig**, solange das so
   bleibt.
5. **Keine medizinischen Überversprechen im README gefunden** — „Kein Diagnose-KI-Ersatz“ steht
   bereits im ersten Absatz. Muss bei der README-Überarbeitung (Stufe 2) erhalten bleiben und
   auf den *aktuellen* Funktionsumfang (Glossar/Evidenz-Einordnung, P11/P12) ausgeweitet werden
   — genau die Art Formulierung, die ein Gutachter (Stufe 8) positiv bewerten würde.

## Stufe 2 — Erster Eindruck (README) — GRÖSSTER EINZELFUND

**`README.md` ist seit dem 21.07. (Tag 1 des Projekts, Commit-Nr. 1 von inzwischen 83) nicht
mehr aktualisiert worden.** Es beschreibt einen Stand, der mit der heutigen App praktisch nichts
mehr zu tun hat:
- Nennt nur 3 Task-Typen (Freisprache/Vokal/Lesetext) — die App hat heute 4 Guide-Module
  (Vokalisation/Vorlesen/Spontansprache/Diadochokinese) mit eigenem Take-Management.
- Beschreibt eine `data/raw/<patient_id>/...`-Ordnerstruktur, die durch das persistente
  Sitzungs-/Proband:innen-Schema (P4/P10, `derived/_sessions/`, `derived/_subjects/`) längst
  abgelöst wurde.
- Erwähnt weder das Streamlit-Guide-Dashboard, das Laborwert-Glossar (P11), die
  Referenzwerte-Recherche (P12), noch die Kachel-Oberfläche.
- Status-Zeile sagt noch „🟡 Konzeptphase“, obwohl die App längst ein funktionierendes
  Mehr-Modul-Analysewerkzeug mit ~90 Backlog-Punkten Historie ist.

**Das ist DER Punkt, der vor jeder Veröffentlichung zwingend gemacht werden muss** — ein
externer Leser, der das aktuelle README liest und dann die App startet, würde sofort merken,
dass die Doku nicht zum Code passt (Stufe 8: „was würde ein Gutachter kritisieren“ — genau das).
Braucht einen kompletten Neuschrieb, kein Update in Stellen: was macht es (2 Sätze), warum
existiert es, wie starte ich es (Docker-Compose-Kurzanleitung), aktueller Modul-Überblick,
Datenschutz-Prinzip, Stand/Status ehrlich benannt.

## Stufe 3 — Wissenschaftliche Ehrlichkeit

Strukturell bereits sehr gut aufgestellt, besser als bei den Schwesterprojekten zu Beginn:
- P11 (Kompakte Übersicht + Evidenz-Glossar) trennt bereits explizit „gut etabliert“ / „in der
  Forschung diskutiert“ / „eigene Heuristik“ / „deskriptiv“ je Parameter — das ist praktisch
  bereits die Art Limitations-Transparenz, die der EDF-Analyzer erst nachträglich mit der
  `methods.py`-Registry eingeführt hat.
- P12 dokumentiert explizit, WO recherchiert wurde und WO bewusst keine Schwelle erfunden wurde.
- `docs/literatur_review.md` mit vollständiger Quellenliste existiert bereits.
- **Zu prüfen vor Public**: `docs/literatur_review.md`s Abschnitt „Perspektivische
  Zusatzparameter“ (Geschlecht/Alter/Nervosität/Lügenerkennung) — dort steht bereits die
  Einordnung „wissenschaftlich widerlegt“ für Lügenerkennung explizit drin, das ist GUT so und
  sollte genau so bestehen bleiben, nicht abgeschwächt werden.

## Stufe 4 — Gepflegt

- Kein Versions-/Status-Badge im README (sollte ergänzt werden).
- `docs/backlog.md` (>1000 Zeilen) und `docs/bugtracker.md` sind ungewöhnlich detailliert und
  gut geführt für ein Solo-Projekt — das ist eher ein STÄRKE-Argument für Stufe 8
  (Gutachterfrage: zeigt systematisches Vorgehen), sollte im README als Verweis erwähnt bleiben,
  aber nicht 1:1 verlinkt werden ohne Kontext (>1000 Zeilen Rohtext ohne Einordnung wirkt für
  Externe eher unübersichtlich als vertrauenswürdig — evtl. eine kurze „Projektstand“-
  Zusammenfassung im README, die auf die Details im Backlog verweist statt sie zu ersetzen).

## Stufe 5 — Lizenz bewusst wählen — **HIER ANDERS ALS BEI DEN SCHWESTERPROJEKTEN**

Anonymisator und EDF-Analyzer haben sich beide für **Apache-2.0** entschieden. Bei NeuroVoice AI
ist die Lage **nicht identisch**, weil eine harte Abhängigkeit anders lizenziert ist:

- **`praat-parselmouth` ist GPL-3.0-or-later lizenziert** (bindet Praats C/C++-Code direkt ein,
  kein Wrapper um eine separate Programminstanz). Anders als beim EDF-Analyzer-Fund
  `py-ecg-detectors` (dort GPL, aber hinter einem `try/except`-Fallback, also OPTIONAL) ist
  Parselmouth bei NeuroVoice AI eine **zwingende, überall genutzte Kernabhängigkeit**
  (`core/audio.py` praktisch komplett darauf aufgebaut).
- **Rechtliche Konsequenz (keine Rechtsberatung, nur Einordnung für die Entscheidung)**: eine
  GPL-3.0-Abhängigkeit, die direkt importiert/gelinkt statt nur als externer Prozess
  aufgerufen wird, zieht bei Weitergabe des KOMBINIERTEN Werks in aller Regel GPL-3.0-kompatible
  Bedingungen nach sich — ein eigenes Apache-2.0-Label für den restlichen Code wäre zwar
  formal möglich, würde aber die praktische Copyleft-Wirkung von Parselmouth nicht aufheben.
  **Pragmatischer Vorschlag: NeuroVoice AI selbst unter GPL-3.0 lizenzieren** (statt Apache-2.0
  wie die Geschwister), um Lizenz und tatsächliche Abhängigkeitslage konsistent zu halten,
  statt eine Lizenz zu wählen, die die Abhängigkeit stillschweigend übergeht.
- **Alternative, falls Apache-2.0 gewünscht bleibt**: Parselmouth-Abhängigkeit isolieren/optional
  machen (wie beim EDF-Analyzer mit `py-ecg-detectors`) — bei NeuroVoice AI aber deutlich
  aufwendiger, da Parselmouth kein optionales Add-on, sondern die zentrale Analyse-Engine ist.
  Realistisch nur sinnvoll, wenn ein alternativer, permissiv lizenzierter Akustik-Analyse-Stack
  das komplett ersetzen würde — kein kleiner Umbau.
- `whisperx` selbst ist BSD-2-Clause (unproblematisch), hat aber eigene Unterabhängigkeiten
  (u.a. `pyannote-audio`, `faster-whisper`, `torch`) — vor Public-Release einmal gezielt prüfen,
  ob eine davon zusätzliche Lizenz-/Nutzungsbedingungen hat (z.B. Modell-Lizenzen bei
  Pyannote-Checkpoints), analog zum EDF-Analyzer-Vorgehen mit `tools/check_licenses.py`.
- **Entscheidung getroffen (2026-08-17): GPL-3.0-or-later.** `LICENSE` liegt jetzt im Repo-Root.

### ✅ Lizenzaudit WhisperX-Unterabhängigkeiten (durchgeführt 2026-08-17, direkt im laufenden
Server-Container per `pip show`/`importlib.metadata` geprüft, nicht nur aus Dokumentation
übernommen)

| Paket | Lizenz | Anmerkung |
|---|---|---|
| whisperx | BSD-2-Clause | |
| faster-whisper | MIT | |
| ctranslate2 | MIT | ASR-Backend |
| torch / torchaudio | BSD-3-Clause | |
| pyannote-audio | MIT | **installiert, aber im Code NICHT genutzt** (`core/transcription.py` ruft `whisperx.load_model()`+`whisperx.align()` auf, nie Diarization/`DiarizationPipeline`, kein `hf_token`) — die potenziell restriktiveren, "gated" Pyannote-Modell-Checkpoints (separates Lizenzmodell auf HuggingFace) kommen dadurch praktisch nie zum Einsatz. |
| numpy, pandas | BSD-3-Clause | |
| nltk | Apache-2.0 | |

**Ergebnis: keine zusätzliche Lizenzauflage über die Code-Abhängigkeiten hinaus gefunden.** Die
Forced-Alignment-Modellgewichte (wav2vec2, sprachabhängig, WhisperX-Standardauswahl) werden zur
Laufzeit von HuggingFace geladen (Docker-Volume `whisperx-models`) — **nie im Git-Repo committet**,
daher keine Lizenzvererbung ins Repo selbst, nur eine Laufzeit-/Deployment-Überlegung (bereits in
`SECURITY.md` in Bezug auf Proband:innendaten, nicht Modell-Lizenzen, adressiert — Modell-Lizenz
ist ein rein operatives Thema für wer selbst deployed, kein Repo-Blocker).

## Stufe 6 — KI-Nutzung knapp offenlegen

Noch nicht vorhanden, ein Satz im README reicht (analog zu den Schwesterprojekten) — wer den
Inhalt/die fachliche Bewertung verantwortet, ist der Autor, nicht die KI.

## Stufe 7 — Fremde Inhalte

Keine Screenshots/Bilder/Icons im Repo gefunden (rein Text-/Code-Repo bisher) — aktuell sauber.
Falls für das README Screenshots ergänzt werden (empfehlenswert für Stufe 2/8, siehe
Anonymisator-Vorbild), müssen das selbst aufgenommene Screenshots der eigenen App sein, keine
fremden Abbildungen.

## Stufe 8 — Gutachterfrage

Was ein:e Reviewer:in (Neurologie/Informatik) an der aktuellen Doku-Lage kritisieren würde,
falls JETZT veröffentlicht:
- Stale README, das nicht zur App passt (siehe Stufe 2) — größter Einzelpunkt.
- Fehlende LICENSE/CITATION.cff/SECURITY.md (siehe unten) — alle drei fehlen komplett, anders
  als bei beiden Schwesterprojekten zu deren jeweiligem Public-Zeitpunkt.
- Reale interne Infrastruktur-Referenzen in der Doku (Stufe 1, Punkt 1).
- Positiv (kein Kritikpunkt, sondern Pluspunkt): die P11/P12-Transparenz-Arbeit (Evidenz-
  Einordnung + Quellenangaben je Parameter) ist bereits ungewöhnlich gründlich für ein
  Solo-Projekt in diesem Stadium.

## Fehlende Standard-Artefakte (alle 3 fehlen komplett, Stand 2026-08-16)

- [ ] `LICENSE` — Entscheidung siehe Stufe 5 (GPL-3.0 vs. Apache-2.0+Parselmouth-Isolierung).
- [ ] `CITATION.cff` — noch nie angelegt (anders als bei den Schwesterprojekten, die es schon
      vor ihrer Public-Phase hatten).
- [ ] `SECURITY.md` — inkl. explizitem Hinweis „kein Auth-Layer, Tailscale ist die einzige
      Zugriffskontrolle“ (siehe Stufe 1, Punkt 2) und „keine Mehrbenutzer-Trennung“.
- [ ] `CONTRIBUTING.md` — optional, aber beim Anonymisator als hilfreich empfunden (klare
      Vor-PR-Checkliste, „nie echte Proband:innen-Daten einreichen“-Regel wäre hier das
      NeuroVoice-AI-Äquivalent zur Anonymisator-Regel „nie echte Dokumente einreichen“).

## Vorgeschlagener Phasenplan (analog zu den Schwesterprojekten, noch NICHT begonnen)

- **Phase 1 (klein, risikoarm)**: `SECURITY.md` (Auth-Hinweis), `CITATION.cff`,
  `CONTRIBUTING.md` mit Proband:innen-Daten-Regel — keine Code-Änderung nötig.
- **Phase 2 (zwingend vor Public)**: README-Neuschrieb (Stufe 2), Lizenz-Entscheidung mit
  Nutzer treffen + `LICENSE` anlegen, reale IPs/Hostnamen in `docs/backlog.md`/
  `docs/bugtracker.md`/`docker-compose.yml` bereinigen ODER bewusst als unkritisch akzeptieren
  (Nutzer-Entscheidung wie bei den Schwesterprojekten), Lizenzaudit der WhisperX-Unter-
  abhängigkeiten.
- **Phase 3 (größer, eigene Rücksprache nötig)**: Screenshots/kurzes Demo-GIF fürs README
  (analog Anonymisator-Vorbild), evtl. eine bewusst synthetische/anonymisierte Beispiel-Session
  zum Ausprobieren ohne eigene Aufnahme (Idee, noch nicht konkretisiert — vergleichbar mit dem
  EDF-Anonymizer-Begleitprojekt-Gedanken, hier aber nicht zwingend ein eigenes Repo nötig).
- **Phase 4**: Repo bleibt privat, bis Phase 1+2 abgeschlossen sind. Phase 3 ist wünschenswert,
  aber keine harte Voraussetzung (wie beim Anonymisator, wo der Goldkorpus am Ende bewusst
  kleiner belassen wurde als ursprünglich geplant — reine Nutzer-Abwägung, kein Muss).

## Nächster konkreter Schritt (bei Freigabe)

Noch NICHTS umgesetzt. Vorschlag für den ersten Schritt, falls freigegeben: Phase 1
(SECURITY.md/CITATION.cff/CONTRIBUTING.md) — unabhängig vom Public-Zeitplan sinnvoll, weil
risikofrei und schnell erledigt, wie bei den Schwesterprojekten als „macht man ohnehin“
eingestuft.
