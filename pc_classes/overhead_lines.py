# -*- coding: utf-8 -*-
"""Overhead line impedance and capacitance calculations.

Implements modified Carson's equations with generalized Kron reduction
for overhead distribution and transmission lines, plus Maxwell potential
coefficient method for shunt capacitance and charging admittance.
"""

from dataclasses import dataclass, field
from cmath import rect
import numpy as np


# Carson earth equivalent depths (feet) by soil classification:
# 1: wet (27.9), 2: swampy (882.0), 3: average (2790.0), 4: dry (8820.0)
SOIL_DE_PRESETS = {
    1: 27.9,
    2: 882.0,
    3: 2790.0,
    4: 8820.0,
}


@dataclass(frozen=True)
class OverheadConductor:
    """Electrical and physical parameters of an overhead conductor."""
    name: str
    gmr_ft: float
    diameter_in: float
    r_ac_per_mile: float          # AC resistance at operating temperature (ohms/mile)
    r_dc_per_mile: float | None = None  # DC resistance (ohms/mile)


@dataclass(frozen=True)
class ConductorPosition:
    """Spatial coordinate of a conductor in feet.

    x_ft : horizontal distance from reference centerline (feet)
    y_ft : vertical height above ground (feet)
    """
    x_ft: float
    y_ft: float


@dataclass
class OverheadLineGeometry:
    """Spatial geometry of phase and neutral/shield conductors."""
    phases: dict[str, ConductorPosition] = field(default_factory=dict)
    neutrals: dict[str, ConductorPosition] = field(default_factory=dict)


@dataclass(frozen=True)
class LineImpedanceResult:
    """Series impedance results for an overhead line circuit."""
    z_primitive: np.ndarray        # (N+M) x (N+M) Carson primitive matrix (ohms/mile)
    z_abc: np.ndarray              # NxN Kron-reduced phase matrix (ohms/mile)
    z_012: np.ndarray | None       # 3x3 sequence impedance matrix (ohms/mile), if 3-phase
    z1: complex                    # Positive-sequence impedance (ohms/mile)
    z0: complex                    # Zero-sequence impedance (ohms/mile)
    z2: complex                    # Negative-sequence impedance (ohms/mile)


@dataclass(frozen=True)
class LineAdmittanceResult:
    """Shunt capacitance and charging admittance results."""
    p_matrix: np.ndarray           # Maxwell potential coefficients matrix
    c_abc: np.ndarray              # Kron-reduced capacitance matrix (F/mile)
    y_abc: np.ndarray              # Shunt admittance matrix (Siemens/mile)
    b1: float                      # Positive-sequence susceptance (Siemens/mile)
    b0: float                      # Zero-sequence susceptance (Siemens/mile)


class OverheadLineImpedance:
    """Calculates series impedance for overhead multi-conductor configurations.

    Uses Carson's equations with generalized Kron reduction for arbitrary M neutrals,
    supporting single-phase, two-phase (V-phase), and three-phase lines.
    """

    def __init__(
        self,
        conductors: dict[str, OverheadConductor],
        geometry: OverheadLineGeometry,
        frequency: float = 60.0,
        earth_resistivity_or_De: float = 2790.0,
    ):
        """
        Parameters
        ----------
        conductors : dict[str, OverheadConductor]
            Conductor parameters keyed by wire label (e.g. {'A': condA, 'B': condB, 'N': condN}).
        geometry : OverheadLineGeometry
            Conductor physical spatial coordinates (x_ft, y_ft).
        frequency : float, optional
            System operating frequency in Hz (default 60.0).
        earth_resistivity_or_De : float, optional
            Earth return equivalent depth De in feet (default 2790.0 for average soil).
            If a value < 20.0 is given, it is treated as soil resistivity rho (ohm-m),
            and De is computed via Carson's formula De = 2160 * sqrt(rho / f).
        """
        self.f = float(frequency)
        self.conductors = conductors
        self.geometry = geometry

        # Resolve Carson equivalent depth De
        if earth_resistivity_or_De < 20.0:
            rho = float(earth_resistivity_or_De)
            self.De = 2160.0 * np.sqrt(rho / self.f)
        else:
            self.De = float(earth_resistivity_or_De)

        # Frequency scaling
        self.w = 2.0224e-3 * (self.f / 60.0)
        self.resd = 1.588e-3 * self.f

    def calc_primitive_matrix(self) -> tuple[np.ndarray, list[str]]:
        """Construct the (N+M) x (N+M) primitive impedance matrix in ohms/mile."""
        phase_labels = sorted(self.geometry.phases.keys())
        neutral_labels = sorted(self.geometry.neutrals.keys())
        all_labels = phase_labels + neutral_labels
        n_total = len(all_labels)

        if n_total == 0:
            raise ValueError('Line geometry has no conductors.')

        Z_prim = np.zeros((n_total, n_total), dtype=np.complex128)

        # Retrieve coordinates and conductor parameters
        coords = {}
        for k in phase_labels:
            coords[k] = self.geometry.phases[k]
        for k in neutral_labels:
            coords[k] = self.geometry.neutrals[k]

        for i, lbl_i in enumerate(all_labels):
            cond_i = self.conductors[lbl_i]
            pos_i = coords[lbl_i]
            # Self-impedance
            Z_prim[i, i] = (
                cond_i.r_ac_per_mile
                + self.resd
                + 1j * self.w * self.f * np.log(self.De / cond_i.gmr_ft)
            )

            for j, lbl_j in enumerate(all_labels):
                if i != j:
                    pos_j = coords[lbl_j]
                    dist_ij = np.sqrt(
                        (pos_i.x_ft - pos_j.x_ft) ** 2 + (pos_i.y_ft - pos_j.y_ft) ** 2
                    )
                    if dist_ij <= 0:
                        raise ValueError(
                            f'Conductors {lbl_i} and {lbl_j} have overlapping coordinates.'
                        )
                    Z_prim[i, j] = (
                        self.resd + 1j * self.w * self.f * np.log(self.De / dist_ij)
                    )

        return Z_prim, all_labels

    def calc_impedance(
        self, transposed: bool = False, span_miles: float = 1.0
    ) -> LineImpedanceResult:
        """Compute the Kron-reduced phase impedance matrix and symmetrical components.

        Parameters
        ----------
        transposed : bool, optional
            If True, applies classical phase transposition averaging to Zabc.
        span_miles : float, optional
            Line length in miles to scale impedances (default 1.0 for per-mile values).
        """
        Z_prim, all_labels = self.calc_primitive_matrix()
        n_phases = len(self.geometry.phases)
        n_neutrals = len(self.geometry.neutrals)

        if n_neutrals > 0:
            # Partition primitive matrix
            Zpp = Z_prim[0:n_phases, 0:n_phases]
            Zpn = Z_prim[0:n_phases, n_phases:]
            Znp = Z_prim[n_phases:, 0:n_phases]
            Znn = Z_prim[n_phases:, n_phases:]

            # Kron reduction: Zabc = Zpp - Zpn @ inv(Znn) @ Znp
            Znn_inv = np.linalg.inv(Znn)
            z_abc = Zpp - Zpn @ Znn_inv @ Znp
        else:
            z_abc = Z_prim[0:n_phases, 0:n_phases]

        # Symmetrical components for three-phase lines
        if n_phases == 3:
            if transposed:
                # Transposition: average self and mutual terms
                zs = (z_abc[0, 0] + z_abc[1, 1] + z_abc[2, 2]) / 3.0
                zm = (z_abc[0, 1] + z_abc[1, 2] + z_abc[2, 0]
                      + z_abc[1, 0] + z_abc[2, 1] + z_abc[0, 2]) / 6.0
                z_abc_trans = np.array([
                    [zs, zm, zm],
                    [zm, zs, zm],
                    [zm, zm, zs]
                ], dtype=np.complex128)
                z_calc = z_abc_trans
            else:
                z_calc = z_abc

            a = rect(1.0, (2.0 * np.pi) / 3.0)
            A = np.array([
                [1.0, 1.0, 1.0],
                [1.0, a ** 2, a],
                [1.0, a, a ** 2],
            ])
            A_inv = np.linalg.inv(A)
            z_012 = A_inv @ z_calc @ A

            z0 = complex(z_012[0, 0]) * span_miles
            z1 = complex(z_012[1, 1]) * span_miles
            z2 = complex(z_012[2, 2]) * span_miles
            z_012_out = z_012 * span_miles
        elif n_phases == 1:
            # Single phase: Z1 = Z0 = loop impedance
            z1 = complex(z_abc[0, 0]) * span_miles
            z0 = z1
            z2 = z1
            z_012_out = None
        else:
            # Two-phase line
            z1 = complex(z_abc[0, 0]) * span_miles
            z0 = complex(z_abc[1, 1]) * span_miles
            z2 = z1
            z_012_out = None

        return LineImpedanceResult(
            z_primitive=Z_prim * span_miles,
            z_abc=z_abc * span_miles,
            z_012=z_012_out,
            z1=z1,
            z0=z0,
            z2=z2,
        )


class OverheadLineCapacitance:
    """Calculates shunt capacitance and admittance using Maxwell potential coefficients."""

    def __init__(
        self,
        conductors: dict[str, OverheadConductor],
        geometry: OverheadLineGeometry,
        frequency: float = 60.0,
    ):
        self.f = float(frequency)
        self.conductors = conductors
        self.geometry = geometry
        # Permittivity constant in F/mile
        # epsilon_0 = 8.854187817e-12 F/m * 1609.344 m/mile
        self.eps0 = 8.854187817e-12 * 1609.344

    def calc_potential_matrix(self) -> tuple[np.ndarray, list[str]]:
        """Construct the Maxwell potential coefficient matrix P in mile/Farad."""
        phase_labels = sorted(self.geometry.phases.keys())
        neutral_labels = sorted(self.geometry.neutrals.keys())
        all_labels = phase_labels + neutral_labels
        n_total = len(all_labels)

        if n_total == 0:
            raise ValueError('Line geometry has no conductors.')

        P = np.zeros((n_total, n_total), dtype=np.float64)
        coords = {}
        for k in phase_labels:
            coords[k] = self.geometry.phases[k]
        for k in neutral_labels:
            coords[k] = self.geometry.neutrals[k]

        k_factor = 1.0 / (2.0 * np.pi * self.eps0)

        for i, lbl_i in enumerate(all_labels):
            pos_i = coords[lbl_i]
            cond_i = self.conductors[lbl_i]
            r_ft = (cond_i.diameter_in / 2.0) / 12.0
            h_i = pos_i.y_ft

            # Self-potential coefficient
            P[i, i] = k_factor * np.log((2.0 * h_i) / r_ft)

            for j, lbl_j in enumerate(all_labels):
                if i != j:
                    pos_j = coords[lbl_j]
                    h_j = pos_j.y_ft
                    # Direct distance D_ij
                    d_ij = np.sqrt(
                        (pos_i.x_ft - pos_j.x_ft) ** 2 + (h_i - h_j) ** 2
                    )
                    # Image distance S_ij
                    s_ij = np.sqrt(
                        (pos_i.x_ft - pos_j.x_ft) ** 2 + (h_i + h_j) ** 2
                    )
                    P[i, j] = k_factor * np.log(s_ij / d_ij)

        return P, all_labels

    def calc_admittance(self, span_miles: float = 1.0) -> LineAdmittanceResult:
        """Compute shunt capacitance matrix and sequence charging susceptance."""
        P, all_labels = self.calc_potential_matrix()
        n_phases = len(self.geometry.phases)
        n_neutrals = len(self.geometry.neutrals)

        # Invert potential matrix to get full capacitance matrix
        C_prim = np.linalg.inv(P)

        if n_neutrals > 0:
            # Kron reduction on capacitance matrix for grounded neutrals
            Cpp = C_prim[0:n_phases, 0:n_phases]
            Cpn = C_prim[0:n_phases, n_phases:]
            Cnp = C_prim[n_phases:, 0:n_phases]
            Cnn = C_prim[n_phases:, n_phases:]

            C_abc = Cpp - Cpn @ np.linalg.inv(Cnn) @ Cnp
        else:
            C_abc = C_prim[0:n_phases, 0:n_phases]

        omega = 2.0 * np.pi * self.f
        Y_abc = 1j * omega * C_abc

        if n_phases == 3:
            a = rect(1.0, (2.0 * np.pi) / 3.0)
            A = np.array([
                [1.0, 1.0, 1.0],
                [1.0, a ** 2, a],
                [1.0, a, a ** 2],
            ])
            A_inv = np.linalg.inv(A)
            Y_012 = A_inv @ Y_abc @ A
            b0 = float(Y_012[0, 0].imag) * span_miles
            b1 = float(Y_012[1, 1].imag) * span_miles
        else:
            b1 = float(Y_abc[0, 0].imag) * span_miles
            b0 = b1

        return LineAdmittanceResult(
            p_matrix=P,
            c_abc=C_abc * span_miles,
            y_abc=Y_abc * span_miles,
            b1=b1,
            b0=b0,
        )
