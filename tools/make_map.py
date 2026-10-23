#!/usr/bin/env python3
"""Write python/worldmap.py, the dot map of the world that ZONE47 draws, from a land / sea mask.

The map: 120 dot columns x 45 dot rows, 3 degrees a dot. Column j covers longitude -172.5 + 3j to -169.5 + 3j
(the map starts at the west edge of the UTC-11 zone, so each 15-degree zone is 5 dot columns and the
UTC+-12 zone, 172.5E to 172.5W, is the last 5 columns); row i covers latitude 81 - 3i down to 78 - 3i
(81N to 54S, Antarctica left out). A dot is land when at least LAND of its 6 x 6 sample points are land.

The land / sea mask: the Python package global-land-mask (pip install global-land-mask; GLOBE 1 km data,
NOAA). Only this tool needs it: python/worldmap.py is kept in the repository.
  python3 tools/make_map.py"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NCOL, NROW, STEP = 120, 45, 3
LON0, LAT0 = -172.5, 81.0
SUB = 6            # sample points per side of a dot
LAND = 0.25        # the share of land samples that makes a dot land (keeps the British Isles, Japan, NZ)


def build():
    from global_land_mask import globe
    cols = []
    for j in range(NCOL):
        bits = 0
        for i in range(NROW):
            n = 0
            for a in range(SUB):
                for b in range(SUB):
                    lon = LON0 + STEP * j + STEP * (b + 0.5) / SUB
                    lat = LAT0 - STEP * i - STEP * (a + 0.5) / SUB
                    lon = (lon + 180) % 360 - 180
                    n += bool(globe.is_land(lat, lon))
            if n >= LAND * SUB * SUB:
                bits |= 1 << i
        cols.append(bits)
    return cols


def main():
    cols = build()
    with open(os.path.join(ROOT, 'python', 'worldmap.py'), 'w') as fh:
        fh.write('"""worldmap.py - the dot map of ZONE47, written by tools/make_map.py (do not edit).\n'
                 'COLS[j]: dot column j (longitude -172.5 + 3j to -169.5 + 3j), bit i = dot row i\n'
                 '(latitude 81 - 3i to 78 - 3i), 1 = land. Land / sea from global-land-mask (GLOBE, NOAA)."""\n')
        fh.write('NCOL, NROW = %d, %d\n' % (NCOL, NROW))
        fh.write('COLS = [\n')
        for k in range(0, NCOL, 6):
            fh.write('    ' + ', '.join('0x%012x' % c for c in cols[k:k + 6]) + ',\n')
        fh.write(']\n')
    for i in range(NROW):                      # a look at it
        print(''.join('#' if cols[j] >> i & 1 else '.' for j in range(NCOL)))


if __name__ == '__main__':
    main()
