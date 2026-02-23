from __future__ import annotations

from pathlib import Path
import pandas as pd


PILLAR_VARIABLES = {
    'reg': ['SPAR_total'],
    'dom': ['CHE_GDP', 'UHC_index', 'Policy_UHC', 'Plan_UHC', 'Right_to_health'],
    'part': ['participation_event', 'leadership_event', 'decision_event'],
    'sanction': ['art7_excluded'],
}


def _missingness(series: pd.Series) -> float:
    if len(series) == 0:
        return 0.0
    return float(series.isna().mean())


def build_coverage_reports(panel_df: pd.DataFrame, outdir: str | Path) -> dict[str, pd.DataFrame]:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # By variable
    var_rows = []
    for col in panel_df.columns:
        if col in ('country', 'year'):
            continue
        s = panel_df[col]
        var_rows.append({
            'variable': col,
            'n_rows': len(s),
            'n_non_missing': int(s.notna().sum()),
            'n_missing': int(s.isna().sum()),
            'missing_rate': _missingness(s),
            'coverage_rate': 1.0 - _missingness(s),
        })
    by_variable = pd.DataFrame(var_rows).sort_values(['missing_rate', 'variable'], ascending=[False, True])

    # By country
    value_cols = [c for c in panel_df.columns if c not in ('country', 'year')]
    by_country = (
        panel_df.assign(_obs=panel_df[value_cols].notna().sum(axis=1), _total=len(value_cols))
        .groupby('country', as_index=False)[['_obs', '_total']]
        .sum()
    )
    by_country['coverage_rate'] = by_country['_obs'] / by_country['_total']
    by_country['missing_rate'] = 1.0 - by_country['coverage_rate']
    by_country = by_country.rename(columns={'_obs': 'n_non_missing_cells', '_total': 'n_total_cells'})

    # By year
    by_year = (
        panel_df.assign(_obs=panel_df[value_cols].notna().sum(axis=1), _total=len(value_cols))
        .groupby('year', as_index=False)[['_obs', '_total']]
        .sum()
    )
    by_year['coverage_rate'] = by_year['_obs'] / by_year['_total']
    by_year['missing_rate'] = 1.0 - by_year['coverage_rate']
    by_year = by_year.rename(columns={'_obs': 'n_non_missing_cells', '_total': 'n_total_cells'})

    # By pillar
    pillar_rows = []
    for pillar, cols in PILLAR_VARIABLES.items():
        existing_cols = [c for c in cols if c in panel_df.columns]
        if not existing_cols:
            pillar_rows.append({
                'pillar': pillar,
                'n_variables': 0,
                'n_total_cells': 0,
                'n_non_missing_cells': 0,
                'coverage_rate': 0.0,
                'missing_rate': 1.0,
            })
            continue

        sub = panel_df[existing_cols]
        n_total = sub.shape[0] * sub.shape[1]
        n_non_missing = int(sub.notna().sum().sum())
        coverage = float(n_non_missing / n_total) if n_total else 0.0
        pillar_rows.append({
            'pillar': pillar,
            'n_variables': len(existing_cols),
            'n_total_cells': int(n_total),
            'n_non_missing_cells': n_non_missing,
            'coverage_rate': coverage,
            'missing_rate': 1.0 - coverage,
        })
    by_pillar = pd.DataFrame(pillar_rows).sort_values('missing_rate', ascending=False)

    # Write outputs
    by_variable.to_csv(outdir / 'coverage_report_by_variable.csv', index=False)
    by_country.to_csv(outdir / 'coverage_report_by_country.csv', index=False)
    by_year.to_csv(outdir / 'coverage_report_by_year.csv', index=False)
    by_pillar.to_csv(outdir / 'coverage_report_by_pillar.csv', index=False)

    summary_md = outdir / 'coverage_summary.md'
    worst_var = by_variable.iloc[0] if len(by_variable) else None
    worst_pillar = by_pillar.iloc[0] if len(by_pillar) else None
    with summary_md.open('w', encoding='utf-8') as f:
        f.write('# Coverage summary\n\n')
        f.write(f'- Rows audited: {len(panel_df)}\n')
        f.write(f'- Variables audited: {len(value_cols)}\n')
        if worst_var is not None:
            f.write(f"- Highest missingness variable: `{worst_var['variable']}` ({worst_var['missing_rate']:.2%}).\n")
        if worst_pillar is not None:
            f.write(f"- Highest missingness pillar: `{worst_pillar['pillar']}` ({worst_pillar['missing_rate']:.2%}).\n")
        f.write('- Reports generated: by variable, country, year, and pillar.\n')

    return {
        'by_variable': by_variable,
        'by_country': by_country,
        'by_year': by_year,
        'by_pillar': by_pillar,
    }
