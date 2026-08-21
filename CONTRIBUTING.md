# Mitwirken

Danke für das Interesse an NeuroVoice AI. Dieses Dokument beschreibt, wie ein Beitrag zustande
kommt — von der Fehlermeldung bis zum Pull Request.

## Die eine Regel, die vor allen anderen steht

**Niemals eine echte Aufnahme, ein echtes Transkript oder echte Proband:innen-Daten (ID,
Alter, Sitzungs-Snapshot) einreichen — auch nicht in einem Issue, auch nicht als Screenshot,
auch nicht ausschnittweise.**

Dieses Projekt sammelt bewusst nur eine pseudonyme ID + Alter, keine Namen (siehe
`core/subject_store.py`, `SECURITY.md`) — trotzdem ist eine Sprachaufnahme selbst potenziell
identifizierend. Ein Issue, das zur Veranschaulichung eine echte Aufnahme/ein echtes Transkript
anhängt, unterläuft genau das Datenschutz-Prinzip, für das die App gebaut ist, und bliebe für
immer in der GitHub-Historie stehen, selbst wenn es später gelöscht wird.

Zum Reproduzieren eines Fehlers reicht in aller Regel:

- eine **synthetische** Testaufnahme (z. B. via `say`/einer beliebigen TTS-Stimme erzeugt,
  siehe `docs/backlog.md`/`views/testdaten.py` für den bisherigen Umgang mit synthetischen
  Referenzaufnahmen)
- oder eine reine Beschreibung: welcher Wert/welche Kachel/welches Diagramm zeigt was Falsches,
  bei welcher Eingabelänge/-art.

## Einen Fehler melden

Über die [Issues](https://github.com/maximilianhabs/neurovoice-ai/issues) des Projekts. Am
hilfreichsten sind:

- welches Modul (Vokalisation/Vorlesen/Spontansprache/Diadochokinese/Gesamtbericht)
- welcher Parameter/welche Kachel betroffen ist
- erwarteter vs. tatsächlicher Wert (oder: was am Diagramm falsch aussieht)
- ob es mit einer synthetischen Testaufnahme reproduzierbar ist

Eine **Sicherheitslücke** gehört nicht in ein öffentliches Issue, sondern in eine private
Meldung nach [SECURITY.md](SECURITY.md).

## Bevor ein neuer Parameter/eine neue Referenzwert-Behauptung eingereicht wird

Jeder Parameter in `core/interpretation.py::PARAMETER_INFO` trägt ein `evidence`-Tag ("gut
etabliert" / "in der Forschung diskutiert" / "eigene Heuristik" / "deskriptiv") und, wo
vorhanden, eine `literature`-Quellenangabe (siehe `docs/literatur_review.md`). Ein neuer
Referenzwert/Cutoff braucht eine zitierfähige Quelle oder muss ehrlich als "eigene Heuristik"
gekennzeichnet werden — keine erfundenen Normbereiche. Wo die Literatur uneinig ist (z. B. MPT,
siehe `PARAMETER_INFO`), gehört das als solches dargestellt, nicht künstlich vereinheitlicht.

## Wenn sich eine Berechnung in `core/audio.py` ändert: Version erhöhen

Jede gespeicherte Aufnahme trägt die Analyse-Version mit, unter der ihre Werte berechnet wurden
(`core/versioning.py::FEATURE_SCHEMA_VERSION`, gestempelt in `core/module_state.py::add_take()`,
sichtbar in Gesamtbericht und Export). Das ist die Grundlage dafür, dass ein Verlaufsvergleich
über Monate hinweg belastbar bleibt: ohne sie ließe sich später nicht mehr unterscheiden, ob ein
veränderter Jitter-Wert an der Stimme oder an einer geänderten Formel liegt.

**Ändert ein Pull Request eine Berechnung so, dass sich bei gleicher Audiodatei ein anderer Wert
ergibt, muss `FEATURE_SCHEMA_VERSION` erhöht und die Historie im Modulkopf ergänzt werden.**
Reines Refactoring ohne Wertänderung bleibt außen vor — eine Version, die sich bei jeder
Codeänderung dreht, sagt nichts mehr aus.

## Bevor ein Vorschlag zum wiederholten Mal kommt

`docs/backlog.md` ist die laufend geführte Historie aller bereits geprüften/entschiedenen
Punkte (inkl. explizit zurückgestellter Ideen mit Begründung, siehe z. B. den Abschnitt zu
externem wissenschaftlichem Audit). Dort zuerst nachsehen, bevor ein bereits verhandelter Punkt
neu aufgemacht wird — insbesondere alles rund um automatische Diagnose/ML-Scores, siehe
"Projektprinzip" weiter unten.

## Projektprinzip: keine Diagnose, kein unvalidierter Score

NeuroVoice AI liefert deskriptive, literaturverankerte Sprachbiomarker — **keine** Diagnose,
keinen Krankheits-Score, keine automatische Klassifikation "krank/gesund". Pull Requests, die
das einführen (z. B. ein ML-Modell, das eine Diagnosewahrscheinlichkeit ausgibt), werden nicht
angenommen, solange keine echte, extern validierte Patient:innen-Kohorte samt entsprechender
klinischer Validierungsstudie dahintersteht — siehe `docs/backlog.md`.

## Lokal einrichten

Siehe [README.md](README.md) — Kurzfassung: `docker compose -f dashboard/docker-compose.local.yml up --build`.

## Tests

```bash
bash tools/preflight.sh
```

Das ist derselbe Lauf wie in der CI (`.github/workflows/test.yml`) und dauert wenige Sekunden.
**Vor jedem Push ausführen.** Kommt eine Prüfung in der Workflow-Datei dazu, gehört sie auch
in `tools/preflight.sh` — sonst öffnet sich genau die Lücke wieder, die das Skript schließt.

Die Suite unter `tests/` prüft gegen **konstruierte Wahrheit**, nicht gegen Plausibilität:

- `signale.py` erzeugt synthetische Signale, deren richtige Antwort aus ihrer Konstruktion
  folgt — eine Pulsfolge mit alternierender Periode T·(1±j) hat per Definition
  `jitter_local = 2j`, Ton plus Rauschen bekannter Leistung hat den konstruierten HNR.
- `test_analytic_groundtruth.py` prüft F0, Jitter, Shimmer, HNR, Formanten, VSA/FCR und
  Übersteuerung dagegen.
- `test_bekannte_schwaechen.py` nagelt die offenen Messwert-Mängel als `xfail(strict=True)`
  fest. Wird einer behoben, wird der Lauf rot („unexpectedly passing") und erinnert daran,
  Markierung und Bugtracker-Eintrag zu schließen — ein behobener Fehler kann so nicht
  unbemerkt bleiben.
- `test_parameter_registry.py` prüft `PARAMETER_INFO` und die drei Anzeigepfade
  (Kachel/Tabelle/Glossar) ohne Audio und ohne Streamlit.

**Was hier bewusst NICHT passiert**: eine Formel neben der Implementierung nachbauen und beide
vergleichen. Das zeigt nur, dass zwei Rechnungen übereinstimmen. Geprüft wird gegen Werte, die
aus der Theorie oder aus der Konstruktion des Eingangssignals folgen.

Ein neuer Kennwert in `core/audio.py` sollte einen solchen Test mitbringen. Die Oberfläche
selbst ist weiterhin nicht automatisiert abgedeckt; dafür gilt weiter der Ad-hoc-`AppTest`-Weg,
und ein Pull Request sollte beschreiben, wie er getestet wurde.

## Lizenz

Beiträge fallen unter die GNU General Public License v3.0 (or later) dieses Projekts (siehe
[LICENSE](LICENSE)) — bedingt durch die GPL-3.0-Kernabhängigkeit `praat-parselmouth`.
