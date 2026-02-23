import os
from typing import Dict, Tuple

import pandas as pd
import numpy as np

from utils import standardize_country_column, coerce_year_column, long_from_wide_indicator

FILES_DIR = "/workspace/files"


def read_spar() -> pd.DataFrame:
    # A_e-SPAR.xlsx like structure resides in 6d1cd8c3c3b54015a3ebf7d77b7e8941.xlsx
    xls_path = os.path.join(FILES_DIR, "6d1cd8c3c3b54015a3ebf7d77b7e8941.xlsx")
    df = pd.read_excel(xls_path)
    # Detect total score column
    total_col = None
    for c in df.columns:
        if str(c).lower().strip() in ["promedio total", "total score", "spar_total", "overall score", "promedio total "]:
            total_col = c
            break
    if total_col is None:
        # fallback: look for a column that is numeric and resembles average
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if len(num_cols) > 0:
            total_col = num_cols[0]
    df = df.rename(columns={total_col: 'SPAR_total'})
    df = df.rename(columns={"ISO Code": "iso3", "Estado Parte de IHR": "country"})
    # Provide year if present; SPAR often by year
    if 'Datos recividos' in df.columns:
        df = df.rename(columns={'Datos recividos': 'year'})
    if 'year' not in df.columns:
        df['year'] = np.nan
    df = df[['country', 'iso3', 'year', 'SPAR_total']]
    df = coerce_year_column(df, year_col_candidates=['year'])
    return df


def read_che_gdp() -> pd.DataFrame:
    csv_path = os.path.join(FILES_DIR, "4b09fbba02e247b7a1497204a0c24cf3.csv")
    df = pd.read_csv(csv_path)
    # filter indicator
    ind_mask = df['Indicator'].str.contains('Current health expenditure', case=False, na=False)
    df = df.loc[ind_mask].copy()
    id_cols = ['Country', 'Indicator']
    m = long_from_wide_indicator(df, id_cols=id_cols)
    m = m.rename(columns={'Country': 'country', 'value': 'CHE_GDP'})
    return m[['country', 'year', 'CHE_GDP']]


def read_uhc() -> pd.DataFrame:
    # UHC index is in 00cf6dbc70fd4017a7987b365d4abba2.csv (tidy format)
    csv_path = os.path.join(FILES_DIR, "00cf6dbc70fd4017a7987b365d4abba2.csv")
    # Some rows may include non-UTF8 bytes; read with latin1 fallback
    df = pd.read_csv(csv_path, encoding='latin1')
    df = df[df['IND_PER_CODE'].str.contains('UHC_INDEX', na=False)].copy()
    df = df.rename(columns={'GEO_NAME_SHORT': 'country', 'DIM_TIME': 'year', 'INDEX_N': 'UHC_index'})
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['UHC_index'] = pd.to_numeric(df['UHC_index'], errors='coerce')
    return df[['country', 'year', 'UHC_index']]


def read_policy_plan_strategy() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    policy_path = os.path.join(FILES_DIR, "8e043d9282aa4e9eb2a6d3cde6f6884e.csv")
    # Plan file may not be available or may be embedded in another dataset; attempt to read if exists
    plan_path = os.path.join(FILES_DIR, "c4da32f6d88f4fc9a1556831f24b3b1c.csv")
    strategy_path = os.path.join(FILES_DIR, "fc9853b355d642cbbf5ed3f52acafd5d.csv")

    def read_discrete(fp: str, varname: str) -> pd.DataFrame:
        if not os.path.exists(fp):
            return pd.DataFrame(columns=['country','year',varname])
        try:
            d = pd.read_csv(fp)
        except Exception:
            # If CSV is a container (e.g., zip/Numbers), return empty
            return pd.DataFrame(columns=['country','year',varname])
        id_cols = ['Country', 'Indicator'] if 'Indicator' in d.columns else ['Country']
        m = long_from_wide_indicator(d, id_cols=id_cols)
        m = m.rename(columns={'Country': 'country', 'value': varname})
        return m[['country', 'year', varname]]

    policy = read_discrete(policy_path, 'Policy_UHC')
    plan = read_discrete(plan_path, 'Plan_UHC')
    strategy = read_discrete(strategy_path, 'Strategy_UHC')
    return policy, plan, strategy


def read_right_to_health() -> pd.DataFrame:
    # Recognition file path may be an Apple Numbers container; handle gracefully
    csv_path = os.path.join(FILES_DIR, "5709f9c0c9924954a8265dee0251b1c1.csv")
    if not os.path.exists(csv_path):
        return pd.DataFrame(columns=['country','year','Right_to_health'])
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return pd.DataFrame(columns=['country','year','Right_to_health'])
    # Assume columns Country, Year, value; otherwise pivot
    if 'Indicator' in df.columns:
        ind_mask = df['Indicator'].str.contains('recognition', case=False, na=False)
        if ind_mask.any():
            df = df.loc[ind_mask]
    if 'Year' in df.columns and 'Value' in df.columns:
        df = df.rename(columns={'Country': 'country', 'Year': 'year', 'Value': 'Right_to_health'})
        return df[['country', 'year', 'Right_to_health']]
    # Otherwise try melt
    id_cols = ['Country', 'Indicator'] if 'Indicator' in df.columns else ['Country']
    m = long_from_wide_indicator(df, id_cols=id_cols)
    m = m.rename(columns={'Country': 'country', 'value': 'Right_to_health'})
    return m[['country', 'year', 'Right_to_health']]


def read_exclusions() -> pd.DataFrame:
    # C_Exclusiones.xlsx mapped to 620a7cada3584b62b348fa698de4f28e.xlsx
    xls_path = os.path.join(FILES_DIR, "620a7cada3584b62b348fa698de4f28e.xlsx")
    df = pd.read_excel(xls_path)
    df = df.rename(columns={'Año': 'year', 'País': 'country'})
    df['art7_excluded'] = 1
    return df[['country', 'year', 'art7_excluded']]


def read_participation_raw() -> pd.DataFrame:
    # C_Particip.xlsx is likely 00e422b990fa433395247ed6b6578aae.xlsx
    xls_path = os.path.join(FILES_DIR, "00e422b990fa433395247ed6b6578aae.xlsx")
    df = pd.read_excel(xls_path)
    # Harmonize potential column names
    if 'País' in df.columns:
        df = df.rename(columns={'País': 'country'})
    if 'Año' in df.columns:
        df = df.rename(columns={'Año': 'year'})
    return df


def load_all() -> Dict[str, pd.DataFrame]:
    return {
        'spar': read_spar(),
        'che_gdp': read_che_gdp(),
        'uhc': read_uhc(),
        'policy_plan_strategy': read_policy_plan_strategy(),
        'right_to_health': read_right_to_health(),
        'exclusions': read_exclusions(),
        'participation_raw': read_participation_raw(),
    }
