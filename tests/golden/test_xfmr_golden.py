"""
Golden regression tests for transformer impedance calculations.

Phase 0: Test-Case Corpus + Golden Regression Baseline
These tests capture the current behavior of the xfmr() method without modifying it.
All expected values are hand-calculated from first principles.

Transformer per-unit impedance formula:
    Z_pu = (Z% / 100) * (Sb / Sbase) * (Vbase / Vrated)^2
    
For a transformer with MVA rating and %Z:
    Z1_pu = Z% / 100  (positive sequence)
    Z0_pu = Z1_pu * zeromult  (zero sequence, with multiplier)
    
    If X/R ratio is given:
        R1 = Z1 / sqrt(1 + (X/R)^2)
        X1 = R1 * (X/R)
        R0 = R1 * zeromult
        X0 = X1 * zeromult
    
    If X/R is not given, it's calculated from the xrcalc() method.
"""

import numpy as np
import pytest
import sys
import os

# Add the repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pc_classes import powercad as pc


class TestTransformerXFMR:
    """Golden tests for xfmr() method."""
    
    def setup_method(self):
        """Initialize faultCalculationClass before each test."""
        self.fcc = pc.faultCalculationClass()
    
    def test_xfmr_20mva_8percent_no_xr(self):
        """
        Test: 20 MVA, 8% Z, X/R from deterministic curve, zeromult=1.0
        
        Expected calculation:
        - Z1_pu = 8/100 = 0.08
        - X/R from xrcurve: at 20 MVA, XR = 21.8 (deterministic curve interpolation)
        - R1 = Z1 / sqrt(1 + XR^2) = 0.08 / sqrt(1 + 21.8^2) = 0.003666
        - X1 = R1 * XR = 0.003666 * 21.8 = 0.07992
        - With zeromult=1.0: Z0 = Z1
        
        Expected: [[0.003666 + j0.07992], [0.003666 + j0.07992]]
        Tolerance: rel=1e-3 for per-unit quantities
        """
        # Use deterministic curve X/R instead of stochastic 'rand' mode
        xr = self.fcc.xrcalc(20, 'curve')
        result = self.fcc.xfmr(20, 8, xr, False, 1.0)
        
        # Expected values calculated from first principles
        Z1_pu = 0.08
        R1 = Z1_pu / np.sqrt(1 + xr**2)
        X1 = R1 * xr
        Z1_expected = R1 + 1j * X1
        Z0_expected = Z1_expected  # zeromult=1.0
        
        expected = np.array([[Z1_expected], [Z0_expected]])
        
        # Check with tolerance
        np.testing.assert_allclose(result, expected, rtol=1e-3, atol=1e-6)
    
    def test_xfmr_10mva_5_75percent_xr_10(self):
        """
        Test: 10 MVA, 5.75% Z, X/R=10, zeromult=0.9
        
        Expected calculation:
        - Z1_pu = 5.75/100 = 0.0575
        - R1 = 0.0575 / sqrt(1 + 10^2) = 0.0575 / 10.0499 = 0.005721
        - X1 = 0.005721 * 10 = 0.05721
        - Z1 = 0.005721 + j*0.05721
        - Z0 = Z1 * 0.9 = 0.005149 + j*0.05149
        
        Expected: [[0.005721 + j0.05721], [0.005149 + j0.05149]]
        Tolerance: rel=1e-3 for per-unit quantities
        """
        result = self.fcc.xfmr(10, 5.75, 10.0, False, 0.9)
        
        # Hand-calculated expected values
        Z1_pu = 0.0575
        R1 = Z1_pu / np.sqrt(1 + 10.0**2)
        X1 = R1 * 10.0
        Z1_expected = R1 + 1j * X1
        Z0_expected = Z1_expected * 0.9
        
        expected = np.array([[Z1_expected], [Z0_expected]])
        
        np.testing.assert_allclose(result, expected, rtol=1e-3, atol=1e-6)
    
    def test_xfmr_100mva_10_5percent_xr_15(self):
        """
        Test: 100 MVA, 10.5% Z, X/R=15, zeromult=1.0
        
        Expected calculation:
        - Z1_pu = 10.5/100 = 0.105
        - R1 = 0.105 / sqrt(1 + 15^2) = 0.105 / 15.0333 = 0.006985
        - X1 = 0.006985 * 15 = 0.10478
        - Z1 = 0.006985 + j*0.10478
        - Z0 = Z1 * 1.0 = Z1
        
        Expected: [[0.006985 + j0.10478], [0.006985 + j0.10478]]
        Tolerance: rel=1e-3 for per-unit quantities
        """
        result = self.fcc.xfmr(100, 10.5, 15.0, False, 1.0)
        
        # Hand-calculated expected values
        Z1_pu = 0.105
        R1 = Z1_pu / np.sqrt(1 + 15.0**2)
        X1 = R1 * 15.0
        Z1_expected = R1 + 1j * X1
        Z0_expected = Z1_expected * 1.0
        
        expected = np.array([[Z1_expected], [Z0_expected]])
        
        np.testing.assert_allclose(result, expected, rtol=1e-3, atol=1e-6)
    
    def test_xfmr_25mva_8percent_xr_5_zeromult_0_9(self):
        """
        Test: 25 MVA, 8% Z, X/R=5, zeromult=0.9
        
        Expected calculation:
        - Z1_pu = 8/100 = 0.08
        - R1 = 0.08 / sqrt(1 + 5^2) = 0.08 / 5.099 = 0.01569
        - X1 = 0.01569 * 5 = 0.07845
        - Z1 = 0.01569 + j*0.07845
        - Z0 = Z1 * 0.9 = 0.01412 + j*0.07061
        
        Expected: [[0.01569 + j0.07845], [0.01412 + j0.07061]]
        Tolerance: rel=1e-3 for per-unit quantities
        """
        result = self.fcc.xfmr(25, 8, 5.0, False, 0.9)
        
        # Hand-calculated expected values
        Z1_pu = 0.08
        R1 = Z1_pu / np.sqrt(1 + 5.0**2)
        X1 = R1 * 5.0
        Z1_expected = R1 + 1j * X1
        Z0_expected = Z1_expected * 0.9
        
        expected = np.array([[Z1_expected], [Z0_expected]])
        
        np.testing.assert_allclose(result, expected, rtol=1e-3, atol=1e-6)
    
    def test_xfmr_10mva_8percent_no_xr_zeromult_1_0(self):
        """
        Test: 10 MVA, 8% Z, X/R from deterministic curve, zeromult=1.0
        
        Expected calculation:
        - Z1_pu = 8/100 = 0.08
        - X/R from xrcurve: at 10 MVA, XR = 15.8 (deterministic curve interpolation)
        - R1 = 0.08 / sqrt(1 + 15.8^2) = 0.005053
        - X1 = 0.005053 * 15.8 = 0.07984
        - Z0 = Z1 * 1.0 = Z1
        
        Expected: [[0.005053 + j0.07984], [0.005053 + j0.07984]]
        Tolerance: rel=1e-3 for per-unit quantities
        """
        # Use deterministic curve X/R instead of stochastic 'rand' mode
        xr = self.fcc.xrcalc(10, 'curve')
        result = self.fcc.xfmr(10, 8, xr, False, 1.0)
        
        # Expected values calculated from first principles
        Z1_pu = 0.08
        R1 = Z1_pu / np.sqrt(1 + xr**2)
        X1 = R1 * xr
        Z1_expected = R1 + 1j * X1
        Z0_expected = Z1_expected  # zeromult=1.0
        
        expected = np.array([[Z1_expected], [Z0_expected]])
        
        np.testing.assert_allclose(result, expected, rtol=1e-3, atol=1e-6)
    
    def test_xfmr_20mva_5_75percent_xr_8_zeromult_0_9(self):
        """
        Test: 20 MVA, 5.75% Z, X/R=8, zeromult=0.9
        
        Expected calculation:
        - Z1_pu = 5.75/100 = 0.0575
        - R1 = 0.0575 / sqrt(1 + 8^2) = 0.0575 / 8.0623 = 0.007132
        - X1 = 0.007132 * 8 = 0.05706
        - Z1 = 0.007132 + j*0.05706
        - Z0 = Z1 * 0.9 = 0.006419 + j*0.05135
        
        Expected: [[0.007132 + j0.05706], [0.006419 + j0.05135]]
        Tolerance: rel=1e-3 for per-unit quantities
        """
        result = self.fcc.xfmr(20, 5.75, 8.0, False, 0.9)
        
        # Hand-calculated expected values
        Z1_pu = 0.0575
        R1 = Z1_pu / np.sqrt(1 + 8.0**2)
        X1 = R1 * 8.0
        Z1_expected = R1 + 1j * X1
        Z0_expected = Z1_expected * 0.9
        
        expected = np.array([[Z1_expected], [Z0_expected]])
        
        np.testing.assert_allclose(result, expected, rtol=1e-3, atol=1e-6)
