import pandas as pd
import numpy as np

from utils import clean_country_name, map_discrete_policy_values
from module_ingest import load_all
from module_participation import clean_participation



def normalize_country_year(df: pd.DataFrame, value_cols: list[str], agg: str = 'mean') -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out['country'] = out['country'].map(clean_country_name)
    out['country'] = out['country'].replace({'Afganist√°n': 'Afghanistan'})
    out['country'] = out['country'].replace({'AfganistaÃÅn': 'Afghanistan'})
    out['country'] = out['country'].replace({'AfganistaÃÅn': 'Afghanistan'})
    out['country'] = out['country'].replace({'Afghanistan ': 'Afghanistan'})
    out['year'] = pd.to_numeric(out['year'], errors='coerce')
    out = out.dropna(subset=['country', 'year'])

    for c in value_cols:
        out[c] = pd.to_numeric(out[c], errors='coerce')

    if agg == 'max':
        out = out.groupby(['country', 'year'], as_index=False)[value_cols].max()
    else:
        out = out.groupby(['country', 'year'], as_index=False)[value_cols].mean()
    return out


def build_panel() -> pd.DataFrame:
    data = load_all()
    spar = data['spar'].copy()
    che = data['che_gdp'].copy()
    uhc = data['uhc'].copy()
    policy, plan, strategy = data['policy_plan_strategy']
    rth = data['right_to_health'].copy()
    excl = data['exclusions'].copy()
    particip_raw = data['participation_raw'].copy()

    # Participation cleaning
    particip = clean_participation(particip_raw)

    # Standardize country/year and collapse duplicates before merging
    spar = normalize_country_year(spar, ['SPAR_total'])
    che = normalize_country_year(che, ['CHE_GDP'])
    uhc = normalize_country_year(uhc, ['UHC_index'])
    policy = normalize_country_year(policy, ['Policy_UHC'])
    plan = normalize_country_year(plan, ['Plan_UHC'])
    strategy = normalize_country_year(strategy, ['Strategy_UHC'])
    rth = normalize_country_year(rth, ['Right_to_health'])
    excl = normalize_country_year(excl, ['art7_excluded'], agg='max')
    particip = normalize_country_year(particip, ['participation_event', 'leadership_event', 'decision_event'], agg='max')

    # SPAR reported dummy
    spar['SPAR_reported'] = (~spar['SPAR_total'].isna()).astype(int)

    # Map discrete scales for policy/plan/strategy
    for name, d in [('Policy_UHC', policy), ('Plan_UHC', plan), ('Strategy_UHC', strategy)]:
        d[name] = d[name].apply(map_discrete_policy_values)

    # Merge step-by-step into a panel on country-year
    dfs = [spar[['country','year','SPAR_total','SPAR_reported']],
           che[['country','year','CHE_GDP']],
           uhc[['country','year','UHC_index']],
           policy[['country','year','Policy_UHC']],
           plan[['country','year','Plan_UHC']],
           strategy[['country','year','Strategy_UHC']],
           rth[['country','year','Right_to_health']],
           particip[['country','year','participation_event','leadership_event','decision_event']],
           excl[['country','year','art7_excluded']]
           ]

    # Outer merge to keep all available years
    panel = None
    for d in dfs:
        if panel is None:
            panel = d.copy()
        else:
            panel = panel.merge(d, on=['country','year'], how='outer')

    # Sort and return
    panel = panel.sort_values(['country','year']).reset_index(drop=True)

    # Imputation flag for values carried to nearest year (rule 5.4): here we do not interpolate; leave NA.
    panel['imputed'] = 0  # placeholder; if nearest-year assignment implemented, set 1 for those rows

    return panel
