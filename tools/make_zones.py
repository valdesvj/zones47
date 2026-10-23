#!/usr/bin/env python3
"""Write python/zones.py, the official time zones ZONE47 steps through, from the IANA tz database (tzdata) of
the computer: on Linux /usr/share/zoneinfo (zone1970.tab, tzdata.zi for the version), read with Python's
zoneinfo. To update after a new tzdata: install it (Arch: pacman -Syu tzdata; Debian/Ubuntu: apt upgrade
tzdata), then
  python3 tools/make_zones.py && python3 tools/build_zone47.py && python3 tests/test_zone47.py

One stop per standard offset (UTC + hours, daylight saving time left out) of the zones in zone1970.tab, plus
-12 (Etc/GMT+12: no one lives there, the nautical zone 172.5W-180). For each offset:
  offset   the standard offset in hours (5.75 = +5:45)
  column   the 15-degree column of the map that is highlighted (0 = UTC-11 ... 23 = UTC+-12): whole hours
           -12..12 their own column; the others (+5:30, +13, -9:30 ...) the column of the city's longitude
  name     a city of the offset (PREFER below, or the first zone of the offset in zone1970.tab)
  dst      the daylight saving of that city in YEAR (hours; 0 = none)
  rule     its DST rule, or None: (start, end), each (month, n, weekday, hour): the n-th (1-4, 5 = the last)
           weekday (0 Sunday) of the month, at that hour of the city's standard time. Found from the
           transitions of zoneinfo in RULE_YEARS; the tool stops if they do not follow one such rule.
  zones    how many zones of zone1970.tab have this standard offset, and how many of them use DST
Standard offset = the UTC offset minus the DST of zoneinfo, on the 15th of each month of YEAR."""
import os, datetime as dt, zoneinfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZI = os.environ.get('TZDIR', '/usr/share/zoneinfo')
YEAR = 2026
RULE_YEARS = range(2026, 2036)
# the city shown for an offset (a zone of zone1970.tab); offsets not listed: the first zone of the offset
PREFER = {-11: 'Pacific/Pago_Pago', -10: 'Pacific/Honolulu', -9: 'America/Anchorage', -8: 'America/Los_Angeles',
          -7: 'America/Denver', -6: 'America/Chicago', -5: 'America/New_York', -4: 'America/Halifax',
          -3: 'America/Sao_Paulo', -2: 'America/Noronha', -1: 'Atlantic/Azores', 0: 'Europe/London',
          1: 'Europe/Paris', 2: 'Africa/Cairo', 3: 'Europe/Moscow', 4: 'Asia/Dubai', 5: 'Asia/Karachi',
          5.5: 'Asia/Kolkata', 6: 'Asia/Dhaka', 7: 'Asia/Bangkok', 8: 'Asia/Shanghai', 9: 'Asia/Tokyo',
          9.5: 'Australia/Adelaide', 10: 'Australia/Sydney', 11: 'Pacific/Noumea', 12: 'Pacific/Auckland',
          13: 'Pacific/Tongatapu'}


def version():
    try:
        for ln in open(os.path.join(ZI, 'tzdata.zi')):
            if ln.startswith('# version'):
                return ln.split()[2]
    except OSError:
        pass
    return 'unknown'


def coord(s):
    """+DDMM+DDDMM or +DDMMSS+DDDMMSS -> lat, lon in degrees."""
    i = max(s.rfind('+'), s.rfind('-'))
    def deg(t, n):
        sg = -1 if t[0] == '-' else 1; t = t[1:]
        d, m = int(t[:n]), int(t[n:n + 2]); sec = int(t[n + 2:] or 0)
        return sg * (d + m / 60 + sec / 3600)
    return deg(s[:i], 2), deg(s[i:], 3)


def name(tzid):
    return tzid.split('/')[-1].replace('_', ' ')


def transitions(tzid, year):
    """The DST transitions of a zone in a year: (utc datetime, dst after) in order, to the minute."""
    z = zoneinfo.ZoneInfo(tzid); utc = dt.timezone.utc
    t = dt.datetime(year, 1, 1, tzinfo=utc); end = dt.datetime(year + 1, 1, 1, tzinfo=utc)
    def dst(u): return u.astimezone(z).dst()
    out, prev = [], dst(t)
    while t < end:
        n = t + dt.timedelta(hours=1)
        if dst(n) != prev:
            lo, hi = t, n                                   # to the minute
            while hi - lo > dt.timedelta(minutes=1):
                mid = lo + (hi - lo) / 2
                mid = mid.replace(second=0, microsecond=0)
                if mid == lo: break
                if dst(mid) == prev: lo = mid
                else: hi = mid
            out.append((hi, dst(n) != dt.timedelta(0))); prev = dst(n)
        t = n
    return out


def rule(tzid, std):
    """The DST rule of a zone (see the docstring), or None when it has no DST in RULE_YEARS."""
    import calendar
    found = {True: [], False: []}
    for y in RULE_YEARS:
        tr = transitions(tzid, y)
        if not tr:
            return None
        for u, on in tr:
            loc = u + dt.timedelta(hours=std)                  # the city's standard time
            ml = calendar.monthrange(loc.year, loc.month)[1]
            wd = (loc.weekday() + 1) % 7                       # 0 Sunday
            ns = {(loc.day - 1) // 7 + 1} | ({5} if loc.day + 7 > ml else set())
            found[on].append((loc.month, ns, wd, loc.hour + loc.minute / 60))
    out = []
    for on in (True, False):
        r = found[on]
        if len({(m, w, h) for m, _, w, h in r}) != 1:
            raise SystemExit('%s: DST %s not one rule: %s' % (tzid, 'start' if on else 'end', r))
        ns = set.intersection(*[n for _, n, _, _ in r])
        if not ns:
            raise SystemExit('%s: no n-th weekday fits every year: %s' % (tzid, r))
        m, _, w, h = r[0]
        out.append((m, 5 if 5 in ns else min(ns), w, h))
    return tuple(out)


def build():
    groups = {}
    for ln in open(os.path.join(ZI, 'zone1970.tab'), encoding='utf-8'):
        if ln.startswith('#') or not ln.strip():
            continue
        f = ln.rstrip('\n').split('\t')
        tzid = f[2]; z = zoneinfo.ZoneInfo(tzid); std, offs = None, set()
        for m in range(1, 13):
            d = dt.datetime(YEAR, m, 15, 12, tzinfo=z)
            o = d.utcoffset().total_seconds() / 3600; s = o - d.dst().total_seconds() / 3600
            offs.add(o); std = s if std is None else std
        groups.setdefault(std, []).append((tzid, coord(f[1]), max(offs) - min(offs)))
    out = [(-12.0, 23, 'at sea', 0.0, 0, 0, 'Etc/GMT+12', None)]
    for off in sorted(groups):
        zs = groups[off]
        pick = next((z for z in zs if z[0] == PREFER.get(off)), zs[0])
        tzid, (lat, lon), dst = pick
        if off == int(off) and -12 <= off <= 12:
            col = int(off + 11) % 24
        else:
            col = int((lon + 172.5) % 360 // 15)
        out.append((off, col, name(tzid), dst, len(zs), sum(1 for z in zs if z[2]), tzid,
                    rule(tzid, off) if dst else None))
    return out


def main():
    zs = build()
    with open(os.path.join(ROOT, 'python', 'zones.py'), 'w', encoding='utf-8') as fh:
        fh.write('"""zones.py - the time zones of ZONE47, written by tools/make_zones.py (do not edit).\n'
                 'Source: the IANA tz database (https://www.iana.org/time-zones), tzdata %s, zone1970.tab,\n'
                 'standard offsets of %d. ZONES: (offset h, map column, city, DST h, zones, zones with DST, tz id,\n'
                 'DST rule: ((month, n, weekday, standard-time hour) start, (...) end) or None; n 5 = the last, weekday 0 Sunday)."""\n'
                 % (version(), YEAR))
        fh.write('TZDATA = %r\nYEAR = %d\nZONES = [\n' % (version(), YEAR))
        for z in zs:
            fh.write('    %r,\n' % (z,))
        fh.write(']\n')
    for z in zs:
        print('%+6.2f col %2d  %-14s DST %.1f  %2d zones, %2d with DST  %-20s %s' % z)
    print('tzdata %s: %d stops' % (version(), len(zs)))


if __name__ == '__main__':
    main()
