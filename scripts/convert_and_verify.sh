#!/usr/bin/env bash
# Konvertiert alle .m4a (ALAC) aus raw-inbox/ verlustfrei zu WAV in data/raw/<patient_id>/
# und verifiziert Codec/Samplerate/Bittiefe + Checksumme.
#
# Erwartetes Voice-Memo-Titelschema (vor der Aufnahme im iPhone so benennen):
#   <patient_id>_task-<typ>_take<n>
# Beispiel: selbst_task-vokal_take1.m4a
#
# ALAC ist ein verlustfreier *komprimierter* Codec; WAV kann keine Kompression enthalten.
# ffmpeg dekodiert ALAC -> PCM, das ist verlustfrei (keine Informationsentfernung),
# aber technisch ein Dekodierschritt, kein reiner Container-Kopiervorgang.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INBOX="$SCRIPT_DIR/../raw-inbox"
OUTBASE="$SCRIPT_DIR/../data/raw"

shopt -s nullglob
for f in "$INBOX"/*.m4a; do
  base=$(basename "$f" .m4a)

  patient_id=$(echo "$base" | sed -E 's/_task-.*//')
  if [ -z "$patient_id" ] || [ "$patient_id" = "$base" ]; then
    echo "WARNUNG: Dateiname '$base' passt nicht ins Schema <patient_id>_task-<typ>_take<n> - übersprungen." >&2
    continue
  fi

  outdir="$OUTBASE/$patient_id"
  mkdir -p "$outdir"

  timestamp=$(date -r "$f" +%Y-%m-%d_%H%M)
  out="$outdir/${timestamp}_${base#*_}.wav"

  src_hash=$(shasum -a 256 "$f" | awk '{print $1}')

  ffmpeg -y -loglevel error -i "$f" -c:a pcm_s24le "$out"

  echo "--- $f -> $out"
  echo "Quell-SHA256: $src_hash"
  ffprobe -v error -select_streams a:0 \
    -show_entries stream=codec_name,sample_rate,bits_per_raw_sample \
    -of default=noprint_wrappers=1 "$out"
done
