# COMMERCIAL.M3C — AASHTO Bridge I/R Recommendation

## Purpose

Add bridge-specific `R` recommendation controls to the DPT EQ workflow without sacrificing traceability. The app now uses:

- DPT 1301/1302-61 for Thai seismic spectrum and `Cs = Sa(I/R)` calculation.
- AASHTO LRFD 2020 Table 3.10.7.1-1 for bridge substructure response modification factor `R` guidance.
- Project/DPT basis for importance factor `I`.

## Source separation

The app deliberately does not equate AASHTO operational category with DPT importance factor `I`.

```text
DPT / project criteria → I
AASHTO operational category + substructure type → R
```

## User controls

One-source EQ controls:

- AASHTO operational category: Critical / Essential / Other.
- Substructure / lateral system.
- R selection mode: automatic table lookup or manual override.
- Importance factor I preset or manual override.
- Analysis period T.

All EQ branches read the same `I`, `R`, and `T` values.

## QA notes

- Connection R-factors are separate from global substructure R.
- Manual override is marked as user override in source trace.
- AASHTO operational category must be confirmed by the owner or authority having jurisdiction.
