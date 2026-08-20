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


DERIVED_DIR = os.environ.get("NEUROVOICE_DERIVED_DIR", "/derived")


def transcript_cache_path(recording_path: str) -> str:
    """Cache-Ablage IMMER unter `<derived>/<ordnername>/<datei>.transcript.json`.

    Bugfix 2026-08-20 (RANDNOTIZ-16, docs/bugtracker.md): vorher wurde die Cache-Datei direkt
    neben die Audiodatei gelegt. Fuer Uploads unter `/derived/_uploads/` ging das gut, fuer den
    Rohdaten-Korpus unter `/data/<patient_id>/` nicht -- `/data` ist laut docker-compose.yml
    bewusst READ-ONLY gemountet. Folge: der Worker transkribierte ein bis zwei Minuten lang,
    scheiterte dann beim Schreiben an `OSError: Read-only file system` und warf das fertige
    Ergebnis weg. Genau so passiert beim iPhone-Paar-Durchlauf am 2026-08-20.

    Die neue Formel ist bewusst dieselbe, die views/testdaten.py schon immer benutzt hat (dort
    als eigene, konkurrierende `_transcript_cache_path()`-Kopie -- jetzt entfernt, siehe
    RANDNOTIZ-16 "Code-Duplikat"). Fuer Uploads liefert sie unveraendert
    `/derived/_uploads/...`, bestehende Caches bleiben also gueltig; nur fuer `/data`-Dateien
    aendert sich der Ort von "unschreibbar" zu "schreibbar"."""
    ordner = os.path.basename(os.path.dirname(os.path.abspath(recording_path)))
    ziel_dir = os.path.join(DERIVED_DIR, ordner)
    base = os.path.splitext(os.path.basename(recording_path))[0]
    return os.path.join(ziel_dir, f"{base}.transcript.json")


def load_cached_transcript(recording_path: str) -> dict | None:
    cache_path = transcript_cache_path(recording_path)
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_transcript_cache(recording_path: str, transcript: dict) -> bool:
    """Schreibt den Cache atomar (temporaere Datei + `os.replace`), damit ein Abbruch mitten im
    Schreiben keine halbe JSON-Datei hinterlaesst, die beim naechsten Laden crasht.

    Gibt True/False zurueck statt zu werfen: das Transkript ist zu diesem Zeitpunkt bereits
    fertig berechnet und liegt im Job-Ergebnis -- ein fehlgeschlagener Cache-Schreibvorgang
    darf diese teure Arbeit NICHT vernichten (RANDNOTIZ-16). Der Aufrufer entscheidet, ob er
    das protokolliert; der Nutzer bekommt sein Transkript in jedem Fall."""
    cache_path = transcript_cache_path(recording_path)
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        tmp_path = f"{cache_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, cache_path)
        return True
    except OSError:
        return False
