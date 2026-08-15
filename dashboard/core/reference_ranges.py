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
