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
    SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING,
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


def word_duration_histogram_figure(words: list[dict]):
    """Histogramm der einzelnen Wortdauern (V1, docs/konzept_visualisierungen.md 3.4) --
    macht die Streuung der Wortdauern sichtbar, die die reine `mean_word_duration_s`-Kennzahl
    verdeckt (z.B. viele kurze Woerter + wenige sehr lange Ausreisser vs. gleichmaessig
    mittellange Woerter koennen denselben Mittelwert ergeben, sehen aber im Histogramm sehr
    unterschiedlich aus). `words`: Liste von {"word", "start", "end", "score"} aus der
    WhisperX-Transkription."""
    durations = [
        w["end"] - w["start"] for w in words
        if w.get("start") is not None and w.get("end") is not None and w["end"] > w["start"]
    ]
    fig, ax = plt.subplots(figsize=(8, 3))
    if durations:
        n_bins = min(20, max(5, len(durations) // 2))
        ax.hist(durations, bins=n_bins, color=ACCENT, alpha=0.85, edgecolor="white")
        ax.axvline(float(np.mean(durations)), color=TEXT_PRIMARY, linewidth=1.5, linestyle="--", label="Ø")
        ax.legend(loc="upper right", fontsize=8)
    else:
        ax.text(0.5, 0.5, "Keine Wort-Zeitstempel verfügbar", ha="center", va="center", color=TEXT_SECONDARY, transform=ax.transAxes)
    ax.set_xlabel("Wortdauer (s)")
    ax.set_ylabel("Anzahl Wörter")
    ax.set_title("Verteilung der Wortdauern")
    ax.grid(color=PLOT_GRID, alpha=0.5, axis="y")
    fig.tight_layout()
    return fig


def pause_timeline_figure(words: list[dict], total_duration_s: float | None = None):
    """Sprechfluss-Zeitstrahl (docs/konzept_visualisierungen.md 3.2) -- zeigt Sprech- und
    Pausensegmente als horizontalen Balken statt der bisherigen isolierten Pausen-Kacheln
    (Anzahl/Ø-/Max-/Mikro-/Makro-Dauer). Macht auf einen Blick sichtbar, WO im Text Pausen
    liegen, ob sie gleichmaessig verteilt oder geklumpt sind -- Information, die reine
    Kennzahlen nicht transportieren. Nutzt DIESELBEN Schwellenwerte wie
    core.speech_metrics.compute_speech_metrics() (0,25s/0,5s), damit Bild und Zahlen nie
    auseinanderlaufen."""
    from core.speech_metrics import DEFAULT_PAUSE_THRESHOLD_S, MACRO_PAUSE_THRESHOLD_S

    timed_words = [w for w in words if w.get("start") is not None and w.get("end") is not None]
    timed_words.sort(key=lambda w: w["start"])

    fig, ax = plt.subplots(figsize=(10, 1.6))
    if not timed_words:
        ax.text(0.5, 0.5, "Keine Wort-Zeitstempel verfügbar", ha="center", va="center", color=TEXT_SECONDARY, transform=ax.transAxes)
        ax.axis("off")
        fig.tight_layout()
        return fig

    speech_spans = [(w["start"], w["end"] - w["start"]) for w in timed_words]
    ax.broken_barh(speech_spans, (0.3, 0.6), facecolors=ACCENT, label="Sprechsegment")

    for prev, cur in zip(timed_words, timed_words[1:]):
        gap = cur["start"] - prev["end"]
        if gap < DEFAULT_PAUSE_THRESHOLD_S:
            continue
        color = WARNING if gap >= MACRO_PAUSE_THRESHOLD_S else SUCCESS
        ax.broken_barh([(prev["end"], gap)], (0.3, 0.6), facecolors=color, alpha=0.85)

    end_time = total_duration_s if total_duration_s else timed_words[-1]["end"]
    ax.set_xlim(0, end_time)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("Zeit (s)")
    ax.set_title("Sprechfluss-Zeitstrahl")
    ax.grid(color=PLOT_GRID, alpha=0.5, axis="x")

    from matplotlib.patches import Patch
    legend_handles = [
        Patch(facecolor=ACCENT, label="Sprechsegment"),
        Patch(facecolor=SUCCESS, label="Mikropause (250–500ms)"),
        Patch(facecolor=WARNING, label="Makropause (≥500ms)"),
    ]
    ax.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.35), ncol=3, fontsize=7.5, frameon=False)

    fig.tight_layout()
    return fig


def ddk_rhythm_figure(cycle_times: list[float], duration_s: float | None = None):
    """DDK-Rhythmus-Spur (docs/konzept_visualisierungen.md 3.3) -- macht "Regelmaessigkeit"
    (bisher nur als einzelne CV-Zahl, core.interpretation::PARAMETER_INFO["cycle_interval_cv"])
    tatsaechlich sichtbar: Tick-Marken der erkannten Silben-Onsets entlang einer Zeitachse,
    darunter die Zyklus-Intervalle als Balken -- "stolpernde"/unregelmaessige Silbenfolgen
    (Verdachtsmoment fuer ataktische Dysarthrie) werden als sichtbar ungleichmaessige
    Balkenhoehen erkennbar, waehrend eine einzelne CV-Zahl diese Textur abstrahiert."""
    fig, (ax_ticks, ax_bars) = plt.subplots(
        2, 1, figsize=(9, 3), height_ratios=[1, 2.2], sharex=False,
    )

    if not cycle_times or len(cycle_times) < 2:
        for ax in (ax_ticks, ax_bars):
            ax.axis("off")
        ax_ticks.text(
            0.5, 0.5, "Zu wenige erkannte Silbenzyklen für eine Rhythmus-Spur",
            ha="center", va="center", color=TEXT_SECONDARY, transform=ax_ticks.transAxes,
        )
        fig.tight_layout()
        return fig

    end_time = duration_s if duration_s else cycle_times[-1] + 0.2
    ax_ticks.eventplot([cycle_times], colors=[ACCENT], lineoffsets=0, linelengths=0.8, linewidths=2)
    ax_ticks.set_xlim(0, end_time)
    ax_ticks.set_yticks([])
    ax_ticks.set_title("DDK-Rhythmus-Spur — erkannte Silben-Onsets")
    for spine in ("top", "right", "left"):
        ax_ticks.spines[spine].set_visible(False)
    ax_ticks.set_xticklabels([])

    intervals = np.diff(cycle_times)
    interval_positions = cycle_times[1:]
    mean_interval = float(np.mean(intervals))
    colors = [WARNING if abs(iv - mean_interval) > 0.4 * mean_interval else ACCENT for iv in intervals]
    ax_bars.bar(interval_positions, intervals, width=mean_interval * 0.6, color=colors)
    ax_bars.axhline(mean_interval, color=TEXT_PRIMARY, linewidth=1, linestyle="--", label="Ø Intervall")
    ax_bars.set_xlim(0, end_time)
    ax_bars.set_xlabel("Zeit (s)")
    ax_bars.set_ylabel("Zyklus-Intervall (s)")
    ax_bars.legend(loc="upper right", fontsize=8)
    ax_bars.grid(color=PLOT_GRID, alpha=0.5, axis="y")

    fig.tight_layout()
    return fig


def perturbation_bundle_figure(entries: list[dict]):
    """Gebuendelte Perturbations-Ansicht (docs/konzept_visualisierungen.md 3.5) -- zeigt
    Jitter (local/RAP/PPQ5) und Shimmer (local/APQ11) als EIN gruppiertes Balkendiagramm statt
    5 isolierter Kacheln, jeweils normalisiert als Vielfaches des eigenen Normwert-Cutoffs
    (core/reference_ranges.py::good_zone_bounds() -- dieselbe Quelle wie die Kachel-Ampel,
    kann also nie von den Zahlen abweichen). Macht sofort sichtbar, ob ALLE Perturbationsmaße
    gemeinsam erhoeht sind (konsistentes Muster) oder nur eines heraussticht.

    `entries`: [{"label": str, "value": float|None, "cutoff": float|None}, ...] -- Werte OHNE
    gueltigen Cutoff (z.B. kein zones_func) werden uebersprungen.
    """
    usable = [e for e in entries if e["value"] is not None and e.get("cutoff")]
    fig, ax = plt.subplots(figsize=(7, 3))
    if not usable:
        ax.text(0.5, 0.5, "Keine Perturbationswerte mit Normwert verfügbar", ha="center", va="center", color=TEXT_SECONDARY, transform=ax.transAxes)
        ax.axis("off")
        fig.tight_layout()
        return fig

    labels = [e["label"] for e in usable]
    ratios = [e["value"] / e["cutoff"] for e in usable]
    colors = [WARNING if r > 1 else SUCCESS for r in ratios]
    x = np.arange(len(labels))
    ax.bar(x, ratios, color=colors, width=0.6)
    ax.axhline(1.0, color=TEXT_PRIMARY, linewidth=1.2, linestyle="--", label="Normwert-Cutoff")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8.5)
    ax.set_ylabel("Vielfaches des Cutoffs")
    ax.set_title("Perturbationsmaße im Vergleich")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(color=PLOT_GRID, alpha=0.5, axis="y")
    fig.tight_layout()
    return fig


def articulation_pause_bar_figure(articulation_span_s: float, total_pause_time_s: float):
    """Sprechrate/Pausenzeit-Balken (docs/konzept_visualisierungen.md 3.6) -- ein gestapelter
    horizontaler Balken, der die Sprechspanne in "reine Artikulationszeit" (Sprechen) und
    "Pausenzeit" aufteilt. Macht den Vergleich Netto- vs. Artikulationsrate (bisher zwei
    separate Kacheln, die man gedanklich selbst in Bezug setzen musste) auf einen Blick
    verstaendlich: wie viel der Sprechspanne ist tatsaechlich Sprechzeit vs. Pausenzeit.
    `articulation_span_s`: core.speech_metrics-Feld (erstes bis letztes Wort), enthaelt die
    Pausenzeit bereits MIT -- Sprechzeit wird daraus als articulation_span_s - total_pause_time_s
    abgeleitet, damit die Balkenlaenge korrekt der Spanne entspricht."""
    speaking_time_s = max(0.0, articulation_span_s - total_pause_time_s)

    fig, ax = plt.subplots(figsize=(8, 1.3))
    if articulation_span_s <= 0:
        ax.text(0.5, 0.5, "Keine Daten verfügbar", ha="center", va="center", color=TEXT_SECONDARY, transform=ax.transAxes)
        ax.axis("off")
        fig.tight_layout()
        return fig

    ax.barh(0, speaking_time_s, color=ACCENT, label="Artikulationszeit")
    ax.barh(0, total_pause_time_s, left=speaking_time_s, color=WARNING, label="Pausenzeit")

    speak_pct = speaking_time_s / articulation_span_s * 100
    if speaking_time_s > 0:
        ax.text(speaking_time_s / 2, 0, f"{speak_pct:.0f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=10)
    if total_pause_time_s > 0:
        ax.text(speaking_time_s + total_pause_time_s / 2, 0, f"{100 - speak_pct:.0f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=10)

    ax.set_xlim(0, articulation_span_s)
    ax.set_yticks([])
    ax.set_xlabel("Zeit (s)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.55), ncol=2, fontsize=8, frameon=False)
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


def voice_gender_estimate_figure(estimate: dict):
    """Visualisierung der F0-basierten Geschlechtsschaetzung (Nutzer-Wunsch 2026-08-17,
    core/voice_demographics.py::estimate_voice_gender()) -- horizontaler "Spektrum"-Balken
    statt nur Text/Prozentzahl: zeigt die beiden literaturbasierten F0-Referenzbereiche
    (Maenner ~100-146Hz, Frauen ~188-221Hz, siehe core/voice_demographics.py fuer die Quelle),
    die Entscheidungsgrenze (165Hz) UND den tatsaechlich gemessenen F0-Wert als Marker auf
    einen Blick. Macht sichtbar, wie WEIT der Wert von der Grenze entfernt liegt (= Grundlage
    der Konfidenzangabe), statt nur das Endergebnis als Zahl zu zeigen.

    `estimate`: Rueckgabe von estimate_voice_gender() -- bei label="nicht bestimmbar" wird ein
    neutraler Hinweis statt der Skala gezeigt (kein F0-Wert zum Einzeichnen vorhanden)."""
    from core.voice_demographics import BOUNDARY_HZ

    fig, ax = plt.subplots(figsize=(7, 2.1))

    if estimate["label"] == "nicht bestimmbar" or estimate["f0_hz"] is None:
        ax.text(0.5, 0.5, "F0 außerhalb des plausiblen Bereichs — keine Schätzung möglich",
                ha="center", va="center", color=TEXT_SECONDARY, transform=ax.transAxes)
        ax.axis("off")
        fig.tight_layout()
        return fig

    # Literaturbasierte Referenzbereiche, siehe core/voice_demographics.py-Docstring fuer die
    # Quelle -- hier bewusst dieselben Zahlen wie dort, nicht neu erfunden.
    male_range = (100, 146)
    female_range = (188, 221)
    f0 = estimate["f0_hz"]

    # Feste, eng gezogene Anzeige-Skala statt des vollen Plausibilitaets-Bereichs
    # (60-400Hz core/voice_demographics.py) -- deckt beide Referenzbereiche + realistische
    # Messwerte komfortabel ab, ohne die Baender auf einen schmalen Streifen zu quetschen. Bei
    # sehr extremen (aber noch plausiblen) F0-Werten dehnt sie sich mit aus, statt den Marker
    # abzuschneiden.
    lo = min(60, f0 - 20)
    hi = max(260, f0 + 20)

    ax.axhspan(0, 1, xmin=(male_range[0] - lo) / (hi - lo), xmax=(male_range[1] - lo) / (hi - lo),
               color=ACCENT, alpha=0.25, label="typisch männlich (Literatur)")
    ax.axhspan(0, 1, xmin=(female_range[0] - lo) / (hi - lo), xmax=(female_range[1] - lo) / (hi - lo),
               color=INFO, alpha=0.25, label="typisch weiblich (Literatur)")

    ax.axvline(BOUNDARY_HZ, color=TEXT_SECONDARY, linewidth=1, linestyle="--")
    ax.text(BOUNDARY_HZ, 0.97, "Grenze", ha="center", va="top", fontsize=7.5, color=TEXT_SECONDARY)

    marker_color = ACCENT if estimate["label"] == "männlich" else INFO
    ax.plot([f0], [0.5], marker="v", markersize=14, color=TEXT_PRIMARY, zorder=5)
    ax.plot([f0], [0.5], marker="o", markersize=9, color=marker_color, zorder=6)
    # Label ueber statt unter dem Marker, versetzt nach oben -- vermeidet Ueberlappung mit den
    # x-Achsen-Ticks direkt darunter (bei Marker nahe am linken/rechten Rand sonst abgeschnitten).
    ax.annotate(f"{f0:.0f} Hz", xy=(f0, 0.5), xytext=(0, 22), textcoords="offset points",
                ha="center", va="bottom", fontsize=9, fontweight="bold", color=TEXT_PRIMARY)

    ax.set_xlim(lo, hi)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("Mittleres F0 (Hz)")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(PLOT_GRID)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.42), ncol=2, fontsize=8, frameon=False)

    fig.tight_layout()
    return fig
