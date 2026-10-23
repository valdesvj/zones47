#!/usr/bin/env python3
"""Write docs/ZONE47_tour.gif: ZONE47 in the C47 simulator, every stop once from the start (TZ = 3, Fri 23 Oct
2026 14:47 on the clock) east around the world (key 5), 0.9 s a stop. Needs Pillow (pip install pillow).
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
    shots, c = Z.frames([Z.EAST5] * len(ZONES) + [Z.END], tz=3)
    ims = [image(s) for s in shots]
    fn = os.path.join(ROOT, 'docs', 'ZONE47_tour.gif')
    ims[0].save(fn, save_all=True, append_images=ims[1:], duration=[1800] + [900] * (len(ims) - 1),
                loop=0, optimize=True)
    print('%s: %d frames, %d bytes' % (os.path.relpath(fn, ROOT), len(ims), os.path.getsize(fn)))


if __name__ == '__main__':
    main()
