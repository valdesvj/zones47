# Zones 47: working rules

- Work on a new branch; Victor creates and merges the PRs. Never force-push or rewrite history.
- Commit author: "Victor Valdes" <valdesvj@users.noreply.github.com>.
- Never commit binaries (.p47 files made by rejig).
- Edit the program in programs_rem/ZONE47.txt (commented source), then run python3 tools/build_zone47.py:
  it writes programs/, build/ and listings/. Never edit those three by hand.
- The build fills the marker lines REM ==== MAP, LABELS, NSTOPS and STOPS from python/worldmap.py and
  python/zones.py. Those two files are written by tools/make_map.py (needs pip global-land-mask) and
  tools/make_zones.py (the computer's tzdata, /usr/share/zoneinfo); never edit them by hand.
- STRUCT as Elements 47: IF / ELSE / ENDIF, DO / WHILE / ENDDO, indented, no numbers in the source; a test
  right before IF / WHILE; never a test before ELSE, ENDIF, DO, ENDDO. Named labels LBL :NAME: (1-7 letters
  or digits); LBL 01-nn are the stops (XEQ IND 32).
- Text on the C47 screen: ATEXT in GRFNT 21 (GRFNT 10 for the tiny font). Restore GRFNT 20 and GRMOD 0 before
  the program ends. GRMOD and GRFNT take X: write `3 GRMOD`.
- Key waits: DO / PAUSE 50 / KEY? 33 / WHILE / ENDDO (as Elements 47).
- Only commands already run on a C47 in Almanac 47 or Elements 47 (the firmware sources on GitLab are not
  reachable from the cloud session); a new command: say so and ask Victor to try it.
- Before changing a screen, check it in the simulator (python3 python/zone47sim.py writes docs/*.png), then
  python3 tests/test_zone47.py.
- python/c47sim.py, stdfont.py, tinyfont.py come from Almanac 47: a fix is made there first, then copied here.
  Known: Date→ⅅ sets the run's step counter n (zone47sim uses maxsteps 10**8): DEVELOPMENT_NOTES.
- Work in one repository at a time (this one); almanac47 and elements47 are for reference only.
- Ask before anything that can't be undone. Pull requests only for zones47.
