"""Globales Styling — Design-Transfer vom EDF-Analyzer-Redesign (Apple-artige Optik).

Bewusst KEIN eigenes Font-Hosting (anders als EDF-Analyzer, das Inter lokal unter
static/fonts/ ausliefert) -- nur Systemschriften (-apple-system/SF Pro), kein zusätzliches
Static-Serving nötig, kein CDN-Request (passt zum Datenschutz-Prinzip des Projekts, gleiche
Begründung wie beim EDF-Analyzer-Fix gegen fonts.googleapis.com-Requests).
"""

import streamlit as st

from core.design_tokens import (
    ACCENT,
    ACCENT_HOVER,
    BG_SUBTLE,
    BORDER,
    DANGER,
    FONT_EYEBROW_PX,
    FONT_HERO_PX,
    FONT_SUBTITLE_PX,
    INFO,
    RADIUS_LG,
    RADIUS_MD,
    RADIUS_SM,
    RADIUS_XL,
    SUCCESS,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING,
)


def apply_global_style() -> None:
    """Injiziert CSS-Variablen + Utility-Klassen (.dw-eyebrow/.dw-hero-title/.dw-subtitle/
    .dw-card) -- einmal pro Seitenaufruf ganz oben in app.py aufrufen, vor allen anderen
    st.-Aufrufen. Ändert NICHT die fachliche Bedeutung der Ampelfarben in
    core/reference_ranges.py, nur die konkreten Hex-Werte (jetzt identisch zum EDF-Analyzer).
    """
    st.markdown(f"""
    <style>
    :root {{
        --dw-bg-subtle: {BG_SUBTLE};
        --dw-surface: {SURFACE};
        --dw-border: {BORDER};
        --dw-text-primary: {TEXT_PRIMARY};
        --dw-text-secondary: {TEXT_SECONDARY};
        --dw-accent: {ACCENT};
        --dw-accent-hover: {ACCENT_HOVER};
        --dw-danger: {DANGER};
        --dw-warning: {WARNING};
        --dw-success: {SUCCESS};
        --dw-info: {INFO};
        --dw-radius-sm: {RADIUS_SM}px;
        --dw-radius-md: {RADIUS_MD}px;
        --dw-radius-lg: {RADIUS_LG}px;
        --dw-radius-xl: {RADIUS_XL}px;
    }}

    html, body, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', sans-serif;
    }}
    h1, h2, h3, h4, h5, h6 {{
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
        font-weight: 600;
        letter-spacing: -0.01em;
        color: var(--dw-text-primary);
    }}
    h1 {{ letter-spacing: -0.02em; }}
    [data-testid="stMetricValue"] {{ font-weight: 700; }}

    /* Sidebar -- dezenter Off-White-Hintergrund statt Streamlits Standard-Weiß, wie beim
    EDF-Analyzer-Redesign. */
    [data-testid="stSidebar"] {{
        background: var(--dw-bg-subtle);
        border-right: 1px solid var(--dw-border);
    }}
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
        font-weight: 500;
        color: var(--dw-text-primary);
    }}

    /* Karten / Container */
    div[data-testid="stExpander"] {{
        border-radius: var(--dw-radius-md);
        border: 1px solid #e8eaed;
    }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: var(--dw-radius-md) !important;
    }}
    .stButton button {{ border-radius: var(--dw-radius-sm); }}
    hr {{ margin: 0.6rem 0; opacity: 0.5; }}

    /* Dataframe / Tabellarische Übersicht -- etwas großzügigere Ecken, ruhigerer Rand */
    div[data-testid="stDataFrame"] {{
        border-radius: var(--dw-radius-md);
        overflow: hidden;
        border: 1px solid var(--dw-border);
    }}

    /* Mikrofon-/Datei-Aufnahme deutlich größer (Nutzer-Feedback 2026-08-15: Steuerelemente
    waren winzig und schwer zu treffen). data-testid noch nicht final gegengeprüft im Browser
    (kein Mikrofon-Zugriff im Sandbox-Browser) -- bei Bedarf nach echtem Test nachschärfen. */
    div[data-testid="stAudioInput"], div[data-testid="stFileUploader"] {{
        border: 1.5px solid var(--dw-border);
        border-radius: var(--dw-radius-lg);
        padding: 16px;
        background: var(--dw-surface);
    }}
    div[data-testid="stAudioInput"] button, div[data-testid="stFileUploader"] button {{
        transform: scale(1.35);
        margin: 6px 10px;
    }}
    /* Dezenter Hinweis waehrend die Aufnahme laeuft (Nutzer-Feedback 2026-08-15) -- nutzt
    :has() auf den Stop-Button, den st.audio_input waehrend der Aufnahme zeigt. Bewusst SEHR
    dezent (kein grelles Rot), wie gewuenscht. Selektor auf `aria-label` gestuetzt, da mir kein
    Browser mit Mikrofonzugriff zum Gegenpruefen zur Verfuegung steht -- bitte visuell
    bestaetigen, ob es greift. */
    div[data-testid="stAudioInput"]:has(button[aria-label*="Stop" i]) {{
        background: color-mix(in srgb, var(--dw-danger) 6%, var(--dw-surface));
        border-color: color-mix(in srgb, var(--dw-danger) 40%, var(--dw-border));
    }}

    /* ── Eyebrow+Hero-Title+Subtitle-Muster (aus dem EDF-Analyzer-Referenz-Prompt,
    auf App-Seitentitel statt Marketing-Hero herunterskaliert) ─────────────────────────── */
    .dw-eyebrow {{
        font-size: {FONT_EYEBROW_PX}px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
        color: var(--dw-text-secondary);
        margin-bottom: 4px;
    }}
    .dw-hero-title {{
        font-size: {FONT_HERO_PX}px;
        font-weight: 600;
        letter-spacing: -0.02em;
        line-height: 1.15;
        color: var(--dw-text-primary);
        margin: 0 0 6px 0;
    }}
    .dw-subtitle {{
        font-size: {FONT_SUBTITLE_PX}px;
        font-weight: 400;
        color: var(--dw-text-secondary);
        line-height: 1.4;
        margin: 0 0 20px 0;
    }}
    .dw-card {{
        background: var(--dw-surface);
        border: 1px solid var(--dw-border);
        border-radius: var(--dw-radius-lg);
        padding: 20px 24px;
    }}
    .dw-card-subtle {{
        background: var(--dw-bg-subtle);
        border: 1px solid var(--dw-border);
        border-radius: var(--dw-radius-lg);
        padding: 20px 24px;
    }}

    /* Mobile-Grundbasis */
    @media (max-width: 640px) {{
        h1 {{ font-size: 1.4rem !important; }}
        h2 {{ font-size: 1.15rem !important; }}
        [data-testid="stMetricValue"] {{ font-size: 1.1rem !important; }}
        .block-container {{ padding-left: 0.8rem !important; padding-right: 0.8rem !important; }}
        .dw-hero-title {{ font-size: 24px; }}
    }}
    </style>
    """, unsafe_allow_html=True)
