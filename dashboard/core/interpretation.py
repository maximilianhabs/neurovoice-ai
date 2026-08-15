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

from core.reference_ranges import hnr_zones, jitter_zones, shimmer_zones, speech_rate_zones, verdict_for_value, zone_for_value

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
        "evidence": "gut etabliert",
        "literature": "Monopitch als eines der robustesten PD-Merkmale — (Dys)Prosody in Parkinson's Disease; ASHA Perspectives, siehe docs/literatur_review.md",
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
        "evidence": "gut etabliert",
        "literature": "Klassisches Stimmklinik-Maß — Vocal Acoustic Analysis: Jitter, Shimmer and HNR Parameters, siehe docs/literatur_review.md",
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
        "evidence": "gut etabliert",
        "literature": "Klassisches Stimmklinik-Maß — Vocal Acoustic Analysis: Jitter, Shimmer and HNR Parameters, siehe docs/literatur_review.md",
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
        "evidence": "gut etabliert",
        "literature": "Klassisches Stimmklinik-Maß — Vocal Acoustic Analysis: Jitter, Shimmer and HNR Parameters, siehe docs/literatur_review.md",
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
        "evidence": "in der Forschung diskutiert",
        "literature": "Als robusteres Äquivalent bei Fließsprache in ALS-/PD-Biomarker-Studien diskutiert, siehe docs/literatur_review.md \"Quellen\"",
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
        "evidence": "gut etabliert",
        "literature": "Sprechrate ist Standard-Sprechfluss-Marker, aber unspezifisch für einzelne Dysarthrie-Typen — siehe docs/literatur_review.md Abschnitt 5",
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
        "evidence": "eigene Heuristik / explorativ",
        "literature": "Projekteigene Burst-Erkennung, kein Standardmaß aus der Literatur — lose an Verschlussdauer-Konzepte angelehnt (siehe „Sprachspezifik Deutsch\" in docs/literatur_review.md)",
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
        "evidence": "gut etabliert",
        "literature": "Klassisches PD-Merkmal neben Monopitch — siehe docs/literatur_review.md Abschnitt 4",
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
        "evidence": "in der Forschung diskutiert",
        "literature": "DDK-Aufgabe selbst ist Standard-Artikulationstest, unser eigener Erkennungsalgorithmus ist NICHT unabhängig validiert — siehe docs/literatur_review.md Abschnitt 3",
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
        "evidence": "in der Forschung diskutiert",
        "literature": "Regelmäßigkeit als möglicher ataktischer Marker diskutiert, weniger standardisiert als reine DDK-Rate — siehe docs/literatur_review.md Abschnitt 3",
    },
    "n_words": {
        "label": "Wörter (erkannt)",
        "unit": "",
        "description": "Anzahl der von der Transkription erkannten Wörter.",
        "zones_func": None,
        "context": "Kein Normwert — abhängig von der freien Sprechdauer/Aufgabenstellung, nur Grundlage für die anderen Sprechrate-Kennwerte.",
        "age_caveat": None,
        "evidence": "deskriptiv, kein Krankheits-Marker",
        "literature": None,
    },
    "articulation_rate_wpm": {
        "label": "Sprechrate (Artikulation)",
        "unit": "WPM",
        "description": "Wörter pro Minute, bezogen NUR auf die Spanne von erstem bis letztem Wort (Anlauf-/Schlusspausen rausgerechnet) — filtert reine Pausenzeit raus.",
        "zones_func": None,
        "context": "Wie die Netto-Sprechrate unspezifisch für einzelne Dysarthrie-Typen — der Vergleich Netto- vs. Artikulationsrate zeigt, wie viel der Verlangsamung reine Pausenzeit ist.",
        "age_caveat": None,
        "evidence": "gut etabliert",
        "literature": "Netto- vs. Artikulationsrate ist Standardunterscheidung in der Sprechfluss-Literatur — siehe docs/literatur_review.md Abschnitt 5",
    },
    "fluency_score": {
        "label": "Flüssigkeits-Score",
        "unit": "",
        "description": "Anteil der Sprechspanne, der tatsächlich mit Sprechen (statt Pausen) gefüllt ist — 1,0 = keine nennenswerten Pausen.",
        "zones_func": None,
        "context": "Eigene, transparente Heuristik, kein etablierter klinischer Score — niedrige Werte können auf Wortfindungsstörungen, Atemreserve-Probleme oder einfach viel Bedenkzeit hindeuten, ohne dass diese Ursachen automatisiert unterscheidbar wären.",
        "age_caveat": None,
        "evidence": "eigene Heuristik / explorativ",
        "literature": "Projekteigene, transparente Definition — kein etablierter klinischer Score",
    },
    "rhythm_npvi": {
        "label": "Rhythmus (nPVI)",
        "unit": "",
        "description": "Normalisierter Pairwise Variability Index — wie unterschiedlich lang aufeinanderfolgende Wörter sind. Hoch = abwechslungsreicher Rhythmus.",
        "zones_func": None,
        "context": "Kein klinischer Normwert (eher sprachtypologisches Maß) — stark reduzierter Wert (monotoner Rhythmus) passt zum Bild hypokinetischer Dysarthrie.",
        "age_caveat": None,
        "evidence": "in der Forschung diskutiert",
        "literature": "nPVI ist ein etabliertes Rhythmus-Maß, hier aber auf Wortebene statt der ursprünglichen Silbenebene angepasst — siehe docs/literatur_review.md Abschnitt 4",
    },
    "mean_pause_duration_s": {
        "label": "Ø Pausendauer",
        "unit": "s",
        "description": "Mittlere Dauer der erkannten Sprechpausen (≥250ms).",
        "zones_func": None,
        "context": "Kein Normwert — verlängerte Pausen können auf Wortfindungsstörungen ODER verkürzte Atemreserve hindeuten, ohne weiteren Kontext nicht unterscheidbar.",
        "age_caveat": None,
        "evidence": "gut etabliert",
        "literature": "Pausenmuster (Duration of Pause Intervals) ist Standard-Sprechfluss-Marker — siehe docs/literatur_review.md Abschnitt 5",
    },
    "max_pause_duration_s": {
        "label": "Max. Pausendauer",
        "unit": "s",
        "description": "Längste einzelne erkannte Sprechpause in der Aufnahme.",
        "zones_func": None,
        "context": "Kein Normwert — eine einzelne sehr lange Pause kann ein Ausreißer (z.B. Räuspern, Nachdenkpause) oder Hinweis auf Wortfindungsstörung sein.",
        "age_caveat": None,
        "evidence": "eigene Heuristik / explorativ",
        "literature": "Einzelwert-Ableitung, kein eigenständiges Standardmaß in der Literatur",
    },
    "micro_pause_count": {
        "label": "Mikropausen (250–500ms)",
        "unit": "",
        "description": "Anzahl kürzerer Pausen — meist normale Atem-/Wortgrenzen.",
        "zones_func": None,
        "context": "Kein Normwert — dient vor allem als Kontrast zu den Makropausen, um zu sehen, ob Pausen überwiegend unauffällig kurz oder auffällig lang sind.",
        "age_caveat": None,
        "evidence": "eigene Heuristik / explorativ",
        "literature": "Projekteigene Schwellenwert-Kategorisierung (500ms-Grenze), keine etablierte Konvention",
    },
    "macro_pause_count": {
        "label": "Makropausen (≥500ms)",
        "unit": "",
        "description": "Anzahl längerer Pausen — eher auffällige Zögerungen/Wortsuche als normale Atemgrenzen.",
        "zones_func": None,
        "context": "Kein Normwert — erhöhte Anzahl kann auf Wortfindungsstörungen/kognitive Verlangsamung hindeuten, aber auch auf verkürzte Atemreserve, ohne weiteren Kontext nicht unterscheidbar.",
        "age_caveat": None,
        "evidence": "eigene Heuristik / explorativ",
        "literature": "Projekteigene Schwellenwert-Kategorisierung (500ms-Grenze), keine etablierte Konvention",
    },
    "mean_micro_pause_duration_s": {
        "label": "Ø Mikropausendauer",
        "unit": "s",
        "description": "Mittlere Dauer der kürzeren Pausen (250–500ms).",
        "zones_func": None,
        "context": "Kein Normwert — nur ergänzend zur Mikropausen-Anzahl.",
        "age_caveat": None,
        "evidence": "eigene Heuristik / explorativ",
        "literature": "Ergänzt die Mikropausen-Anzahl, keine eigenständige Literatur-Referenz",
    },
    "mean_macro_pause_duration_s": {
        "label": "Ø Makropausendauer",
        "unit": "s",
        "description": "Mittlere Dauer der längeren Pausen (≥500ms).",
        "zones_func": None,
        "context": "Kein Normwert — nur ergänzend zur Makropausen-Anzahl.",
        "age_caveat": None,
        "evidence": "eigene Heuristik / explorativ",
        "literature": "Ergänzt die Makropausen-Anzahl, keine eigenständige Literatur-Referenz",
    },
    "mean_word_duration_s": {
        "label": "Ø Wortdauer",
        "unit": "s",
        "description": "Mittlere Dauer eines erkannten Wortes (aus den Wort-Zeitstempeln der Transkription).",
        "zones_func": None,
        "context": "Kein etablierter Normbereich — verlängerte Wortdauern können auf verlangsamte Artikulation hindeuten, aber auch durch lange/zusammengesetzte Wörter allein entstehen.",
        "age_caveat": None,
        "evidence": "eigene Heuristik / explorativ",
        "literature": "Direkt aus den Wort-Zeitstempeln abgeleitet, kein etablierter klinischer Referenzwert",
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
        "evidence": "gut etabliert",
        "literature": "Pausenzahl ist Standard-Sprechfluss-Marker — siehe docs/literatur_review.md Abschnitt 5",
    },
    "f1_mean_hz": {
        "label": "Formant F1",
        "unit": "Hz",
        "description": "Vokaltrakt-Resonanz, hängt vor allem mit der Zungenhöhe (offen/geschlossen) zusammen.",
        "zones_func": None,
        "context": "Kein Normwert ohne bekannte Vokal-Identität — Formanten sind hier nur als Rohwerte informativ.",
        "age_caveat": None,
        "evidence": "deskriptiv, kein Krankheits-Marker",
        "literature": "Formant-Rohwert — Zuordnung F1↔Zungenhöhe ist etabliert (siehe docs/literatur_review.md Abschnitt 2), aber ohne bekannte Vokal-Identität hier nur informativ",
    },
    "f2_mean_hz": {
        "label": "Formant F2",
        "unit": "Hz",
        "description": "Vokaltrakt-Resonanz, hängt vor allem mit der Zungenposition vorne/hinten zusammen.",
        "zones_func": None,
        "context": "Kein Normwert ohne bekannte Vokal-Identität — Formanten sind hier nur als Rohwerte informativ.",
        "age_caveat": None,
        "evidence": "deskriptiv, kein Krankheits-Marker",
        "literature": "Formant-Rohwert — Zuordnung F2↔Zungenposition ist etabliert (siehe docs/literatur_review.md Abschnitt 2), aber ohne bekannte Vokal-Identität hier nur informativ",
    },
    "f1_iqr_hz": {
        "label": "Formant-Streuung F1",
        "unit": "Hz",
        "description": "Wie stark F1 über die Aufnahme hinweg streut (Interquartilsabstand) — Proxy für den genutzten Artikulationsraum, kein Ersatz für eine echte Vokalraum-Fläche.",
        "zones_func": None,
        "context": (
            "Schmale Streuung KANN auf Zentralisierung/eingeschränkte Zungenbeweglichkeit "
            "hindeuten, ist aber kein direkter Ersatz für die klassische Vokalraum-Fläche "
            "(VSA, siehe Vokalisation-Modul) — nur ein zeitaufgelöster Näherungswert, der "
            "ohne bekannte Vokal-Identität auskommt."
        ),
        "age_caveat": None,
        "evidence": "in der Forschung diskutiert",
        "literature": "Formant-Streuung als VSA-Proxy — echte Vokalraum-Flächenmaße sind laut Literatur uneinheitlich validiert (siehe docs/literatur_review.md Punkt 2 der Einschränkungen), unsere zeitaufgelöste Variante ist eigene Anpassung",
    },
    "f2_iqr_hz": {
        "label": "Formant-Streuung F2",
        "unit": "Hz",
        "description": "Wie stark F2 über die Aufnahme hinweg streut (Interquartilsabstand) — Proxy für den genutzten Artikulationsraum, kein Ersatz für eine echte Vokalraum-Fläche.",
        "zones_func": None,
        "context": (
            "Wie bei F1: schmale Streuung KANN auf Zentralisierung hindeuten, ist aber kein "
            "direkter Ersatz für die klassische Vokalraum-Fläche (VSA) — F2 reagiert vor "
            "allem auf die Zungenposition vorne/hinten."
        ),
        "age_caveat": None,
        "evidence": "in der Forschung diskutiert",
        "literature": "Formant-Streuung als VSA-Proxy — echte Vokalraum-Flächenmaße sind laut Literatur uneinheitlich validiert (siehe docs/literatur_review.md Punkt 2 der Einschränkungen), unsere zeitaufgelöste Variante ist eigene Anpassung",
    },
    "n_phrases": {
        "label": "Intonationskontur (Phrasen)",
        "unit": "",
        "description": "Anzahl akustisch erkannter Sprechphrasen (über Pausen in der Stimmgebung abgegrenzt, kein Transkript nötig).",
        "zones_func": None,
        "context": "Kein Normwert, kleine Fallzahl pro Aufnahme — Trend pro Phrase (steigend/fallend) ist informativer als die reine Anzahl.",
        "age_caveat": None,
        "evidence": "deskriptiv, kein Krankheits-Marker",
        "literature": None,
    },
    "ttr": {
        "label": "Lexikalische Diversität (TTR)",
        "unit": "",
        "description": "Type-Token-Ratio — Anteil unterschiedlicher Wörter an allen Wörtern im Transkript.",
        "zones_func": None,
        "context": "Kein etablierter Normbereich, sinkt allein durch Textlänge — nur im Eigenvergleich über Sitzungen sinnvoll.",
        "age_caveat": None,
        "evidence": "gut etabliert",
        "literature": "TTR ist ein etabliertes linguistisches Diversitätsmaß, aber ohne krankheitsspezifischen Cutoff — nur im Eigenvergleich sinnvoll",
    },
    "mtld": {
        "label": "Lexikalische Diversität (MTLD)",
        "unit": "",
        "description": "Measure of Textual Lexical Diversity — misst lexikalische Vielfalt textlängen-robuster als die reine TTR.",
        "zones_func": None,
        "context": "Kein etablierter Normbereich — wurde ursprünglich für deutlich längere Texte entwickelt als unsere kurzen Aufnahmen, hier nur eingeschränkt aussagekräftig.",
        "age_caveat": None,
        "evidence": "gut etabliert",
        "literature": "MTLD (McCarthy & Jarvis 2010) ist ein etabliertes, textlängen-robusteres Diversitätsmaß, aber für deutlich längere Texte entwickelt als unsere Aufnahmen",
    },
    # --- P7/Audit 2026-08-15 (docs/backlog.md "Audit-Parameter einbauen") ---
    "jitter_rap_pct": {
        "label": "Jitter (RAP)",
        "unit": "%",
        "description": "3-Punkt-Periodenperturbation — wie Jitter (local), aber über 3 benachbarte Zyklen geglättet, dadurch robuster gegen einzelne Ausreißer-Zyklen.",
        "zones_func": None,
        "context": (
            "Wie Jitter (local) ein unspezifischer Dysphonie-Marker, nur bei gehaltenem Vokal "
            "zuverlässig interpretierbar. Kein projektintern verifizierter Cutoff hinterlegt "
            "(siehe docs/backlog.md P12) — nur Rohwert, keine Ampel."
        ),
        "age_caveat": AGE_CAVEAT_JITTER_SHIMMER_HNR_F0,
        "evidence": "gut etabliert",
        "literature": "RAP als Jitter-Untermaß ist Teil der klassischen MDVP-Konvention, aber hier ohne projektintern verifizierten Cutoff — siehe docs/backlog.md P12",
    },
    "jitter_ppq5_pct": {
        "label": "Jitter (PPQ5)",
        "unit": "%",
        "description": "5-Punkt-Periodenperturbation — wie RAP, aber über 5 benachbarte Zyklen geglättet.",
        "zones_func": None,
        "context": (
            "Wie Jitter (local)/RAP ein unspezifischer Dysphonie-Marker, nur bei gehaltenem "
            "Vokal zuverlässig interpretierbar. Kein projektintern verifizierter Cutoff "
            "hinterlegt (siehe docs/backlog.md P12) — nur Rohwert, keine Ampel."
        ),
        "age_caveat": AGE_CAVEAT_JITTER_SHIMMER_HNR_F0,
        "evidence": "gut etabliert",
        "literature": "PPQ5 als Jitter-Untermaß ist Teil der klassischen MDVP-Konvention, aber hier ohne projektintern verifizierten Cutoff — siehe docs/backlog.md P12",
    },
    "shimmer_apq11_pct": {
        "label": "Shimmer (APQ11)",
        "unit": "%",
        "description": "11-Punkt-Amplitudenperturbation — wie Shimmer (local), aber über 11 benachbarte Zyklen geglättet, dadurch robuster gegen einzelne Ausreißer-Zyklen.",
        "zones_func": None,
        "context": (
            "Wie Shimmer (local) ein unspezifischer Dysphonie-Marker, nur bei gehaltenem Vokal "
            "zuverlässig interpretierbar. Kein projektintern verifizierter Cutoff hinterlegt "
            "(siehe docs/backlog.md P12) — nur Rohwert, keine Ampel."
        ),
        "age_caveat": AGE_CAVEAT_JITTER_SHIMMER_HNR_F0,
        "evidence": "gut etabliert",
        "literature": "APQ11 als Shimmer-Untermaß ist Teil der klassischen MDVP-Konvention, aber hier ohne projektintern verifizierten Cutoff — siehe docs/backlog.md P12",
    },
    "mpt_s": {
        "label": "Maximum Phonation Time (MPT)",
        "unit": "s",
        "description": "Längste zusammenhängende stimmhafte Passage in der Aufnahme — klassisches Stimm-/Atemreserve-Maß.",
        "zones_func": None,
        "context": (
            "Reduzierte MPT gilt als Hinweis auf eingeschränkte Atem-/Stimmbandfunktion, z.B. "
            "bei ALS/bulbären Erkrankungen. Nur aussagekräftig, wenn gezielt „so lange wie "
            "möglich halten“ instruiert wurde — bei kurzen Standard-Vokalaufnahmen ist der Wert "
            "nur die aufgenommene Dauer, nicht die tatsächliche maximale Phonationsdauer."
        ),
        "age_caveat": None,
        "evidence": "gut etabliert",
        "literature": "MPT ist ein klassisches klinisches Stimm-/Atemreserve-Maß, hier aber ohne dedizierte MPT-Aufnahme-Instruktion nur eingeschränkt aussagekräftig",
    },
    "tremor_freq_hz": {
        "label": "F0-Tremor-Frequenz",
        "unit": "Hz",
        "description": "Dominante Oszillationsfrequenz der Tonhöhen-Kontur im 3–15Hz-Band (Spektralanalyse der F0-Zeitreihe, nicht des Rohsignals).",
        "zones_func": None,
        "context": (
            "Physiologischer/pathologischer Stimmtremor liegt typischerweise bei 4-12Hz — in "
            "der Literatur als Ansatzpunkt zur Differenzierung Parkinson- vs. essenzieller "
            "Tremor diskutiert. Rein explorativ, nicht klinisch validiert, keine automatische "
            "Tremor-Diagnose. Bei kurzen Vokalaufnahmen (~2-3s) ist die Frequenzauflösung grob."
        ),
        "age_caveat": None,
        "evidence": "eigene Heuristik / explorativ",
        "literature": "Rein explorative Spektralanalyse, nicht klinisch validiert — Grundidee (Tremor-Differenzierung PD vs. essenziell) aus der Literatur, konkrete Umsetzung hier eigenständig",
    },
    "vsa_hz2": {
        "label": "Vokalraum-Fläche (VSA)",
        "unit": "Hz²",
        "description": "Fläche des Dreiecks aus den Formant-Mittelwerten (F1/F2) der drei Eckvokale /a/, /i/, /u/ — klassisches Maß für den genutzten Artikulationsraum.",
        "zones_func": None,
        "context": (
            "Kleinere Fläche = stärker zentralisierter Vokalraum, gilt in der Literatur als "
            "möglicher Hinweis auf Artikulationsundeutlichkeit/Dysarthrie. Kein projektintern "
            "verifizierter Cutoff hinterlegt (siehe docs/backlog.md P12) — braucht alle 3 "
            "Vokal-Teilaufgaben mit mindestens einem Versuch."
        ),
        "age_caveat": None,
        "evidence": "in der Forschung diskutiert",
        "literature": "Klassische VSA-Dreiecksformel, aber laut Literatur uneinheitlich validiert (hohe Sprecher-zu-Sprecher-Varianz) — siehe docs/literatur_review.md Punkt 2 der Einschränkungen",
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
        "zone": "neutral",
        "context": info["context"],
        "age_caveat": info["age_caveat"],
        "evidence": info["evidence"],
        "literature": info["literature"],
    }

    if info["zones_func"] is not None and value is not None:
        lo, hi, zones = info["zones_func"]()
        result["range"] = f"{lo:.0f}–{hi:.0f} {info['unit']}".strip()
        _, status = verdict_for_value(value, lo, hi, zones)
        result["status"] = status
        result["zone"] = zone_for_value(value, lo, hi, zones)

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
    """Baut die Zeilen fuer die KOMPAKTE Laborwert-Stil-Uebersicht (Parameter/Wert/
    Normbereich/Status) aus einem geflachten Take-Dict -- bewusst OHNE die langen Erklaerungs-/
    Kontexttexte (P11, docs/backlog.md "Kompakte Uebersicht + ausfuehrliches Evidenz-Glossar
    trennen"). Die ausfuehrliche Fassung mit Erklaerung/Kontext/Evidenz/Literatur liefert
    build_glossary_entries()."""
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
        })
    return rows


def build_glossary_entries(flat: dict) -> list[dict]:
    """Baut die ausfuehrlichen Glossar-Eintraege (P11) fuer alle im Take vorhandenen Parameter:
    Label, "Was es misst", Kontext (deskriptiv), Evidenz-Einordnung, Literaturverweis. Getrennt
    von build_rows() (kompakte Uebersicht), damit die kompakte Tabelle nicht wieder mit langen
    Texten ueberladen wird (Nutzer-Feedback 2026-08-15 zur vorherigen Tabellen-Version)."""
    entries = []
    for param_key in PARAMETER_INFO:
        if param_key not in flat:
            continue
        info = interpret(param_key, flat[param_key])
        if info is None:
            continue
        entries.append({
            "label": info["label"],
            "description": info["description"],
            "context": info["context"],
            "evidence": info["evidence"],
            "literature": info["literature"],
            "age_caveat": info["age_caveat"],
        })
    return entries


def build_tiles(flat: dict) -> list[dict]:
    """Baut die Kachel-Daten (Baustein A, docs/backlog.md "Konzept: Design-Bereinigung") fuer
    die "Auf-einen-Blick"-Ansicht direkt auf der Modul-Seite -- dieselbe Datengrundlage wie
    build_rows(), nur kompakt fuer core/shared.py::kpi_tile() statt einer Tabellenzeile."""
    tiles = []
    for param_key in PARAMETER_INFO:
        if param_key not in flat:
            continue
        info = interpret(param_key, flat[param_key])
        if info is None:
            continue
        value_text = f"{info['value']:.2f} {info['unit']}".strip() if info["value"] is not None else "–"
        tiles.append({
            "label": info["label"],
            "value_text": value_text,
            "sub_text": info["status"],
            "zone": info["zone"],
            "description": info["description"],
        })
    return tiles


