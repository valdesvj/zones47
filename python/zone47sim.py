"""zone47sim.py - run build/ZONE47.txt in the C47 simulator (c47sim.py, from Almanac 47) and turn its
screens into pictures.
  frames(keys, clock, tz)  the screens shown while ZONE47 waits for a key, as sets of (x, row), row 0 = top
  png(fn, pix)             a PNG of one screen (LCD colours, 3 pixels per C47 pixel)
  python3 python/zone47sim.py   writes the screens in docs/ and prints the step counts"""
import os, struct, sys, zlib
from decimal import Decimal as D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import c47sim

PROG = os.environ.get('ZONE47_PROG') or os.path.join(ROOT, 'build', 'ZONE47.txt')
W, H = 400, 240
LCD_BG, LCD_ON = (199, 205, 186), (34, 38, 30)
WEST, EAST5, EAST6, END = 62, 63, 64, 82          # the keys 4 5 6 0
REG = dict(TZ='30', UT='31', K='32', TEXT='34')


def jd(y, m, d, h=0.0):
    """The JD of a calendar date and time (hours), for the simulator's clock (the local time)."""
    a = (14 - m) // 12; yy = y + 4800 - a; mm = m + 12 * a - 3
    n = d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045
    return n - 0.5 + h / 24


class _Frames(list):
    def __init__(self, c): super().__init__(); self.c = c; c.at_steps = []
    def append(self, f): self.c.at_steps.append(self.c.steps); super().append(f)


def frames(keys=(EAST6, END), clock=None, tz=None, prog=PROG):
    """The screens of ZONE47 for the keys pressed, the clock (a JD of the local time) and TZ (None: no
    variable TZ). c.at_steps: the steps run before each screen."""
    c = c47sim.load([prog])
    c.s = [D(0)] * 4; c.pix = []; c.keys = list(keys); c.steps = 0; c.frames = _Frames(c)
    c.clock = jd(2026, 10, 23, 14 + 47 / 60) if clock is None else clock
    if tz is not None:
        c.reg['TZ'] = D(str(tz))
    try:
        # maxsteps 10**8: c47sim's clock (Date→ⅅ) sets the step counter n to the day number (2.46 million);
        # to fix in Almanac 47 (another name there), then copy c47sim.py here
        c.run('ZONE47', maxsteps=10 ** 8)
    except StopIteration:
        pass
    shots = [{(x, H - 1 - y) for y, x in f if 0 <= y < H and 0 <= x < W} for f in c.frames]
    return shots, c


def png(fn, pix, scale=3, border=12):
    w, h = W * scale + 2 * border, H * scale + 2 * border
    buf = bytearray(bytes(LCD_BG) * (w * h))
    dot = bytes(LCD_ON) * scale
    for x, r in pix:
        for dy in range(scale):
            o = ((border + r * scale + dy) * w + border + x * scale) * 3
            buf[o:o + len(dot)] = dot
    raw = b''.join(b'\x00' + bytes(buf[y * w * 3:(y + 1) * w * 3]) for y in range(h))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(fn, 'wb') as fh:
        fh.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                 + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'docs'), exist_ok=True)
    # TZ = 3, Fri 23 Oct 2026 14:47 on the clock (stop 18, Moscow); 6 x5 (+5:30 Kolkata), 4 x14 (-5 New
    # York), 4 x8 (-12 at sea), 4 (+14 Kiritimati: around), 5 (-12 again)
    keys = [EAST6] * 5 + [WEST] * 22 + [WEST, EAST5] + [END]
    shots, c = frames(keys, tz=3)
    st = c.at_steps
    for fn, i, what in (('ZONE47_start.png', 0, 'the start, TZ = 3: Moscow'),
                        ('ZONE47_kolkata.png', 5, '6 x5: +5:30 Kolkata'),
                        ('ZONE47_newyork.png', 19, '4 x14: -5 New York'),
                        ('ZONE47_atsea.png', 27, '4 x8: -12 at sea'),
                        ('ZONE47_kiritimati.png', 28, '4: +14 Kiritimati (around)')):
        png(os.path.join(ROOT, 'docs', fn), shots[i])
        print('docs/%-20s %s' % (fn, what))
    print('steps: start %d, a move %d' % (st[0], st[1] - st[0]))
