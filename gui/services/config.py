"""Dataclass contracts for the calculation facade.

All units and conventions are documented per field. Complex impedances are
carried as Python complex numbers; matrices as nested tuples to keep the
boundary JSON-serializable for the local web GUI.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TransformerConfig:
    """Transformer impedance inputs.

    mva_base:      transformer nameplate base, MVA
    percent_z:     nameplate percent impedance (e.g. 8.0 for 8%)
    xr_ratio:      X/R ratio; None means estimate from the built-in curve
                   (deterministic interpolation of the GE xrcurve)
    zero_mult:    multiplier applied to Z1 to approximate Z0 (powercad
                   convention: r0 = r1 * zero_mult, x0 = x1 * zero_mult)
    """

    mva_base: float
    percent_z: float
    xr_ratio: Optional[float] = None
    zero_mult: float = 1.0

    def __post_init__(self):
        if self.mva_base <= 0 or self.percent_z <= 0:
            raise ValueError("mva_base and percent_z must be positive")
        if self.xr_ratio is not None and self.xr_ratio <= 0:
            raise ValueError("xr_ratio must be positive")
        if self.zero_mult < 0:
            raise ValueError("zero_mult must be non-negative")


@dataclass
class SourceConfig:
    """Bulk electric system (utility source) inputs.

    Exactly one of fault_mva_3ph / explicit_z1 must be provided; likewise
    exactly one of fault_mva_slg / explicit_z0 / zero_mult must be provided.
    Providing both of a pair raises ValueError.

    When fault_mva_slg is used, Z0 is derived from the SLG loop with the
    loop angle aligned to the positive-sequence angle (same X/R as Z1),
    since magnitude-only duty data cannot determine the Z0 angle.

    base_mva:      system base for per-unit conversion, MVA
    base_kv:      base line-to-line voltage at the source bus, kV
    fault_mva_3ph: three-phase fault duty at the bus, MVA (X/R given)
    fault_mva_slg: single-line-to-ground fault duty at the bus, MVA
    xr_ratio:      X/R of the three-phase fault duty (used for Z1 angle);
                   if None, pure-reactive source assumed
    zero_mult:     Z0 = zero_mult * Z1 shortcut when only 3ph duty is known
    explicit_z1:   Thevenin positive-sequence impedance in per-unit on
                   (base_mva, base_kv) if the utility gave it directly
    explicit_z0:   Thevenin zero-sequence impedance, same convention
    """

    base_mva: float
    base_kv: float
    fault_mva_3ph: Optional[float] = None
    fault_mva_slg: Optional[float] = None
    xr_ratio: Optional[float] = None
    zero_mult: Optional[float] = None
    explicit_z1: Optional[complex] = None
    explicit_z0: Optional[complex] = None

    def __post_init__(self):
        if self.base_mva <= 0 or self.base_kv <= 0:
            raise ValueError("base_mva and base_kv must be positive")
        for name in ("fault_mva_3ph", "fault_mva_slg", "xr_ratio", "zero_mult"):
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive")
        if (self.fault_mva_3ph is None) == (self.explicit_z1 is None):
            raise ValueError(
                "provide exactly one of fault_mva_3ph or explicit_z1"
            )
        if (self.fault_mva_slg is not None and self.explicit_z0 is not None) or (
            self.zero_mult is not None
            and (self.fault_mva_slg is not None or self.explicit_z0 is not None)
        ):
            raise ValueError(
                "provide exactly one of fault_mva_slg, explicit_z0, or zero_mult"
            )
        if (
            self.fault_mva_slg is None
            and self.explicit_z0 is None
            and self.zero_mult is None
        ):
            raise ValueError(
                "provide fault_mva_slg, explicit_z0, or zero_mult"
            )


@dataclass
class FaultConfig:
    """Fault study inputs; impedance list is ordered source to fault point.

    z_pu:          ordered list of per-unit impedance pairs on the study
                   base; each element is (z1, z0) complex per-unit
    vf_pu:         pre-fault voltage at the fault point, per-unit
    zgnd_pu:       per-phase ground (neutral) impedance in the fault path,
                   per-unit (appears as 3*zgnd in the SLG/LLG loops)
    zfault_pu:     arc/fault impedance, per-unit
    base_amps:     base current at the fault-point voltage level, amps
                   (used to convert per-unit results to amps)
    """

    z_pu: list
    vf_pu: float = 1.0
    zgnd_pu: float = 0.0
    zfault_pu: float = 0.0
    base_amps: Optional[float] = None

    def __post_init__(self):
        if not self.z_pu:
            raise ValueError("z_pu must contain at least one (z1, z0) pair")
        if self.vf_pu <= 0:
            raise ValueError("vf_pu must be positive")
        if self.base_amps is not None and self.base_amps <= 0:
            raise ValueError("base_amps must be positive")


@dataclass
class ImpedanceResult:
    """Per-unit impedance result plus unit conversions.

    z1_pu, z0_pu:  positive/zero-sequence impedance, complex per-unit
    r1, x1, r0, x0: real/imaginary components for display
    base_mva, base_kv: study bases used
    z1_ohms, z0_ohms: ohmic values at base_kv (Zpu * Zbase)
    """

    z1_pu: complex
    z0_pu: complex
    base_mva: float
    base_kv: float

    @property
    def r1(self):
        return self.z1_pu.real

    @property
    def x1(self):
        return self.z1_pu.imag

    @property
    def r0(self):
        return self.z0_pu.real

    @property
    def x0(self):
        return self.z0_pu.imag

    @property
    def base_z_ohms(self):
        return self.base_kv ** 2 / self.base_mva

    @property
    def z1_ohms(self):
        return self.z1_pu * self.base_z_ohms

    @property
    def z0_ohms(self):
        return self.z0_pu * self.base_z_ohms


@dataclass
class FaultResult:
    """Fault currents at a single node, sequence and phase domains.

    Sequence and phase quantities are stored in per-unit (complex) and,
    when a base current is supplied, also in amps (magnitude).
    Index conventions follow powercad.ifault rows: 0 SLG, 1 LL,
    2 LLG, 3 3ph.
    """

    i_slg_pu: complex
    i_ll_pu: complex
    i_llg_pu: complex
    i_3ph_pu: complex
    base_amps: Optional[float] = None

    @property
    def i_slg_amps(self):
        return abs(self.i_slg_pu) * self.base_amps if self.base_amps else None

    @property
    def i_ll_amps(self):
        return abs(self.i_ll_pu) * self.base_amps if self.base_amps else None

    @property
    def i_llg_amps(self):
        return abs(self.i_llg_pu) * self.base_amps if self.base_amps else None

    @property
    def i_3ph_amps(self):
        return abs(self.i_3ph_pu) * self.base_amps if self.base_amps else None


@dataclass
class VoltageDropResult:
    """Voltage drop result in volts (per powercad calcVoltageDrop)."""

    drop_volts: float
    vs: float
    phase: int
