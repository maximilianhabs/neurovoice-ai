"""Geschlechtsschaetzung aus der Stimme (Nutzer-Wunsch 2026-08-17, Hintergrundrecherche siehe
docs/literatur_review.md "Perspektivische Zusatzparameter" -- Geschlechtserkennung hat dort mit
92-99% Genauigkeit in Studien die mit Abstand solideste Evidenzlage der drei dort geprueften
Zukunfts-Parameter (Geschlecht/Alter/Nervositaet), F0 ist laut Literatur der staerkste
Einzelpraediktor.

BEWUSST NUR F0-basiert (v1) -- keine Formant-Kombination, obwohl Formanten laut Literatur die
Genauigkeit weiter verbessern wuerden. Grund: F0 ist vokal-UNABHAENGIG vergleichbar (funktioniert
gleich fuer /a/, /i/, /u/), Formanten dagegen sind stark vokalspezifisch (F1/F2 von /a/ und /i/
unterscheiden sich um den Faktor 2-3 -- eine belastbare Formant-Normalisierung ueber
unterschiedliche Vokale hinweg waere ein eigenes, groesseres Vorhaben). Spaetere Erweiterung um
Formant-Kombination moeglich, siehe docs/backlog.md.

WICHTIGE EINORDNUNG (Projektprinzip "ehrlich ueber die Grenzen der Methode", siehe
docs/literatur_review.md): das ist eine literaturbasierte HEURISTIK (eigene Sigmoid-Funktion auf
publizierten F0-Referenzbereichen), kein trainiertes/validiertes ML-Modell und keine
Einzelfall-Diagnose. Funktioniert NICHT zuverlaessig bei Kindern (F0-Bereiche ueberlappen mit
Erwachsenen anders), bei manchen Trans-Stimmen, bei atypischer Anatomie, oder bei sehr kurzen/
verrauschten Aufnahmen. Wird deshalb in der UI IMMER mit einer Konfidenzangabe UND einem
Hinweistext gezeigt, nie als absolute Aussage.
"""

from __future__ import annotations

import math

# Literaturbasierte typische F0-Bereiche (docs/literatur_review.md): Maenner grob 100-146Hz,
# Frauen grob 188-221Hz. Entscheidungsgrenze = Mittelpunkt zwischen den beiden Bereichs-
# Mittelpunkten ((123+204.5)/2 ≈ 163.75, gerundet 165Hz). Skalierung (Sigmoid-Steilheit) = halber
# Abstand der beiden Bereichs-Mittelpunkte -- je weiter ein F0-Wert von der Grenze entfernt liegt,
# desto sicherer die Einordnung, symmetrisch in beide Richtungen.
_BOUNDARY_HZ = 165.0
_SCALE_HZ = 41.0

# F0-Werte ausserhalb des menschlichen Sprechstimme-Bereichs sind eher ein Mess-/Extraktions-
# Artefakt (z.B. Oktavfehler der Pitch-Erkennung) als eine echte Stimme -- dann lieber "nicht
# bestimmbar" statt einer falsch selbstsicheren Aussage.
_PLAUSIBLE_MIN_HZ = 60.0
_PLAUSIBLE_MAX_HZ = 400.0

# Nie 100% Sicherheit behaupten -- auch bei extremen F0-Werten bleibt es eine Schaetzung.
_MAX_CONFIDENCE_PCT = 97.0
_MIN_CONFIDENCE_PCT = 50.0


def estimate_voice_gender(f0_mean_hz: float | None) -> dict:
    """Schaetzt aus dem mittleren F0 einer Aufnahme, ob die Stimme eher in den literatur-
    typischen maennlichen oder weiblichen Bereich faellt, mit einer Konfidenzangabe in Prozent.

    Gibt ein dict mit `label` ("männlich"/"weiblich"/"nicht bestimmbar"),
    `confidence_pct` (float oder None) und `f0_hz` zurueck. `label="nicht bestimmbar"` bei
    fehlendem oder unplausiblem F0 (ausserhalb 60-400Hz)."""
    if f0_mean_hz is None or not (_PLAUSIBLE_MIN_HZ <= f0_mean_hz <= _PLAUSIBLE_MAX_HZ):
        return {"label": "nicht bestimmbar", "confidence_pct": None, "f0_hz": f0_mean_hz}

    # Sigmoid auf den Abstand zur Entscheidungsgrenze -- p_male=0.5 GENAU an der Grenze,
    # naehert sich 1.0 (klar maennlich) bzw. 0.0 (klar weiblich) mit wachsendem Abstand.
    distance = _BOUNDARY_HZ - f0_mean_hz
    p_male = 1.0 / (1.0 + math.exp(-distance / _SCALE_HZ))

    if p_male >= 0.5:
        label = "männlich"
        raw_confidence = p_male
    else:
        label = "weiblich"
        raw_confidence = 1.0 - p_male

    confidence_pct = min(raw_confidence * 100.0, _MAX_CONFIDENCE_PCT)
    confidence_pct = max(confidence_pct, _MIN_CONFIDENCE_PCT)

    return {"label": label, "confidence_pct": confidence_pct, "f0_hz": f0_mean_hz}
