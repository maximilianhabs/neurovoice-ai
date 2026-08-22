"""Die drei offenen Messwert-Randnotizen -- als Tests festgenagelt statt nur beschrieben.

Jeder `xfail(strict=True)`-Test formuliert, was das Mass leisten MUESSTE. Solange der Mangel
besteht, ist der Test rot-erwartet und stoert nicht. Wird der Mangel behoben, schlaegt der
Lauf fehl ("unexpectedly passing") und erinnert daran, die Markierung zu entfernen und den
Bugtracker-Eintrag zu schliessen -- ein behobener Fehler kann so nicht unbemerkt bleiben.

Zusaetzlich stehen hier die Tests, die den jeweiligen Mangel EINGRENZEN. Sie laufen normal
gruen und halten fest, welcher Teil der Kette nachweislich in Ordnung ist. Genau das war bei
RANDNOTIZ-17 die entscheidende Frage: rechnet die Funktion falsch, oder bekommt sie schon
falsche Eingaben?
"""

import numpy as np
import pytest

from core.audio import ddk_rate_features, recording_quality_features
from core.speech_metrics import compute_speech_metrics
from signale import FS, glottis_signal, mit_pausen, mit_rauschen, silbenfolge

RAUSCHTEPPICH = 1e-2  # ca. -40 dB; echte Aufnahmen haben nie digitale Stille


def _worte(spannen):
    return [{"word": f"w{i}", "start": a, "end": b, "score": 0.9}
            for i, (a, b) in enumerate(spannen)]


# ══ RANDNOTIZ-17 — Pausenmasse ═══════════════════════════════════════════════════════════

def test_pausenmasse_rechnen_bei_echten_luecken_korrekt():
    """Eingrenzung: `compute_speech_metrics()` selbst ist in Ordnung.

    Mit einer Wortliste, die drei echte Luecken von je 2 s enthaelt, zaehlt die Funktion
    exakt drei Pausen. Der Fehler liegt also NICHT in der Berechnung."""
    spannen = [(0, 0.5), (0.5, 1.0), (3.0, 3.5), (3.5, 4.0), (6.0, 6.5), (8.5, 9.0)]
    r = compute_speech_metrics(_worte(spannen), total_duration_s=9.0)
    assert r["pause_count"] == 3
    assert r["macro_pause_count"] == 3
    assert r["total_pause_time_s"] == pytest.approx(6.0, abs=0.01)
    assert r["fluency_score"] < 0.5


def test_lueckenlose_wortliste_erzeugt_null_pausen():
    """Eingrenzung, zweiter Teil: genau dieses Muster liefert WhisperX.

    Forced Alignment dehnt die Wortgrenzen aneinander -- die Wortliste hat dann keine Luecken
    mehr, voellig unabhaengig davon, ob die Person tatsaechlich pausiert hat. Die Funktion
    meldet daraufhin korrekt null Pausen und `fluency_score` 1,00. Das ist der belegte
    Mechanismus hinter RANDNOTIZ-17: nicht die Berechnung ist falsch, sondern ihre Eingabe."""
    spannen = [(i * 0.5, (i + 1) * 0.5) for i in range(18)]
    r = compute_speech_metrics(_worte(spannen), total_duration_s=9.0)
    assert r["pause_count"] == 0
    assert r["fluency_score"] == pytest.approx(1.0)


def test_pausen_werden_aus_dem_signal_erkannt(tmp_path):
    """✅ Seit 2026-08-21 behoben: `pausen_aus_signal()` findet die konstruierten Stillen ohne
    Umweg ueber eine Transkription. Vorher war dieser Test ein `xfail` -- es gab die Funktion
    gar nicht, das war der Kern des Mangels."""
    import soundfile as sf
    from core.audio import pausen_aus_signal
    rng = np.random.default_rng(20260820)
    signal = mit_pausen(0.5, [0.6, 0.6, 0.6])
    signal = signal + rng.standard_normal(len(signal)) * 1e-3  # realistischer Rauschteppich
    pfad = str(tmp_path / "pausen.wav")
    sf.write(pfad, signal, FS)
    r = pausen_aus_signal(pfad)
    assert r["pause_count"] == 3
    assert r["macro_pause_count"] == 3
    # Praats Intensitaetsfenster glaettet die Flanken, die erkannte Stille faellt dadurch etwas
    # kuerzer aus als die konstruierte -- konservativ in die richtige Richtung.
    assert r["total_pause_time_s"] == pytest.approx(1.8, rel=0.15)


@pytest.mark.parametrize("n_pausen", [1, 2, 4])
def test_pausenzahl_folgt_der_konstruktion(tmp_path, n_pausen):
    import soundfile as sf
    from core.audio import pausen_aus_signal
    rng = np.random.default_rng(20260820)
    signal = mit_pausen(0.5, [0.6] * n_pausen)
    signal = signal + rng.standard_normal(len(signal)) * 1e-3
    pfad = str(tmp_path / f"p{n_pausen}.wav")
    sf.write(pfad, signal, FS)
    assert pausen_aus_signal(pfad)["pause_count"] == n_pausen


# Praat warnt hier zu Recht, dass lauteste und leiseste Stelle sich kaum unterscheiden --
# genau das ist bei einem gehaltenen Vokal ohne Pausen der Fall und der Punkt des Tests.
@pytest.mark.filterwarnings("ignore::parselmouth.PraatWarning")
def test_durchgehende_sprache_hat_keine_pausen(tmp_path):
    """Gegenprobe: ein Mass, das ueberall Pausen findet, waere genauso wertlos wie eines, das
    nie welche findet."""
    import soundfile as sf
    from core.audio import pausen_aus_signal
    rng = np.random.default_rng(20260820)
    signal = glottis_signal(120.0, 3.0, formanten_hz=(700.0, 1200.0))
    signal = signal + rng.standard_normal(len(signal)) * 1e-3
    pfad = str(tmp_path / "durchgehend.wav")
    sf.write(pfad, signal, FS)
    assert pausen_aus_signal(pfad)["pause_count"] == 0


def test_signalpausen_ersetzen_die_wortbasierte_ableitung(tmp_path):
    """Die entscheidende Verdrahtung: dieselbe lueckenlose Wortliste, die vorher zwangslaeufig
    `fluency_score` 1,00 ergab, liefert mit Audio jetzt ein echtes Ergebnis."""
    import soundfile as sf
    from core.audio import pausen_aus_signal
    rng = np.random.default_rng(20260820)
    signal = mit_pausen(0.5, [0.6, 0.6, 0.6])
    signal = signal + rng.standard_normal(len(signal)) * 1e-3
    pfad = str(tmp_path / "verdrahtung.wav")
    sf.write(pfad, signal, FS)
    worte = _worte([(i * 0.5, (i + 1) * 0.5) for i in range(7)])  # lueckenlos, WhisperX-Muster

    ohne = compute_speech_metrics(worte, total_duration_s=3.8)
    mit = compute_speech_metrics(worte, total_duration_s=3.8,
                                 pausen_aus_audio=pausen_aus_signal(pfad))

    assert ohne["pause_count"] == 0 and ohne["fluency_score"] == pytest.approx(1.0)
    assert mit["pause_count"] == 3 and mit["fluency_score"] < 0.7
    # Sprechrate haengt weiterhin an den Woertern und darf sich NICHT veraendert haben
    assert mit["net_speech_rate_wpm"] == pytest.approx(ohne["net_speech_rate_wpm"])


# ══ RANDNOTIZ-15 — SNR bei gehaltenen Vokalen ════════════════════════════════════════════

def test_snr_ist_bei_fliessender_sprache_korrekt(tmp_path):
    """Eingrenzung: fuer Sprache mit natuerlichem Lautstaerkewechsel stimmt das Mass."""
    import soundfile as sf
    signal = mit_rauschen(mit_pausen(0.4, [0.25] * 5), 25.0)
    pfad = str(tmp_path / "sprache.wav")
    sf.write(pfad, signal, FS)
    assert recording_quality_features(pfad)["snr_estimate_db"] == pytest.approx(25.0, abs=5.0)


def _aufnahme_mit_rauschboden(nutzsignal, snr_db, rand_s=0.6, seed=20260822):
    """Realistische Aufnahme: Rauschen laeuft durchgehend, das Nutzsignal nur in der Mitte.
    Damit gibt es eine echte Rauschreferenz -- so sieht eine gewoehnliche Aufnahme aus, bei
    der jemand Aufnahme startet, einatmet, spricht und wieder stoppt."""
    rng = np.random.default_rng(seed)
    p_sig = float(np.mean(nutzsignal ** 2))
    p_noise = p_sig / (10 ** (snr_db / 10))
    n_rand = int(FS * rand_s)
    rausch = rng.standard_normal(n_rand * 2 + len(nutzsignal))
    rausch *= np.sqrt(p_noise / float(np.mean(rausch ** 2)))
    rausch[n_rand:n_rand + len(nutzsignal)] += nutzsignal
    return rausch


@pytest.mark.parametrize("snr_db", [15.0, 25.0, 40.0])
def test_snr_stimmt_auch_beim_vokal_wenn_eine_rauschreferenz_da_ist(tmp_path, snr_db):
    """✅ RANDNOTIZ-15, Kern der Sache: das Verfahren ist nicht per se falsch, es braucht einen
    leisen Abschnitt. Hat die Vokalaufnahme normale Anlauf- und Schlussstille, trifft die
    Schaetzung den konstruierten Rauschabstand -- unabhaengig von der Aufgabenart."""
    import soundfile as sf
    vokal = glottis_signal(120.0, 3.0, formanten_hz=(700.0, 1200.0))
    pfad = str(tmp_path / f"vokal{snr_db}.wav")
    sf.write(pfad, _aufnahme_mit_rauschboden(vokal, snr_db), FS)
    assert recording_quality_features(pfad)["snr_estimate_db"] == pytest.approx(snr_db, abs=5.0)


def test_ohne_rauschreferenz_wird_kein_snr_behauptet(tmp_path):
    """✅ RANDNOTIZ-15, der eigentliche Fix: fehlt der leise Abschnitt voellig, liefert die
    Funktion `None` mit Begruendung statt einer strukturell zu niedrigen Zahl.

    Vorher meldete genau dieser Fall ~1 dB bei konstruierten 25 dB -- und loeste damit in der
    Oberflaeche die Empfehlung aus, die einwandfreie Aufnahme zu wiederholen."""
    import soundfile as sf
    vokal = mit_rauschen(glottis_signal(120.0, 4.0, formanten_hz=(700.0, 1200.0)), 25.0)
    pfad = str(tmp_path / "ohne_referenz.wav")
    sf.write(pfad, vokal, FS)
    r = recording_quality_features(pfad)
    assert r["snr_estimate_db"] is None
    assert r["snr_unavailable_reason"]
    assert r["noise_reference_s"] < 0.5


def test_hnr_bleibt_fuer_solche_aufnahmen_das_passende_rauschmass(tmp_path):
    """Gegenprobe zur Fehlanzeige: was der SNR dort nicht kann, kann der HNR sehr wohl --
    deshalb verweist die Begruendung darauf."""
    import soundfile as sf
    from core.audio import phonation_features
    vokal = mit_rauschen(glottis_signal(120.0, 4.0, formanten_hz=(700.0, 1200.0)), 25.0)
    pfad = str(tmp_path / "hnr_gegenprobe.wav")
    sf.write(pfad, vokal, FS)
    assert recording_quality_features(pfad)["snr_estimate_db"] is None
    assert phonation_features(pfad)["hnr_mean_db"] == pytest.approx(25.0, abs=2.0)


# ══ RANDNOTIZ-18 — DDK-Zaehlung und Regelmaessigkeit ═════════════════════════════════════

@pytest.mark.parametrize("n_silben,rate_hz", [(20, 5.0), (30, 6.0), (15, 3.0), (40, 7.0)])
def test_ddk_zaehlt_silbenzwischenraeume(tmp_path, n_silben, rate_hz):
    """Beantwortet die offene Zaehlfrage aus RANDNOTIZ-18.

    `ddk_rate_features()` sucht Taeler in der Intensitaetskontur. Ob damit einzelne Silben
    oder ganze "pa-ta-ka"-Gruppen gemeint sind, war nie geklaert -- ohne bekannte Sollzahl
    liess es sich nicht entscheiden. Ergebnis: gezaehlt werden die ZWISCHENRAEUME zwischen
    Silben, also n-1 bei n Silben. Damit ist `ddk_rate_hz` eine Silbenrate, keine Gruppenrate,
    und die niedrigen Werte an echten Aufnahmen sind vermutlich echt und kein Zaehlfehler."""
    import soundfile as sf
    rng = np.random.default_rng(20260820)
    signal = silbenfolge(n_silben, rate_hz)
    signal = signal + rng.standard_normal(len(signal)) * RAUSCHTEPPICH
    pfad = str(tmp_path / f"ddk{n_silben}.wav")
    sf.write(pfad, signal, FS)
    assert ddk_rate_features(pfad)["n_cycles"] == n_silben - 1


def test_ddk_versagt_bei_digitaler_stille(tmp_path):
    """Dokumentierte Grenze, damit sie nicht als Zufall durchgeht: ohne Rauschteppich ist das
    Intensitaetstal ein spitzes V statt eines Plateaus, die gemessene Verschlussdauer wird 0
    und der Plausibilitaetsfilter (0,01-0,3 s) verwirft ALLE Zyklen. Betrifft nur synthetisches
    oder geschnittenes Material -- echte Aufnahmen haben immer einen Rauschteppich."""
    import soundfile as sf
    pfad = str(tmp_path / "still.wav")
    sf.write(pfad, silbenfolge(20, 5.0), FS)
    assert ddk_rate_features(pfad)["n_cycles"] == 0


@pytest.mark.xfail(strict=True, reason=(
    "RANDNOTIZ-18: der Variationskoeffizient hat eine Eigenstreuung von ~0,15-0,28, auch wenn "
    "die Silben exakt gleichmaessig konstruiert sind. Er misst damit ueberwiegend die Streuung "
    "der eigenen Erkennung, nicht die Regelmaessigkeit des Sprechens -- und kann kleine echte "
    "Unterschiede nicht aufloesen (real gemessen: 0,41 vs 0,40 zwischen gesund und "
    "mittelgradig-schwer simuliert)."))
def test_perfekt_regelmaessige_silben_haben_cv_nahe_null(tmp_path):
    import soundfile as sf
    rng = np.random.default_rng(20260820)
    signal = silbenfolge(30, 6.0)
    signal = signal + rng.standard_normal(len(signal)) * RAUSCHTEPPICH
    pfad = str(tmp_path / "regelmaessig.wav")
    sf.write(pfad, signal, FS)
    assert ddk_rate_features(pfad)["cycle_interval_cv"] < 0.05
