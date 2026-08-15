"""Laborwert-Stil-Interpretation (P5, siehe docs/backlog.md "Konzept: Modul-basierte,
geführte Analyse"). Pro Parameter: Wert | Normbereich | Status | Kontext-Kommentar.

WICHTIG (Nutzer-Vorgabe 2026-08-15): Rein DESKRIPTIV, KEINE Diagnose, KEIN Score. Der
Kontext-Kommentar sagt, mit welchen Erkrankungen ein Auffälligkeitsmuster in der Literatur
ASSOZIIERT wird -- nie, dass der Wert eine Erkrankung BEDEUTET. Inhaltliche Basis:
docs/literatur_review.md, Abschnitt "Krankheits-Assoziationen je Parameter".

Für Parameter OHNE etablierten Normbereich (kein `zones_func`) wird kein Ampel-Status
vergeben, nur Wert + Kontext -- konsistent mit der bisherigen Gauge-Darstellung
(gauge_figure() zeigt dort eine informative Nadel ohne Farbwertung, siehe core/plots.py).
"""

from __future__ import annotations

from core.reference_ranges import hnr_zones, jitter_zones, shimmer_zones, speech_rate_zones, verdict_for_value

AGE_CAVEAT_JITTER_SHIMMER_HNR_F0 = (
    "F0/Jitter/Shimmer/HNR verändern sich nachweislich mit Alter und Geschlecht (z.B. "
    "Shimmer steigt bei Männern im Alter, F0 sinkt bei älteren Frauen) — der Normbereich hier "
    "ist eine allgemeine Erwachsenen-Range, noch nicht alters-/geschlechtsgebändert."
)

# Jeder Eintrag: label, unit, zones_func (oder None), context (deskriptiv), age_caveat (optional)
PARAMETER_INFO: dict[str, dict] = {
    "f0_sd_hz": {
        "label": "Monopitch (F0-Streuung)",
        "unit": "Hz",
        "zones_func": None,
        "context": (
            "Reduzierte Tonhöhenvariabilität ist ein klassisches Merkmal hypokinetischer "
            "Dysarthrie (Parkinson) — zusammen mit reduzierter Lautstärke und kurzen "
            "„Sprechschüben“. Bei ataktischer Dysarthrie eher unauffällig oder erhöht."
        ),
        "age_caveat": AGE_CAVEAT_JITTER_SHIMMER_HNR_F0,
    },
    "jitter_local_pct": {
        "label": "Jitter (local)",
        "unit": "%",
        "zones_func": jitter_zones,
        "context": (
            "Unspezifischer Dysphonie-Marker (organisch: Stimmlippenpathologie; funktionell: "
            "Stimmermüdung). In einigen Parkinson-Studien erhöht, aber wenig spezifisch. Nur "
            "bei gehaltenem Vokal zuverlässig interpretierbar."
        ),
        "age_caveat": AGE_CAVEAT_JITTER_SHIMMER_HNR_F0,
    },
    "shimmer_local_pct": {
        "label": "Shimmer (local)",
        "unit": "%",
        "zones_func": shimmer_zones,
        "context": (
            "Wie Jitter ein unspezifischer Dysphonie-Marker, nur bei gehaltenem Vokal "
            "zuverlässig interpretierbar."
        ),
        "age_caveat": AGE_CAVEAT_JITTER_SHIMMER_HNR_F0,
    },
    "hnr_mean_db": {
        "label": "HNR",
        "unit": "dB",
        "zones_func": hnr_zones,
        "context": (
            "Erniedrigter Wert = raue/behauchte Stimmqualität allgemein. Häufig beschrieben "
            "bei bulbärer/pseudobulbärer Dysarthrie (z.B. ALS) und hypokinetischer Dysarthrie "
            "(Parkinson)."
        ),
        "age_caveat": AGE_CAVEAT_JITTER_SHIMMER_HNR_F0,
    },
    "cpps_db": {
        "label": "CPPS",
        "unit": "dB",
        "zones_func": None,
        "context": (
            "Robusteres Äquivalent zu Jitter/Shimmer/HNR bei Fließsprache. In der ALS- und "
            "Parkinson-Literatur als digitaler Sprach-Biomarker diskutiert — erniedrigter "
            "Wert = auffälligere Stimmqualität."
        ),
        "age_caveat": None,
    },
    "net_speech_rate_wpm": {
        "label": "Sprechrate",
        "unit": "WPM",
        "zones_func": speech_rate_zones,
        "context": (
            "Verlangsamung ist sehr unspezifisch — kommt bei praktisch allen Dysarthrie-Typen "
            "vor (hypokinetisch, spastisch, ataktisch, bulbär) UND bei rein kognitiver "
            "Verlangsamung ohne motorische Sprechstörung. Erlaubt allein keine Typ-Zuordnung."
        ),
        "age_caveat": None,
    },
    "mean_burst_sharpness_db_s": {
        "label": "Artikulationsschärfe",
        "unit": "dB/s",
        "zones_func": None,
        "context": (
            "Reduzierte Schärfe/verlängerte Verschlussdauer erwartbar bei bulbärer/"
            "pseudobulbärer Dysarthrie (eingeschränkte Zungen-/Lippenbeweglichkeit) und "
            "generell bei ausgeprägterer Dysarthrie jeden Typs."
        ),
        "age_caveat": None,
    },
    "monoloudness_intensity_sd_db": {
        "label": "Monoloudness",
        "unit": "dB",
        "zones_func": None,
        "context": (
            "Reduzierte Lautstärke-Variabilität passt zusammen mit Monopitch zum klassischen "
            "Bild hypokinetischer Dysarthrie (Parkinson)."
        ),
        "age_caveat": None,
    },
    "ddk_rate_hz": {
        "label": "DDK-Rate",
        "unit": "Hz",
        "zones_func": None,
        "context": (
            "Reine Verlangsamung eher bei hypokinetischer/spastischer Dysarthrie. Kein "
            "etablierter Normbereich — siehe zusätzlich Regelmäßigkeit (CV) für ataktische "
            "Muster."
        ),
        "age_caveat": None,
    },
    "cycle_interval_cv": {
        "label": "DDK-Regelmäßigkeit (CV)",
        "unit": "",
        "zones_func": None,
        "context": (
            "Unregelmäßige, „stolpernde“ Silbenfolgen (hoher CV) gelten als möglicher Hinweis "
            "auf ataktische Dysarthrie (zerebelläre Störung) — reine Verlangsamung ohne "
            "Unregelmäßigkeit spricht eher für hypokinetisch/spastisch."
        ),
        "age_caveat": None,
    },
    "pause_count": {
        "label": "Pausen (Anzahl)",
        "unit": "",
        "zones_func": None,
        "context": (
            "Erhöhte Pausenzahl kann auf Wortfindungsstörungen/kognitive Verlangsamung "
            "hindeuten, ABER genauso auf verkürzte Atemreserve (z.B. bei ALS) — ohne "
            "weiteren Kontext nicht unterscheidbar."
        ),
        "age_caveat": None,
    },
}


def interpret(param_key: str, value: float | None) -> dict | None:
    """Liefert die Laborwert-Stil-Einordnung fuer einen Parameter, oder None wenn der
    Parameter hier nicht hinterlegt ist."""
    info = PARAMETER_INFO.get(param_key)
    if info is None:
        return None

    result = {
        "label": info["label"],
        "unit": info["unit"],
        "value": value,
        "range": "kein etablierter Normbereich",
        "status": "kein Normwert",
        "context": info["context"],
        "age_caveat": info["age_caveat"],
    }

    if info["zones_func"] is not None and value is not None:
        lo, hi, zones = info["zones_func"]()
        result["range"] = f"{lo:.0f}–{hi:.0f} {info['unit']}".strip()
        _, status = verdict_for_value(value, lo, hi, zones)
        result["status"] = status

    return result
