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

## Kein formales Testsuite (Stand jetzt)

Es gibt bislang keine automatisierten Unit-/Integrationstests. Änderungen werden manuell und per
Ad-hoc-`streamlit.testing.v1.AppTest`-Skripten gegen alle Seiten regressionsgetestet (siehe
`docs/backlog.md`/`docs/bugtracker.md` für Beispiele des bisherigen Vorgehens). Ein Pull Request
sollte beschreiben, wie er getestet wurde — Beiträge, die eine echte, dauerhafte Testsuite
einführen, sind ausdrücklich willkommen.

## Lizenz

Beiträge fallen unter die GNU General Public License v3.0 (or later) dieses Projekts (siehe
[LICENSE](LICENSE)) — bedingt durch die GPL-3.0-Kernabhängigkeit `praat-parselmouth`.
