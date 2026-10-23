#!/usr/bin/env python3
"""Write python/loadzones.py: the load line zones, areas and seasonal periods of the International Convention on
Load Lines 1966 (IMO), Annex II, on the 3-degree dot grid of the map (python/worldmap.py), for LOAD47.

Sources (the boundaries as written there; named places by the coordinates in PLACES below):
  Annex II, regulations 46 and 48-52: as in the US Load Line Regulations, 46 CFR 42.30-5 to 42.30-35 (the 1966
    text: https://www.law.cornell.edu/cfr/text/46/part-42/subpart-42.30)
  regulation 47, Southern Winter Seasonal Zone: as replaced by IMO resolution MSC.329(90) (2012, in force
    1 January 2014; https://www.imo.org/...MSC.329(90).pdf)
Ships over 100 m (328 ft). The areas that apply only to ships of 100 m and under (Baltic, Black Sea north of
44N, the western Mediterranean, the Sea of Japan north part, the US east coast, the Winter North Atlantic load
line) are not drawn.

Each 3-degree cell takes the area of its centre. An area: a name, the zone outside its seasons (T tropical,
S summer, W winter) and its seasons: [(start MMDD, end MMDD, zone)], the date ranges in which it is another
zone. The cells of each area are cut into rectangles (dot columns c0-c1, dot rows r0-r1) for the calculator.
INDICATIVE ONLY, 3 degrees a cell: the official boundaries are those of Annex II and its chart.
  python3 tools/make_loadlines.py          # python/loadzones.py, prints the map, writes docs/LOAD47_cells.png"""
import math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
from worldmap import COLS, NCOL, NROW

# named places of Annex II (latitude, longitude; S and W negative), from charts and gazetteers
PLACES = {
    'Cape Tres Puntas': (-47.10, -65.87), 'Cape Grim': (-40.68, 144.69), 'Bruny Island S': (-43.50, 147.15),
    'Black Rock Point': (-47.07, 168.15), 'Punta Corona': (-41.78, -73.88), 'Cape Torinana': (43.05, -9.30),
    'Cape Krilon': (45.90, 142.08), 'Wakkanai': (45.42, 141.68), 'Dall Island S': (54.66, -132.68),
    'Cape Catoche': (21.60, -87.10), 'Cape San Antonio': (21.87, -84.95), 'Santos': (-23.97, -46.32),
    'Port Darwin': (-12.46, 130.84), 'Cape Wessel': (-10.98, 136.75), 'Cape York': (-10.69, 142.53),
    'Hong Kong': (22.28, 114.17), 'Sual': (16.07, 120.10), 'The Skaw': (57.75, 10.60),
}


def merc(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def rhumb(lon, a, b):
    """The latitude of the rhumb line from a to b (lat, lon) at longitude lon (between theirs)."""
    (la, oa), (lb, ob) = a, b
    if ob == oa:
        return la
    t = (lon - oa) / (ob - oa)
    y = merc(la) + t * (merc(lb) - merc(la))
    return math.degrees(2 * math.atan(math.exp(y)) - math.pi / 2)


def piece(lon, pts):
    """A boundary given as a function of longitude: pts [(lon, lat, 'r' rhumb / 'p' parallel to the next)],
    lon increasing. Returns the latitude at lon, or None outside."""
    for (o1, l1, k), (o2, l2, _) in zip(pts, pts[1:]):
        if o1 <= lon <= o2:
            return l1 if k == 'p' else rhumb(lon, (l1, o1), (l2, o2))
    return None


def east(lon, start):
    """lon unwrapped to start .. start + 360."""
    return (lon - start) % 360 + start


# ---- regulation 48: the Tropical Zone (northern and southern boundaries as functions of longitude) ----
def trop_north(lon):
    o = east(lon, -180)
    if -180 <= o < -60 or o >= 145:          # 13N from 145E across the Pacific; 13N from the American east coast
        return 13.0
    if -60 <= o < -58:
        return rhumb(o, (13, -60), (10, -58))
    if -58 <= o < -20:
        return 10.0
    if -20 <= o < 43:                        # 20W north to 30N, 30N to Africa; Africa (land)
        return 30.0
    if 43 <= o < 70:                         # 8N from the east coast of Africa to 70E
        return 8.0
    if 70 <= o < 76:                         # 70E to 13N, 13N to India
        return 13.0
    if 76 <= o < 79.8:                       # round the south of India to 10 30N on the east coast
        return 10.5
    if 79.8 <= o < 82:
        return rhumb(o, (10.5, 79.8), (9, 82))
    if 82 <= o < 98.5:                       # 82E down to 8N, 8N to Malaysia
        return 8.0
    if 98.5 <= o < 107:                      # the coasts of South-East Asia: the Gulf of Thailand inside
        return 14.0
    return 10.0                              # 10N from Vietnam to 145E


def trop_south(lon):
    o = east(lon, -180)
    if -150 <= o < -75:
        return rhumb(o, (-11, -150), (-26, -75))
    if -75 <= o < -71:
        return rhumb(o, (-26, -75), (-30, -71.5))
    if -71 <= o < -46.32:
        return -23.97                        # (South America, land; the coast south-west of Santos summer)
    if -46.32 <= o < -40:
        return rhumb(o, PLACES['Santos'], (-23.45, -40))
    if -40 <= o < 34.7:
        return -23.45                        # the Tropic of Capricorn to Africa
    if 34.7 <= o < 44.4:
        return -20.0                         # 20S from Africa to Madagascar
    if 44.4 <= o < 50:
        return -12.5                         # round the north of Madagascar to 50E
    if 50 <= o < 98:
        return -10.0
    if 98 <= o < 130.84:
        return rhumb(o, (-10, 98), PLACES['Port Darwin'])
    if 130.84 <= o < 136.75:
        return -11.5                         # the coast of Australia to Cape Wessel
    return -11.0                             # 11S to Cape York, then to 150W


def red_sea_etc(lat, lon):
    """Included in the Tropical Zone: Suez Canal, Red Sea, Gulf of Aden to 45E; Persian Gulf to 59E; inside the
    Great Barrier Reef 11S-22S."""
    if 12 <= lat <= 31.5 and 32 <= lon <= 45 and lat - 12 >= (lon - 43) * 0:     # Red Sea and the Gulf of Aden
        if lon <= 43.5 or lat <= 15:
            return True
    if 22.5 <= lat <= 30.5 and 47.5 <= lon <= 59:                                 # Persian Gulf, Gulf of Oman
        return True
    if -22 <= lat <= -11 and 142.5 <= lon <= 143.8 + (152.5 - 143.8) * (-11 - lat) / 11:   # the Reef lagoon
        return True
    return False


def tropical(lat, lon):
    return trop_south(lon) < lat < trop_north(lon) or red_sea_etc(lat, lon)


# ---- regulation 49: the Seasonal Tropical Areas ----
def st_north_atlantic(lat, lon):
    if not -98 <= lon <= -20 or lat <= trop_north(lon):
        return False
    if lon < -87.1:
        return False                          # the Gulf of Mexico (north of Cape Catoche) is summer
    top = 21.87 if lon < -74.2 else 20.0      # Catoche - San Antonio - north coast of Cuba to 20N, then 20N
    return lat <= top


def st_arabian(lat, lon):
    if not 45 <= lon <= 78 or lat <= trop_north(lon) or lat > 30:
        return False
    return not (lon < 59 and lat > 22.5)      # the Gulf of Oman west of 59E: Persian Gulf (tropical)


def st_bengal(lat, lon):
    return 78 <= lon <= 99 and trop_north(lon) < lat <= 25


def st_china(lat, lon):
    if not 104 <= lon <= 121 or lat <= 10:
        return False
    if lat <= 16.07:
        return True
    return lat <= 23 and lon <= rhumb_lon(lat, PLACES['Sual'], PLACES['Hong Kong'])


def rhumb_lon(lat, a, b):
    """The longitude of the rhumb line a-b at latitude lat."""
    (la, oa), (lb, ob) = a, b
    t = (merc(lat) - merc(la)) / (merc(lb) - merc(la))
    return oa + t * (ob - oa)


def st_npac_west(lat, lon):
    return 13 < lat <= 25 and east(lon, 0) >= 160 and east(lon, 0) <= 230


def st_npac_east(lat, lon):
    if not 13 < lat <= 40 or not -130 <= lon <= -90:
        return False
    if lat >= 33:
        return lon >= -123
    return lon >= rhumb_lon(lat, (33, -123), (13, -105))


def st_sind_west(lat, lon):
    if not -20 <= lat < trop_south(lon):
        return False
    edge = 51.5 if lat >= -15 else 50 + 1.5 * (lat + 20) / 5
    return 43 <= lon <= edge


def st_sind_east(lat, lon):
    if lat >= trop_south(lon):
        return False
    if 51.5 < lon <= 120:
        return lat >= -15
    if 120 < lon <= 136:
        return lat >= -25                     # to the coast of Australia
    return False


def st_carpentaria(lat, lon):
    return 135.5 <= lon <= 142.5 and -18 <= lat < -11


def st_spac_east(lat, lon):
    o = east(lon, 0)
    if lat >= trop_south(lon) or tropical(lat, lon):
        return False
    if 142 <= o <= 210:                       # Australia's east coast to 150W: the Tropic of Capricorn
        return lat >= -23.45
    if 210 < o <= 255:                        # 150W to the Tropical Zone: 20S
        return lat >= -20
    return False


# ---- regulations 46 and 47: the winter seasonal zones and area (ships over 100 m) ----
def na_zone1(lat, lon):
    return (-50 <= lon <= -15 and lat >= 45) or (-15 < lon <= 0 and lat >= 60)


def na_zone2(lat, lon):
    if na_zone1(lat, lon) or lat < 36 or lon < -75 or lon > 45:
        return False
    if lon < -68.5 and lat < 46:
        return False                          # the US coast west of 68 30W: the Winter Seasonal Area
    if lon > -6 and lat < 46.5:
        return False                          # the Mediterranean and the Black Sea
    if lon > 10.6 and lat < 66 and lon < 31:
        return False                          # the Baltic (inside The Skaw)
    if lon < -73 or lat >= 40:
        south = 40.0 if lon <= -68.5 else None
    if lon <= -73:
        return lat > 40
    if -73 < lon <= -68.5:
        return lat > rhumb(lon, (36, -73), (40, -68.5))
    if -68.5 < lon <= -25:
        return lat > 36
    if -25 < lon <= -9.3:
        return lat > rhumb(lon, (36, -25), PLACES['Cape Torinana'])
    return lat > 43                           # Bay of Biscay north of Cape Torinana, the North Sea


def na_area(lat, lon):
    """The North Atlantic Winter Seasonal Area: west of 68 30W to 40N, rhumb line to 61W on the coast of
    Canada (45.2N), the coasts of Canada and the US."""
    if not -76 <= lon <= -61 or lat > 47:
        return False
    if lon <= -68.5:
        return lat > 40
    return lat > rhumb(lon, (40, -68.5), (45.2, -61))


def np_winter(lat, lon):
    o = east(lon, 0)
    if 130 <= o < 141.7:
        return lat >= 50                      # 50N from Asia to Sakhalin (the Tatar Strait)
    if 141.7 <= o < 145:
        return lat >= 45.4                    # Krilon - Wakkanai, the coasts of Hokkaido: the Okhotsk Sea
    if 145 <= o <= 210:
        return lat >= 35
    if 210 < o <= 227.32:
        return lat >= rhumb(o, (35, 210), (54.66, 227.32))
    return False


SW_PTS = [(-73.88, -41.78, 'p'), (-65.87, -47.1, 'r'), (-50, -34, 'p'), (16, -34, 'r'), (20, -36, 'r'),
          (30, -34, 'r'), (118, -35.5, 'r'), (144.69, -40.68, 'r'), (147.15, -43.5, 'r'), (168.15, -47.07, 'r'),
          (170, -47, 'r'), (190, -33, 'p'), (281, -33, 'r'), (285, -41, 'r'), (286.12, -41.78, 'p')]


def s_winter(lat, lon):
    """South of the boundary of regulation 47 (MSC.329(90))."""
    o = east(lon, -74)
    if o >= 285 or o < -65.87:                # Chile south of Chiloe, Patagonia: the boundary runs on land
        return lat < -41.5
    b = piece(o, SW_PTS)
    return b is not None and lat < b


# the areas, in the order they are tested: (name, zone outside the seasons, [(start, end, zone)], test)
AREAS = [
    ('Tropical Zone', 'T', [], tropical),
    ('N Atlantic, seasonal tropical', 'S', [(1101, 715, 'T')], st_north_atlantic),
    ('Arabian Sea, seasonal tropical', 'S', [(901, 531, 'T')], st_arabian),
    ('Bay of Bengal, seasonal tropical', 'S', [(1201, 430, 'T')], st_bengal),
    ('China Sea, seasonal tropical', 'S', [(121, 430, 'T')], st_china),
    ('N Pacific W, seasonal tropical', 'S', [(401, 1031, 'T')], st_npac_west),
    ('N Pacific E, seasonal tropical', 'S', [(301, 630, 'T'), (1101, 1130, 'T')], st_npac_east),
    ('S Indian W, seasonal tropical', 'S', [(401, 1130, 'T')], st_sind_west),
    ('S Indian E, seasonal tropical', 'S', [(501, 1130, 'T')], st_sind_east),
    ('Carpentaria, seasonal tropical', 'S', [(401, 1130, 'T')], st_carpentaria),
    ('S Pacific, seasonal tropical', 'S', [(401, 1130, 'T')], st_spac_east),
    ('N Atlantic winter zone I', 'S', [(1016, 415, 'W')], na_zone1),
    ('N Atlantic winter zone II', 'S', [(1101, 331, 'W')], na_zone2),
    ('N Atlantic winter area', 'S', [(1216, 215, 'W')], na_area),
    ('N Pacific winter zone', 'S', [(1016, 415, 'W')], np_winter),
    ('Southern winter zone', 'S', [(416, 1015, 'W')], s_winter),
]


def cell(i, j):
    """The centre of dot row i, column j: latitude, longitude (-180..180)."""
    lat = 81 - 3 * i - 1.5
    lon = (-172.5 + 3 * j + 1.5 + 180) % 360 - 180
    return lat, lon


def classify():
    """grid[i][j] = the index of the area (1..), 0 = summer zone."""
    grid = []
    for i in range(NROW):
        row = []
        for j in range(NCOL):
            lat, lon = cell(i, j)
            row.append(next((k for k, a in enumerate(AREAS, 1) if a[3](lat, lon)), 0))
        grid.append(row)
    return grid


def rects(cells):
    """A set of (i, j) cut into rectangles (c0, c1, r0, r1): row runs of each column joined across columns."""
    left = set(cells); out = []
    while left:
        i, j = min(left, key=lambda p: (p[1], p[0]))
        i1 = i
        while (i1 + 1, j) in left:
            i1 += 1
        j1 = j
        while all((r, j1 + 1) in left for r in range(i, i1 + 1)):
            j1 += 1
        for r in range(i, i1 + 1):
            for c in range(j, j1 + 1):
                left.discard((r, c))
        out.append((j, j1, i, i1))
    return out


def land(i, j):
    return COLS[j] >> i & 1


def main():
    grid = classify()
    keys = '.TabcdefghiJKLMNW'
    for i in range(NROW):
        print(''.join('#' if land(i, j) and not grid[i][j] else
                      (keys[grid[i][j]].upper() if land(i, j) else keys[grid[i][j]]) for j in range(NCOL)))
    out = []
    for k, (nm, base, seas, _) in enumerate(AREAS, 1):
        cs = {(i, j) for i in range(NROW) for j in range(NCOL) if grid[i][j] == k}
        rs = rects(cs)
        out.append((nm, base, seas, rs))
        print('%2d %-34s %s %-28s %3d cells %3d rectangles' % (k, nm, base, seas, len(cs), len(rs)))
    with open(os.path.join(ROOT, 'python', 'loadzones.py'), 'w') as fh:
        fh.write('"""loadzones.py - the load line areas of LOAD47, written by tools/make_loadlines.py (do not edit).\n'
                 'Load Lines 1966 Annex II (IMO), regulation 47 as MSC.329(90); ships over 100 m. AREAS: (name, zone\n'
                 'outside the seasons, [(start MMDD, end MMDD, zone)], [(c0, c1, r0, r1) dot columns and rows]);\n'
                 'GRID[i][j] the area (1..) of dot row i, column j, 0 = summer zone. Indicative, 3 degrees a cell."""\n')
        fh.write('AREAS = [\n')
        for a in out:
            fh.write('    %r,\n' % (a,))
        fh.write(']\nGRID = [\n')
        for row in grid:
            fh.write('    %r,\n' % (row,))
        fh.write(']\n')
    print('rectangles: %d' % sum(len(a[3]) for a in out))


if __name__ == '__main__':
    main()
