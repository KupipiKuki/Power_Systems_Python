"""Facade smoke/unit tests.

Expected values are hand-derived in each docstring so they remain valid
even if powercad internals change, per the Phase 0 audit requirement.

Run from the repository root:
    python -m pytest gui/tests/test_services.py -v
"""

import cmath
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gui.services import (
    FaultConfig,
    FaultResult,
    ImpedanceResult,
    SourceConfig,
    TransformerConfig,
    fault_currents,
    source_impedance,
    transformer_impedance,
    voltage_drop,
)


class TestTransformer:
    def test_xfmr_basic(self):
        # 20 MVA, 8% Z, X/R = 12:
        # |Z| = 0.08 pu, r1 = 0.08/sqrt(1+144) = 0.006659,
        # x1 = r1*12 = 0.0799. zeromult 0.9 scales both for z0.
        res = transformer_impedance(TransformerConfig(20.0, 8.0, xr_ratio=12.0, zero_mult=0.9))
        r1 = 0.08 / math.sqrt(1 + 144)
        assert res.z1_pu.real == pytest.approx(r1, rel=1e-9)
        assert res.z1_pu.imag == pytest.approx(r1 * 12, rel=1e-9)
        assert res.z0_pu == pytest.approx(0.9 * res.z1_pu, rel=1e-9)
        assert res.base_mva == 20.0

    def test_xfmr_default_xr_deterministic(self):
        # xr_ratio=None must produce the same value every call (curve interp).
        a = transformer_impedance(TransformerConfig(10.0, 5.75))
        b = transformer_impedance(TransformerConfig(10.0, 5.75))
        assert a.z1_pu == b.z1_pu
        # |Z| preserved regardless of X/R estimate
        assert abs(a.z1_pu) == pytest.approx(0.0575, rel=1e-9)

    def test_xfmr_ohms_conversion(self):
        # 25 MVA base, 12.47 kV: Zbase = 12.47^2/25 = 6.2201 ohm
        res = transformer_impedance(
            TransformerConfig(25.0, 8.0, xr_ratio=10.0), base_kv=12.47
        )
        zbase = 12.47 ** 2 / 25.0
        assert abs(res.z1_pu) == pytest.approx(0.08, rel=1e-9)
        assert abs(res.z1_ohms) == pytest.approx(0.08 * zbase, rel=1e-6)


class TestSource:
    def test_source_from_3ph_mva(self):
        # 100 MVA base, 2500 MVA 3ph duty, X/R = 10:
        # |Z1| = 100/2500 = 0.04 pu; r = 0.04/sqrt(101) = 0.00398
        cfg = SourceConfig(
            base_mva=100.0,
            base_kv=115.0,
            fault_mva_3ph=2500.0,
            xr_ratio=10.0,
            zero_mult=3.0,
        )
        res = source_impedance(cfg)
        assert abs(res.z1_pu) == pytest.approx(0.04, rel=1e-9)
        assert res.z0_pu == pytest.approx(3.0 * res.z1_pu, rel=1e-9)

    def test_source_from_slg_mva(self):
        # Z1 from 3ph duty (0.05 pu, X/R=8); SLG duty 2000 MVA on 100 MVA base:
        # z_loop = 100/2000 = 0.05 pu => Z0 = 0.05 - 2*Z1
        cfg = SourceConfig(
            base_mva=100.0,
            base_kv=115.0,
            fault_mva_3ph=2000.0,
            fault_mva_slg=2000.0,
            xr_ratio=8.0,
        )
        z1 = 0.05 / math.sqrt(65) * (1 + 8j)
        res = source_impedance(cfg)
        assert res.z1_pu == pytest.approx(z1, rel=1e-9)
        assert res.z0_pu == pytest.approx(0.05 - 2 * z1, rel=1e-9)

    def test_source_explicit(self):
        cfg = SourceConfig(base_mva=100.0, base_kv=115.0, explicit_z1=0.02 + 0.1j, explicit_z0=0.06 + 0.3j)
        res = source_impedance(cfg)
        assert res.z1_pu == 0.02 + 0.1j
        assert res.z0_pu == 0.06 + 0.3j

    def test_source_requires_inputs(self):
        with pytest.raises(ValueError):
            SourceConfig(base_mva=100.0, base_kv=115.0)
        with pytest.raises(ValueError):
            SourceConfig(base_mva=100.0, base_kv=115.0, fault_mva_3ph=2000.0)


class TestFaultCurrents:
    def test_infinite_bus_transformer_fault(self):
        # Mirrors xfmrTest.py: 20 MVA, 8% Z, X/R=False -> deterministic here.
        # Infinite bus: only transformer Z in the network, vf = 1.05 pu.
        zxf = transformer_impedance(
            TransformerConfig(20.0, 8.0, xr_ratio=20.0, zero_mult=0.9)
        )
        # Refloat xfmrTest convention: zxfmr scaled *100/20 -> on 100 MVA base
        z1 = zxf.z1_pu * 100.0 / 20.0
        z0 = zxf.z0_pu * 100.0 / 20.0
        res = fault_currents(
            FaultConfig(z_pu=[(z1, z0)], vf_pu=1.05, base_amps=100e6 / (12.47e3 * math.sqrt(3)))
        )
        # 3ph: I = vf/z1
        assert res.i_3ph_pu == pytest.approx(1.05 / z1, rel=1e-9)
        # SLG: I = 3*vf/(2*z1+z0)
        assert res.i_slg_pu == pytest.approx(3 * 1.05 / (2 * z1 + z0), rel=1e-9)
        assert res.i_3ph_amps is not None and res.i_3ph_amps > 0

    def test_series_summation(self):
        # Two segments must sum before ifault: z totals 0.02+0.05j each seq.
        res = fault_currents(
            FaultConfig(z_pu=[(0.01 + 0.02j, 0.03 + 0.06j), (0.01 + 0.03j, 0.03 + 0.06j)], vf_pu=1.0)
        )
        z1 = 0.02 + 0.05j
        z0 = 0.06 + 0.12j
        assert res.i_3ph_pu == pytest.approx(1.0 / z1, rel=1e-9)
        assert res.i_slg_pu == pytest.approx(3.0 / (2 * z1 + z0), rel=1e-9)

    def test_indices_match_powercad(self):
        # Cross-check facade extraction against raw ifault output rows
        # (row 0 = SLG phase a, row 3 = LL, row 6 = LLG, row 9 = 3ph).
        from gui.services.impedance import _engine
        import numpy as np

        engine = _engine()
        zlt = np.array([[0.01 + 0.02j], [0.03 + 0.06j]])
        iabc = engine.ifault(zlt, 1.0, 0.0, 0.0, 0)
        res = fault_currents(FaultConfig(z_pu=[(0.01 + 0.02j, 0.03 + 0.06j)], vf_pu=1.0))
        assert res.i_slg_pu == pytest.approx(complex(iabc[0, 0]), rel=1e-12)
        assert res.i_ll_pu == pytest.approx(complex(iabc[3, 0]), rel=1e-12)
        assert res.i_llg_pu == pytest.approx(complex(iabc[6, 0]), rel=1e-12)
        assert res.i_3ph_pu == pytest.approx(complex(iabc[9, 0]), rel=1e-12)


class TestVoltageDrop:
    def test_single_phase(self):
        # powercad convention: zt = [r, x]; vs/il/pf per its docstring.
        res = voltage_drop([0.2, 0.3], 120.0, 50.0, 0.95, 1)
        assert res.drop_volts > 0


class TestImmutability:
    def test_dataclasses_reject_unknown(self):
        with pytest.raises(TypeError):
            TransformerConfig(20.0, 8.0, bogus=1)
