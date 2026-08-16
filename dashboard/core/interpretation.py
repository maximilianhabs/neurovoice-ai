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

from core.reference_ranges import (
    apq11_zones,
    cpps_zones,
    ddk_rate_zones,
    good_range_text,
    hnr_zones,
    jitter_zones,
    mpt_zones,
    ppq5_zones,
    rap_zones,
    shimmer_zones,
    speech_rate_zones,
    verdict_for_value,
    voice_breaks_zones,
    zone_for_value,
)

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
            "„Sprechschüben“. Bei ataktischer Dysarthrie eher unauffällig oder erhöht. "
            "**P12-Recherche 2026-08-15**: normative Datensätze für Fließsprache berichten "
            "SD-Werte grob im Bereich 12-40Hz (starke Streuung je nach Studie/Sprecher:in) — "
            "bei gehaltenem Vokal ist die SD naturgemäß VIEL kleiner (Zielton wird bewusst "
            "gehalten). Bewusst KEINE Ampel: kein einzelner, klar zitierbarer Cutoff mit "
            "Sensitivität/Spezifität gefunden, nur eine grobe Sekundärquellen-Orientierung."
        ),
        "age_caveat": AGE_CAVEAT_JITTER_SHIMMER_HNR_F0,
        "evidence": "gut etabliert",
        "literature": "Monopitch als eines der robustesten PD-Merkmale — (Dys)Prosody in Parkinson's Disease; ASHA Perspectives. F0SD-Grobbereich 12-40Hz: voicescience.org-Zusammenfassung normativer Datensätze",
        "typical_values": (
            "Richtung gut belegt, konkrete Hz-Zahl bewusst nicht behauptet: Gesunde zeigen in "
            "Vergleichsstudien eine SIGNIFIKANT HÖHERE F0-Variabilität als Parkinson-"
            "Patient:innen (Skodda et al. 2011, Journal of Voice, F0-Variabilität in "
            "Fließsprache ON/OFF-Levodopa vs. Kontrollen; Sci Rep 2020, 10:12237, Parkinson-"
            "Dysarthrie-Kohorte). Bei ataktischer Dysarthrie eher unauffällig/erhöht statt "
            "reduziert (Gegenrichtung zu Parkinson) — kein einheitliches Bild über alle "
            "Dysarthrie-Typen."
        ),
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
        "literature": "Klassischer Praat-Normwert 1,04% (Boersma & Weenink, Praat-Dokumentation „Voice report“); Erhöhung bei Parkinson-Dysarthrie u.a. bei Rusz et al. 2011, J Acoust Soc Am 129(1), und Sci Rep 2020, 10:12237",
        "typical_values": (
            "Gesunde/klinisch unauffällige Stimmen: <1,04% (Praats etablierter "
            "Normalitäts-Schwellenwert). Bei Dysarthrie (u.a. Parkinson) in mehreren Studien "
            "im Mittel erhöht — konkrete Zahlenspannen variieren stark je nach Studie, "
            "Sprachaufgabe und Analyse-Software (Praat vs. MDVP liefern systematisch "
            "unterschiedliche absolute Werte, siehe Kontext oben), deshalb hier keine einzelne "
            "„typische“ Patientenzahl behauptet."
        ),
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
        "literature": "Klassischer Praat-Normwert 3,81% (Boersma & Weenink, Praat-Dokumentation „Voice report“); allgemeine Spanne 3-7% je nach Population/Aufnahmequalität, siehe „Reliable Jitter and Shimmer Measurements in Voice Clinics“ (Journal of Voice)",
        "typical_values": (
            "Gesunde/klinisch unauffällige Stimmen: <3,81% (Praats etablierter "
            "Normalitäts-Schwellenwert), teils auch 3-7% als allgemeine Spanne berichtet. Bei "
            "Dysarthrie im Mittel erhöht, wie bei Jitter keine einzelne verlässliche "
            "„typische“ Patientenzahl über alle Studien/Methoden hinweg."
        ),
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
        "literature": "Erniedrigt bei Dysarthrie/Dysphonie allgemein — Vocal Acoustic Analysis: Jitter, Shimmer and HNR Parameters, siehe docs/literatur_review.md; für Parkinson-Dysarthrie u.a. Rusz et al. 2011, J Acoust Soc Am 129(1); Sci Rep 2020, 10:12237",
        "typical_values": (
            "Kein einzelner publizierter „typischer“ Patientenwert gefunden — Studien "
            "bestätigen konsistent NIEDRIGERE HNR-Werte bei Dysarthrie/Dysphonie (u.a. "
            "Parkinson) im Vergleich zu Gesunden, ohne einheitliche absolute Vergleichszahl "
            "über verschiedene Studien/Aufnahmebedingungen hinweg."
        ),
    },
    "cpps_db": {
        "label": "CPPS",
        "unit": "dB",
        "description": "Cepstral Peak Prominence (geglättet) — alternatives Stimmklang-Maß, funktioniert anders als Jitter/Shimmer auch bei fließender Sprache zuverlässig.",
        "zones_func": cpps_zones,
        "context": (
            "Robusteres Äquivalent zu Jitter/Shimmer/HNR bei Fließsprache. In der ALS- und "
            "Parkinson-Literatur als digitaler Sprach-Biomarker diskutiert — erniedrigter "
            "Wert = auffälligere Stimmqualität. **P12-Nachtrag**: Normbereich (14,45dB-Cutoff, "
            "Praat) stammt aus Untersuchungen an GEHALTENEN VOKALEN — bei Fließsprache "
            "(Vorlesen/Spontansprache/DDK) liegt der literaturbasierte Cutoff niedriger "
            "(~9,33dB, dieselbe Quelle). Ein Wert zwischen 9-14dB bei einer Lesetext-/"
            "Spontansprache-Aufnahme ist NICHT zwingend auffällig, auch wenn die Ampel hier "
            "„grenzwertig“ zeigt — siehe core/reference_ranges.py::cpps_zones() für Details."
        ),
        "age_caveat": None,
        "evidence": "in der Forschung diskutiert",
        "literature": "Cepstral Peak Prominence Values for Clinical Voice Evaluation (ASHA/PMC, Praat-Cutoffs 14,45dB Vokal / 9,33dB Fließsprache); für Parkinson-Dysarthrie zusätzlich „Analysis of Smooth Cepstral Peak Prominence in Hypokinetic Dysarthria Associated With Parkinson's Disease“ (De Gruyter, 2024)",
        "typical_values": (
            "Kein einzelner publizierter Patientenwert als „typisch“ behauptet — mehrere "
            "Studien bestätigen konsistent NIEDRIGERE CPPS-Werte bei Parkinson-Dysarthrie im "
            "Vergleich zu Gesunden, sowohl bei gehaltenem Vokal als auch bei Fließsprache "
            "(Fließsprache zeigte in einer Studie die stärkere Trennschärfe zwischen Gruppen)."
        ),
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
        "literature": "Sprechrate ist Standard-Sprechfluss-Marker, aber unspezifisch für einzelne Dysarthrie-Typen — siehe docs/literatur_review.md Abschnitt 5; zu Depression/psychomotorischer Verlangsamung u.a. Sanchez et al., Depression und Sprechrate; zu Parkinson u.a. De Letter et al., „Speech rate in Parkinson's disease: A controlled study“ (Neurología, 2016), 39 PD vs. 45 Kontrollen",
        "typical_values": (
            "Uneinheitliches Bild, bewusst kein einzelner Zahlenwert behauptet: bei "
            "Depression/psychomotorischer Verlangsamung im Mittel nur GERING reduziert (Studien "
            "berichten einen Unterschied in der Größenordnung von ~5 WPM gegenüber Nicht-"
            "Depressiven — deutlich subtiler, als man intuitiv erwarten würde). Bei Parkinson "
            "in kontrollierten Studien meist reduzierte Sprech-/Artikulationsrate, ABER "
            "einzelne Studien berichten auch eine paradox ERHÖHTE Vorlese-Geschwindigkeit bei "
            "einem Teil der Betroffenen („Festination“ der Sprache, analog zum Gangbild) — "
            "Richtung ist also nicht bei allen Patient:innen gleich, ein einzelner „typischer“ "
            "WPM-Wert wäre irreführend."
        ),
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
            "Bild hypokinetischer Dysarthrie (Parkinson). **P12-Recherche 2026-08-15**: gezielt "
            "nach einem publizierten Intensitäts-SD-Normbereich gesucht — nur allgemeine "
            "Sprachlautstärke-Pegel (60-65dB in 1m Abstand) gefunden, KEIN spezifischer "
            "SD-über-eine-Äußerung-Cutoff. Bewusst weiterhin ohne Ampel."
        ),
        "age_caveat": None,
        "evidence": "gut etabliert",
        "literature": "Klassisches PD-Merkmal neben Monopitch — siehe docs/literatur_review.md Abschnitt 4. Kein spezifischer SD-Cutoff in der Recherche gefunden.",
    },
    "ddk_rate_hz": {
        "label": "DDK-Rate",
        "unit": "Hz",
        "description": "Silbenzyklen pro Sekunde beim \"pa-ta-ka\"-Sprechen — wie schnell die Silbenfolge wiederholt werden kann.",
        "zones_func": ddk_rate_zones,
        "context": (
            "Reine Verlangsamung eher bei hypokinetischer/spastischer Dysarthrie. **P12**: "
            "Normbereich 5-8Hz aus Literaturwerten gesunder Erwachsener (5-7 Silben/s "
            "Einzellaute, 6,57±0,84 Silben/s kombiniert „pa-ta-ka“) — bei zerebellärer Ataxie "
            "in einer Studie im Mittel nur 3,2 Silben/s vs. 5,61 Silben/s bei Kontrollen. "
            "WICHTIG: unser eigener Erkennungsalgorithmus (Burst-basiert) ist NICHT gegen "
            "diese Literaturwerte validiert, nur die Größenordnung stammt daraus — siehe "
            "zusätzlich Regelmäßigkeit (CV) für ataktische Muster."
        ),
        "age_caveat": None,
        "evidence": "in der Forschung diskutiert",
        "literature": "Alternating and sequential motion rates in older adults (Pierce et al.); Oral-DDK-Rate gesunder junger Erwachsener (Speech Language and Hearing 2022); DDK bei zerebellärer Ataxie (Colorado-Dissertation); Einzellaut-Normwerte + Ataxie-Vergleich zusätzlich bei Kent et al. 1979, „Diadochokinetic syllable rate and regularity in normal and in spastic and ataxic dysarthric subjects“, Journal of Speech and Hearing Disorders 47(3)",
        "typical_values": (
            "Gesunde Erwachsene (Einzellaute): /p/ 6,4 Silben/s, /t/ 6,1 Silben/s, /k/ 5,7 "
            "Silben/s (Kent et al. 1979); englischsprachiger Normwert kombiniert ~6,23 "
            "Silben/s (SD 0,81), untere Grenze ~5,4 Silben/s. Bei ataktischer Dysarthrie "
            "DEUTLICH reduziert: /p/ 3,8, /t/ 3,9, /k/ 3,4 Silben/s (dieselbe Quelle) — die "
            "Silbendauer selbst war bei Ataxie mit 166ms gegenüber 80ms bei Gesunden etwa "
            "doppelt so lang. Bei Parkinson ebenfalls reduzierte DDK-Raten berichtet, "
            "konkrete Zahlen variieren je Studie."
        ),
    },
    "mean_cycle_interval_s": {
        "label": "Ø Zyklus-Intervall",
        "unit": "s",
        "description": "Mittlerer zeitlicher Abstand zwischen den erkannten Silbenzyklen — der Kehrwert der DDK-Rate.",
        "zones_func": None,
        "context": (
            "Inhaltlich redundant zur DDK-Rate (1/Rate) — bewusst OHNE eigene Ampel, um nicht "
            "zweimal dieselbe Information unterschiedlich zu bewerten. Nur als ergänzende "
            "Zeitangabe gedacht, siehe DDK-Rate für die eingeordnete Version."
        ),
        "age_caveat": None,
        "evidence": "deskriptiv, kein Krankheits-Marker",
        "literature": "Kehrwert der DDK-Rate, siehe dort für Quellen",
    },
    "cycle_interval_cv": {
        "label": "DDK-Regelmäßigkeit (CV)",
        "unit": "",
        "description": "Variationskoeffizient der Zeitabstände zwischen den Silbenzyklen — wie gleichmäßig/unregelmäßig die Silbenfolge ist.",
        "zones_func": None,
        "context": (
            "Unregelmäßige, „stolpernde“ Silbenfolgen (hoher CV) gelten als möglicher Hinweis "
            "auf ataktische Dysarthrie (zerebelläre Störung) — reine Verlangsamung ohne "
            "Unregelmäßigkeit spricht eher für hypokinetisch/spastisch. **P12-Recherche "
            "2026-08-15**: CV wird in der Ataxie-Literatur als sinnvolles Maß bestätigt "
            "(qualitativ signifikant unterschiedlich bei Ataxie), aber KEIN konkreter "
            "Zahlen-Cutoff gefunden — bewusst weiterhin ohne Ampel, um keine erfundene "
            "Schwelle vorzutäuschen."
        ),
        "age_caveat": None,
        "evidence": "in der Forschung diskutiert",
        "literature": "Coefficient of variation als Ataxie-Marker in Gang-/Sprechstudien bestätigt (z.B. Perceptual and Acoustic Analysis of Speech in Spinocerebellar Ataxia Type 1), aber ohne einheitlichen publizierten Cutoff für DDK-CV",
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
    "f0_mean_hz": {
        "label": "F0 (Mittelwert)",
        "unit": "Hz",
        "description": "Mittlere Grundfrequenz der Stimme über die Aufnahme — die wahrgenommene Tonhöhe.",
        "zones_func": None,
        "context": (
            "Rein deskriptiv, stark geschlechts-/altersabhängig (grob 100-146Hz bei "
            "männlichen, 188-221Hz bei weiblichen Stimmen in Sprechsprache) — kein "
            "Krankheits-Marker per se, aber Grundlage für andere Kennwerte (z.B. Monopitch = "
            "Streuung um diesen Mittelwert). Bewusst OHNE Ampel: ein „normaler“ vs. "
            "„auffälliger“ F0-Mittelwert ergibt ohne bekanntes Geschlecht keinen Sinn."
        ),
        "age_caveat": AGE_CAVEAT_JITTER_SHIMMER_HNR_F0,
        "evidence": "deskriptiv, kein Krankheits-Marker",
        "literature": "Average Speaking Frequencies: F0 Norms by Age, Sex, and Hormonal Status — Voice Science",
    },
    "voice_breaks_count": {
        "label": "Voice Breaks (Anzahl)",
        "unit": "",
        "description": "Anzahl der Stellen, an denen die Stimmgebung kurz unterbrochen ist (Praats Standard-„Voice report“).",
        "zones_func": None,
        "context": (
            "Nur bei gehaltenem Vokal aussagekräftig — bei Fließsprache durch normale "
            "Wortpausen/stimmlose Konsonanten (s, f, ch) ohnehin erwartbar hoch, keine "
            "Auffälligkeit. Siehe „Voice Breaks (Anteil)“ für die eingeordnete Version."
        ),
        "age_caveat": None,
        "evidence": "deskriptiv, kein Krankheits-Marker",
        "literature": "Praat-Dokumentation „Voice 1. Voice breaks“ (fon.hum.uva.nl)",
    },
    "voice_breaks_degree_pct": {
        "label": "Voice Breaks (Anteil)",
        "unit": "%",
        "description": "Anteil der Aufnahme, in dem die Stimmgebung unterbrochen ist (Praats Standard-„Voice report“).",
        "zones_func": voice_breaks_zones,
        "context": (
            "Nur bei gehaltenem Vokal aussagekräftig — bei Fließsprache durch normale "
            "Wortpausen/stimmlose Konsonanten ohnehin erwartbar hoch, keine Auffälligkeit. "
            "Normbereich hier bewusst großzügig/pragmatisch gewählt (Praat-Dokumentation nennt "
            "0% als Normativwert für gesunde gehaltene Vokale, aber keinen graduierten "
            "Cutoff) — erhöhter Anteil kann auf Stimmlippenpathologie oder stimmliche "
            "Ermüdung hindeuten."
        ),
        "age_caveat": None,
        "evidence": "eigene Heuristik / explorativ",
        "literature": "Praat-Dokumentation „Voice 1. Voice breaks“ (fon.hum.uva.nl) — Normativwert 0% für gesunde gehaltene Vokale, Zonen-Grenzen pragmatisch, kein publizierter graduierter Cutoff",
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
    "f3_mean_hz": {
        "label": "Formant F3",
        "unit": "Hz",
        "description": "Dritte Vokaltrakt-Resonanz — trägt zur Klangfarbe/Schärfe bei, weniger eindeutig einer einzelnen Artikulationsdimension zuordenbar als F1/F2.",
        "zones_func": None,
        "context": "Kein Normwert ohne bekannte Vokal-Identität — Formanten sind hier nur als Rohwerte informativ.",
        "age_caveat": None,
        "evidence": "deskriptiv, kein Krankheits-Marker",
        "literature": "Formant-Rohwert, siehe docs/literatur_review.md Abschnitt 2 — ohne bekannte Vokal-Identität hier nur informativ",
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
        "zones_func": rap_zones,
        "context": (
            "Wie Jitter (local) ein unspezifischer Dysphonie-Marker, nur bei gehaltenem Vokal "
            "zuverlässig interpretierbar. **P12**: Normbereich <0,68% aus der klassischen "
            "MDVP-Konvention übernommen — MDVP und Praat liefern für dieselbe Aufnahme "
            "systematisch unterschiedliche absolute Werte (dokumentierter Algorithmus-"
            "Unterschied), die Schwelle ist also eine Orientierung, NICHT gegen unsere eigene "
            "Praat-Pipeline nachvalidiert."
        ),
        "age_caveat": AGE_CAVEAT_JITTER_SHIMMER_HNR_F0,
        "evidence": "gut etabliert",
        "literature": "RAP <0,68% — klassischer MDVP-Normwert (Kay Elemetrics/PENTAX-Konvention), MDVP-vs-Praat-Vorbehalt beachten",
    },
    "jitter_ppq5_pct": {
        "label": "Jitter (PPQ5)",
        "unit": "%",
        "description": "5-Punkt-Periodenperturbation — wie RAP, aber über 5 benachbarte Zyklen geglättet.",
        "zones_func": ppq5_zones,
        "context": (
            "Wie Jitter (local)/RAP ein unspezifischer Dysphonie-Marker, nur bei gehaltenem "
            "Vokal zuverlässig interpretierbar. **P12**: Normbereich <0,84% aus der "
            "klassischen MDVP-Konvention — gleicher MDVP-vs-Praat-Vorbehalt wie bei RAP "
            "(Orientierung, nicht gegen unsere Pipeline nachvalidiert)."
        ),
        "age_caveat": AGE_CAVEAT_JITTER_SHIMMER_HNR_F0,
        "evidence": "gut etabliert",
        "literature": "PPQ5 <0,84% — klassischer MDVP-Normwert (Kay Elemetrics/PENTAX-Konvention), MDVP-vs-Praat-Vorbehalt beachten",
    },
    "shimmer_apq11_pct": {
        "label": "Shimmer (APQ11)",
        "unit": "%",
        "description": "11-Punkt-Amplitudenperturbation — wie Shimmer (local), aber über 11 benachbarte Zyklen geglättet, dadurch robuster gegen einzelne Ausreißer-Zyklen.",
        "zones_func": apq11_zones,
        "context": (
            "Wie Shimmer (local) ein unspezifischer Dysphonie-Marker, nur bei gehaltenem Vokal "
            "zuverlässig interpretierbar. **P12**: Normbereich <3,07% aus der klassischen "
            "MDVP-Konvention — gleicher MDVP-vs-Praat-Vorbehalt wie bei RAP/PPQ5."
        ),
        "age_caveat": AGE_CAVEAT_JITTER_SHIMMER_HNR_F0,
        "evidence": "gut etabliert",
        "literature": "APQ11 <3,07% — klassischer MDVP-Normwert (Kay Elemetrics/PENTAX-Konvention), MDVP-vs-Praat-Vorbehalt beachten",
    },
    "mpt_s": {
        "label": "Maximum Phonation Time (MPT)",
        "unit": "s",
        "description": "Längste zusammenhängende stimmhafte Passage in der Aufnahme — klassisches Stimm-/Atemreserve-Maß.",
        "zones_func": mpt_zones,
        "context": (
            "Reduzierte MPT gilt als Hinweis auf eingeschränkte Atem-/Stimmbandfunktion, z.B. "
            "bei ALS/bulbären Erkrankungen. Nur aussagekräftig, wenn gezielt „so lange wie "
            "möglich halten“ instruiert wurde — bei kurzen Standard-Vokalaufnahmen ist der Wert "
            "nur die aufgenommene Dauer, nicht die tatsächliche maximale Phonationsdauer. "
            "**P12**: Normbereich ≥15s (konservative untere/weibliche Literaturgrenze, da hier "
            "kein Geschlecht erfasst wird) — gesunde Erwachsene erreichen typischerweise "
            "25-35s (Männer)/15-25s (Frauen), <10s gilt allgemein als reduziert."
        ),
        "age_caveat": None,
        "evidence": "gut etabliert",
        "literature": "MPT-Normwerte 25-35s (M)/15-25s (F), <10s reduziert — Iowa Head and Neck Protocols, VoiceDoctor.net, zusammenfassende Sekundärquellen. Abweichende Primärstudie: Maximum Phonation Time Normative Values Among Malaysians (Journal of Voice/ScienceDirect) und „Maximum Phonation Time: Variability and Reliability“ (Journal of Voice)",
        "typical_values": (
            "Literatur ist sich NICHT einig auf eine einzelne Zahl — bewusst als Beispiel für "
            "echte Bandbreite dargestellt statt einer einzelnen Pseudo-Präzisions-Zahl: die "
            "oft zitierte Iowa-Sekundärquelle nennt 25-35s (Männer)/15-25s (Frauen), eine "
            "malaysische Normativ-Studie dagegen deutlich niedriger 21,41±6,85s (Männer)/"
            "18,05±5,06s (Frauen) für den Vokal /a/. Bei Dysphonie/motorischen Störungen im "
            "Mittel reduziert — eine Studie berichtete Patient:innen im Schnitt 6,6s kürzer "
            "als gesunde Kontrollen."
        ),
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
            "möglicher Hinweis auf Artikulationsundeutlichkeit/Dysarthrie. **P12-Recherche "
            "2026-08-15**: gezielt nach einer publizierten Hz²-Normschwelle gesucht — keine "
            "gefunden. VSA ist extrem methodenabhängig (Vokalset, Messzeitpunkt in der "
            "Vokaldauer, Anzahl Wiederholungen), Studien berichten Rohwerte, aber keinen "
            "allgemein akzeptierten Cutoff. Braucht alle 3 Vokal-Teilaufgaben mit mindestens "
            "einem Versuch, bleibt bewusst ohne Ampel."
        ),
        "age_caveat": None,
        "evidence": "in der Forschung diskutiert",
        "literature": "Klassische VSA-Dreiecksformel, aber laut Literatur uneinheitlich validiert (hohe Sprecher-zu-Sprecher-Varianz, methodenabhängig) — siehe docs/literatur_review.md Punkt 2 der Einschränkungen; kein publizierter Hz²-Cutoff, aber konkrete Vergleichswerte bei „Acoustic analysis of the voice in patients with Parkinson's disease and hypokinetic dysarthria“ und „Vowel Articulation in Parkinson's Disease“ (ScienceDirect)",
        "typical_values": (
            "Kein Cutoff, aber echte publizierte Vergleichswerte (nachträglich gefunden, "
            "2026-08-16) — Ergänzung zur ursprünglichen Recherche, die keine Zahlen fand: eine "
            "Studie berichtet 310.517±111.523 Hz² bei Gesunden vs. 247.867±68.934 Hz² bei "
            "Parkinson-Dysarthrie (p=0,012); eine zweite Studie 363.679 Hz² (Gesunde) vs. "
            "306.501 Hz² (Parkinson-Dysarthrie). Beide zeigen dieselbe Richtung (kleinere "
            "Fläche bei Dysarthrie, „Vokal-Zentralisierung“), die ABSOLUTEN Zahlen "
            "unterscheiden sich aber deutlich zwischen den Studien — passt zur bekannten "
            "hohen Methodenabhängigkeit, deshalb weiterhin bewusst ohne Ampel/Cutoff."
        ),
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
        "typical_values": info.get("typical_values"),
    }

    if info["zones_func"] is not None:
        lo, hi, zones = info["zones_func"]()
        # Bugfix 2026-08-16 (Nutzer-Feedback): Anzeigetext MUSS aus der tatsaechlichen
        # GOOD-Zonengrenze kommen, nicht aus lo/hi (das ist nur die Gauge-Achse) -- sonst zeigt
        # die Spalte z.B. "0-30%" an, waehrend Werte weit unterhalb von 30% schon als
        # "auffaellig" gewertet werden, weil der echte Cutoff viel enger ist. Siehe
        # core/reference_ranges.py::good_range_text().
        range_text = good_range_text(lo, hi, zones, info["unit"])
        if range_text is not None:
            result["range"] = range_text
        if value is not None:
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
    Label, "Was es misst", Kontext (deskriptiv), Evidenz-Einordnung, Literaturverweis,
    Referenzwerte (P15, docs/backlog.md "Referenzwerte im Glossar"). Getrennt von build_rows()
    (kompakte Uebersicht), damit die kompakte Tabelle nicht wieder mit langen Texten
    ueberladen wird (Nutzer-Feedback 2026-08-15 zur vorherigen Tabellen-Version)."""
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
            "typical_values": info["typical_values"],
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
        # Bucket I (docs/backlog.md, Nutzer-Feedback 2026-08-15): Normbereich soll DIREKT auf
        # der Kachel sichtbar sein, nicht nur in der versteckten Detailtabelle -- gerade nach
        # der P12-Recherche waren die Ranges sonst "unsichtbar erforscht". Nur anzeigen, wenn
        # ein echter Normbereich existiert (nicht bei "kein etablierter Normbereich").
        range_text = info["range"] if info["range"] != "kein etablierter Normbereich" else None
        tiles.append({
            "label": info["label"],
            "value_text": value_text,
            "sub_text": info["status"],
            "zone": info["zone"],
            "description": info["description"],
            "range_text": range_text,
        })
    return tiles


