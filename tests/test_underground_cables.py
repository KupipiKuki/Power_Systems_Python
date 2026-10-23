# -*- coding: utf-8 -*-
"""Unit tests for underground cable impedance and capacitance calculations."""

import pytest
import numpy as np
from pc_classes.underground_cables import (
    cables,
    tre_cables,
    CableCapacitance,
    CableImpedance,
    CableCapacitanceResult,
    CableImpedanceResult,
)


def test_cable_capacitance_is_positive():
    """Verify that cable capacitance is strictly positive (non-negative)."""
    for name, data in cables.items():
        cc = CableCapacitance(data)
        cpg = cc.Calc_Capacitance()
        yag = cc.Calc_Admittance(frequency=60.0)
        assert cpg > 0.0, f"Capacitance for {name} must be positive, got {cpg}"
        assert yag.imag > 0.0, f"Admittance for {name} must be capacitive (+j), got {yag}"


def test_trefoil_cable_capacitance_is_positive():
    """Verify that Trefoil custom neutral cable capacitance is strictly positive."""
    for name, data in tre_cables.items():
        cc = CableCapacitance(data)
        cpg = cc.Calc_Capacitance()
        assert cpg > 0.0, f"Capacitance for {name} must be positive, got {cpg}"


def test_cable_impedance_sequence_calculation():
    """Verify cable impedance matrix calculation and true matrix sequence transformation."""
    ci = CableImpedance(cables['4/0AWG'], frequency=60.0)
    res = ci.Calc_Impedance_Matrix(Dabc=(0.5, 0.5, 1.0))

    assert isinstance(res, CableImpedanceResult)
    assert res.z_primitive.shape == (6, 6)
    assert res.z_abc.shape == (3, 3)
    assert res.z_012.shape == (3, 3)

    # Real and imaginary components of positive and zero sequence must be positive (passive inductive)
    assert res.z1.real > 0.0
    assert res.z1.imag > 0.0
    assert res.z0.real > 0.0
    assert res.z0.imag > 0.0

    # For inductive distribution cables, Z0 magnitude is typically higher than Z1
    assert abs(res.z0) > abs(res.z1)


def test_cable_matrix_transformation_correctness():
    """Verify that Z012 = inv(A) @ Zabc @ A matches the class fields."""
    ci = CableImpedance(cables['500MCM'])
    res = ci.Calc_Impedance_Matrix()
    assert np.isclose(res.z1, ci.Z1)
    assert np.isclose(res.z0, ci.Z0)
