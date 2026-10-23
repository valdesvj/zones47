#!/usr/bin/env python3
"""Build the LOAD47 files from the commented source programs_rem/LOAD47.txt, as tools/build_zone47.py builds
ZONE47 (named labels, STRUCT numbers, listings; its functions). The build fills:
  REM ==== MAP     the dot map (python/worldmap.py), as ZONE47
  REM ==== NAREAS  the number of areas (python/loadzones.py)
  REM ==== AREAS   the areas, LBL 01-nn: the name STO 72, the season text STO 73, the zone outside the
                   seasons STO 74 (0 summer, 1 tropical, 2 winter), up to two seasons (start MMDD, end MMDD,
                   zone) STO 75-80 (0 when none), XEQ :ZNOW:, then each rectangle 10000000 c0 + 10000 c1 +
                   (see above)
Files: programs/LOAD47.txt, build/LOAD47.txt, listings/LOAD47_doc.txt, listings/LOAD47_labels.txt.
  python3 tools/make_loadlines.py && python3 tools/build_load47.py"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import build_zone47 as B

NAME = 'LOAD47'
ZONE = {'S': 0, 'T': 1, 'W': 2}
WORD = {'S': 'Summer', 'T': 'Tropical', 'W': 'Winter'}
MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()


def day(mmdd):
    return '%d %s' % (mmdd % 100, MONTHS[mmdd // 100 - 1])


def season_text(base, seas):
    """'Tropical 1 Nov-15 Jul, else Summer', 'Tropical all year'."""
    if not seas:
        return '%s all year' % WORD[base]
    parts = ', '.join('%s-%s' % (day(s), day(e)) for s, e, z in seas)
    return '%s %s, else %s' % (WORD[seas[0][2]], parts, WORD[base])


def area_steps():
    from loadzones import AREAS
    if len(AREAS) > 49:
        raise SystemExit('%d areas: LBL 01-39 only' % len(AREAS))
    out = []
    for k, (nm, base, seas, rs, pc) in enumerate(AREAS, 1):
        if len(seas) > 2 or len({z for _, _, z in seas}) > 1:
            raise SystemExit('%s: at most two seasons of one zone' % nm)
        txt = season_text(base, seas)
        if len(txt) > B.MAXSTR:
            raise SystemExit('season text too long: %s' % txt)
        out += ['LBL %02d' % k, '"%s"' % nm, 'STO 72', '"%s"' % txt, 'STO 73', str(ZONE[base]), 'STO 74']
        sv = [v for s, e, z in seas for v in (s, e, ZONE[z])] + [0] * (6 - 3 * len(seas))
        for r, v in enumerate(sv):
            out += [str(v), 'STO %d' % (75 + r)]
        out += ['XEQ :ZNOW:', 'RCL 90', 'X=0?', 'RTN']
        for w, c0, n, b in pc:
            out += [str(w), str(n), str(151 - 45 * b), str(20 + 3 * c0), 'XEQ :PC:']
        out.append('RTN')
    from loadzones import RUNS
    for i, r in enumerate(RUNS):
        out.append('LBL %02d' % (50 + i))
        for last, a in r:
            out += [str(100 * last + a), 'XEQ :RUN:']
        out.append('RTN')
    return out


def expand(lines):
    from loadzones import AREAS
    out = []
    for ln in lines:
        out.append(ln)
        if ln.startswith('REM ==== MAP'):
            out += B.map_steps()
        elif ln.startswith('REM ==== NAREAS'):
            out.append(str(len(AREAS)))
    k = next(i for i, ln in enumerate(out) if ln.startswith('REM ==== AREAS'))
    while out[k + 1].startswith('REM'):
        k += 1
    out[k + 1:k + 1] = area_steps()
    return out


def build():
    src = os.path.join(ROOT, 'programs_rem', NAME + '.txt')
    lines = expand([ln.rstrip() for ln in open(src, encoding='utf-8')])
    steps = B.source_steps(lines)
    numeric, num = B.resolve(steps)
    numeric = B.structures(numeric)
    if [s for s in steps if s.startswith('LBL "')] != ['LBL "%s"' % NAME] or steps.count('END') != 1:
        raise SystemExit('one program, %s' % NAME)
    listing, n = [], 0
    for ln in lines:
        if not ln.strip():
            continue
        ind = ln[:len(ln) - len(ln.lstrip())]
        if ln.lstrip().startswith('REM'):
            listing.append('      ' + ind + '; ' + ln.lstrip()[3:].strip())
        else:
            extra = '' if numeric[n] == steps[n] else '    (%s)' % numeric[n].split(' ', 1)[1]
            listing.append('%4d  %s' % (n + 1, ind + steps[n] + extra))
            n += 1
    for d in ('programs', 'build', 'listings'):
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    for d in ('programs', 'build'):
        with open(os.path.join(ROOT, d, NAME + '.txt'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(numeric) + '\n')
    with open(os.path.join(ROOT, 'listings', NAME + '_doc.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(listing) + '\n')
    lab = B.labels_text(lines, num).replace('ZONE47', NAME)
    with open(os.path.join(ROOT, 'listings', NAME + '_labels.txt'), 'w', encoding='utf-8') as fh:
        fh.write(lab)
    return numeric


if __name__ == '__main__':
    st = build()
    txt = [s for s in st if s.startswith('"')]
    print('%s %5d steps, %2d local labels, longest text %d, about %d bytes (.p47, estimated); IF %d, DO %d' % (
        NAME, len(st), sum(1 for s in st if re.match(r'LBL \d\d', s)), max(len(s) - 2 for s in txt),
        B.estimate(st), sum(1 for s in st if s.startswith('IF ')), sum(1 for s in st if s.startswith('DO '))))
