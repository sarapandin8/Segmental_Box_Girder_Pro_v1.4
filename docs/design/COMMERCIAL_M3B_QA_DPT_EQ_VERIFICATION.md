# COMMERCIAL.M3B-QA — DPT EQ verification notes

## Purpose

Verify and correct the DPT 1301/1302-61 EQ module used in `1.3.9 Earthquake (EQ)`.

## Verified basis

- General Thailand district lookup uses DPT Table 1.4-1 for `Ss` and `S1`.
- Site coefficients use DPT Table 1.4-2 (`Fa`) and Table 1.4-3 (`Fv`).
- Design spectral acceleration uses DPT Section 1.4.4:
  - `SDS = 2/3 SMS`
  - `SD1 = 2/3 SM1`
- Equivalent-static `Cs` uses DPT Chapter 3:
  - `Cs = Sa(I/R)`
  - `Cs >= 0.01`
- Seismic design category uses DPT Section 1.6 tables.

## Corrected issue

M3B plotted and evaluated the General Thailand response spectrum using the dynamic-spectrum shape from DPT Fig. 1.4-3 / Fig. 1.4-4, which includes a `0.4SDS` start and ramp to `SDS`. That shape is for dynamic analysis, not the equivalent-static `Cs` route.

M3B-QA corrects the route:

- If `SD1 <= SDS`: use DPT Fig. 1.4-1.
  - `Sa = SDS` for `T <= Ts = SD1/SDS`.
  - `Sa = SD1/T` for `T > Ts`.
- If `SD1 > SDS`: use DPT Fig. 1.4-2.
  - `Sa = SDS` for `T <= 0.2 s`.
  - `Sa` varies linearly from `SDS` at `T = 0.2 s` to `SD1` at `T = 1.0 s`.
  - `Sa = SD1/T` for `T > 1.0 s`.

## Regression checks

- `test_dpt_m3b_qa_equivalent_static_fig_141_no_dynamic_ramp`
- `test_dpt_m3b_qa_equivalent_static_fig_142_linear_branch`

## Production caution

The DPT database was extracted from the uploaded PDF. The app now has code-level and route-level regression checks, but critical production projects should still spot-check the selected district / Bangkok Basin zone against the official standard page and project geotechnical/seismic criteria.
