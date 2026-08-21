"""Kennwerte gegen ihre konstruierte Wahrheit.

Siehe `docs/konzept_zuverlaessigkeit.md`, Etappe 2. Jeder Sollwert folgt aus der Konstruktion
des Eingangssignals, nicht aus einer zweiten Implementierung derselben Formel.

Vorgeschichte: Kennwerte wurden bisher nur gegen Plausibilitaet und Literatur geprueft. Das
faengt, was auffaellig falsch aussieht -- aber nicht ein Mass, das immer denselben harmlosen
Wert liefert (RANDNOTIZ-17) oder das bei einer bestimmten Aufgabenart systematisch daneben
liegt (RANDNOTIZ-15). Beide waeren von diesen Tests am ersten Tag gefangen worden.
"""

import pytest

from core.audio import (
    formant_centralization_ratio,
    formant_features,
    phonation_features,
    recording_quality_features,
    vowel_space_area,
)
from signale import glottis_signal, mit_rauschen

# Jitter/Shimmer werden bewusst an der UNGEFILTERTEN Pulsfolge geprueft. Empirisch belegt
# (2026-08-20): schickt man dasselbe Signal durch Formant-Resonatoren, daempft deren
# Nachschwingen die Alternation um einen konstanten Faktor (Shimmer 0,8385 in allen geprueften
# Faellen). Das ist ein physikalischer Effekt der Filterung, kein Fehler der Messung -- fuer
# einen analytischen Sollwert muss er aber draussen bleiben.
OHNE_FORMANTEN: tuple = ()


# ── Grundfrequenz ────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("f0", [90.0, 120.0, 200.0])
def test_f0_trifft_konstruierte_frequenz(wav, f0):
    p = wav(glottis_signal(f0_hz=f0, dauer_s=2.0, formanten_hz=OHNE_FORMANTEN))
    gemessen = phonation_features(p)["f0_mean_hz"]
    assert gemessen == pytest.approx(f0, rel=0.01)


# ── Jitter: Sollwert = 2 * jitter_rel ────────────────────────────────────────────────────
# Die Perioden alternieren zwischen T*(1+j) und T*(1-j). Der Betrag der Differenz zweier
# aufeinanderfolgender Perioden ist damit immer 2*j*T, die mittlere Periode T -- Praats
# "jitter (local)" ist genau dieser Quotient.
@pytest.mark.parametrize("j", [0.0025, 0.005, 0.010, 0.020])
def test_jitter_trifft_konstruierte_periodenschwankung(wav, j):
    p = wav(glottis_signal(f0_hz=120.0, dauer_s=3.0, jitter_rel=j, formanten_hz=OHNE_FORMANTEN))
    assert phonation_features(p)["jitter_local_pct"] == pytest.approx(2 * j * 100, rel=0.05)


# ── Shimmer: Sollwert = 2 * shimmer_rel ──────────────────────────────────────────────────
@pytest.mark.parametrize("s", [0.01, 0.02, 0.05])
def test_shimmer_trifft_konstruierte_amplitudenschwankung(wav, s):
    p = wav(glottis_signal(f0_hz=120.0, dauer_s=3.0, shimmer_rel=s, formanten_hz=OHNE_FORMANTEN))
    assert phonation_features(p)["shimmer_local_pct"] == pytest.approx(2 * s * 100, rel=0.05)


def test_perfekt_periodisches_signal_hat_keine_perturbation(wav):
    """Die wichtigste Gegenprobe: ein Mass, das bei perfekter Periodizitaet etwas anderes als
    null meldet, misst Rauschen im eigenen Verfahren statt Eigenschaften der Stimme."""
    p = wav(glottis_signal(f0_hz=120.0, dauer_s=3.0, formanten_hz=OHNE_FORMANTEN))
    r = phonation_features(p)
    assert r["jitter_local_pct"] < 0.01
    assert r["shimmer_local_pct"] < 0.01


# ── HNR: Sollwert = konstruierter Rauschabstand ──────────────────────────────────────────
@pytest.mark.parametrize("snr_db", [5.0, 10.0, 20.0, 30.0])
def test_hnr_trifft_konstruierten_rauschabstand(wav, snr_db):
    rein = glottis_signal(f0_hz=120.0, dauer_s=3.0, formanten_hz=(700.0, 1200.0))
    p = wav(mit_rauschen(rein, snr_db))
    assert phonation_features(p)["hnr_mean_db"] == pytest.approx(snr_db, abs=1.5)


# ── Formanten ────────────────────────────────────────────────────────────────────────────
# F2 wird von Praats Burg-Tracker zuverlaessig wiedergefunden. F1 NUR bei offenen Vokalen:
# liegt F1 nahe an F0 und dessen ersten Harmonischen (geschlossene Vokale wie /i/ und /u/),
# ueberschaetzt der Tracker es am synthetischen Signal deutlich (300 Hz -> ~390 Hz). Das ist
# eine Grenze dieser Pruefung, KEIN belegter Fehler an echter Sprache: echte Vokale haben eine
# dichtere Harmonischen- und Formantstruktur als das Modell hier. Deshalb wird F1 fuer
# geschlossene Vokale nicht auf einen Absolutwert geprueft, sondern nur die Topologie unten.
@pytest.mark.parametrize("f1,f2", [(700.0, 1200.0), (350.0, 800.0), (300.0, 2300.0)])
def test_f2_trifft_gesetzte_polfrequenz(wav, f1, f2):
    p = wav(glottis_signal(f0_hz=120.0, dauer_s=2.0, formanten_hz=(f1, f2, 3000.0, 3800.0)))
    assert formant_features(p)["f2_mean_hz"] == pytest.approx(f2, rel=0.15)


def test_f1_trifft_gesetzte_polfrequenz_bei_offenem_vokal(wav):
    p = wav(glottis_signal(f0_hz=120.0, dauer_s=2.0, formanten_hz=(700.0, 1200.0, 2600.0, 3500.0)))
    assert formant_features(p)["f1_mean_hz"] == pytest.approx(700.0, rel=0.15)


def test_vokaldreieck_behaelt_seine_topologie(wav):
    """Fuer VSA und FCR zaehlt nicht der Absolutwert, sondern die Lage der Vokale zueinander:
    /a/ muss das hoechste F1 haben, /i/ das hoechste F2, /u/ das niedrigste F2."""
    messe = lambda pole: formant_features(wav(glottis_signal(120.0, 2.0, formanten_hz=pole)))
    a = messe((700.0, 1200.0, 2600.0, 3500.0))
    i = messe((300.0, 2300.0, 3000.0, 3800.0))
    u = messe((350.0, 800.0, 2500.0, 3400.0))
    assert a["f1_mean_hz"] > i["f1_mean_hz"] and a["f1_mean_hz"] > u["f1_mean_hz"]
    assert i["f2_mean_hz"] > a["f2_mean_hz"] > u["f2_mean_hz"]


# ── VSA / FCR: reine Arithmetik, analytisch nachrechenbar ────────────────────────────────
def test_vsa_entspricht_der_dreiecksflaeche():
    # Shoelace-Formel von Hand: 0,5*|F1i*(F2a-F2u) + F1a*(F2u-F2i) + F1u*(F2i-F2a)|
    erwartet = 0.5 * abs(300 * (1200 - 800) + 700 * (800 - 2300) + 350 * (2300 - 1200))
    assert vowel_space_area(700, 1200, 300, 2300, 350, 800) == pytest.approx(erwartet)


def test_fcr_entspricht_der_formel_von_sapir():
    erwartet = (800 + 1200 + 300 + 350) / (2300 + 700)
    assert formant_centralization_ratio(700, 1200, 300, 2300, 350, 800) == pytest.approx(erwartet)


def test_fcr_steigt_mit_zentralisierung():
    deutlich = formant_centralization_ratio(730, 1090, 270, 2290, 300, 870)
    zentral = formant_centralization_ratio(550, 1400, 450, 1700, 480, 1250)
    assert zentral > deutlich


def test_fcr_und_vsa_reagieren_gegenlaeufig():
    """Beide messen dieselbe Sache aus entgegengesetzter Richtung -- laufen sie je gleichsinnig,
    ist eine der beiden Formeln verdreht."""
    weit = (730, 1090, 270, 2290, 300, 870)
    eng = (550, 1400, 450, 1700, 480, 1250)
    assert vowel_space_area(*eng) < vowel_space_area(*weit)
    assert formant_centralization_ratio(*eng) > formant_centralization_ratio(*weit)


@pytest.mark.parametrize("args", [
    (None, 1200, 300, 2300, 350, 800),   # fehlender Wert
    (0, 1200, 300, 0, 350, 800),          # entarteter Nenner (f2_i + f1_a = 0)
])
def test_fcr_liefert_none_statt_abzustuerzen(args):
    assert formant_centralization_ratio(*args) is None


# ── Uebersteuerung ───────────────────────────────────────────────────────────────────────
def test_clipping_erkennt_konstruierten_anteil(wav):
    import numpy as np
    x = glottis_signal(120.0, 2.0, formanten_hz=(700.0, 1200.0))
    x = np.clip(x * 4.0, -1.0, 1.0)  # kraeftig uebersteuert
    r = recording_quality_features(wav(x))
    assert r["clipping_pct"] > 1.0


def test_sauberes_signal_meldet_kein_clipping(wav):
    p = wav(glottis_signal(120.0, 2.0, formanten_hz=(700.0, 1200.0)))
    assert recording_quality_features(p)["clipping_pct"] == pytest.approx(0.0, abs=0.01)
