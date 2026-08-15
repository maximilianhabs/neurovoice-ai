"""Design-Tokens — zentrale Quelle für Farben/Typografie/Radien (CSS via core/shared.py::
apply_global_style() UND Python-seitig für matplotlib, das kein CSS lesen kann).

Übertragen vom EDF-Analyzer-Redesign (gedämpfte, "Apple-artige" Basis-Palette statt Ad-hoc-
Hex-Werte je Datei) — siehe dort core/design_tokens.py für die Ursprungsversion. Werte
bewusst IDENTISCH übernommen (nicht neu erfunden), damit alle eigenen Streamlit-Apps optisch
zusammengehören. Klinische Ampelfarben (core/reference_ranges.py) sind hier auf denselben
kanonischen Wert wie im EDF-Analyzer konsolidiert, ihre fachliche Bedeutung bleibt unverändert.
"""

# ── Neutrale Basis-Palette (Apple-artig: reines Weiß/Off-White, near-black Text) ──────────────
BG = "#ffffff"
BG_SUBTLE = "#f5f5f7"          # Apple-typisches Off-White für Sektions-/Card-Hintergründe
SURFACE = "#ffffff"            # Karten-Hintergrund auf BG_SUBTLE
BORDER = "rgba(0,0,0,0.08)"
TEXT_PRIMARY = "#1d1d1f"       # Apple near-black
TEXT_SECONDARY = "#86868b"     # Apple-Grau

# ── EIN Akzentton ───────────────────────────────────────────────────────────────────────────
ACCENT = "#0071e3"             # Apple Blue (primaryColor in .streamlit/config.toml gespiegelt)
ACCENT_HOVER = "#0077ed"

# ── Statusfarben — konsolidiert auf JE EINEN kanonischen Wert (siehe core/reference_ranges.py) ─
DANGER = "#c0392b"             # auffällig / kritisch
WARNING = "#e67e22"            # grenzwertig
SUCCESS = "#27ae60"            # im Normbereich
INFO = "#2471a3"               # neutral-informativ

# ── Radius-Skala ("continuous corners") ────────────────────────────────────────────────────
RADIUS_SM = 8
RADIUS_MD = 12
RADIUS_LG = 16
RADIUS_XL = 24

# ── Typografie-Skala (auf App-Seitentitel statt Marketing-Hero herunterskaliert) ──────────────
FONT_EYEBROW_PX = 13
FONT_HERO_PX = 30
FONT_SUBTITLE_PX = 16
FONT_BODY_PX = 15

# ── Spacing-Skala (px) ──────────────────────────────────────────────────────────────────────
SPACE = {1: 4, 2: 8, 3: 12, 4: 16, 5: 24, 6: 32, 7: 48, 8: 64}

# ── Solide Grau-Töne für matplotlib (core/plots.py) ────────────────────────────────────────
# matplotlib kann kein CSS-rgba() lesen, deshalb hier als konkrete Hex-Werte -- Apple-typische
# Systemgrau-Stufen, ungefähr passend zu BORDER (rgba(0,0,0,0.08)) auf weißem Hintergrund.
# NUR für "Chrome"-Elemente (Gauge-Track, Grid, Achsen) verwenden, NICHT für funktionale
# Kontrastfarben (z.B. F0-/Formant-Overlay im Spektrogramm -- die brauchen bewussten Kontrast
# gegen die "afmhot"-Colormap, keine Marken-Konsistenz, siehe core/plots.py).
PLOT_GRID = "#e5e5ea"
PLOT_TRACK = "#d1d1d6"
