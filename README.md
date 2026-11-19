# DriveDogs: Better Flares City Lights

An ETS2 add-on for **Better Flares v4.9 - City Lights Addon** (by Avelium). Environment lights keep the Better
Flares look (flare sprites, colour shift, beam shape) but light the world about as brightly as the base game, the
lights City Lights drops on game 1.62 come back, and environment lights Better Flares never touches get the same
style.

**Status: in development (`1.0.0-dev.3`: brightness + 1.62 restore + Better Flares sprites on untouched environment flares + the missing white tram traffic flare).** ETS2 1.62 only, Better Flares Base 4.9.1 + City Lights 4.9. An ATS twin
repo comes later.

## Load order
Top = highest priority in Mod Manager:
1. DriveDogs: Better Flares City Lights
2. DriveDogs: Better Flares More Visibility (optional)
3. Better Flares - Traffic Addon (optional)
4. Better Flares - Headlights.2 (optional)
5. Better Flares - Headlights.1 (optional)
6. Better Flares - City Lights Addon v4.9
7. Better Flares - Base v4.9.1

## What it changes
- **Brightness:** City Lights sets environment lights to about 30% of the base game's lumen (median). This mod
  puts each light back to its own base-game lumen and keeps Better Flares' sprite, hue / saturation shift, cone
  angles and flare scaling.
- **1.62 restore:** City Lights ships whole copies of 139 `unit/hookup/lights/**` files made before 1.62, so
  143 newer `light_source` units are missing while it is loaded (underground / indoor fill lights: 1.62
  underground depots, player garages, Helsinki bus station, Eindhoven museum). The regenerated files carry the
  base game's full unit list, so they come back. Better Flares Base's `light_blinking.sii` (4 orange blinkers)
  and `tr_light_flares.sii` (`flare.traffic.white.rh`, the steady white tram aspect on red) have the same
  problem; they come back too, styled like their Better Flares twin where one exists.
- **Untouched environment flares:** speed-camera flashes, plane / obstruction lights and green lamps get the
  sprite Better Flares uses for the same vanilla sprite elsewhere ([ADR-0002](docs/adr/ADR-0002-env-flares-and-bf-base-restore.md)).
  Blue beacons and the yellow garage lamp have no Better Flares sprite and stay vanilla; the untouched
  coloured / decorative lights (Akureyri pier, Genoa bridge, coloured omni, `dealer.int.big`) already match
  Better Flares' style at base-game brightness, so they are not shipped. Tunnels get no sprite (the base game
  has none).

Not here: headlights (MoreVisibility), traffic-light timing / locators / lens textures (DriveDogs World), vehicle
interior / plate lights.

## How it works
The `src/unit/` files are **generated, not hand-edited**, from the extracted base game 1.62 and Better Flares 4.9.1,
so a game or Better Flares update is a regenerate, not a re-edit. Design: [ADR-0001](docs/adr/ADR-0001-generated-city-lights-files.md).

`tools/generate_citylights.py` takes each City Lights file at a base-game path and
- keeps every Better Flares unit's own block, raising only `diffuse_color` / `specular_color` intensity to
  `max(Better Flares, intensity x base game)` (`ambient_color` has its own lever, off by default);
- appends the base units City Lights' (and Better Flares Base's) copy lacks, styled from their Better Flares sibling
  or twin;
- writes only files that differ from Better Flares', and fails on any `model:` it introduces that doesn't resolve.

| Lever (`LEVERS`) | Effect |
|---|---|
| `intensity` | diffuse / specular target as a fraction of the base game (`1.0` = base-game brightness, `None` = BF's) |
| `ambient` | ambient target, same rule (`None` = BF's) |
| `restore` | re-add the units City Lights and Better Flares Base drop on 1.62 |
| `env` | Better Flares sprites on environment flares it leaves vanilla |

Test rounds and their values: [`docs/tuning.md`](docs/tuning.md).

## Build
```
python tools/generate_citylights.py                    # regenerate src/unit/hookup (--notes lists kept / restored units)
python tools/generate_citylights.py --neutral --out <dir>   # identity check: must equal City Lights byte-for-byte
python tools/generate_cover.py                         # src/cover.jpg from logo.png + manifest version (also run by prePack)
```
Packed with the `pack-mod` workflow (`pack.config.json`: `drivedog_bf_citylights`, game `ets2`). Output goes to
`output/` (ignored).

## Permission
Better Flares has no licence text. Its author allows add-ons that require the original mods. Referencing Better
Flares sprites is covered; shipping files derived from Better Flares' own is not yet cleared, so no public upload
before asking Avelium (SCS forum t=326854).
