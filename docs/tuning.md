# Tuning log

Levers live at the top of `tools/generate_citylights.py` (`LEVERS`). One lever group per test build; each round is
logged here with its values and the in-game verdict. At release this becomes the Tx table of released values.

| Round | Build | Lever group | Values | What to check | Verdict |
|---|---|---|---|---|---|
| T1 | 1.0.0-dev.1 | brightness + restore | `intensity` 1.0 (diffuse / specular = max(BF, base game)), `ambient` BF's, `restore` on | City street at night vs BF alone; a highway tunnel (8,000 → 63,700 lm); København underground depot (`goto 7449;-46;-27992`) and a player garage (restored fills) | pending |

## Effect of T1 (generator report, 2026-11-18)
- 530 BF-styled lights: 440 raised to base-game intensity, 84 already at or above it (kept), 6 kept BF's
  (3 other setup unit, 3 without a base twin).
- 143 restored units: 141 BF-styled from their sibling, 2 garage units as base.
- 88 of BF CL's 139 base-path files change; the other 51 stay BF's (not shipped).
