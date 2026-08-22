"""Dysarthrie-Marker — Kennzeichnung und Quantifizierung auffaelliger Messwerte.

Nutzer-Entscheidung 2026-08-22 (siehe docs/konzept_wertung.md): Die Schwere wird dem MARKER
zugeschrieben, nicht der Person. Ausgegeben wird also "Dysarthrie-Marker: hoch", niemals
"schwere Dysarthrie". Es wird ausdruecklich NICHT behauptet, dass eine Dysarthrie vorliegt,
und erst recht nicht, welcher Typ — das bleibt der klinischen Beurteilung vorbehalten.

Diese Trennung ist nicht bloss vorsichtige Formulierung. Sie ist inhaltlich richtig: ein Marker
ist eine Eigenschaft der Messung, und ueber die koennen wir eine belegbare Aussage treffen. Ob
daraus eine Erkrankung folgt, koennen wir mit drei echten Faellen nicht sagen.

WARUM NICHT DIE VORHANDENEN LITERATUR-ZONEN (core/reference_ranges.py)?
Geprueft am 2026-08-22 an den echten SVD-Faellen — die absoluten Grenzen sind zu unempfindlich:
der Parkinson-Fall gilt bei Jitter UND Shimmer als "im Normbereich", der ALS-Fall bei Jitter und
HNR ebenso, und selbst die Bulbaerparalyse erreicht in keinem Wert die oberste Zone. Umgekehrt
wird eine gesunde eigene Aufnahme beim HNR als grenzwertig markiert. Der Grund: innerhalb
derselben Aufnahmekette ist der Gradient eindeutig (gesund 0,21-0,33% Jitter, erkrankt
0,43-1,38%), aber die Literaturgrenzen (<1%) liegen weit oberhalb des gesunden Bereichs, weil
sie ueber heterogene Aufnahmebedingungen hinweg robust sein muessen.

Deshalb arbeitet die Bewertung hier RELATIV zu einer Referenz aus derselben Aufnahmekette --
im Idealfall einer frueheren Aufnahme derselben Person. Das ist zugleich der Kernzweck des
Projekts und umgeht den Aufnahmeketten-Effekt, der in unseren Messungen groesser war als der
Pathologie-Effekt (siehe docs/externe_testdaten.md).
"""

from __future__ import annotations

from dataclasses import dataclass

KEINE_STUFE = None
STUFEN = ("leicht", "mittel", "hoch")

# Skalenarten: wie der Abstand zur Referenz gemessen wird.
VERHAELTNIS = "verhaeltnis"      # Wert / Referenz (fuer Groessen ohne natuerlichen Nullpunkt-Bezug)
DIFFERENZ_DB = "differenz_db"    # Referenz - Wert, in dB (logarithmische Groessen)
ANTEIL = "anteil"                # absoluter Abstand in Prozentpunkten


@dataclass(frozen=True)
class MarkerDefinition:
    """Ein Kennwert, der als Dysarthrie-Marker taugt.

    `schwellen` sind die Untergrenzen fuer leicht/mittel/hoch auf der jeweiligen Skala.
    `vertrauen` folgt derselben Logik wie das evidence-Feld in PARAMETER_INFO.
    `quelle` begruendet die Schwellen -- jede Zahl hier muss sich rechtfertigen lassen.
    """
    box: str
    label: str
    richtung: str          # "hoch" = hoehere Werte sind auffaelliger, "niedrig" = umgekehrt
    skala: str
    schwellen: tuple[float, float, float]
    vertrauen: str
    quelle: str
    gruppe: str = ""       # Marker derselben Gruppe gehoeren laut Literatur zusammen


# ── Schwellenherkunft ────────────────────────────────────────────────────────────────────
#
# ERSTE Fassung war 1,25 / 2,0 / 3,0 bzw. 3 / 6 / 10 dB. Am 2026-08-22 an zwei GESUNDEN
# Sitzungen derselben Person geprueft (NV-BFU8 vs. NV-Z8YW, beides Normalbefunde) -- und dabei
# faelschlich zwei Marker erzeugt: Shimmer wich zwischen den beiden gesunden Sitzungen um
# Faktor 1,28 ab, HNR um 4,0 dB. Beides lag ueber der damaligen "leicht"-Schwelle.
#
# Das ist die entscheidende Lehre: **eine Schwelle muss oberhalb der normalen Schwankung
# derselben gesunden Person liegen**, sonst markiert sie Tagesform statt Befund. Die
# Perturbationsschwellen sind deshalb angehoben (Verhaeltnis 1,5/2,2/3,0; HNR 5/8/12 dB) --
# begruendet an gemessener Test-Retest-Schwankung, nicht am gewuenschten Ergebnis.
#
# Die Schwellen sind an den drei echten SVD-Faellen plus zwei SVD-Gesunden geprueft. Ergebnis
# mit der ERSTEN Fassung (zur Nachvollziehbarkeit dokumentiert):
#
#   Parkinson   Jitter 1,53x | Shimmer 1,36x | HNR -8,3dB
#   ALS         Jitter 1,30x | Shimmer 2,37x | HNR -6,1dB
#   Bulbaer     Jitter 4,20x | Shimmer 3,27x | HNR -11,2dB
#   beide Gesunden: kein Marker
#
# Mit den angehobenen Schwellen bleibt die Reihenfolge erhalten (Bulbaer deutlich vor den
# beiden anderen), die Empfindlichkeit sinkt aber -- der Parkinson-Fall wird dann nur noch
# ueber den HNR erfasst. Das ist der bewusst in Kauf genommene Preis dafuer, gesunde
# Tagesschwankung nicht als Befund auszugeben. Ein Marker, der bei Gesunden anschlaegt, waere
# wertlos; ein etwas unempfindlicherer ist brauchbar.
#
# ABER: n=3 Erkrankte, n=2 gesunde Wiederholungen. Die Schwellen sind plausibel und
# nachvollziehbar, NICHT validiert -- sie gehoeren revidiert, sobald mehr echte Faelle
# vorliegen. Genau dafuer stehen sie hier an einer Stelle und nicht verstreut im Code.

MARKER: dict[str, MarkerDefinition] = {
    # ── Box 1: Vokalisation (Phonation) ──
    "jitter_local_pct": MarkerDefinition(
        box="vokalisation", label="Jitter", richtung="hoch", skala=VERHAELTNIS,
        schwellen=(1.5, 2.2, 3.0), vertrauen="in der Forschung diskutiert", gruppe="perturbation",
        quelle="An den SVD-Faellen (gleiche Aufnahmekette) trennscharf: gesund 0,21-0,33%, "
               "erkrankt 0,43-1,38%. Nur kettenintern gueltig.",
    ),
    "shimmer_local_pct": MarkerDefinition(
        box="vokalisation", label="Shimmer", richtung="hoch", skala=VERHAELTNIS,
        schwellen=(1.5, 2.2, 3.0), vertrauen="in der Forschung diskutiert", gruppe="perturbation",
        quelle="Schwelle liegt ueber der gemessenen gesunden Test-Retest-Schwankung (1,28x). "
               "SVD: gesund 1,56-2,19%, erkrankt 2,99-7,17%. Nur kettenintern gueltig.",
    ),
    "hnr_mean_db": MarkerDefinition(
        box="vokalisation", label="HNR", richtung="niedrig", skala=DIFFERENZ_DB,
        schwellen=(5.0, 8.0, 12.0), vertrauen="in der Forschung diskutiert", gruppe="perturbation",
        quelle="SVD: gesund 27,2-27,4 dB, erkrankt 16,0-21,1 dB. dB ist bereits logarithmisch, "
               "deshalb absolute Differenz statt Verhaeltnis.",
    ),
    "voice_breaks_degree_pct": MarkerDefinition(
        box="vokalisation", label="Stimmabbrueche", richtung="hoch", skala=ANTEIL,
        schwellen=(1.0, 5.0, 15.0), vertrauen="in der Forschung diskutiert",
        quelle="Bei allen Gesunden (eigen und SVD) 0%. Im echten Bulbaerfall 5,95%. "
               "Jeder Wert ueber 0 ist auffaellig, die Stufung ist eine Setzung.",
    ),
    "fcr": MarkerDefinition(
        box="vokalisation", label="Vokal-Zentralisierung (FCR)", richtung="hoch", skala=VERHAELTNIS,
        schwellen=(1.10, 1.25, 1.45), vertrauen="in der Forschung diskutiert",
        quelle="Sapir et al. 2010/2011; eigene Gesunde 0,85-0,98, eigene Simulationen "
               "1,06-1,28. FCR ist konstruktionsbedingt weniger sprecherabhaengig als die VSA "
               "und deshalb auch ohne Voraufnahme brauchbarer. KEIN echter Patientenwert "
               "vorhanden -- die SVD-Faelle liefern nur /a/.",
    ),

    # ── Box 2: Fliessende Sprache ──
    "net_speech_rate_wpm": MarkerDefinition(
        box="fliesssprache", label="Sprechrate", richtung="niedrig", skala=VERHAELTNIS,
        schwellen=(1.15, 1.4, 1.8), vertrauen="gut etabliert", gruppe="tempo",
        quelle="In drei unabhaengigen eigenen Vergleichen reproduziert (170->107, 155->101, "
               "149->94 WPM). Klassischstes Dysarthrie-Signal der Literatur.",
    ),
    "mean_word_duration_s": MarkerDefinition(
        box="fliesssprache", label="Ø Wortdauer", richtung="hoch", skala=VERHAELTNIS,
        schwellen=(1.15, 1.4, 1.8), vertrauen="gut etabliert", gruppe="tempo",
        quelle="Gegenstueck zur Sprechrate, in denselben drei Vergleichen nahezu verdoppelt "
               "(0,27->0,47 / 0,29->0,48 / 0,33->0,56 s).",
    ),
    "wer_pct": MarkerDefinition(
        box="fliesssprache", label="Wortfehlerrate (Verständlichkeit)", richtung="hoch",
        skala=ANTEIL, schwellen=(5.0, 15.0, 30.0), vertrauen="gut etabliert",
        quelle="Bei identischem Lesetext 0,0% (gesund) vs. 33,3% (simuliert). Am echten "
               "ALS-Satz bestaetigt. Nur beim vorgelesenen Standardtext gueltig, da nur dort "
               "der Sollwert bekannt ist.",
    ),
    "fluency_score": MarkerDefinition(
        box="fliesssprache", label="Sprechfluss", richtung="niedrig", skala=VERHAELTNIS,
        schwellen=(1.1, 1.25, 1.5), vertrauen="eigene Heuristik / explorativ",
        quelle="Seit dem Signal-Umbau (RANDNOTIZ-17) belastbar: Lesetext 0,973 vs. 0,794. "
               "NUR beim Lesetext -- bei Spontansprache trennt das Mass nicht, weil freies "
               "Erzaehlen von Natur aus Denkpausen enthaelt.",
    ),
}


def _abstand(wert: float, referenz: float, definition: MarkerDefinition) -> float | None:
    """Abstand zur Referenz auf der Skala des Markers. Negativ = in die unauffaellige Richtung."""
    if wert is None or referenz is None:
        return None
    if definition.skala == VERHAELTNIS:
        if referenz <= 0:
            return None
        return wert / referenz if definition.richtung == "hoch" else referenz / wert if wert > 0 else None
    if definition.skala == DIFFERENZ_DB:
        return referenz - wert if definition.richtung == "niedrig" else wert - referenz
    # ANTEIL: absoluter Abstand in Prozentpunkten
    return wert - referenz if definition.richtung == "hoch" else referenz - wert


def bewerte_marker(key: str, wert: float | None, referenz: float | None) -> dict | None:
    """Bewertet EINEN Kennwert gegen seine Referenz.

    Gibt None zurueck, wenn der Marker unbekannt ist oder Wert/Referenz fehlen -- ein fehlender
    Wert darf nie als "unauffaellig" durchgehen, das waere eine stille Falschaussage."""
    definition = MARKER.get(key)
    if definition is None or wert is None or referenz is None:
        return None

    abstand = _abstand(wert, referenz, definition)
    if abstand is None:
        return None

    leicht, mittel, hoch = definition.schwellen
    if abstand >= hoch:
        stufe = "hoch"
    elif abstand >= mittel:
        stufe = "mittel"
    elif abstand >= leicht:
        stufe = "leicht"
    else:
        stufe = KEINE_STUFE

    return {
        "key": key, "label": definition.label, "box": definition.box, "gruppe": definition.gruppe,
        "wert": wert, "referenz": referenz, "abstand": abstand, "skala": definition.skala,
        "stufe": stufe, "vertrauen": definition.vertrauen,
    }


def _hoechste_stufe(stufen: list[str]) -> str | None:
    for s in reversed(STUFEN):
        if s in stufen:
            return s
    return None


def bewerte_box(box: str, werte: dict, referenzen: dict) -> dict:
    """Fasst alle Marker einer Box zusammen.

    Bewusst OHNE gewichtete Punktsumme: Gewichte waeren frei erfunden, und genau an dieser
    Stelle wuerde aus Beschreibung unvalidierte Diagnostik. Berichtet wird stattdessen, wie
    viele Marker abweichen und ob zusammengehoerige Marker das GEMEINSAM tun -- eine vereinzelte
    Abweichung ist eher ein Messartefakt als ein Befund."""
    bewertungen = []
    for key, definition in MARKER.items():
        if definition.box != box:
            continue
        b = bewerte_marker(key, werte.get(key), referenzen.get(key))
        if b is not None:
            bewertungen.append(b)

    auffaellig = [b for b in bewertungen if b["stufe"] is not None]
    gruppen = {b["gruppe"] for b in auffaellig if b["gruppe"]}
    gleichsinnig = False
    for g in gruppen:
        in_gruppe = [b for b in bewertungen if b["gruppe"] == g]
        auff_in_gruppe = [b for b in in_gruppe if b["stufe"] is not None]
        if len(in_gruppe) >= 2 and len(auff_in_gruppe) >= 2:
            gleichsinnig = True

    return {
        "box": box,
        "geprueft": len(bewertungen),
        "auffaellig": len(auffaellig),
        "hoechste_stufe": _hoechste_stufe([b["stufe"] for b in auffaellig]),
        "gleichsinnig": gleichsinnig,
        "marker": bewertungen,
    }


def dysarthrie_marker(werte: dict, referenzen: dict) -> dict:
    """Gesamtergebnis ueber alle Boxen.

    `werte` ist ein flaches Kennwert-Dict (wie core.interpretation.flatten_take() es liefert),
    `referenzen` dasselbe fuer die Vergleichsaufnahme.

    Liefert bewusst KEINE Diagnose und keine Wahrscheinlichkeit -- nur, welche Marker
    auffaellig sind und wie stark."""
    boxen = [bewerte_box(b, werte, referenzen) for b in ("vokalisation", "fliesssprache")]
    boxen = [b for b in boxen if b["geprueft"] > 0]

    alle_auffaellig = [m for b in boxen for m in b["marker"] if m["stufe"] is not None]
    return {
        "boxen": boxen,
        "marker_gesamt": sum(b["geprueft"] for b in boxen),
        "marker_auffaellig": len(alle_auffaellig),
        "hoechste_stufe": _hoechste_stufe([m["stufe"] for m in alle_auffaellig]),
        "betroffene_boxen": [b["box"] for b in boxen if b["auffaellig"] > 0],
    }
