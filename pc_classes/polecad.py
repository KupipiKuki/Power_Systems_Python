# -*- coding: utf-8 -*-
"""
Pole loading analysis (NESC-style) for joint use studies.

The calculation engine (dataframe in, dataframe out) is separated from
plotting and CSV reporting so it can be embedded in other projects.
"""

import numbers
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .pc_functions import datafunctions as dfn

_POLE_INDEX = ['StudyPoleTag', 'PoleTag', 'PoleNumber']

_POLE_CALC_COLUMNS = [
    'NormX', 'NormY', 'Span', 'NormAngle',
    'PoleCt', 'PoleCb', 'PoleCg',
    'Mrn', 'Mbn', 'Mr', 'Mb',
    'Mbx', 'Mby',
    'Mtx', 'Mty', 'Mgx', 'Mgy',
    'Mtcx', 'Mtcy', 'Mcgx', 'Mcgy',
    'Mcmax', 'Mcwsx', 'Mcwsy',
    'Mccwsx', 'Mccwsy',
    'Mex', 'Mey',
    'Mgndx', 'Mgndy',
    'Mcgndx', 'Mcgndy',
    'MtMapX', 'MtMapY',
    'MgMapX', 'MgMapY',
    'MgndMapX', 'MgndMapY',
    'McgndMapX', 'McgndMapY',
    'NeutralHeight',
]

_CONDUCTOR_CALC_COLUMNS = [
    'Mcn', 'Mc', 'Mcmax', 'Mcmaxws', 'Mcmaxx', 'Mcmaxy',
    'Mcws', 'Mcwsx', 'Mcwsy', 'Mtx', 'Mty', 'Tension',
]

_GUY_CALC_COLUMNS = ['Mtx', 'Mty', 'GuyMapX', 'GuyMapY', 'GuyTension']

_WOOD_FIBER_STRESS = 8000.0
_MOMENT_CONSTANT = 0.000264

# Assembly tables by construction family. The key is the voltage family
# prefix used in project assembly names.
_CONSTRUCTION_FAMILIES = {
    '7200': ('7200_A', '7200_B', '7200_C'),
    '14400': ('14400_A', '14400_B', '14400_C', '14400_D'),
    '34500_46000': ('34500_46000',),
    '69000': ('69000',),
}

# Letter prefix within a family -> phase slots available in that table
# (the rest fall back to the neutral slot).
_FAMILY_TABLE_LETTERS = {'7200': 'ABC', '14400': 'ABCD'}


@dataclass
class PoleCalcConfig:
    """Design parameters required by the pole loading calculations."""
    project_name: str
    project_dir: str
    design_tension: float
    strength_factor: float
    wind_load: float
    wind_overload: float
    tension_overload: float
    ice_thickness: float
    wind_angle: float
    deflection_factor: float
    voltage_family: str = '7200'
    override_span: bool = False
    override_angle: bool = False

    def __post_init__(self):
        self.path = Path(self.project_dir)
        for name in ('design_tension', 'strength_factor', 'wind_load',
                     'wind_overload', 'tension_overload', 'ice_thickness',
                     'wind_angle', 'deflection_factor'):
            value = getattr(self, name)
            if not isinstance(value, numbers.Real) or pd.isna(value):
                raise ValueError(f'{name} must be a number, got {value!r}')
        if self.voltage_family not in _CONSTRUCTION_FAMILIES:
            raise ValueError(
                f'Unknown voltage family {self.voltage_family!r}, '
                f'expected one of {sorted(_CONSTRUCTION_FAMILIES)}')


class PoleCalcError(Exception):
    """Base class for pole calculation input errors."""


class MissingColumnError(PoleCalcError):
    """A required column is absent from an input database."""


class UnknownAssemblyError(PoleCalcError):
    """An assembly name could not be resolved in the construction database."""


class UnknownConductorError(PoleCalcError):
    """A conductor/cable type + name pair could not be resolved."""


class InvalidGuyDataError(PoleCalcError):
    """Guy row data is missing or contradictory."""


def _require_columns(df, columns, source):
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise MissingColumnError(f'{source} is missing required columns: {missing}')


def _empty_indexed_frame(columns):
    index = pd.MultiIndex(levels=[[], [], []], codes=[[], [], []],
                           names=_POLE_INDEX)
    return pd.DataFrame(index=index, columns=columns)


def _is_number(value):
    return isinstance(value, numbers.Real) and not pd.isna(value)


def _is_positive(value):
    return _is_number(value) and value > 0.0


class poleCalculationClass:

    def __init__(self, config):
        if not isinstance(config, PoleCalcConfig):
            raise TypeError('poleCalculationClass requires a PoleCalcConfig')
        self.cfg = config
        self.wooddata = dfn.generate_pole_data()
        self.constructions = dfn.generate_pole_construction()
        self.conductordb = dfn.generate_conductor_database()
        self.cabledb = dfn.generate_cable_database()
        family = self.cfg.voltage_family
        self._family_tables = [self.constructions[key]
                               for key in _CONSTRUCTION_FAMILIES[family]
                               if key in self.constructions]
        if not self._family_tables:
            raise MissingColumnError(
                f'No construction tables found for family {family!r}')

    # ------------------------------------------------------------------
    # Assembly / attachment height resolution
    # ------------------------------------------------------------------

    def _find_assembly(self, name):
        name = str(name).strip()
        matches = []
        for table in self._family_tables:
            if 'Name' not in table.columns:
                continue
            match = table.loc[table['Name'] == name]
            if match.empty:
                match = table.loc[table['Name'].str.contains(name, na=False,
                                                             regex=False)]
            if match.empty and 'AltName' in table.columns:
                match = table.loc[table['AltName'] == name]
            if match.empty and 'AltName' in table.columns:
                match = table.loc[table['AltName'].str.contains(name, na=False,
                                                                regex=False)]
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

    @staticmethod
    def _conductor_height_column(asm, position):
        position = int(position) + 1
        column = f'Phase{position}Hin'
        if column in asm.index and not pd.isna(asm[column]):
            return column
        if 'NeutralHin' in asm.index and not pd.isna(asm['NeutralHin']):
            return 'NeutralHin'
        return None

    @staticmethod
    def _guy_height_column(asm, position):
        position = int(position) + 1
        for column in (f'GuyH{position}', 'GuyH1'):
            if column in asm.index and not pd.isna(asm[column]):
                return column
        return None

    # ------------------------------------------------------------------
    # Data loading and preparation
    # ------------------------------------------------------------------

    def _load_databases(self):
        cfg = self.cfg
        for name in ('poledb', 'conddb', 'guydb'):
            if not (cfg.path / f'{name}.csv').is_file():
                raise FileNotFoundError(
                    f'Required input file not found: {cfg.path / (name + ".csv")}')
        frames = {}
        for name in ('poledb', 'conddb', 'guydb', 'commdb', 'cguydb'):
            path = cfg.path / f'{name}.csv'
            if path.is_file():
                frames[name] = pd.read_csv(path, dtype={'StudyPoleTag': str, 'PoleTag': str})
            else:
                frames[name] = _empty_indexed_frame(list(_POLE_INDEX))
        for name, frame in frames.items():
            _require_columns(frame, _POLE_INDEX, f'{name}.csv')
            frames[name] = frame.set_index(_POLE_INDEX).sort_index()
        self.poledb = frames['poledb']
        self.conddb = frames['conddb']
        self.guydb = frames['guydb']
        self.commdb = frames['commdb']
        self.cguydb = frames['cguydb']

    def _default_grade_height(self, pole_row):
        species = pole_row['PoleSpecies']
        height = pole_row['PoleHeight']
        species_data = self.wooddata.xs(species, level='Species', drop_level=True)
        depth_row = species_data.loc[species_data['Height'] == height]
        if depth_row.empty:
            raise PoleCalcError(
                f'No wood pole data for species {species!r} at height {height}')
        return height - depth_row.iloc[0]['Depth']

    def _prepare_poles(self):
        for column in ('GradeHeight', 'NeutralHeight'):
            if column not in self.poledb.columns:
                self.poledb[column] = np.nan
        for study_tag in self.poledb.index.get_level_values('StudyPoleTag').unique():
            key = (study_tag, study_tag, 0)
            if key not in self.poledb.index:
                raise PoleCalcError(f'Study pole {study_tag!r} not found in poledb')
            if pd.isna(self.poledb.at[key, 'PoleHeight']):
                self.poledb.at[key, 'PoleHeight'] = 20.0
                self.poledb.at[key, 'GradeHeight'] = 16.0
            if pd.isna(self.poledb.at[key, 'PoleClass']):
                self.poledb.at[key, 'PoleClass'] = 7
            if not _is_positive(self.poledb.at[key, 'GradeHeight']):
                self.poledb.at[key, 'GradeHeight'] = self._default_grade_height(
                    self.poledb.loc[key])

    def _prepare_conductors(self):
        _require_columns(self.conddb,
                         ['Assembly', 'AssemblyHeight', 'ConductorType',
                          'ConductorName'],
                         'conddb')
        if 'DesignTension' not in self.conddb.columns:
            self.conddb['DesignTension'] = np.nan
        minheight = {}
        for row_index, row in self.conddb.iterrows():
            if not _is_positive(row['DesignTension']):
                self.conddb.at[row_index, 'DesignTension'] = self.cfg.design_tension
            if not _is_positive(row['Height']):
                study_grade = self.poledb.at[(row_index[0], row_index[0], 0), 'GradeHeight']
                name = row['Assembly']
                if not isinstance(name, str) or not name.strip():
                    raise PoleCalcError(
                        f'No Height and no Assembly for conductor row {row_index}')
                asm = self._find_assembly(name)
                column = self._conductor_height_column(asm, row_index[2])
                if column is None:
                    raise UnknownAssemblyError(
                        f'Assembly {name!r} has no usable attachment height '
                        f'for position {row_index[2]}')
                offset = asm[column]
                self.conddb.at[row_index, 'Height'] = (
                    study_grade + offset / 12.0 + row['AssemblyHeight'])
            height = self.conddb.at[row_index, 'Height']
            if not _is_positive(height):
                raise PoleCalcError(
                    f'Could not resolve attachment height for conductor row {row_index}')
            current = minheight.get(row_index[0])
            if current is None or height < current:
                minheight[row_index[0]] = height
        for study_tag, value in minheight.items():
            self.poledb.at[(study_tag, study_tag, 0), 'NeutralHeight'] = value

    def _prepare_comms(self):
        if self.commdb.empty:
            return
        _require_columns(self.commdb,
                         ['AssemblyHeight', 'ConductorType', 'ConductorName',
                          'DesignTension'],
                         'commdb')
        for column in ('Height', 'DesignTension', 'Tension'):
            if column not in self.commdb.columns:
                self.commdb[column] = np.nan
        for row_index, row in self.commdb.iterrows():
            if not _is_positive(row['DesignTension']):
                self.commdb.at[row_index, 'DesignTension'] = self.cfg.design_tension
            if _is_positive(row['Height']):
                continue
            if _is_positive(row['AssemblyHeight']):
                self.commdb.at[row_index, 'Height'] = row['AssemblyHeight']
                continue
            neutral = self.poledb.at[(row_index[0], row_index[0], 0), 'NeutralHeight']
            if not _is_positive(neutral):
                raise PoleCalcError(
                    f'Cannot resolve comm attachment height at {row_index}: '
                    'no Height, AssemblyHeight, or pole NeutralHeight')
            offsets = {0: 4.0, 1: 6.0}
            self.commdb.at[row_index, 'Height'] = neutral - offsets.get(row_index[2], 8.0)

    def _prepare_guys(self, db, is_comms):
        if db.empty:
            return
        label = 'cguydb' if is_comms else 'guydb'
        _require_columns(db, ['GuyHeight', 'GuyType'], label)
        for column in ('GuyHeight', 'GuyType', 'GuyX', 'GuyY', 'GuyTension'):
            if column not in db.columns:
                db[column] = np.nan
        # GuyHeight may hold assembly names (strings) to resolve against the
        # construction tables; keep unresolved names aside while the column
        # is converted to numeric for the computed values.
        name_heights = {index: row['GuyHeight'] for index, row in db.iterrows()
                        if isinstance(row['GuyHeight'], str)
                        and row['GuyHeight'].strip()}
        if name_heights:
            db['GuyHeight'] = pd.to_numeric(db['GuyHeight'], errors='coerce')
        for row_index, row in db.iterrows():
            key = (row_index[0], row_index[0], 0)
            if _is_positive(row['GuyHeight']):
                continue
            if row_index in name_heights:
                asm = self._find_assembly(name_heights[row_index])
                column = self._guy_height_column(asm, row_index[2])
                if column is None:
                    raise UnknownAssemblyError(
                        f'Assembly {name_heights[row_index]!r} has no guy height '
                        f'for position {row_index[2]}')
                offset = asm[column]
                db.at[row_index, 'GuyHeight'] = (
                    self.poledb.at[key, 'GradeHeight'] + offset / 12.0)
            elif is_comms:
                neutral = self.poledb.at[key, 'NeutralHeight']
                if not _is_positive(neutral):
                    raise PoleCalcError(
                        f'Cannot resolve comm guy height at {row_index}: no NeutralHeight')
                db.at[row_index, 'GuyHeight'] = neutral - 4.0
            else:
                raise InvalidGuyDataError(f'Guy height missing or invalid at {row_index}')

    def _allocate_output_columns(self):
        for column in _POLE_CALC_COLUMNS:
            if column not in self.poledb.columns:
                self.poledb[column] = np.nan
        for db in (self.conddb, self.commdb):
            for column in _CONDUCTOR_CALC_COLUMNS + ['Span', 'NormAngle']:
                if column not in db.columns:
                    db[column] = np.nan
        for db in (self.guydb, self.cguydb):
            for column in _GUY_CALC_COLUMNS:
                if column not in db.columns:
                    db[column] = np.nan

    # ------------------------------------------------------------------
    # Calculation stages
    # ------------------------------------------------------------------

    def _windAngle_wrap(self):
        return np.pi / 2 - ((3 * np.pi) / 2 - self.cfg.wind_angle)

    def _run_pole_calculations(self):
        cfg = self.cfg
        poledb = self.poledb
        for study_tag in poledb.index.get_level_values('StudyPoleTag').unique():
            block = poledb.xs(study_tag, level='StudyPoleTag', drop_level=False)
            ref = block.xs(study_tag, level='PoleTag').iloc[0]
            dx = block['MapX'] - ref['MapX']
            dy = block['MapY'] - ref['MapY']
            poledb.loc[block.index, 'NormX'] = dx
            poledb.loc[block.index, 'NormY'] = dy
            poledb.loc[block.index, 'Span'] = np.hypot(dx, dy)
            poledb.loc[block.index, 'NormAngle'] = np.arctan2(dy, dx)

        for idx, pole in poledb.iterrows():
            if not _is_positive(pole['GradeHeight']):
                poledb.at[idx, 'GradeHeight'] = self._default_grade_height(pole)
                pole = poledb.loc[idx]
            species = pole['PoleSpecies']
            height = pole['PoleHeight']
            species_data = self.wooddata.xs(species, level='Species', drop_level=True)
            depth_row = species_data.loc[species_data['Height'] == height]
            if depth_row.empty:
                raise PoleCalcError(
                    f'No wood pole data for species {species!r} at height {height}')
            depth_index = depth_row.index[0]
            class_value = pole['PoleClass']
            pclass = int(class_value.lstrip('H')) if isinstance(class_value, str) \
                else int(class_value)
            pole_ct = self.wooddata.at[(species, 0), pclass]
            pole_cb = self.wooddata.at[(species, depth_index), pclass]
            depth = self.wooddata.at[(species, depth_index), 'Depth']
            pole_cg = (((height - ((height * 0.1) + 2)) * (pole_cb - pole_ct))
                       / (height - depth)) + pole_ct
            grade_height = pole['GradeHeight']
            mrn = _MOMENT_CONSTANT * _WOOD_FIBER_STRESS * pole_cg ** 3
            mbn = (cfg.wind_load * ((2 * pole_ct + pole_cg) / (72 * np.pi))
                   * grade_height ** 2)
            mb = mbn * cfg.wind_overload
            poledb.at[idx, 'PoleCt'] = pole_ct
            poledb.at[idx, 'PoleCb'] = pole_cb
            poledb.at[idx, 'PoleCg'] = pole_cg
            poledb.at[idx, 'Mrn'] = mrn
            poledb.at[idx, 'Mr'] = mrn * cfg.strength_factor
            poledb.at[idx, 'Mbn'] = mbn
            poledb.at[idx, 'Mb'] = mb
            poledb.at[idx, 'Mbx'] = mb * np.cos(self._windAngle_wrap())
            poledb.at[idx, 'Mby'] = mb * np.sin(self._windAngle_wrap())

    def _lookup_product(self, product_db, conductor_type, conductor_name, row_index):
        product = product_db.loc[
            (product_db.index.get_level_values(0) == conductor_type)
            & (product_db['name'] == conductor_name)]
        if product.empty:
            raise UnknownConductorError(
                f'{conductor_type}/{conductor_name} not found at {row_index}')
        return product.iloc[0]

    def _run_conductor_calculations(self, db, product_db):
        cfg = self.cfg
        if db.empty:
            return db
        for row_index, row in db.iterrows():
            product = self._lookup_product(product_db, row['ConductorType'],
                                           row['ConductorName'], row_index)
            if not _is_positive(row['Tension']):
                db.at[row_index, 'Tension'] = product['strength'] * row['DesignTension']
            pole_span = self.poledb.loc[(row_index[0], row_index[1]), 'Span']
            if isinstance(pole_span, pd.Series):
                pole_span = pole_span.iloc[0]
            if not _is_positive(row['Span']) or cfg.override_span:
                db.at[row_index, 'Span'] = pole_span
            pole_angle = self.poledb.loc[(row_index[0], row_index[1]), 'NormAngle']
            if isinstance(pole_angle, pd.Series):
                pole_angle = pole_angle.iloc[0]
            if not _is_number(row['NormAngle']) or cfg.override_angle:
                db.at[row_index, 'NormAngle'] = pole_angle

        span = db['Span']
        angle = db['NormAngle']
        height = db['Height']
        tension = db['Tension']
        diameter = pd.Series(
            [self._lookup_product(product_db, t, n, i)['diameter']
             for i, t, n in zip(db.index, db['ConductorType'], db['ConductorName'])],
            index=db.index)

        db['Mtx'] = np.cos(angle) * tension * height * cfg.tension_overload
        db['Mty'] = np.sin(angle) * tension * height * cfg.tension_overload
        db['Mcn'] = ((cfg.wind_load * (diameter + 2 * cfg.ice_thickness)) / 12) * height
        db['Mc'] = (db['Mcn'] * cfg.wind_overload
                    * np.abs(np.cos(angle - (((3 * np.pi) / 2) - cfg.wind_angle))))
        db['Mcmax'] = db['Mcn'] * cfg.wind_overload
        db['Mcmaxws'] = db['Mcmax'] * (span / 2)
        db['Mcmaxx'] = db['Mcmaxws'] * np.cos(angle + np.pi / 2)
        db['Mcmaxy'] = db['Mcmaxws'] * np.sin(angle + np.pi / 2)
        db['Mcws'] = db['Mc'] * (span / 2)
        db['Mcwsx'] = db['Mcws'] * np.cos(self._windAngle_wrap())
        db['Mcwsy'] = db['Mcws'] * np.sin(self._windAngle_wrap())
        return db

    def _aggregate_pole_moments(self):
        for db, is_comms in ((self.conddb, False), (self.commdb, True)):
            if db.empty:
                continue
            non_study = db[db.index.get_level_values('StudyPoleTag')
                           != db.index.get_level_values('PoleTag')]
            for study_tag, group in non_study.groupby(level='StudyPoleTag'):
                key = (study_tag, study_tag, 0)
                if is_comms:
                    self.poledb.at[key, 'Mtcx'] = group['Mtx'].sum(skipna=True)
                    self.poledb.at[key, 'Mtcy'] = group['Mty'].sum(skipna=True)
                    self.poledb.at[key, 'Mccwsx'] = group['Mcwsx'].sum(skipna=True)
                    self.poledb.at[key, 'Mccwsy'] = group['Mcwsy'].sum(skipna=True)
                else:
                    self.poledb.at[key, 'Mtx'] = group['Mtx'].sum(skipna=True)
                    self.poledb.at[key, 'Mty'] = group['Mty'].sum(skipna=True)
                    self.poledb.at[key, 'Mcmax'] = group['Mcmax'].sum(skipna=True)
                    self.poledb.at[key, 'Mcwsx'] = group['Mcwsx'].sum(skipna=True)
                    self.poledb.at[key, 'Mcwsy'] = group['Mcwsy'].sum(skipna=True)
        self.polecalc = self.poledb.dropna(subset=['Mtx', 'Mty'])
        non_study_mask = (self.conddb.index.get_level_values('StudyPoleTag')
                          != self.conddb.index.get_level_values('PoleTag'))
        self.condcalc = self.conddb[non_study_mask]
        if not self.commdb.empty:
            comm_mask = (self.commdb.index.get_level_values('StudyPoleTag')
                         != self.commdb.index.get_level_values('PoleTag'))
            self.commcalc = self.commdb[comm_mask]
        else:
            self.commcalc = self.commdb
        self.poleNocalc = self.poledb[self.poledb['Mtx'].isna()]

    def _calculate_guy(self, db, is_comms):
        if db.empty:
            return db
        for pole_key, pole in self.polecalc.iterrows():
            try:
                guys = db.xs((pole_key[0], pole_key[1]),
                             level=['StudyPoleTag', 'PoleTag'],
                             drop_level=False)
            except KeyError:
                continue
            mt_x, mt_y = ((pole['Mtcx'], pole['Mtcy']) if is_comms
                          else (pole['Mtx'], pole['Mty']))
            for guy_index in guys.index:
                guy = db.loc[guy_index]
                if not _is_positive(guy['GuyHeight']):
                    raise InvalidGuyDataError(f'GuyHeight invalid at {guy_index}')
                db.at[guy_index, 'Mtx'] = -mt_x / len(guys)
                db.at[guy_index, 'Mty'] = -mt_y / len(guys)
                guy = db.loc[guy_index]
                guy_type = guy['GuyType']
                if not _is_number(guy_type):
                    raise InvalidGuyDataError(f'GuyType missing at {guy_index}')
                guy_type = int(guy_type)
                if guy_type not in (1, 2, 3, 4, 5, 6):
                    raise InvalidGuyDataError(
                        f'Unknown GuyType {guy["GuyType"]!r} at {guy_index}')
                height = guy['GuyHeight']
                tension = guy['GuyTension']
                mx, my = db.at[guy_index, 'Mtx'], db.at[guy_index, 'Mty']
                if guy_type == 1:
                    if not _is_positive(tension):
                        raise InvalidGuyDataError(f'GuyTension missing at {guy_index}')
                    if not _is_number(guy['GuyX']):
                        raise InvalidGuyDataError(f'GuyX length missing at {guy_index}')
                    if not _is_number(guy['GuyY']) or abs(guy['GuyY']) >= 2 * np.pi:
                        raise InvalidGuyDataError(f'GuyY angle invalid at {guy_index}')
                    horizontal = np.arctan(guy['GuyX'] / height)
                    db.at[guy_index, 'Mtx'] = tension * height * np.sin(horizontal) * np.cos(guy['GuyY'])
                    db.at[guy_index, 'Mty'] = tension * height * np.sin(horizontal) * np.sin(guy['GuyY'])
                    db.at[guy_index, 'GuyMapX'] = pole['MapX'] + guy['GuyX']
                    db.at[guy_index, 'GuyMapY'] = pole['MapY'] + guy['GuyY']
                elif guy_type == 2:
                    if not _is_positive(tension):
                        raise InvalidGuyDataError(f'GuyTension missing at {guy_index}')
                    if not _is_number(guy['GuyX']) or not _is_number(guy['GuyY']):
                        raise InvalidGuyDataError(
                            f'Guy location missing at {guy_index}')
                    radius = np.hypot(guy['GuyX'], guy['GuyY'])
                    lead_angle = np.arctan2(guy['GuyY'], guy['GuyX'])
                    db.at[guy_index, 'Mtx'] = tension * height * np.sin(np.arctan(radius / height)) * np.cos(lead_angle)
                    db.at[guy_index, 'Mty'] = tension * height * np.sin(np.arctan(radius / height)) * np.sin(lead_angle)
                    db.at[guy_index, 'GuyMapX'] = guy['GuyX']
                    db.at[guy_index, 'GuyMapY'] = guy['GuyY']
                elif guy_type in (3, 4, 5):
                    ratio = {3: 1.0, 4: 2 / 3, 5: 1 / 2}[guy_type]
                    db.at[guy_index, 'GuyTension'] = (
                        np.hypot(mx, my) / height / np.sin(np.arctan(ratio)))
                    lead_angle = np.arctan2(my, mx)
                    db.at[guy_index, 'GuyX'] = height * ratio * np.cos(lead_angle)
                    db.at[guy_index, 'GuyY'] = height * ratio * np.sin(lead_angle)
                    db.at[guy_index, 'GuyMapX'] = pole['MapX'] + height * ratio * np.cos(lead_angle)
                    db.at[guy_index, 'GuyMapY'] = pole['MapY'] + height * ratio * np.sin(lead_angle)
                else:
                    if not _is_number(guy['GuyX']) or not _is_number(guy['GuyY']):
                        raise InvalidGuyDataError(
                            f'Overhead guy location missing at {guy_index}')
                    lead_angle = np.arctan2(guy['GuyY'], guy['GuyX'])
                    if _is_positive(tension):
                        db.at[guy_index, 'Mtx'] = tension * height * np.cos(lead_angle)
                        db.at[guy_index, 'Mty'] = tension * height * np.sin(lead_angle)
                    else:
                        db.at[guy_index, 'GuyTension'] = np.hypot(mx, my) / height
                    db.at[guy_index, 'GuyMapX'] = guy['GuyX']
                    db.at[guy_index, 'GuyMapY'] = guy['GuyY']
                gx, gy = db.at[guy_index, 'Mtx'], db.at[guy_index, 'Mty']
                if is_comms:
                    acc_x, acc_y = pole.get('Mcgx'), pole.get('Mcgy')
                    pole['Mcgx'] = gx if pd.isna(acc_x) else acc_x + gx
                    pole['Mcgy'] = gy if pd.isna(acc_y) else acc_y + gy
                    self.polecalc.at[pole_key, 'Mcgx'] = pole['Mcgx']
                    self.polecalc.at[pole_key, 'Mcgy'] = pole['Mcgy']
                else:
                    acc_x, acc_y = pole.get('Mgx'), pole.get('Mgy')
                    pole['Mgx'] = gx if pd.isna(acc_x) else acc_x + gx
                    pole['Mgy'] = gy if pd.isna(acc_y) else acc_y + gy
                    self.polecalc.at[pole_key, 'Mgx'] = pole['Mgx']
                    self.polecalc.at[pole_key, 'Mgy'] = pole['Mgy']
        return db

    def _calculate_total_moments(self):
        for pole_key, pole in self.polecalc.iterrows():
            map_x, map_y = pole['MapX'], pole['MapY']
            mgx = 0.0 if pd.isna(pole['Mgx']) else pole['Mgx']
            mgy = 0.0 if pd.isna(pole['Mgy']) else pole['Mgy']
            mcgx = 0.0 if pd.isna(pole['Mcgx']) else pole['Mcgx']
            mcgy = 0.0 if pd.isna(pole['Mcgy']) else pole['Mcgy']
            self.polecalc.at[pole_key, 'MgMapX'] = map_x + (pole['Mtx'] + mgx) / 2000
            self.polecalc.at[pole_key, 'MgMapY'] = map_y + (pole['Mty'] + mgy) / 2000
            self.polecalc.at[pole_key, 'MtMapX'] = map_x + pole['Mtx'] / 2000
            self.polecalc.at[pole_key, 'MtMapY'] = map_y + pole['Mty'] / 2000
            self.polecalc.at[pole_key, 'Mgndx'] = np.nansum(
                [pole['Mbx'], pole['Mtx'], pole['Mcwsx'], pole['Mex']])
            self.polecalc.at[pole_key, 'Mgndy'] = np.nansum(
                [pole['Mby'], pole['Mty'], pole['Mcwsy'], pole['Mey']])
            self.polecalc.at[pole_key, 'Mcgndx'] = np.nansum([pole['Mtcx'], pole['Mccwsx']])
            self.polecalc.at[pole_key, 'Mcgndy'] = np.nansum([pole['Mtcy'], pole['Mccwsy']])
            self.polecalc.at[pole_key, 'MgndMapX'] = map_x + (pole['Mgndx'] + mgx) / 2000
            self.polecalc.at[pole_key, 'MgndMapY'] = map_y + (pole['Mgndy'] + mgy) / 2000
            self.polecalc.at[pole_key, 'McgndMapX'] = map_x + (pole['Mcgndx'] + mcgx) / 2000
            self.polecalc.at[pole_key, 'McgndMapY'] = map_y + (pole['Mcgndy'] + mcgy) / 2000

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def _write_results(self, out_dir):
        out_dir.mkdir(parents=True, exist_ok=True)
        self.poleNocalc.filter(['PoleTag', 'PoleHeight', 'PoleClass',
                                'MapX', 'MapY', 'PoleSpecies']).to_csv(
            out_dir / 'poleNocalc.csv')
        self.polecalc.to_csv(out_dir / 'polecalc.csv')
        self.condcalc.to_csv(out_dir / 'condcalc.csv')
        self.guydb.to_csv(out_dir / 'guycalc.csv')
        self.cguydb.to_csv(out_dir / 'cguycalc.csv')
        self.commdb.to_csv(out_dir / 'commcalc.csv')
        if hasattr(self, 'polesummary'):
            self.polesummary.to_csv(out_dir / 'polesummary.csv')

    def _calculate_max_spans(self):
        for pole_key, pole in self.polecalc.iterrows():
            mt = np.hypot(pole['Mtx'], pole['Mty'])
            if pole['Mcmax'] == 0:
                self.polecalc.at[pole_key, 'MaxSpan'] = np.nan
                continue
            self.polecalc.at[pole_key, 'MaxSpan'] = (
                pole['Mr'] - pole['Mb'] - mt) / pole['Mcmax']

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run(self, plot_format=None):
        """Run the full calculation. If plot_format is given ('pdf' or 'png'),
        pole plots and the summary table are generated."""
        self._load_databases()
        self._prepare_poles()
        self._prepare_conductors()
        self._prepare_comms()
        self._prepare_guys(self.guydb, is_comms=False)
        self._prepare_guys(self.cguydb, is_comms=True)
        self._allocate_output_columns()
        self._run_pole_calculations()
        self.conddb = self._run_conductor_calculations(self.conddb, self.conductordb)
        self.commdb = self._run_conductor_calculations(self.commdb, self.cabledb)
        self._aggregate_pole_moments()
        self.guydb = self._calculate_guy(self.guydb, is_comms=False)
        self.cguydb = self._calculate_guy(self.cguydb, is_comms=True)
        self._calculate_total_moments()
        if plot_format:
            from .poleplotter import polePlotterClass
            plotter = polePlotterClass(self.cfg.project_name, self.cfg)
            self.polesummary = plotter.plot_poles(
                self.polecalc, self.poleNocalc, self.guydb,
                self.cfg.path / 'PolePlots', plot_format)
        self._write_results(self.cfg.path / 'PoleResults')
        return self.polecalc

    def run_max_span(self):
        """Run the full calculation and report maximum allowable spans."""
        self.run()
        self._calculate_max_spans()
        self.polecalc.to_csv(self.cfg.path / 'PoleResults' / 'polecalc.csv')
        return self.polecalc
