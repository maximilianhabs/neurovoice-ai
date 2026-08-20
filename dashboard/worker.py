"""P9 — Hintergrund-Worker fuer die Transkription (siehe docs/konzept_p9_hintergrundjob_lokal.md
fuer das volle Konzept). Laeuft als EIGENER Container/Prozess, getrennt vom Streamlit-UI-Prozess
(app.py) -- pollt core/job_queue.py nach wartenden Jobs, verarbeitet sie, schreibt Ergebnis +
Transkript-Cache zurueck. Dieselben Docker-Volumes wie der UI-Container (siehe
docker-compose.yml/docker-compose.local.yml), aber ein eigener Prozess mit eigenem
CPU-/Speicher-Limit -- die WhisperX-Inferenz belastet dadurch nicht mehr direkt den
UI-Prozess, der weiterhin auf andere Anfragen reagieren kann.

Bewusst simpel gehalten (Polling-Schleife, kein Redis/Celery) -- passt zum Rest des Projekts
("so einfach wie moeglich, komplett lokal") und funktioniert identisch auf dem Server wie in
einem lokalen Docker-Setup auf Mac/Windows.
"""

from __future__ import annotations

import time

from core.job_queue import (
    list_pending_jobs,
    mark_done,
    mark_error,
    mark_running,
    write_heartbeat,
)
from core.shared import TRANSCRIPTION_REALTIME_FACTOR
from core.transcription import save_transcript_cache, transcribe

POLL_INTERVAL_S = 1.0


def _process_transcription_job(job: dict) -> None:
    job_id = job["job_id"]
    audio_path = job["payload"]["audio_path"]

    import soundfile as sf

    duration_s = sf.info(audio_path).duration
    estimated_total_s = max(duration_s * TRANSCRIPTION_REALTIME_FACTOR, 10.0)

    import threading

    result: dict = {}
    error: dict = {}

    def _run():
        try:
            result["transcript"] = transcribe(audio_path)
        except Exception as exc:  # fail-loud im Log, aber der Job selbst bekommt einen
            # sauberen Fehlerstatus statt den Worker-Prozess abstuerzen zu lassen -- ein
            # kaputtes Audiofile soll nicht die ganze Queue lahmlegen.
            error["message"] = f"{type(exc).__name__}: {exc}"

    thread = threading.Thread(target=_run)
    mark_running(job_id, progress=0)
    thread.start()

    start = time.time()
    while thread.is_alive():
        elapsed = time.time() - start
        progress = min(90, int(elapsed / estimated_total_s * 100))
        mark_running(job_id, progress=progress)
        # Auch waehrend der Inferenz weiterschlagen: die Hauptschleife kommt hier minutenlang
        # nicht vorbei, der Worker wuerde sonst genau waehrend der Arbeit als tot gelten.
        write_heartbeat()
        time.sleep(0.5)
    thread.join()

    if "message" in error:
        mark_error(job_id, error["message"])
        return

    transcript = result["transcript"]
    # Reihenfolge ist Absicht: ERST das Ergebnis sichern, DANN den Cache versuchen. Frueher
    # stand save_transcript_cache() davor und konnte den Job mit einer OSError abbrechen,
    # nachdem die Transkription bereits ein bis zwei Minuten gerechnet hatte -- das Ergebnis
    # war dann verloren (RANDNOTIZ-16). Der Cache ist eine Beschleunigung, kein Bestandteil
    # des Ergebnisses; er darf nie darueber entscheiden, ob die Arbeit zaehlt.
    mark_done(job_id, transcript)
    if not save_transcript_cache(audio_path, transcript):
        print(f"[worker] Job {job_id}: Transkript berechnet, aber Cache nicht schreibbar "
              f"({audio_path}) — Ergebnis wurde trotzdem geliefert.", flush=True)


def main() -> None:
    print("[worker] NeuroVoice AI Hintergrund-Worker gestartet, warte auf Jobs ...", flush=True)
    while True:
        write_heartbeat()
        jobs = list_pending_jobs()
        for job in jobs:
            job_id = job["job_id"]
            kind = job.get("kind")
            print(f"[worker] verarbeite Job {job_id} ({kind}) ...", flush=True)
            try:
                if kind == "transcription":
                    _process_transcription_job(job)
                else:
                    mark_error(job_id, f"Unbekannte Job-Art: {kind}")
                print(f"[worker] Job {job_id} fertig.", flush=True)
            except Exception as exc:  # fail-loud im Log, Worker-Schleife selbst laeuft weiter
                print(f"[worker] Job {job_id} fehlgeschlagen: {exc}", flush=True)
                mark_error(job_id, f"{type(exc).__name__}: {exc}")
        time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    main()
