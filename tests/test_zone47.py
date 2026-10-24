#!/usr/bin/env python3
"""tests/test_zone47.py - ZONE47 in the C47 simulator (python/c47sim.py): every stop both ways and around for 8 TZ
values, every city of every stop (keys 2 and 8) in January and July, each DST rule's city 30 minutes before and
after its changes in 2026 and 2030: the header and city texts against Python's zoneinfo (IANA); the
screen the same after a full turn; TZ kept; the user's stack kept; the work registers cleared.
  python3 tools/build_zone47.py && python3 tests/test_zone47.py"""
import os, sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
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


def city(i, j):
    return ZONES[i - 1][2][j - 1]


def now_offset(i, j, ut):
    """The offset of city j of stop i now: zoneinfo (IANA), DST included; a city whose DST follows no rule:
    its standard offset (what ZONE47 shows)."""
    std = ZONES[i - 1][0]; c = city(i, j)
    if c[4] in (None, 'irregular'):
        return std
    return ut.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(c[2])).utcoffset().total_seconds() / 3600


def expect(i, tz, local, j=1):
    """The texts of stop i, city j, TZ, the clock's local time (a datetime): 6 header texts, the city line.
    The times from Python's zoneinfo (IANA), DST included."""
    std = ZONES[i - 1][0]; nm, cc, tzid, dst, rule = city(i, j); n = len(ZONES[i - 1][2])
    ut = local - timedelta(hours=tz); off = now_offset(i, j, ut); z = ut + timedelta(hours=off)
    d = off - tz
    line = '%s %s  %d/%d' % (nm, cc or '  ', j, n)
    if rule == 'irregular':
        line += '  DST varies'
    elif rule:
        line += ('  summer %s h' % offs(dst)) if off != std else ('  winter, DST %s h' % offs(dst))
    return ['UTC' + (offs(off) if off else ''), ' %02d:%02d' % (z.hour, z.minute),
            '%s %d %s' % (DAYS[z.weekday()], z.day, z.strftime('%b')),
            'TZ ' + offs(tz), ' %02d:%02d' % (local.hour, local.minute),
            'same time' if d == 0 else ' %s h' % offs(d), line]


def nearest(tz, local):
    """The home stop: the smaller of |standard - TZ| and |offset now - TZ| + 0.01 (DST on) of its first city."""
    ut = local - timedelta(hours=tz); ds = []
    for i in range(1, len(ZONES) + 1):
        now = now_offset(i, 1, ut); std = ZONES[i - 1][0]
        ds.append(min(abs(std - tz), abs(now - tz) + (now - std) / 100))
    return 1 + ds.index(min(ds))


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
                      (14, datetime(2026, 6, 30, 12, 0)), (-5, datetime(2026, 7, 4, 4, 4))):
        c, texts = run(keys + [Z.END], tz=tz, local=local)
        t = tz or 0
        want = [expect(i, t, local) for i in walk(nearest(t, local), keys)]
        hs = headers(texts)
        check(len(hs) == len(want), 'TZ %s: %d redraws, %d wanted' % (tz, len(hs), len(want)))
        for a, b in zip(hs, want):
            check(a == b, 'TZ %s: %s / %s' % (tz, a, b))
        shots = c.frames
        check(set(shots[0]) == set(shots[n]), 'TZ %s: around east, the same screen' % tz)
        check(set(shots[n + 1]) == set(shots[2 * n + 1]), 'TZ %s: around west, the same screen' % tz)
        check(str(c.reg.get('TZ')) == str(D(str(tz)) if tz is not None else D(0)), 'TZ kept: %s' % c.reg.get('TZ'))

    # every city of every stop: 2 through all of them and once around, 8 back twice (January and July)
    for local in (datetime(2026, 1, 15, 10, 0), datetime(2026, 7, 15, 10, 0)):
        tz = 0
        i0 = nearest(tz, local)
        for i in range(1, n + 1):
            m = len(ZONES[i - 1][2])
            ks = [Z.EAST6] * ((i - i0) % n) + [73] * m + [53, 53]
            c, texts = run(ks + [Z.END], tz=tz, local=local)
            hs = headers(texts)[(i - i0) % n:]
            js = [1] + [j % m + 1 for j in range(1, m + 1)] + [m, m - 1 if m > 1 else 1]
            want = [expect(i, tz, local, j) for j in js]
            check(hs == want, 'stop %d cities %s: %s' % (i, local.date(), [(a, b) for a, b in zip(hs, want) if a != b][:2]))

    # DST: each rule's city half an hour before and after each change in 2026 and 2030
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    from make_zones import transitions
    seen = set()
    for i, z in enumerate(ZONES, 1):
        for j, cy in enumerate(z[2], 1):
            if not cy[4] or cy[4] == 'irregular' or cy[4] in seen:
                continue
            seen.add(cy[4])
            for y in (2026, 2030):
                for u, on in transitions(cy[2], y):
                    for dm in (-30, 30):
                        utc = (u + timedelta(minutes=dm)).replace(tzinfo=None)
                        local = utc + timedelta(hours=1.5)            # TZ 1.5: a clock with no DST
                        k = [Z.EAST6] * ((i - nearest(1.5, local)) % n) + [73] * (j - 1)
                        c, texts = run(k + [Z.END], tz=1.5, local=local)
                        hs = headers(texts)
                        check(hs and hs[-1] == expect(i, 1.5, local, j), '%s %s %+d min: %s / %s' % (
                            cy[0], u, dm, hs[-1] if hs else None, expect(i, 1.5, local, j)))
    print('DST rules checked: %d' % len(seen))

    # the user's stack kept, R20-R86 cleared, GRMOD 0 and GRFNT 20 at the end
    c, texts = run([Z.EAST6, Z.END], tz=3, stack=(1, 2, 3, 4))
    check([int(v) for v in c.s[:4]] == [1, 2, 3, 4], 'stack: %s' % c.s[:4])
    left = [k for k, v in c.reg.items() if k.isdigit() and 20 <= int(k) <= 86 and v not in (0, '', D(0))]
    check(not left, 'registers left: %s' % left)
    check(getattr(c, 'grmod', 0) == 0 and getattr(c, 'grfnt', 20) == 20, 'GRMOD 0, GRFNT 20 at the end')
    print('%d stops, %d cities (tzdata %s), ' % (n, sum(len(z[2]) for z in ZONES), TZDATA)
          + ('ALL OK' if not FAIL else '%d FAILED' % len(FAIL)))
    return not FAIL


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
