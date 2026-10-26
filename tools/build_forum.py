#!/usr/bin/env python3
"""build_forum.py - the commented rejig sources (.p47u) of ZONE47 and LOAD47, for the forum and the PROGRAMS
folder of a C47 release (as Almanac 47's tools/build_forum.py: '@' header lines, then the steps).

  build/forum/ZONE47.p47u   from build/ZONE47.txt (the steps) and listings/ZONE47_doc.txt (the comments)
  build/forum/LOAD47.p47u   the same for LOAD47

The steps are those of build/*.txt, one by one (the same .p47 as the plain listing): indented as the source
(STRUCT, two spaces a level), the partner numbers written (DO 01 ... ENDDO 01). After the '@' metadata, the
narrative of tools/forum/NAME.txt (what the program does and how to use it, in plain words), then the source's
header as technical notes. The source's comment blocks (its REM lines) are '@' lines before the steps they stand
before; the name of a label (LBL :INIT:) is given after ';' on its LBL and on each XEQ / GTO to it. rejig compiles
neither '@' lines nor what follows ';', so the comments take no memory. A line that starts with ';' or '#' would
become a REM step on the calculator (Almanac 47 DEVELOPMENT_NOTES): there are none.

  python3 tools/build_zone47.py && python3 tools/build_load47.py && python3 tools/build_forum.py
  rejig: the .p47 of build/forum/ZONE47.p47u must be the size of the one of build/ZONE47.txt.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'forum')
AUTHOR = 'Victor Valdes'
SOURCE = 'https://github.com/valdesvj/zones47'
COL = 32                              # the column of the ';' comments (wider steps: two spaces after them)

HEAD = {
    'ZONE47': """@ Index:   World time zones on a map (IANA tz database), with daylight saving time
@ Author:  %(author)s
@ Version: %(version)s
@ Source:  %(source)s
@ Tested:  C47 simulator (python/c47sim.py): tests/test_zone47.py, every stop, its cities and the DST rules
@ Tested:  against Python's zoneinfo (the computer's tzdata) for many dates
@ Input:   the variable TZ, the offset of the calculator's clock from UT in hours (4 for UT+4, -5.5 for
@ Input:   UT-5:30); asked at the start when it is 0 or missing (R/S keeps it)
@ Output:  the map with the column of the stop highlighted; its offset, time and date; the clock (TZ) and the
@ Output:  difference; the city and its DST
@
""",
    'LOAD47': """@ Index:   Load line zones (IMO Load Lines 1966, Annex II) on a world map for a date
@ Author:  %(author)s
@ Version: %(version)s
@ Source:  %(source)s
@ Tested:  C47 simulator (python/c47sim.py): tests/test_load47.py, every area and season against the zones of
@ Tested:  tools/make_loadlines.py (46 CFR 42.30, MSC.329(90)) at many dates
@ Input:   none: the date from the clock (7 and 9 move it 15 days)
@ Output:  the map with the summer, tropical and winter zones of the date; under it the cell of the cursor:
@ Output:  latitude and longitude, its zone on the date, the area and its seasons
@
""",
}

STEP = re.compile(r'^\s*(\d+)  (.*)$')
NAMED = re.compile(r'^(\s*)(.*?)\s{4}\((\d+)\)$')            # "XEQ :INIT:    (83)", "DO    (01)"


def narrative(name):
    """tools/forum/NAME.txt: what the program does and how to use it, in plain words, as '@' lines."""
    fn = os.path.join(ROOT, 'tools', 'forum', name + '.txt')
    lines = open(fn, encoding='utf-8').read().rstrip('\n').split('\n')
    return ['@ ' + ln if ln.strip() else '@' for ln in lines] + ['@']


def parse(name):
    """The doc listing: the header comments, then [(indent, step text with names, number, comments before it)]."""
    head, steps, pending = [], [], []
    for ln in open(os.path.join(ROOT, 'listings', name + '_doc.txt'), encoding='utf-8'):
        ln = ln.rstrip('\n')
        m = STEP.match(ln)
        if m:
            body = m.group(2)
            ind = body[:len(body) - len(body.lstrip())]
            steps.append((ind, body.strip(), int(m.group(1)), pending)); pending = []
        elif ln.strip().startswith(';'):
            text = ln.strip()[1:].strip()
            (pending if steps else head).append(text)          # before step 1: the program's header
    return head, steps


def data_notes(name, plain, names):
    """Notes on the data the build writes (no REM of their own): {step index: note}. ZONE47: each stop (LBL 01-nn,
    its offset and map column), each DST rule (LBL 40 + r), each dot column of the map (XEQ :COL:). LOAD47: each
    area (LBL 01-nn, its name), each row of the cursor (LBL 50 + i), each dot column of the map."""
    notes, col = {}, 0
    byname = {v: k for k, v in names.items()}
    for k, st in enumerate(plain):
        m = re.fullmatch(r'LBL (\d\d)', st)
        if m and m.group(1) not in names:                          # a data label (XEQ IND)
            lab = int(m.group(1)); end = plain.index('RTN', k)
            body = plain[k + 1:end]
            if name == 'ZONE47' and body and body[0].startswith('"'):
                off = body[-1]; c = body[-2]
                notes[k] = 'stop %d: UTC%s%s, map column %s; its cities "rCCname/..." (r the DST rule, CC the country)' % (
                    lab, '' if off.startswith('-') else '+', off, c)
            elif name == 'ZONE47':
                notes[k] = 'DST rule %d: end hour, end code, start hour, start code + 20000 (DST on)' % (lab - 40)
            elif name == 'LOAD47' and lab < 50:
                notes[k] = 'area %d: %s' % (lab, body[0] if body and body[0].startswith('"') else '')
            elif name == 'LOAD47':
                notes[k] = 'cursor row %d: its runs (100 x last column + area) with XEQ :RUN:' % (lab - 50)
        if ':COL:' in byname and st == 'XEQ ' + byname[':COL:']:
            notes[k] = 'dot column %d (x %d)' % (col, 20 + 3 * col); col += 1
    return notes


def build(name):
    head, steps = parse(name)
    plain = open(os.path.join(ROOT, 'build', name + '.txt'), encoding='utf-8').read().split('\n')
    plain = [s for s in plain if s.strip()]
    if len(plain) != len(steps):
        raise SystemExit('%s: %d steps in build/, %d in listings/' % (name, len(plain), len(steps)))
    m = re.search(r'v(\d+\.\d+\.\d+)', head[0])
    version = m.group(1) if m else '?'
    names = {}                                                    # label number -> :NAME:
    for ind, text, n, com in steps:
        mm = NAMED.match(ind + text)
        if mm and mm.group(2).startswith('LBL :'):
            names[mm.group(3)] = mm.group(2)[4:]
    out = [(HEAD[name] % dict(author=AUTHOR, version=version, source=SOURCE)).rstrip('\n')]
    data = data_notes(name, plain, names)
    out += narrative(name)
    out += ['@ ---- Technical notes (from the commented source) ----']
    out += ['@ ' + h if h else '@' for h in head] + ['@', '']
    for k, ((ind, text, n, com), step) in enumerate(zip(steps, plain)):
        if ';' in step or step.lstrip().startswith(('#', '@')):
            raise SystemExit('%s step %d: %r would not survive rejig' % (name, n, step))
        if com:                                                  # the source's comment block: '@' lines (not compiled)
            if com[0].startswith('----') and out[-1] != '':
                out.append('@')
            out += ['@ ' + ind + c if c else '@' for c in com]
        note = ''
        mm = re.fullmatch(r'(LBL|XEQ|GTO) (\d\d)', step)
        if mm and mm.group(2) in names:
            note = names[mm.group(2)] if mm.group(1) == 'LBL' else '-> ' + names[mm.group(2)]
        if k in data:
            note = (note + '  ' if note else '') + data[k]
        line = ind + step
        if note:
            line = line.ljust(COL) + '; ' + note if len(line) < COL else line + '  ; ' + note
        out.append(line)
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, name + '.p47u')
    with open(fn, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(out).rstrip('\n') + '\n')
    ncom = sum(1 for ln in out if ln.startswith('@ ') or re.search(r'\s; ', ln))
    print('build/forum/%s.p47u  %d steps, %d with a comment, version %s' % (name, len(plain), ncom, version))
    return out


if __name__ == '__main__':
    for nm in sys.argv[1:] or ('ZONE47', 'LOAD47'):
        build(nm)
