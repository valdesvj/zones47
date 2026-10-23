# Zones 47 — world time zones for the C47 / R47

`ZONE47` shows a dot map of the world on the SwissMicros C47 / R47 and steps through the **official time
zones** with the keys 4 and 5 (or 6), highlighting the 15° column of each one — in the spirit of the time-zone
page of a Garmin watch, without highlighting countries.

![ZONE47 on New York](docs/ZONE47_newyork.png)

## What it shows

- **The map**: 120 × 45 dots, 3° a dot, 81°N to 54°S, in 24 columns of 15° (UTC−11 at the left, UTC±12 at
  the right: 172.5°E to 172.5°W). Zone numbers and ticks under the map.
- **The stops**: one per official standard offset of the IANA tz database (tzdata 2026e): 37 from −11 to +14,
  including +5:30, +5:45, +8:45, +12:45, +13 and +14, plus **−12 "at sea"** (the nautical zone, no one lives
  there). The highlighted column is the offset's own for whole hours −12…+12; the others take the column of
  their city's longitude.
- **Line 1**: the offset, its time and date (weekday, day, month).
- **Line 2**: your clock (`TZ`), its time, and the difference.
- **Under the map**: a city of that offset and its daylight saving, e.g. `New York   DST +1 h in summer`.
  The times shown are **standard time**: add the DST in summer where it applies.
- A triangle marks the column of your own zone (the stop nearest to `TZ`). The time updates every minute.

## Keys

| Key | |
|---|---|
| 4 | the stop west (a smaller offset) |
| 5 | the stop east (6 works too) |
| 0 | the end: the screen cleared, your stack and LASTx as they were |

At the ends it goes around: east of +14 is −12, west of −12 is +14.

## TZ: the offset of your clock

The calculator's clock has no time zone, so ZONE47 reads the global variable **TZ** = clock − UT in hours,
the same variable as MOON47 in [Almanac 47](https://github.com/valdesvj/almanac47):

    3 STO "TZ"      clock on UT+3
    -5.5 STO "TZ"   clock on UT−5:30
    0 STO "TZ"      clock on UT

`TZ` is what your clock shows minus UT, **summer time included** (Madrid in July: 2). If `TZ` is not there
(or is 0), ZONE47 asks for it at the start (`TZ=CLOCK-UT h, R/S`): key the hours and R/S, or just R/S to keep
0 (clock on UT). Change it when you change the calculator's clock (at sea, when the ship's time changes, or
at a DST change).

## Updating the time zones

The stops come from the computer's tz database (on Linux `/usr/share/zoneinfo`, the package `tzdata`):

    python3 tools/make_zones.py      # python/zones.py from zone1970.tab, prints the stops and the tzdata version
    python3 tools/build_zone47.py    # programs/ and build/ZONE47.txt with the new stops
    python3 tests/test_zone47.py     # every stop checked against Python's zoneinfo

## Build and files

| | |
|---|---|
| `programs_rem/ZONE47.txt` | the commented source (STRUCT, named labels) — edit this one |
| `programs/ZONE47.txt`, `build/ZONE47.txt` | the calculator program (to convert with rejig) |
| `listings/` | numbered steps with comments, the local labels |
| `python/worldmap.py` | the dot map (`tools/make_map.py`, land/sea from the GLOBE 1 km data, NOAA) |
| `python/zones.py` | the stops (`tools/make_zones.py`, from tzdata) |
| `python/c47sim.py`, `stdfont.py`, `tinyfont.py` | the C47 simulator and fonts, from Almanac 47 |
| `python/zone47sim.py` | runs ZONE47 in the simulator, writes `docs/*.png` |
| `tests/test_zone47.py` | the tests |

Calculators: C47 / R47 with STRUCT, ATEXT and GRFNT (firmware 00.109.05.00a0.ALPHA or later, as Elements 47).
Not yet run on a real C47.

## Credits and licence

Victor Valdes, GNU GPL v3.0 or later (`LICENSE`, `NOTICE`). Written with the help of AI (`AI_ASSISTANCE.md`).
Time zones: the IANA tz database (https://www.iana.org/time-zones), public domain. Map: global-land-mask
(GLOBE, NOAA). Fonts: the C43/C47 firmware. SwissMicros, C47, R47 and DM42 are trademarks of their owners.
