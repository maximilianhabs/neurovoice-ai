"""Sprechrate/Pausen/Fluessigkeit aus Wort-Zeitstempeln (Chunk 3 = Stufe 3, siehe docs/backlog.md).

Nutzt die Wort-Zeitstempel aus transcription.transcribe() fuer eine granulare Pausenanalyse
zwischen einzelnen Woertern -- praeziser als reine akustische Stille-Erkennung, weil bekannt
ist, WAS zwischen den Pausen gesprochen wurde (siehe docs/literatur_review.md: "Net Speech
Rate", "Duration of Pause Intervals" als etablierte PD-Marker).
"""

from __future__ import annotations

import math

DEFAULT_PAUSE_THRESHOLD_S = 0.25  # ab hier gilt eine Woertluecke als "echte" Pause, nicht nur normale Koartikulation
MACRO_PAUSE_THRESHOLD_S = 0.5  # ab hier gilt eine Pause als "Makropause" statt "Mikropause" (Audit 2026-07-22)
ENTROPY_BINS = 8  # Anzahl Histogramm-Klassen fuer die prosodische Entropie (max. Entropie = log2(8) = 3 bit)


def _shannon_entropy_bits(values: list[float], n_bins: int = ENTROPY_BINS) -> float | None:
    """Shannon-Entropie (bit) ueber ein Histogramm der uebergebenen Werte.

    Hoehere Werte = gleichmaessiger ueber viele verschiedene Dauern verteilt
    ("unvorhersehbarer" Rhythmus), niedrigere Werte = auf wenige aehnliche Dauern
    konzentriert (vorhersehbarer/monotoner Rhythmus). Ergaenzt nPVI, das nur
    aufeinanderfolgende Paare vergleicht, um eine Gesamtverteilungs-Sicht.
    """
    if len(values) < 2:
        return None
    lo, hi = min(values), max(values)
    # Toleranzschwelle statt exaktem hi<=lo-Vergleich: Wort-Zeitstempel aus Fliesskomma-
    # Arithmetik koennen bei "identischen" Dauern durch Rundungsrauschen um ~1e-16 streuen --
    # ohne Toleranz wuerde das faelschlich als hohe Entropie durchschlagen (Bugfix 2026-07-22,
    # verifiziert mit einer synthetischen Testreihe identischer Wortdauern).
    if hi - lo < 1e-6:
        return 0.0
    bin_width = (hi - lo) / n_bins
    counts = [0] * n_bins
    for v in values:
        idx = min(int((v - lo) / bin_width), n_bins - 1)
        counts[idx] += 1
    total = len(values)
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            entropy -= p * math.log2(p)
    return entropy


def compute_speech_metrics(
    words: list[dict],
    total_duration_s: float,
    pause_threshold_s: float = DEFAULT_PAUSE_THRESHOLD_S,
    pausen_aus_audio: dict | None = None,
) -> dict:
    """Berechnet Sprechrate-/Pausen-/Fluessigkeitsmasse aus einer Wortliste.

    Args:
        words: Liste von {"word": str, "start": float, "end": float, "score": float},
            wie von core.transcription.transcribe() zurueckgegeben.
        total_duration_s: Gesamtdauer der Aufnahme in Sekunden.
        pause_threshold_s: Mindestdauer einer Woertluecke, um als "Pause" gezaehlt zu werden.

    Returns:
        Dict mit Sprechrate-, Pausen- und Fluessigkeits-Kennwerten (siehe einzelne Keys).
    """
    valid_words = [w for w in words if w.get("start") is not None and w.get("end") is not None]
    n_words = len(valid_words)

    if n_words == 0:
        return {
            "n_words": 0,
            "net_speech_rate_wpm": None,
            "articulation_rate_wpm": None,
            "articulation_span_s": None,
            "pause_count": 0,
            "mean_pause_duration_s": None,
            "max_pause_duration_s": None,
            "total_pause_time_s": 0.0,
            "fluency_score": None,
            "rhythm_npvi": None,
            "micro_pause_count": 0,
            "macro_pause_count": 0,
            "mean_micro_pause_duration_s": None,
            "mean_macro_pause_duration_s": None,
            "prosodic_entropy_bits": None,
            "mean_word_duration_s": None,
        }

    speech_start = valid_words[0]["start"]
    speech_end = valid_words[-1]["end"]
    articulation_span_s = speech_end - speech_start

    # Net Speech Rate: bezogen auf die GESAMTE Aufnahmedauer (inkl. Anlauf-/Schlusspausen) --
    # klassische Literatur-Definition, siehe docs/literatur_review.md.
    net_speech_rate_wpm = (n_words / total_duration_s) * 60 if total_duration_s > 0 else None

    # Articulation Rate: nur bezogen auf die Spanne von erstem bis letztem Wort -- filtert
    # Anlauf-/Schlusspausen raus, die nichts mit der eigentlichen Sprechweise zu tun haben.
    articulation_rate_wpm = (n_words / articulation_span_s) * 60 if articulation_span_s > 0 else None

    # Pausen kommen bevorzugt AUS DEM SIGNAL (core/audio.py::pausen_aus_signal()), nicht aus
    # den Wortzeitstempeln. Grund: WhisperX' Forced Alignment dehnt die Wortgrenzen aneinander,
    # sodass die Luecken hier systematisch null werden -- unabhaengig davon, ob tatsaechlich
    # pausiert wurde. Genau das lieferte ueber Monate `fluency_score` = 1,00 in JEDER Aufnahme
    # (RANDNOTIZ-17, am 2026-08-20 mit konstruierten Wortlisten bewiesen).
    #
    # Die wortbasierte Ableitung bleibt als Rueckfallweg erhalten, damit die Funktion auch ohne
    # Audiodatei aufrufbar bleibt (Tests, Altdaten) -- sie ist dann aber nur so gut wie ihre
    # Eingabe, was der Aufrufer wissen muss.
    if pausen_aus_audio is not None:
        real_pauses = None  # unten nicht mehr gebraucht, Werte kommen fertig aus dem Signal
        total_pause_time_s = pausen_aus_audio["total_pause_time_s"]
        mean_pause_duration_s = pausen_aus_audio["mean_pause_duration_s"]
        max_pause_duration_s = pausen_aus_audio["max_pause_duration_s"]
        pause_count = pausen_aus_audio["pause_count"]
        micro_count = pausen_aus_audio["micro_pause_count"]
        macro_count = pausen_aus_audio["macro_pause_count"]
        mean_micro_pause_duration_s = pausen_aus_audio["mean_micro_pause_duration_s"]
        mean_macro_pause_duration_s = pausen_aus_audio["mean_macro_pause_duration_s"]
    else:
        pause_durations = []
        for prev_word, next_word in zip(valid_words, valid_words[1:]):
            gap = next_word["start"] - prev_word["end"]
            if gap > 0:
                pause_durations.append(gap)

        real_pauses = [p for p in pause_durations if p >= pause_threshold_s]
        total_pause_time_s = sum(real_pauses)

        mean_pause_duration_s = total_pause_time_s / len(real_pauses) if real_pauses else None
        max_pause_duration_s = max(real_pauses) if real_pauses else None

    # Mikro-/Makropausen-Verteilung (Audit 2026-07-22): Pausen bislang nur als eine Kategorie
    # gezaehlt -- Unterscheidung nach Dauer kann auf unterschiedliche Ursachen hindeuten
    # (Mikropausen = normale Atem-/Wortgrenzen, Makropausen = auffaellige Zoegerungen/Suchen).
    if real_pauses is not None:
        micro_pauses = [p for p in real_pauses if p < MACRO_PAUSE_THRESHOLD_S]
        macro_pauses = [p for p in real_pauses if p >= MACRO_PAUSE_THRESHOLD_S]
        pause_count = len(real_pauses)
        micro_count = len(micro_pauses)
        macro_count = len(macro_pauses)
        mean_micro_pause_duration_s = sum(micro_pauses) / len(micro_pauses) if micro_pauses else None
        mean_macro_pause_duration_s = sum(macro_pauses) / len(macro_pauses) if macro_pauses else None

    # Fluessigkeits-Score: Anteil der Sprechspanne, der tatsaechlich mit Sprechen (statt Pausen)
    # gefuellt ist. 1.0 = keine nennenswerten Pausen, niedrigere Werte = mehr/laengere Pausen
    # relativ zur Sprechdauer. Bewusst einfache, transparente Definition -- kein Ersatz fuer
    # klinisches Urteil, siehe docs/literatur_review.md ("Diskrepanz automatisierte Metriken
    # vs. klinisch-perzeptiver Eindruck").
    fluency_score = 1 - (total_pause_time_s / articulation_span_s) if articulation_span_s > 0 else None

    # Rhythmus (nPVI, Stufe 4): normalisierter Pairwise Variability Index ueber die
    # Wortdauern -- Standardmass fuer Sprechrhythmus-Variabilitaet aus der Prosodie-
    # Literatur (urspruenglich fuer Vokal-/Silbendauern entwickelt, hier als Naeherung
    # auf Wortebene, da wir keine Silbensegmentierung haben). Hohe Werte = stark
    # wechselnde Wortdauern ("lebendiger" Rhythmus), niedrige Werte = gleichfoermig/eintoenig.
    word_durations = [w["end"] - w["start"] for w in valid_words]
    pvi_diffs = []
    for d1, d2 in zip(word_durations, word_durations[1:]):
        if (d1 + d2) > 0:
            pvi_diffs.append(abs(d1 - d2) / ((d1 + d2) / 2))
    rhythm_npvi = (100 * sum(pvi_diffs) / len(pvi_diffs)) if pvi_diffs else None

    # Prosodische Entropie (Stufe 4, Audit 2026-07-22): ergaenzt nPVI (nur benachbarte Paare)
    # um eine Gesamtverteilungs-Sicht auf die Wortdauern -- siehe _shannon_entropy_bits().
    prosodic_entropy_bits = _shannon_entropy_bits(word_durations)

    # Mittlere Wortdauer (Nutzer-Feedback 2026-08-15, Bucket C2 Nachbesserung) -- war bisher
    # nur implizit in der Wort-Zeitstempel-Detailtabelle sichtbar (duration_s-Spalte seit
    # BUG-19), nie als eigener aggregierter Wert ausgewiesen. word_durations ist fuer nPVI
    # oben ohnehin schon berechnet, kein neuer Datenpfad.
    mean_word_duration_s = sum(word_durations) / len(word_durations) if word_durations else None

    return {
        "n_words": n_words,
        "net_speech_rate_wpm": net_speech_rate_wpm,
        "articulation_rate_wpm": articulation_rate_wpm,
        "articulation_span_s": articulation_span_s,
        "pause_count": pause_count,
        "mean_pause_duration_s": mean_pause_duration_s,
        "max_pause_duration_s": max_pause_duration_s,
        "total_pause_time_s": total_pause_time_s,
        "fluency_score": fluency_score,
        "rhythm_npvi": rhythm_npvi,
        "micro_pause_count": micro_count,
        "macro_pause_count": macro_count,
        "mean_micro_pause_duration_s": mean_micro_pause_duration_s,
        "mean_macro_pause_duration_s": mean_macro_pause_duration_s,
        "prosodic_entropy_bits": prosodic_entropy_bits,
        "mean_word_duration_s": mean_word_duration_s,
    }
