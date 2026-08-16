# Konzept: Visualisierungen — Bestandsaufnahme + kreative Ideen

Status: **Konzept, NICHT umgesetzt** (2026-08-16, Nutzer-Auftrag: "guck dir alle Parameter an,
die während eines Tests erfasst werden, überleg dir kreative, teils kombinierte
Darstellungen, denk auch an etablierte wissenschaftliche Sprach-Visualisierungen, noch nichts
umsetzen"). Verwandte, bereits bestehende Backlog-Punkte: V1 (Histogramm Wortdauern), V2
(Platzhalter für weitere Ideen), J2 (Radar-Diagramm bei Vorlesen "nicht schön").

## 1. Was wird aktuell überhaupt gemessen? (vollständige Bestandsaufnahme)

Ein kompletter Testdurchlauf (Vokalisation → Vorlesen → Spontansprache → DDK) erfasst **40
verschiedene Kennwerte** (`core/interpretation.py::PARAMETER_INFO`). Nach Modul sortiert:

**Vokalisation** (gehaltene Vokale /a/, /i/, /u/):
- Stimmqualität: Jitter (local/RAP/PPQ5), Shimmer (local/APQ11), HNR, CPPS, Voice Breaks
  (Anzahl + Anteil)
- Tonhöhe: F0-Mittelwert, F0-Streuung (Monopitch), F0-Tremor-Frequenz
- Atemreserve: Maximum Phonation Time
- Formanten: F1/F2/F3-Mittelwerte (Rohwerte)
- Nach allen 3 Vokalen: Vokalraum-Fläche (VSA)

**Vorlesen / Spontansprache** (strukturell identisches Kennwert-Set):
- Artikulation: Artikulationsschärfe (Burst-basiert)
- Formant-Dynamik: F1-/F2-Streuung (zeitaufgelöster IQR)
- Prosodie: Monoloudness, Rhythmus (nPVI), Intonationskontur (Phrasenzahl)
- CPP (Fließsprache-Variante)
- Nach Transkription: Sprechrate (netto + Artikulation), Flüssigkeits-Score, Ø Wortdauer,
  Pausen (Anzahl, Ø-/Max-/Mikro-/Makro-Dauer), Lexikalische Diversität (TTR, MTLD),
  Erkennungs-Konfidenz

**DDK** ("pa-ta-ka"):
- DDK-Rate, Ø Zyklus-Intervall, DDK-Regelmäßigkeit (CV)

**Bereits vorhandene Visualisierungen** (`core/plots.py`): Wellenform, Spektrogramm (mit
F0-Overlay), Intensitätskurve, Radar-Profil (nur Vorlesen, 4 Achsen), Gauge/Tacho (weitgehend
durch KPI-Kacheln abgelöst). Alle vier Module zeigen aktuell dieselben drei Basis-Plots
(Wellenform/Intensität/Spektrogramm) — **keine modul-spezifische Zusatz-Visualisierung**,
obwohl DDK (Rhythmus/Regelmäßigkeit) und Vokalisation (Formanten/Vokalraum) inhaltlich sehr
unterschiedliche Dinge zeigen könnten.

## 2. Gruppierungsprinzipien (wie in der Anfrage gewünscht)

Drei Achsen, um Parameter sinnvoll zusammenzufassen statt isoliert als Einzelkachel zu zeigen:

**A) Gleiche Einheit/Größenordnung** — z.B. alle Perturbationsmaße in % (Jitter local/RAP/
PPQ5, Shimmer local/APQ11) lassen sich in EINER gemeinsamen Grafik nebeneinander zeigen, statt
5 separate Kacheln zu lesen.

**B) Gleiches zugrunde liegendes Konstrukt, verschiedene Berechnungsweise** — z.B.
Netto-Sprechrate vs. Artikulationsrate (beide WPM, Unterschied = reine Pausenzeit); TTR vs.
MTLD (beide lexikalische Diversität, MTLD textlängen-robuster); DDK-Rate vs. Ø
Zyklus-Intervall (exakter Kehrwert).

**C) Logisch verknüpft, aber unterschiedliche Einheit** — z.B. alle Pausen-Kennwerte (Anzahl,
Ø-/Max-/Mikro-/Makro-Dauer) beschreiben gemeinsam EIN Phänomen (das Pausenmuster über die
Aufnahme) und ergeben als Timeline viel mehr Sinn als 6 einzelne Zahlen.

## 3. Konkrete neue Visualisierungs-Ideen

### 3.1 Vokalraum-Plot (F1/F2-Diagramm) — größte Lücke, klassischste Darstellung überhaupt

Die **Standard-Darstellung der Phonetik** für Vokale ist ein F2(x)-gegen-F1(y)-Streudiagramm,
BEIDE Achsen umgekehrt (hohe Werte links/unten) — ergibt die vertraute "Vokaltrapez"-Form, die
in jedem Phonetik-Lehrbuch auftaucht. Wir BERECHNEN bereits F1/F2 für alle 3 Eckvokale UND die
VSA-Dreiecksfläche daraus — zeigen visuell aber nur die reinen Zahlen. Ein Plot mit den 3
Vokal-Punkten + dem Dreieck dazwischen würde die Vokalraum-Fläche sofort anschaulich machen
(kleines/zentralisiertes Dreieck = sichtbar reduzierter Artikulationsraum) statt einer
abstrakten Hz²-Zahl. Das ist wahrscheinlich die Visualisierung mit dem größten Verhältnis von
Wirkung zu Aufwand — bereits alle nötigen Rohdaten vorhanden (nur f1/f2_mean_hz je Vokal aus
den 3 Vokalisation-Takes zusammenführen).

### 3.2 Pausen-Timeline ("Sprechfluss-Zeitstrahl") statt 6 Einzelkacheln

Aktuell: Pausen (Anzahl), Ø-/Max-/Mikro-/Makro-Pausendauer als getrennte Zahlen. Eine
horizontale Zeitleiste (Balken = Sprechsegmente, Lücken = Pausen, Farbe/Höhe nach
Mikro-/Makropause unterschieden) macht auf einen Blick sichtbar: WO im Text die Pausen liegen,
ob sie gleichmäßig verteilt oder geklumpt sind, und ob eine einzelne Ausreißer-Pause den
Mittelwert verzerrt — Information, die reine Kennzahlen nicht transportieren. Technisch machbar
aus den vorhandenen Wort-Zeitstempeln (bereits da für die Pausenerkennung selbst).

### 3.3 DDK-Rhythmus-Spur — macht "Regelmäßigkeit" tatsächlich sichtbar

Aktuell nur eine einzelne CV-Zahl für "wie gleichmäßig ist die Silbenfolge". Eine Reihe von
Tick-Marken (erkannte Silben-Onsets) entlang einer Zeitachse, evtl. mit den Zyklus-Intervallen
als kleine Balken darunter, macht "stolpernde"/unregelmäßige Silbenfolgen (Verdachtsmoment für
ataktische Dysarthrie) SOFORT optisch erkennbar — genau die Textur, die eine einzelne CV-Zahl
abstrahiert und verliert. Passt exakt zum bereits vorhandenen Burst-Erkennungsalgorithmus.

### 3.4 Wortdauer-Histogramm (V1, bereits im Backlog) + Pausen-Overlay

Die vom Nutzer schon vorgeschlagene Idee — Histogramm der einzelnen Wortdauern. Kreative
Erweiterung: could zusätzlich die Pausendauern als zweites, überlagertes Histogramm (andere
Farbe) zeigen — macht auf einen Blick sichtbar, ob sich Wort- und Pausendauer klar trennen oder
überlappen (z.B. bei sehr zögerlichem Sprechen verschwimmt die Grenze).

### 3.5 Gebündelte Perturbations-Ansicht (Jitter-/Shimmer-Familie)

Statt 5 einzelner Kacheln (Jitter local/RAP/PPQ5, Shimmer local/APQ11): ein gruppiertes
Balkendiagramm, X-Achse = die 5 Maße, Y-Achse jeweils normalisiert auf den eigenen
Normbereich (z.B. als Vielfaches des Cutoffs) — macht sofort sichtbar, ob ALLE
Perturbationsmaße gemeinsam erhöht sind (konsistentes Muster) oder nur eines heraussticht
(evtl. Messartefakt). Nutzt direkt die in P15 recherchierten Normwerte als Referenzlinie im
Diagramm.

### 3.6 Sprechrate/Pausenzeit-Balken (Netto- vs. Artikulationsrate visuell)

Ein gestapelter Balken, der die Gesamtdauer in "reine Sprechzeit" (Artikulation) und
"Pausenzeit" aufteilt — macht den Vergleich Netto- vs. Artikulationsrate (aktuell zwei separate
Kacheln, die man gedanklich selbst in Bezug setzen muss) auf einen Blick verständlich: wie viel
der Verlangsamung ist reine Pausenzeit vs. tatsächlich langsamere Artikulation.

### 3.7 Erweitertes, überarbeitetes Profil-Radar (statt J2-Fix nur kosmetisch)

Das bestehende Radar (nur Vorlesen, 4 Achsen, laut Nutzer "nicht schön") könnte zu einem
EINZIGEN Gesamt-Sitzungs-Radar werden, das Achsen aus ALLEN Modulen kombiniert, sobald
vorhanden (Stimmqualität aus Vokalisation, Sprechrate/Flüssigkeit/Lexik/Rhythmus aus
Vorlesen/Spontansprache, DDK-Regelmäßigkeit aus DDK) — EIN "Sprachprofil auf einen Blick" für
den ganzen Test statt eines isolierten Vorlesen-Radars. Würde J2 nicht nur kosmetisch, sondern
strukturell lösen.

## 4. Etablierte wissenschaftliche Darstellungsformen, die wir noch NICHT nutzen

- **Vokaltrapez/F1-F2-Plot** — siehe 3.1, DIE klassische phonetische Standarddarstellung,
  fehlt komplett.
- **Prosogramm** (Mertens, IPO-Ansatz) — stilisiert eine Tonhöhenkurve auf perzeptuell
  relevante "Stufen" statt der rohen, verrauschten F0-Kurve — würde Monopitch/Prosodie-
  Auffälligkeiten viel klarer zeigen als die aktuelle rohe Kurve im Spektrogramm-Overlay.
  Größerer Implementierungsaufwand (eigener Glättungs-/Stufen-Algorithmus nötig), aber
  etabliertes linguistisches Werkzeug, kein Hobby-Erfindung.
- **Long-Term Average Spectrum (LTAS)** — über die gesamte Aufnahme gemitteltes
  Frequenzspektrum, klassisches Stimmqualitäts-Werkzeug (zeigt z.B. reduzierte
  Hochfrequenzenergie bei rauer/behauchter Stimme sichtbar als abfallende Kurve) — würde CPPS/
  HNR eine zusätzliche visuelle Entsprechung geben, "outside the box" da bisher nicht im
  Projekt erwähnt.
- **Perioden-zu-Periode-Perturbationsspur** — statt nur der aggregierten Jitter-/Shimmer-
  Prozentzahl eine kleine Linie/Punktwolke der einzelnen Zyklus-zu-Zyklus-Abweichungen über
  die Vokaldauer — zeigt, ob die Perturbation gleichmäßig verteilt oder auf wenige
  Ausreißer-Zyklen konzentriert ist. Fortgeschritten, eher "nice to have".

## 5. Kein Grund für weitere Visualisierung

Nicht jeder Parameter braucht eine eigene Grafik — reine Zähl-/Meta-Werte (Wörter erkannt,
Erkennungs-Konfidenz, n_phrases) bleiben sinnvollerweise Kacheln, eine Visualisierung würde
hier nur Komplexität ohne Erkenntnisgewinn hinzufügen.

## 6. Grobe Priorisierung (Empfehlung, keine Entscheidung)

Nach Aufwand/Wirkung-Verhältnis, absteigend:
1. **Vokalraum-Plot** (3.1) — Rohdaten schon da, klassischste/verständlichste Darstellung,
   macht VSA erstmals wirklich "sichtbar" statt nur als Zahl.
2. **Wortdauer-Histogramm** (3.4, = V1) — vom Nutzer selbst schon vorgeschlagen, Rohdaten
   (Wort-Zeitstempel) bereits vorhanden.
3. **Pausen-Timeline** (3.2) — nutzt dieselben Wort-Zeitstempel wie 3.4, könnte in einem Zug
   mitgebaut werden.
4. **DDK-Rhythmus-Spur** (3.3) — eigenes Modul, macht die bisher "unsichtbare" CV-Zahl greifbar.
5. Perturbations-Bündel (3.5) und Sprechrate-Balken (3.6) — kleinere, isolierte Ergänzungen.
6. Radar-Neukonzeption (3.7) und LTAS/Prosogramm (Abschnitt 4) — größerer Aufwand, eher
   mittelfristig.

Nichts davon ist umgesetzt — dies ist ausschließlich das angefragte Konzept zur Diskussion.
