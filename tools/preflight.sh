#!/usr/bin/env bash
# Bildet den CI-Lauf aus .github/workflows/test.yml lokal nach -- vor jedem Push von Hand
# ausfuehren:
#
#     bash tools/preflight.sh
#
# Vorbild ist das Schwesterprojekt EDF-Analyzer, wo dieselbe Datei existiert. Anlass dort:
# vier rote Pushes in Folge, weil eine Pruefung nur in der CI lief und nie lokal. Diese Datei
# schliesst genau diese Luecke, statt sich darauf zu verlassen, in der naechsten Sitzung wieder
# daran zu denken.
#
# Bei jeder neuen Pruefzeile in der Workflow-Datei auch hier ergaenzen -- sonst oeffnet sich
# dieselbe Luecke an anderer Stelle wieder.
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
if [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
fi

echo "== Python =="
"$PY" --version

echo
echo "== Testsuite (Ground Truth, bekannte Schwaechen, Parameter-Registry) =="
"$PY" -m pytest tests/ -q

echo
echo "Preflight gruen."
