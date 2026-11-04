"""Phase 1 tests: transformer zero-sequence models and network assembly.

Expected values hand-derived from docs/qa/phase1_test_cases.md Sections 2
and 4, with the transformer base-conversion corrected per the Gemini
Phase 0 audit (25 MVA -> 100 MVA base multiplies per-unit impedance by
100/25 = 4, not 0.25; corpus section 4.4 retains the pre-correction
values, so the network fault currents here differ from the corpus table
by design and are re-derived from first principles below).

Run from the repository root:
    python -m pytest gui/tests/test_phase1.py -v
"""

import cmath
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gui.services import (
    FaultConfig,
    LineSegment,
    NetworkConfig,
    SourceConfig,
    TransformerConfig,
    assemble_network,
    fault_currents,
    transformer_zero_sequence,
)

# Corpus Section 2 transformer: 25 MVA, 115/12.47 kV, 8% Z, X/R=10, zeromult=0.9
XF = dict(mva_base=25.0, percent_z=8.0, xr_ratio=10.0, zero_mult=0.9)
Z1 = 0.08 / math.sqrt(101.0) * (1 + 10j)  # 0.007960 + j0.07960 pu
Z0 = 0.9 * Z1                              # 0.007164 + j0.07164 pu


class TestTransformerZeroSequence:
    """Corpus cases 2.1-2.4."""

    def test_case_2_1_grdy_grdy(self):
        # Both neutrals grounded: Z0 = zeromult*Z1 from either side.
        res = transformer_zero_sequence(TransformerConfig(**XF))
        assert res.z0_primary_pu == pytest.approx(Z0, rel=1e-9)
        assert res.z0_secondary_pu == pytest.approx(Z0, rel=1e-9)
        assert res.zero_sequence_path_exists

    def test_case_2_2_grdy_delta(self):
        # Delta secondary blocks external zero-sequence on the secondary
        # side; grounded-wye primary still shows Z0 = zeromult*Z1.
        res = transformer_zero_sequence(
            TransformerConfig(**XF, secondary_connection="delta")
        )
        assert res.z0_primary_pu == pytest.approx(Z0, rel=1e-9)
        assert res.z0_secondary_pu is None
        assert not res.zero_sequence_path_exists

    def test_case_2_3_delta_grdy(self):
        # Delta primary blocks; grounded-wye secondary shows Z0.
        res = transformer_zero_sequence(
            TransformerConfig(**XF, primary_connection="delta")
        )
        assert res.z0_primary_pu is None
        assert res.z0_secondary_pu == pytest.approx(Z0, rel=1e-9)
        assert res.zero_sequence_path_exists

    def test_case_2_4_delta_delta(self):
        # No external zero-sequence path from either side.
        res = transformer_zero_sequence(
            TransformerConfig(**XF, primary_connection="delta", secondary_connection="delta")
        )
        assert res.z0_primary_pu is None
        assert res.z0_secondary_pu is None
        assert not res.zero_sequence_path_exists

    def test_ungrounded_wye_blocks(self):
        # Floating neutral behaves like delta for external zero-seq.
        res = transformer_zero_sequence(
            TransformerConfig(**XF, primary_connection="y")
        )
        assert res.z0_primary_pu is None
        assert res.z0_secondary_pu == pytest.approx(Z0, rel=1e-9)


class TestNetworkAssembly:
    """Corpus Section 4 (audit-corrected base conversion).

    System: 500 MVA / X/R=15 source at 115 kV -> 25 MVA, 8% Z, X/R=10,
    zeromult=0.9, GrdY-GrdY transformer -> 2,000 ft OH line at 12.47 kV
    (Z1 = 0.1018 + j1.228 ohm, Z0 = 0.1018 + j6.496 ohm per corpus 4.3)
    -> fault at line end. Study base 100 MVA, vf = 1.05 pu.

    Per-unit on 100 MVA:
    - Source: |Z1| = 100/500 = 0.20 pu; Z0 = Z1 (corpus assumption).
    - Transformer (CORRECTED): Z1 = 0.08 * 100/25 = 0.32 pu magnitude;
      Z0 = 0.9 * that. With X/R=10: Z1 = 0.32/sqrt(101)*(1+10j),
      Z0 = 0.9*Z1.
    - Line: Zbase = 12.47^2/100 = 1.5550 ohm;
      Z1 = (0.1018 + j1.228)/1.5550 = 0.06547 + j0.7897 pu,
      Z0 = (0.1018 + j6.496)/1.5550 = 0.06547 + j4.1770 pu.
    """

    SRC = SourceConfig(base_mva=100.0, base_kv=115.0, fault_mva_3ph=500.0, xr_ratio=15.0, zero_mult=1.0)
    XFMR = TransformerConfig(mva_base=25.0, percent_z=8.0, xr_ratio=10.0, zero_mult=0.9)
    SEG = LineSegment(z1_ohms=0.1018 + 1.228j, z0_ohms=0.1018 + 6.496j, kv=12.47)

    def _expected_totals(self):
        z1_src = 0.20 / math.sqrt(1 + 15.0 ** 2) * (1 + 15j)
        z1_xf = 0.32 / math.sqrt(101.0) * (1 + 10j)
        z1_line = (0.1018 + 1.228j) / (12.47 ** 2 / 100.0)
        z0_src = z1_src
        z0_xf = 0.9 * z1_xf
        z0_line = (0.1018 + 6.496j) / (12.47 ** 2 / 100.0)
        return z1_src + z1_xf + z1_line, z0_src + z0_xf + z0_line

    def test_corpus_case_4_totals(self):
        cfg = NetworkConfig(
            base_mva=100.0, source=self.SRC, transformer=self.XFMR,
            primary_kv=115.0, secondary_kv=12.47, segments=[self.SEG],
            vf_pu=1.05,
        )
        res = assemble_network(cfg)
        z1_exp, z0_exp = self._expected_totals()
        assert res.z1_total_pu == pytest.approx(z1_exp, rel=1e-9)
        assert res.z0_total_pu == pytest.approx(z0_exp, rel=1e-9)

    def test_corpus_case_4_fault_currents(self):
        # |Z1_total| = 0.58550 + j0.78970 -> I3ph = 1.05/|Z1_total| pu;
        # SLG = 3*1.05/|2*Z1+Z0|; LL = sqrt(3)*1.05/|2*Z1|.
        cfg = NetworkConfig(
            base_mva=100.0, source=self.SRC, transformer=self.XFMR,
            primary_kv=115.0, secondary_kv=12.47, segments=[self.SEG],
            vf_pu=1.05,
        )
        res = assemble_network(cfg)
        z1, z0 = res.z1_total_pu, res.z0_total_pu
        i_base = 100e6 / (12.47e3 * math.sqrt(3))  # 4627.5 A
        assert res.i_3ph_pu == pytest.approx(1.05 / z1, rel=1e-9)
        assert abs(res.i_3ph_amps) == pytest.approx(abs(1.05 / z1) * i_base, rel=1e-6)
        assert res.fault.i_slg_pu == pytest.approx(3 * 1.05 / (2 * z1 + z0), rel=1e-9)
        assert abs(res.fault.i_ll_pu) == pytest.approx(
            abs(1.05 * math.sqrt(3) / (2 * z1)), rel=1e-3
        )
        # 3ph must exceed SLG here (large Z0 from the line)
        assert abs(res.fault.i_3ph_pu) > abs(res.fault.i_slg_pu)

    def test_delta_secondary_blocks_slg(self):
        # GrdY-Delta: SLG fault on the delta side has no zero-seq path.
        cfg = NetworkConfig(
            base_mva=100.0, source=self.SRC,
            transformer=TransformerConfig(
                mva_base=25.0, percent_z=8.0, xr_ratio=10.0, zero_mult=0.9,
                secondary_connection="delta",
            ),
            primary_kv=115.0, secondary_kv=12.47, segments=[self.SEG],
            vf_pu=1.05,
        )
        res = assemble_network(cfg)
        assert res.z0_total_pu is None
        assert res.fault is None
        assert res.i_slg_pu is None
        # z1 total still well defined
        z1_exp, _ = self._expected_totals()
        assert res.z1_total_pu == pytest.approx(z1_exp, rel=1e-9)

    def test_delta_primary_excludes_source_z0(self):
        # Delta-GrdY: transformer Z0 and line Z0 are in the path, but the
        # upstream source Z0 is NOT (delta blocks it); only xfmr + line.
        cfg = NetworkConfig(
            base_mva=100.0, source=self.SRC,
            transformer=TransformerConfig(
                mva_base=25.0, percent_z=8.0, xr_ratio=10.0, zero_mult=0.9,
                primary_connection="delta",
            ),
            primary_kv=115.0, secondary_kv=12.47, segments=[self.SEG],
            vf_pu=1.05,
        )
        res = assemble_network(cfg)
        zbase = 12.47 ** 2 / 100.0
        z0_xf = 0.9 * (0.32 / math.sqrt(101.0) * (1 + 10j))
        z0_line = (0.1018 + 6.496j) / zbase
        assert res.z0_total_pu == pytest.approx(z0_xf + z0_line, rel=1e-9)

    def test_no_segments_fault_at_secondary_bus(self):
        # Zero segments: fault at the transformer secondary bus.
        cfg = NetworkConfig(
            base_mva=100.0, source=self.SRC, transformer=self.XFMR,
            primary_kv=115.0, secondary_kv=12.47, vf_pu=1.0,
        )
        res = assemble_network(cfg)
        assert res.fault_kv == 12.47
        z1_src = 0.20 / math.sqrt(1 + 15.0 ** 2) * (1 + 15j)
        z1_xf = 0.32 / math.sqrt(101.0) * (1 + 10j)
        assert res.z1_total_pu == pytest.approx(z1_src + z1_xf, rel=1e-9)

    def test_source_kv_mismatch_rejected(self):
        with pytest.raises(ValueError):
            NetworkConfig(
                base_mva=100.0,
                source=SourceConfig(base_mva=100.0, base_kv=69.0, fault_mva_3ph=500.0, xr_ratio=15.0, zero_mult=1.0),
                transformer=self.XFMR, primary_kv=115.0, secondary_kv=12.47,
            )
