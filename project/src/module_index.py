import os
import pandas as pd
import numpy as np

from utils import minmax_scale, winsorize_series


MIN_REG_OBS = int(os.getenv('IECGGS_MIN_REG_OBS', '1'))
MIN_DOM_OBS = int(os.getenv('IECGGS_MIN_DOM_OBS', '3'))
MIN_PART_OBS = int(os.getenv('IECGGS_MIN_PART_OBS', '2'))
MIN_INDEX_PILLARS = int(os.getenv('IECGGS_MIN_INDEX_PILLARS', '3'))


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

    # Eligibility counters
    reg_components = ['SPAR_n']
    # Plan_UHC excluded due to extreme missingness; keep domestic pillar on robust components
    dom_components = ['CHE_GDP_n', 'UHC_n', 'Policy_UHC', 'Right_n']
    part_components = ['participation_event_n', 'leadership_event_n', 'decision_event_n']

    df['n_reg_obs'] = df[reg_components].notna().sum(axis=1)
    df['n_dom_obs'] = df[dom_components].notna().sum(axis=1)
    df['n_part_obs'] = df[part_components].notna().sum(axis=1)

    df['flag_pillar_reg_ok'] = df['n_reg_obs'] >= MIN_REG_OBS
    df['flag_pillar_dom_ok'] = df['n_dom_obs'] >= MIN_DOM_OBS
    df['flag_pillar_part_ok'] = df['n_part_obs'] >= MIN_PART_OBS

    # Subindices with explicit eligibility
    df['E_reg'] = np.where(df['flag_pillar_reg_ok'], df[reg_components].mean(axis=1), np.nan)
    df['E_dom'] = np.where(df['flag_pillar_dom_ok'], df[dom_components].mean(axis=1), np.nan)
    df['E_part'] = np.where(df['flag_pillar_part_ok'], df[part_components].mean(axis=1), np.nan)

    sub_cols = [
        'country', 'year',
        'E_reg', 'E_dom', 'E_part',
        'n_reg_obs', 'n_dom_obs', 'n_part_obs',
        'flag_pillar_reg_ok', 'flag_pillar_dom_ok', 'flag_pillar_part_ok',
    ]
    sub = df[sub_cols].copy()
    return sub


def compute_index(panel: pd.DataFrame, sub: pd.DataFrame) -> pd.DataFrame:
    df = panel.merge(sub, on=['country', 'year'], how='left')
    df['n_pillars_ok'] = df[['flag_pillar_reg_ok', 'flag_pillar_dom_ok', 'flag_pillar_part_ok']].sum(axis=1)
    df['flag_iecgss_ok'] = df['n_pillars_ok'] >= MIN_INDEX_PILLARS
    df['IECGGS_raw'] = np.where(df['flag_iecgss_ok'], df[['E_reg', 'E_dom', 'E_part']].mean(axis=1), np.nan)
    return df[[
        'country', 'year', 'IECGGS_raw', 'E_reg', 'E_dom', 'E_part', 'art7_excluded',
        'n_reg_obs', 'n_dom_obs', 'n_part_obs', 'n_pillars_ok',
        'flag_pillar_reg_ok', 'flag_pillar_dom_ok', 'flag_pillar_part_ok', 'flag_iecgss_ok'
    ]]


def apply_penalty(index_df: pd.DataFrame, lambdas=(0.1, 0.25, 0.5)) -> pd.DataFrame:
    out = index_df.copy()
    out['art7_excluded'] = out['art7_excluded'].fillna(0)
    for lam in lambdas:
        out[f'IECGGS_adj_lambda_{lam}'] = out['IECGGS_raw'] * (1 - lam * out['art7_excluded'])
    return out


def sensitivity_table(index_df: pd.DataFrame, lambdas=(0.1, 0.25, 0.5), weight_schemes=None) -> pd.DataFrame:
    if weight_schemes is None:
        weight_schemes = {
            'equal': (1 / 3, 1 / 3, 1 / 3),
            'reg_heavy': (0.5, 0.25, 0.25),
            'dom_heavy': (0.25, 0.5, 0.25),
            'part_heavy': (0.25, 0.25, 0.5),
        }
    rows = []
    for lam in lambdas:
        for scheme_name, (wr, wd, wp) in weight_schemes.items():
            base = index_df.copy()
            base['IECGGS_weighted'] = wr * base['E_reg'] + wd * base['E_dom'] + wp * base['E_part']
            base['IECGGS_adj'] = base['IECGGS_weighted'] * (1 - lam * base['art7_excluded'].fillna(0))
            rows.append({
                'lambda': lam,
                'scheme': scheme_name,
                'mean_IECGGS_adj': base['IECGGS_adj'].mean(skipna=True),
                'std_IECGGS_adj': base['IECGGS_adj'].std(skipna=True),
            })
    return pd.DataFrame(rows)
