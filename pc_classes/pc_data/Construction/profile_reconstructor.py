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
# Attachment X offsets are measured from the POLE CENTERLINE (z axis):
# pole diameter never enters the coordinate data since the crossarm is a
# fixed-width member regardless of pole class. The pole outline below is
# therefore presentation-only; supply --species/--pole-class to draw the
# true diameter from the PoleData tables, otherwise a generic outline is used.
POLE_TOP_WIDTH = 8.5
POLE_LENGTH = 120.0
POLE_TAPER = 0.23
XARM_HEIGHT = 3.5
XARM_THICK = 4.625
XARM_LEN_8FT = 96.0
XARM_LEN_10FT = 120.0
CONDUCTOR_SYMBOL_R = 2.0

# Insulator assumptions from General Notes.txt (inches to conductor seat).
# The CSV Hin/Hout values already bake these heights in: e.g. 7200 A1.1
# (pin) = 4"+5" = 9, A1.1P (post) = 12; 14400 VA1.1 (pin) = 5"+5" = 10,
# VA1.1P (post) = 14. These constants are used to DRAW the hardware
# between the mounting surface and the conductor seat at Hin.
INSULATORS = {
    '7200': {'post': 12.0, 'pin': 9.0, 'spool': 1.0625},
    '14400': {'post': 14.0, 'pin': 10.0, 'spool': 1.5},
    '34500': {'post': 16.0, 'pin': 12.5, 'spool': 1.5},
    '46000': {'post': 20.0, 'pin': 12.5, 'spool': 1.5},
    '69000': {'post': 26.0, 'pin': 12.5, 'spool': 1.5},
}

def insulator_heights(csv_name):
    """Pick the insulator set for a construction table from its file name."""
    stem = os.path.basename(csv_name).replace('.csv', '')
    for key in sorted(INSULATORS, key=len, reverse=True):
        if stem.startswith(key) or key in stem:
            return INSULATORS[key]
    return INSULATORS['7200']

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '..', 'PoleData')


def parse_slots(columns):
    """Return [('Phase1', has_x, has_r), ...] plus neutral and guy info."""
    slots = []
    n = 1
    while f'Phase{n}Hin' in columns:
        slots.append(f'Phase{n}')
        n += 1
    return slots


def pole_geometry(species=None, pole_class=None, pole_height=None):
    """Return (top_width_in, length_in, taper_in_per_ft, butt_width_in).

    Uses the real PoleData circumference tables when species/class/height are
    given; otherwise falls back to the generic presentation outline. The
    conductor X/Y coordinates are unaffected: they are centerline-based.
    """
    if species and pole_class and pole_height:
        path = os.path.join(_DATA_DIR, f'{species}.csv')
        if os.path.isfile(path):
            hdr = pd.read_csv(path, header=None, nrows=1).iloc[0].tolist()
            classes = [str(c).strip("'").strip() for c in hdr[2:]]
            if str(pole_class) in classes:
                col = 2 + classes.index(str(pole_class))
                df = pd.read_csv(path, header=None, skiprows=3)
                row = df.loc[df[0] == float(pole_height)]
                if not row.empty:
                    circ = float(row.iloc[0][col])
                    if not pd.isna(circ):
                        # circumference at 6 ft from butt -> diameter there;
                        # tip circumference comes from the header row's
                        # per-class tip entry (row index 1)
                        tip = pd.read_csv(path, header=None, skiprows=1,
                                          nrows=1).iloc[0]
                        tip_circ = tip[col]
                        top_w = (float(tip_circ) / math.pi
                                 if not pd.isna(tip_circ)
                                 else POLE_TOP_WIDTH)
                        # circumference at 6ft from butt is near the butt;
                        # use it for the butt width
                        butt_w = circ / math.pi
                        return top_w, float(pole_height) * 12.0, None, butt_w
    return POLE_TOP_WIDTH, POLE_LENGTH, POLE_TAPER, None


def draw_profile(row, name, species=None, pole_class=None, pole_height=None,
                 csv_name=None):
    """Build a Drawing for one assembly row (row: pandas Series)."""
    d = Drawing()
    d.add_layer('POLE', color=7)
    d.add_layer('XARM', color=3)
    d.add_layer('CONDUCTOR', color=1)
    d.add_layer('NEUTRAL', color=2)
    d.add_layer('GUY', color=5)
    d.add_layer('DIMS', color=8)
    d.add_layer('LABELS', color=7)

    # Pole: top at y=0, drawn downward (negative y = below pole top).
    # Outline is presentation-only; attachment coordinates are centerline
    # (z-axis) based and independent of pole diameter.
    top_width, pole_len, taper, butt_width = pole_geometry(
        species, pole_class, pole_height)
    top_half = top_width / 2
    if butt_width is not None:
        butt_half = butt_width / 2
    elif taper is not None:
        butt_half = top_half + taper * (pole_len / 12.0)
    else:
        # uniform taper approximation from RUS pole dimensions
        butt_half = top_half + 0.23 * (pole_len / 12.0)
    d.add_polyline([(-top_half, 0), (-butt_half, -pole_len),
                    (butt_half, -pole_len), (top_half, 0)],
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
    ins = insulator_heights(csv_name or '')
    is_post = 'P' in str(name).replace(',', '').split(' ') or str(name).rstrip().endswith('P')
    for slot in parse_slots(row.index):
        hin = row.get(f'{slot}Hin')
        xoff = row.get(f'{slot}X')
        if pd.isna(hin):
            continue
        y = -float(hin)
        x = 0.0 if pd.isna(xoff) else float(xoff)
        # insulator hardware from mounting surface to conductor seat
        hw_h = ins['post'] if is_post else ins['pin']
        if has_xarm and abs(x) > top_half:
            mount_y = -XARM_HEIGHT          # crossarm top
        else:
            mount_y = 0.0 if not is_post else -0.0
        d.add_rect((x - 0.75, y), (x + 0.75, y + hw_h), layer='XARM')
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
        d.add_rect((x - 1.5, y), (x + 1.5, y + ins['spool']), layer='NEUTRAL')
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
    ap.add_argument('--species', default=None,
                    help='pole species file stem from PoleData (outline only)')
    ap.add_argument('--pole-class', default=None,
                    help='pole class (outline only)')
    ap.add_argument('--pole-height', default=None,
                    help='pole length in feet (outline only)')
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
            d = draw_profile(row, row['Name'], args.species, args.pole_class,
                             args.pole_height, csv_name=args.csvfile)
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
    d = draw_profile(row, row['Name'], args.species, args.pole_class,
                             args.pole_height, csv_name=args.csvfile)
    d.save_dxf(args.out)
    print('wrote', args.out)


if __name__ == '__main__':
    main()
