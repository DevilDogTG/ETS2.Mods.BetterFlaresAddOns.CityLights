# Tuning log

Levers live at the top of `tools/generate_citylights.py` (`LEVERS`). One lever group per test build; each round is
logged here with its values and the in-game verdict. At release this becomes the Tx table of released values.

| Round | Build | Lever group | Values | What to check | Verdict |
|---|---|---|---|---|---|
| T1 | 1.0.0-dev.1 | brightness + restore | `intensity` 1.0 (diffuse / specular = max(BF, base game)), `ambient` BF's, `restore` on | City street at night vs BF alone; a highway tunnel (8,000 → 63,700 lm); København underground depot (`goto 7449;-46;-27992`) and a player garage (restored fills) | **Looks right** (2026-11-19). Drive: Iberian motorways at night, 18 Nov; log clean (no light / unit errors, mounted above all BF packs). Restored fills (depot, garage) not seen yet - check in the next round |

| T2 | 1.0.0-dev.2 | env sprites + BF Base restore | `env` on (BF sprite table on untouched env flares), restore widened to BF Base; T1 levers unchanged | Photographer camera flash, plane / obstruction lights, green lamps, roadwork orange blinkers; restored fills from T1 (København depot, garage) | **Pass** (2026-11-21, checked on dev.3, which carries T2 unchanged). Lit: lighthouse `flare.model.plane.blink` (blinks); `flare.model.green` on the Þórshöfn statue, both lake/harbour steamers and both military ships; restored fills in the København underground depot, Helsinki bus station, Eindhoven museum and a player garage. Not seen: photographer flash (crowd movers and Special Transport cutscenes only) and jet flyover plane lights (mover). `orange.blink2-5` are on no 1.62 model, log check only |
| T3 | 1.0.0-dev.3 | `tr_light_flares.sii` restore | restore covers BF Base's `tr_light_flares.sii` (TrafficLights deprecated); twin rule; T2 levers unchanged | T2's points still open; `flare.traffic.white.rh` is used by no 1.62 model (scan 2026-11-21: only `white.r`, 8 tram signals), so it is a log check only; normal and tram traffic lights unchanged | **Pass** (2026-11-21). Two night runs with the console camera, dev.3 only; log clean (no light, flare, hookup or model warnings). Street lamps lit; one traffic signal seen lit from a distance; tram signals not visited |

## Effect of T3 (generator report, 2026-11-19)
- BF Base `tr_light_flares.sii`: `flare.traffic.white.rh` restored, BF-styled from twin `flare.traffic.white.r`
  (`scale_factor` 2 -> 1.5, own `tr_yellow_tram` sprite). Every BF traffic unit byte-identical.
- 3 dangling BF models kept as BF ships them (`flare.traffic.*_left` -> `tr_left_*.pmd`, not in base 1.62).
- 95 files shipped (94 from T2, unchanged, + 1).

## Effect of T2 (generator report, 2026-11-19)
- 8 env flares given BF's sprite: photographer camera flash x3 (`lamp_4k`), plane flares white + white blink (`lamp_4k`),
  red (`bf_r3`), green (`bf_gr`), `flare.model.green` (`bf_gr`).
- 13 env flares kept vanilla (BF has no sprite): blue beacons x8, `flare.model.orange.blink2-5`, yellow garage lamp.
- 24 untouched env lights kept as base (BF's style at base brightness = base).
- BF Base `light_blinking.sii`: 4 dropped orange blinkers restored. 94 files shipped (88 from T1 + 6).

## Effect of T1 (generator report, 2026-11-18)
- 530 BF-styled lights: 440 raised to base-game intensity, 84 already at or above it (kept), 6 kept BF's
  (3 other setup unit, 3 without a base twin).
- 143 restored units: 141 BF-styled from their sibling, 2 garage units as base.
- 88 of BF CL's 139 base-path files change; the other 51 stay BF's (not shipped).
