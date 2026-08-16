"""Lokale Speech-to-Text-Transkription (Chunk 1, siehe docs/backlog.md).

Nutzt WhisperX (whisper.cpp/faster-whisper-Backend + wav2vec2-Forced-Alignment) komplett
lokal, ohne API/Gebühren. Genauigkeit hat laut Nutzer-Vorgabe (2026-07-21) Vorrang vor
Geschwindigkeit -- Standardmodell ist deshalb "large-v3", nicht ein kleineres, schnelleres
Modell. Liefert bewusst nur Text + Wort-Zeitstempel zurueck (roh); Sprechgeschwindigkeit/
Pausen-Metriken sind ein eigener, spaeterer Chunk (core/speech_metrics.py), nicht Teil
dieses Moduls.

Chunk-1-Status: NUR gegen eine synthetische TTS-Testdatei verifiziert (macOS `say`,
Nordwind-und-Sonne-Referenztext), NICHT gegen echte (ggf. dysarthrische) Sprache. Das ist
ein reiner Mechanik-Nachweis ("laeuft die Pipeline durch, ist der Text grob richtig?"),
kein Genauigkeitsnachweis fuer den eigentlichen Anwendungsfall.
"""

from __future__ import annotations

import json
import os

DEFAULT_MODEL = "large-v3"
DEFAULT_LANGUAGE = "de"
DEFAULT_DEVICE = "cpu"
DEFAULT_COMPUTE_TYPE = "int8"  # auf CPU: int8 spart Speicher/Zeit ggue. float32, ohne
# bei WhisperX' eigener Fehlertoleranz (Alignment-Nachbearbeitung) relevant an Genauigkeit
# zu verlieren -- bei Bedarf spaeter gegen float32 A/B-testen (siehe docs/backlog.md).


def transcribe(
    audio_path: str,
    model_name: str = DEFAULT_MODEL,
    language: str = DEFAULT_LANGUAGE,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
) -> dict:
    """Transkribiert eine Audiodatei lokal und liefert Text + wortgenaue Zeitstempel.

    Returns:
        {
            "text": voller Transkript-Text,
            "words": [{"word": str, "start": float, "end": float, "score": float}, ...],
            "language": erkannte/verwendete Sprache,
        }

    Kein try/except um die Modell-Aufrufe (fail-loud, siehe Projektkonvention) -- ein
    Fehler beim Laden/Laufen des Modells soll sichtbar durchschlagen, nicht stumm ein
    leeres Transkript liefern.
    """
    import whisperx  # lazy (P9-Umbau): Cache-Helfer unten sollen auch OHNE installiertes
    # whisperx importierbar sein (core/job_queue.py-Worker prueft z.B. nur den Job-Status).

    model = whisperx.load_model(model_name, device, compute_type=compute_type, language=language)
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, language=language)

    align_model, align_metadata = whisperx.load_align_model(language_code=language, device=device)
    aligned = whisperx.align(result["segments"], align_model, align_metadata, audio, device)

    words = [
        {
            "word": w["word"],
            "start": w.get("start"),
            "end": w.get("end"),
            "score": w.get("score"),
        }
        for segment in aligned["segments"]
        for w in segment["words"]
    ]
    full_text = " ".join(segment["text"].strip() for segment in aligned["segments"])

    return {
        "text": full_text,
        "words": words,
        "language": language,
    }


# --- Transkript-Cache (P9-Umbau, docs/konzept_p9_hintergrundjob_lokal.md) -- vorher als
# fast identischer Code dreimal dupliziert in views/vorlesen.py/spontansprache.py/
# testdaten.py; jetzt zentral, damit views/*.py UND worker.py garantiert denselben Pfad
# lesen/schreiben (der Worker laeuft in einem eigenen Prozess, muss also exakt dieselbe
# Pfad-Formel wie die Streamlit-Seite verwenden).


def transcript_cache_path(recording_path: str) -> str:
    return os.path.splitext(recording_path)[0] + ".transcript.json"


def load_cached_transcript(recording_path: str) -> dict | None:
    cache_path = transcript_cache_path(recording_path)
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_transcript_cache(recording_path: str, transcript: dict) -> None:
    with open(transcript_cache_path(recording_path), "w", encoding="utf-8") as f:
        json.dump(transcript, f, ensure_ascii=False, indent=2)
