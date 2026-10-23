#!/usr/bin/env python3
"""Write docs/ZONE47_tour.gif: ZONE47 in the C47 simulator from the start (TZ = -5, Fri 23 Oct 2026 06:47 on
the clock: Colombia): key 2 to Medellin (the cities of the stop), then key 5 east around the world, every stop
once, 0.9 s a screen. Needs Pillow (pip install pillow).
  python3 tools/build_zone47.py && python3 tools/make_gif.py"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import zone47sim as Z
from zones import ZONES
from PIL import Image

SCALE, BORDER = 2, 8


def image(pix):
    w, h = Z.W * SCALE + 2 * BORDER, Z.H * SCALE + 2 * BORDER
    im = Image.new('P', (w, h), 0)
    im.putpalette(list(Z.LCD_BG) + list(Z.LCD_ON) + [0] * 762)
    px = im.load()
    for x, r in pix:
        for dy in range(SCALE):
            for dx in range(SCALE):
                px[BORDER + x * SCALE + dx, BORDER + r * SCALE + dy] = 1
    return im


def main():
    from zones import ZONES as ZS
    home = [z[0] for z in ZS].index(-5.0)
    med = [c[0] for c in ZS[home][2]].index('Medellin')
    keys = [73] * med + [Z.EAST5] * len(ZONES) + [Z.END]
    shots, c = Z.frames(keys, tz=-5, clock=Z.jd(2026, 10, 23, 6 + 47 / 60))
    ims = [image(s) for s in shots]
    fn = os.path.join(ROOT, 'docs', 'ZONE47_tour.gif')
    ims[0].save(fn, save_all=True, append_images=ims[1:], duration=[1800] + [900] * (len(ims) - 1),
                loop=0, optimize=True)
    print('%s: %d frames, %d bytes' % (os.path.relpath(fn, ROOT), len(ims), os.path.getsize(fn)))


if __name__ == '__main__':
    main()
