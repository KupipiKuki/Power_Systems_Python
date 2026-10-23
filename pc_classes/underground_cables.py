# -*- coding: utf-8 -*-
"""Underground cable impedance and capacitance calculations.

Implements modified Carson's equations with Kron reduction for concentric
neutral and tape-shielded underground distribution cables.
"""

from dataclasses import dataclass
from cmath import rect
import numpy as np


# Carson earth equivalent depths (feet) by soil classification:
# 1: wet, 2: swampy, 3: average, 4: dry/rock, 5: rock/concrete, 6: very dry
De_vals = [27.9, 882.0, 2790.0, 8820.0, 882e3, 882e4]

# Standard concentric neutral cable data
# Nohm: single neutral strand resistance in ohms/mile
# R: radius to neutral strands in feet (e.g. 1.334 * 0.5 / 12)
# D_cond, D_strand: conductor and strand diameters in inches
cables = {
    '4/0AWG': {
        'e_r': 2.3,
        'D_cond': 0.504,
        'D_strand': 0.0641,
        'k': 11,
        'R': 1.334 * 0.5 / 12.0,
        'DCohm': 0.084 * 5.28,
        'ACohm': 0.11 * 5.28,
        'Nohm': 13.36,
    },
    '500MCM': {
        'e_r': 2.3,
        'D_cond': 0.772,
        'D_strand': 0.0808,
        'k': 16,
        'R': 1.602 * 0.5 / 12.0,
        'DCohm': 0.035 * 5.28,
        'ACohm': 0.047 * 5.28,
        'Nohm': 21.2256,
    },
    '750MCM': {
        'e_r': 2.3,
        'D_cond': 0.949,
        'D_strand': 0.0641,
        'k': 19,
        'R': 1.823 * 0.5 / 12.0,
        'DCohm': 0.024 * 5.28,
        'ACohm': 0.032 * 5.28,
        'Nohm': 13.36,
    },
    '1000MCM': {
        'e_r': 2.3,
        'D_cond': 1.904,
        'D_strand': 0.0808,
        'k': 16,
        'R': 1.968 * 0.5 / 12.0,
        'DCohm': 0.018 * 5.28,
        'ACohm': 0.024 * 5.28,
        'Nohm': 21.2256,
    },
}

# Southwire custom neutral using spec 81241 (Trefoil configuration)
tre_cables = {
    '4/0AWG': {
        'e_r': 2.3,
        'D_cond': 0.498,
        'D_strand': 0.0808 / 2.0,
        'k': 14,  # 14 strands of 12AWG (1/2 neutral)
        'R': (1.325 + (1.553 - 0.05 - 1.325) / 2.0) * 0.5 / 12.0,
        'DCohm': 0.0836 * 5.28,
        'ACohm': 0.105 * 5.28,
        'Nohm': 1.65 * 5.28,
    },
    '500MCM': {
        'e_r': 2.3,
        'D_cond': 0.789,
        'D_strand': 0.0808 / 2.0,
        'k': 16,  # 16 strands of 12AWG (1/3 neutral)
        'R': (1.625 + (1.945 - 0.08 - 1.625) / 2.0) * 0.5 / 12.0,
        'DCohm': 0.0354 * 5.28,
        'ACohm': 0.045 * 5.28,
        'Nohm': 1.65 * 5.28,
    },
    '750MCM': {
        'e_r': 2.3,
        'D_cond': 0.968,
        'D_strand': 0.0808 / 2.0,
        'k': 12,  # 12 strands of 12AWG (1/6 neutral)
        'R': (1.843 + (2.163 - 0.08 - 1.843) / 2.0) * 0.5 / 12.0,
        'DCohm': 0.0236 * 5.28,
        'ACohm': 0.03 * 5.28,
        'Nohm': 1.65 * 5.28,
    },
    '1000MCM': {
        'e_r': 2.3,
        'D_cond': 1.117,
        'D_strand': 0.0808 / 2.0,
        'k': 16,  # 16 strands of 12AWG (1/6 neutral)
        'R': (1.992 + (2.356 - 0.08 - 1.992) / 2.0) * 0.5 / 12.0,
        'DCohm': 0.0177 * 5.28,
        'ACohm': 0.023 * 5.28,
        'Nohm': 1.65 * 5.28,
    },
    '1250MCM': {
        'e_r': 2.3,
        'D_cond': 1.250,
        'D_strand': 0.0808 / 2.0,
        'k': 16,  # 16 strands of 12AWG (1/9 neutral)
        'R': (1.992 + (2.356 - 0.08 - 1.992) / 2.0) * 0.5 / 12.0,
        'DCohm': 0.0141 * 5.28,
        'ACohm': 0.019 * 5.28,
        'Nohm': 1.65 * 5.28,
    },
}


@dataclass(frozen=True)
class CableCapacitanceResult:
    """Capacitance and shunt admittance results for an underground cable."""
    c_phase_to_ground_f_per_mile: float
    y_admittance_siemens_per_mile: complex


@dataclass(frozen=True)
class CableImpedanceResult:
    """Series impedance results for an underground cable circuit."""
    z_primitive: np.ndarray        # 6x6 primitive matrix (ohms/mile)
    z_abc: np.ndarray              # 3x3 Kron-reduced phase matrix (ohms/mile)
    z_012: np.ndarray              # 3x3 sequence impedance matrix (ohms/mile)
    z1: complex                    # Positive-sequence impedance (ohms/mile)
    z0: complex                    # Zero-sequence impedance (ohms/mile)
    z2: complex                    # Negative-sequence impedance (ohms/mile)


class CableCapacitance:
    """Calculates underground cable phase-to-ground capacitance and admittance.

    Ensures all spatial dimensions are strictly normalized to feet before
    logarithmic evaluation to guarantee positive, physically valid capacitance.
    """

    def __init__(self, data=None):
        if isinstance(data, dict):
            try:
                self.e_r = float(data['e_r'])
                # Conductor radius converted to feet
                self.Rdc = (float(data['D_cond']) / 2.0) / 12.0
                # Strand radius converted to feet
                self.Rds = (float(data['D_strand']) / 2.0) / 12.0
                # Radius to neutral strands in feet
                self.R = float(data['R'])
                self.k = int(data['k'])
            except KeyError as e:
                raise KeyError(f'Cable dictionary missing required key: {e}')
        elif isinstance(data, (list, tuple)):
            if len(data) < 5:
                raise ValueError('Data list must contain at least 5 elements: '
                                 '[D_cond, D_strand, R, k, e_r]')
            self.Rdc = (float(data[0]) / 2.0) / 12.0
            self.Rds = (float(data[1]) / 2.0) / 12.0
            self.R = float(data[2])
            self.k = int(data[3])
            self.e_r = float(data[4])
        else:
            raise TypeError('Data must be a dictionary or list/tuple')

        self.Cpg = 0.0
        self.Yag = 0.0j

        # Permittivity of free space converted from F/m to F/mile:
        # epsilon_0 = 8.854187817e-12 F/m * 1609.344 m/mile
        self.e_o = 8.854187817e-12 * 1609.344

    def Calc_Capacitance(self) -> float:
        """Calculate phase-to-ground capacitance (F/mile)."""
        # Ensure dimensions in logarithmic arguments are in matching units (feet)
        term1 = np.log(self.R / self.Rdc)
        term2 = (1.0 / self.k) * np.log((self.k * self.Rds) / self.R)
        denom = term1 - term2
        if denom <= 0:
            raise ValueError(
                f'Invalid cable geometry: logarithmic denominator {denom} <= 0')
        self.Cpg = (2.0 * np.pi * self.e_o * self.e_r) / denom
        return self.Cpg

    def Calc_Admittance(self, frequency: float = 60.0) -> complex:
        """Calculate shunt admittance Yag (Siemens/mile)."""
        if self.Cpg == 0.0:
            self.Calc_Capacitance()
        self.Yag = 2.0 * np.pi * frequency * self.Cpg * 1j
        return self.Yag


class CableImpedance:
    """Calculates series impedance matrix for underground concentric neutral cables.

    Applies modified Carson's equations, Kron reduction from 6x6 (phase + neutral)
    to 3x3 phase conductors, and true matrix multiplication symmetrical components.
    """

    def __init__(self, data=None, frequency: float = 60.0, De: float = 2790.0):
        self.f = float(frequency)
        # Reactance coefficient scaling with frequency
        self.w = 2.0224e-3 * (self.f / 60.0)
        # Earth return resistance (ohms/mile)
        self.resd = 1.588e-3 * self.f
        self.De = float(De)

        if isinstance(data, dict):
            try:
                self.k = int(data['k'])
                self.R = float(data['R'])  # feet
                # Convert conductor and strand diameters from inches to feet for GMR
                d_cond_ft = float(data['D_cond']) / 12.0
                d_strand_ft = float(data['D_strand']) / 12.0
                self.GMRc = 0.7788 * (d_cond_ft / 2.0)  # feet
                self.GMRcn = (d_strand_ft * self.k * (self.R ** (self.k - 1))) ** (1.0 / self.k)  # feet
                self.Cres = float(data['ACohm'])  # ohms/mile
                self.CNres = float(data['Nohm']) / self.k  # ohms/mile
            except KeyError as e:
                raise KeyError(f'Cable dictionary missing required key: {e}')
        elif isinstance(data, (list, tuple)):
            if len(data) < 6:
                raise ValueError('Data list must contain at least 6 elements: '
                                 '[ACohm, Nohm, D_cond, D_strand, R, k]')
            self.Cres = float(data[0])
            self.k = int(data[5])
            self.CNres = float(data[1]) / self.k
            self.R = float(data[4])
            d_cond_ft = float(data[2]) / 12.0
            d_strand_ft = float(data[3]) / 12.0
            self.GMRc = 0.7788 * (d_cond_ft / 2.0)
            self.GMRcn = (d_strand_ft * self.k * (self.R ** (self.k - 1))) ** (1.0 / self.k)
        else:
            raise TypeError('Data must be a dictionary or list/tuple')

        self.Zp = 0.0j
        self.Zn = 0.0j
        self.Zmat = None
        self.Zabc = None
        self.Zseq = None
        self.Z1 = None
        self.Z0 = None
        self.Z2 = None

    def Calc_Impedance(self):
        """Calculate self-impedances for phase and concentric neutral conductors."""
        self.Zp = self.Cres + self.resd + 1j * self.w * self.f * np.log(self.De / self.GMRc)
        self.Zn = self.CNres + self.resd + 1j * self.w * self.f * np.log(self.De / self.GMRcn)
        return self.Zp, self.Zn

    def Calc_Impedance_Matrix(self, Dabc=(0.5, 0.5, 1.0)):
        """Compute the 6x6 primitive matrix, perform Kron reduction to 3x3 Zabc,
        and perform true matrix symmetrical component transformation to Z012.

        Parameters
        ----------
        Dabc : tuple or list of 3 floats
            Phase spacing [D_ab, D_bc, D_ca] in feet. Default (0.5, 0.5, 1.0).
        """
        if self.Zp == 0.0j:
            self.Calc_Impedance()

        # Spatial positions: Phase A, B, C and their concentric neutrals
        # Phase A at 0, Phase B at D_ab, Phase C at D_ca
        dmat = np.array([
            0.0,
            Dabc[0],
            Dabc[2],
            self.R * 1j,
            Dabc[0] + (self.R * 1j),
            Dabc[2] + (self.R * 1j),
        ])

        Zmat = np.empty((6, 6), dtype=np.complex128)

        for i in range(6):
            for j in range(6):
                if i != j:
                    dist = abs(dmat[i] - dmat[j])
                    Zmat[i, j] = self.resd + 1j * self.w * self.f * np.log(self.De / dist)
            if i < 3:
                Zmat[i, i] = self.Zp
            else:
                Zmat[i, i] = self.Zn

        # Kron reduction eliminating neutral conductors (indices 3:6)
        # Zabc = Z_pp - Z_pn @ inv(Z_nn) @ Z_np
        Zpp = Zmat[0:3, 0:3]
        Zpn = Zmat[0:3, 3:6]
        Znn = Zmat[3:6, 3:6]
        zabc = Zpp - Zpn @ np.linalg.inv(Znn) @ Zpn.T

        # Symmetrical components transformation matrix A
        a = rect(1.0, (2.0 * np.pi) / 3.0)
        A = np.array([
            [1.0, 1.0, 1.0],
            [1.0, a ** 2, a],
            [1.0, a, a ** 2],
        ])
        A_inv = np.linalg.inv(A)

        # True matrix multiplication for sequence transformation
        zseq = A_inv @ zabc @ A

        # Sequence impedances (diagonal elements)
        self.Z0 = complex(zseq[0, 0])
        self.Z1 = complex(zseq[1, 1])
        self.Z2 = complex(zseq[2, 2])
        self.Zmat = Zmat
        self.Zabc = zabc
        self.Zseq = zseq

        return CableImpedanceResult(
            z_primitive=Zmat,
            z_abc=zabc,
            z_012=zseq,
            z1=self.Z1,
            z0=self.Z0,
            z2=self.Z2,
        )
