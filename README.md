# DriveDogs: Better Flares City Lights

An ETS2 add-on for **Better Flares v4.9 - City Lights Addon** (by Avelium). Environment lights keep the Better
Flares look (flare sprites, colour shift, beam shape) but light the world about as brightly as the base game, the
lights City Lights drops on game 1.62 come back, and environment lights Better Flares never touches get the same
style.

**Status: in development (`1.0.0-dev`).** ETS2 1.62 only, Better Flares Base 4.9.1 + City Lights 4.9. An ATS twin
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
  base game's full unit list, so they come back.
- **Planned for 1.0.0:** tunnel lights (City Lights gives them light but no flare sprite) and environment
  units Better Flares leaves vanilla (beacons / plane flares, Genoa bridge, Akureyri pier, `dealer.int.big`,
  coloured `light.omni.*`).

Not here: headlights (MoreVisibility), traffic lights (DriveDogs World), vehicle interior / plate lights.

## How it works
The `src/unit/` files are **generated, not hand-edited**, from the extracted base game and Better Flares, so a
game or Better Flares update is a regenerate, not a re-edit. The generator lands in phase 2 of the 1.0.0 work;
its design will be in `docs/adr/`.

## Build
```
python tools/generate_cover.py     # src/cover.jpg from logo.png + manifest version (also run by prePack)
```
Packed with the `pack-mod` workflow (`pack.config.json`: `drivedog_bf_citylights`, game `ets2`). Output goes to
`output/` (ignored).

## Permission
Better Flares has no licence text. Its author allows add-ons that require the original mods. Referencing Better
Flares sprites is covered; shipping files derived from Better Flares' own is not yet cleared, so no public upload
before asking Avelium (SCS forum t=326854).
