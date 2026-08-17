"""ASR-basierte Sprachverstaendlichkeit (Nutzer-Idee 2026-08-17, siehe docs/backlog.md
"Speech-Intelligibility-Score (WER/CER)" -- vorher unpriorisiert, jetzt umgesetzt): beim
Vorlesen-Modul ist der Referenztext bekannt (`views/vorlesen.py::LESETEXTE`, je Take als
`lesetext_key` gespeichert). Ein Vergleich der WhisperX-Transkription gegen diesen bekannten
Text liefert eine objektive, quantifizierbare Naeherung an Sprachverstaendlichkeit -- wenn das
Spracherkennungsmodell den bekannten Text schlecht erkennt, ist das ein plausibler (wenn auch
indirekter) Hinweis auf reduzierte artikulatorische Praezision, wie sie bei Dysarthrie erwartet
wird.

Word Error Rate (WER) und Character Error Rate (CER) sind die etablierten Standardmasse dafuer
(Editierdistanz Hypothese vs. Referenz, normalisiert auf die Referenzlaenge). Literaturbasierte
Einordnung (Websuche 2026-08-17, mehrere ASR-/Dysarthrie-Studien): gesunde Sprache erreicht je
nach ASR-System/Korpus ca. 6-27% WER, dysarthrische Sprache deutlich hoehere Werte (~62-135%,
bei schwerer Dysarthrie durch Einfuegungsfehler teils >100% moeglich). **Bewusst OHNE eigene
Zonen-/Normbereich-Definition** -- die Streubreite zwischen Studien/ASR-Systemen ist zu gross
fuer einen seriösen festen Cutoff, siehe PARAMETER_INFO-Kontext fuer die vollen Literaturwerte.
Reine Naeherung: WER erfasst auch Erkennungsfehler des Modells selbst (Hintergrundgeraeusch,
Akzent, Wortschatzluecken), nicht ausschliesslich artikulatorische Praezision -- explizit als
"in der Forschung diskutiert" gekennzeichnet, nicht als etablierter klinischer Kennwert.
"""

from __future__ import annotations

import re


def _normalize_words(text: str) -> list[str]:
    """Kleinschreibung + Satzzeichen entfernt (Umlaute/ß bleiben erhalten), dann in Wörter
    zerlegt -- gleiche Normalisierung fuer Referenztext UND Transkript, sonst waeren
    Satzzeichen-Unterschiede faelschlich Editierdistanz."""
    text = text.lower()
    text = re.sub(r"[^\w\säöüß]", "", text, flags=re.UNICODE)
    return text.split()


def _edit_distance(a: list, b: list) -> int:
    """Klassische Levenshtein-Editierdistanz (Einfuegen/Loeschen/Ersetzen), per dynamischer
    Programmierung -- Referenztexte/Transkripte hier sind kurz (~20-30 Woerter), O(n*m) reicht
    locker, keine Bibliothek noetig."""
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n

    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr[j] = min(
                prev[j] + 1,       # Loeschen
                curr[j - 1] + 1,   # Einfuegen
                prev[j - 1] + cost,  # Ersetzen (oder Treffer)
            )
        prev = curr
    return prev[m]


def compute_intelligibility_score(reference_text: str, transcribed_words: list[dict]) -> dict:
    """Vergleicht die WhisperX-Transkription (`transcribed_words`, Format wie
    `transcript["words"]` aus core/transcription.py) gegen den bekannten Referenztext.

    Gibt ein dict mit `wer_pct`/`cer_pct` (Word-/Character Error Rate in Prozent) sowie
    `reference_word_count`/`hypothesis_word_count` zurueck. `None` fuer die Raten, falls der
    Referenztext leer ist (sollte praktisch nie vorkommen, defensiv trotzdem abgefangen)."""
    hyp_text = " ".join(w.get("word", "") for w in transcribed_words)

    ref_words = _normalize_words(reference_text)
    hyp_words = _normalize_words(hyp_text)

    if not ref_words:
        return {
            "wer_pct": None, "cer_pct": None,
            "reference_word_count": 0, "hypothesis_word_count": len(hyp_words),
        }

    word_distance = _edit_distance(ref_words, hyp_words)
    wer_pct = word_distance / len(ref_words) * 100.0

    # CER auf den normalisierten, mit einzelnen Leerzeichen verbundenen Wortfolgen -- feinere
    # Aufloesung als WER (erkennt z.B. "fast richtig getroffene" Woerter statt nur ganz/falsch).
    ref_chars = list(" ".join(ref_words))
    hyp_chars = list(" ".join(hyp_words))
    char_distance = _edit_distance(ref_chars, hyp_chars)
    cer_pct = char_distance / len(ref_chars) * 100.0 if ref_chars else None

    return {
        "wer_pct": wer_pct,
        "cer_pct": cer_pct,
        "reference_word_count": len(ref_words),
        "hypothesis_word_count": len(hyp_words),
    }
