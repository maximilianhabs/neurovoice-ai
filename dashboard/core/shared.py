"""Globales Styling — Design-Transfer vom EDF-Analyzer-Redesign (Apple-artige Optik).

Bewusst KEIN eigenes Font-Hosting (anders als EDF-Analyzer, das Inter lokal unter
static/fonts/ ausliefert) -- nur Systemschriften (-apple-system/SF Pro), kein zusätzliches
Static-Serving nötig, kein CDN-Request (passt zum Datenschutz-Prinzip des Projekts, gleiche
Begründung wie beim EDF-Analyzer-Fix gegen fonts.googleapis.com-Requests).
"""

import pandas as pd
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

    /* Statische st.table() -- fuer die Interpretations-Tabelle (core/shared.py::
    render_interpretation_table()) statt st.dataframe(), da Letzteres lange Zellen abschneidet
    (Nutzer-Feedback 2026-08-15). Text soll normal umbrechen, nicht abgeschnitten werden. */
    div[data-testid="stTable"] table {{
        border-collapse: collapse;
        width: 100%;
    }}
    div[data-testid="stTable"] th, div[data-testid="stTable"] td {{
        white-space: normal !important;
        vertical-align: top;
        text-align: left;
        padding: 8px 10px;
        border-bottom: 1px solid var(--dw-border);
        font-size: 13.5px;
        line-height: 1.4;
    }}
    div[data-testid="stTable"] th {{
        font-weight: 600;
        color: var(--dw-text-secondary);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.02em;
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

    /* Instruktions-Karten: Meta-Text (WAS zu tun ist) vs. Sprech-Ziel (WAS gesagt werden soll)
    -- Nutzer-Feedback 2026-08-15 (Live-Test): das eigentlich zu Sprechende war kleiner/nicht
    fett als der Instruktionstext drumherum, obwohl genau das im Fokus stehen sollte. */
    .dw-instruction-meta {{
        font-weight: 400;
        color: var(--dw-text-secondary);
    }}
    .dw-instruction-target {{
        display: block;
        font-weight: 700;
        font-size: 1.35em;
        color: var(--dw-text-primary);
        margin-top: 8px;
        line-height: 1.4;
    }}

    /* ── Kachel-Komponente (kpi_tile(), Design-Bereinigung 2026-08-15, siehe docs/backlog.md
    "Konzept: Design-Bereinigung") -- ersetzt die bisherigen Tacho-Gauges. Nuechtern: nur der
    obere Rand traegt die Statusfarbe, nicht die ganze Flaeche (1:1 vom EDF-Analyzer
    uebernommen, dort kpi_tile() genannt). ──────────────────────────────────────────────── */
    .dw-tile {{
        background: var(--dw-surface);
        border: 1px solid var(--dw-border);
        border-top: 3px solid var(--dw-tile-accent, var(--dw-border));
        border-radius: var(--dw-radius-md);
        padding: 12px 14px;
        min-height: 138px;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }}
    .dw-tile-label {{
        font-size: 12px;
        font-weight: 600;
        color: var(--dw-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }}
    .dw-tile-value {{
        font-size: 22px;
        font-weight: 700;
        color: var(--dw-text-primary);
        line-height: 1.2;
        margin: 2px 0;
    }}
    .dw-tile-sub {{
        font-size: 12.5px;
        font-weight: 600;
    }}
    .dw-tile-range {{
        font-size: 11px;
        color: var(--dw-text-secondary);
        font-weight: 500;
    }}
    .dw-tile-desc {{
        font-size: 11.5px;
        color: var(--dw-text-secondary);
        line-height: 1.35;
        margin-top: auto;
        padding-top: 4px;
    }}

    /* ── Evidenz-Glossar (P11, core/shared.py::render_glossary()) ───────────────────────── */
    .dw-glossary-entry {{
        border-bottom: 1px solid var(--dw-border);
        padding: 12px 2px;
    }}
    .dw-glossary-entry:first-child {{ padding-top: 0; }}
    .dw-glossary-entry:last-child {{ border-bottom: none; }}
    .dw-glossary-label {{
        font-size: 14.5px;
        font-weight: 700;
        color: var(--dw-text-primary);
        margin-bottom: 4px;
    }}
    .dw-glossary-evidence {{
        font-size: 10.5px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        border: 1px solid;
        border-radius: 999px;
        padding: 1px 8px;
        margin-left: 6px;
        white-space: nowrap;
    }}
    .dw-glossary-desc {{
        font-size: 13px;
        color: var(--dw-text-secondary);
        line-height: 1.5;
        margin: 3px 0;
    }}
    .dw-glossary-lit {{
        font-size: 11.5px;
        color: var(--dw-text-secondary);
        font-style: italic;
        margin-top: 4px;
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


# Erklaerung der F0/F1-F3-Overlays im Spektrogramm (core/plots.py::spectrogram_figure()) --
# Nutzer-Feedback 2026-08-15: die Formant-Tracks wurden angezeigt, aber nirgends erklaert, was
# sie bedeuten. Geteilt statt 5x dupliziert (testdaten.py + 4 Guide-Module).
SPECTROGRAM_LEGEND_CAPTION = (
    "**F0** (türkis) — Grundfrequenz/Tonhöhe der Stimme. **F1** (grün) — Vokaltrakt-Resonanz, "
    "hängt vor allem mit der Zungenhöhe zusammen (offen/geschlossen). **F2** (gelb) — "
    "Vokaltrakt-Resonanz, hängt vor allem mit der Zungenposition vorne/hinten zusammen. "
    "**F3** (rot) — dritte Resonanz, trägt zur Klangfarbe bei. F1-F3 zusammen formen den "
    "Vokalklang; ihre Position/Streuung ist ein grober Anhaltspunkt für die genutzte "
    "Artikulationsbeweglichkeit."
)


INSTRUCTION_TEXT_SCALE = {"Normal": 1.0, "Groß": 1.3, "Sehr groß": 1.6}


def instruction_text_scale_control(key: str = "default") -> None:
    """Steuerung fuer die Schriftgroesse der Aufnahme-Instruktion (.dw-card-subtle, z.B.
    "Lies den folgenden Satz vor..."/"Halte den Vokal..."). Nutzer-Feedback 2026-08-15
    (Nachbesserung): urspruenglich in der SIDEBAR, das ist falsch platziert -- gehoert direkt
    neben/an die Instruktion selbst (1) inhaltlich naeher an dem, was sie steuert, (2) die
    Sidebar soll bei einer kuenftigen Mobile-Optimierung einklappbar sein, ein dort
    "verschwindendes" Steuerelement waere fuer genau die Zielgruppe (schlecht lesende
    Patient:innen) unbrauchbar. Rendert jetzt IM Hauptbereich, kompakt, direkt vor der
    Instruktions-Card aufzurufen.

    BUGFIX 2026-08-15 (Live-Test): urspruengliche Fassung nutzte `st.select_slider(key=f"text_scale_{key}")`
    -- jede Aufrufstelle (z.B. jeder Vokal-Tab in vokalisation.py) hatte damit einen EIGENEN,
    unabhaengigen Widget-Zustand, der beim Tab-Wechsel wieder auf "Normal" zurueckfiel, obwohl
    die Groesse auf einem anderen Tab schon gesetzt war. Fix: der aktuelle Wert liegt jetzt in
    EINEM gemeinsamen `st.session_state["text_scale"]`, ueber die ganze Sitzung (auch
    seitenuebergreifend) hinweg konsistent -- `key` dient nur noch dazu, pro Aufrufstelle
    eindeutige BUTTON-Widget-IDs zu erzeugen (Streamlit verbietet doppelte IDs), nicht mehr zur
    Werthaltung. Gleichzeitig auf `st.button()`-Gruppe statt Slider umgestellt (Nutzer-Feedback:
    "kein Regler, sondern eher Buttons")."""
    if "text_scale" not in st.session_state:
        st.session_state["text_scale"] = "Normal"
    current = st.session_state["text_scale"]

    for label in INSTRUCTION_TEXT_SCALE:
        clicked = st.button(
            label, key=f"text_scale_btn_{key}_{label}",
            type="primary" if label == current else "secondary",
            width="stretch",
        )
        if clicked and label != current:
            st.session_state["text_scale"] = label
            st.rerun()

    if INSTRUCTION_TEXT_SCALE[current] != 1.0:
        st.markdown(
            f"<style>.dw-card-subtle, .dw-card-subtle * {{ font-size: {INSTRUCTION_TEXT_SCALE[current]}em !important; "
            f"line-height: 1.5 !important; }}</style>",
            unsafe_allow_html=True,
        )


def recording_start_blip() -> None:
    """Dezenter Audio-Piep beim Start einer Mikrofonaufnahme (Nutzer-Idee 2026-08-15, docs/
    backlog.md "Konzept: dezenter Audio-Piep bei Aufnahmestart") -- zusaetzlich zum
    bestehenden visuellen Hinweis (roter Rahmen-Tint, siehe apply_global_style()) als
    auditiver Cue, dass die Aufnahme jetzt laeuft.

    `st.audio_input()` liefert keinen Live-Callback beim Aufnahmestart (wie schon bei P8) --
    eine reine CSS-Loesung kann keinen Ton abspielen, hier ist eine kleine JS-Komponente
    unumgaenglich. Nutzt `st.iframe()` mit einem HTML-String (nicht `st.markdown
    (unsafe_allow_html=True)`, da <script>-Tags dort unzuverlaessig ausgefuehrt werden;
    `st.components.v1.html()` urspruenglich verwendet, aber zur Deploy-Zeit als "wird nach
    2026-06-01 entfernt" markiert -- auf die empfohlene Nachfolge-API umgestellt) mit einem
    MutationObserver auf dem ELTERN-Dokument (`window.parent.document`, da die Komponente
    selbst in einem eigenen iframe rendert -- `st.iframe()` erlaubt laut Doku explizit
    JavaScript-Ausfuehrung + Same-Origin-Zugriff auf die Streamlit-App), der denselben
    Zustandswechsel beobachtet wie der bestehende CSS-Trick in apply_global_style()
    (Erscheinen eines Stop-Buttons mit `aria-label*="Stop"`) und dabei einen kurzen, leisen
    Sinuston ueber die Web Audio API abspielt -- kein Audio-Datei-Asset noetig, synthetisch
    erzeugt (passt zum Datenschutz-Prinzip "kein CDN/lokales Hosting").

    Nur EINMAL pro Seite aufrufen (nicht pro Tab/Teilaufgabe) -- der Observer beobachtet das
    gesamte Dokument, erkennt also jeden Stop-Button, der auf der Seite erscheint, unabhaengig
    davon, in welchem Tab/welcher Teilaufgabe die Aufnahme laeuft. Ein Guard-Flag auf
    `document` verhindert doppelte Observer bei Streamlit-Reruns (die Komponente wird bei
    jedem Rerun neu gerendert, das Eltern-Dokument selbst laedt aber nicht neu).

    NICHT auditiv im Sandbox-Browser vorab testbar (kein Mikrofonzugriff) -- bitte beim
    naechsten echten Test durch den Nutzer bestaetigen, insbesondere Autoplay-Verhalten in
    Safari (dort strenger als Chrome/Firefox bzgl. AudioContext ohne direkten Klick-Kontext).

    Bugfix 2026-08-16 (Nutzer-Feedback "Piepston triggert nur beim ersten Mal"): zwei separate
    Ursachen behoben. (1) Der alte Code trug jeden gesehenen Button-Knoten in ein WeakSet ein
    und spielte den Ton NIE WIEDER fuer denselben Knoten -- `st.audio_input()` scheint aber
    denselben Button-Knoten ueber mehrere Start/Stop-Zyklen hinweg wiederzuverwenden (nur das
    aria-label wechselt zwischen "Start"/"Stop"), wodurch der Ton nach der allerersten Aufnahme
    dieses Widgets fuer immer stumm blieb. Jetzt traegt jeder Button-Knoten SELBST ein
    "scharf/entschaerft"-Flag, das beim Wechsel zurueck auf "Start" zurueckgesetzt wird --
    dadurch kann jede neue Aufnahme wieder ausloesen. (2) Jeder Ton erzeugte vorher einen
    KOMPLETT NEUEN `AudioContext` und schloss ihn danach -- wiederholtes Neu-Erzeugen eines
    AudioContext ohne direkten Klick-Kontext (der MutationObserver-Callback laeuft asynchron
    NACH dem Klick) kann von Browsern nach dem ersten Mal als "kein Nutzer-Gesture" behandelt
    und im "suspended"-Zustand belassen werden. Jetzt wird EIN AudioContext einmalig erzeugt,
    dauerhaft auf `document` gehalten und bei Bedarf per `resume()` reaktiviert statt neu
    gebaut.
    """
    st.iframe(
        """
        <script>
        (function() {
            var doc;
            try {
                doc = window.parent.document;
            } catch (e) {
                return;
            }
            if (doc.__nvBlipInstalled) { return; }
            doc.__nvBlipInstalled = true;

            function getCtx() {
                if (!doc.__nvBlipCtx) {
                    var Ctx = window.parent.AudioContext || window.parent.webkitAudioContext;
                    doc.__nvBlipCtx = new Ctx();
                }
                return doc.__nvBlipCtx;
            }

            function playBlip() {
                try {
                    var ctx = getCtx();
                    if (ctx.state === "suspended") { ctx.resume(); }
                    var osc = ctx.createOscillator();
                    var gain = ctx.createGain();
                    osc.type = "sine";
                    osc.frequency.value = 880;
                    gain.gain.setValueAtTime(0, ctx.currentTime);
                    gain.gain.linearRampToValueAtTime(0.12, ctx.currentTime + 0.012);
                    gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.11);
                    osc.connect(gain);
                    gain.connect(ctx.destination);
                    osc.start();
                    osc.stop(ctx.currentTime + 0.13);
                } catch (e) { /* Autoplay-Policy o.ae. -- bewusst still ignoriert */ }
            }

            function scan() {
                var buttons = doc.querySelectorAll('button[aria-label]');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    var isStop = /stop/i.test(btn.getAttribute('aria-label') || '');
                    if (isStop) {
                        if (!btn.__nvBlipArmed) {
                            btn.__nvBlipArmed = true;
                            playBlip();
                        }
                    } else {
                        btn.__nvBlipArmed = false;
                    }
                }
            }

            var observer = new MutationObserver(scan);
            observer.observe(doc.body, {
                childList: true, subtree: true,
                attributes: true, attributeFilter: ["aria-label"],
            });
        })();
        </script>
        """,
        height=1, width=1,
    )


def recording_duration_feedback_style(green_s: float, orange_s: float, red_s: float, key: str = "default") -> None:
    """P8 (docs/backlog.md, Nutzer-Idee 2026-08-15): faerbt den Aufnahme-Rahmen waehrend einer
    laufenden Mikrofonaufnahme zeitabhaengig gruen -> orange -> rot ein, als Signal "kann/sollte
    beendet werden". `st.audio_input()` liefert waehrend der Aufnahme KEINEN Live-Callback (nur
    das fertige Ergebnis nach Stop) -- eine eigene JS-Komponente waere der "saubere" Weg, aber
    deutlich groesserer Aufwand. Stattdessen eine reine CSS-`@keyframes`-Animation: startet,
    sobald der Stop-Button erscheint (:has()-Trick, siehe apply_global_style()), laeuft dann rein
    clientseitig relativ zu diesem Zeitpunkt -- kein Streamlit-Rerun/Python-Timer noetig.

    `green_s`/`orange_s`/`red_s` sind Sekunden-Schwellen (aufsteigend). `key` erlaubt mehrere
    unabhaengige Instanzen auf derselben Seite (z.B. DDK-Tabs mit unterschiedlichen Ziel-
    Dauern) -- ohne eigenen Key wuerde die zuletzt injizierte Animation alle vorherigen auf der
    Seite ueberschreiben (CSS-`@keyframes`-Namen sind global).

    NICHT visuell im Browser verifizierbar (kein Mikrofonzugriff im Sandbox-Browser, wie schon
    beim bestehenden dezenten Aufnahme-Hinweis) -- bitte nach dem Deploy einmal eine echte
    Aufnahme laufen lassen und den Farbverlauf gegenpruefen.
    """
    total = red_s + 3  # Puffer, damit die Animation nicht kurz vor Rot wieder auf 100% springt
    def _pct(s: float) -> float:
        return max(0.0, min(100.0, s / total * 100))

    anim_name = f"nv-rec-timer-{key}"
    st.markdown(
        f"""
        <style>
        @keyframes {anim_name} {{
            0% {{ border-color: {SUCCESS}; box-shadow: 0 0 0 1px color-mix(in srgb, {SUCCESS} 35%, transparent); }}
            {_pct(green_s):.1f}% {{ border-color: {SUCCESS}; box-shadow: 0 0 0 1px color-mix(in srgb, {SUCCESS} 35%, transparent); }}
            {_pct(orange_s):.1f}% {{ border-color: {WARNING}; box-shadow: 0 0 0 1px color-mix(in srgb, {WARNING} 45%, transparent); }}
            {_pct(red_s):.1f}% {{ border-color: {DANGER}; box-shadow: 0 0 0 1px color-mix(in srgb, {DANGER} 55%, transparent); }}
            100% {{ border-color: {DANGER}; box-shadow: 0 0 0 1px color-mix(in srgb, {DANGER} 55%, transparent); }}
        }}
        div[data-testid="stAudioInput"]:has(button[aria-label*="Stop" i]) {{
            animation: {anim_name} {total}s linear forwards;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_subject_badge() -> None:
    """Zeigt die aktuell zugeordnete Proband:innen-ID + Alter in der Sidebar (P10, docs/
    backlog.md) -- Nutzer-Vorgabe: auf JEDER Seite/jedem Modul sichtbar bleiben, damit klar
    ist, "bei welcher ID man grade ist". Einmal zentral in app.py aufgerufen, VOR pg.run() --
    Sidebar-Inhalt ausserhalb der eigentlichen Seiten-Funktion bleibt ueber Seitenwechsel
    hinweg bestehen, muss also nicht in jeder View einzeln aufgerufen werden."""
    subject_id = st.session_state.get("subject_id")
    if not subject_id:
        return
    age = st.session_state.get("subject_age")
    st.sidebar.markdown(
        f'<div style="padding:10px 12px;margin-bottom:12px;border-radius:var(--dw-radius-md);'
        f'background:var(--dw-bg-subtle);border:1px solid var(--dw-border);">'
        f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:0.02em;'
        f'color:var(--dw-text-secondary);font-weight:600;">Proband:in</div>'
        f'<div style="font-size:16px;font-weight:700;color:var(--dw-text-primary);">{subject_id}</div>'
        f'<div style="font-size:12px;color:var(--dw-text-secondary);">Alter {age if age is not None else "–"}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_interpretation_table(rows: list[dict]) -> None:
    """Rendert die Laborwert-Interpretationstabelle (core.interpretation.build_rows()) so, dass
    lange Texte ("Was es misst"/"Kontext") vollstaendig lesbar sind. Nutzer-Feedback
    2026-08-15: st.dataframe() (glide-data-grid) schneidet lange Zellen mit Ellipsis ab, ohne
    Moeglichkeit den Volltext zu sehen -- st.table() umbricht stattdessen normal. Geteilt
    zwischen allen Modul-Seiten + Gesamtbericht, damit nicht 6x dieselbe Umstellung noetig ist,
    falls die Darstellung nochmal wechselt."""
    st.table(pd.DataFrame(rows))


_EVIDENCE_COLORS = {
    "gut etabliert": SUCCESS,
    "in der Forschung diskutiert": INFO,
    "eigene Heuristik / explorativ": TEXT_SECONDARY,
    "deskriptiv, kein Krankheits-Marker": TEXT_SECONDARY,
}


def render_glossary(entries: list[dict]) -> None:
    """Rendert das ausfuehrliche Evidenz-Glossar (P11, docs/backlog.md "Kompakte Uebersicht +
    ausfuehrliches Evidenz-Glossar trennen") -- ein Block je Parameter mit Erklaerung, Kontext,
    Evidenz-Einordnung (gut etabliert / in der Forschung diskutiert / eigene Heuristik /
    deskriptiv), Referenzwerten (P15) und Literaturverweis. Ergaenzt
    core.interpretation.build_glossary_entries(). Bewusst als eigene, geraeumigere Darstellung
    statt einer weiteren Tabellenspalte -- analog zu den ausfuehrlichen Parameter-Erklaerungen
    beim EDF-Analyzer (z.B. views/ecg_hrv.py)."""
    for entry in entries:
        color = _EVIDENCE_COLORS.get(entry["evidence"], TEXT_SECONDARY)
        typical_html = (
            f'<div class="dw-glossary-desc"><b>Referenzwerte (Literatur):</b> {entry["typical_values"]}</div>'
            if entry.get("typical_values") else ""
        )
        lit_html = f'<div class="dw-glossary-lit">Quelle: {entry["literature"]}</div>' if entry["literature"] else ""
        age_html = f'<div class="dw-glossary-lit">{entry["age_caveat"]}</div>' if entry.get("age_caveat") else ""
        st.markdown(
            f'<div class="dw-glossary-entry">'
            f'<div class="dw-glossary-label">{entry["label"]} '
            f'<span class="dw-glossary-evidence" style="color:{color};border-color:{color};">{entry["evidence"]}</span>'
            f'</div>'
            f'<div class="dw-glossary-desc"><b>Was es misst:</b> {entry["description"]}</div>'
            f'<div class="dw-glossary-desc"><b>Kontext (deskriptiv):</b> {entry["context"]}</div>'
            f'{typical_html}{lit_html}{age_html}'
            f'</div>',
            unsafe_allow_html=True,
        )


_QUALITY_ZONE_RANK = {"danger": 2, "warning": 1, "success": 0, "neutral": -1}


def quality_tiles(q: dict) -> None:
    """Rendert den Aufnahmequalitäts-Check (Clipping/Stille/SNR, P6+Design-Bereinigung
    Baustein B) als eigenen, klar abgesetzten Block mit Überschrift + zusammenfassender
    Empfehlung -- geteilt zwischen allen 4 Guide-Modulen. Nutzer-Feedback 2026-08-15: der
    Qualitäts-Check "erschließt sich nicht", war nur 3 gleichrangige Kacheln ohne Einordnung,
    was sie in Summe bedeuten. `q` = Rueckgabe von core.audio.recording_quality_features()."""
    from core.reference_ranges import clipping_zones, snr_zones, zone_for_value

    def _fmt(value, decimals=1):
        return f"{value:.{decimals}f}" if value is not None else "–"

    with st.container(border=True):
        st.markdown(
            '<div style="font-size:13px;font-weight:600;text-transform:uppercase;'
            'letter-spacing:0.02em;color:var(--dw-text-secondary);margin-bottom:2px;">'
            "Aufnahmequalität prüfen</div>",
            unsafe_allow_html=True,
        )

        if q["clipping_pct"] is not None:
            lo, hi, zones = clipping_zones()
            clip_zone = zone_for_value(q["clipping_pct"], lo, hi, zones)
            clip_label = {"success": "unauffällig", "warning": "vereinzelt", "danger": "deutlich"}[clip_zone]
        else:
            clip_zone, clip_label = "neutral", "–"

        if q["snr_estimate_db"] is not None:
            lo, hi, zones = snr_zones()
            snr_zone = zone_for_value(q["snr_estimate_db"], lo, hi, zones)
            snr_label = {"success": "gut", "warning": "Hintergrundgeräusch hörbar", "danger": "Kennwerte ggf. verzerrt"}[snr_zone]
        else:
            snr_zone, snr_label = "neutral", "–"

        worst_zone = max((clip_zone, snr_zone), key=lambda z: _QUALITY_ZONE_RANK[z])
        if worst_zone == "danger":
            st.warning(
                "Aufnahmequalität eingeschränkt — die akustischen Kennwerte könnten dadurch "
                "verzerrt sein. Empfehlung: Aufnahme wiederholen (weniger Hintergrundgeräusch, "
                "normale Lautstärke ohne Übersteuerung).",
                icon=":material/replay:",
            )
        elif worst_zone == "warning":
            st.info(
                "Aufnahmequalität grenzwertig — Ergebnisse mit etwas Vorsicht interpretieren, "
                "bei Unsicherheit erneut aufnehmen.",
                icon=":material/info:",
            )
        else:
            st.caption("Unauffällig — keine technischen Einschränkungen erkannt.")

        qc1, qc2, qc3 = st.columns(3)
        with qc1:
            kpi_tile("Clipping", f"{_fmt(q['clipping_pct'], 1)} %", clip_label, clip_zone,
                     "Anteil der Samples nahe Vollaussteuerung — Faustregel, keine feste Norm.")
        with qc2:
            kpi_tile("Stille-Anteil", f"{_fmt(q['silence_pct'], 0)} %", "taskabhängig, kein fester Korridor", "neutral",
                     "Anteil leiser Fenster — bei Spontansprache mit Pausen normal auch 15-30%.")
        with qc3:
            kpi_tile("SNR (geschätzt)", f"{_fmt(q['snr_estimate_db'], 1)} dB", snr_label, snr_zone,
                     "90.–10. Perzentil der Fenster-Lautstärke — Heuristik aus der Signalverarbeitung, keine stimmklinische Referenz.")
        st.caption(
            "Rein informativ, kein automatisches Aussortieren. Grenzwerte sind pragmatische "
            "Faustregeln, keine klinische Norm."
        )


_TILE_ZONE_COLORS = {
    "success": SUCCESS,
    "warning": WARNING,
    "danger": DANGER,
    "info": INFO,
    "neutral": TEXT_SECONDARY,
}


def kpi_tile(
    label: str, value_text: str, sub_text: str = "", zone: str = "neutral",
    description: str | None = None, range_text: str | None = None,
) -> None:
    """Nuechterne Kennwert-Kachel statt Tacho-Gauge (Design-Bereinigung 2026-08-15, siehe
    docs/backlog.md "Konzept: Design-Bereinigung"/[[project_edf_ui_redesign]]). `zone` faerbt
    NUR den oberen Rand + das Status-Wort, nicht die ganze Kachel -- bewusst gedaempft.
    Rendert direkt via st.markdown (Seiteneffekt, wie st.metric()), kein Rueckgabewert.

    `range_text` (Bucket I, docs/backlog.md, Nutzer-Feedback 2026-08-15): der konkrete
    Normbereich (z.B. "5-8Hz"), NEUTRAL eingefaerbt (nicht in der Status-Farbe) -- Fakt statt
    Bewertung, direkt auf der Kachel sichtbar statt nur in der versteckten Detailtabelle.
    """
    color = _TILE_ZONE_COLORS.get(zone, TEXT_SECONDARY)
    sub_html = f'<div class="dw-tile-sub" style="color:{color}">{sub_text}</div>' if sub_text else ""
    range_html = f'<div class="dw-tile-range">Norm: {range_text}</div>' if range_text else ""
    desc_html = f'<div class="dw-tile-desc">{description}</div>' if description else ""
    st.markdown(
        f'<div class="dw-tile" style="--dw-tile-accent:{color}">'
        f'<div class="dw-tile-label">{label}</div>'
        f'<div class="dw-tile-value">{value_text}</div>'
        f'{sub_html}{range_html}{desc_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# Grobe empirische Schaetzung, NICHT praezise (WhisperX liefert keinen echten Fortschritts-
# Callback) -- nur genug fuer eine grobe visuelle Orientierung statt eines unbestimmten
# Spinners. Frueher gemessene Werte streuen erheblich (83-96s fuer ~10-12s Audio ~7-9x an
# einem Tag, aber 38s fuer 11,5s Audio ~3,3x bei einem frischen Test 2026-08-15 -- vermutlich
# Modell-Warmlauf-/Auslastungseffekte). 5x als Kompromiss, Deckelung bei 90% faengt grobe
# Abweichungen nach oben ab; bei zu optimistischer Schaetzung springt die Anzeige stattdessen
# kurz von <90% auf 100%, kein Beinbruch.
TRANSCRIPTION_REALTIME_FACTOR = 5.0


def transcribe_with_progress(audio_path: str, duration_s: float) -> dict:
    """Transkribiert in einem Hintergrund-Thread und zeigt eine GESCHAETZTE Fortschrittsleiste
    (Nutzer-Feedback 2026-08-15: unbestimmter Spinner allein wirkte wie ein Absturz bei
    1-2 Minuten Wartezeit). Deckelt bei 90%, bis der Thread tatsaechlich fertig ist -- verhindert
    einen falschen "100%, aber laeuft noch weiter"-Eindruck, da die Schaetzung oft daneben liegt.

    Blockiert die Streamlit-Sitzung weiterhin fuer die volle Dauer (kein echter Hintergrund-Job).
    Seit dem P9-Umbau (docs/konzept_p9_hintergrundjob_lokal.md) nur noch in `views/testdaten.py`
    verwendet (bewusst unveraendert erhalten, siehe dessen Docstring) -- `views/vorlesen.py`/
    `views/spontansprache.py` nutzen jetzt `render_transcription_job()` weiter unten (echter
    Hintergrund-Job ueber `worker.py`, Seite bleibt waehrenddessen bedienbar).
    """
    import threading
    import time

    from core.transcription import transcribe

    estimated_total_s = max(duration_s * TRANSCRIPTION_REALTIME_FACTOR, 10.0)
    result: dict = {}

    def _run():
        result["transcript"] = transcribe(audio_path)

    thread = threading.Thread(target=_run)
    thread.start()

    progress = st.progress(0, text="Transkribiere lokal … geschätzter Fortschritt")
    start = time.time()
    while thread.is_alive():
        frac = min((time.time() - start) / estimated_total_s, 0.9)
        progress.progress(frac, text=f"Transkribiere lokal … geschätzt {frac * 100:.0f}% (Schätzung kann abweichen)")
        time.sleep(0.5)
    thread.join()
    progress.progress(1.0, text="Transkription abgeschlossen")

    return result["transcript"]


def render_transcription_job(recording_path: str) -> dict | None:
    """P9 (docs/konzept_p9_hintergrundjob_lokal.md) -- ECHTER Hintergrund-Job statt
    `transcribe_with_progress()`s blockierender Thread-Schleife: Klick auf "Transkription
    starten" schreibt nur einen Job-Eintrag (`core/job_queue.py`) und die Skriptausfuehrung
    kehrt SOFORT zurueck -- die eigentliche Arbeit macht der getrennte `worker.py`-Prozess.
    Der Fortschritt wird ueber ein `st.fragment(run_every=...)` angezeigt, das NUR sich selbst
    periodisch neu rendert, nicht die ganze Seite -- man kann waehrenddessen problemlos zu
    einem anderen Modul wechseln und spaeter zurueckkommen (der Job-Zustand liegt auf Platte,
    ueberlebt also auch einen Reload, gleiches Prinzip wie `core/session_store.py`).

    Liefert das fertige Transkript (aus dem Cache) sobald verfuegbar, sonst None -- die
    aufrufende Seite prueft `if transcript:` genau wie vorher.
    """
    from core.job_queue import STATUS_DONE, STATUS_ERROR, get_job_status, submit_job
    from core.transcription import load_cached_transcript

    cached = load_cached_transcript(recording_path)
    if cached is not None:
        st.caption("Transkript aus dem Cache geladen.")
        return cached

    # Ein Job-Key pro Aufnahme (nicht pro Seite) -- verschiedene Takes/Module haben eigene,
    # unabhaengige Jobs, ein Seitenwechsel verliert den laufenden Job dadurch nicht.
    job_key = f"_transcription_job_{recording_path}"

    @st.fragment(run_every="1s")
    def _fragment():
        job_id = st.session_state.get(job_key)

        if job_id is None:
            if st.button(
                "Transkription starten (läuft jetzt im Hintergrund — die Seite bleibt "
                "bedienbar, du kannst auch zu einem anderen Modul wechseln)",
                icon=":material/graphic_eq:",
            ):
                st.session_state[job_key] = submit_job("transcription", {"audio_path": recording_path})
                st.rerun()
            return

        job = get_job_status(job_id)
        if job is None:
            st.error("Job nicht gefunden — bitte erneut starten.")
            del st.session_state[job_key]
            return

        if job["status"] == STATUS_DONE:
            st.success("Transkription abgeschlossen.")
            del st.session_state[job_key]
            st.rerun()
        elif job["status"] == STATUS_ERROR:
            st.error(f"Transkription fehlgeschlagen: {job.get('error_message', 'unbekannter Fehler')}")
            if st.button("Erneut versuchen", key=f"retry_{job_key}"):
                del st.session_state[job_key]
                st.rerun()
        else:
            st.progress(
                job.get("progress", 0) / 100,
                text=f"Transkribiere im Hintergrund … geschätzt {job.get('progress', 0)}% "
                     "(Schätzung kann abweichen)",
            )

    _fragment()
    return None
