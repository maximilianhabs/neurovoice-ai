"""Visualisierungen: Wellenform, Spektrogramm mit Pitch-/Intensitäts-Overlay."""

import matplotlib.pyplot as plt
import numpy as np
import parselmouth


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
    ax.legend(loc="upper right")

    fig.tight_layout()
    return fig


def intensity_figure(sound: parselmouth.Sound):
    intensity = sound.to_intensity()
    fig, ax = plt.subplots(figsize=(10, 2))
    ax.plot(intensity.xs(), intensity.values[0], color="#c05621")
    ax.set_xlabel("Zeit (s)")
    ax.set_ylabel("Intensität (dB)")
    ax.set_title("Lautstärkeverlauf")
    fig.tight_layout()
    return fig
