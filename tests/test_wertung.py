"""Dysarthrie-Marker: Einstufung und Aggregation.

Geprueft wird gegen konstruierte Konstellationen mit bekannter erwarteter Einstufung -- und
gegen die REALEN Messwerte der drei echten SVD-Faelle, deren Reihenfolge klinisch bekannt ist.
Ein Regelwerk ohne Tests waere nach den Befunden der letzten Tage fahrlaessig.
"""

import pytest

from core.wertung import MARKER, bewerte_box, bewerte_marker, dysarthrie_marker

# Echte Messwerte, gehaltener Vokal /a/, alle aus derselben Aufnahmekette (SVD).
# Referenz = ungünstigster Wert der beiden SVD-Gesunden.
SVD_REFERENZ = {"jitter_local_pct": 0.33, "shimmer_local_pct": 2.19, "hnr_mean_db": 27.18}
SVD_FAELLE = {
    "gesund_m":  {"jitter_local_pct": 0.21, "shimmer_local_pct": 1.56, "hnr_mean_db": 27.37},
    "gesund_w":  {"jitter_local_pct": 0.33, "shimmer_local_pct": 2.19, "hnr_mean_db": 27.18},
    "parkinson": {"jitter_local_pct": 0.50, "shimmer_local_pct": 2.99, "hnr_mean_db": 18.85},
    "als":       {"jitter_local_pct": 0.43, "shimmer_local_pct": 5.19, "hnr_mean_db": 21.12},
    "bulbaer":   {"jitter_local_pct": 1.38, "shimmer_local_pct": 7.17, "hnr_mean_db": 15.98},
}


# ── Die entscheidende Probe: echte Faelle ────────────────────────────────────────────────
@pytest.mark.parametrize("fall", ["gesund_m", "gesund_w"])
def test_gesunde_erzeugen_keinen_marker(fall):
    """Kein Fehlalarm -- ein Marker, der bei Gesunden anschlaegt, waere unbrauchbar."""
    r = bewerte_box("vokalisation", SVD_FAELLE[fall], SVD_REFERENZ)
    assert r["auffaellig"] == 0
    assert r["hoechste_stufe"] is None


@pytest.mark.parametrize("fall", ["parkinson", "als", "bulbaer"])
def test_echte_faelle_erzeugen_marker(fall):
    """Mindestens ein Marker je echtem Fall. Nach dem Anheben der Schwellen (gesunde
    Test-Retest-Schwankung, siehe core/wertung.py) wird der Parkinson-Fall nur noch ueber den
    HNR erfasst -- der bewusst gewaehlte Preis dafuer, Gesunde nicht zu markieren."""
    r = bewerte_box("vokalisation", SVD_FAELLE[fall], SVD_REFERENZ)
    assert r["auffaellig"] >= 1, f"{fall}: kein Marker"


def test_gesunde_wiederholungsmessung_erzeugt_keinen_marker():
    """Der Fall, der die erste Schwellenfassung widerlegt hat: zwei GESUNDE Sitzungen derselben
    Person (NV-BFU8 als Referenz, NV-Z8YW als Messung) duerfen keinen Marker erzeugen."""
    referenz = {"jitter_local_pct": 0.595, "shimmer_local_pct": 7.610, "hnr_mean_db": 16.486}
    zweite_gesunde = {"jitter_local_pct": 0.64, "shimmer_local_pct": 9.72, "hnr_mean_db": 12.49}
    r = bewerte_box("vokalisation", zweite_gesunde, referenz)
    assert r["auffaellig"] == 0, f"Fehlalarm: {[m['label'] for m in r['marker'] if m['stufe']]}"


def test_bulbaerparalyse_ist_der_schwerste_fall():
    """Die Reihenfolge ist der eigentliche Test: die Bulbaerparalyse zeigt klinisch die
    deutlichste Phonationsstoerung der drei und muss die hoechste Stufe erreichen."""
    stufen = {f: bewerte_box("vokalisation", SVD_FAELLE[f], SVD_REFERENZ)["hoechste_stufe"]
              for f in ("parkinson", "als", "bulbaer")}
    assert stufen["bulbaer"] == "hoch"
    assert stufen["parkinson"] in ("leicht", "mittel")
    assert stufen["als"] in ("leicht", "mittel")


def test_alle_drei_perturbationsmarker_schlagen_beim_bulbaerfall_an():
    """Der schwerste echte Fall muss in allen drei Phonationsmarkern anschlagen.

    Die HNR-Abweichung (-11,2 dB) liegt nach dem Anheben der Schwellen knapp unter "hoch"
    (12 dB) -- deshalb hier "mindestens mittel" statt "hoch". Festgehalten, damit die
    Verschiebung sichtbar bleibt und nicht als Verschlechterung unbemerkt durchgeht."""
    r = bewerte_box("vokalisation", SVD_FAELLE["bulbaer"], SVD_REFERENZ)
    stufen = {m["key"]: m["stufe"] for m in r["marker"]}
    assert stufen["jitter_local_pct"] == "hoch"
    assert stufen["shimmer_local_pct"] == "hoch"
    assert stufen["hnr_mean_db"] in ("mittel", "hoch")


# ── Einstufungslogik ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("faktor,erwartet", [
    (1.0, None), (1.49, None), (1.5, "leicht"), (2.19, "leicht"),
    (2.2, "mittel"), (2.99, "mittel"), (3.0, "hoch"), (10.0, "hoch"),
])
def test_verhaeltnisskala_stuft_an_den_dokumentierten_grenzen(faktor, erwartet):
    b = bewerte_marker("jitter_local_pct", 0.4 * faktor, 0.4)
    assert b["stufe"] == erwartet


def test_richtung_niedrig_wird_richtig_herum_gewertet():
    """HNR ist der Gegenfall: NIEDRIGERE Werte sind auffaelliger. Waere die Richtung verdreht,
    wuerde eine bessere Aufnahme als auffaellig gelten -- ein Fehler, der in der Anzeige kaum
    auffiele."""
    schlechter = bewerte_marker("hnr_mean_db", 18.0, 27.0)
    besser = bewerte_marker("hnr_mean_db", 30.0, 27.0)
    assert schlechter["stufe"] == "mittel"
    assert besser["stufe"] is None


def test_sprechrate_wird_bei_verlangsamung_gewertet_nicht_bei_beschleunigung():
    langsamer = bewerte_marker("net_speech_rate_wpm", 94.0, 149.0)
    schneller = bewerte_marker("net_speech_rate_wpm", 180.0, 149.0)
    assert langsamer["stufe"] in ("mittel", "hoch")
    assert schneller["stufe"] is None


def test_fehlender_wert_gilt_nicht_als_unauffaellig():
    """Ein fehlender Kennwert darf niemals stillschweigend als "in Ordnung" durchgehen."""
    assert bewerte_marker("jitter_local_pct", None, 0.33) is None
    assert bewerte_marker("jitter_local_pct", 0.5, None) is None
    assert bewerte_marker("gibt_es_nicht", 1.0, 1.0) is None


# ── Aggregation ──────────────────────────────────────────────────────────────────────────
def test_vereinzelte_abweichung_gilt_nicht_als_gleichsinnig():
    """Ein einzelner abweichender Marker ist eher ein Messartefakt als ein Befund -- genau
    diese Unterscheidung soll die Aggregation leisten."""
    werte = {**SVD_REFERENZ, "jitter_local_pct": 1.0}   # nur Jitter auffaellig
    r = bewerte_box("vokalisation", werte, SVD_REFERENZ)
    assert r["auffaellig"] == 1
    assert r["gleichsinnig"] is False


def test_boxen_werden_getrennt_gehalten():
    """Vokalisation und Fliessprache messen Verschiedenes und duerfen nicht vermischt werden --
    die eigene Simulation zeigte genau die Trennung (Artikulation betroffen, Phonation nicht)."""
    werte = {**SVD_REFERENZ, "net_speech_rate_wpm": 94.0, "mean_word_duration_s": 0.56}
    referenzen = {**SVD_REFERENZ, "net_speech_rate_wpm": 149.0, "mean_word_duration_s": 0.33}
    r = dysarthrie_marker(werte, referenzen)
    assert r["betroffene_boxen"] == ["fliesssprache"]
    assert r["hoechste_stufe"] in ("mittel", "hoch")


def test_ohne_auffaelligkeit_bleibt_das_ergebnis_leer():
    r = dysarthrie_marker(SVD_REFERENZ, SVD_REFERENZ)
    assert r["marker_auffaellig"] == 0
    assert r["hoechste_stufe"] is None
    assert r["betroffene_boxen"] == []


def test_jeder_marker_ist_vollstaendig_begruendet():
    """Jede Schwelle muss sich rechtfertigen lassen -- eine Zahl ohne Herkunft ist genau die
    unbelegte Heuristik, die das Projekt vermeidet."""
    for key, d in MARKER.items():
        assert d.quelle.strip(), key
        assert d.richtung in ("hoch", "niedrig"), key
        assert len(d.schwellen) == 3 and list(d.schwellen) == sorted(d.schwellen), key
