# Handoff: Power_Systems_Python — polecad refactor & RUS data verification

**Repo:** `KupipiKuki/Power_Systems_Python` (branch `vibe/polecad-refactor-c349b2`)
**PR:** https://github.com/KupipiKuki/Power_Systems_Python/pull/1 (OPEN, draft)
**State:** all work committed and pushed; working tree clean; both example projects run green.

---

## 1. What was done (this session)

### a) `pc_classes/polecad.py` — full refactor (was 930-line naive pandas code)
- **New API**: `PoleCalcConfig` dataclass + `poleCalculationClass(config).run(plot_format=None)` / `run_max_span()`. Replaces 11-positional-arg `poleLaunch`/`spanLaunch`.
- **Explicit failures** (user chose NO backward compatibility): typed exception hierarchy — `PoleCalcError`, `MissingColumnError`, `UnknownAssemblyError`, `UnknownConductorError`, `InvalidGuyDataError`. Bad input raises with the offending row in the message; no silent defaults.
- **Bugs fixed**: `'Guyy'/'Guyx'` typos (GuyType 2/6 paths), comms-guy accumulation writing `Mgx` instead of `Mcgx`, `==False | override` precedence, `assign(MaxSpan=np)`, pandas-3 string-dtype write-back on GuyHeight, `xs(drop_level=False)` for guy lookups.
- **Performance**: deduped A/B/C assembly lookup (one `_find_assembly`), GuyType 3/4/5 collapsed to slope-ratio dict, vectorized conductor/comm moments.

### b) `pc_classes/poleplotter.py` — new module
- All plotting/summary extracted: `polePlotterClass(project_name, config)` with `pole_summary()`, `build_summary()`, `plot_poles()`.
- `polecad` no longer imports matplotlib at module level (lazy import only when plotting). Uses Agg backend (headless-safe).

### c) Voltage families (`voltage_family` config field)
- `datafunctions.generate_pole_construction()` loads ALL CSVs in `pc_data/Construction/` dynamically.
- `PoleCalcConfig.voltage_family` ∈ {`'7200'`, `'14400'`, `'34500_46000'`, `'69000'`} scopes assembly lookup; ambiguous cross-table matches raise.
- Phase slots generalize to `Phase1..6Hin` (neutral fallback), guys to `GuyH1..6` (GuyH1 fallback) — 6-phase double-circuit `14400_D` (VD1.8x) works.
- New example: `test14400.py` + `PoleCadTests/Test14400/` (VA assemblies, verified end-to-end).

### d) Data infrastructure fixes
- `datafunctions.py`: package-relative `pathlib` paths (CWD-independent), `np.mat`→`np.asmatrix`, `np.NaN`→`np.nan` (NumPy 2.0 compat; also in `powercad.py`).

### e) RUS data verification
- **`DATA_AUDIT.md`** (in `pc_data/Construction/`): audit of `7200_A/B/C.csv` against Bulletin 1728F-804 (April 2005). Method: extracted text-layer pages with pypdf; OCR'd drawing-page title blocks (drawings are vector-traced, no text layer) to build a complete page→assembly map (pages 15–199).
- **Confirmed**: numbering format (Exhibit 5), V-prefix = 14.4kV, all 231 CSV pairings map to real drawings, spot-checks of A1.1/C1.11 families.
- **Discrepancies flagged for user review**: `A6.22` (only A6.2/A6.22G exist), `B1.15,B2.25` pairing (B1.15 not in bulletin), `B1.14,B2.24` pairing mismatch, combined `C5.21L/C5.31L` row (separate large-conductor drawing), `C6.52G/C6.53G` (G = guide drawings, no materials).
- Numeric Hin/GuyH values NOT verified digit-by-digit (OCR too unreliable on traced text) — needs human/CAD overlay.

### f) `profile_reconstructor.py` — NEW verification tool (in `pc_data/Construction/`)
Rebuilds pole-top profiles as R12 DXF from construction CSV rows, for visual verification against RUS drawings:
- **Datum**: pole top y=0, down is negative; attachment X/Y are **centerline (z-axis) based — pole diameter never enters coordinates** (crossarm is fixed-width).
- Draws: pole outline (true diameter from `PoleData` circumference tables via `--species/--pole-class/--pole-height`; generic fallback), crossarm, **insulator hardware** per `General Notes.txt` (post/pin/spool by voltage family + `P` suffix), conductor/neutral circles, guy leads, vertical dimensions.
- Insulator table encoded: 7200: post 12", pin 4"+5"=9", spool 1-1/16"; 14400: post 14", pin 10", spool 1-1/2"; 34500: post 16", pin 12.5"; 46000: 20"; 69000: 26". **CSV Hin values already bake these in** (A1.1=9, A1.1P=12, VA1.1=10, VA1.1P=14 — verified).
- CLI: `python profile_reconstructor.py 7200_C.csv "C1.11,C2.21" -o out.dxf` | `--list` | `--all ... -o dir`
- Uses `minicad_dxf.py` (user-provided headless R12 DXF library; self-tests pass; round-trips with MiniCAD editor, opens in AutoCAD/LibreCAD).

---

## 2. Key architecture facts for the next session

- **What `polecad` consumes from construction tables**: ONLY `Phase*Hin`/`NeutralHin` (conductor heights) and `GuyH*` (guy heights). `Radius`/`X` columns are NOT consumed by any code yet — they exist for GMD/impedance work (see `General Notes.txt` GMD matrix; wiring them into `powercad` is a candidate next task).
- **GMD Calculation Matrix** in `General Notes.txt` defines phase-pair distance groups for impedance calcs (AB,BC,AC),(AN,BN,CN),... — currently unimplemented.
- Input CSVs (`poledb/conddb/guydb/commdb/cguydb.csv`) are indexed on `['StudyPoleTag','PoleTag','PoleNumber']`; `commdb`/`cguydb` optional (empty frames created if absent).
- Study pole row must exist at `(StudyPoleTag, StudyPoleTag, 0)` — raises otherwise.
- `conddb` `DesignTension` column optional (defaults to config value); `Height` resolved from assembly tables if absent.
- Tests: no test suite. Verification = running `spantest.py`, `test1.py`, `test14400.py` against `PoleCadTests/` datasets and checking `PoleResults/*.csv`.

## 3. Environment

- Python 3.12, pandas 3.0.6, numpy 2.5.4, matplotlib 3.11.2, scipy, openpyxl (WoodPoles.xlsx), pypdf/pymupdf/easyocr (installed for PDF audit; OCR needs ~2GB RAM per process — batch jobs get OOM-killed, run page-by-page).
- `gh` CLI authenticated. Remote push to the vibe branch is fine; `main` not touched.
- Bulletins in `pc_data/Construction/`: 1728F-803 (telecom), 804 (12.47/7.2kV), 810 (34.5/46kV), 811 (69kV).

## 4. Suggested next steps

1. **Resolve DATA_AUDIT.md discrepancies** (user review pending): A6.22, B1.15/B1.14 pairings, C5.21L combined row, G-suffix guide entries.
2. **Overlay verification workflow**: render `--all 7200_X.csv -o dir`, overlay DXFs on RUS drawing pages in CAD, log divergences (wrong assumed constants vs. wrong CSV values). Optional: `--json` export of assumed dimensions per assembly for auditability.
3. **Wire Radius/X into `powercad` GMD calcs** per the General Notes matrix (currently dead data).
4. **14.4kV audit** vs the V-prefix drawings in bulletin 804 (same OCR method; page map already built — `/tmp/page_map.json` was session-local, regenerate if needed).
5. Consider a real test suite (golden-file comparison of `PoleResults/*.csv`).
6. PR #1 is draft — review/merge decision pending with the user.

---

# Handoff addendum (session 3): powercad refactor

**Branch:** `vibe/powercad-refactor` (off `vibe/polecad-refactor-c349b2`).
`pc_classes/powercad.py` refactored in the polecad style:

- New API: `PowerCalcConfig` dataclass + `faultCalculationClass(config).run()`
  (replaces `calcImpedanceLaunch`/`calcVoltDropLaunch`; loads poledb/conddb,
  runs `calcCurrent` + `calcImpedance`, writes `condfcc.csv`).
- Typed exceptions (`PowerCalcError` hierarchy), no silent defaults; assembly
  lookup scoped by `voltage_family` with a single shared `_find_assembly`.
- Bugs fixed: spacing formula `+` vs `-` (F1), conddb Span ft-as-miles (F2),
  B-table AltName fallback (F3), wrong per-section span (F4), pandas-3 int
  Span crash (F5). Details + every suspect-but-unchanged calculation in
  **`POWERCAD_AUDIT.md`** (items A1–A9) — user chose "refactor + flag";
  A-items await the user's revised calculation documentation.
- Consumers updated: `temptest1.py`, `temptest2.py`, `test1.py`,
  `xfmrTest.py`, `VoltageDropTest.py`; `condfcc.csv` baselines regenerated.
- Verified: all example scripts run clean on pandas 3.0.6/numpy 2.5.4;
  unchanged quantities (CurrentCalc, OhmsCalc, GMR...) match legacy baselines;
  changed quantities trace to F1/F2/F4 and were sanity-checked against
  construction CSV geometry.
