# Consolidated Issue Tracker

**Branch:** `major-refactors`
**Last Updated:** 2026-10-24
**Sources:** `POWERCAD_AUDIT.md`, `DATA_AUDIT.md`, `docs/audit/phase0_gemini_audit.md`, `HANDOFF.md`

---

## Legend

| Priority | Meaning |
|----------|---------|
| **P0** | Blocking — must fix before any GUI work or production use |
| **P1** | High — mathematical correctness, affects calculation results |
| **P2** | Medium — code quality, maintainability, missing features |
| **P3** | Low — documentation, nice-to-have, future work |

| Status | Meaning |
|--------|---------|
| `OPEN` | Not started |
| `IN_PROGRESS` | Being worked on |
| `BLOCKED` | Waiting on user input/decision |
| `RESOLVED` | Fixed and verified |
| `DEFERRED` | Intentionally postponed |

---

## P0 — Blocking Issues

### P0-1: LLG Fault Current Divider (Audit A3 / NB-5)
- **Source:** `POWERCAD_AUDIT.md` A3, `phase0_gemini_audit.md` NB-5
- **Location:** `pc_classes/powercad.py:447-454` (`ifault` method, BC-G branch)
- **Issue:** The LLG sequence current divider is inverted:
  - Code: `I0 = -I1 * (z0t / (zt + z0t))`, `I2 = -I1 * (zt / (zt + z0t))`
  - Correct: `I0 = -I1 * (Z2 / (Z1 + Z2))`, `I2 = -I1 * (Z1 / (Z1 + Z2))` — with Z1=Z2=zt, this gives I0 = I2 = -I1/2 (symmetric)
  - The code's formula swaps the roles: it assigns I0 proportional to Z0 and I2 proportional to Z1, which is backwards
  - Additionally, zfault and zgnd are accounted for in I1 but dropped from the I0/I2 divider
- **Impact:** LLG fault currents are wrong. The faulted-phase current magnitude |Ib| may still be approximately correct because it depends primarily on I1, but the ground return current Ig = 3*I0 is wrong.
- **Correct Formula (standard symmetrical components for LLG):**
  ```
  I1 = Vf / ((Z1 + Zf/2) + (Z1 + Zf/2)(Z0 + Zf/2 + 3Zg) / (Z1 + Z0 + Zf + 3Zg))
  I0 = -I1 * (Z1 + Zf/2) / (Z1 + Z0 + Zf + 3Zg)
  I2 = -I1 * (Z0 + Zf/2 + 3Zg) / (Z1 + Z0 + Zf + 3Zg)
  ```
- **Status:** OPEN
- **Note:** `overhead_lines.py` and the new modular engines have correct implementations. This is the legacy `powercad.ifault()` path.

### P0-2: 3-Phase Fault Includes Zgnd in Positive-Sequence Path (Audit A3)
- **Source:** `POWERCAD_AUDIT.md` A3
- **Location:** `pc_classes/powercad.py:503` (`ifault` method, 3PH branch)
- **Issue:** `I1 = vf / (zt + zfault + zgnd)` — `zgnd` should NOT be in the 3-phase fault positive-sequence path
- **Correct:** `I1 = vf / (zt + zfault)` for a 3-phase fault (ground impedance doesn't affect balanced 3PH faults)
- **Impact:** 3-phase fault currents are understated when zgnd > 0
- **Status:** OPEN

### P0-3: Single-Phase Impedance — Assumed 1 ft Neutral Spacing (Audit A1)
- **Source:** `POWERCAD_AUDIT.md` A1
- **Location:** `pc_classes/powercad.py:432-436` (`calcImpedance`, LineType 1 branch)
- **Issue:** `zkn = resd + 1j * w * f * log(De / 1.0)` — hardcoded 1 ft phase-neutral distance
- **Impact:** Single-phase line impedances are not physically meaningful. The neutral geometry from construction CSVs is not used.
- **Options:**
  1. Wire the actual NeutralX/NeutralHin geometry from construction tables (preferred)
  2. Document the limitation and require users to use `overhead_lines.py` for single-phase calcs
- **Status:** BLOCKED — needs user decision on approach

---

## P1 — High Priority (Mathematical Correctness)

### P1-1: Frequency Scaling of Reactance Coefficient (Audit A2)
- **Source:** `POWERCAD_AUDIT.md` A2
- **Location:** `pc_classes/powercad.py:349-350` (`calcImpedance`)
- **Issue:** `w = _W60` (2.0224e-3) is the 60 Hz constant. `resd` is scaled by `f/60` but `w` is not. At non-60 Hz frequencies, the reactance term is inconsistent.
- **Correct:** `w = 2.0224e-3 * (f / 60.0)` (matching `overhead_lines.py`)
- **Also:** `De` should scale with frequency: `De = 2160 * sqrt(rho / f)`
- **Impact:** Only affects non-60 Hz studies. Currently only 60 Hz is exercised.
- **Status:** OPEN
- **Note:** `overhead_lines.py` already implements this correctly.

### P1-2: xrcalc "low" Multipliers Inverted (Audit A5)
- **Source:** `POWERCAD_AUDIT.md` A5
- **Location:** `pc_classes/powercad.py:549-555` (`xrcalc`, 'low' branch)
- **Issue:** `results='low'` multiplies by `(2 - 1.677) = 0.323`, `(2 - 1.5) = 0.5`, `(2 - 1.3) = 0.7`
- **Comparison:** `'high'` multiplies by 1.677, 1.5, 1.3; `'rlow'` uses `1 - abs(1 - N(1, sigma))`
- **Analysis:** The 'low' multipliers (0.323, 0.5, 0.7) are far below the curve, while 'high' (1.677, 1.5, 1.3) is above. This asymmetry suggests the 'low' formula was meant to be `1/1.677 = 0.596`, `1/1.5 = 0.667`, `1/1.3 = 0.769` — or symmetric bounds around 1.0.
- **Impact:** 'low' mode produces unrealistically low X/R ratios (more resistive than the GE curve suggests)
- **Status:** OPEN — needs user confirmation of intended bounds

### P1-3: Copper (Type 1) Resistance Not Scaled to Operating Temperature (Audit A6)
- **Source:** `POWERCAD_AUDIT.md` A6
- **Location:** `pc_classes/powercad.py` (`calcCurrent` / `_conductor_ampacity`)
- **Issue:** For Copper (ConductorType=1), `resdc` is computed at 75°C but `resac` is never re-scaled to the actual operating temperature (`tempamb + temprise`). Type 3 (ACSR) does scale correctly.
- **Impact:** Copper conductor ampacity and resistance values are wrong at temperatures other than 75°C
- **Status:** OPEN
- **Note:** `thermal_ampacity.py` already has the correct implementation — needs to be wired into the legacy path or the legacy path deprecated.

### P1-4: Voltage Drop √3 Approximation (Audit A7)
- **Source:** `POWERCAD_AUDIT.md` A7
- **Location:** `pc_classes/powercad.py:621-630` (`calcVoltageDrop`)
- **Issue:** Uses exact-form per-phase drop `sqrt(vs² - ...)` then multiplies by √3 for 3-phase
- **Standard formula:** `V_drop = √3 · I · (R·cos(φ) + X·sin(φ))` for line-to-line 3-phase
- **Impact:** Approximation may differ from standard formula by a few percent
- **Status:** OPEN — needs mathematical analysis (see THEORY_ANALYSIS.md)

### P1-5: SLG Fault Denominator Assumes Z2 = Z1 (Audit A4)
- **Source:** `POWERCAD_AUDIT.md` A4
- **Location:** `pc_classes/powercad.py:452` (`ifault`, SLG branch)
- **Issue:** `vf / (z0t + zt + zt + zfault + 3*zgnd)` — the `zt + zt` assumes Z1 = Z2
- **Standard:** `vf / (z1 + z2 + z0 + zfault + 3*Zg)` — correct when Z1 = Z2 (true for lines/transformers)
- **Impact:** None for standard equipment, but naming is confusing (`zt` doubles as Z1 and Z2)
- **Status:** OPEN — documentation/clarity issue, not a math bug

### P1-6: Transformer Zero-Sequence Default (Audit A8)
- **Source:** `POWERCAD_AUDIT.md` A8
- **Location:** `pc_classes/powercad.py:523` (`xfmr`)
- **Issue:** `xfmr(..., zeromult=1)` assumes Z0 = Z1 by default
- **Standard:** Core-type distribution transformers: Z0 ≈ 0.85·Z1; Shell-type: Z0 ≈ Z1
- **Note:** `distxfmr` table in `dataconstants.py` has per-size data but is unused
- **Status:** OPEN — needs user decision on default zeromult

### P1-7: Kron Reduction Assumes Full Transposition (Audit A9)
- **Source:** `POWERCAD_AUDIT.md` A9
- **Location:** `pc_classes/powercad.py:365-368` (`calcImpedance`, 3-phase branch)
- **Issue:** Uses `fmat = [[0.33, 0.33, 0.33], ...]` — circulating factor assumes full transposition
- **Note:** `overhead_lines.py` supports both transposed and untransposed modes
- **Impact:** Standard practice for distribution; acceptable but should be documented
- **Status:** OPEN — documentation + consider using `overhead_lines.py` instead

### P1-8: DATA_AUDIT Discrepancies — Assembly Data (DATA_AUDIT.md)
- **Source:** `DATA_AUDIT.md`
- **Issues:**
  1. `A6.22` — only A6.2/A6.22G exist in bulletin (likely typo for A6.2)
  2. `B1.15,B2.25` pairing — B1.15 not in bulletin
  3. `B1.14,B2.24` pairing — B1.14 is "single support, neutral on crossarm", not tangent double support
  4. `C5.21L/C5.31L` — combined row mixes standard and large-conductor variants
  5. `C6.52G/C6.53G` — G suffix = guide drawings (no materials), shouldn't be used as assemblies
- **Status:** BLOCKED — needs user review against RUS bulletins

---

## P2 — Medium Priority (Code Quality / Features)

### P2-1: Wire Radius/X into powercad GMD Calculations
- **Source:** HANDOFF session 1, session 4
- **Issue:** Construction CSV `Radius` and `X` columns are dead data — not consumed by any code
- **Opportunity:** Use actual conductor positions for GMD-based impedance calculations instead of the simplified AB/BC/CA distances
- **Reference:** `General Notes.txt` GMD Calculation Matrix (currently unimplemented)
- **Status:** OPEN

### P2-2: Automate Legacy Script Regression into pytest
- **Source:** HANDOFF session 4
- **Issue:** `spantest.py`, `test1.py`, `test14400.py`, `temptest1.py`, `temptest2.py` run as standalone scripts, not in CI
- **Opportunity:** Port to golden pytest cases comparing `PoleResults/*.csv` and `condfcc.csv` against committed fixtures
- **Status:** OPEN

### P2-3: Deprecate Legacy powercad calcImpedance in Favor of overhead_lines.py
- **Source:** This analysis
- **Issue:** `powercad.calcImpedance()` duplicates functionality now in `overhead_lines.py` with known bugs (A1, A2, A9)
- **Opportunity:** Refactor `powercad.calcImpedance()` to delegate to `OverheadLineImpedance` using construction CSV geometry
- **Status:** OPEN

### P2-4: 14.4 kV Audit vs V-Prefix Drawings
- **Source:** HANDOFF session 1
- **Issue:** `14400_A/B/C/D.csv` not audited against Bulletin 804 V-prefix drawings
- **Status:** OPEN

### P2-5: GUI Facade — Remove np.mat Monkey-Patch
- **Source:** `phase0_gemini_audit.md` NB-4
- **Location:** `gui/services/impedance.py:20-21`
- **Issue:** `np.mat = np.asmatrix` shim at import time
- **Note:** `datafunctions.py` already uses `np.asmatrix` directly; shim is harmless but should be removed once confirmed unnecessary
- **Status:** OPEN

### P2-6: Legacy calcCurrent Ampacity Constants (Audit A6)
- **Source:** `POWERCAD_AUDIT.md` A6
- **Issues:**
  - `wsbase` hardcodes 100 W/ft² solar
  - `wr` uses 0.138 emissivity product with hardcoded factor
  - `currentbase = sqrt(37.7 · d · powerloss / resac)` — the 37.7 constant embeds unit conversions
- **Action:** Verify against IEEE 738-2012
- **Status:** OPEN

### P2-7: Code Duplication — _find_assembly in polecad and powercad
- **Source:** This analysis
- **Location:** `pc_classes/polecad.py:156` and `pc_classes/powercad.py:268`
- **Issue:** Nearly identical assembly lookup logic duplicated
- **Opportunity:** Extract to shared utility module
- **Status:** OPEN

### P2-8: curvegenerator.py and faultgenerator.py Not Refactored
- **Source:** This analysis
- **Issue:** `pc_classes/curvegenerator.py` (356 lines) and `pc_classes/faultgenerator.py` (212 lines) still use legacy patterns
- **Status:** OPEN

---

## P3 — Low Priority (Documentation / Future)

### P3-1: Document All Calculation Assumptions
- **Source:** This analysis
- **Action:** Create `docs/CALCULATION_REFERENCE.md` documenting every formula, constant, and assumption
- **Status:** OPEN

### P3-2: Add Type Hints Throughout
- **Source:** This analysis
- **Status:** OPEN

### P3-3: Profile Reconstructor — JSON Export
- **Source:** HANDOFF session 1
- **Issue:** Optional `--json` export of assumed dimensions per assembly for auditability
- **Status:** OPEN

### P3-4: 34.5/46kV and 69kV Data Audits
- **Source:** HANDOFF session 1
- **Issue:** `34500_46000.csv` and `69000.csv` not audited against Bulletins 810/811
- **Status:** OPEN

### P3-5: TCC (Time-Current Curve) Module Review
- **Source:** This analysis
- **Issue:** `coordtcc.py`, `testtcc.py`, `pc_classes/curvegenerator.py` — TCC curve generation not reviewed
- **Status:** OPEN

---

## Resolved Issues (for reference)

| ID | Issue | Resolution |
|----|-------|------------|
| F1 | Phase-spacing formula `+` vs `-` | FIXED in powercad refactor |
| F2 | conddb Span ft-as-miles | FIXED in powercad refactor |
| F3 | B-table AltName fallback | FIXED in powercad refactor |
| F4 | Wrong per-section span | FIXED in powercad refactor |
| F5 | Pandas-3 compatibility | FIXED in powercad refactor |
| T-1 | Underground cable matrix multiplication | FIXED in underground_cables overhaul |
| T-2 | Negative capacitance / unit mismatch | FIXED in underground_cables overhaul |
| T-3 | GMR vs De unit mismatch | FIXED in underground_cables overhaul |
| T-4 | Sequence extraction from rows | FIXED in underground_cables overhaul |
| B-1 | LL/LLG faulted-phase extraction (facade) | FIXED in gui-impedance branch |
| B-2 | SLG loop factor-3 + complex subtraction (facade) | FIXED in gui-impedance branch |
| B-3 | Constructor signature drift | FIXED — config=None default |
| GIT-1 | PDF bloat (58K text lines) | FIXED — .gitattributes binary marking |

---

## Summary Counts

| Priority | Open | Blocked | Resolved |
|----------|------|---------|----------|
| P0 | 2 | 1 | 0 |
| P1 | 6 | 2 | 0 |
| P2 | 8 | 0 | 0 |
| P3 | 5 | 0 | 0 |
| **Fixed** | — | — | 13 |
| **Total** | **21** | **3** | **13** |
