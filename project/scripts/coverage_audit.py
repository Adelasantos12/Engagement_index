#!/usr/bin/env python3
from pathlib import Path
import sys
import pandas as pd

# Local import path for project/src
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from module_coverage import build_coverage_reports


def main():
    outdir = ROOT / 'outputs'
    panel_path = outdir / 'panel_clean.csv'
    if not panel_path.exists():
        raise FileNotFoundError(f'Panel not found: {panel_path}. Run pipeline first.')

    panel = pd.read_csv(panel_path)
    build_coverage_reports(panel, outdir)
    print(f'Coverage reports written to {outdir}')


if __name__ == '__main__':
    main()
