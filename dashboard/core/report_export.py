"""On-demand Excel-/PDF-Report-Export im Gesamtbericht (P14, docs/backlog.md,
Nutzer-Feedback 2026-08-15). Erzeugt NUR auf Knopfdruck (views/gesamtbericht.py ruft
collect_report_data() und die build_*-Funktionen erst nach einem Button-Klick auf), nie
automatisch beim Laden der Seite.

WICHTIG: Beide Formate speisen sich AUSSCHLIESSLICH aus core.interpretation.flatten_take()/
build_rows() -- denselben Funktionen, die auch views/gesamtbericht.py fuer die Live-Ansicht
nutzt. Kein eigener, duplizierter Normbereichs-/Erklaerungstext. Aendert sich ein zones_func in
core/reference_ranges.py oder kommt ein neuer Parameter zu core.interpretation.PARAMETER_INFO
dazu, uebernehmen beide Reports das automatisch beim naechsten Erzeugen -- kein separater
Pflegeaufwand. Grund: beim EDF-Analyzer-Schwesterprojekt fanden sich veraltete, von der Live-App
abweichende statische Normbereiche in einem Report, der eigene Werte hartkodiert hatte (siehe
Memory [[project_edf_report_audit]]).

Nutzer-Feedback 2026-08-16: das Glossar (Erklaerungen/Literatur je Parameter, urspruenglich
Teil von P14/P15) wurde WIEDER ENTFERNT -- der Report soll nur die reinen Werte enthalten, die
Erklaerungen bleiben der Live-Ansicht (views/gesamtbericht.py) vorbehalten."""

from __future__ import annotations

import io
from datetime import datetime, timezone

import pandas as pd

from core.interpretation import build_rows, flatten_take
from core.recording_setup import describe_recording_setup
from core.versioning import FEATURE_SCHEMA_VERSION

DISCLAIMER = (
    "Diese Übersicht ist rein beschreibend. Ein \"auffälliger\" Wert bedeutet NICHT "
    "automatisch eine Erkrankung -- der Kontext-Kommentar zeigt nur, mit welchen Mustern eine "
    "Auffälligkeit in der Literatur assoziiert wird. Keine Diagnose, keine ärztliche "
    "Einschätzung ersetzt."
)


def collect_report_data(session_id: str) -> dict:
    """Sammelt EINMAL alle Report-Daten aus st.session_state -- Excel- und PDF-Export werden
    beide aus derselben Struktur gebaut, damit sie garantiert dieselben Werte zeigen.
    session_id kommt von core.session_store.get_session_id() -- die ist NICHT in
    st.session_state hinterlegt, sondern wird aus den URL-Query-Params gelesen."""
    import streamlit as st

    results = st.session_state.get("module_results", {})
    modules_out: dict[str, dict] = {}

    for module_name, subtasks in results.items():
        module_takes = {k: v for k, v in subtasks.items() if v}
        if not module_takes:
            continue
        module_out: dict = {}
        for subtask, takes in module_takes.items():
            selected = next((t for t in takes if t.get("selected")), takes[-1] if takes else None)
            if selected is None:
                continue
            flat = flatten_take(selected)
            rows = build_rows(flat)
            if not rows:
                continue
            module_out[subtask] = {
                "take_number": selected.get("take_number", "?"),
                "recorded_at": selected.get("recorded_at", "–"),
                # Aeltere Sitzungen (vor Einfuehrung der Analyse-Versionierung) haben das Feld
                # nicht -- leeres Dict statt KeyError, Report bleibt erzeugbar.
                "analysis_metadata": selected.get("analysis_metadata") or {},
                "recording_setup": selected.get("recording_setup") or {},
                "rows": rows,
            }
        if module_out:
            modules_out[module_name] = module_out

    # Dysarthrie-Marker (docs/konzept_wertung.md) -- gegen die juengste fruehere Sitzung
    # derselben Person. Ohne Voraufnahme bewusst KEIN Ersatzmassstab.
    from core.session_store import load_previous_session_values
    from core.wertung import dysarthrie_marker

    aktuelle_werte: dict = {}
    for subtasks in results.values():
        for takes in subtasks.values():
            gewaehlt = next((t for t in takes if t.get("selected")), takes[-1] if takes else None)
            if gewaehlt:
                for k, v in flatten_take(gewaehlt).items():
                    aktuelle_werte.setdefault(k, v)

    referenz = load_previous_session_values(st.session_state.get("subject_id"), session_id)
    marker = dysarthrie_marker(aktuelle_werte, referenz["werte"]) if referenz else None

    return {
        "dysarthrie_marker": marker,
        "marker_referenz": {"aufgenommen_am": referenz["aufgenommen_am"]} if referenz else None,
        "subject_id": st.session_state.get("subject_id"),
        "subject_age": st.session_state.get("subject_age"),
        "session_id": session_id,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "modules": modules_out,
    }


def build_excel_report(data: dict) -> bytes:
    """Baut die Excel-Arbeitsmappe (Übersicht/Werte) aus der gesammelten Report-Datenstruktur."""
    meta_rows = [
        {"Feld": "Proband:in", "Wert": data["subject_id"] or "–"},
        {"Feld": "Alter", "Wert": data["subject_age"] if data["subject_age"] is not None else "–"},
        {"Feld": "Sitzungs-ID", "Wert": data["session_id"] or "–"},
        {"Feld": "Erstellt am", "Wert": data["generated_at"]},
        {"Feld": "Analyse-Version (aktueller Code)", "Wert": FEATURE_SCHEMA_VERSION},
        {"Feld": "Hinweis", "Wert": DISCLAIMER},
    ]

    value_rows = []
    for module_name, subtasks in data["modules"].items():
        for subtask, info in subtasks.items():
            for row in info["rows"]:
                value_rows.append({
                    "Modul": module_name,
                    "Teilaufgabe": subtask,
                    "Versuch": info["take_number"],
                    "Aufgenommen": info["recorded_at"],
                    "Analyse-Version": info["analysis_metadata"].get("feature_schema_version", "–"),
                    "Analysiert am": info["analysis_metadata"].get("analysis_timestamp", "–"),
                    "Abtastrate (Hz)": info["analysis_metadata"].get("audio_sampling_rate_hz", "–"),
                    "Aufnahmebedingungen": describe_recording_setup(info["recording_setup"]),
                    **row,
                })

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(meta_rows).to_excel(writer, sheet_name="Übersicht", index=False)

        marker = data.get("dysarthrie_marker")
        referenz = data.get("marker_referenz")
        if marker and referenz:
            marker_rows = [{
                "Box": m["box"], "Marker": m["label"],
                "Ausprägung": m["stufe"] or "unauffällig",
                "Wert": round(m["wert"], 3), "Referenz": round(m["referenz"], 3),
                "Abstand": round(m["abstand"], 3), "Skala": m["skala"],
                "Vertrauen": m["vertrauen"],
            } for box in marker["boxen"] for m in box["marker"]]
        else:
            marker_rows = [{"Box": "–", "Marker": "keine Voraufnahme vorhanden",
                            "Ausprägung": "–", "Wert": None, "Referenz": None,
                            "Abstand": None, "Skala": "–", "Vertrauen": "–"}]
        pd.DataFrame(marker_rows).to_excel(writer, sheet_name="Dysarthrie-Marker", index=False)

        pd.DataFrame(value_rows).to_excel(writer, sheet_name="Werte", index=False)

        for sheet in writer.sheets.values():
            sheet.column_dimensions["A"].width = 28
            for col in "BCDEFG":
                sheet.column_dimensions[col].width = 40

    return buffer.getvalue()


def _pdf_safe(text) -> str:
    """fpdf2s Core-Fonts (Helvetica) koennen nur Latin-1 -- typografische Zeichen (Gedankenstrich,
    Anfuehrungszeichen aus PARAMETER_INFO) vorher auf ASCII-Aequivalente abbilden, statt fpdf2
    beim Rendern abstuerzen zu lassen oder Zeichen kommentarlos zu verlieren."""
    if text is None:
        return "–"
    text = str(text)
    replacements = {
        "—": "-", "–": "-", "„": '"', "“": '"', "‘": "'", "’": "'",
        "→": "->", "…": "...",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")


_BOX_LABEL_PDF = {"vokalisation": "Vokalisation (Stimmgebung)", "fliesssprache": "Fliessende Sprache"}

DYSARTHRIE_MARKER_HINWEIS = (
    "Dies sind Messbefunde, keine Diagnose. Gekennzeichnet wird, welche Kennwerte von der "
    "Referenz abweichen und wie stark - nicht, ob eine Dysarthrie vorliegt oder welcher Art. "
    "Grundlage sind drei echte Vergleichsfaelle; die Einstufungsgrenzen sind nachvollziehbar "
    "hergeleitet, aber nicht klinisch validiert. Ersetzt keine aerztliche Beurteilung."
)


def _pdf_dysarthrie_marker(pdf, data: dict) -> None:
    """Rendert den Dysarthrie-Marker-Block ins PDF (docs/konzept_wertung.md).

    Der Vorbehalt steht IM Block, nicht am Dokumentende -- sonst wird die Aussage
    herausgeloest zitiert und der Vorbehalt bleibt liegen."""
    marker, referenz = data.get("dysarthrie_marker"), data.get("marker_referenz")

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, _pdf_safe("Dysarthrie-Marker"), new_x="LMARGIN", new_y="NEXT")

    if not marker or not referenz:
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, _pdf_safe(
            "Keine Voraufnahme dieser Proband:in vorhanden - ohne Referenz aus derselben "
            "Aufnahmekette lassen sich die Marker nicht bestimmen. Absolute Literaturgrenzen "
            "werden bewusst nicht ersatzweise verwendet: sie erwiesen sich an echten "
            "Patient:innen als zu unempfindlich und loesten zugleich bei gesunden Aufnahmen "
            "Fehlalarm aus."), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        return

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(0, 5, _pdf_safe(
        f"Referenz: eigene Voraufnahme vom {referenz.get('aufgenommen_am', '-')}"),
        new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    pdf.set_font("Helvetica", "B", 10)
    if marker["marker_auffaellig"] == 0:
        pdf.cell(0, 6, _pdf_safe(
            f"Kein Marker auffaellig ({marker['marker_gesamt']} Kennwerte geprueft)."),
            new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 6, _pdf_safe(
            f"{marker['marker_auffaellig']} von {marker['marker_gesamt']} Markern auffaellig, "
            f"hoechste Auspraegung: {marker['hoechste_stufe']}."),
            new_x="LMARGIN", new_y="NEXT")

    for box in marker["boxen"]:
        auff = [m for m in box["marker"] if m["stufe"]]
        pdf.set_font("Helvetica", "B", 9)
        zeile = f"{_BOX_LABEL_PDF.get(box['box'], box['box'])}: "
        zeile += (f"{box['auffaellig']} von {box['geprueft']} Markern auffaellig"
                  if auff else f"unauffaellig ({box['geprueft']} geprueft)")
        if box["gleichsinnig"]:
            zeile += " - zusammengehoerige Marker weichen gemeinsam ab"
        pdf.cell(0, 5, _pdf_safe(zeile), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for m in auff:
            pdf.cell(0, 5, _pdf_safe(
                f"    - {m['label']}: {m['stufe']} ({m['wert']:.2f} vs. Referenz {m['referenz']:.2f})"),
                new_x="LMARGIN", new_y="NEXT")

    pdf.ln(1)
    pdf.set_fill_color(255, 244, 225)
    pdf.set_text_color(130, 80, 0)
    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 4, _pdf_safe(DYSARTHRIE_MARKER_HINWEIS), fill=True,
                   new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)


def build_pdf_report(data: dict) -> bytes:
    """Baut den PDF-Report (Titel/Metadaten/Disclaimer, dann je Modul/Teilaufgabe die
    Parameter/Wert/Normbereich/Status-Tabelle) aus der gesammelten Report-Datenstruktur."""
    from fpdf import FPDF

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _pdf_safe("NeuroVoice AI - Sprachbiomarker-Report"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(
        0, 6,
        _pdf_safe(
            f"Proband:in: {data['subject_id'] or '-'}  |  Alter: "
            f"{data['subject_age'] if data['subject_age'] is not None else '-'}  |  "
            f"Sitzung: {data['session_id'] or '-'}"
        ),
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.cell(0, 6, _pdf_safe(f"Erstellt: {data['generated_at']}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.set_fill_color(255, 244, 225)
    pdf.set_text_color(130, 80, 0)
    pdf.set_font("Helvetica", "B", 9)
    pdf.multi_cell(0, 5, _pdf_safe("Wichtig: " + DISCLAIMER), fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # Dysarthrie-Marker als Erstes -- das ist die Zusammenfassung, kein Anhang.
    _pdf_dysarthrie_marker(pdf, data)

    col_widths = [58, 28, 40, 30]
    headers = ["Parameter", "Wert", "Normbereich", "Status"]

    for module_name, subtasks in data["modules"].items():
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, _pdf_safe(module_name.capitalize()), new_x="LMARGIN", new_y="NEXT")

        for subtask, info in subtasks.items():
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(
                0, 6,
                _pdf_safe(f"{subtask} - Versuch {info['take_number']} ({info['recorded_at']})"),
                new_x="LMARGIN", new_y="NEXT",
            )

            meta = info["analysis_metadata"]
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(130, 130, 130)
            pdf.cell(
                0, 4,
                _pdf_safe(
                    f"Analyse-Version {meta.get('feature_schema_version', '-')}  |  "
                    f"Abtastrate {meta.get('audio_sampling_rate_hz', '-')} Hz  |  "
                    f"{describe_recording_setup(info['recording_setup'])}"
                ),
                new_x="LMARGIN", new_y="NEXT",
            )
            pdf.set_text_color(0, 0, 0)

            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(235, 235, 235)
            for width, header in zip(col_widths, headers):
                pdf.cell(width, 6, _pdf_safe(header), border=1, fill=True)
            pdf.ln()

            pdf.set_font("Helvetica", "", 8)
            for row in info["rows"]:
                pdf.cell(col_widths[0], 6, _pdf_safe(row["Parameter"]), border=1)
                pdf.cell(col_widths[1], 6, _pdf_safe(row["Wert"]), border=1)
                pdf.cell(col_widths[2], 6, _pdf_safe(row["Normbereich"]), border=1)
                pdf.cell(col_widths[3], 6, _pdf_safe(row["Status"]), border=1)
                pdf.ln()
            pdf.ln(3)

    return bytes(pdf.output())
