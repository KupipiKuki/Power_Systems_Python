"""Network assembly: BES source + transformer + line segments -> faults.

All internal math is on a common per-unit base (config.base_mva).
Element conversions:
- Source (from SourceConfig): already per-unit on base_mva.
- Transformer: nameplate per-unit on its own MVA base rebased by
  z_pu * base_mva / mva_rating (NOTE: 25 MVA -> 100 MVA base multiplies
  by 4, per the Gemini audit correction to corpus section 4.4).
- Line segment (ohms at its voltage level): z_pu = z_ohms * base_mva / kv^2.

Zero-sequence path logic (fault on the secondary system):
- Source Z0 is in the path only if the transformer primary passes
  zero-sequence (grounded-wye primary).
- Transformer Z0 is in the path only if the secondary passes
  zero-sequence (grounded-wye secondary).
- If the path is open, SLG and LLG fault currents are None (no
  zero-sequence return path through the source).
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional

from .config import FaultConfig, FaultResult, SourceConfig, TransformerConfig
from .impedance import fault_currents, source_impedance
from .transformer_z0 import (
    WindingConnection,
    _passes_zero_sequence,
    transformer_z1,
    transformer_zero_sequence,
)


@dataclass
class LineSegment:
    """A series line segment with ohmic sequence impedances.

    z1_ohms, z0_ohms: total (not per-unit-length) sequence impedances
    kv:                line-to-line voltage level of the segment
    """

    z1_ohms: complex
    z0_ohms: complex
    kv: float

    def to_per_unit(self, base_mva):
        base_z = self.kv ** 2 / base_mva
        return self.z1_ohms / base_z, self.z0_ohms / base_z


@dataclass
class NetworkConfig:
    """Radial network: source -> transformer -> segments -> fault.

    source:      SourceConfig; base_kv is the transformer primary voltage
    transformer: TransformerConfig (with primary/secondary connections);
                 mva_base is the nameplate rating
    primary_kv:  transformer primary line-to-line voltage, kV
    secondary_kv: transformer secondary line-to-line voltage, kV
    segments:    series line segments on the secondary system (all at
                 secondary_kv unless a segment carries its own kv)
    vf_pu:       pre-fault voltage at the fault point
    zgnd_pu, zfault_pu: fault-path impedances on the study base
    """

    base_mva: float
    source: SourceConfig
    transformer: TransformerConfig
    primary_kv: float
    secondary_kv: float
    segments: List[LineSegment] = field(default_factory=list)
    vf_pu: float = 1.0
    zgnd_pu: float = 0.0
    zfault_pu: float = 0.0

    def __post_init__(self):
        if self.primary_kv <= 0 or self.secondary_kv <= 0:
            raise ValueError("primary_kv and secondary_kv must be positive")
        if self.source.base_kv != self.primary_kv:
            raise ValueError(
                "source base_kv must equal transformer primary_kv "
                f"({self.source.base_kv} != {self.primary_kv})"
            )
        if self.vf_pu <= 0:
            raise ValueError("vf_pu must be positive")


@dataclass
class NetworkResult:
    """Assembled per-unit network totals and fault currents at the end node."""

    z1_total_pu: complex
    z0_total_pu: Optional[complex]  # None = zero-sequence path open
    base_mva: float
    fault_kv: float
    fault: Optional[FaultResult]  # None when zero-seq path open (use 3ph/ll)

    @property
    def base_amps(self):
        return self.base_mva * 1e6 / (self.fault_kv * 1e3 * math.sqrt(3))

    @property
    def i_3ph_pu(self):
        if self.fault is not None:
            return self.fault.i_3ph_pu
        return None

    @property
    def i_3ph_amps(self):
        if self.fault is not None:
            return self.fault.i_3ph_amps
        return None

    @property
    def i_slg_pu(self):
        """None when the zero-sequence path is open (no SLG return path)."""
        if self.fault is not None:
            return self.fault.i_slg_pu
        return None

    @property
    def i_ll_pu(self):
        if self.fault is not None:
            return self.fault.i_ll_pu
        return None


def assemble_network(config):
    """Sum the network into per-unit Z1/Z0 totals and compute faults.

    Returns NetworkResult; SLG/LLG are None (via fault=None and
    z0_total_pu=None) when the winding connections block the
    zero-sequence path.
    """
    # Source
    src = source_impedance(config.source)
    z1_total = src.z1_pu

    # Transformer on the study base (audit-corrected rebasing)
    xfmr_z1_pu = transformer_z1(config.transformer) * (
        config.base_mva / config.transformer.mva_base
    )
    z1_total += xfmr_z1_pu

    z0_model = transformer_zero_sequence(config.transformer)
    # Zero-sequence path (fault on the secondary system):
    z0_parts = []
    if z0_model.zero_sequence_path_exists:
        if _passes_zero_sequence(z0_model.connection_primary):
            z0_parts.append(src.z0_pu)
        if z0_model.z0_secondary_pu is not None:
            z0_parts.append(
                z0_model.z0_secondary_pu
                * config.base_mva
                / config.transformer.mva_base
            )
    z0_total = sum(z0_parts, 0j) if z0_parts else None

    # Line segments (ohms at their voltage level)
    for segment in config.segments:
        z1_seg, z0_seg = segment.to_per_unit(config.base_mva)
        z1_total += z1_seg
        if z0_total is not None:
            z0_total += z0_seg

    fault_kv = config.segments[-1].kv if config.segments else config.secondary_kv
    base_amps = config.base_mva * 1e6 / (fault_kv * 1e3 * math.sqrt(3))

    if z0_total is None:
        # Open zero-sequence path: 3ph and LL still computable directly.
        return NetworkResult(
            z1_total_pu=z1_total,
            z0_total_pu=None,
            base_mva=config.base_mva,
            fault_kv=fault_kv,
            fault=None,
        )

    result = fault_currents(
        FaultConfig(
            z_pu=[(z1_total, z0_total)],
            vf_pu=config.vf_pu,
            zgnd_pu=config.zgnd_pu,
            zfault_pu=config.zfault_pu,
            base_amps=base_amps,
        )
    )
    return NetworkResult(
        z1_total_pu=z1_total,
        z0_total_pu=z0_total,
        base_mva=config.base_mva,
        fault_kv=fault_kv,
        fault=result,
    )
