# AI Assistance Policy

## How this project uses AI

This project was **developed with the help of AI** — Claude (Anthropic) — as a cooperation. AI assisted with brainstorming, code generation, and documentation, but I reviewed all output, validated results against reference implementations, and take full responsibility for the work and any mistakes.

## Responsible use

- ✅ **I checked the results** — Every time shown is validated against Python's `zoneinfo` (the IANA tz database) in the C47 simulator, at every stop and around every daylight-saving change (`tests/test_zone47.py`)
- ✅ **I maintained domain expertise** — I guide the AI with design decisions based on navigation and time-keeping at sea
- ✅ **I take full responsibility** — The work is mine; any errors are mine to fix
- ✅ **I'm transparent** — This file documents how AI was used

## Testing & Validation

- Simulator tests: the C47 program in `python/c47sim.py` (from Almanac 47), every screen and every text checked
- Cross-validated against the IANA tz database (tzdata) through Python's `zoneinfo`
- To be tested on real C47 hardware before each release

## License

This does not affect the GNU GPL-3.0 license. All code remains open-source and fully accessible.

---

*For more details, see `NOTICE` and the development documentation.*
