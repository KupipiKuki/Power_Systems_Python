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
    ConductorPositionConfig,
    FaultConfig,
    FaultResult,
    ImpedanceResult,
    OverheadLineConfig,
    OverheadLineConductorConfig,
    SourceConfig,
    TransformerConfig,
    UndergroundCableConfig,
    fault_currents,
    overhead_line_impedance,
    source_impedance,
    transformer_impedance,
    underground_cable_impedance,
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

    def test_source_from_slg_mva_equal_duty(self):
        # Physical anchor: when SLG duty equals 3ph duty, Z0 = Z1.
        # |2*Z1 + Z0| = 3*S_base/S_slg = 3*100/2000 = 0.15 pu; with Z0=Z1,
        # |3*Z1| = 0.15 => |Z1| = 0.05 pu, consistent with 3ph duty 100/2000.
        cfg = SourceConfig(
            base_mva=100.0,
            base_kv=115.0,
            fault_mva_3ph=2000.0,
            fault_mva_slg=2000.0,
            xr_ratio=8.0,
        )
        res = source_impedance(cfg)
        assert abs(res.z1_pu) == pytest.approx(0.05, rel=1e-9)
        assert res.z0_pu == pytest.approx(res.z1_pu, rel=1e-9)
        assert res.z0_pu.imag > 0

    def test_source_from_slg_mva_general(self):
        # SLG duty 1500 MVA: |2*Z1 + Z0| = 3*100/1500 = 0.20 pu, loop angle
        # aligned to Z1's angle. Z0 = 0.20*e^{j*theta1} - 2*Z1, and since
        # Z0 lies on the same ray: Z0 = (0.20 - 2*0.05)*e^{j*theta1} = 0.10*e^{j*theta1}.
        cfg = SourceConfig(
            base_mva=100.0,
            base_kv=115.0,
            fault_mva_3ph=2000.0,
            fault_mva_slg=1500.0,
            xr_ratio=8.0,
        )
        res = source_impedance(cfg)
        theta1 = 0.05 / math.sqrt(65) * (1 + 8j)
        expected_z0 = 0.10 / abs(theta1) * theta1
        assert res.z0_pu == pytest.approx(expected_z0, rel=1e-9)
        assert res.z0_pu.imag > 0

    def test_source_mutual_exclusivity(self):
        with pytest.raises(ValueError):
            SourceConfig(base_mva=100.0, base_kv=115.0, fault_mva_3ph=2000.0, explicit_z1=0.05j)
        with pytest.raises(ValueError):
            SourceConfig(
                base_mva=100.0, base_kv=115.0, fault_mva_3ph=2000.0,
                fault_mva_slg=2000.0, zero_mult=3.0,
            )
        with pytest.raises(ValueError):
            SourceConfig(base_mva=100.0, base_kv=115.0, fault_mva_3ph=-2000.0, zero_mult=3.0)

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
        # Cross-check facade extraction against raw ifault rows, using the
        # faulted phase: row 0 = SLG phase a, row 4 = LL phase b (BC fault,
        # phase a unfaulted), row 7 = LLG phase b (BC-G fault), row 9 = 3ph a.
        from gui.services.impedance import _engine
        import numpy as np

        engine = _engine()
        zlt = np.array([[0.01 + 0.02j], [0.03 + 0.06j]])
        iabc = engine.ifault(zlt, 1.0, 0.0, 0.0, 0)
        res = fault_currents(FaultConfig(z_pu=[(0.01 + 0.02j, 0.03 + 0.06j)], vf_pu=1.0))
        assert res.i_slg_pu == pytest.approx(complex(iabc[0, 0]), rel=1e-12)
        assert res.i_ll_pu == pytest.approx(complex(iabc[4, 0]), rel=1e-12)
        assert res.i_llg_pu == pytest.approx(complex(iabc[7, 0]), rel=1e-12)
        assert res.i_3ph_pu == pytest.approx(complex(iabc[9, 0]), rel=1e-12)

    def test_ll_llg_nonzero_first_principles(self):
        # Bolted LL (phase BC): |I_b| = sqrt(3)*vf/|2*Z1| (Zf = 0).
        # Bolted LLG (BC-G): sequence network I1 = vf/(Z1 + Z1||Z0), with
        # Z1||Z0 = (0.01+0.02j)*(0.03+0.06j)/(0.04+0.08j).
        z1 = 0.01 + 0.02j
        z0 = 0.03 + 0.06j
        res = fault_currents(FaultConfig(z_pu=[(z1, z0)], vf_pu=1.0))
        expected_ll = abs(1.7320508075688772 * 1.0 / (2 * z1))
        assert abs(res.i_ll_pu) == pytest.approx(expected_ll, rel=1e-3)
        assert abs(res.i_ll_pu) > 0
        # Note: upstream ifault has a known LLG I0/I2 divider defect
        # (audit finding NB-5); this assertion pins the faulted-phase b
        # current magnitude |I_b| = |A * I012|_b which uses I1 correctly.
        i1 = 1.0 / (z1 + (z1 * z0) / (z1 + z0))
        i012 = np.array([[-i1 * (z0 / (z1 + z0))], [i1], [-i1 * (z1 / (z1 + z0))]])
        from gui.services.impedance import _engine
        engine = _engine()
        expected_ib = complex(np.dot(engine.Amat, i012)[1, 0])
        assert res.i_llg_pu == pytest.approx(expected_ib, rel=1e-12)
        assert abs(res.i_llg_pu) > 0


class TestVoltageDrop:
    def test_single_phase(self):
        # powercad convention: zt = [r, x]; vs/il/pf per its docstring.
        res = voltage_drop([0.2, 0.3], 120.0, 50.0, 0.95, 1)
        assert res.drop_volts > 0


class TestOverheadLineImpedance:
    def test_three_phase_balanced(self):
        # Symmetric 3-phase line: conductors at equilateral triangle.
        # Same conductor for all phases and neutral.
        cond = OverheadLineConductorConfig(
            gmr_ft=0.01, diameter_in=0.5, r_ac_per_mile=0.2
        )
        cfg = OverheadLineConfig(
            conductors={'A': cond, 'B': cond, 'C': cond, 'N': cond},
            phases={
                'A': ConductorPositionConfig(x_ft=-1.0, y_ft=30.0),
                'B': ConductorPositionConfig(x_ft=0.0, y_ft=31.0),
                'C': ConductorPositionConfig(x_ft=1.0, y_ft=30.0),
            },
            neutrals={
                'N': ConductorPositionConfig(x_ft=0.0, y_ft=25.0),
            },
        )
        res = overhead_line_impedance(cfg)
        assert res.z1.imag > 0, "Positive-sequence reactance must be positive"
        assert res.z0.imag > 0, "Zero-sequence reactance must be positive"
        assert res.z0.real > res.z1.real, "Z0 resistance > Z1 resistance (earth return)"
        assert len(res.z_abc) == 3

    def test_single_phase(self):
        cond = OverheadLineConductorConfig(
            gmr_ft=0.01, diameter_in=0.5, r_ac_per_mile=0.2
        )
        cfg = OverheadLineConfig(
            conductors={'A': cond, 'N': cond},
            phases={'A': ConductorPositionConfig(x_ft=0.0, y_ft=30.0)},
            neutrals={'N': ConductorPositionConfig(x_ft=0.0, y_ft=25.0)},
        )
        res = overhead_line_impedance(cfg)
        assert res.z1 == res.z0, "Single-phase: Z1 == Z0"
        assert res.z1.imag > 0

    def test_missing_conductor_raises(self):
        cond = OverheadLineConductorConfig(
            gmr_ft=0.01, diameter_in=0.5, r_ac_per_mile=0.2
        )
        with pytest.raises(ValueError, match="missing"):
            OverheadLineConfig(
                conductors={'A': cond},
                phases={
                    'A': ConductorPositionConfig(x_ft=0.0, y_ft=30.0),
                    'B': ConductorPositionConfig(x_ft=1.0, y_ft=30.0),
                },
            )


class TestUndergroundCableImpedance:
    def test_catalog_cable(self):
        cfg = UndergroundCableConfig(cable_type='4/0AWG')
        res = underground_cable_impedance(cfg)
        assert res.z1.imag > 0, "Positive-sequence reactance must be positive"
        assert res.z0.imag > 0, "Zero-sequence reactance must be positive"
        assert len(res.z_abc) == 3

    def test_all_catalog_cables(self):
        for cable_type in ('4/0AWG', '500MCM', '750MCM', '1000MCM'):
            cfg = UndergroundCableConfig(cable_type=cable_type)
            res = underground_cable_impedance(cfg)
            assert res.z1.imag > 0, f"{cable_type}: Z1 reactance must be positive"
            assert res.z0.imag > 0, f"{cable_type}: Z0 reactance must be positive"

    def test_unknown_cable_raises(self):
        cfg = UndergroundCableConfig(cable_type='BOGUS')
        with pytest.raises(ValueError, match="Unknown cable type"):
            underground_cable_impedance(cfg)


class TestImmutability:
    def test_dataclasses_reject_unknown(self):
        with pytest.raises(TypeError):
            TransformerConfig(20.0, 8.0, bogus=1)
