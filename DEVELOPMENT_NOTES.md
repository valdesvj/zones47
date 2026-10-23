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

## To do

1. Run on Victor's C47 (convert build/ZONE47.txt with rejig).
2. c47sim fix in Almanac 47 (above).
3. Ideas: a key to set TZ from the stop; DST rules on the calculator; day / night shading.
