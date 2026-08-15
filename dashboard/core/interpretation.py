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

# Jeder Eintrag: label, unit, description (was der Parameter misst -- Nutzer-Vorgabe
# 2026-08-15: "Erklärung aller Parameter" direkt auf der Aufnahme-Seite), zones_func (oder
# None), context (Krankheits-Assoziation, deskriptiv), age_caveat (optional)
PARAMETER_INFO: dict[str, dict] = {
    "f0_sd_hz": {
        "label": "Monopitch (F0-Streuung)",
        "unit": "Hz",
        "description": "Wie stark die Tonhöhe über die Aufnahme schwankt (Standardabweichung der Grundfrequenz).",
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
        "description": "Wie stark die Tonhöhe von einem Stimmzyklus zum nächsten schwankt (Zyklus-zu-Zyklus-Perturbation).",
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
        "description": "Wie stark die Lautstärke von einem Stimmzyklus zum nächsten schwankt (Zyklus-zu-Zyklus-Perturbation).",
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
        "description": "Harmonics-to-Noise-Ratio — Verhältnis von klarem, harmonischem Stimmklang zu Rauschanteil. Höher = klarere Stimme.",
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
        "description": "Cepstral Peak Prominence (geglättet) — alternatives Stimmklang-Maß, funktioniert anders als Jitter/Shimmer auch bei fließender Sprache zuverlässig.",
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
        "description": "Wörter pro Minute, bezogen auf die Gesamtdauer der Aufnahme (inkl. Pausen).",
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
        "description": "Wie klar/scharf Verschlusslaute (p, t, k, b, d, g) gebildet werden — erkannt über kurze Energieeinbrüche mit anschließendem scharfem Anstieg.",
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
        "description": "Wie wenig sich die Lautstärke über eine Äußerung verändert (Standardabweichung der Intensität).",
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
        "description": "Silbenzyklen pro Sekunde beim \"pa-ta-ka\"-Sprechen — wie schnell die Silbenfolge wiederholt werden kann.",
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
        "description": "Variationskoeffizient der Zeitabstände zwischen den Silbenzyklen — wie gleichmäßig/unregelmäßig die Silbenfolge ist.",
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
        "description": "Anzahl der Sprechpausen ≥250ms, ermittelt aus den Wort-Zeitstempeln der Transkription.",
        "zones_func": None,
        "context": (
            "Erhöhte Pausenzahl kann auf Wortfindungsstörungen/kognitive Verlangsamung "
            "hindeuten, ABER genauso auf verkürzte Atemreserve (z.B. bei ALS) — ohne "
            "weiteren Kontext nicht unterscheidbar."
        ),
        "age_caveat": None,
    },
    "f1_mean_hz": {
        "label": "Formant F1",
        "unit": "Hz",
        "description": "Vokaltrakt-Resonanz, hängt vor allem mit der Zungenhöhe (offen/geschlossen) zusammen.",
        "zones_func": None,
        "context": "Kein Normwert ohne bekannte Vokal-Identität — Formanten sind hier nur als Rohwerte informativ.",
        "age_caveat": None,
    },
    "f2_mean_hz": {
        "label": "Formant F2",
        "unit": "Hz",
        "description": "Vokaltrakt-Resonanz, hängt vor allem mit der Zungenposition vorne/hinten zusammen.",
        "zones_func": None,
        "context": "Kein Normwert ohne bekannte Vokal-Identität — Formanten sind hier nur als Rohwerte informativ.",
        "age_caveat": None,
    },
    "n_phrases": {
        "label": "Intonationskontur (Phrasen)",
        "unit": "",
        "description": "Anzahl akustisch erkannter Sprechphrasen (über Pausen in der Stimmgebung abgegrenzt, kein Transkript nötig).",
        "zones_func": None,
        "context": "Kein Normwert, kleine Fallzahl pro Aufnahme — Trend pro Phrase (steigend/fallend) ist informativer als die reine Anzahl.",
        "age_caveat": None,
    },
    "ttr": {
        "label": "Lexikalische Diversität (TTR)",
        "unit": "",
        "description": "Type-Token-Ratio — Anteil unterschiedlicher Wörter an allen Wörtern im Transkript.",
        "zones_func": None,
        "context": "Kein etablierter Normbereich, sinkt allein durch Textlänge — nur im Eigenvergleich über Sitzungen sinnvoll.",
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
        "description": info["description"],
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


def flatten_take(take: dict) -> dict:
    """Fasst alle Kennwert-Gruppen eines Takes (phonation/dynamics/cpp/... je nach Modul
    unterschiedlich benannt) zu einem flachen Dict zusammen, um gegen PARAMETER_INFO zu
    suchen. Geteilt zwischen den Modul-Seiten und views/gesamtbericht.py, damit die Zuordnung
    nur an einer Stelle gepflegt werden muss."""
    flat: dict = {}
    for value in take.values():
        if isinstance(value, dict):
            flat.update(value)
    return flat


def build_rows(flat: dict) -> list[dict]:
    """Baut die Zeilen fuer eine Laborwert-Stil-Tabelle (Parameter/Wert/Normbereich/Status/
    Was es misst/Kontext) aus einem geflachten Take-Dict."""
    rows = []
    for param_key in PARAMETER_INFO:
        if param_key not in flat:
            continue
        info = interpret(param_key, flat[param_key])
        if info is None:
            continue
        value_str = f"{info['value']:.2f} {info['unit']}".strip() if info["value"] is not None else "–"
        rows.append({
            "Parameter": info["label"],
            "Wert": value_str,
            "Normbereich": info["range"],
            "Status": info["status"],
            "Was es misst": info["description"],
            "Kontext (deskriptiv)": info["context"],
        })
    return rows


def age_caveats_for(flat: dict) -> set[str]:
    """Liefert die Menge der Alters-/Geschlechts-Hinweise, die fuer die im Take vorhandenen
    Parameter relevant sind (dedupliziert, da z.B. Jitter/Shimmer/HNR denselben Hinweistext teilen)."""
    caveats = set()
    for param_key in PARAMETER_INFO:
        if param_key not in flat:
            continue
        info = interpret(param_key, flat[param_key])
        if info and info["age_caveat"]:
            caveats.add(info["age_caveat"])
    return caveats
