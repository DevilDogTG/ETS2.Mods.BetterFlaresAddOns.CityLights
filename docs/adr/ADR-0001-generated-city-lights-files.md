# ADR-0001: Generate Better Flares City Lights' files with base-game brightness and the 1.62 units

- Status: accepted (2026-11-18)
- Context: game ETS2 1.62, Better Flares Base 4.9.1 + City Lights 4.9 (plain, not "with Fog")

## Context
Better Flares City Lights (BF CL) ships whole copies of 141 `unit/hookup/lights/**` files (139 at base-game paths). It
restyles 530 `light_source` units: flare sprites `lamp_*k` + scaling, warmer hue / lower saturation, narrower cones, and
deliberately darker light (diffuse median x0.30 of the base game, specular x0.40, ambient x0.10). 74 of its lights
are brighter than the base game.

Its copies predate 1.62, so while it is loaded 143 base units are missing (`light.fill.*.always`, custom `bb/gg/rr`
fills, two garage units, `template.light.lamp.*.always`, `light.spot.b.fadelong.30m.deg130.always`). They are used
by 19 base models, all underground / indoor fill light (1.62 underground depots, player garages, Helsinki bus
station, Eindhoven museum).

ETS2 loads a file path from the highest mod only and a unit name must be unique, so changing any BF CL unit means
shipping the whole file. A hand-edited copy goes stale on the next BF or game update (seen in MoreVisibility 1.x).

## Decision
`tools/generate_citylights.py` regenerates BF CL's files from the extracted base game and BF (module `city_lights`):

1. **Brightness.** For each unit BF styles, take BF's block and edit only the first component of `diffuse_color` /
   `specular_color` to `max(BF, intensity x base game)`; `ambient_color` has its own lever (`None` = BF's).
   Everything else (sprite, hue, saturation, angles, range, scaling) stays BF's, byte-for-byte. Lights whose `setup`
   unit differs from the base game (lux vs lumen; 3) or that have no base twin (3) keep BF's values.
2. **1.62 restore.** A base unit missing from BF's copy of its file is appended to that file. When it is the
   `.always` twin of a unit BF styles (141 of 143), it is BF's sibling block renamed plus every key where the base
   unit differs from its base sibling (`always_on`); then rule 1 applies against its own base value. Otherwise
   (the two near-white garage units) the base block is used verbatim. A missing unit BF defines in another file is
   skipped and reported.
3. **Files.** Output paths are BF CL's own; a file equal to BF's is not written. `src/unit/hookup` is owned by the
   generator and cleared on each run. Every `model:` must resolve in the base game or BF, or the run fails before
   writing. Versions are pinned (base 1.62, BF 4.9.1) and checked against the extraction metadata; the generator
   refuses ATS.
4. **Checks.** `--neutral --out <dir>` (levers off, restore off, every file emitted) must equal BF CL byte-for-byte,
   and a second run must reproduce `src/` byte-for-byte. `src/unit/**` is `-text` in git.

## Consequences
- The mod ships files derived from BF CL. Avelium allows add-ons that require the original mods; shipping
  derived files is not explicitly covered, so ask before any public upload.
- A BF update that re-copies the files with the 1.62 units makes the restore report empty (nothing to restore);
  a BF update that changes values flows through on regenerate.
- Users of "City Lights Addon with Fog" would get plain-CL sprite paths; not supported (stated in the description).
- Environment lights BF never touches (beacons, Genoa, Akureyri, dealer, coloured omni) and a tunnel sprite are a
  separate module, added after the first test build so each build changes one lever group.
