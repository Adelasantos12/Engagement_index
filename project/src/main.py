import os
import pandas as pd

from module_build import build_panel
from module_index import compute_subindices, compute_index, apply_penalty, sensitivity_table

OUTDIR = "/workspace/project/outputs"

def run_pipeline():
    os.makedirs(OUTDIR, exist_ok=True)
    panel = build_panel()
    sub = compute_subindices(panel)
    idx = compute_index(panel, sub)
    pen = apply_penalty(idx)
    sens = sensitivity_table(idx)

    panel.to_csv(os.path.join(OUTDIR, 'panel_clean.csv'), index=False)
    sub.to_csv(os.path.join(OUTDIR, 'subindices.csv'), index=False)
    idx[['country','year','IECGGS_raw']].to_csv(os.path.join(OUTDIR, 'IECGGS_raw.csv'), index=False)
    pen.to_csv(os.path.join(OUTDIR, 'IECGGS_penalized.csv'), index=False)
    sens.to_csv(os.path.join(OUTDIR, 'sensitivity.csv'), index=False)

    # Data dictionary minimal
    with open(os.path.join(OUTDIR, 'data_dictionary.md'), 'w') as f:
        f.write("Variables:\n")
        f.write("- SPAR_total: puntaje RSI (0-100)\n")
        f.write("- CHE_GDP: gasto corriente en salud / PIB\n")
        f.write("- UHC_index: índice de cobertura de servicios UHC (0-100)\n")
        f.write("- Policy_UHC / Plan_UHC / Strategy_UHC: 0/0.5/1 (No/Parcial/Sí)\n")
        f.write("- Right_to_health: reconocimiento derecho a la salud\n")
        f.write("- participation_event / leadership_event / decision_event: recuentos país-año\n")
        f.write("- E_reg / E_dom / E_part: subíndices en 0-1\n")
        f.write("- IECGGS_raw: índice base (0-1)\n")
        f.write("- art7_excluded: 0/1 (exclusión Art.7)\n")
        f.write("- IECGGS_adj_lambda_{x}: índice penalizado con λ=x\n")

if __name__ == '__main__':
    run_pipeline()
