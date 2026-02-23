#!/bin/bash
set -euo pipefail

export PYTHONUNBUFFERED=1

# Paths
PROJECT_DIR="/workspace/project"
OUTDIR="$PROJECT_DIR/outputs"
PYTHON_BIN="${PYTHON_BIN:-python3}"
LOCAL_WHEELHOUSE="${LOCAL_WHEELHOUSE:-/workspace/wheels}"

mkdir -p "$OUTDIR"

check_deps() {
  "$PYTHON_BIN" - <<'PY'
import importlib.util, sys
required = ["pandas", "openpyxl", "country_converter", "unidecode"]
missing = [m for m in required if importlib.util.find_spec(m) is None]
if missing:
    print("MISSING:" + ",".join(missing))
    sys.exit(1)
print("OK")
PY
}

if ! check_deps >/tmp/iecg_deps_check.log 2>&1; then
  echo "Dependencies not available in current Python:"
  cat /tmp/iecg_deps_check.log || true

  # Offline-first install strategy: install only from local wheelhouse when present.
  if [ -d "$LOCAL_WHEELHOUSE" ]; then
    echo "Attempting offline install from wheelhouse: $LOCAL_WHEELHOUSE"
    "$PYTHON_BIN" -m pip install --no-index --find-links "$LOCAL_WHEELHOUSE" pandas openpyxl country_converter unidecode || true
  fi

  # Optional online fallback only when explicitly enabled.
  if ! check_deps >/tmp/iecg_deps_check_after.log 2>&1; then
    if [ "${ALLOW_ONLINE_INSTALL:-0}" = "1" ]; then
      echo "Attempting online pip install (ALLOW_ONLINE_INSTALL=1)"
      "$PYTHON_BIN" -m pip install pandas openpyxl country_converter unidecode || true
    fi
  fi

  if ! check_deps >/tmp/iecg_deps_final.log 2>&1; then
    echo "ERROR: Missing runtime dependencies and unable to install them in this environment."
    cat /tmp/iecg_deps_final.log || true
    echo "Hints:"
    echo "  1) Provide an offline wheelhouse at $LOCAL_WHEELHOUSE"
    echo "  2) Or preinstall deps in the selected Python ($PYTHON_BIN)"
    echo "  3) Or set ALLOW_ONLINE_INSTALL=1 in environments with internet/proxy access"
    exit 1
  fi
fi

# Run pipeline
"$PYTHON_BIN" /workspace/project/src/main.py

echo "Outputs written to $OUTDIR:"
ls -l "$OUTDIR"
