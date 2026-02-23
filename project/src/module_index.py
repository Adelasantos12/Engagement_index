import pandas as pd
import numpy as np

from utils import minmax_scale, winsorize_series


def compute_subindices(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy()
    # Normalizations
    # CHE_GDP winsorize
    if 'CHE_GDP' in df.columns:
        df['CHE_GDP_w'] = winsorize_series(df['CHE_GDP'])
        df['CHE_GDP_n'] = minmax_scale(df['CHE_GDP_w'])
    else:
        df['CHE_GDP_n'] = np.nan
    # UHC and SPAR already normalized (0-100); bring to 0-1
    df['UHC_n'] = df['UHC_index'] / 100.0 if 'UHC_index' in df.columns else np.nan
    df['SPAR_n'] = df['SPAR_total'] / 100.0 if 'SPAR_total' in df.columns else np.nan

    # Discrete variables already mapped to 0-1 in build_panel
    # Right_to_health assumed in 0-100 if provided -> normalize
    if 'Right_to_health' in df.columns:
        # detect likely scale
        if df['Right_to_health'].max(skipna=True) > 1.0:
            df['Right_n'] = df['Right_to_health'] / 100.0
        else:
            df['Right_n'] = df['Right_to_health']
    else:
        df['Right_n'] = np.nan

    # Participation counts: normalize across all countries-years using min-max
    for col in ['participation_event', 'leadership_event', 'decision_event']:
        if col in df.columns:
            df[f'{col}_n'] = minmax_scale(df[col])
        else:
            df[f'{col}_n'] = np.nan

    # Subindices
    df['E_reg'] = df[['SPAR_n']].mean(axis=1)
    df['E_dom'] = df[['CHE_GDP_n', 'UHC_n', 'Policy_UHC', 'Plan_UHC', 'Right_n']].mean(axis=1)
    df['E_part'] = df[['participation_event_n', 'leadership_event_n', 'decision_event_n']].mean(axis=1)

    sub = df[['country','year','E_reg','E_dom','E_part']].copy()
    return sub


def compute_index(panel: pd.DataFrame, sub: pd.DataFrame) -> pd.DataFrame:
    df = panel.merge(sub, on=['country','year'], how='left')
    df['IECGGS_raw'] = df[['E_reg','E_dom','E_part']].mean(axis=1)
    return df[['country','year','IECGGS_raw','E_reg','E_dom','E_part','art7_excluded']]


def apply_penalty(index_df: pd.DataFrame, lambdas=(0.1, 0.25, 0.5)) -> pd.DataFrame:
    out = index_df.copy()
    out['art7_excluded'] = out['art7_excluded'].fillna(0)
    for lam in lambdas:
        out[f'IECGGS_adj_lambda_{lam}'] = out['IECGGS_raw'] * (1 - lam * out['art7_excluded'])
    return out


def sensitivity_table(index_df: pd.DataFrame, lambdas=(0.1,0.25,0.5), weight_schemes=None) -> pd.DataFrame:
    if weight_schemes is None:
        weight_schemes = {
            'equal': (1/3, 1/3, 1/3),
            'reg_heavy': (0.5, 0.25, 0.25),
            'dom_heavy': (0.25, 0.5, 0.25),
            'part_heavy': (0.25, 0.25, 0.5),
        }
    rows = []
    for lam in lambdas:
        for scheme_name, (wr, wd, wp) in weight_schemes.items():
            base = index_df.copy()
            base['IECGGS_weighted'] = wr*base['E_reg'] + wd*base['E_dom'] + wp*base['E_part']
            base['IECGGS_adj'] = base['IECGGS_weighted'] * (1 - lam * base['art7_excluded'].fillna(0))
            rows.append({
                'lambda': lam,
                'scheme': scheme_name,
                'mean_IECGGS_adj': base['IECGGS_adj'].mean(skipna=True),
                'std_IECGGS_adj': base['IECGGS_adj'].std(skipna=True),
            })
    return pd.DataFrame(rows)
