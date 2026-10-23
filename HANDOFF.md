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

---

# Handoff addendum (session 4): Modular Overhead & Underground Impedance, Thermal Ampacity, and Unified Branch Consolidation

**Branch:** `gemini/modular-refactor` (pushed to `origin/gemini/modular-refactor`).  
**PR:** https://github.com/KupipiKuki/Power_Systems_Python/pull/new/gemini/modular-refactor  
**Merged Sources:**
- `origin/vibe/powercad-refactor` (includes all 10 commits from `origin/vibe/polecad-refactor-c349b2`)
- `origin/testing` (underground cable calculator)

**State:** all work committed and pushed; working tree clean; automated pytest suite passing 11/11 tests; all 7 legacy verification scripts passing.

---

## 1. What was done (this session)

### a) `pc_classes/overhead_lines.py` — NEW standalone module
Extracted overhead line impedance and capacitance calculations into a pure mathematical module independent of Pandas DataFrame schemas and disk CSV file I/O:
- **`OverheadLineImpedance`**:
  - Implements Carson's equations with frequency-scaled earth return resistance $r_d = 1.588 \times 10^{-3} \cdot f$ and reactance coefficient $\omega_{\text{scale}} = 2.0224 \times 10^{-3} \cdot (f / 60)$.
  - Generalized Kron reduction for arbitrary $M$ neutral and shield conductors ($[Z_{abc}] = [Z_{pp}] - [Z_{pn}] [Z_{nn}]^{-1} [Z_{np}]$).
  - True matrix symmetrical component sequence transformation using `@`: $Z_{012} = \mathbf{A}^{-1} [Z_{abc}] \mathbf{A}$. Supports both untransposed and transposed configurations.
- **`OverheadLineCapacitance`**:
  - Implements Maxwell potential coefficient matrix $[P]$ inversion to shunt capacitance matrix $[C]$ and sequence charging susceptance matrix $[Y_{012}]$ (first time in codebase; previously missing).
- **Dataclasses**: `OverheadConductor`, `ConductorPosition`, `OverheadGeometry`, `LineImpedanceResult`, `LineAdmittanceResult`.

### b) `pc_classes/underground_cables.py` — full overhaul & bug fixes
Overhauled the underground cable calculator brought in from branch `testing`:
- **Defect T-1 (Matrix Multiplication) FIXED**: Replaced Hadamard element-wise multiplication `*` with matrix product `@` in sequence transformation (`zseq = np.linalg.inv(A) @ zabc @ A`). Eliminates the 67% error in zero-sequence impedance.
- **Defect T-2 (Negative Capacitance / Unit Mismatch) FIXED**: Unified all spatial dimensions ($R_{dc}, R_{ds}, R$) strictly to feet before evaluating $\ln(R / R_{dc})$. Eliminates the negative logarithm bug, guaranteeing strictly positive physical capacitance ($C_{pg} = 1.997 \times 10^{-7}\text{ F/mi} > 0$).
- **Defect T-3 (GMR vs De Unit Mismatch) FIXED**: Converted conductor diameter and strand diameter to feet for GMR calculation, matching $D_e$ units and eliminating ~25% error in self-reactance.
- **Defect T-4 (Sequence Extraction) FIXED**: Extracted sequence impedances directly from diagonal elements ($Z_0 = Z_{012}[0,0], Z_1 = Z_{012}[1,1], Z_2 = Z_{012}[2,2]$) instead of non-standard row-summation.
- **Dataclasses**: Added `CableImpedanceResult` and `CableCapacitanceResult` while maintaining full backward-compatibility with existing class methods.

### c) `pc_classes/thermal_ampacity.py` — NEW standalone module
Extracted IEEE 738 steady-state heat balance and temperature-corrected resistance from `powercad.py:calcCurrent()`:
- **`calculate_conductor_ampacity()`**: Computes convective heat loss ($q_c$), radiated heat loss ($q_r$), solar heat gain ($q_s$), temperature-corrected AC and DC resistances ($R_{ac}, R_{dc}$), and maximum continuous current capacity ($I_{\text{max}}$).
- **Dataclasses**: `AmpacityEnvironment` and `ThermalRatingResult`.

### d) `pc_classes/powercad.py` — decoupling & delegation
- **Finding B-3 FIXED (Constructor Decoupling)**: Modified `faultCalculationClass.__init__(self, config=None)`. Calling with zero arguments initializes transformation matrices and lookup curves, enabling pure calculation methods (`xfmr`, `ifault`, `calcVoltageDrop`, `xrcalc`) to execute standalone without requiring project directories, CSV files, or mock DataFrames.
- **Ampacity Delegation**: Delegated `_conductor_ampacity` directly to `thermal_ampacity.calculate_conductor_ampacity()`.

### e) Automated unit test harness (`tests/`)
Created standard pytest test suite (`uv run --with pytest pytest tests/`):
- `tests/test_thermal_ampacity.py` (4 tests: ACSR ampacity, temperature rise resistance scaling, wind cooling effects, Copper conduction model).
- `tests/test_underground_cables.py` (4 tests: strictly positive capacitance across all catalog cables, trefoil custom neutral capacitance, true matrix sequence transformation, diagonal extraction).
- `tests/test_overhead_lines.py` (3 tests: Carson's series impedance, Kron reduction, Maxwell potential shunt admittance/charging susceptance, single-phase loop impedance).
- **Result**: All 11 unit tests pass (`11 passed in 0.37s`).

---

## 2. What needs to be implemented (immediate next steps)

1. **GUI Facade Integration (`gui/services/impedance.py`)**:
   - Wire `OverheadLineImpedance` and `CableImpedance` directly into the facade API (`overhead_line_impedance()` and `underground_cable_impedance()`) so GUI and client scripts can compute line and cable parameters without configuring pole projects.
   - Address remaining Phase 0 Audit blocking facade findings:
     - **Finding B-1**: Correct row extraction for LL (`iabc[4,0]` / `iabc[5,0]`) and LLG (`iabc[7,0]` / `iabc[8,0]`) in `fault_currents()`.
     - **Finding B-2**: Fix factor of 3 and scalar/complex subtraction in `source_impedance()` SLG loop.
2. **Wire Radius/X into `powercad` GMD calcs**:
   - Wire `Radius` and `X` columns from construction tables into `powercad.py`'s assembly resolver (using the GMD calculation matrix from `General Notes.txt` - currently dead data).
3. **Automate legacy script regression into `tests/`**:
   - Port `spantest.py`, `test1.py`, `test14400.py`, `temptest1.py`, and `temptest2.py` into golden pytest test cases comparing `PoleResults/*.csv` and `condfcc.csv` against committed fixtures.

---

## 3. What remains from initial refactors (flagged debt & pending decisions)

### a) From `vibe/polecad-refactor-c349b2` (PR #1)
- **Git Repository Bloat**: `UEP_Bulletin_1728F-804.pdf` was committed directly into git in commit `81640f3` as **58,405 plain text lines**. Needs `.gitattributes` binary marking or Git LFS tracking before merging to `main`.
- **`DATA_AUDIT.md` Discrepancies**:
  - `A6.22` (drawing vs CSV discrepancy).
  - `B1.15,B2.25` pairing (B1.15 missing from bulletin).
  - `B1.14,B2.24` pairing mismatch.
  - Combined `C5.21L/C5.31L` row (separate large-conductor drawing).
  - `G`-suffix guide entries (`C6.52G/C6.53G`).
- **14.4 kV Audit**: Verify V-prefix drawings in Bulletin 804 against `14400_A/B/C/D.csv`.

### b) From `vibe/powercad-refactor` (PR #2 / `POWERCAD_AUDIT.md` items A1–A9)
- **A1 (Single-Phase Line Impedance)**: Legacy formula assumes 1 ft neutral spacing; combined rows (`A5.01`) carry no neutral geometry in CSVs.
- **A2 (Frequency Scaling)**: Reactance coefficient `_W60 = 2.0224e-3` hardcoded for 60 Hz in legacy `calcImpedance` (fixed in `overhead_lines.py`, legacy path kept as-is for baseline matching).
- **A3 (Fault Sequence Current Dividers)**: LLG sequence current divider inverted ($I_0 = -I_1 \frac{Z_{0t}}{Z_t + Z_{0t}}$); 3PH fault includes $Z_{\text{gnd}}$ in positive sequence path.
- **A4 (SLG Denominator)**: Assumes $Z_2 = Z_1$.
- **A5 (`xrcalc` Low Multipliers)**: Inverted range (`2 - 1.677 = 0.323`).
- **A6 (Copper Type 1 Resistance)**: Legacy path does not re-scale to operating temperature ($T_{\text{amb}} + T_{\text{rise}}$) (fixed in `thermal_ampacity.py`).
- **A7 (`calcVoltageDrop`)**: Applies $\sqrt{3}$ line-to-line approximation to per-phase drop.
- **A8 (Transformer Zero-Sequence Default)**: Assumes $Z_0 = Z_1$ instead of core-type distribution transformer $Z_0 \approx 0.85 Z_1$.
- **A9 (Kron Reduction Transposition)**: Legacy uses `0.33/0.33/0.33` circulating factor (`fmat`) assuming transposition. `overhead_lines.py` supports both untransposed and transposed modes.

