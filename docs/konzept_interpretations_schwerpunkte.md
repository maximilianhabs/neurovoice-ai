# Konzept: Interpretations-Schwerpunkte je Aufgabentyp — grobe Schlagrichtung statt Score

**Status: reines Konzept, NICHT umgesetzt.** Erstellt 2026-08-17 auf Nutzer-Wunsch, nachdem
mehrere eigene Testreihen (simulierte Dysarthrie, siehe `docs/backlog.md`
"Dysarthrie-Vergleichsstudie") UND ein extern gegengehörter, echter Dysarthrie-Fall
(`docs/externe_testdaten.md`, ALS-Sprecher) genug Datenpunkte ergeben haben, um erste,
vorsichtige Interpretationsschwerpunkte zu benennen.

**Bewusster Bezug zur bereits offenen Grundsatzfrage** (siehe `docs/backlog.md` "Offene
Grundsatzfrage: über die reine Deskription hinaus?"): dieses Dokument bewegt sich innerhalb
der dort skizzierten, mit dem Projektprinzip vereinbaren Zwischenstufen (Muster-
Zusammenfassung, Konsistenz-Hinweis) — **explizit KEIN Einzel-Score, keine
Wahrscheinlichkeitsangabe "X% Dysarthrie"**. Stattdessen: pro Parameter eine grobe
Richtungs-/Vertrauens-Einordnung, analog zum bereits etablierten Evidenz-Tier-System in
`core/interpretation.py::PARAMETER_INFO` ("gut etabliert"/"in der Forschung diskutiert"/
"eigene Heuristik"/"deskriptiv").

## Grundidee: drei getrennte "Boxen" nach Aufgabentyp

Der Nutzer hat zu Recht betont: ein gehaltener Vokal misst etwas fundamental anderes als
fließende Sprache oder Diadochokinese — Kennwerte aus unterschiedlichen Boxen dürfen nicht
vermischt oder gegeneinander aufgewogen werden. Diese Trennung zieht sich durch das gesamte
Konzept.

---

## Box 1 — Vokalisation (gehaltener Vokal /a/, /i/, /u/)

Misst: Phonationsstabilität (Kehlkopf-/Stimmlippenebene), NICHT Artikulation oder Tempo.

### Datengrundlage (bisher gesammelt)

| Quelle | Jitter% | Shimmer% | HNR dB | Voice Breaks % |
|---|---|---|---|---|
| Eigene gesund (2 Sessions) | 0,59–0,64 | 7,61–9,72 | 12,5–16,5 | 0 (bis auf 1 Ausreißer 4%) |
| Eigene simuliert (2 Sessions) | 0,55–0,97 | 4,76–11,29 | 9,45–22,60 | 0–34% |
| SVD gesund (extern, n=2) | 0,21–0,33 | 1,56–2,19 | 27,2–27,4 | — |
| SVD pathologisch (extern, n=2, Parkinson+ALS) | 0,43–0,50 | 2,99–5,19 | 18,8–21,1 | — |

### Grobe Schlagrichtung je Parameter

- **Voice Breaks — ★★★ robustestes Signal in dieser Box.** In BEIDEN eigenen simulierten
  Durchläufen der klarste Sprung (0% → 10–34%), während beide eigenen UND beide externen
  gesunden Referenzen bei ~0% liegen. **Richtung**: deutlich über 0% (v.a. >5-10%) bei
  gehaltenem Vokal = Hinweis auf Instabilität der Phonation, konsistent mit Dysarthrie-
  Literatur zu Stimmlippen-Koordinationsstörungen.
- **Jitter/Shimmer/HNR — ★☆☆ Richtung plausibel, ABSOLUTE Schwellen NICHT verlässlich
  über verschiedene Aufnahmeketten hinweg.** Innerhalb SVD (gleiche Aufnahmekette) bestätigt
  sich die erwartete Richtung (gesund besser als pathologisch). Aber: unsere eigenen
  "gesunden" Aufnahmen liegen bei diesen 3 Werten durchgehend SCHLECHTER als sogar die
  externen SVD-*Patient:innen* (siehe `docs/externe_testdaten.md`) — vermutlich ein
  Aufnahmeketten-Effekt (Browser-Mikrofon vs. Klinik-Laborausrüstung), nicht verifiziert.
  **Konsequenz**: diese 3 Werte NUR als Verlaufsvergleich INNERHALB derselben Aufnahmekette/
  Person nutzen (Vorher/Nachher bei gleichbleibendem Aufnahme-Setup), NICHT als absoluten
  Cutoff gegen eine fremde Referenzdatenbank.
- **MPT — ❓ aktuell nicht auswertbar.** Alle bisherigen eigenen Aufnahmen (gesund UND
  simuliert) liegen weit unter dem Literatur-Normbereich — spricht für ein
  Aufgaben-Compliance-Problem (nicht wirklich "so lange wie möglich" gehalten), nicht für
  einen echten Befund. Keine Schlagrichtung ableitbar, bis das aufgeklärt ist.
- **F0-Tremor-Frequenz — ❓ ein Ausreißer (12Hz) bei einer simulierten Session, sonst
  unauffällig.** Zu wenig Datenpunkte, vermutlich artefaktanfällig bei gleichzeitigen Voice
  Breaks. Keine Schlagrichtung ableitbar.

---

## Box 2 — Fließende Sprache (Vorlesen + Spontansprache)

Misst: Artikulation, Tempo, Prosodie, Sprachproduktion — NICHT reine Phonationsstabilität.

### Datengrundlage

| Parameter | Eigene gesund | Eigene simuliert (leicht→schwer) | Extern (ALS-Satz, gegengehört) |
|---|---|---|---|
| Sprechrate Spontan (WPM) | 121–155 | 101→93 | — (nur 6 Wörter, zu kurz für Rate) |
| Ø Wortdauer (s) | 0,29–0,41 | 0,48→0,53 | — |
| Ø Erkennungs-Konfidenz | (noch nicht systematisch erhoben bei eigenen Sessions) | (noch nicht erhoben) | **52,3%** (5/6 Wörter unsicher) |
| WER/CER | — | — | 0% (aber irreführend, s.u.) |

### Grobe Schlagrichtung je Parameter

- **Sprechrate — ★★★ robustestes Signal insgesamt, über alle 4 eigenen Sessions.** Sauberer,
  fast monotoner Abfall mit dem simulierten Schweregrad (155→121→101→93 WPM). **Richtung**:
  deutlich unter 140 WPM (unserem bisherigen unteren Normbereichs-Rand) bei Spontansprache =
  klares Verlangsamungssignal, eines der literaturmäßig etabliertesten Dysarthrie-Zeichen
  überhaupt.
- **Ø Wortdauer — ★★☆ konsistent mit Sprechrate, aber redundant dazu** (beide messen im Kern
  dasselbe Tempo-Phänomen aus unterschiedlichem Blickwinkel). Eigenständiger Zusatznutzen
  fraglich, sollte NICHT als zweites unabhängiges Signal gezählt werden, eher als
  Bestätigung/Détailebene der Sprechrate.
- **Erkennungs-Konfidenz — ★★☆ neu, aber vielversprechend, nur 1 Datenpunkt.** Der externe
  ALS-Fall zeigte extrem niedrige Konfidenz (52%) trotz korrekt erkannter Wörter — passt zur
  Erwartung, dass unklare Artikulation die Spracherkennung unsicherer macht, auch wenn sie
  den Text am Ende noch "erraten" kann. **Braucht dringend mehr Datenpunkte** (auch von den
  eigenen simulierten Sessions — bisher nicht systematisch mit ausgewertet!) bevor daraus
  eine verlässliche Richtung wird.
- **WER/CER — ⚠️ Richtung nicht eindeutig, siehe eigener Befund in `docs/backlog.md`.** Bei
  kurzen, hochgradig vorhersehbaren Sätzen kann WER trotz echter Dysarthrie bei 0% liegen
  (Sprachmodell "errät" den Text). Vermutlich empfindlicher bei LÄNGEREN, weniger
  vorhersehbaren Texten (unser eigener Nordwind-Lesetext, 27 Wörter) — aber dafür noch KEIN
  Datenpunkt mit einem echten oder simulierten Dysarthrie-Fall vorhanden. Offene Frage, nicht
  isoliert nutzen (siehe unten, immer mit Konfidenz kombinieren).
- **CPPS — ❌ aktuell NICHT als Unterscheidungsmerkmal nutzbar.** Zeigte sich bei ALLEN
  eigenen Sessions (gesund UND simuliert) durchgehend niedrig/"auffällig" — kein Unterschied
  zwischen den Gruppen erkennbar in unseren bisherigen Daten. Könnte an einem zu strengen
  Cutoff für unsere spezifische Aufnahmesituation liegen (siehe RANDNOTIZ in
  `docs/backlog.md`). Nicht in die Schlagrichtung einbeziehen, bis geklärt.
- **Artikulationsschärfe (`mean_burst_sharpness_db_s`) — ★☆☆ erster Datenpunkt vorhanden
  (2026-08-17), noch zu wenig für mehr als ★.** Nachgeholt an den beiden SVD-Satz-Aufnahmen
  (nur bei Wort-/Satzmaterial auswertbar, bei reinen Vokalen `None` — korrekt, da keine
  Konsonanten-Verschlüsse vorhanden). **ALS-Fall (vom Nutzer als eindeutig dysarthrisch
  bestätigt): 181,8 dB/s — deutlich unter unserer eigenen gesunden Baseline (~350-380 dB/s
  bei Vorlesen).** Parkinson-Fall dagegen 357,1 dB/s — unauffällig, im gesunden Bereich.
  Plausibel richtungsweisend für den ALS-Fall, aber mit nur 2 externen Fällen (und
  unterschiedlichem Ätiologie-Typ: bulbär/ALS vs. hypokinetisch/Parkinson) zu wenig für mehr
  als eine vorsichtige erste Einschätzung. Formant-Spannweite/-Geschwindigkeit
  (`formant_dynamics_features()`) ebenfalls erstmals ausgewertet, aber Richtung noch unklar
  (ALS zeigte größere F1-Spannweite, aber kleinere F2-Geschwindigkeit als Parkinson — kein
  konsistentes Muster erkennbar bei n=2).

---

## Box 3 — Diadochokinese (DDK, "pa-ta-ka")

Misst: Artikulations-Koordination/-Tempo bei schnellem Silbenwechsel.

### Datengrundlage

| Parameter | Eigene gesund | Eigene simuliert | Externe SVD-Referenz |
|---|---|---|---|
| DDK-Rate (Hz) | 1,84–1,92 | 2,37–2,47 (HÖHER, nicht niedriger!) | noch nicht getestet |
| DDK-Regelmäßigkeit (CV) | 0,51–1,02 | 0,53–0,67 | noch nicht getestet |

### Grobe Schlagrichtung: **aktuell KEINE — echte offene Messfrage**

Beide DDK-Kennwerte verhalten sich in unseren eigenen Daten NICHT literaturkonform (DDK-Rate
sollte bei Dysarthrie sinken, stieg bei uns aber in beiden simulierten Sessions). Wie in
`docs/bugtracker.md` RANDNOTIZ-18 vermutet, könnte die Zyklus-Zaehlung bei "pa-ta-ka" den
kompletten Dreiklang statt der drei Einzellaute zaehlen — bevor hier irgendeine Schlagrichtung
genannt wird, muss diese Messfrage geklärt werden (Audio-Gegenprobe mit bekannter
Wiederholungszahl, siehe dort). **Wichtig: keine Richtung raten, nur weil andere Boxen schon
welche haben** — lieber ehrlich "noch nicht auswertbar" als eine falsche Richtung.

---

## Zusammenfassende Tabelle (für schnellen Überblick)

| Box | Parameter | Vertrauen | Schlagrichtung Dysarthrie |
|---|---|---|---|
| Vokalisation | Voice Breaks | ★★★ | ↑ deutlich über 0% |
| Vokalisation | Jitter/Shimmer/HNR | ★☆☆ | ↑/↓ Richtung ja, absolute Schwelle nein |
| Vokalisation | MPT | ❓ | nicht auswertbar (Compliance-Problem) |
| Vokalisation | F0-Tremor | ❓ | nicht auswertbar (zu wenig Daten) |
| Fließsprache | Sprechrate | ★★★ | ↓ deutlich unter 140 WPM |
| Fließsprache | Ø Wortdauer | ★★☆ | ↑, aber redundant zu Sprechrate |
| Fließsprache | Erkennungs-Konfidenz | ★★☆ | ↓ (vielversprechend, wenig Daten) |
| Fließsprache | WER/CER | ⚠️ | unklar, nur in Kombination mit Konfidenz |
| Fließsprache | CPPS | ❌ | aktuell kein Signal in unseren Daten |
| Fließsprache | Alpha Ratio / Hammarberg-Index | ❓ | neu (2026-08-17), noch keine gesunde Vergleichsaufnahme |
| Fließsprache | Artikulationsschärfe | ★☆☆ | ↓ bei ALS-Fall (181,8 vs. ~350-380 gesund), Parkinson-Fall unauffällig — n=2, vorsichtig |
| DDK | DDK-Rate | ❌ | widerspricht Literatur in unseren Daten |
| DDK | DDK-Regelmäßigkeit (CV) | ❌ | inkonsistent |

## Nächste Schritte (Vorschlag, noch nicht umgesetzt)

1. **Konfidenz-Werte auch bei Spontansprache/eigenen simulierten Sessions systematisch
   erheben** — bisher nur beim externen ALS-Fall ausgewertet, größte offene Datenlücke bei
   einem ★★☆-Signal.
2. **Artikulationsschärfe gezielt bei einem nächsten Vorher/Nachher-Vergleich mit auswerten**
   — bisher komplette Lücke, nicht negativ, einfach nie verglichen.
3. **DDK-Zähl-Hypothese klären** (siehe `docs/bugtracker.md` RANDNOTIZ-18), bevor DDK
   überhaupt in eine Schlagrichtung einfließen kann.
4. **Erst NACH mehr Datenpunkten** über eine konkrete UI-Umsetzung nachdenken (z.B. ein
   "Mustererkennung"-Kasten im Gesamtbericht: "3 von 5 auswertbaren Parametern zeigen ein
   Dysarthrie-typisches Muster" — rein deskriptiv-zählend, siehe Zwischenstufe 1 in
   `docs/backlog.md`) — explizit NICHT vor dieser weiteren Datensammlung umsetzen, um nicht
   auf zu wenigen Fällen basierende Schwellen fest einzubauen.

**Ausdrücklich weiterhin nicht vorgesehen**: ein einzelner Gesamt-Score oder eine
Prozent-Wahrscheinlichkeit "X% Dysarthrie" — bleibt mit dem Projektprinzip unvereinbar, siehe
`docs/backlog.md`/`CONTRIBUTING.md`.
