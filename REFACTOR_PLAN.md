# Refactor Implementation Plan

**Branch:** `major-refactors`
**Created:** 2026-10-24
**Goal:** Address all issues from audits, QAQC, and handoff; perform full mathematical analysis; prepare for GUI development

---

## Overview

This plan is organized into **phases**. Each phase has clear entry/exit criteria. Do not proceed to the next phase until the current phase is complete and verified.

**References:**
- `ISSUES.md` — Consolidated issue tracker (P0/P1/P2/P3)
- `THEORY_ANALYSIS.md` — Mathematical theory analysis
- `POWERCAD_AUDIT.md` — Original powercad audit (A1-A9, F1-F5)
- `DATA_AUDIT.md` — RUS bulletin data audit
- `docs/audit/phase0_gemini_audit.md` — Gemini Phase 0 audit
- `HANDOFF.md` — Session handoffs

---

## Phase 0: Foundation (Current State Assessment)

**Goal:** Establish baseline — all tests pass, all issues documented.

### Tasks
- [x] Consolidate all branches into `major-refactors`
- [x] Create `ISSUES.md` — consolidated issue tracker
- [x] Create `THEORY_ANALYSIS.md` — mathematical analysis
- [x] Create `REFACTOR_PLAN.md` — this document
- [ ] Verify baseline: 51 tests pass, 7 legacy scripts pass
- [ ] User adds new document with further issues (expected tomorrow)

### Exit Criteria
- All tests green
- All known issues documented in ISSUES.md
- User's new document reviewed and incorporated

---

## Phase 1: Critical Math Fixes (P0)

**Goal:** Fix all blocking mathematical errors that affect calculation correctness.

**Estimated scope:** 3-5 issues, ~200-400 lines changed

### Tasks

#### 1.1 Fix LLG Fault Current Divider (P0-1 / A3 / NB-5)
- **File:** `pc_classes/powercad.py` (`ifault` method, lines ~447-454)
- **Change:** Replace the inverted I0/I2 divider with the correct formula:
  ```python
  # Current (WRONG):
  I012 = [[-I1 * (z0t / (zt + z0t))],
          [I1],
          [-I1 * (zt / (zt + z0t))]]
  
  # Correct:
  z1f = zt + zfault / 2
  z0f = z0t + zfault / 2 + 3 * zgnd
  z_loop = zt + z0t + zfault + 3 * zgnd
  I0 = -I1 * z1f / z_loop
  I2 = -I1 * z0f / z_loop
  I012 = [[I0], [I1], [I2]]
  ```
- **Tests:** Update `tests/golden/test_ifault_golden.py` with correct expected values
- **Verification:** Compare against hand-calculated LLG fault currents

#### 1.2 Fix 3-Phase Fault Zgnd Inclusion (P0-2 / A3)
- **File:** `pc_classes/powercad.py` (`ifault` method, 3PH branch)
- **Change:** Remove `zgnd` from the 3-phase fault path:
  ```python
  # Current (WRONG):
  I1 = vf / (zt + zfault + zgnd)
  
  # Correct:
  I1 = vf / (zt + zfault)
  ```
- **Tests:** Update golden tests
- **Verification:** 3PH fault current should be independent of zgnd

#### 1.3 Resolve Single-Phase Neutral Geometry (P0-3 / A1)
- **File:** `pc_classes/powercad.py` (`calcImpedance`, LineType 1 branch)
- **Decision needed:** User to choose approach
  - **Option A:** Wire NeutralX/NeutralHin from construction CSVs (preferred)
  - **Option B:** Delegate to `overhead_lines.py` for single-phase
  - **Option C:** Document limitation, require manual impedance input
- **Implementation:** Depends on user decision

### Phase 1 Exit Criteria
- All P0 issues resolved or explicitly deferred with user approval
- All tests updated and passing
- Golden test baselines regenerated and reviewed

---

## Phase 2: High-Priority Math Fixes (P1)

**Goal:** Fix all mathematical correctness issues.

**Estimated scope:** 6-8 issues, ~300-500 lines changed

### Tasks

#### 2.1 Fix Frequency Scaling (P1-1 / A2)
- **File:** `pc_classes/powercad.py` (`calcImpedance`)
- **Change:** `w = _W60 * (f / 60.0)` and scale De with frequency

#### 2.2 Fix xrcalc 'low' Multipliers (P1-2 / A5)
- **File:** `pc_classes/powercad.py` (`xrcalc`)
- **Decision needed:** Confirm intended bounds with user
- **Likely fix:** Use `1/1.677`, `1/1.5`, `1/1.3` for symmetry

#### 2.3 Fix Copper Temperature Scaling (P1-3 / A6)
- **File:** `pc_classes/powercad.py` (`calcCurrent` / `_conductor_ampacity`)
- **Change:** Wire `thermal_ampacity.calculate_conductor_ampacity()` for type-1 conductors
- **Or:** Fix the legacy path to scale R to operating temperature

#### 2.4 Fix Voltage Drop Formula (P1-4 / A7)
- **File:** `pc_classes/powercad.py` (`calcVoltageDrop`)
- **Change:** Replace with standard approximate formula:
  ```python
  vdrop = il * (zt[0] * pf + zt[1] * sin(arccos(pf)))  # per-phase
  if phase > 2: return vdrop * sqrt(3)
  elif phase > 1: return vdrop * 2
  else: return vdrop
  ```
- **Tests:** Update `tests/golden/test_voltage_drop_golden.py`

#### 2.5 Document SLG Z2=Z1 Assumption (P1-5 / A4)
- **File:** `pc_classes/powercad.py` (docstring)
- **Change:** Add documentation, no code change needed

#### 2.6 Transformer Z0 Default (P1-6 / A8)
- **Decision needed:** Default zeromult (1.0 vs 0.85 vs table-driven)
- **File:** `pc_classes/powercad.py` (`xfmr`), `pc_classes/pc_functions/dataconstants.py`

#### 2.7 Kron Transposition Documentation (P1-7 / A9)
- **File:** `pc_classes/powercad.py` (docstring)
- **Change:** Document the transposition assumption

#### 2.8 Resolve DATA_AUDIT Discrepancies (P1-8)
- **File:** `pc_classes/pc_data/Construction/7200_*.csv`
- **Decision needed:** User review of 5 flagged assemblies
- **Actions:** Fix CSV entries or document as intentional in-house standards

### Phase 2 Exit Criteria
- All P1 issues resolved or deferred with user approval
- All tests passing with updated baselines
- THEORY_ANALYSIS.md updated with resolutions

---

## Phase 3: Architecture Refactor (P2)

**Goal:** Improve code quality, reduce duplication, wire up dead data.

**Estimated scope:** 8 issues, ~500-800 lines changed

### Tasks

#### 3.1 Extract Shared Assembly Lookup (P2-7)
- **Files:** `pc_classes/polecad.py`, `pc_classes/powercad.py`
- **Action:** Create `pc_classes/pc_functions/assembly_lookup.py` with shared `_find_assembly`
- **Impact:** Both modules use the same logic

#### 3.2 Wire Radius/X into Impedance Calcs (P2-1)
- **Files:** `pc_classes/powercad.py` (`towerCalc`, `calcImpedance`)
- **Action:** Use construction CSV `Phase*Radius`, `Phase*X`, `NeutralRadius`, `NeutralX` for GMD-based distances
- **Reference:** `General Notes.txt` GMD Calculation Matrix

#### 3.3 Deprecate Legacy calcImpedance (P2-3)
- **Files:** `pc_classes/powercad.py`
- **Action:** Refactor `calcImpedance()` to delegate to `OverheadLineImpedance` using CSV geometry
- **Or:** Mark as deprecated, point users to `overhead_lines.py`

#### 3.4 Automate Legacy Script Regression (P2-2)
- **Files:** `tests/golden/test_polecad_golden.py` (new)
- **Action:** Port `spantest.py`, `test1.py`, `test14400.py` into pytest golden tests

#### 3.5 Remove np.mat Monkey-Patch (P2-5)
- **File:** `gui/services/impedance.py`
- **Action:** Remove shim, verify no breakage

#### 3.6 Refactor curvegenerator.py and faultgenerator.py (P2-8)
- **Files:** `pc_classes/curvegenerator.py`, `pc_classes/faultgenerator.py`
- **Action:** Apply same refactor patterns (dataclass config, typed exceptions)

#### 3.7 14.4 kV Data Audit (P2-4)
- **Files:** `pc_classes/pc_data/Construction/14400_*.csv`
- **Action:** Audit against Bulletin 804 V-prefix drawings

#### 3.8 Verify Ampacity Constants (P2-6)
- **File:** `pc_classes/thermal_ampacity.py`
- **Action:** Verify all constants against IEEE 738-2012

### Phase 3 Exit Criteria
- All P2 issues resolved or deferred
- Code duplication reduced
- All tests passing
- New golden tests for polecad scripts

---

## Phase 4: Documentation & Polish (P3)

**Goal:** Complete documentation, type hints, and prepare for GUI.

### Tasks
- [ ] Create `docs/CALCULATION_REFERENCE.md` — every formula documented
- [ ] Add type hints throughout `pc_classes/`
- [ ] Profile reconstructor JSON export
- [ ] 34.5/46kV and 69kV data audits
- [ ] TCC module review
- [ ] Update README.md with new architecture
- [ ] Create `docs/DEVELOPER_GUIDE.md`

### Phase 4 Exit Criteria
- All documentation complete
- Type hints on all public APIs
- Ready for GUI development

---

## Phase 5: GUI Development (Future)

**Goal:** Build the GUI on top of the clean, verified facade.

**Prerequisites:** Phases 0-4 complete, all P0/P1 issues resolved.

---

## Decision Points (User Input Needed)

| # | Decision | Phase | Options |
|---|----------|-------|---------|
| D1 | Single-phase neutral geometry | 1 | A) Use CSV data, B) Delegate to overhead_lines, C) Document limitation |
| D2 | xrcalc 'low' bounds | 2 | Symmetric (1/1.677 etc.) vs current vs custom |
| D3 | Transformer Z0 default | 2 | 1.0 vs 0.85 vs table-driven |
| D4 | Legacy calcImpedance | 3 | Fix in place vs deprecate for overhead_lines |
| D5 | DATA_AUDIT discrepancies | 2 | Fix CSVs vs document as in-house |
| D6 | New document (expected tomorrow) | 0 | Review and incorporate |

---

## Progress Tracking

| Phase | Status | Started | Completed | Notes |
|-------|--------|---------|-----------|-------|
| 0 — Foundation | IN_PROGRESS | 2026-10-24 | — | Awaiting user's new document |
| 1 — Critical Math (P0) | NOT_STARTED | — | — | |
| 2 — High-Priority Math (P1) | NOT_STARTED | — | — | |
| 3 — Architecture (P2) | NOT_STARTED | — | — | |
| 4 — Documentation (P3) | NOT_STARTED | — | — | |
| 5 — GUI | NOT_STARTED | — | — | Blocked on Phases 0-4 |

---

## Next Immediate Actions

1. **Verify baseline** — run all tests, confirm 51 passed + 1 xpassed
2. **Wait for user's new document** — review and incorporate into ISSUES.md
3. **Present decision points D1-D6** to user for input
4. **Begin Phase 1** — start with P0-1 (LLG fault divider) which has a clear fix
