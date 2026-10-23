# AI Assistance Policy

## How this project uses AI

This project was **developed with the help of AI** — Claude (Anthropic) — as a cooperation. AI assisted with code generation, the map and time-zone tools, and documentation, but I reviewed all output, validated results against reference data and the C47 simulator, and take full responsibility for the work and any mistakes.

## Responsible use

- ✅ **I checked the results** — Every stop is run in the C47 simulator and its texts checked (`tests/test_zone47.py`)
- ✅ **I checked the data** — The time zones come from the IANA tz database (tzdata) and are tested against Python's `zoneinfo`
- ✅ **I maintained domain expertise** — I guide the AI with the design decisions: the map, the keys, the data shown
- ✅ **I take full responsibility** — The work is mine; any errors are mine to fix
- ✅ **I'm transparent** — This file documents how AI was used

## Testing & Validation

- Simulator tests: the C47 program runs in `python/c47sim.py` (from Almanac 47)
- Time zones from tzdata; times and dates checked against Python's `datetime`
- To be tested on real C47 hardware before each release

## License

This does not affect the GNU GPL-3.0 license. All code remains open-source and fully accessible.
