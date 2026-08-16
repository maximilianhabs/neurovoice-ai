"""Referenzbereiche fuer die Normwert-Ampel-Visualisierung (siehe docs/backlog.md,
Abschnitt "Werte-Hierarchie", Konzept-Artifact vom 2026-07-21).

Zwei getrennte Dimensionen pro Parameter:
- FIT: ist der Wert aus JEDER Aufnahme (v.a. Lesetext) auswertbar, oder braucht er
  gehaltenen Vokal? Bestimmt Position/Groesse (primaer vorne+gross, sekundaer hinten+klein).
- Referenzbereich (falls vorhanden): bestimmt, ob eine echte Ampel gezeigt wird ("norm")
  oder nur eine informative Nadel ohne Farbwertung ("info", da Literatur nur Richtung,
  keinen harten Cutoff nennt) oder gar keine Skala ("na", z.B. Task-Mismatch).

WICHTIG: Die festen Grenzwerte (Jitter/Shimmer/HNR/Sprechrate) stammen aus allgemeiner
stimmklinischer Literatur bzw. der IReST-Studie (siehe docs/literatur_review.md) - NICHT
aus einer projekteigenen Auswertung der Saarbruecker Voice Database. Bei Bedarf spaeter
gegen echte SVD-Zahlen austauschen (offene Frage, siehe docs/backlog.md).
"""

from __future__ import annotations

from core.design_tokens import SUCCESS, WARNING as _WARNING, DANGER, TEXT_SECONDARY

# Design-Transfer vom EDF-Analyzer (2026-08-14, siehe [[project_edf_ui_redesign]]): gleiche
# kanonische Ampelfarben wie dort, statt eigener Ad-hoc-Hex-Werte -- fachliche Bedeutung
# (gut/grenzwertig/auffällig/neutral) bleibt unverändert, nur die konkreten Töne wurden auf
# core/design_tokens.py umgestellt, damit beide Streamlit-Apps optisch zusammengehören.
GOOD = SUCCESS
WARNING = _WARNING
CRITICAL = DANGER
NEUTRAL = TEXT_SECONDARY

FIT_IMMER = "immer"
FIT_EINGESCHRAENKT = "eingeschraenkt"
FIT_VOKAL = "vokal"
FIT_DDK = "ddk"

FIT_LABELS = {
    FIT_IMMER: "immer auswertbar",
    FIT_EINGESCHRAENKT: "eingeschränkt aussagekräftig bei Fließsprache",
    FIT_VOKAL: "nur bei gehaltenem Vokal",
    FIT_DDK: 'nur beim DDK-Task ("pa-ta-ka")',
}


def speech_rate_zones():
    """WPM-Zonen, symmetrisch: zu langsam UND zu schnell werden markiert.
    Referenz: IReST-Studie, deutsche Vorlesegeschwindigkeit ca. 179 WPM (siehe Literatur-Review).
    """
    lo, hi = 60, 300
    span = hi - lo
    bounds = [60, 100, 140, 220, 260, 300]
    colors = [CRITICAL, WARNING, GOOD, WARNING, CRITICAL]
    zones = []
    for i in range(len(bounds) - 1):
        zones.append(((bounds[i] - lo) / span, (bounds[i + 1] - lo) / span, colors[i]))
    return lo, hi, zones


def hnr_zones():
    """Referenz: >20dB klar, 15-20dB grenzwertig, <15dB auffaellig (allg. Stimmklinik-Lit.)."""
    lo, hi = 0, 30
    return lo, hi, [(0, 15 / 30, CRITICAL), (15 / 30, 20 / 30, WARNING), (20 / 30, 1, GOOD)]


def jitter_zones():
    """Referenz: <1% normal (allg. Stimmklinik-Literatur) - nur bei gehaltenem Vokal gueltig."""
    lo, hi = 0, 5
    return lo, hi, [(0, 1 / 5, GOOD), (1 / 5, 2 / 5, WARNING), (2 / 5, 1, CRITICAL)]


def shimmer_zones():
    """Referenz: <3-5% normal - nur bei gehaltenem Vokal gueltig."""
    lo, hi = 0, 20
    return lo, hi, [(0, 5 / 20, GOOD), (5 / 20, 8 / 20, WARNING), (8 / 20, 1, CRITICAL)]


def ddk_rate_zones():
    """Referenz (P12, docs/backlog.md, Literaturrecherche 2026-08-15): gesunde Erwachsene
    erreichen bei AMR ("pa"/"ta"/"ka" einzeln) 5-7 Silben/s, bei SMR ("pa-ta-ka" kombiniert)
    im Mittel 6,57 Silben/s (SD 0,84) -- Pierce et al., "Alternating and sequential motion
    rates in older adults"; oral-DDK-Studie gesunder junger Erwachsener (Jordanien, Speech
    Language and Hearing 2022). Bei zerebellaerer Ataxie in einer Studie im Mittel nur 3,20
    Silben/s vs. 5,61 Silben/s bei Kontrollen (Colorado-Dissertation zu DDK bei Ataxie) --
    deutlich reduzierte Raten sind also literaturbasiert erwartbar, keine erfundene Schwelle.
    Asymmetrisch: nur "zu langsam" wird als auffaellig markiert, keine Obergrenze (keine
    Evidenz fuer "zu schnell" als eigenstaendiges Auffaelligkeitsmuster gefunden)."""
    lo, hi = 0, 8
    return lo, hi, [(0, 4 / 8, CRITICAL), (4 / 8, 5 / 8, WARNING), (5 / 8, 1, GOOD)]


def mpt_zones():
    """Referenz (P12, Literaturrecherche 2026-08-15): MPT ca. 25-35s (Maenner) / 15-25s
    (Frauen) bei gesunden Erwachsenen, <10s allgemein als reduziert/auffaellig beschrieben
    (Iowa Head and Neck Protocols; VoiceDoctor.net; mehrere zusammenfassende Quellen).
    UNISEX-Kompromiss, da hier kein Geschlecht erfasst wird: untere (weibliche) Grenze als
    konservative "Normbereich"-Schwelle verwendet, um maennliche UND weibliche Sprecher:innen
    nicht faelschlich als auffaellig einzustufen. Nur aussagekraeftig bei dedizierter
    "so lange wie moeglich halten"-Instruktion (siehe PARAMETER_INFO-Kontext)."""
    lo, hi = 0, 40
    return lo, hi, [(0, 10 / 40, CRITICAL), (10 / 40, 15 / 40, WARNING), (15 / 40, 1, GOOD)]


def rap_zones():
    """Referenz (P12, Literaturrecherche 2026-08-15): klassischer MDVP-Normwert RAP <0,68%
    (Multi-Dimensional Voice Program, Kay Elemetrics/PENTAX). WICHTIG: MDVP und Praat liefern
    fuer dieselbe Aufnahme systematisch unterschiedliche absolute Werte (dokumentierter
    Algorithmus-Unterschied, kein Bug) -- Schwelle hier als Orientierung uebernommen, NICHT
    gegen unsere eigene Praat-Pipeline nachvalidiert. Nur bei gehaltenem Vokal gueltig."""
    lo, hi = 0, 3
    return lo, hi, [(0, 0.68 / 3, GOOD), (0.68 / 3, 1.4 / 3, WARNING), (1.4 / 3, 1, CRITICAL)]


def ppq5_zones():
    """Referenz (P12, Literaturrecherche 2026-08-15): klassischer MDVP-Normwert PPQ5 <0,84%.
    Gleicher MDVP-vs-Praat-Vorbehalt wie bei RAP (siehe rap_zones())."""
    lo, hi = 0, 3
    return lo, hi, [(0, 0.84 / 3, GOOD), (0.84 / 3, 1.7 / 3, WARNING), (1.7 / 3, 1, CRITICAL)]


def apq11_zones():
    """Referenz (P12, Literaturrecherche 2026-08-15): klassischer MDVP-Normwert APQ11 <3,07%.
    Gleicher MDVP-vs-Praat-Vorbehalt wie bei RAP (siehe rap_zones())."""
    lo, hi = 0, 15
    return lo, hi, [(0, 3.07 / 15, GOOD), (3.07 / 15, 6 / 15, WARNING), (6 / 15, 1, CRITICAL)]


def cpps_zones():
    """Referenz (P12, Literaturrecherche 2026-08-15), Praat-spezifisch (passend zu unserer
    eigenen Pipeline, anders als die MDVP-Werte oben): Cutoff 14,45dB fuer gehaltenen Vokal
    /a/ (94,5% Trennschaerfe gesund/dysphon, Praat-Analyse) -- Quelle: "Cepstral Peak
    Prominence Values for Clinical Voice Evaluation", ASHA/PMC 2020/2021.
    **WICHTIGER VORBEHALT**: dieselbe Quelle nennt fuer Fliessprache (Rainbow Passage, Praat)
    einen NIEDRIGEREN Cutoff von 9,33dB -- CPPS bei gehaltenem Vokal liegt systematisch hoeher
    als bei Fliessprache. Diese Zone nutzt den VOKAL-Cutoff (14,45dB), da CPPS hier primaer im
    Vokalisation-Modul gezeigt wird. **Bei Fliessprache (Vorlesen/Spontansprache/DDK) faellt
    der Wert dadurch systematisch "strenger" aus als literaturbasiert gerechtfertigt** -- ein
    Wert zwischen 9-14dB bei einer Lesetext-/Spontansprache-Aufnahme ist NICHT zwingend
    auffaellig, auch wenn die Kachel "grenzwertig"/"auffaellig" zeigt. Explizit im
    PARAMETER_INFO-Kontext dokumentiert, damit das nicht verloren geht."""
    lo, hi = 0, 20
    return lo, hi, [(0, 9.33 / 20, CRITICAL), (9.33 / 20, 14.45 / 20, WARNING), (14.45 / 20, 1, GOOD)]


def voice_breaks_zones():
    """Referenz (Bucket H, docs/backlog.md, Nutzer-Feedback 2026-08-15): Praat-Dokumentation
    nennt den Normativwert fuer unstimmhafte Frames bei gehaltenem Vokal als 0% -- gesunde
    Stimmen sollten die Stimmgebung praktisch luekenlos halten koennen. KEIN publizierter
    graduierter Cutoff mit Sensitivitaet/Spezifitaet gefunden -- Grenzen hier bewusst PRAGMATISCH
    und grosszuegig gewaehlt (nicht wie RAP/PPQ5/APQ11 aus einer zitierbaren Einzelquelle),
    NUR bei gehaltenem Vokal aussagekraeftig (siehe PARAMETER_INFO-Kontext)."""
    lo, hi = 0, 30
    return lo, hi, [(0, 2 / 30, GOOD), (2 / 30, 10 / 30, WARNING), (10 / 30, 1, CRITICAL)]


def clipping_zones():
    """Faustregel, NICHT literaturbasiert (anders als Jitter/HNR/etc.) -- reine technische
    Heuristik, siehe docs/backlog.md "Konzept: Design-Bereinigung", Baustein B."""
    lo, hi = 0, 5
    return lo, hi, [(0, 0.1, GOOD), (0.1, 0.5 / 5, WARNING), (0.5 / 5, 1, CRITICAL)]


def snr_zones():
    """Faustregel aus allgemeiner Signalverarbeitung, keine stimmklinische Referenz."""
    lo, hi = 0, 40
    return lo, hi, [(0, 15 / 40, CRITICAL), (15 / 40, 25 / 40, WARNING), (25 / 40, 1, GOOD)]


def verdict_for_value(value: float, lo: float, hi: float, zones: list[tuple[float, float, str]]) -> tuple[str, str]:
    """Liefert (Farbe, Label) fuer den Zonenbereich, in dem `value` liegt."""
    frac = max(0.0, min(1.0, (value - lo) / (hi - lo)))
    for f0, f1, color in zones:
        if f0 <= frac <= f1:
            if color == GOOD:
                return color, "im Normbereich"
            if color == WARNING:
                return color, "grenzwertig"
            return color, "auffällig"
    return NEUTRAL, "unbekannt"


_COLOR_TO_ZONE = {GOOD: "success", WARNING: "warning", CRITICAL: "danger"}


def zone_for_value(value: float, lo: float, hi: float, zones: list[tuple[float, float, str]]) -> str:
    """Wie verdict_for_value(), liefert aber den maschinenlesbaren Zonen-Key
    ('success'/'warning'/'danger'/'neutral') statt Hex-Farbe+Klartext -- fuer core/shared.py::
    kpi_tile()."""
    color, _ = verdict_for_value(value, lo, hi, zones)
    return _COLOR_TO_ZONE.get(color, "neutral")


def _fmt_num(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s else "0"


def good_zone_bounds(lo: float, hi: float, zones: list[tuple[float, float, str]]) -> tuple[float | None, float | None]:
    """Liefert die absoluten (abs_lo, abs_hi)-Grenzen der GOOD-Zone(n) -- die numerische
    Grundlage fuer good_range_text() (Anzeigetext) UND core/plots.py::perturbation_bundle_figure()
    (Referenzlinie im Diagramm), damit beide garantiert denselben Cutoff verwenden. `None, None`
    wenn keine GOOD-Zone existiert."""
    good_segments = [(f0, f1) for f0, f1, color in zones if color == GOOD]
    if not good_segments:
        return None, None
    f0 = min(seg[0] for seg in good_segments)
    f1 = max(seg[1] for seg in good_segments)
    return lo + f0 * (hi - lo), lo + f1 * (hi - lo)


def good_range_text(lo: float, hi: float, zones: list[tuple[float, float, str]], unit: str) -> str | None:
    """Baut den "Normbereich"-Anzeigetext aus den tatsaechlichen GOOD-Zonengrenzen -- NICHT aus
    lo/hi (das ist nur die Gauge-Achse, siehe Docstring oben in diesem Modul). Bugfix
    2026-08-16 (Nutzer-Feedback): vorher zeigte die Normbereich-Spalte lo-hi an (z.B. "0-30%"
    bei Voice Breaks), waehrend der tatsaechliche Cutoff fuer "im Normbereich" viel enger war
    (hier: <=2%) -- ein Wert wie 12% wurde dadurch als "auffaellig" gewertet, obwohl er
    innerhalb des angezeigten Bereichs lag. Diese Funktion liest die GOOD-Zone(n) direkt aus
    denselben zones-Tupeln, die auch verdict_for_value()/zone_for_value() auswerten, damit
    Text und Bewertung nie wieder auseinanderlaufen koennen."""
    abs_lo, abs_hi = good_zone_bounds(lo, hi, zones)
    if abs_lo is None:
        return None
    # f0/f1 nochmal aus den Bounds zurueckrechnen, um touches_left/right zu bestimmen (ohne
    # good_zone_bounds() erneut die rohen Fraktionen exponieren zu muessen).
    f0 = (abs_lo - lo) / (hi - lo) if hi != lo else 0
    f1 = (abs_hi - lo) / (hi - lo) if hi != lo else 1
    unit_suffix = f" {unit}" if unit else ""
    touches_left = f0 <= 1e-9
    touches_right = f1 >= 1 - 1e-9
    if touches_left and not touches_right:
        return f"≤{_fmt_num(abs_hi)}{unit_suffix}"
    if touches_right and not touches_left:
        return f"≥{_fmt_num(abs_lo)}{unit_suffix}"
    return f"{_fmt_num(abs_lo)}–{_fmt_num(abs_hi)}{unit_suffix}"
