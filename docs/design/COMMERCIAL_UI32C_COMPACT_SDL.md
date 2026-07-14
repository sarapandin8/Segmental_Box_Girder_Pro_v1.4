# COMMERCIAL.UI.3.2C — Compact Reversible SDL Schedule

## Accepted UI contract

The visible 3.2 SDL schedule has only three engineering columns:

- Component
- Single Track (kN/m)
- Double Track (kN/m)

The nine BG40 R10 standard rows are fixed, restored during schema migration, and cannot be deleted or archived. Their load values remain editable.

Project-specific SDL rows are created through `＋ Add SDL component`. Custom rows remain in Project JSON and may be archived from the active total or restored later. The UI does not permanently delete them.

The old zero ballastless placeholder is removed from the SDL schedule because it is not listed in the BG40 SDL table and contributes zero load.

## Engineering behavior

- Calculated totals are the sum of active standard and custom rows.
- Adopted SDL values remain separate user-controlled design values and may conservatively exceed the calculated totals.
- The selected Single Track / Double Track basis controls the adopted SDL value passed to the FEA summary.
- Source and row-type metadata remain stored internally for traceability but are not repeated in the compact table.

## Native-crash guard

- Do not use `st.data_editor`.
- Keep `pandas==2.3.3`.
- Keep `plotly==5.24.1`.
- Keep `pd.options.future.infer_string = False`.
