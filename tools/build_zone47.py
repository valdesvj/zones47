#!/usr/bin/env python3
"""Build the ZONE47 files from the commented source programs_rem/ZONE47.txt.

One program, ZONE47. Its labels are written by name in the source (LBL :HEAD:, XEQ :HEAD:, 1-7 letters
and digits); the build gives each name a local number 00-99 (listings/ZONE47_labels.txt says which is
which). The control flow is written with the C47 STRUCT commands (AN0007), indented, without numbers: the
build checks the structures as the firmware's VALID does and numbers them (IF 01 ...), as Elements 47.
Two parts are written by the build (the source keeps only their marker line):
  REM ==== MAP     the dot map, from python/worldmap.py: per dot column the three band patterns (rows
                   151, 106, 61 up; bit 3m and 3m + 1 = the dot m of the band, from the bottom) and XEQ :COL:
  REM ==== LABELS  the zone numbers under the map (even zones, tinyFont, centred on their column)
  REM ==== NSTOPS  the number of stops (python/zones.py, from the IANA tz database: tools/make_zones.py)
  REM ==== STOPS   the stops, LBL 01-nn: the city, DST, the column, the offset (XEQ IND 32)
Files written:
  programs/ZONE47.txt        the program without REM lines, numeric labels (to convert with rejig)
  build/ZONE47.txt           the calculator file (the same steps)
  listings/ZONE47_doc.txt    numbered steps with the comments and the label names
  build/forum/ZONE47.p47u    the rejig source with the comments after ';' (tools/build_forum.py)
  listings/ZONE47_labels.txt the local labels: name, number, what it does
The functions structures(), resolve(), estimate() come from Elements 47 (tools/build_elem47.py).
  python3 tools/build_zone47.py"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))

NAME = 'ZONE47'
NAMED_RE = re.compile(r'(LBL|GTO|XEQ) :([A-Za-z0-9]{1,7}):$')
OPENERS = {'IF': 'ENDIF', 'DO': 'ENDDO', 'REPEAT': 'UNTIL'}
STRUCT = ('IF', 'ELSE', 'ENDIF', 'DO', 'WHILE', 'ENDDO', 'REPEAT', 'UNTIL')
DM42_MAX = 10           # STRUCT_MAX_NUMBER and STRUCT_MAX_NESTING of the original DM42 (R47, DM42n: 255, 63)
NOT_USED = ('FOR', 'NEXT', 'FORₓ', 'NEXTₓ', 'FOR𝑦ˣ', 'FORᵀᴼᴾ')
BAND = 15               # dot rows per band (45 pixel rows, one AGRAPH word)


def is_test(step):
    """A step that leaves a test answer (the firmware's structTest list: the comparisons, the flag and type
    tests ending with ?, the counters, KEY?)."""
    op = step.split(' ')[0]
    return op.endswith('?') or op in ('DSE', 'ISG', 'DSZ', 'ISZ', 'DSL', 'ISE')


def structures(steps):
    """The steps with the partner numbers of the STRUCT commands, as VALID numbers them (manage.c /
    structured.c structWalkProgram): per program, IF, DO and REPEAT in three series from 1, in the order
    the openers appear; ELSE, WHILE, ENDDO, ENDIF, UNTIL take the number of their opener. Stops on what
    VALID refuses (a closer without its opener or of another kind, a structure left open at END or across
    a routine (RTN then LBL), a DO without WHILE, an IF / WHILE / UNTIL without a test just before it) and
    on a test before ELSE, ENDIF, DO, ENDDO, REPEAT or UNTIL: the firmware never skips those (structured.c
    structNoLegacySkip)."""
    out, open_, n = [], [], {}

    def fail(i, msg):
        raise SystemExit('STRUCT, step %d (%s): %s' % (i + 1, steps[i], msg))
    for i, s in enumerate(steps):
        op = s.split(' ')[0]
        prev = steps[i - 1] if i else ''
        if op in NOT_USED:
            fail(i, 'FOR / NEXT not used here (they take the start, end and step off the stack)')
        if op in STRUCT and s != op:
            fail(i, 'written without a number: the build numbers the structures')
        if op in ('IF', 'WHILE', 'UNTIL') and not is_test(prev):
            fail(i, 'no test just before it')
        if op in ('ELSE', 'ENDIF', 'DO', 'ENDDO', 'REPEAT', 'UNTIL') and is_test(prev) and not op == 'UNTIL':
            fail(i, 'a test before it: the firmware never skips a structure step')
        if s == 'END' or (s.startswith('LBL ') and prev == 'RTN'):
            if open_:
                fail(i, 'structure %s %02d still open' % tuple(open_[-1][:2]))
            if s == 'END':
                n = {}
        if op in OPENERS:
            n[op] = n.get(op, 0) + 1
            # the original DM42 (c43 structured.h, OLD_HW): 10 numbers of each kind per program, 10 levels
            if n[op] > DM42_MAX or len(open_) >= DM42_MAX:
                fail(i, 'past the original DM42 limit: %d %s a program, %d levels (structured.h, OLD_HW)'
                     % (DM42_MAX, op, DM42_MAX))
            open_.append([op, n[op], False])
            out.append('%s %02d' % (op, n[op]))
            continue
        if op in STRUCT:
            want = {'ELSE': 'IF', 'ENDIF': 'IF', 'WHILE': 'DO', 'ENDDO': 'DO', 'UNTIL': 'REPEAT'}[op]
            if not open_ or open_[-1][0] != want:
                fail(i, 'no %s open here' % want)
            top = open_[-1]
            if op in ('ELSE', 'WHILE'):
                if top[2]:
                    fail(i, 'a second %s' % op)
                top[2] = True
            if op == 'ENDDO' and not top[2]:
                fail(i, 'a DO without WHILE')
            if op in ('ENDIF', 'ENDDO', 'UNTIL'):
                open_.pop()
            out.append('%s %02d' % (op, top[1]))
            continue
        out.append(s)
    if open_:
        raise SystemExit('STRUCT: %s %02d still open at the end' % tuple(open_[-1][:2]))
    return out


def estimate(steps):
    """Estimated .p47 bytes of a program: 2.3 bytes per command, 2 + its characters per number and
    per binary number, 2 + its UTF-8 bytes per text. Calibrated on Almanac 47's MOON47 (4 836 bytes) and
    NAVFULL (24 160 bytes), within 3 % of both; rejig gives the real size."""
    b = 0.0
    for s in steps:
        if s.startswith('"'):
            b += 2 + len(s.encode('utf-8')) - 2
        elif re.fullmatch(r'-?[\d.]+(E-?\d+)?|[01]+#2', s):
            b += 2 + len(s)
        elif NAMED_RE.match(s):
            b += 3 + len(s.split(':')[1])      # command, 249, length, the name (bytes of the test program)
        else:
            b += 2.3
    return int(round(b))


def resolve(steps):
    """The steps with each named label replaced by a free local number (the fallback file), and the
    numbers: the numbers 00-99 not taken by a numeric label of the first program (the other programs
    have their own local labels), in order. Stops on a name defined twice, a name used but not defined,
    more labels than 00-99."""
    defs = [m.group(2) for s in steps for m in [NAMED_RE.match(s)] if m and m.group(1) == 'LBL']
    dup = sorted({d for d in defs if defs.count(d) > 1})
    if dup:
        raise SystemExit('named labels defined twice: %s' % ', '.join(dup))
    used = {m.group(2) for s in steps for m in [NAMED_RE.match(s)] if m}
    if used - set(defs):
        raise SystemExit('named labels used but not defined: %s' % ', '.join(sorted(used - set(defs))))
    bad = [s for s in steps if re.match(r'(LBL|GTO|XEQ) :', s) and not NAMED_RE.match(s)]
    if bad:
        raise SystemExit('a named label is 1-7 letters or digits between colons: %s' % bad[:3])
    first = steps[:steps.index('END') + 1] if 'END' in steps else steps
    taken = {int(m.group(1)) for s in first for m in [re.fullmatch(r'LBL (\d\d)', s)] if m}
    free = [n for n in range(100) if n not in taken]
    if len(defs) > len(free):
        raise SystemExit('%d named labels, only %d local numbers free' % (len(defs), len(free)))
    num = dict(zip(defs, free))
    return [NAMED_RE.sub(lambda m: '%s %02d' % (m.group(1), num[m.group(2)]), s) for s in steps], num


def programs(steps):
    """The programs of a list of steps (each ends with END)."""
    out, cur = [], []
    for s in steps:
        cur.append(s)
        if s == 'END':
            out.append(cur); cur = []
    return out


def source_steps(lines):
    """The steps of the source lines: no REM, no empty lines, the indentation off."""
    return [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith('REM')]


def band_words(col):
    """The three AGRAPH words of a dot column (bit i of col = dot row i from the top): bands of rows 151,
    106, 61 up (top, middle, bottom); dot i of the 45 at rows 194 - 3i and 193 - 3i."""
    out = []
    for b in range(3):                       # 0 top (dots 0-14), 1 middle, 2 bottom
        w = 0
        for i in range(BAND * b, BAND * (b + 1)):
            if col >> i & 1:
                m = BAND * (b + 1) - 1 - i     # from the bottom of the band
                w |= 3 << (3 * m)
        out.append(w)
    return out


def map_steps():
    from worldmap import COLS
    out = []
    for c in COLS:
        out += [str(w) for w in band_words(c)] + ['XEQ :COL:']
    return out


def label_steps():
    from tinyfont import TINY
    from stdfont import code
    out = []
    for k in range(-10, 13, 2):
        t = ('+' if k > 0 else '') + str(k)
        w = sum(sum(TINY[code(ch)][:3]) for ch in t)
        x = 26 + 15 * ((k + 11) % 24) - w // 2
        out += ['"%s"' % t, '46', str(x), 'ATEXT Z']
    return out


def num(v):
    """A number as the program writes it: 5.75, -3.5, 12, 0."""
    return ('%.2f' % v).rstrip('0').rstrip('.') if v != int(v) else str(int(v))


MAXSTR = 196            # the longest text the C47 keeps (Elements 47, tests/calc/LTEST.txt)
LETTERS = '-ABCDEFGHIJKLMNOPQRSTUVWXYZ*'      # the rule letters (R81 in ZONE47): - none, * irregular


def rules():
    """The DST rules of the cities, each once, in order: r = 1, 2 ... (LBL 40 + r, letter LETTERS[r])."""
    from zones import ZONES
    out = []
    for z in ZONES:
        for c in z[2]:
            if c[4] and c[4] != 'irregular' and c[4] not in out:
                out.append(c[4])
    return out


def code(t):
    """A transition (month, n, weekday, hour) -> the code 100 month + 10 n + weekday."""
    return 100 * t[0] + 10 * t[1] + t[2]


def entries(cities):
    """The city entries of a stop: rule letter, country code (2), name."""
    rs = rules()
    out = []
    for nm, cc, tz, dst, r in cities:
        let = '*' if r == 'irregular' else LETTERS[rs.index(r) + 1] if r else '-'
        out.append(let + (cc or '  ')[:2] + nm)
    return out


def parts(ents):
    """The entries joined by "/" in at most 3 texts of MAXSTR characters, and the number of entries in each."""
    out, cur = [], []
    for e in ents:
        if cur and len('/'.join(cur + [e])) > MAXSTR:
            out.append(cur); cur = []
        cur.append(e)
    out.append(cur)
    if len(out) > 3:
        raise SystemExit('a stop needs %d texts: more than R72-R74' % len(out))
    return out


def stop_steps():
    """The stops (python/zones.py): LBL nn, the city texts STO 72-74 and the numbers STO 75-77, the column,
    the offset, RTN; then the rules LBL 40 + r: the end hour, the end code, the start hour, the start code +
    20000 x DST, RTN."""
    from zones import ZONES
    rs = rules()
    if len(ZONES) >= 40 or len(rs) > 26:
        raise SystemExit('%d stops (LBL 01-39) and %d rules (LBL 41-66)' % (len(ZONES), len(rs)))
    out = []
    for i, (off, col, cities) in enumerate(ZONES, 1):
        ps = parts(entries(cities))
        out.append('LBL %02d' % i)
        for k, p in enumerate(ps):
            out += ['"%s"' % '/'.join(p), 'STO %d' % (72 + k)]
        n1 = len(ps[0]); n2 = n1 + (len(ps[1]) if len(ps) > 1 else 0)
        out += [str(n1), 'STO 75', str(n2), 'STO 76', str(len(cities)), 'STO 77', str(col), num(off), 'RTN']
    for r, (st, en) in enumerate(rs, 1):
        dst = next(c[3] for z in ZONES for c in z[2] if c[4] == (st, en))
        out += ['LBL %02d' % (40 + r), num(en[3]), str(code(en)), num(st[3]),
                str(code(st) + int(round(20000 * dst))), 'RTN']
    return out


def expand(lines):
    from zones import ZONES
    out = []
    for ln in lines:
        out.append(ln)
        if ln.startswith('REM ==== MAP'):
            out += map_steps()
        elif ln.startswith('REM ==== LABELS'):
            out += label_steps()
        elif ln.startswith('REM ==== NSTOPS'):
            out.append(str(len(ZONES)))
    k = next(i for i, ln in enumerate(out) if ln.startswith('REM ==== STOPS'))
    while out[k + 1].startswith('REM'):
        k += 1
    out[k + 1:k + 1] = stop_steps()
    return out


def labels_text(lines, num):
    out = ['ZONE47 local labels: name (programs_rem/ZONE47.txt), number (build/ZONE47.txt), what it does', '']
    for i, ln in enumerate(lines):
        m = NAMED_RE.match(ln)
        if m and m.group(1) == 'LBL':
            j = i
            while j > 0 and lines[j - 1].startswith('REM'):
                j -= 1
            note = lines[j][3:].strip(' -') if j < i else ''
            note = re.sub(r'^(LBL )?:%s:\s*' % m.group(2), '', note)
            out.append(':%s:%s %02d  %s' % (m.group(2), ' ' * (8 - len(m.group(2))), num[m.group(2)], note[:90]))
    return '\n'.join(out) + '\n'


def build():
    src = os.path.join(ROOT, 'programs_rem', NAME + '.txt')
    lines = expand([ln.rstrip() for ln in open(src, encoding='utf-8')])
    steps = source_steps(lines)
    numeric, num = resolve(steps)
    numeric = structures(numeric)
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
    plain = '\n'.join(numeric) + '\n'
    for d in ('programs', 'build', 'listings'):
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    for d in ('programs', 'build'):
        with open(os.path.join(ROOT, d, NAME + '.txt'), 'w', encoding='utf-8') as fh:
            fh.write(plain)
    with open(os.path.join(ROOT, 'listings', NAME + '_doc.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(listing) + '\n')
    with open(os.path.join(ROOT, 'listings', NAME + '_labels.txt'), 'w', encoding='utf-8') as fh:
        fh.write(labels_text(lines, num))
    return numeric


if __name__ == '__main__':
    st = build()
    txt = [s for s in st if s.startswith('"')]
    print('%s %5d steps, %2d local labels, longest text %d, about %d bytes (.p47, estimated)' % (
        NAME, len(st), sum(1 for s in st if re.match(r'LBL \d\d', s)), max(len(s) - 2 for s in txt), estimate(st)))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_forum
    build_forum.build(NAME)                                   # build/forum/ZONE47.p47u, the commented rejig source
