"""Datei-basierte Job-Queue fuer lang laufende Hintergrund-Arbeit (P9, docs/backlog.md,
siehe docs/konzept_p9_hintergrundjob_lokal.md fuer das volle Konzept). Bewusst OHNE neue
Infrastruktur (kein Redis/Celery) -- passt zum bestehenden Muster in core/session_store.py/
core/subject_store.py (Zustand als JSON-Dateien unter NEUROVOICE_DERIVED_DIR) und funktioniert
identisch auf dem Server wie auf einem lokalen Mac/Windows-Docker-Setup, ohne zusaetzlichen
Dienst.

Ablauf: Streamlit-Seite ruft submit_job() auf (schreibt eine "pending"-Job-Datei, kehrt sofort
zurueck), der separate worker.py-Prozess/Container pollt das Job-Verzeichnis, verarbeitet
"pending"-Jobs und schreibt Ergebnis + Status zurueck. Die Seite pollt ihrerseits per
st.fragment(run_every=...) den Job-Status, OHNE die Skriptausfuehrung zu blockieren.
"""

from __future__ import annotations

import json
import os
import time
import uuid

DERIVED_DIR = os.environ.get("NEUROVOICE_DERIVED_DIR", "/derived")
JOBS_DIR = os.path.join(DERIVED_DIR, "_jobs")

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_ERROR = "error"


def _job_file(job_id: str) -> str:
    os.makedirs(JOBS_DIR, exist_ok=True)
    # Job-IDs kommen immer aus unserer eigenen uuid4()-Erzeugung (submit_job()), aber defensiv
    # trotzdem sanitisieren -- gleiches Pfad-Traversal-Prinzip wie in session_store.py/
    # subject_store.py.
    safe_id = "".join(c for c in job_id if c.isalnum())[:64] or "unknown"
    return os.path.join(JOBS_DIR, f"{safe_id}.json")


def submit_job(kind: str, payload: dict) -> str:
    """Legt einen neuen Job an und liefert die job_id. Der eigentliche Streamlit-Skriptlauf
    kehrt danach SOFORT zurueck -- verarbeitet wird der Job separat vom worker.py-Prozess."""
    job_id = uuid.uuid4().hex[:16]
    now = time.time()
    payload_out = {
        "job_id": job_id,
        "kind": kind,
        "payload": payload,
        "status": STATUS_PENDING,
        "progress": 0,
        "result": None,
        "error_message": None,
        "created_at": now,
        "updated_at": now,
    }
    with open(_job_file(job_id), "w", encoding="utf-8") as f:
        json.dump(payload_out, f, ensure_ascii=False, indent=2)
    return job_id


def get_job_status(job_id: str) -> dict | None:
    """Liest den aktuellen Job-Zustand, oder None falls die Job-Datei (noch) nicht existiert."""
    path = _job_file(job_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_job(job_id: str, **updates) -> None:
    job = get_job_status(job_id)
    if job is None:
        return
    job.update(updates)
    job["updated_at"] = time.time()
    with open(_job_file(job_id), "w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=2)


def mark_running(job_id: str, progress: int = 0) -> None:
    _write_job(job_id, status=STATUS_RUNNING, progress=progress)


def mark_progress(job_id: str, progress: int) -> None:
    _write_job(job_id, progress=progress)


def mark_done(job_id: str, result: dict) -> None:
    _write_job(job_id, status=STATUS_DONE, progress=100, result=result)


def mark_error(job_id: str, error_message: str) -> None:
    _write_job(job_id, status=STATUS_ERROR, error_message=error_message)


def list_pending_jobs() -> list[dict]:
    """Fuer worker.py: alle wartenden Jobs, aeltester zuerst (FIFO)."""
    if not os.path.isdir(JOBS_DIR):
        return []
    jobs = []
    for name in os.listdir(JOBS_DIR):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(JOBS_DIR, name), encoding="utf-8") as f:
                job = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if job.get("status") == STATUS_PENDING:
            jobs.append(job)
    jobs.sort(key=lambda j: j.get("created_at", 0))
    return jobs
