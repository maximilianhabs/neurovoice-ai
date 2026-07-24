"""Lexikalische Diversitaet aus dem Transkript-Text (Stufe 7, siehe docs/backlog.md).

Bewusst OHNE spaCy/POS-Tagging umgesetzt -- TTR und MTLD brauchen nur eine Tokenisierung
(hier: die von WhisperX ohnehin schon segmentierten Woerter), kein linguistisches Tooling.
Syntaktische Komplexitaet (MLU/POS-Dichte) und semantische Kohaerenz bleiben bewusst offen
(siehe docs/backlog.md Stufe 7) -- das braucht tatsaechlich einen neuen NLP-Stack.
"""

from __future__ import annotations

import re

MTLD_TTR_THRESHOLD = 0.72  # Standardschwelle aus McCarthy & Jarvis (2010)

_WORD_RE = re.compile(r"[a-zA-ZäöüÄÖÜß]+")


def _normalize_tokens(words: list[dict]) -> list[str]:
    tokens = []
    for w in words:
        raw = w.get("word", "")
        match = _WORD_RE.search(raw)
        if match:
            tokens.append(match.group(0).lower())
    return tokens


def _mtld_one_direction(tokens: list[str], threshold: float = MTLD_TTR_THRESHOLD) -> float:
    """Anzahl "Faktoren" (Textabschnitte bis TTR unter die Schwelle faellt), gemittelt.

    Standardalgorithmus (McCarthy & Jarvis 2010): lauft durch den Token-Strom, haelt eine
    laufende Type-Token-Ratio nach, und zaehlt einen "Faktor" jedes Mal, wenn diese TTR
    unter die Schwelle faellt -- danach wird der Zaehler zurueckgesetzt. Ein unvollstaendiger
    Rest-Faktor am Ende wird anteilig gewichtet, statt verworfen.
    """
    if len(tokens) < 2:
        return 0.0

    factors = 0.0
    types_seen: set[str] = set()
    segment_len = 0

    for token in tokens:
        segment_len += 1
        types_seen.add(token)
        ttr = len(types_seen) / segment_len
        if ttr <= threshold:
            factors += 1
            types_seen = set()
            segment_len = 0

    # unvollstaendiger Rest-Faktor: anteilig nach wie weit die TTR schon gefallen ist
    if segment_len > 0:
        ttr = len(types_seen) / segment_len
        remainder = (1 - ttr) / (1 - threshold) if ttr < 1 else 0.0
        factors += remainder

    return len(tokens) / factors if factors > 0 else float(len(tokens))


def lexical_diversity_features(words: list[dict]) -> dict:
    """Berechnet Type-Token-Ratio und MTLD aus einer WhisperX-Wortliste.

    Args:
        words: Liste von {"word": str, ...}, wie von core.transcription.transcribe()
            zurueckgegeben (Zeitstempel werden hier nicht gebraucht).

    Returns:
        Dict mit n_tokens, n_types, ttr, mtld. Alle None, wenn zu wenige Woerter vorhanden.
    """
    tokens = _normalize_tokens(words)
    n_tokens = len(tokens)

    if n_tokens < 2:
        return {"n_tokens": n_tokens, "n_types": None, "ttr": None, "mtld": None}

    n_types = len(set(tokens))
    ttr = n_types / n_tokens

    # MTLD bidirektional (vorwaerts + rueckwaerts gemittelt) -- Standardverfahren, robuster
    # gegen die Reihenfolge der Woerter als eine reine Vorwaertsrichtung.
    forward = _mtld_one_direction(tokens)
    backward = _mtld_one_direction(list(reversed(tokens)))
    mtld = (forward + backward) / 2

    return {"n_tokens": n_tokens, "n_types": n_types, "ttr": ttr, "mtld": mtld}
