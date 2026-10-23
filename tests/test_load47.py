#!/usr/bin/env python3
"""tests/test_load47.py - LOAD47 in the C47 simulator against python/loadzones.py (tools/make_loadlines.py):
on dates across the year (each a season change of some area, the day before and the day itself), every sea cell
of the map drawn in its zone (tropical: the dot's upper left pixel only; winter: upper left and lower right;
summer: none), the land cells full; the cursor texts (date, position, zone and area, seasons) at cells of every
area; the user's stack kept and R20-R92 cleared.
  python3 tools/make_loadlines.py && python3 tools/build_load47.py && python3 tests/test_load47.py"""
import os, sys
from datetime import date, timedelta
from decimal import Decimal as D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import load47sim as L, zone47sim as Z, c47sim
from loadzones import AREAS, GRID
from worldmap import COLS
from build_load47 import season_text

FAIL = []
DAYS = 'Mon Tue Wed Thu Fri Sat Sun'.split()


def check(ok, what):
    if not ok:
        FAIL.append(what); print('FAIL', what)


def zone(k, d):
    """The zone of area k (0 = the summer zones) on the date d: 'S', 'T' or 'W'."""
    if k == 0:
        return 'S'
    nm, base, seas = AREAS[k - 1][:3]
    md = d.month * 100 + d.day
    for s, e, z in seas:
        if (s <= md <= e) if s <= e else (md >= s or md <= e):
            return z
    return base


def cells_ok(pix, d, cursor):
    """The pixels of every cell against its zone on d. pix: set of (row, x), row 0 = bottom."""
    bad = []
    for i in range(45):
        for j in range(120):
            if (i, j) == cursor:
                continue
            x, top = 20 + 3 * j, 194 - 3 * i
            got = ((top, x) in pix, (top, x + 1) in pix, (top - 1, x) in pix, (top - 1, x + 1) in pix)
            if COLS[j] >> i & 1:
                want = (True, True, True, True)
            else:
                z = zone(GRID[i][j], d)
                want = (z != 'S', False, False, z == 'W')
            if got != want:
                bad.append((i, j, got, want))
    return bad


def jd(d):
    return Z.jd(d.year, d.month, d.day, 12.0)


def run(keys, d, stack=None):
    c = c47sim.load([L.PROG])
    c.s = [D(v) for v in (stack or (0, 0, 0, 0))]; c.pix = []; c.keys = list(keys); c.steps = 0
    c.frames = Z._Frames(c); c.clock = jd(d)
    texts = []
    cls = type(c)
    orig = cls.atext
    cls.atext = lambda self, t: (texts.append((getattr(self, 'grfnt', 20), str(t))), orig(self, t))[1]
    try:
        c.run('LOAD47', maxsteps=10 ** 8)
    except StopIteration:
        pass
    finally:
        cls.atext = orig
    return c, texts


def latlon(i, j):
    lat = 79.5 - 3 * i; lon = (-171 + 3 * j + 180) % 360 - 180
    return ' %d.5%s%d%s' % (abs(int(lat)), 'N ' if lat >= 0 else 'S ', abs(lon), 'E' if lon >= 0 else 'W')


def main():
    # the dates: every season start and end of every area, the day before and the day itself (2027)
    ds = set()
    for nm, base, seas, rs, pc in AREAS:
        for s, e, z in seas:
            for md in (s, e):
                d = date(2027, md // 100, md % 100)
                ds |= {d, d + timedelta(days=1)}
    ds = sorted(ds)
    for d in ds:
        c, texts = run([L.END], d)
        bad = cells_ok(set(c.frames[0]), d, (15, 63))
        check(not bad, '%s: %d cells wrong %s' % (d, len(bad), bad[:3]))
    print('%d dates, every cell' % len(ds))

    # the cursor: one cell of each area (and a summer cell), its texts, on two dates; the cursor moves from
    # (15, 63) by keys 2 / 8 and 6 / 4
    for d in (date(2026, 1, 20), date(2026, 7, 20)):
        for k in range(0, len(AREAS) + 1):
            cs = [(i, j) for i in range(45) for j in range(120) if GRID[i][j] == k and not COLS[j] >> i & 1]
            i, j = cs[len(cs) // 2]
            keys = [L.DOWN if i > 15 else L.UP] * abs(i - 15) + [L.RIGHT if j > 63 else L.LEFT] * abs(j - 63)
            c, texts = run(keys + [L.END], d)
            big = [t for f, t in texts if f == 21]
            z = zone(k, d)
            zn = {'S': 'SUMMER', 'T': 'TROPICAL', 'W': 'WINTER'}[z]
            want = ['%s %d %s %d' % (DAYS[d.weekday()], d.day, d.strftime('%b'), d.year), latlon(i, j),
                    'SUMMER zone' if k == 0 else '%s - %s' % (zn, AREAS[k - 1][0]),
                    'Summer all year' if k == 0 else season_text(AREAS[k - 1][1], AREAS[k - 1][2])]
            got = [big[-5], big[-4], big[-3], big[-1]]
            check(got == want, '%s area %d cell %s: %s / %s' % (d, k, (i, j), got, want))
            bad = cells_ok(set(c.frames[-1]), d, (i, j))
            check(not bad, '%s cursor %s: cells %s' % (d, (i, j), bad[:2]))
    print('%d areas: the cursor texts' % len(AREAS))

    # 9 x 24 (a year on), 7 x 24 (back), 1 (today): the same screen as the start
    d = date(2026, 10, 23)
    c, texts = run([L.FWD] * 24 + [L.BACK] * 24 + [L.TODAY, L.END], d)
    check(set(c.frames[0]) == set(c.frames[48]) == set(c.frames[49]), 'a year on and back: the same screen')

    c, texts = run([L.RIGHT, L.END], d, stack=(1, 2, 3, 4))
    check([int(v) for v in c.s[:4]] == [1, 2, 3, 4], 'stack: %s' % c.s[:4])
    left = [k for k, v in c.reg.items() if k.isdigit() and 20 <= int(k) <= 92 and v not in (0, '', D(0))]
    check(not left, 'registers left: %s' % left)
    check(getattr(c, 'grmod', 0) == 0 and getattr(c, 'grfnt', 20) == 20, 'GRMOD 0, GRFNT 20 at the end')
    print('ALL OK' if not FAIL else '%d FAILED' % len(FAIL))
    return not FAIL


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
