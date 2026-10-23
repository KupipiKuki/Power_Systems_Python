"""Facade implementations wrapping pc_classes.powercad.

Implementation notes:
- faultCalculationClass reads its CSV databases via paths relative to the
  repository root ('./pc_classes/pc_data/...'), so _engine() pins the
  working directory while instantiating the class.
- The stochastic X/R modes of powercad ('rand', 'rlow', 'rhigh') are
  intentionally not exposed; xr_ratio=None selects the deterministic
  xrcurve interpolation.
"""

import contextlib
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
        # SLG loop: E/I = Z1 + Z2 + Z0 = 2*Z1 + Z0 (Z2 = Z1, E = 1 pu)
        z_loop = config.base_mva / config.fault_mva_slg
        z0 = z_loop - 2.0 * z1
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
    return FaultResult(
        i_slg_pu=complex(iabc[0, 0]),
        i_ll_pu=complex(iabc[3, 0]),
        i_llg_pu=complex(iabc[6, 0]),
        i_3ph_pu=complex(iabc[9, 0]),
        base_amps=config.base_amps,
    )


def voltage_drop(zt, vs, il, pf, phase):
    """Wrap powercad.calcVoltageDrop; see its docstring for conventions."""
    engine = _engine()
    drop = engine.calcVoltageDrop(zt, vs, il, pf, phase)
    return VoltageDropResult(drop_volts=float(drop), vs=vs, phase=phase)
