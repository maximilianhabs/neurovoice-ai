# Konzept: Visualisierungen — Bestandsaufnahme + kreative Ideen

**Teil 1 (unten) ✅ VOLLSTÄNDIG UMGESETZT (2026-08-16)** — alle 6 geplanten Visualisierungen
implementiert, server-verifiziert, committed. **Teil 2 (weiter unten) ist ein neuer, größerer
Konzept-Nachtrag** (2026-08-16, Nutzer-Feedback mit ~35 Visualisierungsideen im Stil eines
"Speech Motor Control Visual-Analytics-Systems") — davon ausgewertet, was mit vorhandenen
Daten machbar ist. **NICHTS aus Teil 2 ist umgesetzt**, nur Backlog-Einträge (siehe
`docs/backlog.md` V3 ff.).

Verwandte, bereits bestehende Backlog-Punkte: V1 (Histogramm Wortdauern), V2 (sechs weitere
Visualisierungen), J2 (Radar-Diagramm bei Vorlesen "nicht schön").

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

**Nachtrag 2026-08-16**: alle 6 Punkte oben sind inzwischen umgesetzt (siehe Commits
4ef4bde/d4831c7/ada9a4a/502ba37/45ec5e9) — Teil 1 dieses Dokuments ist damit historisch zu
lesen ("Konzept" beschreibt den Plan, wie er VOR der Umsetzung aussah).

---

# Teil 2: Erweiterte Ideen aus Nutzer-Feedback (2026-08-16) — "Speech Motor Visual Analytics"

Der Nutzer brachte ein sehr umfangreiches, gut recherchiertes Feedback mit ~35
Visualisierungsideen ein (Kernthese: weg von Einzel-Charts, hin zu einem zusammenhängenden
"Speech Motor Control"-Visual-Analytics-System, mit Bezug auf aktuelle 2026er-Literatur zu
trajectory-basierten Vokalraummaßen, Entropie-/Komplexitäts-Markern und Composite-Biomarkern).
Systematisch triagiert nach: **(A)** mit vorhandenen Daten sofort umsetzbar, **(B)** braucht
neue, aber machbare Backend-Berechnung, **(C)** verletzt bestehende Projekt-Prinzipien,
**(D)** braucht Daten, die es noch nicht gibt.

## (A) Mit vorhandenen Daten umsetzbar — konkrete neue Backlog-Punkte

Diese vier haben es als **V3–V6** in `docs/backlog.md` geschafft, mit konkreter technischer
Grundlage:

1. **Speech Rail** (Idee #8 im Feedback, vom Nutzer selbst als Top-Priorität eingestuft) —
   eine gemeinsame Zeitachse mit Audio-Wellenform, Wörtern, Phasen, F0, Intensität, Formanten,
   Pausen UNTEREINANDER statt in getrennten Plots. Ist im Kern eine Erweiterung/
   Zusammenführung der bereits gebauten `pause_timeline_figure()` mit den bereits
   existierenden F0-/Intensitäts-/Formant-Daten (aus `spectrogram_figure()`,
   `intensity_figure()`) auf EINE gemeinsame Zeitachse statt mehrerer separater Plots
   übereinander. Höchster Aufwand der vier, aber auch höchster Nutzen laut Nutzer-Einschätzung.
2. **Patient-vs-Norm-Profil (Z-Score-artige Balken)** (Idee #15) — eine direkte Generalisierung
   des bereits gebauten `perturbation_bundle_figure()`-Musters (Wert als Vielfaches des
   Cutoffs, siehe `good_zone_bounds()`) auf ALLE 22 Parameter mit `typical_values`/Cutoff aus
   P15, nicht nur die 5 Jitter-/Shimmer-Maße. Technisch der einfachste neue Punkt, da die
   Infrastruktur (Cutoffs, Referenzwerte) bereits vollständig da ist.
3. **Vokal-Trajektorie über Zeit ("Vowel Flight")** (Idee #4) — F1/F2-Bewegung WÄHREND einer
   Äußerung statt nur der Mittelwert-Punkte im bestehenden Vokaltrapez. Braucht eine kleine
   Erweiterung: `formant_features()`/`formant_dynamics_features()` müssten die
   Frame-für-Frame-F1/F2-Werte zusätzlich zurückgeben (aktuell nur Mittelwert/IQR aggregiert) —
   dieselben Rohdaten werden intern in `spectrogram_figure()` schon einmal berechnet
   (`formant.get_value_at_time()`-Schleife), nur nicht persistiert.
4. **Tremor-Modulationsspektrum** (Idee #23) — `f0_tremor_features()` berechnet intern bereits
   ein Spektrum der F0-Zeitreihe, gibt aber nur die Peak-Frequenz zurück. Das volle Spektrum
   (Frequenz × Power) als kleine zusätzliche Grafik zu zeigen ist eine additive Erweiterung,
   analog zum DDK-Rhythmus-Muster (cycle_times additiv ergänzt).

## (B) Braucht neue, aber grundsätzlich machbare Backend-Berechnung (größerer Aufwand)

- **Vokalraum-Dichtekarte (KDE)** (Idee #5) und **Trajektorie-Stabilitäts-Ellipse** (Idee #22)
  — beide brauchen dieselbe Voraussetzung wie Punkt 3 oben (Frame-Level-F1/F2-Samples statt
  nur Mittelwerte), zusätzlich eine 2D-Dichteschätzung (KDE) bzw. Kovarianz-Ellipsen-Berechnung
  — machbar mit `scipy`/`numpy` (bereits Abhängigkeiten), aber mehr Aufwand als (A).
- **CPPS/Stimmstabilität über Zeit** ("Cepstral Mountain", Idee #24, vereinfacht) — aktuell
  liefert `cpp_features()` einen einzigen Aggregatwert pro Aufnahme. Für eine Zeitverlaufs-
  Darstellung müsste CPPS in gleitenden Zeitfenstern berechnet werden — Praat/Parselmouth
  unterstützt das grundsätzlich, aber neue Implementierung nötig.
- **Recurrence-Plot / Entropie-Karte** (Ideen #11, #12) — konzeptionell interessant und OHNE
  Patientenkohorte umsetzbar (reine Signalanalyse einer einzelnen Aufnahme), aber
  algorithmisch aufwendiger (Recurrence Quantification Analysis, gleitende Shannon-Entropie)
  und noch nicht in der Literatur-Rechercheliefe wie P15 abgesichert — eher ein
  Forschungs-Experiment als ein "kleiner Schritt".
- **Interaktives Hover/Brushing** (Ideen #7, #27, #28) — WICHTIGER ARCHITEKTUR-VORBEHALT: alle
  bisherigen Plots nutzen `matplotlib`/`st.pyplot()` (statische Bilder, kein Hover/Klick).
  Echte Interaktivität (Tooltip bei Formant-Position, Zeitbereich markieren und alle Plots
  synchron reagieren lassen) bräuchte einen Wechsel zu einer JS-basierten Chart-Bibliothek
  (z.B. Plotly via `st.plotly_chart()`) — das ist eine grundsätzliche Tech-Stack-Entscheidung,
  keine einzelne Visualisierung, und sollte separat entschieden werden, nicht nebenbei
  mitgezogen.
- **Small-Multiples-Dashboard mit gemeinsamer Zeitachse** (Idee #26) — organisatorisch
  sinnvoll, aber im Kern dieselbe Grundidee wie die Speech Rail oben (A.1) — eher eine
  Weiterentwicklung/alternative Anordnung davon als ein eigenständiger neuer Punkt.

## (C) Verletzt bestehende Projekt-Prinzipien — bewusst NICHT ins Backlog übernommen

Diese Ideen sind fachlich interessant, widersprechen aber expliziten, mehrfach bestätigten
Vorgaben dieses Projekts (rein deskriptiv, keine Diagnose, kein Score, kein ML-Modell ohne
echte gelabelte Patientendaten — siehe Backlog-Abschnitt "Klinische Indizes", dort bereits
bewusst zurückgestellt):

- **Motor-Landscape via PCA/UMAP-Embedding** (Idee #2) — würde eine Kohorte mit vielen
  Proband:innen brauchen, um einen sinnvollen Einbettungsraum zu lernen; wir haben aktuell nur
  Testaufnahmen einer einzelnen Person.
- **Phänotyp-Klassifikation** ("Hypokinetic 0.78", Ideen #2, #33 View 1) — ist im Kern ein
  automatisierter Diagnose-/Score-Vorschlag, genau das, was dieses Projekt bewusst NICHT tun
  soll (Nutzer-Vorgabe seit Projektbeginn).
- **SHAP-Erklärungen eines ML-Modells** (Idee #29) — setzt ein trainiertes Klassifikations-
  modell voraus, das es hier nicht gibt und ohne echte, gelabelte Patientendaten auch nicht
  verantwortbar wäre (dieselbe Begründung wie bei den "Klinischen Indizes" im Backlog).

## (D) Braucht Daten, die es noch nicht gibt

- **Longitudinale Trajektorien/River-Plots über mehrere Sitzungen** (Ideen #3, #16, #17, #30,
  View 5) — konzeptionell genau das, was der bereits bestehende Backlog-Punkt
  "Longitudinal-Tracking/Δ-Metriken" beschreibt — wartet weiterhin auf echte
  Mehrfach-Sitzungen über Zeit (P10 Proband:innen-Tracking existiert zwar schon, aber es gibt
  noch keine Person mit mehreren Sitzungen über Wochen/Monate).
- **Artikulatorische Mundraum-Animation via Acoustic-to-Articulatory-Inversion** (Idee #20) —
  bräuchte ein eigenes ML-Inversionsmodell (oder externe EMA-Hardware für echte Messungen),
  weit über den aktuellen Projektumfang hinaus. Explizit als "geschätzt, keine Messung"
  markieren, falls das jemals verfolgt wird.
- **3D-Vokal-Dichtewolke** (Idee #6) — dieselbe Datenvoraussetzung wie (B) oben
  (Frame-Level-F1/F2/Zeit), zusätzlich eine 3D-Visualisierungsentscheidung — der Nutzer merkt
  selbst an, dass 3D nur sinnvoll ist, wenn die dritte Dimension echte Information trägt
  (hier: Zeit) — grundsätzlich vertretbar, aber niedrige Priorität ohne die A/B-Grundlagen.

## Priorisierungsempfehlung für Teil 2

Reihenfolge, falls diese Runde als Nächstes angegangen wird: **Patient-vs-Norm-Profil
zuerst** (geringster Aufwand, nutzt bereits vorhandene P15-Infrastruktur vollständig) → dann
**Vokal-Trajektorie über Zeit** (kleine Backend-Erweiterung, macht danach auch Dichtekarte/
Ellipse aus (B) möglich) → dann **Speech Rail** (größter Umfang, aber vom Nutzer selbst als
wichtigste Einzelvisualisierung eingestuft) → Tremor-Spektrum als kleinerer Nebenschritt
irgendwo dazwischen. Die Interaktivitäts-Frage (Plotly vs. matplotlib) sollte VOR größeren
neuen Zeitachsen-Visualisierungen wie der Speech Rail entschieden werden, da sie beeinflusst,
wie diese am sinnvollsten gebaut wird.
