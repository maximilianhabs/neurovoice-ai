"""Pfad-Setup + gemeinsame Fixtures.

`dashboard/` liegt nicht als installierbares Paket vor (die App laeuft im Container mit
`/app` als Arbeitsverzeichnis), deshalb wird der Ordner hier auf den Importpfad gelegt --
dieselbe Auswahl, die auch `app.py` zur Laufzeit vorfindet.
"""

import os
import sys

import pytest

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WURZEL, "dashboard"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def wav(tmp_path_factory):
    """Schreibt ein Signal in eine WAV-Datei und liefert den Pfad.

    Session-weit, weil das Erzeugen der Resonator-gefilterten Signale in reinem Python laeuft
    und je Sekunde Audio spuerbar Zeit kostet -- die Tests sollen im Preflight nicht bremsen.
    """
    verzeichnis = tmp_path_factory.mktemp("signale")
    zaehler = {"n": 0}

    def _schreibe(signal):
        import signale as sg
        zaehler["n"] += 1
        return sg.schreibe(str(verzeichnis / f"s{zaehler['n']}.wav"), signal)

    return _schreibe
