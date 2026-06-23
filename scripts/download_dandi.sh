#!/usr/bin/env bash
# Download an OpenScope dandiset (default: 000253, the Global/Local Oddball set).
#
#   bash scripts/download_dandi.sh                 # lists assets only (safe, no big download)
#   bash scripts/download_dandi.sh 000253 --full   # full set — ~680 GB, make sure you have disk
#
# The full 000253 is ~680 GB (633 GiB) across 98 NWB files. Prefer streaming
# (scripts/stream_first_nwb.py) or pulling a SINGLE asset for a first look.
set -euo pipefail

DANDISET="${1:-000253}"
MODE="${2:-list}"
DEST="${DANDI_DEST:-$HOME/data/openscope}"

command -v dandi >/dev/null 2>&1 || { echo "dandi-cli not found. pip install dandi"; exit 1; }

echo "Dandiset: $DANDISET   →   $DEST"
mkdir -p "$DEST"

if [[ "$MODE" == "--full" ]]; then
    echo "Downloading the FULL dandiset (~680 GB for 000253). Ctrl-C to abort..."
    cd "$DEST"
    dandi download "DANDI:${DANDISET}"
elif [[ "$MODE" == "--asset" ]]; then
    # Pull one asset:  bash scripts/download_dandi.sh 000253 --asset <asset/path.nwb>
    ASSET="${3:?Pass an asset path as the 3rd argument (see the list output)}"
    cd "$DEST"
    dandi download "DANDI:${DANDISET}/${ASSET}"
else
    echo "Listing assets (no download). Re-run with --full or --asset <path> to fetch."
    dandi ls "https://api.dandiarchive.org/api/dandisets/${DANDISET}/versions/draft/assets/?path=" 2>/dev/null \
        || dandi ls "DANDI:${DANDISET}"
fi
