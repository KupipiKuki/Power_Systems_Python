# -*- coding: utf-8 -*-
"""
Plotting and summary reporting for pole loading analyses.

Separated from the calculation engine so results can be consumed
programmatically without matplotlib.
"""

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_PLOT_FORMATS = ('pdf', 'png')

_SUMMARY_COLUMNS = ['Pole Strength', 'Utility Moment', 'Utility Guyed Moment',
                   'Total Utility Moment', 'Communications Moment',
                   'Communications Guyed Moment', 'Total Communications Moment',
                   'Overall Pole Moment', 'Guy Required']


class polePlotterClass:

    def __init__(self, project_name, config):
        self.project_name = project_name
        self.cfg = config

    def pole_summary(self, pole):
        """Per-pole summary moments for the results table."""
        resist = pole['Mr']
        mgx = 0.0 if pd.isna(pole['Mgx']) else pole['Mgx']
        mgy = 0.0 if pd.isna(pole['Mgy']) else pole['Mgy']
        mcgx = 0.0 if pd.isna(pole['Mcgx']) else pole['Mcgx']
        mcgy = 0.0 if pd.isna(pole['Mcgy']) else pole['Mcgy']
        gnd_moment = np.hypot(pole['Mgndx'] + mgx, pole['Mgndy'] + mgy) \
            * self.cfg.deflection_factor
        bgnd = np.hypot(pole['Mgndx'], pole['Mgndy'])
        guy_moment = np.hypot(mgx, mgy)
        cgnd_moment = np.hypot(pole['Mcgndx'] + mcgx, pole['Mcgndy'] + mcgy) \
            * self.cfg.deflection_factor
        bcgnd = np.hypot(pole['Mcgndx'], pole['Mcgndy'])
        cguy_moment = np.hypot(mcgx, mcgy)
        total = np.hypot(pole['Mgndx'] + mgx + pole['Mcgndx'] + mcgx,
                         pole['Mgndy'] + mgy + pole['Mcgndy'] + mcgy)
        return {
            'Pole Strength': round(resist, 1),
            'Utility Moment': bgnd,
            'Utility Guyed Moment': guy_moment,
            'Total Utility Moment': gnd_moment,
            'Communications Moment': bcgnd,
            'Communications Guyed Moment': cguy_moment,
            'Total Communications Moment': cgnd_moment,
            'Overall Pole Moment': total,
            'Guy Required': total / resist > 0.8,
        }

    def build_summary(self, polecalc):
        """Build the summary table for all study poles."""
        return pd.DataFrame.from_dict(
            {pole_key[0]: self.pole_summary(pole)
             for pole_key, pole in polecalc.iterrows()},
            orient='index', columns=_SUMMARY_COLUMNS)

    def plot_poles(self, polecalc, poleNocalc, guydb, out_dir, file_format):
        """Generate one plot per study pole plus the summary table."""
        if file_format not in _PLOT_FORMATS:
            raise ValueError(
                f'plot format must be one of {_PLOT_FORMATS}, got {file_format!r}')
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        summary_rows = {}
        for pole_key, pole in polecalc.iterrows():
            summary = self.pole_summary(pole)
            summary_rows[pole_key[0]] = summary
            self._plot_single_pole(pole_key, pole, summary,
                                   polecalc, poleNocalc, guydb,
                                   out_dir, file_format)
        self.polesummary = pd.DataFrame.from_dict(summary_rows, orient='index',
                                                  columns=_SUMMARY_COLUMNS)
        return self.polesummary

    def _plot_single_pole(self, pole_key, pole, summary,
                          polecalc, poleNocalc, guydb, out_dir, file_format):
        cfg = self.cfg
        fig_width, fig_height = 8.5, 11
        span = np.nanmax(poleNocalc.xs(pole_key[0], level='StudyPoleTag')['Span'])
        xlim = np.ceil(span / 100) * 100
        ylim = np.ceil((fig_height / fig_width) * span / 100) * 100
        fig = plt.figure(figsize=(fig_width, fig_height), dpi=80,
                         facecolor='w', edgecolor='k')
        ax = fig.add_subplot(111)
        study = polecalc.xs(pole_key[0], level='StudyPoleTag')
        poles = poleNocalc.xs(pole_key[0], level='StudyPoleTag')
        study.plot(kind='scatter', x='MapX', y='MapY', color='g', ax=ax,
                   marker='o', s=250, label='Study Pole')
        poles.plot(kind='scatter', x='MapX', y='MapY', color='c', ax=ax,
                   marker='o', label='Poles')
        study.plot(kind='scatter', x='MtMapX', y='MtMapY', color='r', ax=ax,
                   marker='x', s=100, label='Conductor Tension Moment')
        study.plot(kind='scatter', x='McgndMapX', y='McgndMapY', color='m', ax=ax,
                   marker='x', s=100, label='Communications Ground Moment')
        study.plot(kind='scatter', x='MgndMapX', y='MgndMapY', color='orange',
                   ax=ax, marker='x', s=100,
                   label='Ground Moment\nNot Including Communications')
        try:
            guydb.xs(pole_key[0], level='StudyPoleTag').plot(
                kind='scatter', x='GuyMapX', y='GuyMapY', color='k', ax=ax,
                marker='+', s=100, label='Guy Location')
        except KeyError:
            pass
        ax.set_xlim(pole['MapX'] - xlim, pole['MapX'] + xlim)
        ax.set_ylim(pole['MapY'] - ylim, pole['MapY'] + ylim)
        ax.arrow(0.7, 0.3,
                 0.05 * np.cos(cfg.wind_angle + np.pi),
                 0.05 * np.sin(cfg.wind_angle + np.pi),
                 head_width=0.01, head_length=0.01, transform=ax.transAxes,
                 label='Wind')
        text_y = 0.315 if cfg.wind_angle < np.pi else 0.285
        ax.text(0.7, text_y, 'Wind', transform=ax.transAxes,
                horizontalalignment='center')
        ax.legend(loc=0)
        ax.set_title(f'{self.project_name} Pole {pole_key[0]}')
        ax.set_xlabel('Map X Coordinates')
        ax.set_ylabel('Map Y Coordinates')
        fig.text(0.1, 0.985, f"Resisting Moment: {pole['Mr']:.1f}", fontsize=8)
        fig.text(0.1, 0.97,
                 f"Ground Moment: {summary['Total Utility Moment']:.1f}", fontsize=8)
        fig.text(0.1, 0.955,
                 f"Communications Ground Moment: "
                 f"{summary['Total Communications Moment']:.1f}", fontsize=8)
        fig.text(0.1, 0.91,
                 f"Pole : {pole['PoleHeight']}-{pole['PoleClass']}, "
                 f"{pole['PoleSpecies']}, {pole['GradeHeight']} Feet Above Grade",
                 fontsize=8)
        fig.text(0.6, 0.985, f'Design Tension: {cfg.design_tension}, '
                             f'Tension Overload: {cfg.tension_overload}', fontsize=8)
        fig.text(0.6, 0.97, f'Wind Load: {cfg.wind_load}, '
                            f'Wind Overload: {cfg.wind_overload}', fontsize=8)
        fig.text(0.6, 0.955, f'Strength Factor: {cfg.strength_factor}', fontsize=8)
        fig.text(0.6, 0.94, f'Ice Thickness: {cfg.ice_thickness}', fontsize=8)
        fig.text(0.6, 0.925, f'Deflection Factor: {cfg.deflection_factor}', fontsize=8)
        plt.savefig(out_dir / f'{pole_key[0]}.{file_format}',
                   facecolor='w', edgecolor='w', bbox_inches='tight',
                   pad_inches=0.5)
        plt.close()
