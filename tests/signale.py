"""Synthetische Testsignale, deren wahre Antwort in der KONSTRUKTION steckt.

Der Leitsatz stammt aus dem Schwesterprojekt EDF-Analyzer
(`tests/test_analytic_groundtruth.py`) und gilt hier unveraendert:

    Was hier NICHT passiert: eine Formel neben der Implementierung nachbauen und beide
    vergleichen. Das zeigte nur, dass zwei Rechnungen uebereinstimmen. Geprueft wird gegen
    Werte, die aus der Theorie oder aus der Konstruktion des Eingangssignals folgen.

Warum das noetig ist (siehe `docs/konzept_zuverlaessigkeit.md`, Ursache B): Kennwerte wurden
bisher nur gegen Plausibilitaet und Literatur geprueft. Das faengt, was auffaellig falsch
aussieht -- aber nicht ein Mass, das immer denselben harmlosen Wert liefert. Genau so blieb
`fluency_score` konstant 1,00 unbemerkt (RANDNOTIZ-17).

Alle Zufallsanteile laufen ueber einen festen Seed: ein Test, der gelegentlich rot wird, wird
irgendwann ignoriert -- und ist dann schlimmer als keiner.
"""

from __future__ import annotations

import numpy as np
import soundfile as sf

FS = 48000  # wie unsere echten Aufnahmen (iPhone/Browser liefern beide 48 kHz)


def _pulse_positions(f0_hz: float, dauer_s: float, jitter_rel: float = 0.0) -> np.ndarray:
    """Anregungszeitpunkte einer Glottis-Pulsfolge.

    `jitter_rel` alterniert die Periodenlaenge zwischen T*(1+j) und T*(1-j). Daraus folgt der
    Sollwert fuer Praats "jitter (local)" analytisch: der Betrag der Differenz zweier
    aufeinanderfolgender Perioden ist 2*j*T, die mittlere Periode ist T, also

        jitter_local = 2 * jitter_rel

    Das ist der eigentliche Punkt dieser Datei -- der Erwartungswert kommt aus der Konstruktion,
    nicht aus einer zweiten Implementierung derselben Formel.
    """
    T = 1.0 / f0_hz
    zeiten, t = [], 0.0
    i = 0
    while t < dauer_s:
        zeiten.append(t)
        periode = T * (1.0 + jitter_rel) if i % 2 == 0 else T * (1.0 - jitter_rel)
        t += periode
        i += 1
    return np.array(zeiten)


def glottis_signal(
    f0_hz: float = 120.0,
    dauer_s: float = 3.0,
    jitter_rel: float = 0.0,
    shimmer_rel: float = 0.0,
    formanten_hz: tuple[float, ...] = (),
    bandbreite_hz: float = 80.0,
) -> np.ndarray:
    """Pulsfolge mit optionalem Jitter/Shimmer, optional durch Formant-Resonatoren gefiltert.

    `shimmer_rel` alterniert die Pulsamplitude zwischen A*(1+s) und A*(1-s) -- analog zum
    Jitter folgt daraus `shimmer_local = 2 * shimmer_rel`.
    """
    n = int(FS * dauer_s)
    x = np.zeros(n)
    for i, t in enumerate(_pulse_positions(f0_hz, dauer_s, jitter_rel)):
        idx = int(round(t * FS))
        if 0 <= idx < n:
            x[idx] = 1.0 + (shimmer_rel if i % 2 == 0 else -shimmer_rel)

    for f in formanten_hz:
        x = _resonator(x, f, bandbreite_hz)

    spitze = np.max(np.abs(x))
    return x / spitze * 0.5 if spitze > 0 else x


def _resonator(x: np.ndarray, f_hz: float, bandbreite_hz: float) -> np.ndarray:
    """Zweipoliger Resonator mit Polfrequenz `f_hz` -- erzeugt einen Formanten an genau dieser
    Stelle. Standard-Digitalfilter-Konstruktion (Klatt-Synthesizer): r = exp(-pi*B/fs),
    Polwinkel = 2*pi*f/fs."""
    r = np.exp(-np.pi * bandbreite_hz / FS)
    theta = 2.0 * np.pi * f_hz / FS
    a1, a2 = 2.0 * r * np.cos(theta), -(r ** 2)
    y = np.zeros_like(x)
    for n in range(len(x)):
        y[n] = x[n] + (a1 * y[n - 1] if n >= 1 else 0.0) + (a2 * y[n - 2] if n >= 2 else 0.0)
    return y


def mit_rauschen(signal: np.ndarray, snr_db: float, seed: int = 20260820) -> np.ndarray:
    """Addiert weisses Rauschen so, dass das Leistungsverhaeltnis exakt `snr_db` betraegt.
    Damit ist der HNR-Sollwert durch die Konstruktion festgelegt."""
    rng = np.random.default_rng(seed)
    p_signal = float(np.mean(signal ** 2))
    p_rausch = p_signal / (10.0 ** (snr_db / 10.0))
    rauschen = rng.standard_normal(len(signal))
    rauschen *= np.sqrt(p_rausch / float(np.mean(rauschen ** 2)))
    return signal + rauschen


def silbenfolge(n_silben: int, rate_hz: float, dauer_silbe_s: float = 0.08) -> np.ndarray:
    """`n_silben` stimmhafte Bursts mit Stille dazwischen -- Modell einer DDK-Aufgabe.

    Die wahre Silbenzahl und die wahre Rate stehen damit fest. Genau das braucht RANDNOTIZ-18:
    `ddk_rate_features()` zaehlt Intensitaets-Einbrueche als "Zyklen", und ohne bekannte
    Sollzahl liess sich nie entscheiden, ob damit Silben oder "pa-ta-ka"-Gruppen gemeint sind.
    """
    abstand_s = 1.0 / rate_hz
    n = int(FS * (n_silben * abstand_s + 0.3))
    x = np.zeros(n)
    burst = glottis_signal(f0_hz=120.0, dauer_s=dauer_silbe_s, formanten_hz=(700.0, 1200.0))
    # weiche Flanken, sonst erzeugen die Sprungstellen selbst Intensitaetseinbrueche
    huelle = np.hanning(len(burst))
    burst = burst * huelle
    for i in range(n_silben):
        start = int((0.15 + i * abstand_s) * FS)
        if start + len(burst) < n:
            x[start:start + len(burst)] += burst
    return x


def mit_pausen(dauer_block_s: float, pausen_s: list[float], block_f0: float = 120.0) -> np.ndarray:
    """Abwechselnd Sprachbloecke und Stillen bekannter Laenge."""
    teile = []
    for i, pause in enumerate(pausen_s + [0.0]):
        teile.append(glottis_signal(f0_hz=block_f0, dauer_s=dauer_block_s,
                                    formanten_hz=(700.0, 1200.0)))
        if pause > 0:
            teile.append(np.zeros(int(FS * pause)))
    return np.concatenate(teile)


def schreibe(pfad: str, signal: np.ndarray) -> str:
    sf.write(pfad, signal, FS, subtype="PCM_24")
    return pfad
