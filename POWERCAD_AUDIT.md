# POWERCAD_AUDIT — calculation audit of `pc_classes/powercad.py`

Scope: refactor of `powercad` (session 3, branch `vibe/powercad-refactor`),
following the polecad refactor on `vibe/polecad-refactor-c349b2`.
Policy chosen by the user: **refactor structure; flag every suspect
calculation for review; fix only unambiguous errors.**

Verification baselines: `PowerCadTests/temptest1/condfcc.csv` and
`temptest2/condfcc.csv` (checked in before the refactor; regenerated after).

---

## 1. Unambiguous bugs FIXED in this refactor

### F1. Phase-spacing formula used `+` instead of `-` (towerCalc)
Legacy computed every phase-pair and phase-neutral distance as
`hypot(Xa + Xb, Ha + Hb)`. Construction `X` columns are **signed**
crossarm offsets (e.g. B6-21: Phase1X=-42", Phase2X=+42", same height),
so the plus-form gives the nonsense result `AB = 3.0 ft` for a 7 ft
crossarm (true spacing 7.0 ft) and a wrong phase-neutral distance
(4.61 ft vs. true 3.5 ft for B6-21). For C1.11 the plus-form even
produced `CA = 0.83 ft` for conductors 88 in. apart (true 7.33 ft).
Fixed to the coordinate difference `hypot(Xa - Xb, Ha - Hb)`.
Affected outputs: `AB/BC/CA/AN/BN/CN`, and consequently all
`Z0*/Z1*` values in both test projects.

### F2. `conddb.Span` unit bug (feet used as miles)
`poledb.Span` was converted ft→miles, but a `Span` supplied directly in
`conddb.csv` (same ft values as poledb: 131.0, 340.0) was used **as-is**
when multiplying the per-mile impedance matrix. Every study section with
an explicit conductor span was overstated by ×5280 (e.g. temptest1 study
24290/01427: `Z1real` 2217 Ω → 0.42 Ω). Fixed: explicit conductor spans
are converted ft→miles like poledb spans.

### F3. B-table lookup fallback searched the wrong column
The `B` assembly fallback path (`Bcon.Name == test` twice) never
searched `AltName` (copy-paste from the A path). Unified into a single
`_find_assembly()` shared by all families — same resolution chain as
polecad (exact Name → Name contains → exact AltName → AltName contains,
ambiguity raises `UnknownAssemblyError`).

### F4. Per-pole span replaced by the group's first-row span
Legacy `calcImpedance` multiplied every section by
`pl1.iat[0, Span]` — the span of the **first row of the study group**,
not the pole being calculated. Combined with F2 this produced
cross-contaminated impedances (temptest1 study `1290` shows sections
with 257 Ω and 2460 Ω for identical 131 ft construction — the 2460 Ω
row inherited a 1127 ft span from a different pole). Fixed: each
section uses its own pole's span. NOTE: with F2 fixed, the remaining
per-section spans are poledb-derived; the legacy numbers were wrong
either way.

### F5. Pandas-3 compatibility
- Integer-typed `Span` columns crash on float write-back
  (`temptest2` failed outright on pandas 3.0.6 before the refactor);
  spans are now coerced to float.
- `np.NaN` → `np.nan`; legacy `.iat[...]` cell loops replaced with
  explicit row iteration and `at[]` writes.
- Index-sorted outputs (row order differs from legacy CSVs; values are
  keyed by `StudyPoleTag/PoleTag/PoleNumber`).

---

## 2. Flagged for user review — NOT changed (math as-is)

### A1. Single-phase (LineType 1) impedance branch
The single-phase fallback uses `zkn = resd + jw·f·log(De/1)` — an
assumed 1 ft phase-neutral spacing — and `zsn` identical to `zsa`
(same conductor). Also, rows matching combined multi-assembly names
(e.g. `A5.01,A5.02,A5.03` in `7200_A.csv`) carry **no neutral
geometry**, so `AN` stays NaN and the branch cannot do better.
**Decision needed:** intended neutral spacing for single-phase
assemblies, or geometry data for combined rows. temptest1 study
24290/25520 (`A5.01`) is affected: its Z values are not trustworthy.

### A2. Frequency scaling of the reactance coefficient
`w = 2.0224e-3` and `resd = 1.588e-3·f` are the 60 Hz Carson
constants. `resd` is scaled by `f` but `w` is not; at any frequency
other than 60 Hz the reactance term is inconsistent (should scale
roughly with f, and `De` is itself frequency-dependent:
`De = 2160·sqrt(ρ/f/60)` style). Since `PowerCalcConfig` now exposes
`frequency`, either restrict to 60 Hz (validate) or implement proper
frequency scaling. Currently only 60 Hz is exercised.

### A3. `ifault` BC-G (double-line-to-ground) sequence distribution
The active code uses
`I0 = -I1·z0t/(zt+z0t)`, `I2 = -I1·zt/(zt+z0t)` — which is only exact
for `zfault = zgnd = 0`, while `I1` itself is computed **with**
zfault/zgnd terms (inconsistent mixture). Two alternative formulas are
left commented in the legacy source (the first one, using
`zt+zfault`, is the standard textbook form for LLG). **Decision
needed:** which reference formula to adopt (standard symmetrical
component LLG: `I1 = V/((Z1+Zf/2) + (Z1+Zf/2)(Z0+Zf/2+3Zg)/
(Z0+Z1+Zf+3Zg))`, `I0 = -I1·(Z1+Zf/2)/(Z1+Z0+Zf+3Zg)` etc.).
Also flagged: the 3-phase-to-ground branch uses `vf/(zt+zfault+zgnd)`
— `zgnd` does not belong in the positive-sequence path of a 3PH fault
(should be `vf/(zt+zfault)` for a solid or arcing 3PH fault).

### A4. SLG fault denominator
A-G uses `vf/(z0 + 2·z1 + zfault + 3·zgnd)` — the standard form is
`vf/(z1+z2+z0+zfault+3Zg)` with `z1 = z2`; the code's
`z0t + zt + zt` matches this only if `zt` is the positive-sequence
impedance **and z2 = z1** — true for lines/transformers, but the
naming (`zt` doubles as z1 and z2) should be documented.

### A5. `xrcalc` "low" multipliers
`results='low'` multiplies the GE curve by `(2-1.677)`, `(2-1.5)`,
`(2-1.3)` — i.e. 0.323, 0.5, 0.7 — which look like an inverted-range
mistake (compare `'high'`: ×1.677/1.5/1.3, and `'rlow'` uses
`1-abs(...)` around 1.0). The `'low'` branch drives X/R far below the
curve while `'high'` is above it; asymmetric. **Decision needed**
intended bounds (presumably symmetric to `high`).

### A6. Ampacity (`calcCurrent`) constants
The IEEE 738-style heat balance carries several oddities kept
as-is (results were previously accepted as ~90%+ accurate):
- `tf = (tempcond + tempamb)/2` — "temperature ratio" should probably
  be the **film temperature** `(tempcond + tempamb)/2` in °C — this is
  actually consistent with IEEE 738's `Tf`; OK, but confirm units of the
  viscosity/conductivity fits (they are the IEEE 738 air-property fits).
- `wsbase` hardcodes 100 W/ft² solar, `wr` uses a 0.138 emissivity
  product with a hardcoded factor; `currentbase = sqrt(37.7·d·powerloss
  / resac)` — the 37.7 constant embeds unit conversions; verify against
  IEEE 738-2012 §"Conductor temperature" for your conductor table.
- Copper (type 1) resistance scaling computes `resdc` at 75 °C then
  never re-scales `resac` to the actual conductor temperature
  (`resac = resdc·resacdc` uses the 75 °C `resdc`, unlike type 3 which
  scales to `tempamb+temprise`). **Likely a bug** — flagged rather than
  fixed because type-1 output feeds accepted baselines.
- The `windval <= 0` natural-convection branch uses `0.283·sqrt(pf)…`
  (IEEE 738 form) — OK.

### A7. `calcVoltageDrop` 3PH/1PH multiplier
Uses `sqrt(vs² - …)` exact-form drop, then multiplies by √3 for
3-phase and 2 for center-tapped 120/240. The √3 form is a
line-to-line approximation applied to a per-phase drop; the center-
tapped ×2 assumes equal split of the 240 V halves. Both are
approximations — document or replace with the standard
`√3·I·(R·cosφ + X·sinφ)` formula for 3φ.

### A8. Transformer zero-sequence default
`xfmr(..., zeromult=1)` assumes Z0 = Z1. For core-type distribution
transformers Z0 ≈ 0.85·Z1 and for shell-type ≈ 1.0; `distxfmr` table in
`dataconstants.py` has per-size R/X but is unused by `xfmr`. Consider
wiring the RUS table in when the user's revised documentation lands.

### A9. Kron reduction for untransposed lines
The 3φ `zk` mutual-impedance matrix uses the `0.33/0.33/0.33`
circulating factor (`fmat`) — an implicit full-transposition
assumption. Untransposed line impedance would keep the full
`zab/zbc/zca` matrix (matrix Zabc, sequence transform without
averaging). Current approach is the standard "transposed" simplification
and fine for distribution; documented here for completeness.

---

## 3. API changes (no backward compatibility, per prior decision)

- `faultCalculationClass()` → `faultCalculationClass(PowerCalcConfig)`
  with a `PowerCalcConfig` dataclass (`project_name`, `project_dir`,
  `frequency=60`, `environmenttype=3`, `voltage_family='7200'`,
  `ampacity_env=AmpacityEnvironment()`).
- `calcImpedanceLaunch(...)` / `calcVoltDropLaunch(...)` (4 positional
  args) replaced by `run()` (loads poledb/conddb, runs `calcCurrent` +
  `calcImpedance`, writes `condfcc.csv`, returns the conddb frame).
- `calcImpedance(environmenttype, f)` → `calcImpedance()` (config-driven);
  `towerCalc()` unchanged in signature.
- Typed exceptions: `PowerCalcError` base, `MissingColumnError`,
  `UnknownAssemblyError`, `UnknownConductorError`, `InvalidGeometryError`.
  Bad input raises instead of silently defaulting (missing Assembly on a
  study-pole row now raises `InvalidGeometryError`; unknown conductor
  raises `UnknownConductorError` with the offending row).
- `calcCurrent` no longer silently assigns TAmb/TRise per-cell via
  try/except column probing; defaults are explicit (25/50 °C).
- Assembly lookup is scoped by `voltage_family` (same family tables as
  polecad) with shared `_find_assembly` logic.

## 4. Updated consumers

- `temptest1.py`, `temptest2.py`, `test1.py`, `xfmrTest.py`,
  `VoltageDropTest.py` — new API.
- Regenerated `PowerCadTests/temptest{1,2}/condfcc.csv` (row order now
  index-sorted; geometry/unit fixes change Z values as described in F1,
  F2, F4).
