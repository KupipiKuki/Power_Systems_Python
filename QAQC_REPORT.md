# QAQC Report — Branch Analysis & Deviation Check

**Date:** 2026-11-04
**Branches Reviewed:** `main`, `major-refactors`, `vibe/phase1-network-assembly`
**PRs Reviewed:** #4 (merged+reverted), #5 (revert, merged), #6 (open draft)
**Baseline:** `major-refactors` @ `a8b3994`

---

## 1. Executive Summary

| Metric | Status |
|--------|--------|
| `main` branch | Clean — revert applied, back to pre-refactor state (`2604c5e`) |
| `major-refactors` | Complete — all refactor work, plan docs, 51 tests + 1 xpassed |
| `vibe/phase1-network-assembly` (PR #6) | **NEW** — 1 commit on top of `major-refactors`, 62 tests pass |
| Deviations from plan | **2 found** — see Section 4 |
| Test status | 62 passed + 1 xpassed on phase1 branch; 51 passed + 1 xpassed on major-refactors |
| Legacy scripts | All 7 pass on both branches |

**Overall verdict:** Implementation has **NOT significantly deviated** from the plan. PR #6 correctly builds on `major-refactors` and implements Phase 1 GUI work (transformer Z0 models + network assembly) as anticipated by the REFACTOR_PLAN. Two minor deviations documented below.

---

## 2. Branch Topology

```
main (2604c5e) ← revert of PR #4
  ↑
  └── [PR #4 merged then reverted via PR #5 — main is clean]

major-refactors (a8b3994) ← single source of truth for all refactor work
  │
  └── vibe/phase1-network-assembly (6daf6e4) ← PR #6, DRAFT, targets major-refactors
```

**Key facts:**
- `major-refactors` merge-base with `vibe/phase1-network-assembly` = `a8b3994` (the plan commit) — PR #6 is built directly on the planned base
- PR #6 targets `major-refactors` (not `main`) — **correct**
- No other branches exist — all old branches (`gemini/modular-refactor`, `vibe/gui-impedance`, etc.) were deleted after consolidation

---

## 3. PR #6 Content Review

### Files Changed (508 insertions, 0 deletions, 5 files)

| File | Lines | Purpose |
|------|-------|---------|
| `gui/services/transformer_z0.py` | 90 | Transformer zero-sequence models by winding connection |
| `gui/services/network.py` | 194 | Radial network assembly (source → transformer → line → fault) |
| `gui/services/config.py` | +2 | Added `primary_connection`/`secondary_connection` to `TransformerConfig` |
| `gui/services/__init__.py` | +18 | Exports for new modules |
| `gui/tests/test_phase1.py` | 204 | 11 hand-derived tests from QA corpus Sections 2 & 4 |

### Mathematical Verification

| Check | Result |
|-------|--------|
| `transformer_z1()` matches `powercad.xfmr()` | ✅ Exact match (verified numerically) |
| Line segment per-unit conversion `z_pu = z_ohms / (kv²/base_mva)` | ✅ Correct |
| Transformer rebasing `z_pu_study = z_pu_nameplate × (base_mva / mva_rating)` | ✅ Correct (×4 for 25→100 MVA) |
| Zero-sequence path logic (GrdY passes, Delta/Y block) | ✅ Matches corpus Section 2 |
| Delta-primary excludes source Z0 | ✅ Tested and verified |
| Delta-secondary blocks SLG/LLG (returns None) | ✅ Tested and verified |
| 62 tests pass | ✅ All green |
| 7 legacy scripts pass | ✅ All green |

### Corpus Section 4.4 Discrepancy (Expected)

The QA corpus (`docs/qa/phase1_test_cases.md` §4.4) contains a **known error**: transformer rebasing uses `×(25/100) = 0.25` (wrong direction) instead of `×(100/25) = 4.0`. PR #6 correctly uses the audit-corrected formula. This means:

- Corpus §4.5 fault currents (3PH=5,784A, SLG=2,511A) are based on the wrong rebasing
- PR #6's corrected values: 3PH≈3,704A, SLG≈2,002A (verified numerically)
- **Recommendation:** Update corpus §4.4/§4.5 to match the correction (PR #6 notes this)

---

## 4. Deviations from Plan

### Deviation 1: PR #6 implements Phase 5 (GUI) work before Phases 1-4 complete

| Aspect | Plan Said | What Happened |
|--------|-----------|---------------|
| REFACTOR_PLAN.md Phase 5 (GUI) | "Blocked on Phases 0-4" | PR #6 adds GUI facade extensions (network assembly, transformer Z0) while P0/P1 math bugs in `powercad.py` remain unfixed |

**Assessment:** MINOR. The new code lives entirely in `gui/services/` (the facade layer), which is the correct architectural boundary. It does NOT modify `pc_classes/powercad.py` legacy code, so the P0/P1 bugs are unaffected. The facade delegates to `faultCalculationClass.ifault()` which still has the LLG/3PH bugs (P0-1, P0-2), so fault currents computed through `assemble_network()` inherit those bugs.

**Risk:** LOW-MEDIUM. Network fault currents for LLG faults will be wrong until P0-1 is fixed in `powercad.ifault()`.

### Deviation 2: Corpus §4.4/§4.5 not corrected in the corpus document itself

| Aspect | Plan Said | What Happened |
|--------|-----------|---------------|
| PR #6 body says | "recommend Mistral update the corpus doc" | Corpus document still has the wrong 0.02 pu value and 5,784A figure |

**Assessment:** MINOR. The code is correct; the documentation is stale. Should be fixed when the corpus is next updated.

---

## 5. What Has NOT Deviated (Good)

| Area | Status |
|------|--------|
| Branch consolidation | ✅ `major-refactors` is the single base; PR #6 correctly targets it |
| No changes to `main` | ✅ Main remains clean (reverted) |
| No changes to legacy `pc_classes/` | ✅ PR #6 only touches `gui/services/` and `gui/tests/` |
| Test count grew correctly | ✅ 51 → 62 tests (+11 new), all passing |
| No new branches created | ✅ Only `vibe/phase1-network-assembly` exists beyond `major-refactors` |
| Plan documents intact | ✅ `ISSUES.md`, `THEORY_ANALYSIS.md`, `REFACTOR_PLAN.md` unchanged on `major-refactors` |
| Old branches cleaned up | ✅ All deleted after consolidation |

---

## 6. Outstanding Issues Status (from ISSUES.md)

PR #6 does NOT address any of the P0/P1 issues in `ISSUES.md` — it's purely additive GUI facade work. The P0/P1 issues remain OPEN:

| Priority | Open | Blocked | Notes |
|----------|------|---------|-------|
| P0 | 2 | 1 | LLG divider, 3PH zgnd, single-phase neutral — all still in `powercad.py` |
| P1 | 6 | 2 | Frequency scaling, xrcalc, Copper temp, Vdrop, SLG doc, XFMR Z0, DATA_AUDIT |
| P2 | 8 | 0 | Architecture improvements |
| P3 | 5 | 0 | Documentation |

---

## 7. Recommendations

1. **Merge PR #6 into `major-refactors`** — it's clean, tested, and correctly based. The GUI facade work is ready.
2. **Fix corpus §4.4/§4.5** — update the QA corpus document to use the correct transformer rebasing (×4 not ×0.25).
3. **Prioritize P0 fixes next** — especially P0-1 (LLG fault divider) since `assemble_network()` delegates to `ifault()` and inherits the bug.
4. **Add a note to `REFACTOR_PLAN.md`** that Phase 5 (GUI facade) has partially started via PR #6, and that P0/P1 fixes in `pc_classes/` remain the critical path.
5. **Consider adding network-assembly golden tests** that compare against first-principles values (PR #6 already has these in `test_phase1.py`).

---

## 8. Verification Commands Run

```bash
# On vibe/phase1-network-assembly:
python -m pytest tests/ gui/tests/ tests/golden/ -v
# Result: 62 passed, 1 xpassed

# Legacy scripts:
for s in spantest.py test1.py test14400.py temptest1.py temptest2.py xfmrTest.py VoltageDropTest.py; do
  MPLBACKEND=Agg python $s && echo "$s: PASS"
done
# Result: all 7 PASS

# Numerical verification:
python -c "..."  # transformer_z1 vs powercad.xfmr — exact match
python -c "..."  # line segment per-unit conversion — correct
python -c "..."  # transformer rebasing direction — correct (×4)
python -c "..."  # full network fault currents with correct rebasing — 3PH≈3704A
```
