# -*- coding: utf-8 -*-
"""
Profile reconstructor for RUS pole-top assembly data files.

Recreates the pole-top profile drawing from a construction CSV row using
minicad_dxf, so the row's Hin/Hout/X/GuyH values can be visually verified
against the source RUS drawing (UEP bulletins).

The vertical datum is the POLE TOP (y = 0); positive y is DOWN the pole
in the CSV sense (Hin values are inches BELOW pole top), so CSV values
are drawn as negative y (standard drawing orientation, pole top at the
top of the sheet).

Assumed dimensions (inches, from RUS standard framing):
  - Pole top width: 8.5 (circumference 27 in), butt taper 0.23 in/ft
  - Crossarm: 8-0" x 3-5/8" x 4-5/8" unless 10-foot variant (x suffix 41+)
  - Crossarm mounting: top of crossarm is 3 inches below pole top
    unless the row's Hin for a crossarm phase says otherwise
  - Pin insulator height above crossarm: 8 inches to conductor seat
  - Post insulator height above pole: per drawing (12 in default)
  - Spool bracket: conductor 3 in below bracket bolt hole

Usage:
    python profile_reconstructor.py 7200_C.csv "C1.11,C2.21" -o out.dxf
    python profile_reconstructor.py --list 7200_C.csv
    python profile_reconstructor.py --all 7200_A.csv -o outdir/
"""

import argparse
import math
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minicad_dxf import Drawing  # noqa: E402

SCALE = 1.0
POLE_TOP_WIDTH = 8.5
POLE_LENGTH = 120.0
POLE_TAPER = 0.23
XARM_HEIGHT = 3.5
XARM_THICK = 4.625
XARM_LEN_8FT = 96.0
XARM_LEN_10FT = 120.0
PIN_HEIGHT = 8.0
CONDUCTOR_SYMBOL_R = 2.0


def parse_slots(columns):
    """Return [('Phase1', has_x, has_r), ...] plus neutral and guy info."""
    slots = []
    n = 1
    while f'Phase{n}Hin' in columns:
        slots.append(f'Phase{n}')
        n += 1
    return slots


def draw_profile(row, name):
    """Build a Drawing for one assembly row (row: pandas Series)."""
    d = Drawing()
    d.add_layer('POLE', color=7)
    d.add_layer('XARM', color=3)
    d.add_layer('CONDUCTOR', color=1)
    d.add_layer('NEUTRAL', color=2)
    d.add_layer('GUY', color=5)
    d.add_layer('DIMS', color=8)
    d.add_layer('LABELS', color=7)

    # Pole: top at y=0, drawn downward (negative y = below pole top)
    top_half = POLE_TOP_WIDTH / 2
    butt_half = top_half + POLE_TAPER * (POLE_LENGTH / 12.0)
    d.add_polyline([(-top_half, 0), (-butt_half, -POLE_LENGTH),
                    (butt_half, -POLE_LENGTH), (top_half, 0)],
                   closed=False, layer='POLE')
    # pole top cap
    d.add_line((-top_half, 0), (top_half, 0), layer='POLE')

    slot_types = []

    # Crossarm if any crossarm-phase Hin is set (typ. phases with X != 0)
    has_xarm = any(_num(row.get(f'{s}X')) for s in parse_slots(row.index))
    xarm_len = XARM_LEN_8FT
    if has_xarm:
        # crossarm top 3 in below pole top; thickness 4.625
        d.add_rect((-xarm_len / 2, -XARM_HEIGHT - XARM_THICK),
                   (xarm_len / 2, -XARM_HEIGHT), layer='XARM')

    # Phases
    for slot in parse_slots(row.index):
        hin = row.get(f'{slot}Hin')
        xoff = row.get(f'{slot}X')
        if pd.isna(hin):
            continue
        y = -float(hin)
        x = 0.0 if pd.isna(xoff) else float(xoff)
        d.add_circle((x, y), CONDUCTOR_SYMBOL_R, layer='CONDUCTOR')
        d.add_text((x + 3, y - 1), slot, height=2.5, align='left',
                   layer='LABELS')
        # dimension from pole top
        d.add_dim((x, 0), (x, y), (x + 15, y / 2), dtype='vertical',
                  layer='DIMS')
        slot_types.append(slot)

    # Neutral
    nhin = row.get('NeutralHin')
    if not pd.isna(nhin):
        y = -float(nhin)
        nx = row.get('NeutralX')
        x = 0.0 if pd.isna(nx) else float(nx)
        d.add_circle((x, y), CONDUCTOR_SYMBOL_R, layer='NEUTRAL')
        d.add_text((x + 3, y - 1), 'N', height=2.5, align='left',
                   layer='LABELS')
        d.add_dim((x, 0), (x, y), (x + 15, y / 2), dtype='vertical',
                  layer='DIMS')

    # Guys
    for i in range(1, 7):
        gh = row.get(f'GuyH{i}')
        if not pd.isna(gh):
            y = -float(gh)
            d.add_line((0, y), (30, y - 60), layer='GUY')
            d.add_text((31, y - 30), f'GUY{i}', height=2.5, align='left',
                       layer='LABELS')
            d.add_dim((0, 0), (0, y), (-20, y / 2), dtype='vertical',
                      layer='DIMS')

    # Title
    d.add_text((-xarm_len / 2 if has_xarm else -40, 12), str(name),
               height=6, align='left', layer='LABELS')
    return d


def _num(v):
    try:
        f = float(v)
        return f
    except (TypeError, ValueError):
        return 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('csvfile', help='construction CSV (e.g. 7200_C.csv)')
    ap.add_argument('name', nargs='?', help='assembly Name column value')
    ap.add_argument('-o', '--out', default=None, help='output .dxf path')
    ap.add_argument('--list', action='store_true', help='list names')
    ap.add_argument('--all', action='store_true',
                    help='render every row to out dir')
    args = ap.parse_args()

    df = pd.read_csv(args.csvfile)
    here = os.path.dirname(os.path.abspath(args.csvfile))

    if args.list:
        for n in df['Name']:
            print(n)
        return

    if args.all:
        outdir = args.out or os.path.join(here, 'profiles')
        os.makedirs(outdir, exist_ok=True)
        for _, row in df.iterrows():
            d = draw_profile(row, row['Name'])
            safe = str(row['Name']).replace('/', '_').replace(',', '_')
            path = os.path.join(outdir, f'{safe}.dxf')
            d.save_dxf(path)
            print('wrote', path)
        return

    if not args.name or args.out is None:
        ap.error('provide assembly name and -o output path '
                 '(or --list / --all)')

    match = df.loc[df['Name'] == args.name]
    if match.empty:
        match = df.loc[df['Name'].str.contains(args.name, na=False,
                                               regex=False)]
    if match.empty:
        print(f'Assembly {args.name!r} not found in {args.csvfile}')
        raise SystemExit(1)
    row = match.iloc[0]
    d = draw_profile(row, row['Name'])
    d.save_dxf(args.out)
    print('wrote', args.out)


if __name__ == '__main__':
    main()
