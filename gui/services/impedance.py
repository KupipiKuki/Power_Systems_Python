"""Facade implementations wrapping pc_classes.powercad.

Implementation notes:
- faultCalculationClass reads its CSV databases via paths relative to the
  repository root ('./pc_classes/pc_data/...'), so _engine() pins the
  working directory while instantiating the class.
- The stochastic X/R modes of powercad ('rand', 'rlow', 'rhigh') are
  intentionally not exposed; xr_ratio=None selects the deterministic
  xrcurve interpolation.
"""

import cmath
import contextlib
import math
import os

import numpy as np

# pc_classes predates NumPy 2.0, which removed np.mat (used in
# datafunctions.generate_transforms). Shim it at import time so the facade
# works on modern NumPy without editing the refactor-in-flight modules.
if not hasattr(np, "mat"):
    np.mat = np.asmatrix

from .config import (
    FaultConfig,
    FaultResult,
    ImpedanceResult,
    SourceConfig,
    TransformerConfig,
    VoltageDropResult,
)


@contextlib.contextmanager
def _repo_cwd():
    prev = os.getcwd()
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.chdir(root)
    try:
        yield
    finally:
        os.chdir(prev)


_ENGINE = None


def _engine():
    global _ENGINE
    if _ENGINE is None:
        from pc_classes.powercad import faultCalculationClass

        with _repo_cwd():
            _ENGINE = faultCalculationClass()
    return _ENGINE


def _xr_estimate(mva_base):
    """Deterministic X/R from the built-in GE curve (powercad else-branch)."""
    engine = _engine()
    return float(engine.xrcalc(mva_base, "curve"))


def transformer_impedance(config, base_kv=None):
    """Per-unit transformer impedance on the transformer MVA base.

    base_kv (line-to-line, kV) is only used for the ohmic conversions on
    the returned ImpedanceResult; it does not affect the per-unit math.
    """
    engine = _engine()
    xr = config.xr_ratio if config.xr_ratio is not None else _xr_estimate(config.mva_base)
    z = engine.xfmr(config.mva_base, config.percent_z, xr, False, config.zero_mult)
    return ImpedanceResult(
        z1_pu=complex(z[0, 0]),
        z0_pu=complex(z[1, 0]),
        base_mva=config.mva_base,
        base_kv=base_kv if base_kv is not None else 0.0,
    )


def _z_from_pu_magnitude(mag_pu, xr):
    """Complex per-unit Z from magnitude and X/R (90 degrees if X/R unknown)."""
    if xr is None or xr == 0:
        return complex(0.0, mag_pu)
    r = mag_pu / np.sqrt(1.0 + xr ** 2)
    return complex(r, r * xr)


def source_impedance(config):
    """Thevenin source Z1/Z0 in per-unit on (base_mva, base_kv).

    Cases:
    - fault_mva_3ph given:  |Z1| = base_mva / fault_mva_3ph, angle from X/R
      (or 90 degrees if X/R unknown).
    - explicit_z1 given: used directly.
    - Z0: explicit_z0, or from fault_mva_slg via the SLG loop
      Z0 = 3*E/I_slg_base - 2*Z1 (with Z2=Z1 and E=1 pu), or the
      zero_mult shortcut.
    """
    if config.explicit_z1 is not None:
        z1 = config.explicit_z1
    else:
        z1 = _z_from_pu_magnitude(
            config.base_mva / config.fault_mva_3ph, config.xr_ratio
        )
    if config.explicit_z0 is not None:
        z0 = config.explicit_z0
    elif config.fault_mva_slg is not None:
        # SLG duty MVA (three-phase equivalent, IEEE C37.010 convention):
        # S_slg = S_base * |3 / (2*Z1 + Z0)|  =>  |2*Z1 + Z0| = 3*S_base/S_slg.
        # The loop impedance angle is unknown from magnitude data alone, so
        # align it with the positive-sequence angle (same X/R as Z1).
        z_loop_mag = 3.0 * config.base_mva / config.fault_mva_slg
        theta = cmath.phase(z1) if z1 != 0 else math.pi / 2.0
        z_loop = cmath.rect(z_loop_mag, theta)
        z0 = z_loop - 2.0 * z1
        if z0.imag < 0 or z0.real < 0:
            raise ValueError(
                "derived zero-sequence impedance is not passive "
                f"(Z0={z0}); check fault_mva_slg and xr_ratio"
            )
    else:
        z0 = z1 * config.zero_mult
    return ImpedanceResult(
        z1_pu=z1,
        z0_pu=z0,
        base_mva=config.base_mva,
        base_kv=config.base_kv,
    )


def fault_currents(config):
    """Series-network fault currents via powercad.ifault.

    All (z1, z0) pairs in FaultConfig.z_pu are summed (source to fault
    point) into the single two-row impedance matrix ifault expects.
    """
    engine = _engine()
    z1 = sum((pair[0] for pair in config.z_pu), 0j)
    z0 = sum((pair[1] for pair in config.z_pu), 0j)
    zlt = np.array([[z1], [z0]])
    iabc = engine.ifault(zlt, config.vf_pu, config.zgnd_pu, config.zfault_pu, 0)
    # ifault blocks are [SLG A-G | LL BC | LLG BC-G | 3ph ABC], phase a on
    # top of each block. For LL/LLG phase a is unfaulted (zero); the faulted
    # phase currents are b (rows 4, 7) and c (rows 5, 8).
    i_ll_b = complex(iabc[4, 0])
    i_llg_b = complex(iabc[7, 0])
    return FaultResult(
        i_slg_pu=complex(iabc[0, 0]),
        i_ll_pu=i_ll_b,
        i_llg_pu=i_llg_b,
        i_3ph_pu=complex(iabc[9, 0]),
        base_amps=config.base_amps,
    )


def voltage_drop(zt, vs, il, pf, phase):
    """Wrap powercad.calcVoltageDrop; see its docstring for conventions."""
    engine = _engine()
    drop = engine.calcVoltageDrop(zt, vs, il, pf, phase)
    return VoltageDropResult(drop_volts=float(drop), vs=vs, phase=phase)
