"""Dateizugriff + Grundkennwerte + Phonation-Features (Parselmouth) für eine Aufnahme."""

import os
import re
from dataclasses import dataclass

import numpy as np
import parselmouth
import soundfile as sf

FILENAME_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2}_\d{4})_task-(?P<task>[a-zA-Z]+)_take(?P<take>\d+)\.wav$")


@dataclass
class Recording:
    patient_id: str
    filename: str
    path: str
    date: str
    task: str
    take: str


def list_patients(data_dir: str) -> list[str]:
    if not os.path.isdir(data_dir):
        return []
    return sorted(
        d for d in os.listdir(data_dir)
        if os.path.isdir(os.path.join(data_dir, d))
    )


def list_recordings(data_dir: str, patient_id: str) -> list[Recording]:
    patient_dir = os.path.join(data_dir, patient_id)
    if not os.path.isdir(patient_dir):
        return []
    recordings = []
    for fname in sorted(os.listdir(patient_dir)):
        if not fname.endswith(".wav"):
            continue
        match = FILENAME_RE.match(fname)
        if match:
            recordings.append(Recording(
                patient_id=patient_id,
                filename=fname,
                path=os.path.join(patient_dir, fname),
                date=match.group("date"),
                task=match.group("task"),
                take=match.group("take"),
            ))
        else:
            # Passt nicht ins Namensschema - trotzdem anzeigen, Task unbekannt
            recordings.append(Recording(
                patient_id=patient_id, filename=fname, path=os.path.join(patient_dir, fname),
                date="?", task="unbekannt", take="?",
            ))
    return recordings


_SUBTYPE_BITS = {"PCM_16": 16, "PCM_24": 24, "PCM_32": 32, "FLOAT": 32, "DOUBLE": 64}


def basic_stats(path: str) -> dict:
    info = sf.info(path)
    # dtype='float64' normalisiert Integer-Samples automatisch auf [-1, 1] -
    # WICHTIG: das muss VOR jeder Kanal-Mittelung passieren, sonst verliert man
    # die Information ueber den Wertebereich der Rohdaten (siehe Bugfix-Historie).
    samples, sample_rate = sf.read(path, dtype="float64", always_2d=True)
    samples_mono = samples.mean(axis=1)

    duration_s = len(samples_mono) / sample_rate
    peak = np.max(np.abs(samples_mono)) if len(samples_mono) else 0.0
    rms = np.sqrt(np.mean(samples_mono ** 2)) if len(samples_mono) else 0.0

    peak_dbfs = 20 * np.log10(peak) if peak > 0 else float("-inf")
    rms_dbfs = 20 * np.log10(rms) if rms > 0 else float("-inf")

    return {
        "duration_s": duration_s,
        "sample_rate": sample_rate,
        "bit_depth": _SUBTYPE_BITS.get(info.subtype, info.subtype),
        "channels": info.channels,
        "peak_dbfs": peak_dbfs,
        "rms_dbfs": rms_dbfs,
    }


def phonation_features(path: str) -> dict:
    """Stufe-1-Features (siehe docs/backlog.md): F0, Jitter, Shimmer, HNR via Parselmouth."""
    sound = parselmouth.Sound(path)

    pitch = sound.to_pitch()
    f0_values = pitch.selected_array["frequency"]
    f0_values = f0_values[f0_values > 0]
    f0_mean = float(np.mean(f0_values)) if len(f0_values) else None
    f0_sd = float(np.std(f0_values)) if len(f0_values) else None

    point_process = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", 75, 500)
    try:
        jitter_local = parselmouth.praat.call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
        shimmer_local = parselmouth.praat.call(
            [sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6
        )
    except Exception:
        jitter_local = None
        shimmer_local = None

    harmonicity = sound.to_harmonicity()
    hnr_values = harmonicity.values[harmonicity.values != -200]
    hnr_mean = float(np.mean(hnr_values)) if len(hnr_values) else None

    return {
        "f0_mean_hz": f0_mean,
        "f0_sd_hz": f0_sd,
        "jitter_local_pct": jitter_local * 100 if jitter_local is not None else None,
        "shimmer_local_pct": shimmer_local * 100 if shimmer_local is not None else None,
        "hnr_mean_db": hnr_mean,
    }


def formant_features(path: str) -> dict:
    """Stufe-2-Features (siehe docs/backlog.md): Formanten F1-F3 via Parselmouth.

    F1 korreliert mit Zungenhoehe (offen/geschlossen), F2 mit Zungenposition
    vorne/hinten -- siehe docs/literatur_review.md. Mittelwerte ueber die gesamte
    Aufnahme, kein Versuch einer vollen Vokalraum-Flaeche (dafuer braeuchte man
    mehrere unterschiedliche Vokale in einer Aufnahme, siehe Backlog-Hinweis).
    """
    sound = parselmouth.Sound(path)
    formant = sound.to_formant_burg()

    times = np.arange(formant.xmin, formant.xmax, 0.01)

    def _mean_formant(n: int) -> float | None:
        values = [formant.get_value_at_time(n, t) for t in times]
        values = [v for v in values if v is not None and not np.isnan(v)]
        return float(np.mean(values)) if values else None

    return {
        "f1_mean_hz": _mean_formant(1),
        "f2_mean_hz": _mean_formant(2),
        "f3_mean_hz": _mean_formant(3),
    }
