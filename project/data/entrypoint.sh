#!/bin/bash
set -euo pipefail

export PYTHONUNBUFFERED=1

# Paths
PROJECT_DIR="/workspace/project"
OUTDIR="$PROJECT_DIR/outputs"

mkdir -p "$OUTDIR"

# Install runtime deps (if not already)
pip install pandas openpyxl country_converter unidecode

# Run pipeline
python /workspace/project/src/main.py

echo "Outputs written to $OUTDIR:"
ls -l "$OUTDIR"
