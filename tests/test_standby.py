#!/usr/bin/env python3
"""tests/test_standby.py - the standby check (LBL :WAKE:) of ZONE47 and LOAD47 in the C47 simulator: a key wait
with no key during which the clock moves 10 minutes (the calculator was in standby) ends the program cleanly (the
user's stack and LASTx back, the work registers cleared, the screen cleared, GRMOD 0, GRFNT 20); 5 s does not.
  python3 tools/build_zone47.py && python3 tools/build_load47.py && python3 tests/test_standby.py"""
import os, sys
from decimal import Decimal as D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import c47sim, zone47sim as Z

FAIL = []


def check(ok, what):
    print('  %s  %s' % ('ok  ' if ok else 'FAIL', what))
    if not ok:
        FAIL.append(what)


def run(prog, name, key, gap, top, tz=None):
    """name with the keys [key, standby of gap s, key, key, 0]: the simulator and the keys not used."""
    c = c47sim.load([os.path.join(ROOT, 'build', prog)])
    c.s = [D(1), D(2), D(3), D(4)]; c.lastx = D(99); c.pix = []; c.frames = []
    c.clock = Z.jd(2026, 10, 24, 14.5)
    if tz is not None:
        c.reg['TZ'] = D(str(tz))
    script = [key, None, key, key, 82]

    def count(op, x):
        if op == 'KEY?':
            k = script.pop(0) if script else 82
            if k is None:
                c.keys = []; c.keyskip = True; c.clock += gap / 86400.0
            else:
                c.keys = [k]; c.keyskip = False
    c.count = count
    c.run(name, maxsteps=10 ** 9)
    return c, script


for prog, name, key, top, tz in (('ZONE47.txt', 'ZONE47', 63, 86, 3), ('LOAD47.txt', 'LOAD47', 64, 94, None)):
    print('==', name)
    c, left = run(prog, name, key, 600, top, tz)
    check(left == [key, key, 82], 'after 10 min with no key the program ends (keys left %s)' % left)
    check(c.s == [D(1), D(2), D(3), D(4)] and c.lastx == D(99), 'the stack and LASTx back: %s' % c.s)
    left_regs = [k for k, v in c.reg.items() if k.isdigit() and 20 <= int(k) <= top and v not in (0, '', D(0))]
    check(not left_regs, 'R20-R%d cleared (%s)' % (top, left_regs))
    check(c.pix == [] and getattr(c, 'grmod', 0) == 0 and getattr(c, 'grfnt', 20) == 20, 'the screen cleared')
    c, left = run(prog, name, key, 5, top, tz)
    check(left == [], 'a gap of 5 s: it waits on and ends with 0 (keys left %s)' % left)
print('ALL OK' if not FAIL else '%d FAILED' % len(FAIL))
sys.exit(1 if FAIL else 0)
