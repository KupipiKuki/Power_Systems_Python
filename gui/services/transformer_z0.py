"""Transformer zero-sequence models by winding connection.

Model per docs/qa/phase1_test_cases.md Section 2:
- GrdY-GrdY: zero-sequence flows through both grounded neutrals;
  Z0 = zeromult * Z1 from either side.
- GrdY-Delta / Delta-GrdY: zero-sequence flows only on the grounded-wye
  side; the delta side is an open circuit for external zero-sequence
  current (delta provides a circulating path but blocks external flow).
- Delta-Delta: no external zero-sequence path from either side; the
  delta windings only support internal circulating current.

A return of None means "open circuit for zero-sequence" (Z0 = inf).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .config import ImpedanceResult, TransformerConfig


class WindingConnection(Enum):
    """Transformer winding connection relevant to zero-sequence flow."""

    GROUNDED_WYE = "grdy"   # neutral solidly grounded: passes zero-seq
    UNGROUNDED_WYE = "y"    # floating neutral: blocks zero-seq
    DELTA = "delta"         # blocks external zero-seq (circulates internally)

    @classmethod
    def from_string(cls, value):
        if isinstance(value, cls):
            return value
        return cls(str(value).lower())


def _passes_zero_sequence(connection):
    return connection is WindingConnection.GROUNDED_WYE


@dataclass
class TransformerZ0Result:
    """Zero-sequence impedance seen from each side of the transformer.

    A side with z0_pu=None is an open circuit for zero-sequence current
    from that side (SLG/LLG faults there have no zero-sequence path
    through the transformer).
    """

    z0_primary_pu: Optional[complex]
    z0_secondary_pu: Optional[complex]
    connection_primary: WindingConnection
    connection_secondary: WindingConnection

    @property
    def zero_sequence_path_exists(self):
        """True if zero-sequence current can reach the secondary system."""
        return _passes_zero_sequence(self.connection_secondary)


def transformer_zero_sequence(config):
    """Zero-sequence model for a two-winding transformer.

    config: TransformerConfig extended with primary_connection and
    secondary_connection (see transformer_impedance_inputs); uses the
    same zeromult convention as powercad.xfmr (r0 = r1*zeromult,
    x0 = x1*zeromult).
    """
    primary = WindingConnection.from_string(config.primary_connection)
    secondary = WindingConnection.from_string(config.secondary_connection)

    z1 = transformer_z1(config)

    # Zero-sequence impedance exists on a side only if that side's
    # winding passes zero-sequence current (grounded-wye neutral).
    z0 = z1 * config.zero_mult
    z0_primary = z0 if _passes_zero_sequence(primary) else None
    z0_secondary = z0 if _passes_zero_sequence(secondary) else None

    return TransformerZ0Result(
        z0_primary_pu=z0_primary,
        z0_secondary_pu=z0_secondary,
        connection_primary=primary,
        connection_secondary=secondary,
    )


def transformer_z1(config):
    """Positive-sequence impedance on the transformer's own MVA base."""
    r1 = (config.percent_z / 100.0) / (1.0 + config.xr_ratio ** 2) ** 0.5
    return complex(r1, r1 * config.xr_ratio)
