# Konzept: Muster-Wertung — von Einzelwerten zu einer Gesamtaussage

**Status: Konzept, noch nicht umgesetzt.** Erstellt 2026-08-22 auf Nutzer-Wunsch: die
Parameter aufgreifen, die bei den vorliegenden Dysarthrie-Aufnahmen auffällig sind, daraus eine
Aussage bilden („wenn sich diese Konstellation zeigt, ist das verdächtig für eine Dysarthrie"),
möglichst mit Abstufung leicht/mittel/schwer, und das im Report abbilden.

Dieses Dokument sagt zuerst, **was die Datenlage trägt und was nicht** — sonst entsteht genau
die unvalidierte Bewertung, die das Projekt seit Beginn vermeidet.

---

## 1. Die Datenlage, schonungslos

### Was an ECHTEN Patient:innen vorliegt

| Fall | Aufgabe | Jitter % | Shimmer % | HNR dB | Voice Breaks |
|---|---|---|---|---|---|
| SVD gesund m | /a/ 1,35 s | 0,21 | 1,56 | 27,4 | 0 |
| SVD gesund w | /a/ 0,80 s | 0,33 | 2,19 | 27,2 | 0 |
| SVD Parkinson | /a/ 0,72 s | 0,50 | 2,99 | 18,8 | 0 |
| SVD ALS | /a/ 1,57 s | 0,43 | 5,19 | 21,1 | 0 |
| SVD Bulbärparalyse | /a/ 1,99 s | 1,38 | 7,17 | 16,0 | 1 (5,95 %) |

**Drei echte Patient:innen, deutsch, gleiche Aufnahmekette — und ein sauberer Gradient**:
Gesunde 0,21–0,33 / 1,56–2,19 / 27,2–27,4, Erkrankte 0,43–1,38 / 2,99–7,17 / 16,0–21,1.
Innerhalb dieser Kette trennen Jitter, Shimmer und HNR die Gruppen vollständig überlappungsfrei.

**Aber**: Es gibt von diesen Personen **ausschließlich den gehaltenen Vokal /a/** (plus zwei
Sätze von 2,2 s bzw. 2,3 s). Kein /i/, kein /u/, kein Lesetext, keine Spontansprache, keine
Diadochokinese. Für die Boxen 2 und 3 liegen **null echte Patientendaten** vor.

### Was aus Simulation vorliegt

Vier Durchläufe, alle von **derselben einen Person**: NV-4A4T (leicht), NV-VAE5 (schwer),
IPH-SIM-01 (mittel–schwer, bulbär/fazial), NV-99H7 (nicht dokumentiert).

### Der Befund, der alles Weitere prägt: Simulation ≠ Erkrankung

Ein direkter Vergleich desselben Krankheitsbildes, einmal simuliert und einmal echt:

| | eigene Simulation „bulbär/fazial" | echte SVD-Bulbärparalyse |
|---|---|---|
| Jitter | 0,43 % (Kontrolle: 0,41 %) | **1,38 %** |
| Shimmer | 4,30 % (Kontrolle: 4,09 %) | **7,17 %** |
| HNR | 20,7 dB (Kontrolle: 19,1 dB) | **16,0 dB** |
| Voice Breaks | 0 | **1 (5,95 %)** |
| Vokalraum (FCR) | **1,276** (Kontrolle: 0,853) | nicht berechenbar (nur /a/) |

**Die Simulation traf die artikulatorische Seite und verfehlte die phonatorische vollständig.**
Der echte Bulbär-Fall zeigt das umgekehrte Bild: deutlich gestörte Phonation. Das ist keine
Kleinigkeit — es heißt, dass eine willentliche Nachahmung genau die Komponente nicht
reproduziert, die bei der echten Erkrankung aus der Schwäche der Kehlkopfmuskulatur folgt.

**Konsequenz für dieses Konzept: Schwellenwerte und Schweregrade dürfen NICHT aus den
Simulationen abgeleitet werden.** Sie taugen zum Prüfen, ob ein Marker überhaupt reagiert —
nicht dazu, festzulegen, ab wann ein Wert „mittelgradig" ist.

---

## 2. Was daraus folgt: zwei Dinge trennen

Der Wunsch enthält zwei Bestandteile, die unterschiedlich gut abgesichert sind:

1. **Mustererkennung** — welche Marker weichen ab, und ergeben sie zusammen ein stimmiges
   Bild? **Das ist heute tragfähig** und bewegt sich innerhalb der bereits vereinbarten
   Zwischenstufen 1+2 aus `docs/backlog.md` („Muster-Zusammenfassung", „Konsistenz-Hinweis").
2. **Schweregrad leicht/mittel/schwer** — **das ist eine klinische Einstufung.** Sie bräuchte
   eine Kohorte mit klinisch erhobenem Schweregrad als Referenz. Die haben wir nicht: drei
   Patient:innen ohne Schweregrad-Angabe und eine simulierende Person.

**Vorschlag**: (1) voll umsetzen. Für (2) nicht den klinischen Schweregrad behaupten, sondern
die **Ausprägung der Messabweichung** angeben — eine Aussage über die Zahl, nicht über den
Menschen. Formulierung z. B. „deutlich außerhalb des Referenzbereichs" statt „schwere
Dysarthrie". Das gibt praktisch dieselbe Abstufung, ohne eine Behauptung aufzustellen, die die
Daten nicht decken.

---

## 3. Das Marker-Set

Nur Marker mit belegter Reaktion. Jeder trägt eine Vertrauensstufe, wie schon bei
`PARAMETER_INFO`.

### Box 1 — Vokalisation (Phonation)

| Marker | Stufe | Begründung | Referenz |
|---|---|---|---|
| Jitter, Shimmer, HNR | ★★☆ | trennen bei den echten SVD-Fällen überlappungsfrei | **nur innerhalb derselben Aufnahmekette** |
| Voice Breaks | ★★☆ | im echten Bulbär-Fall vorhanden, bei allen Gesunden 0 | Grenze >0 |
| FCR / VSA | ★★☆ | Literatur (Sapir), stärkster Effekt der Simulation | Verlauf, nicht absolut |
| MPT | ❌ | Compliance-Problem, alle eigenen Werte unplausibel niedrig | — |

**Wichtige Einschränkung, die bestehen bleibt**: Jitter/Shimmer/HNR sind über verschiedene
Aufnahmeketten **nicht** absolut vergleichbar. Der Ketteneffekt war in unseren Messungen größer
als der Pathologieeffekt (siehe `docs/externe_testdaten.md`). Diese drei Marker dürfen daher nur
im Verlauf derselben Person bei gleichem Setup gewertet werden — oder gegen eine Referenz aus
**derselben** Kette.

### Box 2 — Fließende Sprache

| Marker | Stufe | Begründung |
|---|---|---|
| Sprechrate (WPM) | ★★★ | in allen drei Vergleichsdurchläufen reproduziert (170→107, 155→101, 149→94) |
| Ø Wortdauer | ★★★ | ebenso, nahezu verdoppelt |
| WER / CER | ★★★ | 0,0 % vs. 33,3 % bei identischem Text; am echten ALS-Satz bestätigt |
| ASR-Konfidenz | ★★☆ | 0,878 vs. 0,716 |
| Pausen / Flüssigkeit | ★★☆ | **nur Lesetext** (0,973 vs. 0,794); bei Spontansprache trennt es nicht |
| Burst-Schärfe | ★☆☆ | 331 vs. 281 dB/s, nur ein Durchlauf |

### Box 3 — Diadochokinese

**Derzeit nicht verwendbar.** Die Rate ist plausibel, aber der Variationskoeffizient hat eine
Eigenstreuung von 0,15–0,28 bei perfekt gleichmäßiger Eingabe (RANDNOTIZ-18) — er kann echte
Unterschiede in dieser Größenordnung gar nicht auflösen. Box 3 bleibt außen vor, bis das geklärt
ist. Das ist ehrlicher, als sie mit einem Marker zu füllen, der nachweislich rauscht.

---

## 4. Woran gemessen wird — drei Referenzarten, absteigend belastbar

1. **Eigene Voraufnahme derselben Person, gleiches Setup** (longitudinal). Hebt alle
   Ketten- und Sprecherprobleme auf und ist der erklärte Kernzweck des Projekts. **Stärkste
   Aussage.**
2. **Literatur-Referenzbereiche**, wo vorhanden (Sprechrate, teils FCR). Mittelstark.
3. **Eigenes Referenzkorpus** (SVD-Gesunde, eigene Kontrollen). Schwach — n=2 bis 5, und nur
   innerhalb derselben Kette gültig.

Der Report muss **anzeigen, welche Referenzart** einer Aussage zugrunde liegt. Ein Muster ohne
Voraufnahme ist eine schwächere Aussage als eines mit — und das darf nicht unsichtbar bleiben.

---

## 5. Wie aggregiert wird — Regeln, keine Punktsumme

Bewusst **keine gewichtete Summe**: Gewichte wären frei erfunden, und genau das ist der Punkt,
an dem aus Deskription unvalidierte Diagnostik wird.

Stattdessen je Box zwei Angaben:

- **Wie viele Marker weichen ab** — „3 von 5 Markern der Box Fließsprache weichen in der von
  der Literatur beschriebenen Richtung ab."
- **Wie stimmig** — weichen zusammengehörige Marker gemeinsam ab (Sprechrate + Wortdauer + WER
  gehören zusammen) oder nur vereinzelt? Vereinzelte Abweichung ist eher ein Messartefakt.

Daraus die Gesamtaussage, die **die betroffenen Boxen benennt** statt sie zu verrechnen:

> „Auffälligkeiten in der Box Fließsprache (3 von 5 Markern, gleichsinnig), unauffällige
> Phonation. Dieses Muster — gestörte Artikulation bei erhaltener Stimmqualität — beschreibt die
> Literatur bei artikulatorisch betonten Dysarthrien."

Das ist klinisch informativer als eine Zahl, und es ist genau das, was unsere Daten hergeben:
Der iPhone-Durchlauf zeigte diese Trennung (Artikulation betroffen, Phonation nicht), der echte
Bulbär-Fall die umgekehrte.

---

## 6. Ausprägung statt Schweregrad

Je Marker drei Stufen, definiert über den **Abstand zur Referenz**, nicht über eine klinische
Skala:

| Stufe | Kriterium |
|---|---|
| grenzwertig | knapp außerhalb des Referenzbereichs |
| deutlich | klar außerhalb |
| stark | um ein Vielfaches außerhalb |

Die konkreten Grenzen müssen je Marker aus der jeweils besten verfügbaren Referenz kommen und
**einzeln begründet** sein — kein einheitlicher Faktor über alle Marker. Wo keine belastbare
Referenz existiert, wird **keine** Stufe vergeben, sondern die Abweichung nur beschrieben.

Auf Box-Ebene wird die Ausprägung **nicht gemittelt**, sondern als Spanne genannt („zwei Marker
deutlich, einer grenzwertig"). Ein Mittelwert über ungleichartige Marker wäre wieder ein Score.

---

## 7. Darstellung im Report

Neuer Abschnitt **vor** den Einzelwert-Tabellen, damit er die Zusammenfassung ist und nicht ein
Anhang:

```
MUSTER-ZUSAMMENFASSUNG
Referenz: eigene Voraufnahme vom 12.07.2026, gleiches Aufnahme-Setup

Vokalisation      unauffällig          0 von 4 Markern abweichend
Fließsprache      auffällig            3 von 5 Markern, gleichsinnig
                  · Sprechrate      94 WPM     deutlich unter Referenz (149)
                  · Ø Wortdauer     0,56 s     deutlich über Referenz (0,33)
                  · Verständlichkeit 33,3 % WER deutlich über Referenz (0,0)
Diadochokinese    nicht bewertet       Marker derzeit nicht ausreichend zuverlässig

EINORDNUNG
Gestörte Artikulation bei erhaltener Stimmqualität. Dieses Muster beschreibt die
Literatur bei artikulatorisch betonten Dysarthrien.

Diese Auswertung ist ein Messbefund, keine Diagnose. Sie beruht auf N=3 echten
Vergleichsfällen und ersetzt keine klinische Beurteilung.
```

Der Disclaimer gehört **in denselben Kasten**, nicht ans Ende des Dokuments — sonst wird die
Aussage zitiert und der Vorbehalt bleibt liegen.

---

## 8. Zur Formulierung „verdächtig für eine Dysarthrie"

Der Wunsch war diese Wendung. Sie ist eine diagnostische Aussage; das Projektprinzip
(`CONTRIBUTING.md`) schließt sie aus, und die Datenlage — drei echte Fälle, alle nur mit
gehaltenem Vokal — trägt sie auch nicht.

**Vorgeschlagene Formulierung**: „Dieses Muster ist mit einer Dysarthrie vereinbar" bzw.
„entspricht dem Muster, das die Literatur bei … beschreibt". Sie transportiert praktisch
dieselbe Information, behauptet aber keine Wahrscheinlichkeit für eine Person.

**Ausdrücklich nicht vorgesehen**: eine Prozentangabe, ein Gesamt-Score, eine
Erkrankungswahrscheinlichkeit. Das bleibt Stufe 3 der Grundsatzfrage und damit ausgeschlossen,
solange keine validierte Kohorte dahintersteht.

---

## 9. Umsetzungsschritte

1. `core/wertung.py` — Marker-Registry mit Box, Vertrauensstufe, Richtung und Referenzquelle;
   je Marker eine Funktion, die aus Wert + Referenz eine Ausprägungsstufe bestimmt.
2. Regelwerk für die Box-Aussage (Anzahl + Gleichsinnigkeit), ohne Punktsumme.
3. Ground-Truth-Tests: konstruierte Marker-Konstellationen → erwartete Box-Aussage. Ein
   Regelwerk ohne Tests wäre nach allem, was in den letzten Tagen aufgefallen ist, fahrlässig.
4. Report-Abschnitt in `core/report_export.py` (PDF + Excel) und im Gesamtbericht.
5. Referenzarten sichtbar machen (Voraufnahme / Literatur / Korpus).

## 10. Offene Entscheidungen

- **Formulierung**: „vereinbar mit" (Vorschlag) oder „verdächtig für" (Wunsch)?
- **Ausprägungsstufen anzeigen, wenn nur die schwächste Referenzart vorliegt** — oder dann nur
  beschreiben ohne Stufe?
- **Box 3 leer lassen** oder ganz ausblenden, solange die DDK-Marker rauschen?
