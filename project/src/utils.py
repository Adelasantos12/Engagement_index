import re
from typing import Optional

import pandas as pd
import numpy as np
from unidecode import unidecode

try:
    import country_converter as coco
    _coco = coco.CountryConverter()
except Exception:  # fallback if not available
    _coco = None


def clean_country_name(name: str) -> str:
    if pd.isna(name):
        return name
    s = str(name).strip()
    s = unidecode(s)
    # common fixes
    s = s.replace('Rep. ', 'Republic ').replace('Dem. ', 'Democratic ')
    s = re.sub(r"\s+", " ", s)
    return s


def to_iso3(name: str) -> Optional[str]:
    if name is None or (isinstance(name, float) and np.isnan(name)):
        return None
    s = clean_country_name(name)
    if _coco is None:
        return None
    try:
        code = _coco.convert(names=s, to='ISO3')
        if code in (None, 'not found'):
            return None
        return code
    except Exception:
        return None


def standardize_country_column(df: pd.DataFrame, country_col_candidates=None) -> pd.DataFrame:
    if country_col_candidates is None:
        country_col_candidates = ['country', 'Country', 'Pais', 'País', 'País', 'Estado Parte de IHR', 'Member State', 'País/territorio']
    country_col = None
    for c in df.columns:
        if c in country_col_candidates:
            country_col = c
            break
    if country_col is None:
        # try heuristic: column with many string country-like values
        for c in df.columns:
            if df[c].dtype == object and df[c].astype(str).str.len().mean() > 4:
                country_col = c
                break
    if country_col is None:
        raise ValueError('No country column found in dataframe')

    df = df.copy()
    df['country'] = df[country_col].apply(clean_country_name)
    df['iso3'] = df['country'].apply(to_iso3)
    return df


def coerce_year_column(df: pd.DataFrame, year_col_candidates=None) -> pd.DataFrame:
    if year_col_candidates is None:
        year_col_candidates = ['year', 'Year', 'Año', 'Anio']
    year_col = None
    for c in df.columns:
        if c in year_col_candidates:
            year_col = c
            break
    if year_col is None:
        # try detect numeric-like column named similar to year
        for c in df.columns:
            if re.match(r"(?i)year|año|anio", str(c)):
                year_col = c
                break
    if year_col is None and 'WHA' in df.columns:
        # derive from WHA code (e.g., WHA58)
        def wha_to_year(x):
            m = re.search(r"WHA(\d+)", str(x))
            if m:
                num = int(m.group(1))
                # WHA1=1948 -> year = 1947 + num
                return 1947 + num
            return None
        df['year'] = df['WHA'].apply(wha_to_year)
    elif year_col is not None:
        df = df.copy()
        df['year'] = pd.to_numeric(df[year_col], errors='coerce')
    else:
        if 'Year' in df.columns:
            df['year'] = pd.to_numeric(df['Year'], errors='coerce')
        else:
            raise ValueError('No year column found and cannot infer from WHA')
    return df


def long_from_wide_indicator(df: pd.DataFrame, id_cols, year_cols_regex=r"^\d{4}$", value_name='value') -> pd.DataFrame:
    year_cols = [c for c in df.columns if re.match(year_cols_regex, str(c))]
    m = df.melt(id_vars=id_cols, value_vars=year_cols, var_name='year', value_name=value_name)
    m['year'] = pd.to_numeric(m['year'], errors='coerce')
    # standardize missing markers
    m[value_name] = m[value_name].replace(['..', '', 'NA', 'NaN', 'nan', None], np.nan)
    return m


def winsorize_series(s: pd.Series, lower=0.01, upper=0.99) -> pd.Series:
    s = s.astype(float)
    lo = s.quantile(lower)
    hi = s.quantile(upper)
    return s.clip(lower=lo, upper=hi)


def minmax_scale(s: pd.Series) -> pd.Series:
    s = s.astype(float)
    if s.dropna().nunique() <= 1:
        return pd.Series(np.where(s.notna(), 0.0, np.nan), index=s.index)
    mn = s.min(skipna=True)
    mx = s.max(skipna=True)
    return (s - mn) / (mx - mn)


def map_discrete_policy_values(x):
    # Expect values 0/1/2, sometimes strings 'No','Partial','Yes'
    if pd.isna(x):
        return np.nan
    try:
        xv = float(x)
        if np.isnan(xv):
            return np.nan
        # map 0->0, 1->0.5, 2->1
        return {0.0: 0.0, 1.0: 0.5, 2.0: 1.0}.get(xv, np.nan)
    except Exception:
        xs = str(x).strip().lower()
        if xs in ['yes', 'si', 'sí', 'y']:
            return 1.0
        if xs in ['partial', 'parcial']:
            return 0.5
        if xs in ['no', '0']:
            return 0.0
        return np.nan
