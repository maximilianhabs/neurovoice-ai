"""Visualisierungen: Wellenform, Spektrogramm mit Pitch-/Intensitäts-Overlay, Normwert-Gauges."""

import math

import matplotlib.pyplot as plt
import numpy as np
import parselmouth
from matplotlib.patches import Circle, Wedge

from core.design_tokens import (
    ACCENT,
    INFO,
    PLOT_GRID,
    PLOT_TRACK,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


def waveform_figure(sound: parselmouth.Sound):
    fig, ax = plt.subplots(figsize=(10, 2.5))
    times = sound.xs()
    values = sound.values[0]
    ax.plot(times, values, linewidth=0.5, color=ACCENT)
    ax.set_xlim(times[0], times[-1])
    ax.set_xlabel("Zeit (s)")
    ax.set_ylabel("Amplitude")
    ax.set_title("Wellenform")
    fig.tight_layout()
    return fig


def spectrogram_figure(sound: parselmouth.Sound):
    # Bewusst NICHT auf die Design-Tokens umgestellt (anders als die übrigen Diagramme hier):
    # F0-/Formant-Overlay-Farben (teal/gruen/gelb/rot) sind funktional gegen die "afmhot"-
    # Colormap kontrastgewaehlt, keine Marken-/Chrome-Farben -- gleiche Begruendung wie beim
    # EDF-Analyzer-Redesign, das sein dunkles EEG-Viewer-Theme aus demselben Grund unberuehrt
    # liess (siehe core/design_tokens.py-Kommentar).
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
    ax.plot(times, values, color=INFO)
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
        wedge = Wedge((0, 0), 1, 0, 180, width=0.28, facecolor=PLOT_TRACK, alpha=0.5)
        ax.add_patch(wedge)
        ax.text(0, 0.35, "n/a", ha="center", va="center", fontsize=13, color=TEXT_SECONDARY)
        ax.text(0, -0.05, na_reason, ha="center", va="top", fontsize=7, color=TEXT_SECONDARY, wrap=True)
        fig.tight_layout()
        return fig

    if zones:
        for f0, f1, color in zones:
            theta0 = 180 - f0 * 180
            theta1 = 180 - f1 * 180
            ax.add_patch(Wedge((0, 0), 1, theta1, theta0, width=0.28, facecolor=color))
    else:
        ax.add_patch(Wedge((0, 0), 1, 0, 180, width=0.28, facecolor=PLOT_TRACK))

    frac = max(0.0, min(1.0, (value - lo) / (hi - lo))) if value is not None else 0.5
    angle = math.radians(180 - frac * 180)
    ax.plot([0, 0.7 * math.cos(angle)], [0, 0.7 * math.sin(angle)], color=TEXT_PRIMARY, linewidth=2.5, solid_capstyle="round")
    ax.add_patch(Circle((0, 0), 0.045, color=TEXT_PRIMARY))

    value_text = f"{value:.1f}{(' ' + unit) if unit else ''}" if value is not None else "–"
    ax.text(0, -0.08, value_text, ha="center", va="top", fontsize=12.5, fontweight="bold")

    fig.tight_layout()
    return fig


def vowel_space_figure(vowels: dict[str, tuple[float, float]]):
    """Vokaltrapez (F1/F2-Diagramm) — die klassische phonetische Standarddarstellung fuer
    Vokale (siehe docs/konzept_visualisierungen.md, Abschnitt 3.1). Macht die bereits
    berechnete Vokalraum-Flaeche (VSA, core/audio.py::vowel_space_area()) erstmals visuell
    nachvollziehbar statt nur als abstrakte Hz²-Zahl -- ein kleines/zentralisiertes Dreieck
    ist auf einen Blick als "eingeschraenkter Artikulationsraum" erkennbar.

    `vowels`: {"a": (f1, f2), "i": (f1, f2), "u": (f1, f2)} -- nur Eintraege mit BEIDEN Werten
    vorhanden werden geplottet, Funktion braucht nicht zwingend alle 3 (zeigt dann nur Punkte,
    kein Dreieck).

    Achsen-Konvention (Standard in der Phonetik, z.B. Peterson & Barney 1952): F2 auf der
    X-Achse UMGEKEHRT (hohe Werte links -> vordere Vokale links), F1 auf der Y-Achse UMGEKEHRT
    (niedrige Werte oben -> hohe/geschlossene Vokale oben) -- ergibt die vertraute
    "Vokaltrapez"-Form aus Lehrbuechern.
    """
    points = {k: v for k, v in vowels.items() if v[0] is not None and v[1] is not None}

    fig, ax = plt.subplots(figsize=(5, 4.5))
    if len(points) >= 2:
        order = [k for k in ("i", "a", "u") if k in points]
        f2s = [points[k][1] for k in order]
        f1s = [points[k][0] for k in order]
        if len(order) == 3:
            closed_f2 = f2s + [f2s[0]]
            closed_f1 = f1s + [f1s[0]]
            ax.plot(closed_f2, closed_f1, color=ACCENT, linewidth=1.5, alpha=0.6)
            ax.fill(closed_f2, closed_f1, color=ACCENT, alpha=0.12)
        ax.scatter(f2s, f1s, s=90, color=ACCENT, zorder=3, edgecolors="white", linewidths=1.5)
        for k in order:
            f1, f2 = points[k]
            ax.annotate(
                f"/{k}/", (f2, f1), textcoords="offset points", xytext=(8, 6),
                fontsize=13, fontweight="bold", color=TEXT_PRIMARY,
            )
    ax.set_xlabel("F2 (Hz) — hinten ← → vorne")
    ax.set_ylabel("F1 (Hz) — geschlossen ↑ ↓ offen")
    ax.set_title("Vokalraum (Vokaltrapez)")
    ax.invert_xaxis()
    ax.invert_yaxis()
    ax.grid(color=PLOT_GRID, alpha=0.5)
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
    ax.spines["polar"].set_color(PLOT_GRID)
    ax.grid(color=PLOT_GRID)

    ax.plot(angles, vals, color=ACCENT, linewidth=2)
    ax.fill(angles, vals, color=ACCENT, alpha=0.22)

    fig.tight_layout()
    return fig
