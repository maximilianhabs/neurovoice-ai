"""Feature-/Algorithmus-Versionierung je Messung (Nutzer-Wunsch 2026-08-20, aus dem zweiten
externen KI-Review, siehe docs/backlog.md "Externes KI-Review 2026-08-20" -- berechtigter
Punkt: `core/session_store.py::SCHEMA_VERSION` versioniert nur das SITZUNGS-Speicherformat,
nicht die eigentliche Analyse. Ohne das laesst sich in sechs Monaten nicht mehr sicher sagen,
ob zwei "Jitter 0,72%"-Werte aus derselben Berechnungslogik stammen -- fuer longitudinale
Vergleiche (das erklaerte Kernziel des Projekts) fundamental.

FEATURE_SCHEMA_VERSION ist eine bewusst simple, manuell gepflegte Versionsnummer (kein
automatisches Ableiten aus Git-Commits -- das Docker-Image enthaelt kein .git-Verzeichnis,
siehe Dockerfile). MUSS von Hand erhoeht werden, wann immer sich eine Berechnungsformel in
core/audio.py inhaltlich aendert (nicht bei reinem Refactoring ohne Wertaenderung). Ohne
Erhoehung waere die Versionsnummer wertlos -- Disziplin bei kuenftigen Aenderungen an
core/audio.py noetig, siehe CONTRIBUTING.md."""

from __future__ import annotations

from datetime import datetime, timezone

import soundfile as sf

# Historie (bei jeder inhaltlichen Aenderung an core/audio.py-Berechnungen erhoehen):
# 1.0.0 (2026-08-20): Erstversion, deckt den Stand aller bis dahin vorhandenen Features ab
#                      (Jitter/Shimmer/HNR/CPPS/Formanten/DDK/Sprechrate/WER-CER/Alpha Ratio/
#                      Hammarberg-Index/Geschlechtsschaetzung/...).
FEATURE_SCHEMA_VERSION = "1.0.0"


def build_analysis_metadata(recording_path: str | None) -> dict:
    """Baut die Provenienz-Metadaten fuer EINEN Take -- wird zentral in
    core/module_state.py::add_take() aufgerufen, damit jede Aufnahme aus jedem der 4 Module
    automatisch dieselben Metadaten bekommt, ohne die einzelnen Modul-Seiten anfassen zu
    muessen.

    `analysis_timestamp` ist bewusst NICHT dasselbe wie `recorded_at` (Zeitpunkt der Aufnahme
    selbst, siehe add_take()) -- falls Aufnahmen spaeter re-analysiert werden (z.B. nach einem
    Bugfix), koennen beide Zeitpunkte auseinanderfallen.

    `audio_sampling_rate_hz` direkt aus der Datei gelesen statt angenommen -- wichtig, weil
    unsere eigenen Aufnahmen 48kHz nutzen, aber z.B. importierte externe Referenzdateien (SVD:
    50kHz, TORGO: 16kHz, siehe docs/externe_testdaten.md) davon abweichen koennen und das
    Ergebnisse beeinflussen kann."""
    metadata = {
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        "audio_sampling_rate_hz": None,
    }
    if recording_path:
        try:
            metadata["audio_sampling_rate_hz"] = sf.info(recording_path).samplerate
        except Exception:
            pass  # Datei (noch) nicht lesbar -- Metadaten bleiben unvollstaendig, kein Absturz
    return metadata


def take_provenance_caption(take: dict) -> str:
    """Einzeilige Herkunftsangabe fuer die Take-Verwaltung in den 4 Modul-Seiten. Takes aus
    Sitzungen vor Einfuehrung der Versionierung haben kein `analysis_metadata` -- dann nur der
    Dateiname, statt eine Version vorzutaeuschen, die nicht bekannt ist."""
    parts = [take.get("filename", "–")]
    meta = take.get("analysis_metadata") or {}
    if meta.get("feature_schema_version"):
        parts.append(f"Analyse v{meta['feature_schema_version']}")
    if meta.get("audio_sampling_rate_hz"):
        parts.append(f"{meta['audio_sampling_rate_hz']} Hz")
    return " · ".join(parts)
