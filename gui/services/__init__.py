"""Calculation facade for the impedance GUI.

This package is the only seam between the GUI and pc_classes. It wraps
faultCalculationClass behind dataclass-in/dataclass-out functions so the
in-flight powercad/polecad refactors can proceed underneath without
breaking GUI code. No pc_classes internals leak past this boundary.
"""

from .config import (
    TransformerConfig,
    SourceConfig,
    FaultConfig,
    ImpedanceResult,
    FaultResult,
    OverheadLineConfig,
    OverheadLineConductorConfig,
    ConductorPositionConfig,
    LineImpedanceResult,
    UndergroundCableConfig,
)
from .impedance import (
    transformer_impedance,
    source_impedance,
    fault_currents,
    voltage_drop,
    overhead_line_impedance,
    underground_cable_impedance,
)

__all__ = [
    "TransformerConfig",
    "SourceConfig",
    "FaultConfig",
    "ImpedanceResult",
    "FaultResult",
    "OverheadLineConfig",
    "OverheadLineConductorConfig",
    "ConductorPositionConfig",
    "LineImpedanceResult",
    "UndergroundCableConfig",
    "transformer_impedance",
    "source_impedance",
    "fault_currents",
    "voltage_drop",
    "overhead_line_impedance",
    "underground_cable_impedance",
]
