# Zones 47: development notes

## Oct 23, 2026 - v0.1.0, the first version

- Idea (Victor): the time-zone page of the Garmin Instinct 3 on the C47: a world map, keys 4 and 5 move
  through the zones, the column highlighted, no countries; the variable TZ for the clock's zone. Then: the
  official zones, with their source, so they can be updated (from Linux).
- Map: a dot map, 120 x 45 dots of 2 x 2 pixels at a 3-pixel pitch (3 degrees a dot), 81N-54S, longitude from
  172.5W so each 15-degree zone is exactly 5 dot columns. tools/make_map.py samples 6 x 6 points a dot with
  global-land-mask (GLOBE 1 km), land when at least 25 % (keeps the British Isles, Japan, New Zealand).
- Drawing: AGRAPH, one 64-bit word per band of 15 dots (45 rows: bits 3m and 3m + 1 for the dot m), three
  bands a column, each drawn twice (the dot is 2 wide). The data: three decimal numbers and XEQ :COL: per dot
  column (SINT before AGRAPH, as MOON47); 120 columns. Start screen 5 350 steps in the simulator, a move 824.
- ATEXT with a square glyph instead (Victor's question): the fonts have only the tinyFont "·" (2 x 2 ink,
  6 columns advance) and the standard "▪" (8 x 8, 12 advance): the advance sets the pitch, so a map of about
  60 x 20 dots, one glyph per dot. AGRAPH draws 15 dots a step: kept.
- The highlight: XOR (GRMOD 3), 15 columns x 138 rows (59-196) in AGRAPH passes of 64, 64, 10 rows; drawn
  again = off, so a move redraws no map.
- The stops: tools/make_zones.py reads zone1970.tab of the computer's tzdata (2026e here) with zoneinfo; the
  standard offset = utcoffset - dst on the 15th of each month of 2026; one stop per standard offset (37) and
  -12 "at sea" (Etc/GMT+12). City: PREFER in the tool, else the first zone of zone1970.tab. DST: of that city.
  Column: whole hours -12..12 their own; the rest from the city's longitude (zone1970.tab coordinates).
- Time: the clock (Date→ⅅ Time→ℸ ⅅℸ→J, as MOON47) - TZ/24 = UT (R31); + offset/24 = the zone. hh:mm and the
  date from the JD by arithmetic (Fliegel - Van Flandern), no J→ⅅℸ (not used in Almanac 47 yet). Names by
  αSL / αLEFT on one text (αMID not used yet). The minute checked at each key wait: a new minute redraws the
  header.
- Commands: all already in Almanac 47 or Elements 47 on a C47 (LocR, R-CLR, STRUCT, ATEXT, GRFNT, GRMOD,
  AGRAPH, SINT, CLLCDxy, x→α, αIP, αSL, αLEFT, DSE, KEY?, XEQ IND, the clock). The C43/C47 sources on GitLab
  could not be reached from the cloud session.
- c47sim (from Almanac 47): its Date→ⅅ code sets n = the day number, and n is also run()'s step counter, so
  any run past the clock stops with "too many steps". zone47sim and the tests use maxsteps 10**8. To fix in
  Almanac 47 (another variable name), then copy c47sim.py here.
- Tests (tests/test_zone47.py): every stop east and west and around, for TZ none, 3, 5.5, -3.5, 13, 14, -12,
  -9.75 and dates across a year end and a leap day: every header and city text against Python's datetime and
  python/zones.py; the screen the same after a full turn; TZ kept; the stack kept; R20-R49 cleared.

## Oct 23, 2026 - DST worked out on the calculator (Victor: "do it real")

- tools/make_zones.py: the DST rule of each stop's city from zoneinfo's transitions in 2026-2035 (to the
  minute), as (month, n 1-4 or 5 = last, weekday 0 Sunday, hour of standard time) for the start and the end;
  the tool stops if a city does not follow one such rule. 16 cities, 9 rules.
- The build: the stop's DST field = 100r + 10 DST (r the rule); the rules LBL 41-49 push the end hour, the
  end code, the start hour, the start code (code = 100 month + 10 n + weekday).
- ZONE47: LBL :NOWOFF: (R59 = the offset now) takes the stop's standard time t, its year (LBL :CAL:), the
  start and the end of that year (LBL :TRANS:, LBL :JDN: the 1st of a month; n = 5 from the 1st of the next
  month - 1), on when start <= t < end (north) or t >= start or t < end (south). The header, the clock line
  and the home stop use the offset now. Home stop: the nearest to TZ now, of two as near the one without DST
  on (TZ 3 in October: Moscow, not Cairo on summer time).
- Steps: 1 602; the start 11 494 in the simulator (the home stop checks DST at all 38 stops), a move 864.
- Tests: every stop at 8 TZ values; each rule city 30 minutes before and after each change in 2026, 2027
  and 2030; the texts against zoneinfo.
- docs/ZONE47_tour.gif (tools/make_gif.py, Pillow): key 5 through every stop. LICENSE copied from Almanac 47
  (the same GPL-3.0 text, its http links), AI_ASSISTANCE.md in Almanac 47's form.

## Oct 23, 2026 - the cities of every stop (Victor: "the user will not miss his capital"; Medellin)

- tools/make_zones.py reads zone.tab (a line per country, its main zone first) instead of zone1970.tab: one
  city per country and DST rule in each stop (Antarctica left out), 311 cities, the PREFER city first and the
  others by name; EXTRA cities not in tzdata after their zone's city (Medellin after Bogota, America/Bogota).
- DST rules per city: 17. The rule finder also tries the day of a change 1-3 days off with the hour moved by
  24 h (Chile: the first Saturday at 24:00; Israel: the 4th Thursday at 26:00 = the Friday before the last
  Sunday; Nuuk: the last Sunday at -1:00). A city whose changes are not one a year in each direction follows
  no rule: "irregular", standard time shown with "DST varies" (Casablanca, El Aaiun: Ramadan).
- The stop label stores its cities in R72-R74 (texts of at most 196 characters, "/" between the entries
  "rCCname": r the rule letter of R81, CC the country) and their numbers R75-R77. LBL :CITY: takes the R80-th
  out (αPOS "/", αSL, αLEFT). Keys 8 / 2: the city before / after. The rules LBL 41-57; the DST amount in the
  start code (+ 20000 x DST). Bug found by the tests: the decode pushed numbers before the rule's four values
  were stored; now stored first.
- Home stop: the smaller of |standard - TZ| and |offset now - TZ| + 0.01 of its first city (TZ -5 in October:
  the -5 stop, not Chicago on summer time).
- 2 012 steps, about 12 KB, 7 IF and 7 DO (the original DM42's limit: 10 each). Start 13 200 steps, a move 915.
- docs/ZONE47_tour.gif starts in Colombia (TZ -5) and steps to Medellin before going round.

## Oct 23, 2026 - faster start

- Profiled by label in the simulator: of the 13 200 steps of the start, 8 300 were LBL :NEAR: (the home stop:
  DST worked out for the first city of all 38 stops), 3 400 the map. Now a stop more than 1.5 h from TZ (by its
  standard offset) is only read (LBL :RECX:, no city, no DST): its distance is that of its standard offset (DST
  adds 1 h at most, so it cannot be the nearest); the others as before (LBL :NEAR2:). Of two as near: the first
  (X≤Y?), as before. Start 13 200 -> 6 326 steps (about 1.1 s at Almanac 47's 0.17 ms a step), a move 917,
  a city 473.

## To do

1. Run on Victor's C47 (convert build/ZONE47.txt with rejig).
2. c47sim fix in Almanac 47 (above).
3. Ideas: a key to set TZ from the stop; day / night shading.

## Oct 23, 2026 - Branch claude/load47-loadlines: LOAD47, the load line zones (Victor's next step)

- The zones, areas and seasonal periods of Load Lines 1966 Annex II on the same dot map, drawn for a date.
  Sources: 46 CFR 42.30-5 to -35 (the 1966 text of regulations 46 and 48-52) and MSC.329(90) (regulation 47,
  in force 1 Jan 2014). Ships over 100 m only for now.
- tools/make_loadlines.py: each boundary written as a function of longitude (rhumb lines on the Mercator
  latitude) or a test per area; the named places with the coordinates in PLACES (from charts, to check). Each
  3-degree cell takes the area of its centre; 16 areas, cut into 89 rectangles. A colour picture of the cells
  was checked by eye against the Annex II chart.
- LOAD47: each area a label (name, season text, zone, two seasons MMDD, then its rectangles as numbers
  10000000 c0 + 10000 c1 + 100 r0 + r1 with XEQ :RECT:). Drawing: per band the dots' rows as
  (8^(m1+1) - 8^m0) / 7 (lower rows) and twice that (upper rows), SINT, AGRAPH per dot column. The same labels
  find the cursor's area (mode 1) and give its texts (mode 2).
- Patterns: tropical the dot's upper left pixel, winter upper left and lower right, summer none, land full.
- Keys: 8 4 6 2 the cursor (as ELEM47: k div 10 - 6, k mod 10 - 3), 7 / 9 the date -/+ 15 days, 1 today.
- 1 693 steps, about 9 KB, no IF, 4 DO. Start 26 000 steps, a cursor move 4 500, a new date 30 000.
- Tests (tests/test_load47.py): every cell on 34 dates (each season change, the day before and the day), the
  cursor texts at a cell of each area in January and July, a year on and back the same screen, the stack.
- To do: the areas for ships of 100 m and under (a key to switch), the cursor on land (say so), Annex II's
  chart against the cells cell by cell, the coordinates of the named places checked.
