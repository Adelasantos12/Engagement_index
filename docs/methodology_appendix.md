# Methodology Appendix

## Eligibility rules (explicit)

To make score computation auditable and reproducible, IECGGS now applies explicit eligibility thresholds before sub-index and index calculation:

- Regulatory pillar (`E_reg`): computed only if `n_reg_obs >= 1` (from `SPAR_n`).
- Domestic pillar (`E_dom`): computed only if `n_dom_obs >= 3` (from `CHE_GDP_n`, `UHC_n`, `Policy_UHC`, `Plan_UHC`, `Right_n`).
- Participation pillar (`E_part`): computed only if `n_part_obs >= 2` (from normalized participation counts).
- Global index (`IECGGS_raw`): computed only if `n_pillars_ok >= 3`.

Thresholds are configurable with environment variables:

- `IECGGS_MIN_REG_OBS` (default `1`)
- `IECGGS_MIN_DOM_OBS` (default `3`)
- `IECGGS_MIN_PART_OBS` (default `2`)
- `IECGGS_MIN_INDEX_PILLARS` (default `3`)

## Flags and auditability

The pipeline exports `panel_with_flags.csv` including:

- `n_reg_obs`, `n_dom_obs`, `n_part_obs`, `n_pillars_ok`
- `flag_pillar_reg_ok`, `flag_pillar_dom_ok`, `flag_pillar_part_ok`, `flag_iecgss_ok`

These fields document exactly why a row receives (or does not receive) a score.

## Coverage audit outputs

The pipeline generates:

- `coverage_report_by_variable.csv`
- `coverage_report_by_country.csv`
- `coverage_report_by_year.csv`
- `coverage_report_by_pillar.csv`
- `coverage_summary.md`

All are derived from pre-index panel data (`panel_clean.csv` equivalent in memory) and are intended to support transparent missingness diagnostics before interpretation of ranks.
