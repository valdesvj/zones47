#!/usr/bin/env python3
"""tests/test_zone47.py - ZONE47 in the C47 simulator (python/c47sim.py): every stop both ways and around, the
texts of the header and the city line against Python's datetime and python/zones.py, the screen the same after
a full turn, TZ (none, whole, half hours, +13, +14, -12, -9:45), the user's stack kept, the work registers cleared.
  python3 tools/build_zone47.py && python3 tests/test_zone47.py"""
import os, sys
from datetime import datetime, timedelta
from decimal import Decimal as D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import c47sim, zone47sim as Z
from zones import ZONES, TZDATA

DAYS = 'Mon Tue Wed Thu Fri Sat Sun'.split()
FAIL = []


def check(ok, what):
    if not ok:
        FAIL.append(what); print('FAIL', what)


def offs(o):
    """The offset as ZONE47 writes it: +3, -5:30."""
    s = '-' if o < 0 else '+'; o = abs(o); h = int(o); m = int(round((o - h) * 60))
    return s + str(h) + (':%02d' % m if m else '')


def expect(i, tz, local):
    """The header texts of stop i (1..), TZ, the clock's local time (a datetime): 6 header texts, the city line."""
    off, col, city, dst = ZONES[i - 1][:4]
    ut = local - timedelta(hours=tz); z = ut + timedelta(hours=off)
    d = off - tz
    return ['UTC' + (offs(off) if off else ''), ' %02d:%02d' % (z.hour, z.minute),
            '%s %d %s' % (DAYS[z.weekday()], z.day, z.strftime('%b')),
            'TZ ' + offs(tz), ' %02d:%02d' % (local.hour, local.minute),
            'same time' if d == 0 else ' %s h' % offs(d),
            city + ('   DST %s h in summer' % offs(dst) if dst else '')]


def nearest(tz):
    best = min(abs(z[0] - tz) for z in ZONES)
    return 1 + next(i for i, z in enumerate(ZONES) if abs(z[0] - tz) == best)


c47sim_atext = type(c47sim.load([Z.PROG])).atext


def run(keys, tz=None, local=datetime(2026, 10, 23, 14, 47), stack=None):
    texts = []

    def hook(self, text):
        texts.append((getattr(self, 'grfnt', 20), str(text))); return c47sim_atext(self, text)
    cls = type(c47sim.load([Z.PROG]))
    cls.atext = hook
    try:
        clock = Z.jd(local.year, local.month, local.day, local.hour + local.minute / 60 + 1e-7)
        c = c47sim.load([Z.PROG])
        c.s = [D(v) for v in (stack or (0, 0, 0, 0))]; c.pix = []; c.keys = list(keys); c.steps = 0
        c.frames = Z._Frames(c); c.clock = clock
        if tz is not None:
            c.reg['TZ'] = D(str(tz))
        try:
            c.run('ZONE47', maxsteps=10 ** 8)
        except StopIteration:
            pass
    finally:
        cls.atext = c47sim_atext
    return c, texts


def headers(texts):
    """The texts of each redraw: 8 GRFNT 21 texts (6 header, the line of spaces, the city line)."""
    big = [t for f, t in texts if f == 21]
    return [big[i:i + 6] + [big[i + 7]] for i in range(0, len(big) - 7, 8)]


def walk(i, keys):
    out = [i]
    for k in keys:
        i = (i - 2) % len(ZONES) + 1 if k == Z.WEST else i % len(ZONES) + 1
        out.append(i)
    return out


def main():
    n = len(ZONES)
    keys = [Z.EAST6] * (n + 1) + [Z.WEST] * (n + 1) + [Z.EAST5]
    for tz, local in ((3, datetime(2026, 10, 23, 14, 47)), (None, datetime(2026, 12, 31, 23, 59)),
                      (5.5, datetime(2026, 1, 1, 0, 5)), (-3.5, datetime(2028, 2, 29, 22, 30)),
                      (13, datetime(2027, 1, 1, 0, 30)), (-12, datetime(2026, 3, 1, 0, 0)),
                      (14, datetime(2026, 6, 30, 12, 0)), (-9.75, datetime(2026, 7, 4, 4, 4))):
        c, texts = run(keys + [Z.END], tz=tz, local=local)
        t = tz or 0
        want = [expect(i, t, local) for i in walk(nearest(t), keys)]
        hs = headers(texts)
        check(len(hs) == len(want), 'TZ %s: %d redraws, %d wanted' % (tz, len(hs), len(want)))
        for a, b in zip(hs, want):
            check(a == b, 'TZ %s: %s / %s' % (tz, a, b))
        shots = c.frames
        check(set(shots[0]) == set(shots[n]), 'TZ %s: around east, the same screen' % tz)
        check(set(shots[n + 1]) == set(shots[2 * n + 1]), 'TZ %s: around west, the same screen' % tz)
        check(str(c.reg.get('TZ')) == str(D(str(tz)) if tz is not None else D(0)), 'TZ kept: %s' % c.reg.get('TZ'))

    # the user's stack kept, R20-R49 cleared, GRMOD 0 and GRFNT 20 at the end
    c, texts = run([Z.EAST6, Z.END], tz=3, stack=(1, 2, 3, 4))
    check([int(v) for v in c.s[:4]] == [1, 2, 3, 4], 'stack: %s' % c.s[:4])
    left = [k for k, v in c.reg.items() if k.isdigit() and 20 <= int(k) <= 49 and v not in (0, '', D(0))]
    check(not left, 'registers left: %s' % left)
    check(getattr(c, 'grmod', 0) == 0 and getattr(c, 'grfnt', 20) == 20, 'GRMOD 0, GRFNT 20 at the end')
    print('%d stops (tzdata %s), ' % (n, TZDATA) + ('ALL OK' if not FAIL else '%d FAILED' % len(FAIL)))
    return not FAIL


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
