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
                "rows": rows,
            }
        if module_out:
            modules_out[module_name] = module_out

    return {
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
                    **row,
                })

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(meta_rows).to_excel(writer, sheet_name="Übersicht", index=False)
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
