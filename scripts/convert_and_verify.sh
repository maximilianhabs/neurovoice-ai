#!/usr/bin/env bash
# Konvertiert alle .m4a (ALAC) aus dem Syncthing-Inbox-Ordner verlustfrei zu WAV
# nach data/raw/<patient_id>/ und verifiziert Codec/Samplerate/Bittiefe + Checksumme.
#
# Laeuft auf dem Homeserver gegen ~/neurovoice-data (Syncthing-Zielordner),
# ueberschreibbar via Umgebungsvariablen NEUROVOICE_INBOX / NEUROVOICE_DATA.
#
# Erwartetes Voice-Memo-Titelschema (vor der Aufnahme im iPhone so benennen):
#   <patient_id>_task-<typ>_take<n>
# Beispiel: selbst_task-vokal_take1.m4a
#
# ALAC ist ein verlustfreier *komprimierter* Codec; WAV kann keine Kompression enthalten.
# ffmpeg dekodiert ALAC -> PCM, das ist verlustfrei (keine Informationsentfernung),
# aber technisch ein Dekodierschritt, kein reiner Container-Kopiervorgang.

set -euo pipefail

INBOX="${NEUROVOICE_INBOX:-$HOME/neurovoice-data/raw-inbox}"
OUTBASE="${NEUROVOICE_DATA:-$HOME/neurovoice-data/raw}"

sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

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

  src_hash=$(sha256 "$f")

  ffmpeg -y -loglevel error -i "$f" -c:a pcm_s24le "$out"

  echo "--- $f -> $out"
  echo "Quell-SHA256: $src_hash"
  ffprobe -v error -select_streams a:0 \
    -show_entries stream=codec_name,sample_rate,bits_per_raw_sample \
    -of default=noprint_wrappers=1 "$out"
done
