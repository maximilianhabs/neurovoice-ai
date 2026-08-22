"""Struktur der Parameter-Registry und der drei Anzeige-Pfade.

`core/interpretation.py::PARAMETER_INFO` ist die einzige Quelle fuer Label, Erklaerung,
Normbereich, Evidenz-Einordnung und Literatur -- Kachel, Tabelle, Glossar und der PDF-/
Excel-Export speisen sich alle daraus. Ein unvollstaendiger oder inkonsistenter Eintrag wirkt
sich damit sofort an mehreren Stellen aus, faellt aber beim Durchklicken leicht nicht auf.

Diese Tests brauchen weder Audio noch Streamlit und laufen in Millisekunden.
"""

import pytest

from core.interpretation import (
    PARAMETER_INFO,
    build_glossary_entries,
    build_rows,
    build_tiles,
    interpret,
)

PFLICHTFELDER = ("label", "unit", "description", "zones_func", "context",
                 "age_caveat", "evidence", "literature")

# Bewusst geschlossene Liste: eine neue Stufe soll eine bewusste Entscheidung sein, kein
# Tippfehler, der still eine vierte Kategorie einfuehrt (die Glossar-Einfaerbung in
# core/shared.py::_EVIDENCE_COLORS kennt nur diese Werte).
ERLAUBTE_EVIDENZ = {
    "gut etabliert",
    "in der Forschung diskutiert",
    "eigene Heuristik / explorativ",
    "deskriptiv, kein Krankheits-Marker",
}

PAUSENMASSE = {"fluency_score", "pause_count", "micro_pause_count", "macro_pause_count",
               "mean_pause_duration_s", "max_pause_duration_s",
               "mean_micro_pause_duration_s", "mean_macro_pause_duration_s"}


@pytest.mark.parametrize("key", sorted(PARAMETER_INFO))
def test_jeder_parameter_ist_vollstaendig(key):
    fehlend = [f for f in PFLICHTFELDER if f not in PARAMETER_INFO[key]]
    assert not fehlend, f"{key} fehlen: {fehlend}"


@pytest.mark.parametrize("key", sorted(PARAMETER_INFO))
def test_evidenzstufe_ist_eine_der_vereinbarten(key):
    assert PARAMETER_INFO[key]["evidence"] in ERLAUBTE_EVIDENZ


@pytest.mark.parametrize("key", sorted(PARAMETER_INFO))
def test_ohne_zonen_wird_kein_normbereich_behauptet(key):
    """Projektprinzip: keine erfundenen Normbereiche. Wo keine Zonenfunktion hinterlegt ist,
    muss die Anzeige das auch sagen statt eine Grenze zu suggerieren."""
    if PARAMETER_INFO[key]["zones_func"] is None:
        assert interpret(key, 1.0)["range"] == "kein etablierter Normbereich"


def test_aktuell_traegt_kein_parameter_eine_warnung():
    """Die Pausenmasse trugen die Kennzeichnung vom 2026-08-20 bis 2026-08-21 (RANDNOTIZ-17);
    seit die Erkennung am Signal arbeitet, ist der Grund entfallen. Schlaegt dieser Test fehl,
    wurde irgendwo eine Kennzeichnung gesetzt -- dann gehoert sie hier eingetragen, damit sie
    nicht unbemerkt wieder verschwindet."""
    markiert = {k for k, v in PARAMETER_INFO.items() if v.get("validation_warning")}
    assert markiert == set()


def test_kennzeichnung_erreicht_alle_drei_anzeigepfade():
    """Der Mechanismus muss funktionsfaehig bleiben, auch wenn ihn gerade kein Parameter nutzt --
    sonst faellt beim naechsten Bedarf erst auf, dass er unterwegs kaputtgegangen ist.

    Kachel, Tabelle und Glossar werden getrennt gebaut; eine Markierung, die nur an einer Stelle
    ankommt, ist keine. Geprueft an einem kuenstlich markierten Eintrag."""
    import copy
    from core import interpretation

    original = interpretation.PARAMETER_INFO["fluency_score"]
    interpretation.PARAMETER_INFO["fluency_score"] = {**copy.deepcopy(original),
                                                     "validation_warning": "Testwarnung"}
    try:
        flat = {"fluency_score": 1.0, "jitter_local_pct": 0.41}
        zeile = {r["Parameter"]: r["Status"] for r in build_rows(flat)}
        kachel = {t["label"]: (t["sub_text"], t["zone"]) for t in build_tiles(flat)}
        glossar = {e["label"]: e.get("validation_warning") for e in build_glossary_entries(flat)}

        fl = original["label"]
        ji = PARAMETER_INFO["jitter_local_pct"]["label"]

        assert zeile[fl] == "nicht validiert"
        assert kachel[fl] == ("nicht validiert", "warning")
        assert glossar[fl] == "Testwarnung"

        # Gegenprobe: ein unmarkiertes Mass darf NICHT mitgezogen werden
        assert zeile[ji] != "nicht validiert"
        assert kachel[ji][1] != "warning"
        assert glossar[ji] is None
    finally:
        interpretation.PARAMETER_INFO["fluency_score"] = original


def test_unbekannter_parameter_liefert_none_statt_abzustuerzen():
    assert interpret("gibt_es_nicht", 1.0) is None


def test_leeres_ergebnis_erzeugt_leere_ansichten():
    assert build_rows({}) == []
    assert build_tiles({}) == []
    assert build_glossary_entries({}) == []
