# ADR-0002: Better Flares sprites for untouched environment flares, and the BF Base restore

- Status: accepted (2026-11-19)
- Context: game ETS2 1.62, Better Flares Base 4.9.1 + City Lights 4.9; follows [ADR-0001](ADR-0001-generated-city-lights-files.md)

## Context
After ADR-0001 (round T1: "looks right" at base-game brightness), 42 base environment units under `unit/hookup`
(outside `vehicle/`) are still defined by no Better Flares pack:
- 24 `light_source`: Akureyri pier, coloured weak omni lamps, Genoa bridge, `dealer.int.big`, `light.unset`.
- 18 flares: photographer camera flash (`foto_01-03`, crowd movers `man_foto_01-03`; not speed cameras), plane / obstruction lights (`plane_flares.sii`), `green.sii`, blue
  beacons (`blue_blinking.sii`), the yellow garage lamp.

Better Flares' own data shows what its look means for these:
- For `light_source` units BF keeps saturated colours (hue/sat 148/72, 0/56, 264/68, 240/68 stay) and only moves
  white / sodium tones onto its palette; the rest of its change is the darkening ADR-0001 undoes. So BF's style at
  base-game brightness *is* the base unit for every untouched light here.
- For flares BF swaps the vanilla sprite for its own, with its scaling (`default_scale`, `scale_factor`,
  `scaling_start/end_distance`), consistently per vanilla sprite: `lamp_flare` / `lamp_flare_small` → `lamp_4k`
  (9, x1.6, 0-60 m), `lamp_flare_red` → `bf_r3`, `lamp_flare_green` → `bf_gr` (1.5, x2.5, 0-80 m), orange → `bf_o1`
  / `bf_lmp_o`. It has no sprite for blue beacons or the yellow garage lamp.

Also: BF Base's own `light_blinking.sii` is a pre-1.62 copy and drops 4 base flares (`flare.model.orange.blink2-5`),
the same problem ADR-0001 fixes for City Lights. Its `tr_light_flares.sii` drops `flare.traffic.white.rh`, but that
path belonged to `BetterFlaresAddOns.TrafficLights` (see the dev.3 amendment below).

## Decision
1. **Module `env`** (lever `env`). The generator learns a sprite table from BF at build time: for each vanilla flare
   model BF replaces (both packs, units with a base twin, outside `vehicle/`), BF's most common
   `(model, default_scale, scale_factor, scaling_start_distance, scaling_end_distance)`. Every base file under
   `unit/hookup` that no BF pack ships, outside `vehicle/` and not owned by another DriveDogs mod, gets that tuple on
   each unit whose `model:` is in the table (value token edited, missing keys inserted before the closing brace, a
   key BF leaves unset is not added). Files with no change are not shipped. Untouched `light_source` units and flares
   without a BF sprite stay vanilla (reported).
2. **Restore widened** to BF Base's files at base paths (outside `vehicle/`, not another mod's): the dropped base
   blocks are appended as in ADR-0001; with no BF sibling they are base verbatim plus the sprite table.
   Brightness stays a City Lights-only rule.
3. **Ownership.** `FOREIGN` lists base paths another DriveDogs mod owns (was `tr_light_flares.sii` →
   TrafficLights; empty since dev.3); they are never emitted. `vehicle/` stays out (MoreVisibility / a later add-on).
4. **No tunnel sprite.** The base game has none and T1 tunnels looked right.

## Consequences
- dev.2 ships 6 more files: `foto_01-03.sii`, `green.sii`, `lights/plane_flares.sii` (8 flares restyled) and
  BF Base's `light_blinking.sii` with the 4 orange blinkers back (vanilla sprite: BF has no precedent for
  `sign_flare_orange_small`).
- The neutral check now covers BF Base's files too (156 files byte-identical).
- A BF update that adds a sprite rule flows into the table on regenerate; a BF copy of one of these files makes
  the env module skip it automatically.

## Amendment (2026-11-19, dev.3): `tr_light_flares.sii` comes back under the BF Base restore
- The DriveDogs TrafficLights add-on is deprecated (2026-10-28, World ADR-0006) and no longer loaded. BF Traffic
  Addon ships no `unit/hookup`, so BF Base's pre-1.62 copy is the only one in play and `flare.traffic.white.rh`
  (base 1.62, steady white tram aspect on red) is missing in-game. `FOREIGN` is now empty and decision 2 covers it.
- **Twin rule.** A restored unit with no `.always` sibling takes BF's edits from its *twin*: a unit in the same base
  file that BF ships, same class, whose base block differs in at most 1 value (`TWIN_MAX_KEYS`). `white.rh` vs
  `white.r` differ only in the sprite, so it gets BF's `scale_factor` 1.5 and keeps its own `tr_yellow_tram`.
  No other restored unit has a twin (orange blink2-5 and the 2 garage units stay as before).
- **Dangling models.** BF Base's copy carries 3 units the base game does not have (`flare.traffic.*_left` ->
  `/model/flare/tr_left_*.pmd`, which exist nowhere; unused, no log lines). The model check keeps a dangling path the
  source file already carries (noted) and still fails on one the generator introduces.
- Traffic-light timing, locators and lens textures stay World's; this mod only ships BF's file plus the dropped unit.
