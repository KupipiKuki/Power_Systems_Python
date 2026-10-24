# -*- coding: utf-8 -*-
"""Unit tests for overhead line impedance and capacitance calculations."""

import pytest
import numpy as np
from pc_classes.overhead_lines import (
    OverheadConductor,
    ConductorPosition,
    OverheadLineGeometry,
    OverheadLineImpedance,
    OverheadLineCapacitance,
    LineImpedanceResult,
    LineAdmittanceResult,
)


@pytest.fixture
def standard_3ph_geometry():
    """Standard horizontal distribution line geometry with neutral."""
    c_phase = OverheadConductor(
        name='Raven',
        gmr_ft=0.0059,
        diameter_in=0.398,
        r_ac_per_mile=0.35,
    )
    c_neutral = OverheadConductor(
        name='Raven',
        gmr_ft=0.0059,
        diameter_in=0.398,
        r_ac_per_mile=0.35,
    )
    geom = OverheadLineGeometry(
        phases={
            'A': ConductorPosition(-2.5, 30.0),
            'B': ConductorPosition(0.0, 31.0),
            'C': ConductorPosition(2.5, 30.0),
        },
        neutrals={
            'N': ConductorPosition(0.0, 25.0),
        },
    )
    conductors = {'A': c_phase, 'B': c_phase, 'C': c_phase, 'N': c_neutral}
    return conductors, geom


def test_overhead_line_impedance_calculation(standard_3ph_geometry):
    """Verify Carson's equations, Kron reduction, and sequence impedance extraction."""
    conductors, geom = standard_3ph_geometry
    calc = OverheadLineImpedance(conductors, geom, frequency=60.0, earth_resistivity_or_De=2790.0)
    res = calc.calc_impedance(transposed=False)

    assert isinstance(res, LineImpedanceResult)
    assert res.z_primitive.shape == (4, 4)
    assert res.z_abc.shape == (3, 3)
    assert res.z_012.shape == (3, 3)

    # Resistances and inductive reactances must be positive
    assert res.z1.real > 0.0
    assert res.z1.imag > 0.0
    assert res.z0.real > 0.0
    assert res.z0.imag > 0.0

    # Zero sequence impedance must be greater than positive sequence (Z0 > Z1)
    assert abs(res.z0) > abs(res.z1)


def test_overhead_line_capacitance_calculation(standard_3ph_geometry):
    """Verify Maxwell potential matrix inversion and shunt charging susceptance."""
    conductors, geom = standard_3ph_geometry
    calc = OverheadLineCapacitance(conductors, geom, frequency=60.0)
    res = calc.calc_admittance()

    assert isinstance(res, LineAdmittanceResult)
    assert res.p_matrix.shape == (4, 4)
    assert res.c_abc.shape == (3, 3)
    assert res.y_abc.shape == (3, 3)

    # Shunt charging susceptances B1 and B0 must be positive (capacitive)
    assert res.b1 > 0.0
    assert res.b0 > 0.0
    assert res.b1 > res.b0


def test_single_phase_overhead_line():
    """Verify single phase overhead line calculation."""
    c = OverheadConductor('Sparrow', 0.0039, 0.316, 0.45)
    geom = OverheadLineGeometry(
        phases={'A': ConductorPosition(0.0, 30.0)},
        neutrals={'N': ConductorPosition(0.0, 25.0)},
    )
    calc = OverheadLineImpedance({'A': c, 'N': c}, geom)
    res = calc.calc_impedance()

    assert res.z_abc.shape == (1, 1)
    assert res.z1 == res.z0
    assert res.z1.real > 0.0
    assert res.z1.imag > 0.0
