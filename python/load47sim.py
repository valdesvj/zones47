"""load47sim.py - run build/LOAD47.txt in the C47 simulator (c47sim.py) and write its screens (docs/LOAD47_*.png).
  frames(keys, clock)  the screens shown while LOAD47 waits for a key; c.at_steps the steps before each
  python3 python/load47sim.py"""
import os, sys
from decimal import Decimal as D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import c47sim, zone47sim as Z

PROG = os.environ.get('LOAD47_PROG') or os.path.join(ROOT, 'build', 'LOAD47.txt')
UP, LEFT, RIGHT, DOWN, BACK, FWD, TODAY, END = 53, 62, 64, 73, 52, 54, 72, 82   # 8 4 6 2 7 9 1 0


def frames(keys=(END,), clock=None, prog=PROG):
    c = c47sim.load([prog])
    c.s = [D(0)] * 4; c.pix = []; c.keys = list(keys); c.steps = 0; c.frames = Z._Frames(c)
    c.clock = Z.jd(2026, 10, 23, 14 + 47 / 60) if clock is None else clock
    try:
        c.run('LOAD47', maxsteps=10 ** 8)            # 10**8: c47sim's Date→ⅅ sets the step counter (zone47sim)
    except StopIteration:
        pass
    shots = [{(x, Z.H - 1 - y) for y, x in f if 0 <= y < Z.H and 0 <= x < Z.W} for f in c.frames]
    return shots, c


if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
    # 23 Oct 2026, the cursor off Libya; 2 x5 and 6 x15: 19.5S 63E (S Indian E, tropical); 9 x12 (+180 days)
    keys = [DOWN] * 5 + [RIGHT] * 15 + [FWD] * 12 + [END]
    shots, c = frames(keys)
    st = c.at_steps
    for fn, i, what in (('LOAD47_oct.png', 0, '23 Oct 2026, the cursor off Libya'),
                        ('LOAD47_sindian.png', 20, '2 x5, 6 x15: South Indian Ocean'),
                        ('LOAD47_apr.png', 32, '9 x12: 21 Apr 2027')):
        Z.png(os.path.join(ROOT, 'docs', fn), shots[i])
        print('docs/%-20s %s' % (fn, what))
    print('steps: start %d, a cursor move %d, a new date %d' % (st[0], st[1] - st[0], st[21] - st[20]))
