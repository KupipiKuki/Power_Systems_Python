# Phase 0 Audit Report: Calculation Facade Review

**Target Artifact:** PR #3, branch `vibe/gui-impedance`, commit `f94c5f1` ("Phase 0: Calculation facade API with dataclass contracts and tests")  
**Repository:** `KupipiKuki/Power_Systems_Python`  
**Auditor:** Gemini (Advanced Agentic Systems Reviewer)  
**Date:** 2026-10-22  
**Audit Branch:** `audit/gemini-phase0`  

---

## Verdict: FAIL

The calculation facade in PR #3 succeeds in establishing a clean packaging boundary: it isolates `pc_classes` behind dataclasses, touches exclusively files under `gui/`, and keeps all returned objects in pure Python types (`complex`, `float`, `int`).

However, **two severe mathematical and indexing defects** in the facade implementation produce invalid or zeroed engineering results:
1. **Line-to-Line and Double-Line-to-Ground fault currents are identically zero**: `fault_currents()` extracts rows 3 and 6 of `powercad.ifault()`'s `Iabc` matrix. In `powercad.py`, LL and LLG faults are simulated on phases B and C (BC and BC-G), leaving phase A unfaulted ($I_a = 0$). Extracting rows 3 and 6 yields strictly zero ($0\text{ A}$) for all LL and LLG fault studies (`gui/services/impedance.py:134-135`).
2. **Erroneous SLG source impedance derivation**: In `source_impedance()`, when deriving $Z_0$ from `fault_mva_slg`, the facade omits the factor of 3 in the loop impedance ($I_\text{SLG} = 3 V / (2 Z_1 + Z_0) \implies |2 Z_1 + Z_0| = 3 S_\text{base} / S_\text{SLG}$), producing a 300% error in fault current. Furthermore, it subtracts a complex impedance ($2 Z_1$) from a scalar real float (`z_loop`), yielding an unphysical negative zero-sequence reactance ($X_0 < 0$, capacitive) for an inductive source (`gui/services/impedance.py:107-110`).
3. **Refactor Incompatibility with PR #2**: PR #2 (`vibe/powercad-refactor`) makes `config: PowerCalcConfig` a mandatory argument in `faultCalculationClass.__init__()`. Calling `faultCalculationClass()` with zero arguments as the facade does will raise a `TypeError` as soon as PR #2 lands.

These blocking issues must be resolved before proceeding to Phase 1.

---

## Blocking findings (must fix before Phase 1)

### Finding B-1: `fault_currents()` extracts unfaulted phase current ($0\text{ A}$) for LL and LLG faults
- **Location:** [`gui/services/impedance.py:132-138`](file:///o:/Data/Programming/Github/Power_Systems_Python/gui/services/impedance.py#L132-L138)
- **Problem:** In `fault_currents()`:
  ```python
  iabc = engine.ifault(zlt, config.vf_pu, config.zgnd_pu, config.zfault_pu, 0)
  return FaultResult(
      i_slg_pu=complex(iabc[0, 0]),
      i_ll_pu=complex(iabc[3, 0]),
      i_llg_pu=complex(iabc[6, 0]),
      i_3ph_pu=complex(iabc[9, 0]),
      base_amps=config.base_amps,
  )
  ```
  In `pc_classes/powercad.py:408-481`, `ifault(..., matreturn=0)` generates a $(12 \times 1)$ phase current matrix $I_{abc}$ composed of four 3-row blocks:
  - **Rows 0–2 (SLG, Phase A to Ground):** Row 0 is faulted Phase A ($I_a \neq 0$), Rows 1 and 2 are unfaulted Phases B and C ($I_b = I_c = 0$).
  - **Rows 3–5 (LL, Phase B to Phase C):** Line 426 explicitly specifies `#Phase to Phase Fault, (BC)`. Phase A is unfaulted: $I_a = I_{a0} + I_{a1} + I_{a2} = 0 + I_1 - I_1 = 0$. Row 3 is Phase A ($I_a = 0$). The actual faulted phase currents are in Row 4 ($I_b$) and Row 5 ($I_c = -I_b$).
  - **Rows 6–8 (LLG, Phase B and Phase C to Ground):** Line 443 explicitly specifies `#Phase to Phase to Ground Fault, (BC-G)`. Phase A is unfaulted: $I_a = I_0 + I_1 + I_2 = -I_1 + I_1 = 0$. Row 6 is Phase A ($I_a = 0$). The actual faulted phase currents are in Row 7 ($I_b$) and Row 8 ($I_c$).
  - **Rows 9–11 (3-Phase, ABC):** Rows 9, 10, 11 are Phases A, B, and C.
- **Impact:** `FaultResult.i_ll_pu`, `FaultResult.i_ll_amps`, `FaultResult.i_llg_pu`, and `FaultResult.i_llg_amps` evaluate to `0.0` for all system configurations. Any GUI displaying these fields will display $0\text{ A}$.
- **Test Blindness:** `test_indices_match_powercad` ([`gui/tests/test_services.py:146-147`](file:///o:/Data/Programming/Github/Power_Systems_Python/gui/tests/test_services.py#L146-L147)) asserted `res.i_ll_pu == approx(complex(iabc[3, 0]))` and `res.i_llg_pu == approx(complex(iabc[6, 0]))`. Because both sides were identically zero, the test passed without detecting that the extracted current was zero.
- **Required Resolution:**
  Extract the faulted phase currents:
  - For LL: Use Row 4 (Phase B) or Row 5 (Phase C): $|I_{\text{LL}}| = \text{abs}(iabc[4, 0]) = \frac{\sqrt{3} |V_f|}{|2 Z_1 + Z_f|}$.
  - For LLG: Use Row 7 (Phase B) or Row 8 (Phase C) for phase conductor fault current, and/or provide the ground return current $I_g = I_b + I_c = 3 I_0$.

---

### Finding B-2: Missing factor of 3 and scalar/complex subtraction in `source_impedance()` SLG loop
- **Location:** [`gui/services/impedance.py:107-111`](file:///o:/Data/Programming/Github/Power_Systems_Python/gui/services/impedance.py#L107-L111)
- **Problem:** The facade derives $Z_0$ from `fault_mva_slg` as follows:
  ```python
  elif config.fault_mva_slg is not None:
      # SLG loop: E/I = Z1 + Z2 + Z0 = 2*Z1 + Z0 (Z2 = Z1, E = 1 pu)
      z_loop = config.base_mva / config.fault_mva_slg
      z0 = z_loop - 2.0 * z1
  ```
  This implementation contains two critical errors:
  1. **Omission of the factor of 3 in loop impedance:**
     In symmetrical components, for a bolted SLG fault with $E = 1.0\text{ pu}$ and $Z_2 = Z_1$, the phase fault current is:
     $$I_{\text{SLG, pu}} = 3 I_{a1} = \frac{3 E}{2 Z_1 + Z_0}$$
     Per IEEE C37.010 / IEEE 399, the three-phase equivalent SLG fault duty is:
     $$\text{Duty MVA}_{\text{SLG}} = \sqrt{3} V_{LL} I_{\text{SLG}} = S_{\text{base}} \cdot |I_{\text{SLG, pu}}| = S_{\text{base}} \cdot \frac{3}{|2 Z_1 + Z_0|}$$
     Therefore, the true loop impedance magnitude is:
     $$|Z_{\text{loop}}| = |2 Z_1 + Z_0| = \frac{3 \cdot S_{\text{base}}}{\text{Duty MVA}_{\text{SLG}}}$$
     The code calculates `z_loop = base_mva / fault_mva_slg`, which is $1/3$ of the required value.
  2. **Subtracting a complex impedance from a scalar real float:**
     `z_loop` is computed as a real float ($100 / 2000 = 0.05$). $Z_1 = R_1 + j X_1$ is a complex number ($0.0062 + j 0.0496$).
     Subtracting $2 Z_1$ from real scalar $z_\text{loop}$ yields:
     $$R_0 = z_\text{loop} - 2 R_1 = 0.05 - 0.0124 = 0.0376$$
     $$X_0 = 0 - 2 X_1 = -2(0.0496) = -0.0992$$
     The resulting zero-sequence impedance has a **negative reactance** ($X_0 < 0$, capacitive), which is physically impossible for a passive BES utility network.
     When this $Z_0$ is used in `ifault()`, $2 Z_1 + Z_0 = 2 Z_1 + (0.05 - 2 Z_1) = 0.05 + j 0.0$. The reactive component cancels out entirely, and the calculated SLG fault current is:
     $$I_{\text{SLG}} = \frac{3 \cdot 1.0}{0.05} = 60.0\angle 0^\circ\text{ pu}$$
     This corresponds to $6000\text{ MVA}$ of fault duty—exactly **3 times the user-specified 2000 MVA**!
- **Test Blindness:** `test_source_from_slg_mva` ([`gui/tests/test_services.py:91`](file:///o:/Data/Programming/Github/Power_Systems_Python/gui/tests/test_services.py#L91)) asserted `res.z0_pu == approx(0.05 - 2 * z1)`, circularly pinning the buggy formula rather than validating physical electrical quantities.
- **Required Resolution:**
  Include the factor of 3 and handle vector angles properly:
  $$|Z_{\text{loop}}| = \frac{3 \cdot S_{\text{base}}}{\text{fault\_mva\_slg}}$$
  If zero-sequence angle is assumed aligned with positive-sequence ($X/R$ ratio $\theta$), or if $(X/R)_{\text{SLG}}$ is supplied:
  $$Z_{\text{loop}} = |Z_{\text{loop}}| e^{j \theta_{\text{loop}}}, \quad Z_0 = Z_{\text{loop}} - 2 Z_1$$
  Ensure $R_0 \ge 0$ and $X_0 \ge 0$.

---

### Finding B-3: Breaking constructor signature drift between Facade and PR #2 `faultCalculationClass`
- **Location:** [`gui/services/impedance.py:53`](file:///o:/Data/Programming/Github/Power_Systems_Python/gui/services/impedance.py#L53) vs [`pc_classes/powercad.py:126`](file:///o:/Data/Programming/Github/Power_Systems_Python/pc_classes/powercad.py#L126) on branch `vibe/powercad-refactor`
- **Problem:** In PR #2 (`vibe/powercad-refactor`), `faultCalculationClass.__init__` was refactored:
  ```python
  class faultCalculationClass:
      def __init__(self, config):
          if not isinstance(config, PowerCalcConfig):
              raise TypeError('faultCalculationClass requires a PowerCalcConfig')
          self.cfg = config
  ```
  The facade instantiates the engine with no arguments:
  ```python
  def _engine():
      global _ENGINE
      if _ENGINE is None:
          from pc_classes.powercad import faultCalculationClass
          with _repo_cwd():
              _ENGINE = faultCalculationClass()
      return _ENGINE
  ```
  As soon as PR #2 is merged, every facade function (`transformer_impedance`, `source_impedance`, `fault_currents`, `voltage_drop`) will crash with `TypeError: faultCalculationClass requires a PowerCalcConfig`.
- **Required Resolution:**
  Coordinate with the PR #2 author to make `config` optional in `faultCalculationClass.__init__(self, config=None)` (see Refactor-Coordination Notes below).

---

## Non-blocking findings (should fix, tracked)

### Finding NB-1: Docstring parameter name mismatch in `SourceConfig`
- **Location:** [`gui/services/config.py:35`](file:///o:/Data/Programming/Github/Power_Systems_Python/gui/services/config.py#L35)
- **Details:** The docstring states:
  `likewise one of fault_mva_slg / explicit_z0 / zero_from_xr must be provided.`
  The actual field name defined on line 54 and validated on line 64 is `zero_mult`. `zero_from_xr` does not exist.
- **Recommendation:** Update the docstring to refer to `zero_mult`.

### Finding NB-2: Validation checks "at least one" instead of "exactly one"
- **Location:** [`gui/services/config.py:59-68`](file:///o:/Data/Programming/Github/Power_Systems_Python/gui/services/config.py#L59-L68)
- **Details:** The docstring claims "Exactly one of fault_mva_3ph / explicit_z1 must be provided", but `__post_init__` only checks that both are not `None`. If a caller provides both `fault_mva_3ph` and `explicit_z1`, `source_impedance` silently prefers `explicit_z1`.
- **Recommendation:** Either validate mutual exclusivity in `__post_init__` or explicitly document the precedence order in the docstring.

### Finding NB-3: Lack of domain validation on dataclass fields
- **Location:** [`gui/services/config.py:13-90`](file:///o:/Data/Programming/Github/Power_Systems_Python/gui/services/config.py#L13-L90)
- **Details:** Dataclasses accept unphysical negative values:
  - `TransformerConfig`: allows `mva_base <= 0`, `percent_z <= 0`, `xr_ratio <= 0`, `zero_mult < 0`.
  - `FaultConfig`: allows negative pre-fault voltage or impedances.
  - `SourceConfig`: allows negative MVA duties.
- **Recommendation:** Add standard positivity checks in `__post_init__`.

### Finding NB-4: `np.mat` monkey-patch in facade
- **Location:** [`gui/services/impedance.py:20-21`](file:///o:/Data/Programming/Github/Power_Systems_Python/gui/services/impedance.py#L20-L21)
- **Details:** The facade patches `np.mat = np.asmatrix` at import time. This monkey-patch is effective because `generate_transforms()` is only executed when `_engine()` is called. However, monkey-patching third-party modules is an antipattern.
- **Status in PR #2:** In `vibe/powercad-refactor`, `datafunctions.py:67-68` already replaced `np.mat` with `np.asmatrix`. Once PR #2 merges, this shim will no longer be needed.

### Finding NB-5: Upstream bug in `powercad.py` LLG sequence current calculation
- **Location:** [`pc_classes/powercad.py:447-454`](file:///o:/Data/Programming/Github/Power_Systems_Python/pc_classes/powercad.py#L447-L454)
- **Details:** In `powercad.py`:
  ```python
  I1=vf/(zt+(zfault/2)+((zt+(zfault/2))*(z0t+(zfault/2)+(3*zgnd)))/(zt+z0t+zfault+(3*zgnd)))
  I012=np.array([[-I1*(z0t/(zt+z0t))],
                 [I1],
                 [-I1*(zt/(zt+z0t))]])
  ```
  Two issues exist in the underlying engine (flag only):
  1. $I_0$ and $I_2$ current divider ratios are inverted: $I_0$ should be proportional to $Z_2 = Z_t$, and $I_2$ proportional to $Z_0 = Z_{0t}$.
  2. $z_{\text{fault}}$ and $z_{\text{gnd}}$ are accounted for in $I_1$, but dropped from the current divider splitting into $I_0$ and $I_2$.
- **Recommendation:** Inform PR #2 author to correct lines 447–454 in `powercad.py`. The facade should document a caveat for LLG calculations until corrected upstream.

---

## Refactor-coordination notes (for PR #1/#2 authors)

Inspection of `origin/vibe/powercad-refactor` (PR #2) and `origin/vibe/polecad-refactor-c349b2` (PR #1) reveals the following integration requirements:

1. **`faultCalculationClass` constructor decoupling (Critical):**
   - In PR #2, `faultCalculationClass.__init__(self, config)` requires a `PowerCalcConfig` containing `project_name` and `project_dir`.
   - However, the mathematical methods required by the GUI facade (`xfmr`, `xrcalc`, `ifault`, `calcVoltageDrop`) depend only on `self.Amat`, `self.Ainv`, `self.compy`, `self.compd`, `self.xrcurve`, and `self.distxfmr`. They **never** access `self.cfg`, `self.poledb`, or `self.conddb`.
   - **Recommendation for PR #2 author:** Modify `faultCalculationClass.__init__(self, config=None)` to make `config` optional. When `config is None`, initialize only the transformation matrices and constants, bypassing project directory checks.
2. **Path handling and CWD pinning:**
   - In `main`, `datafunctions.py` used relative string paths like `'./pc_classes/pc_data/...'`, forcing the facade to use `_repo_cwd()` (`gui/services/impedance.py:34-42`).
   - PR #2 has resolved this cleanly by introducing `_DATA_DIR = Path(__file__).resolve().parent.parent / 'pc_data'` in `datafunctions.py`. Once PR #2 is merged, `_repo_cwd()` in `gui/services/impedance.py` can be removed.
3. **NumPy 2.0 compatibility:**
   - PR #2 already replaces `np.mat` with `np.asmatrix` in `datafunctions.py:67-68`.
   - The facade shim `np.mat = np.asmatrix` (`gui/services/impedance.py:21`) can be safely retired or retained as a harmless guard.
4. **Signature stability of calculation methods:**
   - Signatures for `xfmr()`, `xrcalc()`, `ifault()`, and `calcVoltageDrop()` in PR #2 are fully preserved and match the facade's calls.

---

## Re-derivation table (test → your value → match y/n)

All unit test expectations in `gui/tests/test_services.py` were independently re-derived from first principles:

| Test Name | Theoretical Formula / Derivation | Expected Numerical Value | Facade Assertion | Assertion Match? | Physically Sound? | Notes |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `test_xfmr_basic` | $r_1 = \frac{0.08}{\sqrt{1+12^2}}$, $x_1 = 12 r_1$, $z_0 = 0.9 z_1$ | $r_1 \approx 0.0066436$, $x_1 \approx 0.0797237$, $z_0 = 0.9 z_1$ | `res.z1_pu.real == approx(r1, rel=1e-9)` | **YES** | **YES** | Exact match. Comment line 36 rounded to 0.006659, but assertion uses exact math. |
| `test_xfmr_default_xr_deterministic` | $\text{interp}(10, \text{xrcurve}) = 15.8$; $\|Z_1\| = 0.0575$ | $\|Z_1\| = 0.0575\text{ pu}$; repeated calls equal | `a.z1_pu == b.z1_pu`, `abs(a.z1_pu) == approx(0.0575)` | **YES** | **YES** | Deterministic GE curve interpolation verified. |
| `test_xfmr_ohms_conversion` | $Z_\text{base} = \frac{12.47^2}{25} = 6.220036\text{ }\Omega$; $Z_\Omega = Z_\text{pu} \cdot Z_\text{base}$ | $\|Z_\Omega\| = 0.08 \times 6.220036 = 0.497603\text{ }\Omega$ | `abs(res.z1_ohms) == approx(0.08 * zbase, rel=1e-6)` | **YES** | **YES** | Unit conversion matches IEEE definitions. |
| `test_source_from_3ph_mva` | $\|Z_1\| = \frac{100}{2500} = 0.04\text{ pu}$; $Z_0 = 3 Z_1$ | $\|Z_1\| = 0.04\text{ pu}$; $Z_0 = 0.12\angle\theta$ | `abs(res.z1_pu) == approx(0.04)`, `res.z0_pu == approx(3 * res.z1_pu)` | **YES** | **YES** | Matches standard 3-phase short-circuit duty definition. |
| `test_source_from_slg_mva` | $\|Z_\text{loop}\| = \frac{3 \cdot S_\text{base}}{S_\text{SLG}} = \frac{300}{2000} = 0.15\text{ pu}$ | $Z_0 = Z_\text{loop} - 2 Z_1$, $X_0 > 0$ | `res.z0_pu == approx(0.05 - 2 * z1)` | **YES** (asserts code bug) | **NO** (Finding B-2) | **Flawed derivation:** Code omitted factor of 3 and subtracted complex $2 Z_1$ from scalar 0.05, producing $X_0 = -0.0992j$ and 300% fault current. Test blindly pinned flawed formula. |
| `test_source_explicit` | Direct passthrough of $Z_1, Z_0$ | $Z_1 = 0.02 + 0.1j$, $Z_0 = 0.06 + 0.3j$ | Exact equality check | **YES** | **YES** | Passthrough verified. |
| `test_source_requires_inputs` | Validation requires at least one Z1 and Z0 source | Raises `ValueError` | `pytest.raises(ValueError)` | **YES** | **YES** | Validation exceptions trigger as expected. |
| `test_infinite_bus_transformer_fault` | $I_{3\phi} = \frac{1.05}{Z_1}$; $I_\text{SLG} = \frac{3 \cdot 1.05}{2 Z_1 + Z_0}$ | Rebase $\times 5$: $\|I_{3\phi}\| = 2.625\text{ pu}$; $\|I_\text{SLG}\| \approx 2.7155\text{ pu}$ | `res.i_3ph_pu == approx(1.05/z1)`, `res.i_slg_pu == approx(3.15/(2*z1+z0))` | **YES** | **YES** | Matches symmetrical component network equations. |
| `test_series_summation` | $Z_1 = \sum Z_{1i} = 0.02 + 0.05j$; $Z_0 = 0.06 + 0.12j$ | $\|I_{3\phi}\| \approx 18.570\text{ pu}$; $\|I_\text{SLG}\| \approx 12.414\text{ pu}$ | `res.i_3ph_pu == approx(1.0/z1)`, `res.i_slg_pu == approx(3.0/(2*z1+z0))` | **YES** | **YES** | Linear series summation verified. |
| `test_indices_match_powercad` | Row 0: SLG ($I_a$); Row 3: LL ($I_a = 0$); Row 6: LLG ($I_a = 0$); Row 9: 3$\phi$ ($I_a$) | Row 3 and 6 are $0.0$; Faulted LL is Row 4/5 ($38.73\text{ pu}$); Faulted LLG is Row 7/8 ($39.90\text{ pu}$) | `res.i_ll_pu == approx(iabc[3,0])`, `res.i_llg_pu == approx(iabc[6,0])` | **YES** (asserts $0 == 0$) | **NO** (Finding B-1) | **Extraction defect:** Rows 3 and 6 are unfaulted Phase A ($0\text{ A}$). Facade reports zero current for LL and LLG. |
| `test_single_phase` | $V_\text{drop} = V_s + I R \cos\phi + I X \sin\phi - \sqrt{V_s^2 - (I X \cos\phi - I R \sin\phi)^2}$ | $V_\text{drop} \approx 14.7008\text{ V}$ | `res.drop_volts > 0` | **YES** | **YES** | Accurate single-phase voltage drop formula verified. |
| `test_dataclasses_reject_unknown` | Dataclass `__init__` rejects unrecognized keyword arguments | Raises `TypeError` | `pytest.raises(TypeError)` | **YES** | **YES** | Python dataclass contract verified. |

---

## Recommendations for Phase 1

1. **Fix Fault Current Extraction (Finding B-1):**
   Update `fault_currents()` in `gui/services/impedance.py` to extract the faulted phase current magnitudes:
   - $I_{\text{LL}}$: extract `iabc[4, 0]` (Phase B) or `iabc[5, 0]` (Phase C).
   - $I_{\text{LLG}}$: extract `iabc[7, 0]` (Phase B) or `iabc[8, 0]` (Phase C).
   - Consider exposing all three phase currents ($I_a, I_b, I_c$) or ground return current ($I_g$) in `FaultResult` for engineering clarity.
   - Update `gui/tests/test_services.py` with hand-derived assertions verifying non-zero fault currents:
     $$\|I_{\text{LL}}\| = \frac{\sqrt{3} |V_f|}{|2 Z_1 + Z_f|}, \quad \|I_{\text{LLG}}\| = \left| \mathbf{A} \cdot I_{012} \right|_{\text{phase b, c}}$$

2. **Fix SLG Zero-Sequence Derivation (Finding B-2):**
   - Correct the loop impedance magnitude to $|Z_{\text{loop}}| = \frac{3 \cdot S_{\text{base}}}{\text{fault\_mva\_slg}}$.
   - Require or default an $(X/R)_{\text{SLG}}$ or zero-sequence angle, or align $Z_{\text{loop}}$ along the positive-sequence angle:
     $$Z_{\text{loop}} = |Z_{\text{loop}}| e^{j \theta_1}, \quad Z_0 = Z_{\text{loop}} - 2 Z_1$$
   - Enforce $R_0 \ge 0$ and $X_0 \ge 0$.
   - Update `test_source_from_slg_mva` with first-principles derivation confirming that when $MVA_{3\phi} = MVA_{\text{SLG}}$, the derived $Z_0$ equals $Z_1$.

3. **Coordinate Engine Decoupling with PR #2 (Finding B-3):**
   - Align with PR #2 author to allow `faultCalculationClass(config=None)` to run in a standalone calculation mode without requiring project directory paths or CSV database loads.

4. **Expand Golden Regression Suite:**
   - Integrate the test cases from `qa/mistral-phase0` (`tests/golden/`) into CI to ensure the facade and underlying engine are verified simultaneously against external benchmarks.
   - Note for QA team: Correct the transformer base conversion formula in Section 4.4 of `docs/qa/phase1_test_cases.md` (converting from 25 MVA to 100 MVA base multiplies per-unit impedance by $100/25 = 4$, not $25/100 = 0.25$).

5. **Enhance Config Dataclass Contracts:**
   - Correct the `zero_from_xr` docstring typo in `SourceConfig`.
   - Add input validation in `__post_init__` for `TransformerConfig`, `SourceConfig`, and `FaultConfig` to reject non-positive impedances, voltages, and bases.
