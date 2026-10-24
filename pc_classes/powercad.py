# -*- coding: utf-8 -*-
"""
Power system electrical calculations for distribution studies.

Implements conductor ampacity (IEEE 738-style heat balance), phase
impedance from pole construction geometry (Carson's equations with
Kron reduction of the neutral), shunt/harness calculations, transformer
and line impedance modeling, symmetrical-component fault currents, and
service voltage drop.

The calculation engine (dataframe in, dataframe out) is separated from
CSV reporting so it can be embedded in other projects. Failures raise
typed exceptions instead of silently defaulting.
"""

import numbers
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats as ssp

from .pc_functions import dataconstants as dct
from .pc_functions import datafunctions as dfn
from .pc_functions import testfunctions as tfn
from .thermal_ampacity import AmpacityEnvironment, calculate_conductor_ampacity

_INDEX = ['StudyPoleTag', 'PoleTag', 'PoleNumber']

_CONDUCTION_TYPES = {'Copper': 1, 'ACCC': 2}

_CONSTRUCTION_FAMILIES = {
    '7200': ('7200_A', '7200_B', '7200_C'),
    '14400': ('14400_A', '14400_B', '14400_C', '14400_D'),
    '34500_46000': ('34500_46000',),
    '69000': ('69000',),
}

# 60 Hz earth-return constants (Carson's equivalent depth terms).
# w: inductive reactance spacing factor coefficient (ohms/mile).
# resd: earth resistance term (ohms/mile) at 60 Hz.
_W60 = 2.0224e-3
_RESD60 = 1.588e-3 * 60.0

# Soil type (environmenttype) -> Carson equivalent depth De (feet).
_SOIL_DE = {
    1: 27.9,     # wet
    2: 882.0,    # swampy
    3: 2790.0,   # average
    4: 8820.0,   # dry
}


class PowerCalcError(Exception):
    """Base class for power calculation errors."""


class MissingColumnError(PowerCalcError):
    """A required column is absent from an input database."""


class UnknownAssemblyError(PowerCalcError):
    """An assembly name could not be resolved in the construction database."""


class UnknownConductorError(PowerCalcError):
    """A conductor type + name pair could not be resolved."""


class InvalidGeometryError(PowerCalcError):
    """Construction geometry needed for impedance is missing."""


@dataclass
class PowerCalcConfig:
    """Parameters for the impedance / ampacity study."""
    project_name: str
    project_dir: str
    frequency: float = 60.0
    # Soil type: 1 wet, 2 swampy, 3 average, 4 dry.
    environmenttype: int = 3
    voltage_family: str = '7200'
    ampacity_env: AmpacityEnvironment = None

    def __post_init__(self):
        self.path = Path(self.project_dir)
        if not isinstance(self.frequency, numbers.Real) or self.frequency <= 0:
            raise ValueError(
                f'frequency must be a positive number, got {self.frequency!r}')
        if self.environmenttype not in _SOIL_DE:
            raise ValueError(
                f'environmenttype must be one of {sorted(_SOIL_DE)}, '
                f'got {self.environmenttype!r}')
        if self.voltage_family not in _CONSTRUCTION_FAMILIES:
            raise ValueError(
                f'Unknown voltage family {self.voltage_family!r}, '
                f'expected one of {sorted(_CONSTRUCTION_FAMILIES)}')
        if self.ampacity_env is None:
            self.ampacity_env = AmpacityEnvironment()


def _require_columns(df, columns, source):
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise MissingColumnError(f'{source} is missing required columns: {missing}')


def _empty_indexed_frame(columns):
    index = pd.MultiIndex(levels=[[], [], []], codes=[[], [], []],
                           names=_INDEX)
    return pd.DataFrame(index=index, columns=columns)


class faultCalculationClass:
    """Impedance, ampacity, fault and voltage-drop calculation engine."""

    def __init__(self, config=None):
        self.Amat, self.Ainv, self.compd, self.compy = dfn.generate_transforms()
        self.conductordb = dfn.generate_conductor_database()
        self.distxfmr = dct.distxfmr
        self.xrcurve = dct.xrcurve
        self.constructions = dfn.generate_pole_construction()

        self.cfg = config
        if config is not None:
            if not isinstance(config, PowerCalcConfig):
                raise TypeError(
                    f'faultCalculationClass requires a PowerCalcConfig, '
                    f'got {type(config).__name__}')
            family = self.cfg.voltage_family
            self._family_tables = [self.constructions[key]
                                   for key in _CONSTRUCTION_FAMILIES[family]
                                   if key in self.constructions]
            if not self._family_tables:
                raise MissingColumnError(
                    f'No construction tables found for family {family!r}')
            self.poledb = _empty_indexed_frame(list(_INDEX))
            self.conddb = _empty_indexed_frame(list(_INDEX))
        else:
            self._family_tables = []
            self.poledb = _empty_indexed_frame(list(_INDEX))
            self.conddb = _empty_indexed_frame(list(_INDEX))

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def _load_databases(self):
        cfg = self.cfg
        for name in ('poledb', 'conddb'):
            path = cfg.path / f'{name}.csv'
            if not path.is_file():
                raise FileNotFoundError(f'Required input file not found: {path}')
        for name in ('poledb', 'conddb'):
            frame = pd.read_csv(cfg.path / f'{name}.csv',
                                dtype={'StudyPoleTag': str, 'PoleTag': str})
            _require_columns(frame, _INDEX, f'{name}.csv')
            setattr(self, name, frame.set_index(_INDEX).sort_index())

    # ------------------------------------------------------------------
    # Conductor ampacity (IEEE 738-style heat balance)
    # ------------------------------------------------------------------
    def calcCurrent(self):
        """Populate resistance (OhmsCalc, ohms/mile at operating
        temperature) and ampacity (CurrentCalc, amps) on conddb."""
        env = self.cfg.ampacity_env
        if env is None:
            env = self.ampacity_env = AmpacityEnvironment()

        conddb = self.conddb
        _require_columns(conddb, ('ConductorType', 'ConductorName'),
                         'conddb.csv')
        for column, default in (('TAmb', 25.0), ('TRise', 50.0),
                                ('GMR', np.nan), ('DCOhmsCalc', np.nan),
                                ('ACOhmsCalc', np.nan), ('GMRCalc', np.nan),
                                ('OhmsCalc', np.nan), ('CurrentCalc', np.nan)):
            if column not in conddb.columns:
                conddb[column] = default
        conddb[['TAmb', 'TRise']] = conddb[['TAmb', 'TRise']].astype(float)

        params = ['gmr', 'DCohms', 'ACohms']
        for row_index, row in conddb.iterrows():
            pl1 = self._lookup_product(self.conductordb, row['ConductorType'],
                                        row['ConductorName'], row_index)
            values = {p: pl1.at[pl1.index[0], p] for p in params
                      if p in pl1.columns}
            if 'gmr' not in values or 'DCohms' not in values or 'ACohms' not in values:
                raise UnknownConductorError(
                    f'Conductor database lacks GMR/DCohms/ACohms for '
                    f'{row["ConductorType"]}/{row["ConductorName"]!r} '
                    f'(row {row_index})')
            gmrval = float(values['gmr'])
            dcohmval = float(values['DCohms'])
            acohmval = float(values['ACohms'])

            conddb.at[row_index, 'GMR'] = gmrval
            conddb.at[row_index, 'DCOhmsCalc'] = dcohmval
            conddb.at[row_index, 'ACOhmsCalc'] = acohmval
            current, ohmval = self._conductor_ampacity(
                gmrval, dcohmval, acohmval, row['ConductorType'],
                float(row['TAmb']), float(row['TRise']), env)
            conddb.at[row_index, 'GMRCalc'] = gmrval
            conddb.at[row_index, 'OhmsCalc'] = ohmval
            conddb.at[row_index, 'CurrentCalc'] = current
        return conddb

    def _conductor_ampacity(self, gmrval, dcohmval, acohmval, conductortype,
                            tempamb, temprise, env):
        """IEEE 738-style heat balance for one conductor. Returns
        (ampacity, ac resistance ohms/mile at operating temperature)."""
        result = calculate_conductor_ampacity(
            gmr_ft=gmrval,
            dcohm_per_kft=dcohmval,
            acohm_per_kft=acohmval,
            conductor_type=conductortype,
            temp_amb_c=tempamb,
            temp_rise_c=temprise,
            env=env,
        )
        return result.ampacity_amps, result.r_ac_ohms_per_mile

    def _lookup_product(self, product_db, conductor_type, conductor_name,
                        row_index):
        pl1 = product_db.loc[product_db.index.get_level_values(0) == conductor_type]
        match = pl1[pl1['name'] == conductor_name]
        if match.empty:
            raise UnknownConductorError(
                f'Conductor {conductor_type}/{conductor_name!r} not found '
                f'in product database (row {row_index})')
        return match

    # ------------------------------------------------------------------
    # Line geometry
    # ------------------------------------------------------------------
    def towerCalc(self):
        """Resolve each study-pole row's assembly and compute phase-pair
        and phase-neutral horizontal spacing (ft) from construction
        geometry. Sets LineType (1/2/3 phases) and AB/BC/CA/AN/BN/CN."""
        conddb = self.conddb
        for column in ('LineType', 'AB', 'BC', 'CA', 'AN', 'BN', 'CN'):
            if column not in conddb.columns:
                conddb[column] = np.nan

        for polein in conddb.index:
            if polein[2] != 0:
                continue
            assembly = conddb.at[polein, 'Assembly']
            if pd.isna(assembly):
                raise InvalidGeometryError(
                    f'Study pole row {polein} has no Assembly value')
            asm = self._find_assembly(str(assembly))
            line_type = _phases_from_table(asm)
            conddb.at[polein, 'LineType'] = line_type
            if line_type == 3:
                pairs = (('AB', 'Phase1', 'Phase2'), ('BC', 'Phase2', 'Phase3'),
                         ('CA', 'Phase3', 'Phase1'))
            elif line_type == 2:
                pairs = (('AB', 'Phase1', 'Phase2'),)
            else:
                pairs = ()
            pairs += tuple((f'{letter}N', p, 'Neutral')
                           for letter, p in zip('ABC',
                                               _phase_slots(line_type)))
            for column, a, b in pairs:
                conddb.at[polein, column] = _center_distance_ft(asm, a, b)
        return conddb

    def _find_assembly(self, name):
        name = str(name).strip()
        matches = []
        for table in self._family_tables:
            if 'Name' not in table.columns:
                continue
            match = table.loc[table['Name'] == name]
            if match.empty:
                match = table.loc[table['Name'].str.contains(name, na=False)]
            if match.empty and 'AltName' in table.columns:
                match = table.loc[table['AltName'] == name]
            if match.empty and 'AltName' in table.columns:
                match = table.loc[table['AltName'].str.contains(
                    name, na=False)]
            if not match.empty:
                matches.append(match.iloc[0])
        if not matches:
            raise UnknownAssemblyError(
                f'Assembly {name!r} not found in construction family '
                f'{self.cfg.voltage_family!r}')
        if len(matches) > 1:
            found_in = [m['Name'] for m in matches]
            raise UnknownAssemblyError(
                f'Assembly {name!r} is ambiguous in family '
                f'{self.cfg.voltage_family!r}: matched {found_in}')
        return matches[0]

    # ------------------------------------------------------------------
    # Spans
    # ------------------------------------------------------------------
    def _calc_spans(self):
        poledb = self.poledb
        conddb = self.conddb
        if 'Span' not in poledb.columns:
            poledb['Span'] = np.nan
        if 'Span' not in conddb.columns:
            conddb['Span'] = np.nan
        # Integer span columns cannot hold the mile-converted floats.
        poledb['Span'] = poledb['Span'].astype(float)
        conddb['Span'] = conddb['Span'].astype(float)
        _require_columns(poledb, ('MapX', 'MapY'), 'poledb.csv')

        refx = refy = None
        for pole in poledb.index:
            pole_row = poledb.loc[pole]
            span = pole_row['Span']
            if not tfn.testPositiveFloat(span):
                if pole[2] == 0:
                    refx = pole_row['MapX']
                    refy = pole_row['MapY']
                normx = pole_row['MapX'] - refx
                normy = pole_row['MapY'] - refy
                if pole[2] > 0:
                    span = float(np.sqrt(normx ** 2 + normy ** 2))
                    poledb.at[pole, 'Span'] = span
            # Convert feet to miles.
            poledb.at[pole, 'Span'] = (span if tfn.testPositiveFloat(span)
                                       else 0.0) / 5280.0

        for polein in conddb.index:
            span = conddb.at[polein, 'Span']
            if tfn.testPositiveFloat(span):
                # Explicit conductor spans are in feet, matching poledb.
                conddb.at[polein, 'Span'] = span / 5280.0
            else:
                conddb.at[polein, 'Span'] = poledb.loc[
                    (polein[0], polein[1]), 'Span'].iloc[0]
        return poledb, conddb

    # ------------------------------------------------------------------
    # Phase impedance
    # ------------------------------------------------------------------
    def calcImpedance(self):
        """Compute phase impedance (Z0/Z1, ohms) for each study-pole
        section using Carson's equations with Kron reduction. Requires
        calcCurrent() results on conddb."""
        f = self.cfg.frequency
        try:
            De = _SOIL_DE[self.cfg.environmenttype]
        except KeyError:
            raise ValueError(
                f'environmenttype must be one of {sorted(_SOIL_DE)}, '
                f'got {self.cfg.environmenttype!r}')
        w = _W60
        resd = _RESD60 * (f / 60.0)
        # NOTE: the reactance term below uses the 60 Hz coefficient (w)
        # directly; scale for other frequencies in POWERCAD_AUDIT.md (item A2).

        self.towerCalc()
        self._calc_spans()

        conddb = self.conddb
        for column in ('Z0real', 'Z0imag', 'Z1real', 'Z1imag'):
            if column not in conddb.columns:
                conddb[column] = np.nan

        for polein in conddb.index:
            if polein[2] != 0:
                continue
            pl1 = conddb.loc[polein[0]]
            linetype = pl1.at[(polein[1], 0), 'LineType']
            if pd.isna(linetype):
                raise InvalidGeometryError(
                    f'LineType unresolved for study pole row {polein}')
            if linetype == 3:
                f1 = f2 = f3 = 0.33
                fmat = np.asmatrix([[f1, f2, f3],
                                    [f3, f1, f2],
                                    [f2, f3, f1]])
                zs = [pl1.at[(polein[1], i), 'OhmsCalc'] + resd
                      + 1j * w * f * np.log(De
                                            / pl1.at[(polein[1], i), 'GMRCalc'])
                      for i in range(3)]
                zk = (resd + 1j * w * f
                      * np.asmatrix([np.log(De / pl1.at[(polein[1], 0), 'AB']),
                                     np.log(De / pl1.at[(polein[1], 0), 'BC']),
                                     np.log(De / pl1.at[(polein[1], 0), 'CA'])])
                      * fmat)
                zabc = np.asmatrix([[zs[0], zk[0, 0], zk[0, 2]],
                                    [zk[0, 0], zs[1], zk[0, 1]],
                                    [zk[0, 2], zk[0, 1], zs[2]]])
                zsn = (pl1.at[(polein[1], 3), 'OhmsCalc'] + resd
                       + 1j * w * f * np.log(De
                                             / pl1.at[(polein[1], 3), 'GMRCalc']))
                zkn = np.asmatrix(
                    [resd + 1j * w * f * np.log(De / pl1.at[(polein[1], 0), 'AN']),
                     resd + 1j * w * f * np.log(De / pl1.at[(polein[1], 0), 'BN']),
                     resd + 1j * w * f * np.log(De / pl1.at[(polein[1], 0), 'CN'])])
                zabc = zabc - zkn.T * (1.0 / zsn) * zkn
            elif linetype == 2:
                f1 = f2 = 0.5
                fmat = np.asmatrix([[f1, f2, 0],
                                    [f2, f1, 0],
                                    [0, 0, 0]])
                zsa = (pl1.at[(polein[1], 0), 'OhmsCalc'] + resd
                       + 1j * w * f * np.log(De
                                             / pl1.at[(polein[1], 0), 'GMRCalc']))
                zsb = (pl1.at[(polein[1], 1), 'OhmsCalc'] + resd
                       + 1j * w * f * np.log(De
                                             / pl1.at[(polein[1], 1), 'GMRCalc']))
                zk = resd + 1j * w * f * np.log(De
                                                / pl1.at[(polein[1], 0), 'AB']) * fmat
                zabc = np.asmatrix([[zsa, zk[0, 0], 0],
                                    [zk[0, 0], zsb, 0],
                                    [0, 0, 0]])
                zsn = (pl1.at[(polein[1], 2), 'OhmsCalc'] + resd
                       + 1j * w * f * np.log(De
                                             / pl1.at[(polein[1], 2), 'GMRCalc']))
                zkn = np.asmatrix(
                    [resd + 1j * w * f * np.log(De / pl1.at[(polein[1], 0), 'AN']),
                     resd + 1j * w * f * np.log(De / pl1.at[(polein[1], 0), 'BN']),
                     0.0])
                zabc = zabc - zkn.T * (1.0 / zsn) * zkn
            else:
                zsa = (pl1.at[(polein[1], 0), 'OhmsCalc'] + resd
                       + 1j * w * f * np.log(De
                                             / pl1.at[(polein[1], 0), 'GMRCalc']))
                zabc = np.asmatrix([[zsa, 0, 0], [0, 0, 0], [0, 0, 0]])
                zsn = zsa
                zkn = resd + 1j * w * f * np.log(De / 1.0)
                zabc[0, 0] = zsn - (zkn * zkn) / zsn
            zabc = zabc * pl1.at[(polein[1], 0), 'Span']
            z012 = self.Ainv * zabc * self.Amat
            z0 = z012[0, 0] + z012[0, 1] + z012[0, 2]
            z1 = z012[1, 0] + z012[1, 1] + z012[1, 2]
            conddb.at[polein, 'Z1real'] = z1.real
            conddb.at[polein, 'Z1imag'] = z1.imag
            conddb.at[polein, 'Z0real'] = z0.real
            conddb.at[polein, 'Z0imag'] = z0.imag
        return conddb

    # ------------------------------------------------------------------
    # Fault calculations (symmetrical components)
    # ------------------------------------------------------------------
    def ifault(self, zlt, vf, zgnd, zfault, matreturn):
        """ifault\n
        \n
        zlt - impedance in pu, np.array complex format [[r1+x1j],[r0+x0j]]
        vf - voltage in pu, float
        zgnd - ground impedance in pu, float
        zfault - fault impedance in pu, float
        matreturn:
            0 Iabc matrix
            1 Iabc matrix dy viewed from D
            2 Iabc matrix yd viewed from Y
            3 I012 matrix dy viewed from D
            4 I012 matrix yd viewed from Y
            5 I012 matrix
        """
        zt = zlt[0, 0]
        z0t = zlt[1, 0]
        # Phase to ground fault (A-G)
        I012 = np.array([[(vf / (z0t + zt + zt + zfault + (3 * zgnd)))],
                         [(vf / (z0t + zt + zt + zfault + (3 * zgnd)))],
                         [(vf / (z0t + zt + zt + zfault + (3 * zgnd)))]])
        Iabc = np.dot(self.Amat, I012)
        Iseq = I012
        I012d = np.multiply(self.compy, I012)
        IabcD = np.dot(self.Amat, I012d)
        IseqD = I012d
        I012y = np.multiply(self.compd, Iseq)
        IabcY = np.dot(self.Amat, I012y)
        IseqY = I012y
        # Phase to phase fault (BC)
        I012 = np.array([[0],
                         [(vf / (zt + zt + (zfault)))],
                         [-vf / (zt + zt + (zfault))]])
        Iabc = np.vstack((Iabc, np.dot(self.Amat, I012)))
        Iseq = np.vstack((Iseq, I012))
        I012d = np.multiply(self.compy, I012)
        IabcD = np.vstack((IabcD, np.dot(self.Amat, I012d)))
        IseqD = np.vstack((IseqD, I012d))
        I012y = np.multiply(self.compd, I012)
        IabcY = np.vstack((IabcY, np.dot(self.Amat, I012y)))
        IseqY = np.vstack((IseqY, I012y))
        # Phase to phase to ground fault (BC-G)
        I1 = vf / (zt + (zfault / 2)
                   + ((zt + (zfault / 2)) * (z0t + (zfault / 2) + (3 * zgnd)))
                   / (zt + z0t + zfault + (3 * zgnd)))
        I012 = np.array([[-I1 * (z0t / (zt + z0t))],
                         [I1],
                         [-I1 * (zt / (zt + z0t))]])
        Iabc = np.vstack((Iabc, np.dot(self.Amat, I012)))
        Iseq = np.vstack((Iseq, I012))
        I012d = np.multiply(self.compy, I012)
        IabcD = np.vstack((IabcD, np.dot(self.Amat, I012d)))
        IseqD = np.vstack((IseqD, I012d))
        I012y = np.multiply(self.compd, I012)
        IabcY = np.vstack((IabcY, np.dot(self.Amat, I012y)))
        IseqY = np.vstack((IseqY, I012y))
        # Three phase to ground fault
        I1 = (vf / (zt + zfault + zgnd))
        I012 = np.array([[0], [I1], [0]])
        Iabc = np.vstack((Iabc, np.dot(self.Amat, I012)))
        Iseq = np.vstack((Iseq, I012))
        I012d = np.multiply(self.compy, I012)
        IabcD = np.vstack((IabcD, np.dot(self.Amat, I012d)))
        IseqD = np.vstack((IseqD, I012d))
        I012y = np.multiply(self.compd, I012)
        IabcY = np.vstack((IabcY, np.dot(self.Amat, I012y)))
        IseqY = np.vstack((IseqY, I012y))

        if matreturn == 1:
            return IabcD
        elif matreturn == 2:
            return IabcY
        elif matreturn == 3:
            return IseqD
        elif matreturn == 4:
            return IseqY
        elif matreturn == 5:
            return Iseq
        else:
            return Iabc

    def xfmr(self, MVAbase, Zpercent, XRratio=False, results=False, zeromult=1):
        """xfmr\n
        \n
        MVAbase - Transformer Base MVA, float
        Zpercent - Percent Impedance, float
        XRratio - Default False (random) or float
        results - 'rand' or False for random, 'rlow' random low range,
                  'rhigh' random high range
        zeromult - multiplier for zero sequence, float
        """
        if tfn.testPositiveFloat(XRratio) == False:
            XRratio = self.xrcalc(MVAbase, results)
        z1 = (Zpercent / 100)
        r1 = z1 / np.sqrt(1 + XRratio ** 2)
        x1 = 1j * r1 * XRratio
        r0 = r1 * zeromult
        x0 = x1 * zeromult
        z1 = r1 + x1
        z0 = r0 + x0
        return np.array([[z1], [z0]])

    def xrcalc(self, MVAbase, results):
        if tfn.testIsString(results) == False:
            results = 'rand'

        if results == 'low':
            if MVAbase >= 12:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * (2 - 1.677)
            elif MVAbase >= 2.5:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * (2 - 1.5)
            elif MVAbase >= 0.5:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * (2 - 1.3)
            else:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1])
        elif results == 'high':
            if MVAbase >= 12:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * 1.677
            elif MVAbase >= 2.5:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * 1.5
            elif MVAbase >= 0.5:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * 1.3
            else:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1])
        elif results == 'rlow':
            if MVAbase >= 12:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * (1 - abs(1 - ssp.norm.rvs(loc=1, scale=(0.677 / 3))))
            elif MVAbase >= 2.5:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * (1 - abs(1 - ssp.norm.rvs(loc=1, scale=(0.5 / 3))))
            elif MVAbase >= 0.5:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * (1 - abs(1 - ssp.norm.rvs(loc=1, scale=(0.3 / 3))))
            else:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1])
        elif results == 'rhigh':
            if MVAbase >= 12:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * (1 + abs(1 - ssp.norm.rvs(loc=1, scale=(0.677 / 3))))
            elif MVAbase >= 2.5:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * (1 + abs(1 - ssp.norm.rvs(loc=1, scale=(0.5 / 3))))
            elif MVAbase >= 0.5:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * (1 + abs(1 - ssp.norm.rvs(loc=1, scale=(0.3 / 3))))
            else:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1])
        elif results == 'rand':
            if MVAbase >= 12:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * ssp.norm.rvs(loc=1, scale=(0.677 / 3))
            elif MVAbase >= 2.5:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * ssp.norm.rvs(loc=1, scale=(0.5 / 3))
            elif MVAbase >= 0.5:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1]) * ssp.norm.rvs(loc=1, scale=(0.3 / 3))
            else:
                XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1])
        else:
            XRratio = np.interp(MVAbase, self.xrcurve[:, 0], self.xrcurve[:, 1])
        return XRratio

    def abcseq(self, abcmat):
        seqmat = self.Ainv * abcmat * self.Amat
        return seqmat

    def abc2seq(self, abc):
        seq = np.dot(self.Ainv, abc)
        return seq

    def seq2abc(self, seq):
        abc = np.dot(self.Amat, seq)
        return abc

    def dy1(self, ID):
        I012 = np.dot(self.Ainv, ID)
        I012Y = np.multiply(self.compy, I012)
        IY = np.dot(self.Amat, I012Y)
        return IY

    def yd1(self, IY):
        I012 = np.dot(self.Ainv, IY)
        I012D = np.multiply(self.compd, I012)
        ID = np.dot(self.Amat, I012D)
        return ID

    def calcVoltageDrop(self, zt, vs, il, pf, phase):
        """Approximate voltage drop. zt = (R, X) ohms; phase: 1 = single
        phase, 2 = center-tapped 240/120 service, 3 = three phase."""
        rf = np.sin(np.arccos(pf))
        vdrop = vs + il * zt[0] * pf + il * zt[1] * rf \
            - np.sqrt(vs ** 2 - (il * zt[1] * pf - il * zt[0] * rf) ** 2)
        if phase > 2:
            return vdrop * np.sqrt(3)
        elif phase > 1:
            return vdrop * 2
        else:
            return vdrop

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------
    def run(self, out_path=None):
        """Load project databases, run ampacity and impedance
        calculations. Writes condfcc.csv to the project directory
        (or out_path if given) and returns conddb."""
        self._load_databases()
        self.calcCurrent()
        self.calcImpedance()
        out = Path(out_path) if out_path else self.cfg.path / 'condfcc.csv'
        self.conddb.to_csv(out)
        return self.conddb


def _phases_from_table(asm):
    """Infer the number of phases from populated Phase slots."""
    for n in range(6, 0, -1):
        if f'Phase{n}Hin' in asm.index and not pd.isna(asm[f'Phase{n}Hin']):
            return min(n, 3)
    return 1


def _phase_slots(line_type):
    if line_type >= 3:
        return ('Phase1', 'Phase2', 'Phase3')
    if line_type == 2:
        return ('Phase1', 'Phase2')
    return ('Phase1',)


def _center_distance_ft(asm, a, b):
    """Distance between the centerline-based attachment points of two
    conductors, in feet. Construction geometry columns are centerline
    (z-axis) based with signed X offsets, so the distance is the plain
    coordinate difference; the pole radius never enters it. Returns NaN
    when geometry is absent (matching the legacy CSV output)."""
    columns = (f'{a}X', f'{a}Hin', f'{b}X', f'{b}Hin')
    missing = [c for c in columns
               if c not in asm.index or pd.isna(asm[c])]
    if missing:
        return np.nan
    dx = asm[f'{a}X'] - asm[f'{b}X']
    dy = asm[f'{a}Hin'] - asm[f'{b}Hin']
    return float(np.sqrt(dx * dx + dy * dy) / 12.0)
