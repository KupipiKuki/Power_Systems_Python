# Mathematical Theory Analysis

**Branch:** `major-refactors`
**Purpose:** Full analysis of the mathematics and theory used in the original development
**Date:** 2026-10-24

---

## Table of Contents

1. [Symmetrical Components](#1-symmetrical-components)
2. [Carson's Equations (Earth Return)](#2-carsons-equations-earth-return)
3. [Kron Reduction](#3-kron-reduction)
4. [Fault Analysis](#4-fault-analysis)
5. [Transformer Impedance](#5-transformer-impedance)
6. [Line Impedance](#6-line-impedance)
7. [Ampacity (IEEE 738)](#7-ampacity-ieee-738)
8. [Voltage Drop](#8-voltage-drop)
9. [Pole Structural Calculations](#9-pole-structural-calculations)
10. [Discrepancies and Corrections Needed](#10-discrepancies-and-corrections-needed)

---

## 1. Symmetrical Components

### 1.1 Theory

Fortescue's symmetrical components transform unbalanced 3-phase quantities into three balanced sequence networks:

```
[V012] = A⁻¹ · [Vabc]
[I012] = A⁻¹ · [Iabc]
[Z012] = A⁻¹ · [Zabc] · A
```

Where the transformation matrix A is:

```
        [1    1     1  ]
A  =   [1   a²     a  ]
        [1    a    a²  ]
```

with `a = e^(j·2π/3) = -0.5 + j·0.866` and `a² = e^(j·4π/3) = -0.5 - j·0.866`

### 1.2 Implementation Review

**Location:** `pc_classes/pc_functions/datafunctions.py` (`generate_transforms`)

**Status:** CORRECT

The transformation matrices are generated correctly. The `abcseq`, `abc2seq`, `seq2abc` methods in `powercad.py` use matrix multiplication properly.

**Note:** The legacy `underground_cables.py` had a bug (Hadamard `*` instead of matrix `@`) which has been FIXED.

### 1.3 Sequence Network Connections for Faults

| Fault Type | Sequence Network Connection |
|-----------|---------------------------|
| 3-Phase (ABC) | Positive sequence only: I₁ = V / (Z₁ + Zf) |
| SLG (A-G) | All three in series: I₁ = V / (Z₁ + Z₂ + Z₀ + Zf + 3Zg) |
| LL (B-C) | Positive and negative in parallel: I₁ = V / (Z₁ + Z₂ + Zf) |
| LLG (B-C-G) | Positive in series with (negative || zero): I₁ = V / (Z₁ + Zf/2 + (Z₁+Zf/2)(Z₀+Zf/2+3Zg)/(Z₁+Z₀+Zf+3Zg)) |

---

## 2. Carson's Equations (Earth Return)

### 2.1 Theory

Carson's equations model the impedance of conductors with earth return. The self-impedance of conductor i:

```
Z_ii = R_i + R_d + j·ω·μ₀/(2π) · ln(D_e / GMR_i)
```

The mutual impedance between conductors i and j:

```
Z_ij = R_d + j·ω·μ₀/(2π) · ln(D_e / D_ij)
```

Where:
- `R_i` = conductor AC resistance (Ω/mile)
- `R_d` = earth return resistance = `π²·f·10⁻⁴` Ω/mile ≈ `1.588×10⁻³·f` at 60 Hz
- `D_e` = Carson's equivalent depth of return = `2160·√(ρ/f)` feet (ρ in Ω·m)
- `GMR_i` = geometric mean radius of conductor i (feet)
- `D_ij` = distance between conductors i and j (feet)
- `ω·μ₀/(2π)` = `2.0224×10⁻³` at 60 Hz (Ω/mile per natural log unit)

### 2.2 Implementation Review

**Location:** `pc_classes/powercad.py:calcImpedance()`, `pc_classes/overhead_lines.py`

**In powercad.py (legacy):**
```python
w = _W60                    # 2.0224e-3 (60 Hz constant)
resd = _RESD60 * (f / 60.0) # 1.588e-3 * 60 * (f/60) = 1.588e-3 * f
```

**Issue A2:** `w` is NOT scaled by frequency. Should be `w = 2.0224e-3 * (f/60)`.

**In overhead_lines.py (new):**
```python
self.w = 2.0224e-3 * (self.f / 60.0)  # CORRECT
self.resd = 1.588e-3 * self.f          # CORRECT
```

**Status:** overhead_lines.py CORRECT; powercad.py has A2 bug.

### 2.3 Carson's Equivalent Depth De

| Soil Type | ρ (Ω·m) | De at 60 Hz (ft) |
|-----------|---------|------------------|
| Wet | ~10 | 27.9 |
| Swampy | ~100 | 882 |
| Average | ~1000 | 2790 |
| Dry | ~10000 | 8820 |

**Implementation:** `_SOIL_DE` dict in `powercad.py` — CORRECT for 60 Hz.

**Note:** De is frequency-dependent: `De = 2160·√(ρ/f)`. At non-60 Hz, the lookup table values are wrong.

---

## 3. Kron Reduction

### 3.1 Theory

Kron reduction eliminates neutral/shield conductors from the primitive impedance matrix to obtain the phase-conductor matrix:

```
[Z_abc] = [Z_pp] - [Z_pn] · [Z_nn]⁻¹ · [Z_np]
```

Where:
- `[Z_pp]` = phase-phase submatrix (N×N)
- `[Z_pn]` = phase-neutral submatrix (N×M)
- `[Z_nn]` = neutral-neutral submatrix (M×M)
- `[Z_np]` = neutral-phase submatrix (M×N) = `[Z_pn]`ᵀ

### 3.2 Implementation Review

**In powercad.py (legacy, 3-phase):**
```python
zabc = zabc - zkn.T * (1.0 / zsn) * zkn
```
This is a simplified single-neutral Kron reduction: `Z_abc = Z_pp - Z_pn · (1/Z_nn) · Z_np` where `zsn` is the scalar neutral self-impedance and `zkn` is the 1×3 mutual vector.

**Status:** CORRECT for single-neutral case, but assumes the neutral is a single conductor (no neutral-neutral mutual terms).

**In overhead_lines.py (new):**
```python
Znn_inv = np.linalg.inv(Znn)
z_abc = Zpp - Zpn @ Znn_inv @ Znp
```
**Status:** CORRECT — generalized for arbitrary M neutrals.

### 3.3 Transposition Assumption (Audit A9)

The legacy code uses a circulating factor matrix:
```python
fmat = [[0.33, 0.33, 0.33],
        [0.33, 0.33, 0.33],
        [0.33, 0.33, 0.33]]
```
This averages the mutual impedances, which is equivalent to assuming full transposition. For untransposed lines, the full 3×3 mutual matrix should be retained.

**overhead_lines.py** supports both modes via the `transposed` parameter.

---

## 4. Fault Analysis

### 4.1 Theory

#### 4.1.1 Three-Phase Fault (ABC)
```
I₁ = V_f / (Z₁ + Z_f)
I_abc = A · [0, I₁, 0]ᵀ
```
Only the positive-sequence network is involved. Ground impedance Zg does NOT appear.

#### 4.1.2 Single-Line-to-Ground Fault (A-G)
```
I₁ = I₂ = I₀ = V_f / (Z₁ + Z₂ + Z₀ + Z_f + 3·Z_g)
I_a = 3·I₁ = 3·V_f / (Z₁ + Z₂ + Z₀ + Z_f + 3·Z_g)
```
With Z₁ = Z₂ (standard for lines/transformers):
```
I_a = 3·V_f / (2·Z₁ + Z₀ + Z_f + 3·Z_g)
```

#### 4.1.3 Line-to-Line Fault (B-C)
```
I₁ = V_f / (Z₁ + Z₂ + Z_f)
I₂ = -I₁
I₀ = 0
I_b = (a² - a)·I₁ = -j·√3·I₁
|I_b| = √3 · V_f / |Z₁ + Z₂ + Z_f|
```

#### 4.1.4 Double-Line-to-Ground Fault (B-C-G)
```
I₁ = V_f / (Z₁ + Z_f/2 + (Z₁+Zf/2)·(Z₀+Zf/2+3Zg) / (Z₁+Z₀+Zf+3Zg))
I₀ = -I₁ · (Z₁ + Z_f/2) / (Z₁ + Z₀ + Z_f + 3·Z_g)
I₂ = -I₁ · (Z₀ + Z_f/2 + 3·Z_g) / (Z₁ + Z₀ + Z_f + 3·Z_g)
```

### 4.2 Implementation Review

**Location:** `pc_classes/powercad.py:442-520` (`ifault`)

| Fault | Code Formula | Assessment |
|-------|-----------|------------|
| 3PH | `vf / (zt + zfault + zgnd)` | **BUG (A3):** zgnd should not be here. Should be `vf / (zt + zfault)` |
| SLG | `vf / (z0t + zt + zt + zfault + 3*zgnd)` | CORRECT (with Z₁=Z₂=zt, this is `vf/(2Z₁+Z₀+Zf+3Zg)`) |
| LL | `vf / (zt + zt + zfault)` for I₁, `-I₁` for I₂ | CORRECT (with Z₁=Z₂=zt) |
| LLG | `I1 = vf/(zt + zfault/2 + (zt+zfault/2)(z0t+zfault/2+3zgnd)/(zt+z0t+zfault+3zgnd))` | I₁ formula CORRECT |
| LLG | `I0 = -I1·(z0t/(zt+z0t))`, `I2 = -I1·(zt/(zt+z0t))` | **BUG (A3/NB-5):** Divider inverted and missing Zf/Zg terms |

### 4.3 LLG Divider Analysis (Detailed)

**Code:**
```python
I1 = vf / (zt + (zfault/2) + ((zt + (zfault/2)) * (z0t + (zfault/2) + (3*zgnd)))
           / (zt + z0t + zfault + (3*zgnd)))
I012 = [[-I1 * (z0t / (zt + z0t))],
        [I1],
        [-I1 * (zt / (zt + z0t))]]
```

**Correct (with Zf, Zg terms):**
```
I0 = -I1 · (Z1 + Zf/2) / (Z1 + Z0 + Zf + 3Zg)
I2 = -I1 · (Z0 + Zf/2 + 3Zg) / (Z1 + Z0 + Zf + 3Zg)
```

**Verification when Zf = Zg = 0:**
- Correct: `I0 = -I1·Z1/(Z1+Z0)`, `I2 = -I1·Z0/(Z1+Z0)`
- Code: `I0 = -I1·Z0/(Z1+Z0)`, `I2 = -I1·Z1/(Z1+Z0)`
- **The code has I0 and I2 SWAPPED.**

**Impact on phase currents:**
```
I_b = I₀ + a²·I₁ + a·I₂
```
With the code's swapped I0/I2, I_b is wrong. However, |I_b| may appear approximately correct because the error partially cancels in the magnitude.

**Ground return current:** `I_g = I_b + I_c = 3·I₀` — this is directly wrong.

---

## 5. Transformer Impedance

### 5.1 Theory

Transformer per-unit impedance on its own base:
```
Z_pu = Z% / 100
```

With X/R ratio:
```
R₁ = Z_pu / √(1 + (X/R)²)
X₁ = R₁ · (X/R)
Z₁ = R₁ + j·X₁
```

Zero-sequence (depends on core type):
- Shell-type: Z₀ ≈ Z₁
- Core-type (3-leg): Z₀ ≈ 0.85·Z₁ (typical for distribution)
- Core-type (5-leg): Z₀ ≈ Z₁

### 5.2 Implementation Review

**Location:** `pc_classes/powercad.py:523-542` (`xfmr`)

```python
def xfmr(self, MVAbase, Zpercent, XRratio=False, results=False, zeromult=1):
    if not testPositiveFloat(XRratio):
        XRratio = self.xrcalc(MVAbase, results)
    z1 = (Zpercent / 100)
    r1 = z1 / np.sqrt(1 + XRratio ** 2)
    x1 = 1j * r1 * XRratio
    r0 = r1 * zeromult
    x0 = x1 * zeromult
    z1 = r1 + x1
    z0 = r0 + x0
    return np.array([[z1], [z0]])
```

**Status:** CORRECT for the given zeromult. Default `zeromult=1` assumes Z₀=Z₁ (shell-type or conservative).

**Issue A8:** For core-type distribution transformers, `zeromult=0.85` would be more accurate. The `distxfmr` table in `dataconstants.py` has per-size data that could provide better defaults.

### 5.3 X/R Curve (xrcalc)

**Location:** `pc_classes/powercad.py:544-595` (`xrcalc`)

Uses the GE xrcurve for deterministic X/R estimation based on transformer MVA base.

**Issue A5:** The 'low' multipliers are inverted:
- `'high'`: ×1.677, ×1.5, ×1.3 (above curve)
- `'low'`: ×(2-1.677)=0.323, ×(2-1.5)=0.5, ×(2-1.3)=0.7 (far below curve)
- `'rlow'`: ×(1 - |1 - N(1,σ)|) (random below curve, centered on 1.0)

The 'low' values (0.323, 0.5, 0.7) are inconsistent with the 'high' values (1.677, 1.5, 1.3). If symmetric, 'low' should be approximately 1/1.677=0.596, 1/1.5=0.667, 1/1.3=0.769.

---

## 6. Line Impedance

### 6.1 Theory

See Section 2 (Carson's Equations) and Section 3 (Kron Reduction).

### 6.2 Implementation Review

**Three-phase (LineType=3):**
- Builds 3×3 Zabc with self-impedances zs and mutual impedances zk
- Applies transposition factor fmat (0.33/0.33/0.33)
- Kron-reduces single neutral
- Sequence transform: `z012 = Ainv * zabc * Amat`
- Extracts Z0, Z1 by summing rows (NOT diagonal elements)

**Issue:** Z0/Z1 extraction uses row summation:
```python
z0 = z012[0, 0] + z012[0, 1] + z012[0, 2]
z1 = z012[1, 0] + z012[1, 1] + z012[1, 2]
```

**Correct:** For a transposed (balanced) line, Z012 is diagonal, so row summation = diagonal element. For untransposed lines, the diagonal elements are the correct sequence impedances:
```python
z0 = z012[0, 0]
z1 = z012[1, 1]
```

Since the code already applies the transposition factor (making Zabc symmetric), the row summation happens to give the same result as the diagonal. But this is fragile — if the transposition factor is removed, the extraction method is wrong.

**Two-phase (LineType=2):** Similar structure with 0.5/0.5 factor.

**Single-phase (LineType=1):**
```python
zkn = resd + 1j * w * f * np.log(De / 1.0)  # 1 ft assumed spacing!
zabc[0, 0] = zsn - (zkn * zkn) / zsn
```

**Issue A1:** The 1 ft neutral spacing is arbitrary. Should use actual geometry from construction CSVs.

---

## 7. Ampacity (IEEE 738)

### 7.1 Theory

IEEE 738 steady-state heat balance:

```
q_c + q_r = q_s + I²·R(T_c)
```

Where:
- `q_c` = convective heat loss (forced + natural)
- `q_r` = radiated heat loss
- `q_s` = solar heat gain
- `R(T_c)` = AC resistance at conductor temperature T_c

Solving for I gives the maximum continuous current (ampacity).

### 7.2 Implementation Review

**Location:** `pc_classes/powercad.py:163-220` (`calcCurrent`, `_conductor_ampacity`), `pc_classes/thermal_ampacity.py`

**In thermal_ampacity.py (new, extracted):**
- CORRECT implementation of IEEE 738
- Handles ACSR (type 3) and Copper (type 1) with proper temperature scaling

**In powercad.py (legacy):**
- **Issue A6:** Copper (type 1) resistance not scaled to operating temperature
  - `resdc` computed at 75°C, then `resac = resdc · resacdc` uses the 75°C value
  - Should scale: `R(T) = R(T_ref) · (1 + α·(T - T_ref))`

**Constants to verify (A6):**
- `wsbase = 100 W/ft²` solar — standard assumption, OK
- Emissivity factor 0.138 — needs verification against IEEE 738
- `currentbase = sqrt(37.7 · d · powerloss / resac)` — the 37.7 constant embeds unit conversions

---

## 8. Voltage Drop

### 8.1 Theory

**Exact per-phase voltage drop (single-phase):**
```
V_drop = V_s - V_r = V_s - √(V_s² - (I·X·cos(φ) - I·R·sin(φ))²) + I·R·cos(φ) + I·X·sin(φ)
```
Wait — let me re-derive. The standard exact formula is:

```
V_r = √((V_s - I·R·cos(φ) - I·X·sin(φ))² + (I·X·cos(φ) - I·R·sin(φ))²)
V_drop = V_s - V_r
```

**Approximate formula (commonly used):**
```
V_drop ≈ I · (R·cos(φ) + X·sin(φ))
```

**Three-phase line-to-line:**
```
V_drop_LL = √3 · I · (R·cos(φ) + X·sin(φ))
```

### 8.2 Implementation Review

**Location:** `pc_classes/powercad.py:621-630` (`calcVoltageDrop`)

```python
rf = np.sin(np.arccos(pf))           # sin(φ) from cos(φ)
vdrop = vs + il * zt[0] * pf + il * zt[1] * rf \
    - np.sqrt(vs ** 2 - (il * zt[1] * pf - il * zt[0] * rf) ** 2)
if phase > 2:
    return vdrop * np.sqrt(3)
elif phase > 1:
    return vdrop * 2
else:
    return vdrop
```

**Analysis:**
```
vdrop = vs + I·R·cos(φ) + I·X·sin(φ) - √(vs² - (I·X·cos(φ) - I·R·sin(φ))²)
```

This is an unusual form. Let me check: the standard exact receiving-end voltage is:
```
V_r = √((V_s - I·R·cos(φ) - I·X·sin(φ))² + (I·X·cos(φ) - I·R·sin(φ))²)
```

The code's formula doesn't match this. Let me expand the code's formula:
```
vdrop = vs - √(vs² - (I·X·cos(φ) - I·R·sin(φ))²) + I·R·cos(φ) + I·X·sin(φ)
```

This appears to be: `V_drop = V_s - V_r' + I·(R·cos(φ) + X·sin(φ))` where `V_r' = √(vs² - (I·X·cos(φ) - I·R·sin(φ))²)`.

This is NOT the standard exact formula. The term under the square root should be the full phasor difference, not just `vs² - (quadrature component)²`.

**Issue A7:** The formula is non-standard. The √3 multiplication for 3-phase is applied to this non-standard per-phase result.

**Recommended:** Replace with the standard approximate formula:
```python
vdrop = il * (zt[0] * pf + zt[1] * rf)  # per-phase
if phase > 2:
    return vdrop * np.sqrt(3)            # 3-phase line-to-line
elif phase > 1:
    return vdrop * 2                      # center-tapped 240V
else:
    return vdrop                          # single-phase
```

---

## 9. Pole Structural Calculations

### 9.1 Theory

Pole structural analysis involves:
1. **Wind loading** on conductors and pole surface
2. **Ice loading** (radial ice on conductors)
3. **Conductor tension** (horizontal and vertical components)
4. **Guy wire tension** (for guys poles)
5. **Moment aggregation** at ground line
6. **Stress check** against pole class strength

### 9.2 Implementation Review

**Location:** `pc_classes/polecad.py`

The polecad module has been fully refactored with:
- `PoleCalcConfig` dataclass for all parameters
- Typed exceptions
- Vectorized calculations
- Bug fixes for Guyy/Guyx typos, comms-guy accumulation, precedence issues

**Status:** Refactored and verified. Mathematical formulas were not independently re-derived in this analysis — recommended as a separate review task.

### 9.3 Key Formulas (from code review)

**Wind force on conductor:**
```
F_wind = P · d · span · sin(θ)
```
Where P = wind pressure, d = diameter (with ice), span = length, θ = angle between wind and conductor.

**Moment at ground line:**
```
M = Σ(F_i · h_i)
```
Where F_i = force on each attachment, h_i = height above ground.

**Guy tension:**
```
T_guy = M / (h_guy · cos(α))
```
Where M = moment to be resisted, h_guy = guy attachment height, α = guy angle.

---

## 10. Discrepancies and Corrections Needed

### 10.1 Confirmed Bugs (need fixing)

| # | Issue | Location | Severity | Fix |
|---|-------|----------|----------|-----|
| 1 | LLG I0/I2 divider swapped | `powercad.py:ifault` | HIGH | Swap formulas, add Zf/Zg terms |
| 2 | 3PH fault includes Zgnd | `powercad.py:ifault` | MEDIUM | Remove zgnd from 3PH path |
| 3 | Frequency scaling of w | `powercad.py:calcImpedance` | LOW | `w = 2.0224e-3 * (f/60)` |
| 4 | xrcalc 'low' multipliers | `powercad.py:xrcalc` | MEDIUM | Fix to symmetric bounds |
| 5 | Copper R not scaled to temp | `powercad.py:calcCurrent` | MEDIUM | Use thermal_ampacity.py |
| 6 | Voltage drop non-standard formula | `powercad.py:calcVoltageDrop` | MEDIUM | Use standard √3·I·(R·cosφ+X·sinφ) |
| 7 | Single-phase 1 ft neutral spacing | `powercad.py:calcImpedance` | HIGH | Use construction CSV geometry |
| 8 | Z0/Z1 extraction by row sum | `powercad.py:calcImpedance` | LOW | Use diagonal elements |

### 10.2 Design Decisions Needed (user input)

| # | Decision | Options |
|---|----------|---------|
| 1 | Transformer Z0 default | 1.0 (current) vs 0.85 (core-type typical) vs table-driven |
| 2 | Single-phase neutral geometry | Use CSV data vs document limitation vs use overhead_lines.py |
| 3 | Transposition assumption | Keep fmat averaging vs support untransposed vs use overhead_lines.py |
| 4 | xrcalc 'low' bounds | Symmetric (1/1.677 etc.) vs current (0.323 etc.) vs user-specified |
| 5 | Legacy calcImpedance | Fix in place vs deprecate in favor of overhead_lines.py |

### 10.3 Verified Correct

| Component | Status |
|-----------|--------|
| Symmetrical component transformation | CORRECT |
| Carson's equations constants (60 Hz) | CORRECT |
| Kron reduction (single neutral) | CORRECT |
| Kron reduction (generalized, overhead_lines.py) | CORRECT |
| SLG fault formula | CORRECT |
| LL fault formula | CORRECT |
| LLG I1 formula | CORRECT |
| Transformer impedance (xfmr) | CORRECT |
| Overhead line impedance (overhead_lines.py) | CORRECT |
| Underground cable impedance (underground_cables.py) | CORRECT (after T-1..T-4 fixes) |
| Thermal ampacity (thermal_ampacity.py) | CORRECT |
| Overhead line capacitance (overhead_lines.py) | CORRECT |

---

## 11. Recommendations

### 11.1 Immediate (P0)
1. Fix LLG fault divider in `powercad.ifault()`
2. Fix 3PH fault zgnd inclusion
3. Resolve single-phase neutral geometry (use CSV data or delegate to overhead_lines.py)

### 11.2 Short-term (P1)
4. Fix frequency scaling in `calcImpedance`
5. Fix xrcalc 'low' multipliers
6. Wire Copper temperature scaling from `thermal_ampacity.py`
7. Replace voltage drop formula with standard form
8. Resolve DATA_AUDIT discrepancies

### 11.3 Medium-term (P2)
9. Deprecate legacy `calcImpedance` in favor of `overhead_lines.py`
10. Wire Radius/X from construction CSVs into impedance calculations
n11. Extract shared `_find_assembly` to common module
12. Automate legacy script regression tests

### 11.4 Long-term (P3)
13. Full documentation of all formulas and assumptions
14. Type hints throughout
15. TCC module review
16. 34.5/46kV and 69kV data audits
