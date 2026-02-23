import re
import pandas as pd
import numpy as np

from utils import standardize_country_column, coerce_year_column


LEADERSHIP_PATTERNS = [
    r"\bpresident\b", r"\bvice[- ]?president\b", r"\bvicepresident\b", r"\bchair\b", r"\bco[- ]?chair\b",
    r"\brelator\b", r"\brapporteur\b", r"\bvice[- ]?chair\b", r"\bpresidencia\b", r"\bvicepresidencia\b",
]

DECISION_BODY_PATTERNS = [
    r"comision\s*a\b", r"comision\s*b\b", r"commission\s*a\b", r"commission\s*b\b",
    r"mesa de la asamblea", r"asamblea", r"committee", r"executive board", r"board",
]

INSTITUTIONAL_PARTICIPATION_PATTERNS = [
    r"eleccion de miembros", r"election of members", r"nombramiento de representantes",
    r"appointment of representatives", r"miembro[s]? electo[s]?", r"elected member",
]

ADMIN_BODY_PATTERNS = [
    r"caja comun de pensiones", r"common pension fund", r"administrative", r"financ(e|ial)" ,
]


def normalize_activity_text(s: str) -> str:
    if pd.isna(s):
        return ""
    # remove newlines and compress spaces, lower-case
    s2 = str(s).replace("\n", " ").replace("\r", " ")
    s2 = re.sub(r"\s+", " ", s2).strip().lower()
    return s2


def classify_activity(activity_raw: str) -> str:
    txt = normalize_activity_text(activity_raw)
    if not txt:
        return 'unknown'
    # rule-based matching in order
    for pat in LEADERSHIP_PATTERNS:
        if re.search(pat, txt, flags=re.IGNORECASE):
            return 'leadership'
    for pat in DECISION_BODY_PATTERNS:
        if re.search(pat, txt, flags=re.IGNORECASE):
            return 'decision_body'
    for pat in INSTITUTIONAL_PARTICIPATION_PATTERNS:
        if re.search(pat, txt, flags=re.IGNORECASE):
            return 'institutional_participation'
    for pat in ADMIN_BODY_PATTERNS:
        if re.search(pat, txt, flags=re.IGNORECASE):
            return 'administrative_body'
    # fallback: if contains election/appoint keywords
    if re.search(r"election|appoint|nombramiento|eleccion", txt):
        return 'institutional_participation'
    return 'other'


def clean_participation(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    # Identify activity column
    candidate_cols = ['Actividad', 'Activity', 'Descripcion', 'Descripción', 'Description', 'Texto', 'Text']
    act_col = None
    for c in df.columns:
        if c in candidate_cols:
            act_col = c
            break
    if act_col is None:
        # if there is only one non-WHA/year/country object column, take it
        object_cols = [c for c in df.columns if df[c].dtype == object and c not in ('WHA','year','country')]
        if object_cols:
            act_col = object_cols[0]
    # Standardize country and year
    if 'country' not in df.columns:
        df = standardize_country_column(df)
    df = coerce_year_column(df)
    # Normalize activity text
    if act_col is not None:
        df['activity_raw'] = df[act_col].apply(normalize_activity_text)
    else:
        df['activity_raw'] = ''
    # Classify
    df['activity_type'] = df['activity_raw'].apply(classify_activity)
    # Aggregations by country-year
    grp = df.groupby(['country','year'], dropna=False)
    participation_event = grp.size().rename('participation_event')
    leadership_event = grp.apply(lambda g: (g['activity_type']=='leadership').sum()).rename('leadership_event')
    decision_event = grp.apply(lambda g: (g['activity_type']=='decision_body').sum()).rename('decision_event')
    out = pd.concat([participation_event, leadership_event, decision_event], axis=1).reset_index()
    # Remove rows without valid year
    out = out[pd.notna(out['year'])]
    out['year'] = out['year'].astype(int)
    return out[['country','year','participation_event','leadership_event','decision_event']]
