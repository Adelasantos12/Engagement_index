import pandas as pd
import numpy as np

from utils import standardize_country_column, coerce_year_column, map_discrete_policy_values
from module_ingest import load_all
from module_participation import clean_participation


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

    # Standardize all country names
    for df in [spar, che, uhc, policy, plan, strategy, rth, excl, particip]:
        if 'country' in df.columns and 'iso3' not in df.columns:
            df['country'] = df['country'].astype(str)

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
