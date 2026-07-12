# Segmental Box Girder Pro — COMMERCIAL.FEA.5D1A

This milestone adds **COMMERCIAL.FEA.5D1A — Legacy Project Load Single-Pass Migration and Memory-Safe Save Hotfix** on the accepted `COMMERCIAL.FEA.5D1` source-review baseline.

## Scope implemented

- Stores only raw immutable JSON bytes in the pending Streamlit load state; decoding and schema migration occur once at the top of the next rerun before widget keys exist.
- Removes the second migration from `_apply_pending_project_json_load` and removes unconditional full-project migration/deepcopy from every Streamlit rerun.
- Adds an explicit current-schema fast path using `migration_complete` and `migration_target_schema_version`.
- Uses the file's declared `meta.schema_version` as the source-file schema. Historical `loaded_schema_version` is retained separately as provenance and no longer forces repeated migration from an older origin.
- Keeps the active project unchanged when a legacy load fails and reports the failure in the sidebar.
- Makes Save memory-safer by shallow-copying metadata only for current projects and emitting compact UTF-8 JSON instead of deep-copying and re-migrating the whole project.
- Preserves all section, tendon, ULS, Transfer, and Final Service source records.
- Retains `plotly==5.24.1` for verified Streamlit Cloud compatibility.

Schema:

- `0.5.11-commercial-fea5d1c-pandas-arrow-string-crash-hotfix`

---

# Segmental Box Girder Pro — COMMERCIAL.FEA.5D1

This milestone closes **COMMERCIAL.FEA.5D1 — Final Service Component Review and Schema-Trace Closeout** on the accepted `COMMERCIAL.FEA.5D` source-safe calculation baseline.

## Scope implemented

- Makes `Summary`, `P (Axial)`, `V2 (Vy)`, `T (Torsion)`, and `M3 (Mx)` the only primary Section 5.4 review navigation.
- Keeps full-span component charts, governing cards, source cases, station identity, compact component tables, and raw-source trace as the commercial review path.
- Removes the legacy generic envelope-stage renderer so the wide station-by-station table cannot replace the component chart workspace.
- Retains the wide mixed-source scalar-bound table only inside `Detailed mixed-source scalar-bound audit` on the Summary page.
- Preserves mixed-source semantics: `COMPONENT ENVELOPE` extrema are independent scalar bounds; `SINGLE STATE` is simultaneous only within its original source row.
- Clarifies that Final Service downstream targets are Sections `8 SLS Stress` and `9 Deflection`, both still `NOT YET CONNECTED`.
- Separates active app schema, loaded source schema, and migration status in the Project File panel and load confirmation.
- Retains `plotly==5.24.1` for verified Streamlit Cloud compatibility.

Schema:

- `0.5.8-commercial-fea5d1-final-service-component-review-closeout`

---

# Segmental Box Girder Pro — COMMERCIAL.FEA.5D

This milestone adds **COMMERCIAL.FEA.5D — Final Service SLS Mixed-Source Force Review** on the accepted `COMMERCIAL.FEA.5C1` Transfer-stage review baseline.

## Scope implemented

- Converts Section `5.4 Final Service SLS` from a raw envelope table into a commercial nested review workspace: `Summary`, `P (Axial)`, `V2 (Vy)`, `T (Torsion)`, and `M3 (Mx)`.
- Preserves the imported mixed source semantics: `S1A` and `S1B` are `COMPONENT ENVELOPE` Max/Min sources, while `S1C_01`, `S1C_02`, `S2`, `S3_01`, and `S3_02` are `SINGLE STATE` sources.
- Builds source-traced scalar min/max bounds across all validated Final Service candidates without synthesizing simultaneous `P–M3` or `V2–T` force pairs.
- Adds full-span source-review charts with governing markers, edge-safe annotations, four-decimal station identity, dominant-source captions, compact envelope tables, and detailed/raw QA toggles.
- Adds a Final Service Summary with governing absolute magnitude, signed value, governing station, LocType, and exact source row for `P`, `V2`, `T`, and `M3`.
- States explicitly that an individual `SINGLE STATE` row is simultaneous only within that source row; the global scalar bounds and four governing cards are not one common vector.
- Keeps Sections `8 SLS Stress` and `9 Deflection` explicitly **NOT YET CONNECTED**. No stress, deflection, or downstream design demand is changed.
- Retains `plotly==5.24.1` for Streamlit Cloud compatibility.

Schema:

- `0.5.7-commercial-fea5d-final-service-sls-force-review`

---

# Segmental Box Girder Pro — COMMERCIAL.FEA.5C1

This milestone adds **COMMERCIAL.FEA.5C1 — Transfer Signed-Governing Display Consistency** on the accepted `COMMERCIAL.FEA.5C` Transfer-stage review baseline.

## Scope implemented

- Keeps the governing-station selection rule unchanged: each Transfer component is still selected by maximum absolute magnitude.
- Displays the signed governing source value as the primary value on Transfer Summary and component-review cards.
- Moves the absolute magnitude to secondary supporting text so negative governing values agree visually with the plotted marker and curve.
- Uses Transfer-specific chart legend and annotation labels without absolute-value bars: `Governing P (Axial)`, `Governing V2 (Vy)`, `Governing T (Torsion)`, and `Governing M3 (Mx)`.
- Reorders the Transfer summary table to show `Signed governing value` before `Absolute magnitude`.
- Applies the same signed-display rule to P, V2, T, and M3 while leaving the ULS scalar-envelope `Governing |...|` convention unchanged.
- Retains `plotly==5.24.1` for Streamlit Cloud compatibility and keeps Sections 6–8 explicitly **NOT YET CONNECTED**.

Schema:

- `0.5.6-commercial-fea5c1-transfer-signed-governing-display-consistency`

---

# Segmental Box Girder Pro — COMMERCIAL.FEA.5C

This milestone adds **COMMERCIAL.FEA.5C — Transfer-Stage Simultaneous Force-Vector Review** on the accepted `COMMERCIAL.FEA.5B2` ULS-review baseline.

## Scope implemented

- Converts Section `5.3 Transfer Stage` from a raw table into a commercial nested review workspace: `Summary`, `P (Axial)`, `V2 (Vy)`, `T (Torsion)`, and `M3 (Mx)`.
- Preserves the hard source contract: exactly one OutputCase, one row per SectCutNum, blank StepType, and `SINGLE STATE` semantics.
- Adds source-traced full-span component charts with four-decimal station identity, governing markers, edge-safe annotations, and Concrete Section Pro figure styling.
- Exposes the complete simultaneous `P–V2–T–M3` companion vector in chart hover and in a governing-station vector table.
- Distinguishes two valid statements: each source row is one simultaneous vector, while the four global governing components may occur at different section cuts and are not one common vector.
- Keeps Sections 6–8 explicitly **NOT YET CONNECTED**; no design demand or result changes in this milestone.
- Pins `plotly==5.24.1`, matching the Streamlit Cloud-compatible figure runtime verified against Concrete Section Pro; Plotly 6 remains blocked pending a separate compatibility audit.

Schema:

- `0.5.5-commercial-fea5c-transfer-stage-simultaneous-force-review`

---

# Segmental Box Girder Pro — COMMERCIAL.FEA.5B2

This milestone adds **COMMERCIAL.FEA.5B2 — Governing Annotation and Station Precision Polish** on the accepted `COMMERCIAL.FEA.5B1` axis-convention ULS-review baseline.

## Scope implemented

- Retains the original imported CSiBridge field names for audit traceability while displaying the active app-axis meaning consistently as `P (Axial)`, `V2 (Vy)`, `T (Torsion)`, and `M3 (Mx)`.
- Updates ULS subpage labels, chart titles/subtitles, y-axis labels, governing cards, summary tables, compact envelope tables, Transfer-stage tables, and source-policy text to the same convention.
- Adds a visible Axis / Force Convention note: `P → Axial`, `V2 → Vy`, `T → Torsion`, and `M3 → Mx`.
- States explicitly that non-CSiBridge imports require source-axis mapping confirmation; V2/V3 and M2/M3 directions must not be inferred from names alone.
- Shortens the nested ULS selector to `Summary`, `P (Axial)`, `V2 (Vy)`, `T (Torsion)`, and `M3 (Mx)` while preserving section numbering in the active-review caption.
- Uses neutral review cards for scalar values and locations; green remains reserved for source/readiness state and amber for provenance/connection warnings.
- Adds dominant Max/Min source-case insight across section cuts, useful for explaining nearly uniform force-envelope shapes such as torsion.
- Makes the default scalar-envelope table compact and moves candidate counts plus full min/max source trace behind a detailed QA toggle.
- Shortens repeated chart captions while preserving the non-simultaneous component-envelope warning.
- Keeps Sections 6–8 explicitly **NOT YET CONNECTED**; no ULS design demand is changed by this milestone.

## Axis convention

| Imported source field | App display | Active app meaning |
|---|---|---|
| `P` | `P (Axial)` | axial force along the member axis |
| `V2` | `V2 (Vy)` | vertical shear in the app y direction |
| `T` | `T (Torsion)` | torsional moment about the member longitudinal axis |
| `M3` | `M3 (Mx)` | bending moment about the app x axis |

Schema:

- `0.5.4-commercial-fea5b2-governing-annotation-station-precision-polish`

# Segmental Box Girder Pro — COMMERCIAL.FEA.5A

This milestone adds **COMMERCIAL.FEA.5A — Source-Safe Three-Stage CSiBridge Force Import Hub** on the accepted `TENDON.2.4Q` baseline.

## Scope implemented

- Adds separate `.xlsx` sources for ULS, Transfer Stage, and Final Service SLS Bridge Object Forces.
- Imports only the actions required by this app: `P`, `V2`, `T`, and `M3`, while preserving `BridgeObj`, `SectCutNum`, `Distance`, `LocType`, `OutputCase`, `CaseType`, `StepType`, and source row.
- Classifies every source row as either `SINGLE STATE` or `COMPONENT ENVELOPE`. Max/Min component-envelope rows are never described as simultaneous force vectors.
- Builds one compact scalar-envelope row per `SectCutNum`, with separate source trace for every component minimum and maximum.
- Enforces the Transfer Stage contract as a hard gate: exactly one OutputCase, one row per `SectCutNum`, blank StepType, and `SINGLE STATE` semantics.
- Requires the three stages to match the active `BridgeObj` and the same `SectCutNum` / `Distance` / `LocType` station map.
- Preserves the previously validated source if a replacement workbook is rejected and labels the failed attempt explicitly.
- Persists only engineering-use Program Control metadata (`ProgramName`, `Version`, `CurrUnits`, `BridgeCode`, `ConcCode`); license and machine metadata are excluded.
- Adds Project Validation / Report QA issue codes for missing sources, span mismatch, station mismatch, downstream-not-connected state, and stale connected results.
- Keeps Sections 6–8 explicitly **NOT YET CONNECTED**. Their existing BG40/keyed demand values are not silently replaced by the imported source package.
- Adds a read-only Section 5 source snapshot to Report / QA.

## Verified project fixtures

- ULS: 2,560 raw rows, 80 section cuts, 18 output cases, 32 rows per cut.
- Transfer Stage: 80 raw rows, 80 section cuts, one single-state row per cut.
- Final Service SLS: 720 raw rows, 80 section cuts, 7 output cases, 9 rows per cut.
- Cross-stage station map: 80 matching section-cut identities for `B2_SPAN1`.

## Important limitation

`COMPONENT ENVELOPE` Max/Min output may not preserve simultaneous `P-M3` or `V2-T` pairs. This milestone validates and stores the FEA source package only. A later, separately reviewed milestone must define the conservative/non-envelope downstream design route before Sections 6–8 consume these results.

Schema:

- `0.5.1-commercial-fea5a-source-safe-three-stage-import-hub`

# Segmental Box Girder Pro — COMMERCIAL.TENDON.2.4Q

This milestone adds **COMMERCIAL.TENDON.2.4Q — Source Provenance and Save Label Clarity**:

- Separates adopted calculation-payload readiness from original upload-file provenance.
- Source rows with complete filename and SHA-256 metadata remain `READY`.
- Complete saved-project tendon rows without original upload metadata are labelled `RESTORED FROM PROJECT SNAPSHOT` rather than being over-certified.
- Partly retained filename/SHA metadata is labelled `SOURCE METADATA PARTIAL`.
- Detailed QA now reports `Source trace rows` and `Source metadata provenance` as separate checks.
- A complete calculation snapshot with partial provenance displays `DETAILED PAYLOAD READY — SOURCE METADATA PARTIAL` and remains usable without hiding the audit limitation.
- Project-load migration refreshes the adopted source trace using the new provenance rules.
- The sidebar save panel distinguishes section rows, computed section, adopted section properties, tendon-source adoption, and project snapshot availability.
- Prestress-loss values and the CSiBridge final-stage handoff remain unchanged.

Schema:

- 0.4.111-commercial-tendon24q-source-provenance-save-label-clarity

# Segmental Box Girder Pro — COMMERCIAL.TENDON.2.4P

This milestone adds **COMMERCIAL.TENDON.2.4P — Print Text-Layer Cleanup and Detailed QA Integrity**:

- Keeps the accepted B2_SPAN1 fresh-project default and compact Adopted Tendon Data workflow from TENDON.2.4O.
- Tightens browser-print CSS around the Streamlit sidebar scroll container so Edge/Chromium scrollbar arrow controls do not leak as Segoe Fluent private-use glyphs in PDF text extraction.
- Hides Streamlit Material Symbols control glyphs, including file-uploader icons, from browser-print output while keeping their on-screen behavior unchanged.
- Adds an explicit **Detailed QA integrity** table when `Detailed adopted tendon tables / QA` is opened. It verifies tendon rows, merged profile rows, group summary rows, downstream summary, and source trace before rendering the detailed tables.
- Adds automated integrity tests for the detailed QA payload and static print selectors.
- Prestress-loss calculations and the CSiBridge final-stage handoff remain unchanged: 21.36% total loss, 298.03 MPa total stress loss, fpe,avg = 1096.97 MPa, and Pe,total = 58,973 kN.

Schema:

- 0.4.110-commercial-tendon24p-print-text-layer-detailed-qa-integrity

# Segmental Box Girder Pro — COMMERCIAL.TENDON.2.4O

This milestone adds **COMMERCIAL.TENDON.2.4O — Default Span, Compact Adopted Data, and Print Glyph Polish**:

- Fresh projects now default to active span / BridgeObj **B2_SPAN1** in both project context and tendon-layout mapping. Loaded projects retain their saved span.
- Fresh sessions with no tendon files still open at **Import / Mapping**; valid locked sources still default to **Adopted Tendon Data**.
- The main Adopted Tendon Data view is compact: source status, stressing basis, and the four-row tendon group summary remain visible.
- Tendon-by-tendon rows, merged station profiles, downstream full summary, and source trace move behind **Detailed adopted tendon tables / QA**.
- Browser-print CSS additionally suppresses Streamlit sidebar open/close controls that can appear as private-use glyphs in PDF text extraction.
- Prestress-loss calculation values and the CSiBridge final-stage handoff remain unchanged.

# Segmental Box Girder Pro — COMMERCIAL.TENDON.2.4N

This milestone adds **COMMERCIAL.TENDON.2.4N — Fresh Import State Polish and Disabled Build Gate**:

- Fresh app sessions with no imported tendon tables remain correctly on **Import / Mapping**.
- Invalid placeholder tendon models no longer show a deterministic working-model hash; the card now reads **NO WORKING MODEL** until the General / Vertical / Horizontal tables exist.
- The **Build / refresh imported tendon layout model** action is disabled until all three required tendon tables are uploaded.
- A clear missing-table message tells the user exactly which tendon source files are required before building.
- Locked/adopted-source workflow from TENDON.2.4M is preserved: when a valid working model matches the adopted source, 2.4 defaults to **Adopted Tendon Data** and upload/refresh controls remain collapsed.
- Prestress-loss values are unchanged: CSiBridge final loss = **21.36%**, total stress loss = **298.03 MPa**, `fpe,avg = 1096.97 MPa`, and `Pe,total = 58,973 kN`.

# Segmental Box Girder Pro — COMMERCIAL.TENDON.2.4M

This milestone adds **COMMERCIAL.TENDON.2.4M — Locked Source Entry Default and Print Polish**:

- When the tendon source is locked and the working model matches the adopted downstream source, entering **2.4 Tendon Layout Reference** now resets the internal tab to **Adopted Tendon Data**.
- Users can still intentionally switch to **Import / Mapping**, but navigating away and back returns to the locked adopted source view.
- The 4.1 and 4.6 milestone labels are updated from TENDON.2.4K to TENDON.2.4M.
- Print/PDF CSS is tightened to hide more Streamlit control icons that can leak as glyphs in browser-generated PDFs.
- Prestress-loss values are unchanged: CSiBridge final loss = **21.36%**, total stress loss = **298.03 MPa**, `fpe,avg = 1096.97 MPa`, and `Pe,total = 58,973 kN`.

# Segmental Box Girder Pro — COMMERCIAL.TENDON.2.4L

This milestone adds **COMMERCIAL.TENDON.2.4L — Locked Source Default Adopted Tab and Update Controls Collapse**:

- When the working tendon model already matches the adopted downstream source, the 2.4 internal tab defaults once to **Adopted Tendon Data** instead of **Import / Mapping**.
- Upload, mapping, and refresh controls are hidden under **Update / replace tendon source** for locked sources.
- The Import / Mapping page now shows a locked-source summary and source trace without suggesting the user must upload or rebuild anything.
- Refresh remains available as a secondary QA action only after explicitly opening the update controls.
- Adds print CSS to suppress common Streamlit toolbar/status glyph artifacts during browser PDF export.
- Downstream prestress-loss values are unchanged: CSiBridge final loss = **21.36%**, total stress loss = **298.03 MPa**, fpe,avg = **1096.97 MPa**, Pe,total = **58,973 kN**.

# Segmental Box Girder Pro — COMMERCIAL.TENDON.2.4K

This milestone adds **COMMERCIAL.TENDON.2.4K — Locked Source Button and Print Glyph Polish**:

- Keeps the 2.4 tendon source locked workflow from TENDON.2.4J.
- Hides the prominent Build / refresh action when the working tendon model already matches the adopted downstream source.
- Moves working-model refresh to a small QA toggle and uses a secondary button, not a red/primary action.
- Converts raw import data and tendon-location QA details from Streamlit expanders to print-safe toggles.
- Keeps CSiBridge final-stage loss handoff unchanged at 21.36% when using the current BG40 example basis.

# Segmental Box Girder Pro — COMMERCIAL.TENDON.2.4J

This milestone adds **COMMERCIAL.TENDON.2.4J — Downstream Span Source Propagation Fix**:

- Propagates active-span BridgeObj mapping into the locked adopted tendon snapshot whenever downstream pages read the tendon source.
- Directly opening Section 4 pages no longer depends on first visiting 2.4 to run the B2_SPAN1 → B2_SPAN2 migration.
- Updates adopted tendon model fingerprint, downstream summary, source trace, and prestress handoff fields after span-label migration.
- Keeps 2.4, 4.1, and 4.6 on the same adopted tendon source state for active-span consistency checks.
- Preserves the CSiBridge final-stage average total loss handoff: 21.36% for the current BG40 dataset.

# Segmental Box Girder Pro — COMMERCIAL.PSLOSS.26J


This milestone adds COMMERCIAL.PSLOSS.26J — Clean 4.1 General and PDF Export Polish:

- Reworks 4.1 General into a compact design-source summary for Section 4 rather than a developer-style readiness page.
- Keeps source-gate registers, blocked-input checks, tendon readiness, CR&SH handoff, and formula readiness in a collapsed Source trace / QA toggle.
- Renders engineering tables as static HTML tables to avoid Streamlit dataframe toolbar/scroll glyphs in browser PDF exports.
- Converts key 2.4 tendon-source expanders to trace toggles so `keyboard_arrow_right` artifacts are reduced in printed/PDF output.
- Preserves the active-span tendon source consistency gate and the locked CSiBridge final-stage loss handoff from TENDON.2.4I / PSLOSS.26I.

This milestone adds COMMERCIAL.TENDON.2.4I — Active Span Source Consistency Polish:
- Syncs the adopted tendon source to the active project span when BridgeObj mapping is enabled.
- Migrates legacy adopted source labels such as B2_SPAN1 to active B2_SPAN2 when the working mapped model is otherwise unchanged and valid.
- Marks JackFrom/stressing basis as ADOPTED / ACTIVE when the working model matches the locked downstream source.
- Updates 2.4 source notes so physical bend/deviator geometry is explicitly the 4.2 friction α source.
- Adds active-span tendon-source status into the 4.6 CSiBridge handoff gate.

This baseline carries forward the accepted commercial milestones and standards:
- COMMERCIAL.PSLOSS.26A
- COMMERCIAL.PSLOSS.26
- COMMERCIAL.UI.SIDEBAR.2
- COMMERCIAL.UI.SIDEBAR.1
- COMMERCIAL.UI.HEADER.1
- COMMERCIAL.M3H.8
- COMMERCIAL.M3H.9
- COMMERCIAL.M3H.10
- COMMERCIAL.M3H.11
- COMMERCIAL.UI.1
- COMMERCIAL.UI.2
- COMMERCIAL.M4.1A
- COMMERCIAL.M4.1B
- COMMERCIAL.M4.1C
- COMMERCIAL.M4.1D
- COMMERCIAL.M4.1E
- COMMERCIAL.CODE.1
- COMMERCIAL.LOADS.1
- COMMERCIAL.LOADS.2
- COMMERCIAL.LOADS.3
- COMMERCIAL.LOADS.4
- COMMERCIAL.LOADS.5
- COMMERCIAL.LOADS.6
- COMMERCIAL.LOADS.7
- COMMERCIAL.LOADS.8
- COMMERCIAL.LOADS.9
- COMMERCIAL.LOADS.10
- COMMERCIAL.LOADS.11
- COMMERCIAL.LOADS.12
- COMMERCIAL.LOADS.13
- COMMERCIAL.LOADS.14
- COMMERCIAL.LOADS.15
- COMMERCIAL.LOADS.16
- COMMERCIAL.LOADS.17
- COMMERCIAL.LOADS.24
- COMMERCIAL.LOADS.25
- COMMERCIAL.LOADS.26
- COMMERCIAL.LOADS.27
- COMMERCIAL.LOADS.28
- COMMERCIAL.LOADS.29
- COMMERCIAL.LOADS.30
- COMMERCIAL.LOADS.31
- COMMERCIAL.LOADS.32
- COMMERCIAL.LOADS.33
- COMMERCIAL.LOADS.34
- COMMERCIAL.LOADS.35
- COMMERCIAL.LOADS.36
- COMMERCIAL.LOADS.37
- COMMERCIAL.LOADS.38

Display formatting rules
- Retain the commercial engineering figure system and canvas-card presentation.
- Shared figure helpers remain under `visualization/figure_system.py`.
- New figures must follow the existing UI.1 / UI.2 standards.
- Screen figures default to Interactive review; Report / QA and export workflows force Report preview figure configuration internally.
- Shared figure helpers remain the backend source for Plotly toolbar/export behavior; the global Figure System sidebar control is intentionally hidden.

Retained basis / reference notes
- 1.3.7 Wind Load
- EN 1991-1-4
- Table 2.5
- DPT seismic database
- Bangkok Basin Zone 1–10
- AASHTO LRFD 2020 Table 3.10.7.1-1
- Full station-by-station FEA import remains pending
- Coordinate-driven section properties
- AASHTO LRFD Bridge Design Specifications, 9th Edition, 2020
- Structural Polygon 1
- Opening Polygon 1
- Orthographic Isometric

Current milestone focus
- Remove the global Figure System control from the sidebar so the sidebar remains focused on navigation and project controls.
- Keep the backend engineering figure system intact.
- Default on-screen figures to Interactive review.
- Force Report preview figure configuration for Report / QA and future export workflows without requiring a user toggle.
- Preserve all engineering calculations, save/load behavior, report data, and figure-generation logic.

Clean release rule
- ZIP packages must not include `__pycache__/`, `.pytest_cache/`, `*.pyc`, `*.pyo`, `.streamlit/`, or `.DS_Store`.


Current milestone focus:
- Replace the grayscale/contrast-enhanced DPT wind map card asset with the user-approved clean color reference map.
- Keep province lookup as the authoritative adopted wind-group source.

- Replace the simplified lower z_e schematic in the wind factor C reference card with the user-provided four-pier bridge SVG reference.

- Split the wind factor C / z_e mixed reference into a compact Table 2.5 card plus a separate z_e bridge-profile card so the figure fits comfortably in the UI.

- Compact the separate z_e bridge-profile card using an embedded SVG image constrained to a fixed card height so the editable wind parameter table remains close to the input assistant.

- Remove duplicate right-side report images from the EN Factors tab; the tab now shows only the formula, Table 2.5 data, interpolation results, and a note that figures remain in Input Assistant cards.

- Polish the Wind Calculations tab with result cards, explicit q = 0.5ρvb² velocity pressure, and Pa→N→kN unit trace using Fw = q·C·Aref/1000.

- Replace the WS/WL wind application model card image with the user-provided refined bridge/train figure and enlarge the display height for better readability.

- Replace the bridge wind-direction reference card image with the user-provided refined EN Figure 8.2 style sketch and enlarge the display height for readability.

- Clarify the WS/WL wind application figure note so V is explicitly identified as an associated vertical reference effect, not wind velocity.

- Upgrade the 3.6 CF page from a factor-only calculator to a code-assisted input assistant with curvature condition, f/C result cards, explicit EN unit trace, project threshold, and FEA adoption status.

- Simplify CF track alignment condition to two modes: straight track/no horizontal curve and curved track/finite radius; large-radius cases are treated as finite-radius curved track with small-result assessment.

- Simplify CF alignment UI to two meaningful modes: Straight track / no horizontal curve and Curved track / finite radius, migrating old large-radius values into the finite-radius curved-track calculation.

- Split CF engineering assessment from FEA adoption status so threshold compliance remains visible even when CF is reported as factor-only/not adopted.

- COMMERCIAL.LOADS.32: Polished straight-track CF mode by hiding finite-radius inputs, threshold, FEA adoption checkbox, and Adopt span as Lf controls when straight track is selected; result cards and zero-force FEA trace remain visible.

- COMMERCIAL.LOADS.33: Upgraded 3.8 CR&SH to a minimal-input assistant with RH/age/drying-basis inputs, geometry-derived u_total, V/S and h0 trace, AASHTO unit conversion preview, and Prestress Losses handoff panel.

- COMMERCIAL.LOADS.34: Added CR&SH drying perimeter basis guidance for outer-only versus outer-plus-inner-void drying surfaces and displayed final design age in years while preserving existing derived-geometry and Prestress Losses handoff logic.

- COMMERCIAL.LOADS.35: Added EQ result summary cards, one-source trace, and FEA adoption panel for Cs/EQX/EQY coefficient export while updating bridge R-factor wording to AASHTO LRFD 9th Edition (2020).

- COMMERCIAL.LOADS.36: Polished EQ schema/status display, clarified coefficient-trace FEA adoption and numeric-force ownership, and wrapped the DPT response spectrum in a report-ready canvas figure without changing EQ formulas.

- COMMERCIAL.LOADS.37: Renamed 3.10 to FEA Load Input Summary and upgraded the page into a source-of-truth load handoff table for DL, SDL, LL+IM, LF/HF, CF, Wind, EQ coefficient trace, and CR&SH parameters.


- COMMERCIAL.LOADS.38: Polished 3.10 FEA Load Input Summary as a wrapped commercial handoff sheet with HANDOFF READY status, compact adopted value/basis wording, explicit quantity types, and row-level required FEA actions without changing load formulas.


- COMMERCIAL.LOADS.39: Added a FEA handoff status legend, transfer-control checklist, and print-safe handoff styling for 3.10 FEA Load Input Summary without changing load formulas.

- COMMERCIAL.LOADS.40: Closed the Loads workspace for the current load-source scope by adding a Loads closeout and Report/QA handoff panel to 3.10 FEA Load Input Summary, surfacing the same read-only Loads handoff snapshot in Report / QA, and preserving all load formulas.


- COMMERCIAL.PSLOSS.1: Added a source-gated Prestress Losses input handoff that reads locked adopted tendon data, adopted section properties, CR&SH parameters, and span/stage basis before detailed loss calculation; clarified that jacking force is tendon axial force and must not be doubled for two-end stressing.

- COMMERCIAL.PSLOSS.2: Added a tendon-adoption action panel, blocked prestress-input checklist, and explicit JackFrom / stressing-basis gate so future friction and anchor-set losses can distinguish one-end, two-end, mixed, or missing stressing traces without doubling total jacking force.


- COMMERCIAL.PSLOSS.3: Added an adopted-tendon readiness register, loss-component calculation-readiness register, and Report/QA readiness snapshot so future friction, anchor-set, elastic-shortening, creep/shrinkage, relaxation, and effective-prestress formulas remain source-gated before calculation.

- COMMERCIAL.PSLOSS.4: Reworked 4.2 Friction into a source-gated friction source model that reads only the adopted tendon profile and JackFrom/stressing trace, adds μ/K input trace and tendon-by-tendon preview gating, and keeps preview results out of final effective-prestress adoption.

- COMMERCIAL.TENDON.1: Polish 2.4 Tendon Layout Reference with JackFrom/stressing-basis auto-detection, force-policy trace, QA/adoption readiness rows, and a numeric section-overlay station control to avoid slider dynamic-import instability, without changing tendon geometry or force calculations.
- COMMERCIAL.TENDON.2: Add an explicit visible source note that the stressing basis is auto-detected from the General tendon table · JackFrom field, keeping it as a traced tendon-source value rather than a duplicate Prestress Losses input.

- COMMERCIAL.PSLOSS.5: Add friction formula trace and report-style calculation summary to 4.2 Friction, including variable definitions, governing-tendon walkthrough, tendon-by-tendon Kx/μα/exponent/ΔfpF/fpx trace, and Report/QA snapshot without adopting friction into effective prestress.
- COMMERCIAL.PSLOSS.6: Standardized 4.2 Friction with report-grade equation blocks using `st.latex`, a reusable loss-type result-summary card pattern at the top of the page, and source-gated substitution/result display without changing friction values or effective-prestress adoption.

- COMMERCIAL.PSLOSS.7: Polishes 4.2 Friction report trace by showing governing-tendon ties (for mirrored tendons with equal loss), adding full-tendon row-count notes and display height for tendon-by-tendon report tables, and keeping the PSLOSS.6 equation/summary pattern unchanged for future loss pages.


- COMMERCIAL.PSLOSS.9: Adds a position-dependent 4.3 Anchor Set distribution trace and friction-coupling preview while preserving equivalent anchor-set quick check and keeping final effective-prestress adoption blocked.


- COMMERCIAL.PSLOSS.10: Polishes 4.3 Anchor Set distribution wording and variable trace by separating the equivalent quick check from the position-dependent friction-coupled preview, documenting 2ΔfpF(s), ΔfpA,0, s_a, fpx,F+A(s), and the 1000 m-to-mm compatibility conversion without changing anchor-set results or effective-prestress adoption.

- COMMERCIAL.PSLOSS.11: Adds a source-gated 4.4 Elastic Shortening stage preview using adopted tendon count, Ep/Eci material source, engineer-reviewed f_cgp stage input, report-grade equation blocks, loss-summary cards, variable trace, and tendon-by-tendon sequence audit without adopting elastic shortening into final effective prestress.

- COMMERCIAL.PSLOSS.12: Polishes 4.4 Elastic Shortening summary consistency by separating average ES loss, fpx after average ES, maximum sequence ES loss, and minimum sequence stress; adds sequence-basis review wording while keeping formulas and effective-prestress adoption unchanged.
- COMMERCIAL.PSLOSS.13: Standardizes loss-percent interpretation across 4.2 Friction, 4.3 Anchor Set, and 4.4 Elastic Shortening by adding a shared component-loss / fpj basis note, non-cumulative warning, and report-summary rows without changing formulas or results.

- COMMERCIAL.PSLOSS.14: Cleans up active Prestress Losses headers and 4.1 next-step wording so the closed Friction, Anchor Set, and Elastic Shortening preview pages reflect the shared loss-percent basis standard and the workflow points to 4.5 Time-Dependent Losses next, without changing formulas or results.

- COMMERCIAL.PSLOSS.16–18: Completes the 4.5 Time-Dependent Losses source-gated preview package with a calculation-route selector, refined/time-step factor trace, approximate quick-check comparison, result-summary cards, effective-prestress handoff, editable segment age at transport defaulting to 30 days, editable span assembly duration before stressing, computed representative t_jack, and 3.8 ti reconciliation without adopting final time-dependent losses.
- COMMERCIAL.PSLOSS.20: Polishes 4.5 Time-Dependent Losses selected-age symbol consistency by using t_start for the selected time-step start age in equations, variable traces, and report rows, while retaining computed t_jack only in the construction-stage reconciliation and preserving all creep/shrinkage results.
- COMMERCIAL.PSLOSS.21: Adds a source-gated relaxation preview to 4.5 with method/stress-basis/steel-class selectors, AASHTO R1/R2 equation trace, low-relaxation quick-check comparison, and route-dependent 4.6 handoff while keeping final effective-prestress adoption blocked.

- COMMERCIAL.PSLOSS.22: Renames 4.5 to Time-Dependent Losses and splits the workflow into internal Overview, Creep, Shrinkage, Relaxation, and Handoff to 4.6 tabs while preserving creep, shrinkage, relaxation, route-selection, t_start, and handoff results.

- COMMERCIAL.PSLOSS.23: Polishes the Time-Dependent Losses handoff summary and relaxation wording so relaxation, total time-dependent preview subtotal, and fpx after time-dependent preview are reported consistently before 4.6 without changing formulas or preview values.


- COMMERCIAL.PSLOSS.24: Fixes 4.1 General Prestress Losses source-gate CR&SH handoff compatibility by avoiding direct `state["factors"]` access when the page receives a general/migrated source-gate state; displays SOURCE PARTIAL / REVIEW-compatible CR&SH handoff rows instead of crashing, without changing prestress-loss formulas or preview values.

- COMMERCIAL.UI.PSLOSS.1: Standardizes the 4 Prestress Losses in-page subpage navigation with the horizontal radio pattern used by 3 Loads, keeping sidebar synchronization, component preview source gates, and all prestress-loss formulas/results unchanged.


## COMMERCIAL.UI.PSLOSS.1

- Standardizes the 4 Prestress Losses subpage navigation with an in-page horizontal radio bar matching the 3 Loads workspace pattern.
- Keeps sidebar navigation synchronized with the in-page selector.
- Preserves all Friction, Anchor Set, Elastic Shortening, Time-Dependent Losses, and 4.6 Effective Prestress logic/results.


Previous milestone retained: COMMERCIAL.PSLOSS.25 polished 4.1 General readiness wording and pointed the workflow to 4.6 Effective Prestress.


## COMMERCIAL.UI.BRIDGE.1

- Standardizes the 2 Bridge Geometry / Section Properties subpage navigation with an in-page horizontal radio bar matching the 3 Loads and 4 Prestress Losses workspace pattern.
- Keeps sidebar navigation synchronized with the in-page selector.
- Preserves bridge description, geometry/model assumptions, section-property engine, tendon-layout reference, consistency checks, and QA/report preview logic/results.
- Carries forward COMMERCIAL.UI.PSLOSS.1 and all completed Prestress Losses component preview milestones unchanged.

## COMMERCIAL.UI.BRIDGE.2

- Standardizes the internal 2.3 Section Properties review tabs with the same in-page horizontal radio navigation pattern used by 3 Loads, 4 Prestress Losses, and 2 Bridge Geometry / Section Properties.
- Standardizes the internal 2.4 Tendon Layout Reference review tabs with the same horizontal radio pattern.
- Preserves coordinate import, section preview, adopted section properties, QA/comparison, tendon import/mapping, elevation/plan/3D views, section overlay, adopted tendon data, and tendon QA logic/results unchanged.


Previous milestone retained: COMMERCIAL.UI.HEADER.1 removed the global project/context banner card below the main app header while preserving structured context cards and all app logic/results.

Current milestone focus — COMMERCIAL.UI.SIDEBAR.1
- Remove the PROJECT STATUS diagnostic block from the sidebar so the sidebar focuses on navigation, figure mode, active context, and project JSON loading.
- Remove always-visible QA/DCR/schema cards from the sidebar; those diagnostics remain available from Project Dashboard and Report / QA.
- Preserve the horizontal subpage navigation standardized for Loads, Prestress Losses, and Bridge Geometry.
- Preserve all geometry, tendon-reference, loads, prestress-loss, QA/report, schema migration, and save/load logic/results.

Schema
- 0.4.90-commercial-ui-sidebar1-clean-project-status

## COMMERCIAL.PSLOSS.26A

- Adds a 4.6 Effective Prestress loss audit against the calculation report while keeping the PSLOSS.26 source map and total-loss %fpi preview.
- Flags the representative total loss when it exceeds the internal high-preview threshold and identifies ES + creep as the first f_cgp-driven audit target.
- Adds optional report comparison inputs for immediate F+A, elastic shortening, creep, shrinkage, relaxation, time-dependent subtotal, and total loss as % of fpi.
- Adds app-vs-report comparison rows with App − report delta and MATCH / REVIEW / DIFFERENCE / INPUT PENDING status.
- Adds an f_cgp sensitivity diagnostic that estimates the f_cgp implied by a report total-loss benchmark without changing any design result.
- Replaces fragile LaTeX formula rendering in 4.6 with a print-safe plain formula trace and relabels total loss/fpe cards as representative preview values.
- Adds explicit review gates for station/tendon effective-prestress basis and relaxation-source confirmation.
- Preserves all friction, anchor-set, elastic-shortening, creep, shrinkage, relaxation, save/load, and report logic/results; final fpe adoption remains blocked.

Schema
- 0.4.93-commercial-psloss26a-effective-prestress-loss-audit


## COMMERCIAL.PSLOSS.26B

- Adds a focused high-loss root-cause diagnosis to 4.6 Effective Prestress without changing any prestress-loss calculation or adoption logic.
- Explicitly identifies the current high representative loss as driven by elastic shortening + creep and traces both terms back to the f_cgp stage-stress basis.
- Adds a diagnosis table with source owners and next actions for total loss, ES + creep, f_cgp coupling, immediate F+A, shrinkage/relaxation, and calculation-report benchmark status.
- Adds an f_cgp stage-basis sensitivity sweep that holds F+A, shrinkage, and relaxation fixed and scales only the f_cgp-driven ES + creep block for audit triage.
- Keeps calculation-report comparison inputs and f_cgp back-calculation from PSLOSS.26A; report values are still optional audit benchmarks and do not alter the app result.
- Preserves all friction, anchor-set, elastic-shortening, creep, shrinkage, relaxation, save/load, report, and QA behavior; final fpe adoption remains blocked.

Schema
- 0.4.95-commercial-psloss26c-friction-alpha-gate

## COMMERCIAL.PSLOSS.26C

- Adds a friction α gate so the app no longer treats the merged station-polyline α as automatically eligible for global effective-prestress adoption.
- Computes tendon-by-tendon α directly from the adopted 2.4 vertical and horizontal tendon-layout profiles using the component route αtotal = sqrt(αv² + αh²).
- Compares the 2.4 component α values against the calculation-report tendon-group α benchmark while keeping the report values as a benchmark, not an unverified source of truth.
- Keeps the existing station-polyline / 3D profile friction route visible as a local/distribution diagnostic and flags possible over-counting where station interpolation/control points create nonphysical angular changes.
- Updates 4.6 to use the α-audited equivalent friction plus equivalent anchor-set quick-check as the representative immediate-loss preview, while retaining the local station F+A envelope as diagnostic only.
- Preserves final fpe adoption as REVIEW/BLOCKED until the friction α audit, equivalent anchor-set basis, elastic-shortening sequence, time-step age source, and relaxation source are all closed.

Schema
- 0.4.95-commercial-psloss26c-friction-alpha-gate

## COMMERCIAL.PSLOSS.26D

- Adds a creep report-match audit route for 4.5 Time-Dependent Losses: the selected route now uses BG40-style incremental `Δktd = ktd(tf) − ktd(t_start)` by default, while the former direct-elapsed `ktd(tf − t_start)` route is retained as diagnostic only.
- Exposes selected ψ, report-match ψ, direct-elapsed diagnostic ψ, creep loss delta, and a PSLOSS.26D creep-basis audit table so inflated creep can be traced without hard-coding the report result.
- Updates relaxation to use the BG40 low-relaxation interaction expression `0.30[20.0 - 0.4ΔfpES - 0.2(ΔfpSH + ΔfpCR)]` with negative values capped at `0.0 MPa`; the older AASHTO R1/R2 and 2.4 ksi routes remain visible only as diagnostics/quick checks.
- Preloads the 4.6 App-vs-report benchmark table with BG40 report values for friction, anchor set, elastic shortening, creep, shrinkage, relaxation, total loss, and fpe. These are comparison inputs only and do not drive final adoption.
- Keeps 4.6 Effective Prestress as PREVIEW / REVIEW REQUIRED. The app still does not certify final fpe until friction α, equivalent anchor set, ES sequence, creep route, relaxation basis, and final combination gates are closed.

Schema
- 0.4.96-commercial-psloss26d-creep-relaxation-audit

## COMMERCIAL.PSLOSS.26E

- Changes the friction basis from report-equivalent / mismatch-gated comparison to the engineer-confirmed physical cumulative 3D deviator route. Bend point and physical deviator stations in the adopted 2.4 tendon layout are treated as real tendon direction-change/contact points.
- Uses the physical 3D friction average as the selected 4.6 representative friction component, while retaining the 2D component-alpha route and BG40 report-equivalent alpha only as comparison traces.
- Updates 4.2 Friction cards, alpha audit wording, 4.6 source map, component handoff, driver table, and App-vs-report comparison so the lower report friction value is no longer allowed to override physical tendon geometry.
- Keeps 4.6 Effective Prestress in PREVIEW / REVIEW REQUIRED because ES sequence, time-step age source, relaxation/manufacturer basis, and final report adoption still need engineer sign-off.

Schema
- 0.4.97-commercial-psloss26e-physical-alpha-basis

## COMMERCIAL.PSLOSS.26F

- Adds a dedicated 4.6 CSiBridge final-stage loss input block. The recommended CSiBridge percentage is calculated as the area-weighted average total stress loss divided by fpi/fpj, not from the governing local tendon loss.
- Makes each prestress-loss page show the correct average component %loss handoff basis: average physical 3D friction, average equivalent anchor set, average elastic shortening, and average time-dependent losses. Local maximum/govening tendon values remain visible as diagnostics only.
- Keeps tendon-specific/local loss traces available for QA while clearly separating them from the single global fpe / Pe / CSiBridge lump-sum total-loss input.
- Retains 4.6 as PREVIEW / REVIEW REQUIRED until the remaining ES sequence, t_start, relaxation/manufacturer, and final report adoption gates are signed off.

Schema
- 0.4.98-commercial-psloss26f-csibridge-average-loss-handoff


## COMMERCIAL.PSLOSS.26G

Clean Prestress-Loss Workspace and Collapsed Calculation Trace

Schema:

- 0.4.99-commercial-psloss26g-clean-loss-workspace-trace-collapse

Changes:

- Reorganized 4 Prestress Losses as a design-handoff workspace instead of an audit-heavy workspace.
- Kept each loss page focused on the selected average loss, percent of fpi/fpj, downstream feed status, and CSiBridge/design-use value.
- Moved formula blocks, substitution walkthroughs, tendon-by-tendon tables, report benchmark comparisons, source maps, and diagnostics into collapsed Calculation trace / QA expanders.
- Preserved all engineering formulas and traceability while reducing main-page clutter.
- Kept 4.6 focused on the CSiBridge final-stage total loss percent, fpe, Pe, and component average chain.

## COMMERCIAL.PSLOSS.26H

Auto f_cgp Stage-Stress Source

Schema:

- 0.4.100-commercial-psloss26h-auto-fcgp-stage-stress

Changes:

- Removed the main-page editable `f_cgp` number input from 4.4 Elastic Shortening to prevent accidental manual edits from corrupting ES, creep, and CSiBridge total-loss results.
- Added a read-only `f_cgp` stage-stress source card and trace table on the 4.4 main page.
- Added an advanced-only manual override inside the Calculation trace / QA expander; enabling it marks the stage-stress source as `MANUAL OVERRIDE` and keeps final loss adoption in review.
- Synchronized the selected stage-stress source with the legacy `prestress.fcgp_mpa` key so existing ES and creep formulas continue to use one source of truth.
- Preserved the ES formula, average substitution, and tendon-by-tendon sequence trace in the collapsed QA expander.


## COMMERCIAL.PSLOSS.26I

Final loss status polish and stage-source consistency cleanup.

Changes:

- Locked 4.5 prestress-loss start age to the computed construction-map t_jack by default.
- Renamed Time-step age source to Prestress-loss start age for clearer engineering intent.
- Replaced ambiguous PREVIEW ONLY component cards with ACTIVE IN 4.6 / source-blocked status semantics.
- Changed f_cgp wording from auto-calculated to source-derived/read-only unless a future staged-analysis calculation is wired.
- Recolored average component cards that feed 4.6 as green/pass; diagnostic/local maxima remain orange/warn.
- Replaced Section 4 trace expanders with toggles to reduce PDF glyph artifacts while keeping calculation trace available.

Schema:

- 0.4.101-commercial-psloss26i-final-loss-status-polish

## COMMERCIAL.TENDON.2.4H

Auto-adopted tendon source UX simplification.

Changes:

- Auto-adopts the first valid tendon model as the downstream design source when the imported General / Vertical / Horizontal tables pass source checks and no adopted snapshot exists.
- Hides the redundant Adopt / Re-adopt button when the working model fingerprint already matches the adopted design source.
- Shows a compact “No action required” locked-state message for the normal adopted workflow.
- Adds a changed-working-model state with a concise adopted-vs-working comparison before updating the design source.
- Moves re-adoption controls and Clear adopted tendon source into a collapsed Manage adopted source / QA section; the destructive clear action is now the only red/danger-style action.
- Preserves the tendon source gate so downstream prestress-loss and report checks continue to read only the adopted snapshot, not transient imports.

Schema:

- 0.4.103-commercial-tendon24i-span-source-consistency-polish

## FEA.5B2 visual-integrity polish

- Governing annotations now move inward automatically when the governing point is near the left or right chart edge, preventing label clipping at end cuts.
- FEA station identity is displayed to four decimal places in governing cards, summary tables, chart hover text, and compact/detailed scalar-envelope tables.
- The underlying imported forces, envelopes, source semantics, and downstream-disconnection policy are unchanged.

## Streamlit Cloud native-crash guard

- Production pandas is pinned to `2.3.3` (Python 3.14 compatible).
- `pd.options.future.infer_string = False` is set immediately after importing pandas.
- This avoids pandas 3.x automatic Arrow-backed string inference, the exact native path shown in the Streamlit Cloud crash log (`pandas.core.arrays.string_arrow` → `pyarrow.libarrow`).
- Plotly remains pinned to `5.24.1`.
