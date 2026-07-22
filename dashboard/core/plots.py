"""Visualisierungen: Wellenform, Spektrogramm mit Pitch-/Intensitäts-Overlay, Normwert-Gauges."""

import math

import matplotlib.pyplot as plt
import numpy as np
import parselmouth
from matplotlib.patches import Circle, Wedge


def waveform_figure(sound: parselmouth.Sound):
    fig, ax = plt.subplots(figsize=(10, 2.5))
    times = sound.xs()
    values = sound.values[0]
    ax.plot(times, values, linewidth=0.5, color="#2b6cb0")
    ax.set_xlim(times[0], times[-1])
    ax.set_xlabel("Zeit (s)")
    ax.set_ylabel("Amplitude")
    ax.set_title("Wellenform")
    fig.tight_layout()
    return fig


def spectrogram_figure(sound: parselmouth.Sound):
    spectrogram = sound.to_spectrogram()
    X, Y = spectrogram.x_grid(), spectrogram.y_grid()
    sg_db = 10 * np.log10(spectrogram.values + 1e-10)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.pcolormesh(X, Y, sg_db, cmap="afmhot", shading="auto", vmin=sg_db.max() - 70, vmax=sg_db.max())
    ax.set_ylim(0, 5000)
    ax.set_xlabel("Zeit (s)")
    ax.set_ylabel("Frequenz (Hz)")
    ax.set_title("Spektrogramm")

    pitch = sound.to_pitch()
    pitch_values = pitch.selected_array["frequency"]
    pitch_values[pitch_values == 0] = np.nan
    ax.plot(pitch.xs(), pitch_values, "o", markersize=2, color="#4fd1c5", label="F0")

    # Formant-Tracks F1-F3 (Stufe 2, docs/backlog.md) -- F1 korreliert mit Zungenhoehe,
    # F2 mit Zungenposition vorne/hinten, siehe docs/literatur_review.md.
    formant = sound.to_formant_burg()
    formant_times = np.arange(formant.xmin, formant.xmax, 0.01)
    formant_colors = {1: "#68d391", 2: "#fbd38d", 3: "#fc8181"}
    for n in (1, 2, 3):
        values = np.array([formant.get_value_at_time(n, t) or np.nan for t in formant_times])
        ax.plot(formant_times, values, ".", markersize=2, color=formant_colors[n], label=f"F{n}")

    ax.legend(loc="upper right")

    fig.tight_layout()
    return fig


def intensity_figure(sound: parselmouth.Sound):
    intensity = sound.to_intensity()
    times = intensity.xs()
    values = intensity.values[0].copy()
    # -300 dB ist Praats Sentinel fuer "keine definierte Intensitaet" (Stille), kein
    # echter Messwert -- als Luecke (NaN) darstellen statt die y-Achse zu stauchen.
    values[values <= -300] = np.nan
    fig, ax = plt.subplots(figsize=(10, 2))
    ax.plot(times, values, color="#c05621")
    ax.set_xlabel("Zeit (s)")
    ax.set_ylabel("Intensität (dB)")
    ax.set_title("Lautstärkeverlauf")
    fig.tight_layout()
    return fig


def gauge_figure(
    label: str,
    value: float | None = None,
    unit: str = "",
    lo: float = 0,
    hi: float = 1,
    zones: list[tuple[float, float, str]] | None = None,
    na: bool = False,
    na_reason: str = "",
):
    """Halbkreis-Gauge (Tacho-Stil), siehe Normwert-Konzept vom 2026-07-21.

    `zones=None` und `na=False` => informative Nadel ohne Farbwertung (Tier B/C:
    Richtung bekannt, aber kein harter Cutoff). `na=True` => grau/nicht auswertbar
    (z.B. Jitter/Shimmer bei Lesetext-Aufnahmen).
    """
    fig, ax = plt.subplots(figsize=(3.0, 2.1), subplot_kw={"aspect": "equal"})
    ax.set_xlim(-1.15, 1.15)
    ax.set_ylim(-0.25, 1.15)
    ax.axis("off")
    ax.text(0, 1.05, label, ha="center", va="bottom", fontsize=9.5, fontweight="bold", wrap=True)

    if na:
        wedge = Wedge((0, 0), 1, 0, 180, width=0.28, facecolor="#a3adb8", alpha=0.3)
        ax.add_patch(wedge)
        ax.text(0, 0.35, "n/a", ha="center", va="center", fontsize=13, color="#7c8998")
        ax.text(0, -0.05, na_reason, ha="center", va="top", fontsize=7, color="#7c8998", wrap=True)
        fig.tight_layout()
        return fig

    if zones:
        for f0, f1, color in zones:
            theta0 = 180 - f0 * 180
            theta1 = 180 - f1 * 180
            ax.add_patch(Wedge((0, 0), 1, theta1, theta0, width=0.28, facecolor=color))
    else:
        ax.add_patch(Wedge((0, 0), 1, 0, 180, width=0.28, facecolor="#cfd6dd"))

    frac = max(0.0, min(1.0, (value - lo) / (hi - lo))) if value is not None else 0.5
    angle = math.radians(180 - frac * 180)
    ax.plot([0, 0.7 * math.cos(angle)], [0, 0.7 * math.sin(angle)], color="#1b2530", linewidth=2.5, solid_capstyle="round")
    ax.add_patch(Circle((0, 0), 0.045, color="#1b2530"))

    value_text = f"{value:.1f}{(' ' + unit) if unit else ''}" if value is not None else "–"
    ax.text(0, -0.08, value_text, ha="center", va="top", fontsize=12.5, fontweight="bold")

    fig.tight_layout()
    return fig


def radar_figure(labels: list[str], values: list[float]):
    """Radar-/Spinnennetz-Profil ueber mehrere normalisierte (0-1) Werte, siehe Normwert-Konzept."""
    n = len(labels)
    angles = [i / n * 2 * math.pi for i in range(n)]
    angles += angles[:1]
    vals = list(values) + [values[0]]

    fig, ax = plt.subplots(figsize=(4.2, 4.2), subplot_kw={"projection": "polar"})
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylim(0, 1)
    ax.set_yticklabels([])
    ax.spines["polar"].set_color("#dde3ea")
    ax.grid(color="#dde3ea")

    ax.plot(angles, vals, color="#2b6cb0", linewidth=2)
    ax.fill(angles, vals, color="#2b6cb0", alpha=0.22)

    fig.tight_layout()
    return fig
