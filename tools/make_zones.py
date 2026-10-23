#!/usr/bin/env python3
"""Write python/zones.py, the official time zones ZONE47 steps through, from the IANA tz database (tzdata) of
the computer: on Linux /usr/share/zoneinfo (zone1970.tab, tzdata.zi for the version), read with Python's
zoneinfo. To update after a new tzdata: install it (Arch: pacman -Syu tzdata; Debian/Ubuntu: apt upgrade
tzdata), then
  python3 tools/make_zones.py && python3 tools/build_zone47.py && python3 tests/test_zone47.py

One stop per standard offset (UTC + hours, daylight saving time left out) of the zones in zone.tab, plus -12
(Etc/GMT+12: no one lives there, the nautical zone 172.5W-180). zone.tab has a line for every country (its
main zone first; several for the large countries), so every country is in its stop. For each stop:
  offset   the standard offset in hours (5.75 = +5:45)
  column   the 15-degree column of the map that is highlighted (0 = UTC-11 ... 23 = UTC+-12): whole hours
           -12..12 their own column; the others (+5:30, +13, -9:30 ...) the column of the first city's longitude
  cities   (city, country code, tz id, DST h, rule), the first one PREFER below, then by city name; one per
           country and rule (the first line of zone.tab for it), plus EXTRA cities (same zone as their tz id),
           right after the city of that zone. Antarctica (AQ) left out.
  rule     the city's DST rule, None (no DST) or 'irregular' (Casablanca, El Aaiun: their changes follow Ramadan):
           (start, end), each (month, n, weekday, hour): the n-th (1-4, 5 = the last) weekday (0 Sunday) of the
           month, then that hour of standard time (the hour may be past 24 or below 0: Chile, Israel, Nuuk).
           Found from the transitions of zoneinfo in RULE_YEARS, checked to be the same rule every year.
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
# cities that are not in the tz database, with the zone they keep (shown right after that zone's city)
EXTRA = [('Medellin', 'CO', 'America/Bogota')]


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
    """The DST rule of a zone (see the docstring), None when it has no DST in RULE_YEARS, 'irregular' when its
    changes follow no such rule. The day of a change may be taken 0, -1, +1 ... 3 days off with the hour
    moved by 24 h a day (Chile: the Sunday after the first Saturday at 0:00 = the first Saturday at 24:00)."""
    import calendar
    found = {True: [], False: []}
    for y in RULE_YEARS:
        for u, on in transitions(tzid, y):
            found[on].append(u + dt.timedelta(hours=std))         # the city's standard time
    if not found[True] and not found[False]:
        return None
    if len(found[True]) != len(RULE_YEARS) or len(found[False]) != len(RULE_YEARS):
        return 'irregular'
    out = []
    for on in (True, False):
        best = None
        for shift in (0, -1, 1, -2, 2, -3, 3):
            r = []
            for loc in found[on]:
                d = loc + dt.timedelta(days=shift)
                ml = calendar.monthrange(d.year, d.month)[1]
                wd = (d.weekday() + 1) % 7
                ns = {(d.day - 1) // 7 + 1} | ({5} if d.day + 7 > ml else set())
                r.append((d.month, ns, wd, loc.hour + loc.minute / 60 - 24 * shift))
            if len({(m, w, h) for m, _, w, h in r}) != 1:
                continue
            ns = set.intersection(*[n for _, n, _, _ in r])
            if ns:
                m, _, w, h = r[0]
                best = (m, 5 if 5 in ns else min(ns), w, h)
                break
        if best is None:
            return 'irregular'
        out.append(best)
    return tuple(out)


def std_offset(tzid):
    z = zoneinfo.ZoneInfo(tzid); std, offs = None, set()
    for m in range(1, 13):
        d = dt.datetime(YEAR, m, 15, 12, tzinfo=z)
        o = d.utcoffset().total_seconds() / 3600; s = o - d.dst().total_seconds() / 3600
        offs.add(o); std = s if std is None else std
    return std, max(offs) - min(offs)


def build():
    groups = {}
    for ln in open(os.path.join(ZI, 'zone.tab'), encoding='utf-8'):
        if ln.startswith('#') or not ln.strip():
            continue
        cc, co, tzid = ln.rstrip('\n').split('\t')[:3]
        if cc == 'AQ':
            continue
        std, dst = std_offset(tzid)
        r = rule(tzid, std) if dst else None
        g = groups.setdefault(std, [])
        if any(c[1] == cc and c[4] == r for c in g):
            continue                                   # one city per country and rule
        g.append((name(tzid), cc, tzid, dst, r, coord(co)))
    out = [(-12.0, 23, [('at sea', '', 'Etc/GMT+12', 0.0, None)])]
    for off in sorted(groups):
        g = groups[off]
        first = next((c for c in g if c[2] == PREFER.get(off)), g[0])
        rest = sorted((c for c in g if c is not first), key=lambda c: c[0])
        cities = []
        for c in [first] + rest:
            cities.append(c[:5])
            for nm, cc, tz in EXTRA:
                if tz == c[2]:
                    cities.append((nm, cc, tz, c[3], c[4]))
        lat, lon = first[5]
        col = int(off + 11) % 24 if off == int(off) and -12 <= off <= 12 else int((lon + 172.5) % 360 // 15)
        out.append((off, col, cities))
    return out


def main():
    zs = build()
    with open(os.path.join(ROOT, 'python', 'zones.py'), 'w', encoding='utf-8') as fh:
        fh.write('"""zones.py - the time zones of ZONE47, written by tools/make_zones.py (do not edit).\n'
                 'Source: the IANA tz database (https://www.iana.org/time-zones), tzdata %s, zone.tab, standard\n'
                 'offsets of %d. ZONES: (offset h, map column, cities); a city: (name, country code, tz id, DST h,\n'
                 'rule: ((month, n, weekday, standard-time hour) start, (...) end), None or "irregular"; n 5 = the\n'
                 'last, weekday 0 Sunday)."""\n' % (version(), YEAR))
        fh.write('TZDATA = %r\nYEAR = %d\nZONES = [\n' % (version(), YEAR))
        for z in zs:
            fh.write('    (%r, %r, [\n' % z[:2])
            for c in z[2]:
                fh.write('        %r,\n' % (c,))
            fh.write('    ]),\n')
        fh.write(']\n')
    rules = {c[4] for z in zs for c in z[2] if c[4] and c[4] != 'irregular'}
    for off, col, cities in zs:
        print('%+6.2f col %2d  %2d cities: %s' % (off, col, len(cities), ', '.join(
            c[0] + ('*' if c[4] == 'irregular' else '+' if c[4] else '') for c in cities)))
    print('tzdata %s: %d stops, %d cities, %d DST rules (+ DST, * irregular)' % (
        version(), len(zs), sum(len(z[2]) for z in zs), len(rules)))


if __name__ == '__main__':
    main()
