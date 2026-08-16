"""Dateizugriff + Grundkennwerte + Phonation-Features (Parselmouth) für eine Aufnahme."""

import os
import re
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import parselmouth
import soundfile as sf
from scipy.signal import find_peaks

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


# Phase A, Schritt 1 (Self-Service-Upload, siehe docs/backlog.md): eigener Patient-Namespace
# fuer hochgeladene Dateien, damit sie nie mit echten Testaufnahmen im selben Ordner landen.
UPLOAD_PATIENT_ID = "_uploads"
# Grosszuegiges Sicherheitsnetz -- bisherige 10s-Testaufnahmen (48kHz/24bit/stereo) liegen
# bei max. ~2,3MB, 25MB laesst deutlich Luft nach oben, verhindert aber trotzdem eine
# versehentlich riesige Datei/einen simplen DoS-Versuch ueber die Upload-Flaeche.
# Bewusst dezimal (1_000_000) definiert, NICHT 1024*1024 -- die Fehlermeldung unten
# rechnet mit derselben Einheit um, sonst zeigt sie z.B. "Limit 26 MB" bei "25 MB" Absicht.
MAX_UPLOAD_BYTES = 25 * 1_000_000

# Phase A, Schritt 2 (Self-Service-Upload, siehe docs/backlog.md): feste Task-Typ-Liste fuer
# Uploads, deckungsgleich mit den Task-Codes, die bislang aus Dateinamen geparst wurden
# (FILENAME_RE) -- "vokal" (gehaltenes /a/) kommt bisher aus keiner echten Testaufnahme,
# ist aber im Aufnahme-Konzept (docs/backlog.md "Patienten-Testprotokoll") vorgesehen.
UPLOAD_TASK_LABELS = {
    "lesetext": "Lesetext (Vorlesen)",
    "vokal": "Gehaltener Vokal /a/",
    "vokali": "Gehaltener Vokal /i/",
    "vokalu": "Gehaltener Vokal /u/",
    "ddkgemischt": "DDK kombiniert (\"pa-ta-ka\")",
    "ddkeinzeln": "DDK einzeln (pa / ta / ka nacheinander)",
    "spontan": "Spontansprache (freies Erzählen)",
    "unbekannt": "Unbekannt / Sonstiges",
}


def save_uploaded_wav(derived_dir: str, filename: str, data: bytes, task: str = "unbekannt") -> Recording:
    """Validiert + speichert eine hochgeladene WAV-Datei, gibt eine Recording zurueck.

    Bewusst als reine Funktion getrennt von der Streamlit-file_uploader-Widget-Logik in
    app.py, damit Validierung/Speicherung ohne laufende Streamlit-Session testbar sind
    (Streamlit AppTest unterstuetzt file_uploader-Interaktion nur eingeschraenkt).

    Speichert NICHT in `data_dir` (read-only gemountet, siehe docker-compose.yml), sondern
    in `derived_dir/_uploads/` -- getrennt vom eigenen Testdaten-Patienten. Ersetzt noch
    NICHT die Konvertierungs-/Verifikationslogik aus scripts/convert_and_verify.sh (nur
    WAV-Uploads, kein M4A/ALAC) -- das ist ein spaeterer Schritt (siehe docs/backlog.md
    "Self-Service-Upload", Schritt 4).

    Args:
        task: Task-Typ, wie ihn die/der Nutzer:in beim Upload ausgewaehlt hat (siehe
            UPLOAD_TASK_LABELS). Faellt auf "unbekannt" zurueck, falls ein unbekannter Wert
            hereinkommt -- verhindert, dass ein manipulierter/veralteter Aufrufer einen Wert
            einschleust, der nicht zur Ampel-/Fit-Logik (core/reference_ranges.py) passt.

    Raises:
        ValueError: bei zu grosser Datei oder wenn die Datei kein gueltiges, nicht-leeres
            WAV ist -- mit einer fuer die UI verstaendlichen Fehlermeldung.
    """
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError(
            f"Datei zu groß ({len(data) / 1_000_000:.1f} MB, Limit "
            f"{MAX_UPLOAD_BYTES / 1_000_000:.0f} MB)."
        )
    if len(data) == 0:
        raise ValueError("Datei ist leer.")
    if task not in UPLOAD_TASK_LABELS:
        task = "unbekannt"

    upload_dir = os.path.join(derived_dir, UPLOAD_PATIENT_ID)
    os.makedirs(upload_dir, exist_ok=True)

    # Dateiname sanitisieren -- kommt direkt vom Client, koennte theoretisch Pfad-
    # Traversal-Zeichen enthalten (../../etc). Nur alphanumerisch + . _ - erlaubt.
    safe_base = re.sub(r"[^a-zA-Z0-9_.-]", "_", os.path.basename(filename)) or "upload.wav"
    if not safe_base.lower().endswith(".wav"):
        safe_base += ".wav"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    unique_name = f"{timestamp}_{safe_base}"
    out_path = os.path.join(upload_dir, unique_name)

    with open(out_path, "wb") as f:
        f.write(data)

    try:
        info = sf.info(out_path)
        if info.duration <= 0:
            raise ValueError("Datei enthält keine Audiodaten (Dauer 0s).")
    except Exception as exc:
        os.remove(out_path)
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"Datei ist keine gültige WAV-Datei (Lesefehler: {exc}).") from exc

    return Recording(
        patient_id=UPLOAD_PATIENT_ID,
        filename=unique_name,
        path=out_path,
        date=timestamp[:10],
        task=task,
        take="1",
    )


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


SILENCE_THRESHOLD_DBFS = -40.0  # Fenster unterhalb gelten als "Stille" -- grobe Heuristik,
# noch nicht an echten Aufnahmen kalibriert (siehe Docstring unten).
CLIPPING_THRESHOLD = 0.99  # Anteil der Vollaussteuerung, ab dem ein Sample als "geklippt" zaehlt


def recording_quality_features(path: str, frame_ms: float = 30.0) -> dict:
    """Recording-Quality-Check (P6, siehe docs/backlog.md, externer Audit Prio 1) --
    SNR-Naeherung, Clipping-Anteil, Stille-Anteil aus den Rohdaten, ohne neue Abhaengigkeit
    (nutzt dieselbe soundfile-Basis wie basic_stats()).

    BEWUSST REIN INFORMATIV, KEIN HARTES CUTOFF-GATE (Nutzer-Prinzip aus
    [[feedback_signalverarbeitung_kennwerte]]: Schwellen erst an echten Aufnahmen
    kalibrieren, bevor irgendwas als "schlecht" markiert wird -- die Schwellen hier
    (SILENCE_THRESHOLD_DBFS/CLIPPING_THRESHOLD) sind grobe Startwerte, keine validierten
    Grenzwerte).

    SNR-Schaetzung: 90. Perzentil der Fenster-Lautstaerke (lauter/Sprach-Anteil) minus
    10. Perzentil (leiser, aber von Null verschiedener Anteil, Naeherung fuer den
    Rauschboden) -- kein echtes Signal-Rausch-Verhaeltnis im messtechnischen Sinn (dafuer
    braeuchte man eine echte Stille-Referenz ohne Sprache), aber ein brauchbarer
    Anhaltspunkt ohne zusaetzliches Tooling.

    Bugfix beim Testen gefunden (2026-08-15, synthetischer Test mit reiner Stille):
    ein erster Entwurf filterte Fenster mit RMS==0 VOR der Stille-Berechnung heraus --
    dadurch wurde reine Digitalstille faelschlich NICHT als Stille gezaehlt (0% statt 100%).
    Jetzt zwei getrennte Fenster-Reihen: `frame_db_all` (epsilon-geflooert, zaehlt ALLES
    fuer die Stille-Quote) vs. `frame_rms_nonzero` (nur fuer die SNR-Schaetzung, da reine
    Digital-Nullen kein realer Rauschboden sind und die Schaetzung sonst absurd aufblaehen
    -- bei echtem Mikrofon-Grundrauschen praktisch nie exakt Null, betrifft also v.a.
    synthetische Randfaelle/angehaengte Stille).
    """
    samples, sample_rate = sf.read(path, dtype="float64", always_2d=True)
    samples_mono = samples.mean(axis=1)
    n = len(samples_mono)
    empty = {"clipping_pct": None, "silence_pct": None, "snr_estimate_db": None}
    if n == 0:
        return empty

    clipping_pct = float(100 * np.mean(np.abs(samples_mono) >= CLIPPING_THRESHOLD))

    frame_len = max(1, int(sample_rate * frame_ms / 1000))
    n_frames = n // frame_len
    if n_frames == 0:
        return {**empty, "clipping_pct": clipping_pct}

    frames = samples_mono[: n_frames * frame_len].reshape(n_frames, frame_len)
    frame_rms = np.sqrt(np.mean(frames ** 2, axis=1))

    EPS = 1e-10
    frame_db_all = 20 * np.log10(np.maximum(frame_rms, EPS))
    silence_pct = float(100 * np.mean(frame_db_all < SILENCE_THRESHOLD_DBFS))

    frame_rms_nonzero = frame_rms[frame_rms > 0]
    if len(frame_rms_nonzero) < 2:
        snr_estimate_db = None
    else:
        frame_db_nonzero = 20 * np.log10(frame_rms_nonzero)
        snr_estimate_db = float(np.percentile(frame_db_nonzero, 90) - np.percentile(frame_db_nonzero, 10))

    return {
        "clipping_pct": clipping_pct,
        "silence_pct": silence_pct,
        "snr_estimate_db": snr_estimate_db,
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

    # RAP/PPQ5/APQ11 (P7/Audit, docs/backlog.md "Prio 1"): feinere Jitter-/Shimmer-Untermasse,
    # nutzen denselben point_process wie jitter/shimmer local -- technisch trivial, da die
    # Infrastruktur schon da ist. RAP = 3-Punkt-, PPQ5 = 5-Punkt-Periodenperturbation, APQ11 =
    # 11-Punkt-Amplitudenperturbation (glaetten jeweils ueber mehr Nachbarzyklen als "local",
    # dadurch robuster gegen einzelne Ausreisser-Zyklen). Wie lokal nur bei gehaltenem Vokal
    # zuverlaessig interpretierbar.
    try:
        jitter_rap = parselmouth.praat.call(point_process, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3)
        jitter_ppq5 = parselmouth.praat.call(point_process, "Get jitter (ppq5)", 0, 0, 0.0001, 0.02, 1.3)
        shimmer_apq11 = parselmouth.praat.call(
            [sound, point_process], "Get shimmer (apq11)", 0, 0, 0.0001, 0.02, 1.3, 1.6
        )
    except Exception:
        jitter_rap = None
        jitter_ppq5 = None
        shimmer_apq11 = None

    harmonicity = sound.to_harmonicity()
    hnr_values = harmonicity.values[harmonicity.values != -200]
    hnr_mean = float(np.mean(hnr_values)) if len(hnr_values) else None

    return {
        "f0_mean_hz": f0_mean,
        "f0_sd_hz": f0_sd,
        "jitter_local_pct": jitter_local * 100 if jitter_local is not None else None,
        "shimmer_local_pct": shimmer_local * 100 if shimmer_local is not None else None,
        "jitter_rap_pct": jitter_rap * 100 if jitter_rap is not None else None,
        "jitter_ppq5_pct": jitter_ppq5 * 100 if jitter_ppq5 is not None else None,
        "shimmer_apq11_pct": shimmer_apq11 * 100 if shimmer_apq11 is not None else None,
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


MAX_ADJACENT_FRAME_GAP_S = 0.03  # Formant-Frames weiter auseinander gelten als nicht direkt benachbart
# Physiologisch plausible Bereiche fuer erwachsene Sprecher (grosszuegig, beide Geschlechter).
# Noetig, weil Praats Formant-Tracker (to_formant_burg) gelegentlich auf falsche Spektralpeaks
# "springt" (z.B. F1 faelschlich >1500Hz) -- verifiziert an Take 3: ~10% der Frames ausserhalb
# dieses Bereichs, klar erkennbare Tracking-Fehler, keine echten Sprachwerte.
F1_PLAUSIBLE_RANGE_HZ = (150, 1100)
F2_PLAUSIBLE_RANGE_HZ = (500, 3500)


def formant_dynamics_features(path: str) -> dict:
    """Zeitaufgeloeste Formantanalyse (Audit 2026-07-22) -- Grundlage fuer Vokalzentralisierung
    und Formant-Dynamik, die formant_features() (reiner Ganzaufnahme-Mittelwert) nicht liefern kann.

    EHRLICHKEIT UEBER DIE GRENZEN: Ohne Phonem-/Vokal-Identifikation (wir haben nur Wort-
    Zeitstempel, keine Silben-/Lautsegmentierung) ist dies KEIN Ersatz fuer die klassische
    Vokalraum-Flaeche (VSA, feste Eckvokale i/a/u -- siehe docs/backlog.md, weiterhin nicht
    moeglich). Stattdessen zwei einfachere, aber ehrliche Annaeherungen:

    - Formant-Streuung (Dispersion) ueber alle stimmhaften Abschnitte: ein Proxy dafuer, wie
      viel vokalischer Raum in der Aufnahme ueberhaupt genutzt wird. Schmale Streuung KANN auf
      Zentralisierung hindeuten, ist aber kein direkter Ersatz fuer eine echte VSA-Messung.
    - Formant-Geschwindigkeit (F1-/F2-Aenderung pro Zeit): wie schnell sich die Formanten
      aendern, als Naeherung fuer Zungen-/Kieferbeweglichkeit -- funktioniert OHNE Vokal-Identitaet.

    Nur stimmhafte Frames (ueber die Pitch-Kontur bestimmt) werden beruecksichtigt, da
    Formant-Schaetzungen bei Stille/stimmlosen Lauten unzuverlaessig sind. Geschwindigkeiten
    werden nur zwischen zeitlich direkt benachbarten Frames berechnet (siehe
    MAX_ADJACENT_FRAME_GAP_S) -- sonst wuerde ein Sprung ueber eine stimmlose Luecke
    faelschlich als schnelle Formant-Bewegung gezaehlt.
    """
    sound = parselmouth.Sound(path)
    pitch = sound.to_pitch()
    formant = sound.to_formant_burg()

    times = pitch.xs()
    f0_values = pitch.selected_array["frequency"]
    voiced_times = times[f0_values > 0]

    f1_lo, f1_hi = F1_PLAUSIBLE_RANGE_HZ
    f2_lo, f2_hi = F2_PLAUSIBLE_RANGE_HZ

    f1_list, f2_list, t_list = [], [], []
    for t in voiced_times:
        f1 = formant.get_value_at_time(1, t)
        f2 = formant.get_value_at_time(2, t)
        if (
            f1 is not None and f2 is not None and not np.isnan(f1) and not np.isnan(f2)
            and f1_lo <= f1 <= f1_hi and f2_lo <= f2 <= f2_hi
        ):
            f1_list.append(f1)
            f2_list.append(f2)
            t_list.append(t)

    f1_arr = np.array(f1_list)
    f2_arr = np.array(f2_list)
    t_arr = np.array(t_list)

    empty_result = {
        "n_voiced_frames": len(f1_arr),
        "f1_range_hz": None, "f2_range_hz": None,
        "f1_iqr_hz": None, "f2_iqr_hz": None,
        "f1_velocity_mean_hz_s": None, "f1_velocity_max_hz_s": None,
        "f2_velocity_mean_hz_s": None,
    }
    if len(f1_arr) < 2:
        return empty_result

    f1_velocities, f2_velocities = [], []
    for i in range(1, len(t_arr)):
        dt = t_arr[i] - t_arr[i - 1]
        if 0 < dt <= MAX_ADJACENT_FRAME_GAP_S:
            f1_velocities.append(abs(f1_arr[i] - f1_arr[i - 1]) / dt)
            f2_velocities.append(abs(f2_arr[i] - f2_arr[i - 1]) / dt)

    return {
        "n_voiced_frames": len(f1_arr),
        "f1_range_hz": float(np.max(f1_arr) - np.min(f1_arr)),
        "f2_range_hz": float(np.max(f2_arr) - np.min(f2_arr)),
        "f1_iqr_hz": float(np.percentile(f1_arr, 75) - np.percentile(f1_arr, 25)),
        "f2_iqr_hz": float(np.percentile(f2_arr, 75) - np.percentile(f2_arr, 25)),
        "f1_velocity_mean_hz_s": float(np.mean(f1_velocities)) if f1_velocities else None,
        "f1_velocity_max_hz_s": float(np.max(f1_velocities)) if f1_velocities else None,
        "f2_velocity_mean_hz_s": float(np.mean(f2_velocities)) if f2_velocities else None,
    }


def prosody_features(path: str) -> dict:
    """Stufe-4-Features (siehe docs/backlog.md): Monoloudness via Parselmouth.

    Monoloudness = SD(Intensitaet) ueber die gesamte Aeusserung -- klassischer PD-Marker
    (reduzierte Variabilitaet = auffaellig), siehe docs/literatur_review.md. Monopitch
    (SD(F0)) wird bewusst NICHT hier nochmal berechnet -- der Wert ist identisch mit
    "F0 Standardabweichung" aus phonation_features() (Stufe 1) und wird von dort
    wiederverwendet, um doppelte Berechnung/Anzeige desselben Werts zu vermeiden.
    """
    sound = parselmouth.Sound(path)

    intensity = sound.to_intensity()
    intensity_values = intensity.values[0]
    # Praat markiert "keine definierte Intensitaet" (Stille) mit dem Sentinel-Wert -300 dB --
    # das ist kein echter Messwert und muss raus, sonst wird die SD massiv durch den
    # Stille/Sprache-Kontrast an den Raendern verzerrt statt die eigentliche Modulation
    # innerhalb der Sprache abzubilden (siehe docs/bugtracker.md).
    intensity_values = intensity_values[(~np.isnan(intensity_values)) & (intensity_values > -300)]
    intensity_sd = float(np.std(intensity_values)) if len(intensity_values) else None

    return {
        "monoloudness_intensity_sd_db": intensity_sd,
    }


def articulation_features(path: str) -> dict:
    """Stufe-5-Features (siehe docs/backlog.md): Verschluss-/Burst-Erkennung als
    generischer Artikulationsschaerfe-Indikator.

    WICHTIG (Scope, mit Blick auf das Dysarthrie-Fernziel des Projekts): Das hier ist
    KEINE phonetische Erkennung einzelner Laute/Plosive -- es erkennt rein akustisch
    Verschluss-Loese-Muster (kurzer Energieeinbruch, gefolgt von einem scharfen
    Wiederanstieg) in der Intensitaetskontur, ohne zu wissen, ob/welcher Konsonant
    gemeint war. Ziel ist eine grobe Gradmesser-Kennzahl ("wie viele klare, scharfe
    Verschluss-Gesten enthaelt die Aufnahme, wie lang sind die Verschluesse") --
    passend zum Nutzerziel "Schweregrad einordnen, nicht Inhalt entschluesseln"
    (2026-07-21). Bei eingeschraenkter Zungenbeweglichkeit (z.B. bulbaere Dysarthrie)
    waeren weniger/unschaerfere/laengere Verschluss-Ereignisse zu erwarten -- diese
    Referenzwerte hier stammen aber nur von gesunden Testaufnahmen, noch keine
    dysarthrische Vergleichsaufnahme vorhanden (siehe docs/backlog.md).

    Deutsche Besonderheit (siehe docs/literatur_review.md): Fortis/Lenis wird im
    Deutschen primaer ueber Verschlussdauer signalisiert, nicht ueber Aspiration/VOT --
    macht Verschlussdauer als Kennzahl besonders relevant fuer diese Sprache. VOT wird
    hier trotzdem zusaetzlich als Zusatzmass gemessen (Audit 2026-07-22), da es in der
    internationalen Literatur trotzdem haeufig zitiert wird -- Zeit von der Verschluss-
    loesung (Burst-Beginn) bis zum ersten stimmhaften Pitch-Frame danach.
    """
    sound = parselmouth.Sound(path)
    intensity = sound.to_intensity()
    pitch = sound.to_pitch()
    pitch_times = pitch.xs()
    pitch_f0 = pitch.selected_array["frequency"]

    times = intensity.xs()
    values = intensity.values[0].copy()

    valid = (~np.isnan(values)) & (values > -300)
    times = times[valid]
    values = values[valid]

    if len(values) < 10:
        return {
            "n_stop_events": 0, "mean_closure_duration_s": None, "mean_burst_sharpness_db_s": None,
            "mean_vot_s": None, "vot_count": 0,
        }

    dt = float(np.median(np.diff(times)))

    # Taeler = potenzielle Verschluesse: lokale Minima mit ausreichend Tiefe (Prominence),
    # damit normales Sprechrauschen nicht faelschlich als Verschluss zaehlt.
    valley_idx, _ = find_peaks(-values, prominence=8, distance=max(1, int(0.03 / dt)))

    closure_durations = []
    burst_sharpness = []
    vot_durations = []
    VOT_MAX_WINDOW_S = 0.15  # VOT ueberschreitet selbst bei starker Aspiration selten 100-150ms

    for idx in valley_idx:
        valley_val = values[idx]

        # Verschlussdauer: wie lange bleibt der Pegel nahe am Minimum (innerhalb 3 dB)?
        left = idx
        while left > 0 and values[left - 1] <= valley_val + 3:
            left -= 1
        right = idx
        while right < len(values) - 1 and values[right + 1] <= valley_val + 3:
            right += 1
        closure_duration = times[right] - times[left]

        # Nur plausibler Bereich fuer eine Plosiv-Verschlussdauer (siehe Literatur-Review:
        # deutsche Lenis ~5-20ms, Fortis ~40-60ms) -- alles ausserhalb ist vermutlich eine
        # laengere Sprechpause, kein einzelner Verschlusslaut.
        if not (0.01 <= closure_duration <= 0.3):
            continue

        # Burst-Schaerfe: staerkster Wiederanstieg in den 60ms nach dem Minimum.
        window_end = min(len(values), idx + max(2, int(0.06 / dt)))
        if window_end <= idx + 1:
            continue
        rise = values[window_end - 1] - values[idx]
        time_span = times[window_end - 1] - times[idx]
        if time_span <= 0 or rise <= 0:
            continue

        closure_durations.append(closure_duration)
        burst_sharpness.append(rise / time_span)

        # VOT: Zeit von der Verschlussloesung (Burst-Beginn, times[idx]) bis zum ersten
        # stimmhaften Pitch-Frame danach, innerhalb eines physiologisch plausiblen Fensters.
        release_time = times[idx]
        window_mask = (pitch_times >= release_time) & (pitch_times <= release_time + VOT_MAX_WINDOW_S)
        voiced_after = pitch_times[window_mask][pitch_f0[window_mask] > 0]
        if len(voiced_after) > 0:
            vot_durations.append(float(voiced_after[0] - release_time))

    return {
        "n_stop_events": len(closure_durations),
        "mean_closure_duration_s": float(np.mean(closure_durations)) if closure_durations else None,
        "mean_burst_sharpness_db_s": float(np.mean(burst_sharpness)) if burst_sharpness else None,
        "mean_vot_s": float(np.mean(vot_durations)) if vot_durations else None,
        "vot_count": len(vot_durations),
    }


def cpp_features(path: str) -> dict:
    """Stufe-6-Features (siehe docs/backlog.md): CPPS (Cepstral Peak Prominence, geglaettet)
    via Parselmouth/Praat.

    Robusteres Alternativmass zu Jitter/Shimmer bei Fliessprache/Lesetext -- CPPS braucht
    KEINE periodische, gehaltene Phonation und funktioniert deshalb genau bei dem Task-Typ,
    den wir hauptsaechlich sammeln (siehe docs/literatur_review.md). Parameter folgen den
    ueblichen CPPS-Konventionen aus der Stimmklinik-Literatur (Hillenbrand/Heman-Ackah-Stil):
    Pitch-Boden 60Hz, Zeitmittelungsfenster 10ms, Quefrenz-Mittelungsfenster 1ms,
    Trendlinie linear ("Straight"), robuste Anpassung.

    WICHTIG: CPPS-Werte sind stark parameterabhaengig (Fenstergroessen, Trendlinien-Methode) --
    Zahlen aus anderen Tools/Studien nicht ungeprueft als Normwert uebernehmen, siehe
    docs/bugtracker.md-Prinzip "MDVP- und Praat-Normwerte sind nicht direkt vergleichbar".
    """
    sound = parselmouth.Sound(path)
    power_cepstrogram = parselmouth.praat.call(sound, "To PowerCepstrogram", 60, 0.002, 5000, 50)
    cpps_db = parselmouth.praat.call(
        power_cepstrogram, "Get CPPS", True, 0.01, 0.001, 60, 330, 0.05,
        "Parabolic", 0.001, 0.05, "Straight", "Robust",
    )
    return {"cpps_db": float(cpps_db)}


def phonation_dynamics_features(path: str) -> dict:
    """Erweiterung zu Stufe 1 (Audit 2026-07-22): geht ueber die reine Momentaufnahme
    (Mittelwert/SD) hinaus.

    F0-Perzentile und Pitch Slope sind aus JEDER Aufnahme berechenbar (immer auswertbar).
    Voice Breaks (Praats Standard-"Voice report") dagegen sind -- genau wie Jitter/Shimmer --
    nur bei GEHALTENEM VOKAL sauber interpretierbar: bei Fliessprache erzeugen normale
    Wortpausen und stimmlose Konsonanten (s, f, ch, ...) zwangslaeufig viele "Breaks", die
    nichts mit einer pathologischen Stimmbandfunktion zu tun haben. Verifiziert an Take 3
    (Lesetext): 24 Voice Breaks, 26% Anteil -- das ist bei Fliessprache erwartbar hoch und
    NICHT als Auffaelligkeit zu werten (siehe docs/bugtracker.md-Prinzip Jitter/Shimmer).
    """
    sound = parselmouth.Sound(path)
    pitch = sound.to_pitch()
    f0_values = pitch.selected_array["frequency"]
    voiced = f0_values[f0_values > 0]

    f0_p5 = float(np.percentile(voiced, 5)) if len(voiced) else None
    f0_p95 = float(np.percentile(voiced, 95)) if len(voiced) else None

    # Pitch Slope: linearer Trend der F0-Kontur ueber die Zeit (Hz/s) -- Fatigue-Marker.
    # Bei kurzen ~10s-Snippets ist der Trend vermutlich verrauscht/wenig aussagekraeftig,
    # bei laengeren Freisprache-Aufnahmen aber sinnvoll (siehe docs/backlog.md).
    times = pitch.xs()
    voiced_mask = f0_values > 0
    if voiced_mask.sum() >= 2:
        slope, _ = np.polyfit(times[voiced_mask], f0_values[voiced_mask], 1)
        pitch_slope_hz_per_s = float(slope)
    else:
        pitch_slope_hz_per_s = None

    point_process = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", 75, 500)
    report = parselmouth.praat.call(
        [sound, pitch, point_process], "Voice report", 0, 0, 75, 500, 1.3, 1.6, 0.03, 0.45,
    )
    breaks_match = re.search(r"Number of voice breaks:\s*(\d+)", report)
    degree_match = re.search(r"Degree of voice breaks:\s*([\d.]+)%", report)

    return {
        "f0_p5_hz": f0_p5,
        "f0_p95_hz": f0_p95,
        "pitch_slope_hz_per_s": pitch_slope_hz_per_s,
        "voice_breaks_count": int(breaks_match.group(1)) if breaks_match else None,
        "voice_breaks_degree_pct": float(degree_match.group(1)) if degree_match else None,
    }


def mpt_features(path: str) -> dict:
    """Maximum Phonation Time (MPT, P7/Audit 2026-08-15, docs/backlog.md "Prio 1") -- laengste
    zusammenhaengende stimmhafte Passage in einer Aufnahme. Klassisches Stimm-/Atemreserve-Mass
    (z.B. bei ALS/neurologischen Erkrankungen mit Atemschwaeche reduziert). Nutzt dieselbe
    Pitch-Kontur wie phonation_dynamics_features(), aber eigene Berechnung (laengste
    zusammenhaengende Voiced-Serie statt Anzahl Unterbrechungen).

    WICHTIG: nur aussagekraeftig, wenn die Aufnahme-Instruktion "so lange wie moeglich halten"
    war -- bei normalen kurzen Vokalaufnahmen (2-3s) ist der Wert nur die aufgenommene Dauer,
    nicht die tatsaechliche maximale Phonationsdauer der Person (siehe docs/backlog.md, MPT
    braucht eigentlich einen eigenen Aufnahme-Task).
    """
    sound = parselmouth.Sound(path)
    pitch = sound.to_pitch()
    times = pitch.xs()
    f0_values = pitch.selected_array["frequency"]

    if len(times) < 2:
        return {"mpt_s": None, "n_voiced_segments": 0}

    dt = float(times[1] - times[0])
    voiced_mask = f0_values > 0

    max_run = 0
    current_run = 0
    n_segments = 0
    prev_voiced = False
    for is_voiced in voiced_mask:
        if is_voiced:
            current_run += 1
            if not prev_voiced:
                n_segments += 1
        else:
            max_run = max(max_run, current_run)
            current_run = 0
        prev_voiced = is_voiced
    max_run = max(max_run, current_run)

    return {
        "mpt_s": max_run * dt if max_run > 0 else None,
        "n_voiced_segments": n_segments,
    }


TREMOR_BAND_HZ = (3.0, 15.0)  # physiologischer/pathologischer Stimmtremor liegt typ. bei 4-12 Hz


def f0_tremor_features(path: str) -> dict:
    """F0-Tremor-Analyse (P7/Audit 2026-08-15, docs/backlog.md "Prio 2") -- Spektralanalyse der
    Grundfrequenz-ZEITREIHE selbst (nicht des Rohsignals), um rhythmische Tonhoehen-
    Oszillationen zu erkennen. Interessant fuer die Differenzierung Parkinson- vs. essenzieller
    Tremor laut externem Audit -- hier bewusst nur als deskriptiver Peak/Staerke-Wert, KEINE
    automatische Tremor-Diagnose oder -Klassifikation.

    Ablauf: stimmhafte F0-Werte auf ein gleichabstaendiges Zeitraster interpolieren (Pitch-
    Frames sind ueber stimmlose Luecken hinweg nicht zwingend zusammenhaengend), linearen Trend
    entfernen (sonst dominiert der bereits an anderer Stelle erfasste Pitch Slope das Spektrum),
    dann FFT/Periodogramm im 3-15Hz-Band. EHRLICHKEIT UEBER DIE GRENZEN: braucht genug
    stimmhafte Dauer fuer eine sinnvolle Frequenzaufloesung -- bei kurzen ~2-3s-Vokalaufnahmen
    ist die Aufloesung grob, Tremor unterhalb weniger Hz laesst sich kaum von normalem Pitch-
    Rauschen trennen. Nicht klinisch validiert, rein explorativ.
    """
    sound = parselmouth.Sound(path)
    pitch = sound.to_pitch()
    times = pitch.xs()
    f0_values = pitch.selected_array["frequency"]
    voiced_mask = f0_values > 0

    empty = {"tremor_freq_hz": None, "tremor_amplitude_hz": None, "tremor_power_ratio": None}
    if voiced_mask.sum() < 20 or len(times) < 2:
        return empty

    t_voiced = times[voiced_mask]
    f0_voiced = f0_values[voiced_mask]
    dt = float(times[1] - times[0])

    t_grid = np.arange(t_voiced[0], t_voiced[-1], dt)
    if len(t_grid) < 20:
        return empty
    f0_grid = np.interp(t_grid, t_voiced, f0_voiced)

    detrended = f0_grid - np.polyval(np.polyfit(t_grid, f0_grid, 1), t_grid)
    windowed = detrended * np.hanning(len(detrended))

    freqs = np.fft.rfftfreq(len(windowed), d=dt)
    power = np.abs(np.fft.rfft(windowed)) ** 2

    lo, hi = TREMOR_BAND_HZ
    band_mask = (freqs >= lo) & (freqs <= hi)
    if not band_mask.any() or power.sum() == 0:
        return empty

    band_freqs = freqs[band_mask]
    band_power = power[band_mask]
    peak_idx = int(np.argmax(band_power))

    return {
        "tremor_freq_hz": float(band_freqs[peak_idx]),
        # grobe Amplitude-Naeherung aus der Spektralleistung (Hanning-Fenster-Skalierung) --
        # kein kalibriertes Absolutmass, nur fuer den Eigenvergleich zwischen Aufnahmen gedacht.
        "tremor_amplitude_hz": float(np.sqrt(band_power[peak_idx]) / len(windowed) * 2),
        "tremor_power_ratio": float(band_power[peak_idx] / power.sum()),
    }


def vowel_space_area(f1_a, f2_a, f1_i, f2_i, f1_u, f2_u) -> float | None:
    """Klassische Vokalraum-Flaeche (VSA, P7/Audit 2026-08-15, docs/backlog.md "Prio 1") nach
    der Dreiecksformel (Shoelace) fuer die Eckvokale /a/, /i/, /u/ im F1-F2-Formantraum.
    Braucht Formant-Mittelwerte aus 3 GETRENNTEN Aufnahmen (Vokalisation-Modul: /a/ Pflicht,
    /i/+/u/ optional) -- anders als die uebrigen Funktionen hier arbeitet diese NICHT auf einer
    einzelnen Sound-Datei, sondern auf bereits berechneten formant_features()-Werten dreier
    Takes, wird also aus der UI-Ebene (views/vokalisation.py) heraus aufgerufen, nicht aus einem
    einzelnen `path`.

    Formel: VSA = 0.5 * |F1i*(F2a-F2u) + F1a*(F2u-F2i) + F1u*(F2i-F2a)| (Flaeche eines Dreiecks
    aus 3 Punkten in der Ebene). Kleinere Flaeche = staerker zentralisierter Vokalraum, gilt in
    der Literatur als moeglicher Hinweis auf Artikulationsundeutlichkeit/Dysarthrie.
    """
    values = (f1_a, f2_a, f1_i, f2_i, f1_u, f2_u)
    if any(v is None for v in values):
        return None
    return 0.5 * abs(f1_i * (f2_a - f2_u) + f1_a * (f2_u - f2_i) + f1_u * (f2_i - f2_a))


MFCC_N_COEFFS = 12


def mfcc_features(path: str, n_coeffs: int = MFCC_N_COEFFS) -> dict:
    """Stufe-2-Feature (Audit 2026-07-22): MFCCs (Mel-Frequency Cepstral Coefficients) --
    allgemeine Klangfarben-Beschreibung, ergaenzt die formantbasierten Merkmale.

    Nutzt Praats natives "To MFCC"-Kommando + `to_array()` fuer eine schnelle Matrix-
    Extraktion (kein langsames Frame-fuer-Frame-Auslesen ueber einzelne Praat-Aufrufe).
    Der 0. Koeffizient (Gesamtenergie) wird bewusst ausgelassen -- das deckt sich bereits
    mit der bestehenden Monoloudness-Kennzahl (Intensitaets-SD, siehe prosody_features()),
    keine Redundanz noetig. Nur stimmhafte Frames (ueber die Pitch-Kontur bestimmt) werden
    beruecksichtigt, analog zu formant_dynamics_features() -- reduziert Kontamination durch
    Stille/Hintergrundrauschen an den Aufnahmeraendern.

    WICHTIGER VORBEHALT (verifiziert an allen 3 Testaufnahmen, 2026-07-22): MFCCs 1-4
    streuen zwischen den drei unabhaengigen Lesungen desselben Texts deutlich mehr als
    andere Kennzahlen in diesem Projekt (z.B. Formanten) -- das liegt vermutlich an
    Aufnahmebedingungen (Mikrofonabstand/-ausrichtung, Raumakustik), nicht an echten
    Sprechunterschieden. MFCCs sind literaturbekannt kanal-/mikrofonempfindlich (in der
    ASR-Forschung wird das ueblicherweise mit "Cepstral Mean Normalization" kompensiert,
    hier bewusst NICHT gemacht). Werte sind deshalb v.a. INNERHALB derselben Aufnahme-
    Session vergleichbar, nicht unbedingt ueber Sessions mit unterschiedlichem Aufnahme-
    Setup hinweg.
    """
    sound = parselmouth.Sound(path)
    mfcc = parselmouth.praat.call(sound, "To MFCC", n_coeffs, 0.015, 0.005, 100, 100, 0)
    arr = mfcc.to_array()  # shape (n_coeffs+1, n_frames); Zeile 0 = C0 (Energie), ausgelassen

    pitch = sound.to_pitch()
    pitch_times = pitch.xs()
    voiced_pitch_times = pitch_times[pitch.selected_array["frequency"] > 0]

    n_frames = arr.shape[1]
    frame_times = np.array([mfcc.frame_number_to_time(i + 1) for i in range(n_frames)])
    # Ein MFCC-Frame gilt als stimmhaft, wenn es nahe (< 5ms) an einem stimmhaften Pitch-Frame liegt.
    voiced_mask = np.zeros(n_frames, dtype=bool)
    if len(voiced_pitch_times) > 0:
        for i, t in enumerate(frame_times):
            voiced_mask[i] = np.min(np.abs(voiced_pitch_times - t)) < 0.005

    means = {}
    for c in range(1, n_coeffs + 1):
        row = arr[c][voiced_mask]
        row = row[np.isfinite(row)]
        means[f"mfcc_{c}_mean"] = float(np.mean(row)) if len(row) else None
    return means


PHRASE_GAP_THRESHOLD_S = 0.25  # ab hier gilt eine Stimmluecke als Phrasengrenze, nicht nur Konsonant
MIN_PHRASE_DURATION_S = 0.3
MIN_PHRASE_POINTS = 3
FLAT_SLOPE_THRESHOLD_HZ_S = 5.0  # |Steigung| darunter gilt als "flach", nicht steigend/fallend


def intonation_contour_features(path: str) -> dict:
    """Stufe-4-Feature (Audit 2026-07-22): Intonationskontur pro Phrase statt nur ein
    einziger Trend ueber die gesamte Aufnahme (siehe phonation_dynamics_features()
    "Pitch Slope", das nur einen Gesamttrend liefert).

    Segmentiert rein akustisch (ueber Luecken in der stimmhaften Pitch-Kontur, OHNE
    Transkript-Abhaengigkeit -- funktioniert also auch ohne Chunk-5-Transkription) in
    "Phrasen" und klassifiziert pro Phrase einen linearen Trend als steigend/fallend/flach.
    Bewusst erster, einfacher Wurf: nur linearer Trend, keine Kruemmungs-/Formanalyse der
    Kontur (das waere ein groesserer Ausbauschritt, siehe docs/backlog.md).
    """
    sound = parselmouth.Sound(path)
    pitch = sound.to_pitch()
    times = pitch.xs()
    f0_values = pitch.selected_array["frequency"]

    voiced_idx = np.where(f0_values > 0)[0]
    if len(voiced_idx) < MIN_PHRASE_POINTS:
        return {"n_phrases": 0, "pct_falling": None, "pct_rising": None, "pct_flat": None, "mean_phrase_slope_hz_s": None}

    # Phrasengrenzen: Luecken zwischen aufeinanderfolgenden stimmhaften Frames, die groesser
    # als PHRASE_GAP_THRESHOLD_S sind (Pause/laengere stimmlose Passage), nicht jede einzelne
    # kurze Konsonanten-Unterbrechung.
    phrase_bounds = [0]
    for i in range(1, len(voiced_idx)):
        gap = times[voiced_idx[i]] - times[voiced_idx[i - 1]]
        if gap > PHRASE_GAP_THRESHOLD_S:
            phrase_bounds.append(i)
    phrase_bounds.append(len(voiced_idx))

    slopes = []
    for start, end in zip(phrase_bounds, phrase_bounds[1:]):
        idx = voiced_idx[start:end]
        if len(idx) < MIN_PHRASE_POINTS:
            continue
        phrase_times = times[idx]
        if phrase_times[-1] - phrase_times[0] < MIN_PHRASE_DURATION_S:
            continue
        slope, _ = np.polyfit(phrase_times, f0_values[idx], 1)
        slopes.append(float(slope))

    if not slopes:
        return {"n_phrases": 0, "pct_falling": None, "pct_rising": None, "pct_flat": None, "mean_phrase_slope_hz_s": None}

    n = len(slopes)
    n_falling = sum(1 for s in slopes if s < -FLAT_SLOPE_THRESHOLD_HZ_S)
    n_rising = sum(1 for s in slopes if s > FLAT_SLOPE_THRESHOLD_HZ_S)
    n_flat = n - n_falling - n_rising

    return {
        "n_phrases": n,
        "pct_falling": 100 * n_falling / n,
        "pct_rising": 100 * n_rising / n,
        "pct_flat": 100 * n_flat / n,
        "mean_phrase_slope_hz_s": float(np.mean(slopes)),
    }


MIN_DDK_CYCLES = 3  # unter 3 erkannten Zyklen ist eine Rate/Regelmaessigkeit nicht sinnvoll interpretierbar


def ddk_rate_features(path: str) -> dict:
    """Diadochokinese-Rate (Stufe 3, siehe docs/backlog.md) -- Silbenzyklen/Sekunde beim
    "pa-ta-ka"-Task, jetzt umsetzbar seit den DDK-Testaufnahmen vom 2026-07-24.

    Nutzt bewusst DIESELBE Verschluss-/Burst-Erkennung (Taeler in der Intensitaetskontur,
    gleiche Prominence-/Plausibilitaetsschwellen) wie articulation_features(), NICHT ueber
    einen Refactor geteilt -- die bestehende Erkennung ist an gesunden Aufnahmen kalibriert
    und wird hier bewusst unangetastet gelassen (siehe feedback zu Vorsicht bei Aenderungen
    an bereits verifizierter Signal-Erkennung), nur der Rueckgabewert unterscheidet sich
    (Zyklus-Zeitpunkte statt nur Verschlussdauer/Burst-Schaerfe).

    Liefert Rate (Zyklen/Sekunde, netto ueber die Gesamtdauer) UND eine Regelmaessigkeits-
    Kennzahl (Variationskoeffizient der Zyklus-Intervalle) -- unregelmaessige DDK-Raten
    sind in der Literatur ein moeglicher Hinweis auf ataktische Dysarthrie, nicht nur die
    reine Rate.
    """
    sound = parselmouth.Sound(path)
    intensity = sound.to_intensity()

    times = intensity.xs()
    values = intensity.values[0].copy()

    valid = (~np.isnan(values)) & (values > -300)
    times = times[valid]
    values = values[valid]

    empty = {
        "n_cycles": 0, "duration_s": sound.duration, "ddk_rate_hz": None,
        "mean_cycle_interval_s": None, "cycle_interval_cv": None, "cycle_times": [],
    }
    if len(values) < 10:
        return empty

    dt = float(np.median(np.diff(times)))
    valley_idx, _ = find_peaks(-values, prominence=8, distance=max(1, int(0.03 / dt)))

    cycle_times = []
    for idx in valley_idx:
        valley_val = values[idx]
        left = idx
        while left > 0 and values[left - 1] <= valley_val + 3:
            left -= 1
        right = idx
        while right < len(values) - 1 and values[right + 1] <= valley_val + 3:
            right += 1
        closure_duration = times[right] - times[left]
        if not (0.01 <= closure_duration <= 0.3):
            continue
        cycle_times.append(float(times[idx]))

    n_cycles = len(cycle_times)
    duration_s = sound.duration
    if n_cycles < MIN_DDK_CYCLES:
        return {**empty, "n_cycles": n_cycles}

    ddk_rate_hz = n_cycles / duration_s if duration_s > 0 else None

    intervals = np.diff(cycle_times)
    mean_interval = float(np.mean(intervals)) if len(intervals) else None
    cycle_interval_cv = (
        float(np.std(intervals) / mean_interval) if mean_interval and mean_interval > 0 else None
    )

    return {
        "n_cycles": n_cycles,
        "duration_s": duration_s,
        "ddk_rate_hz": ddk_rate_hz,
        "mean_cycle_interval_s": mean_interval,
        "cycle_interval_cv": cycle_interval_cv,
        # Rohdaten fuer die DDK-Rhythmus-Spur (docs/konzept_visualisierungen.md 3.3) -- rein
        # additiv, aendert nichts an der bestehenden, bewusst unangetasteten Erkennung oben.
        # Kein PARAMETER_INFO-Eintrag dafuer noetig: build_rows()/build_tiles() iterieren nur
        # ueber bekannte PARAMETER_INFO-Schluessel, ignorieren also diesen zusaetzlichen Key.
        "cycle_times": cycle_times,
    }
