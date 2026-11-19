#!/usr/bin/env python3
"""
Generates the add-on's environment light units from the base game and Better Flares City Lights.

Module `city_lights` (ADR-0001): for every `unit/hookup/**.sii` file Better Flares City Lights ships at a
base-game path, write the same path with
  1. every unit BF styles: BF's own block, with only the intensity tokens raised toward the base game's
     value (levers below) - sprite, hue / saturation, angles, range and scaling stay BF's;
  2. every unit the base game has and BF's (pre-1.62) copy lacks: BF's styling taken from its sibling
     (`<name>.always` -> `<name>`) plus the unit's own base differences (`always_on`), or the base
     block verbatim when it has no sibling.
Step 2 also runs on Better Flares Base's files at base-game paths (outside `vehicle/`).

Module `env` (ADR-0002): base files under `unit/hookup` that no BF pack ships get BF's sprite for every
flare whose vanilla sprite BF replaces elsewhere (table learned from BF at build time: base model -> BF
model + scaling). Lights and flares BF has no precedent for stay vanilla.

ETS2 replaces whole files, so an output file carries every BF value; lines are edited in place (value
token only) and line endings stay BF's. A file equal to its source is not written. Re-run after every game
or Better Flares update.

    python tools/generate_citylights.py                   # regenerate src/unit/hookup
    python tools/generate_citylights.py --neutral --out <dir>   # identity run: must equal BF byte-for-byte
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_ROOT = ROOT / "src"
OWNED_DIR = "unit/hookup"            # every generated file lives under src/unit/hookup

sys.path.insert(0, str(Path.home() / ".agent-brains/profiles/scs-mod-developer/skills/megapack/scripts"))
from megapack import base_dir, ref_exists, reference_root, repo_game  # noqa: E402

GAME = "ets2"
BASE_VERSION = "1.62"
BF_VERSION = "4.9.1"
BF_ROOT = reference_root(repo_game(ROOT)) / "local" / "better-flares" / BF_VERSION
BF_CL = BF_ROOT / "bf_city_lights_v4.9"       # plain City Lights; the Fog variant (lamp_*k_fog sprites) is not supported
BF_PACKS = (BF_ROOT / "bf_base_v4.9.1", BF_CL)

# --- Levers (log every test build in docs/tuning.md) ----------------------------------------------------
# intensity  diffuse_color / specular_color first component := max(BF, intensity x base game).
#            1.0 = base-game brightness; BF's lights that are already brighter stay BF's. None = BF's values.
# ambient    ambient_color first component, same rule. None = BF's (BF keeps ambient at ~0.1 x base).
# restore    re-add the units BF's pre-1.62 copies drop.
# env        BF sprites on base env flares BF leaves vanilla (module `env`).
LEVERS = dict(intensity=1.0, ambient=None, restore=True, env=True)
NEUTRAL = dict(intensity=None, ambient=None, restore=False, env=False)
# ---------------------------------------------------------------------------------------------------------

INTENSITY_KEYS = ("diffuse_color", "specular_color")
SIBLING_SUFFIX = ".always"
TWIN_MAX_KEYS = 1                             # restored unit with no .always sibling: BF's edits from a 1-key twin
SPRITE_KEYS = ("model", "default_scale", "scale_factor", "scaling_start_distance", "scaling_end_distance")
SKIP_PREFIX = "unit/hookup/vehicle/"          # vehicle lights: MoreVisibility / a later add-on, not here
FOREIGN: dict[str, str] = {}                  # base paths another DriveDogs mod owns: never shipped here
# (tr_light_flares.sii was TrafficLights'; that add-on is deprecated, so the BF Base restore now covers it - ADR-0002)

HEADER_RE = re.compile(r"^[ \t]*(\w+)[ \t]*:[ \t]*([\w.]+)[ \t]*\r?\n[ \t]*\{[^\r\n]*\r?\n", re.M)
CLOSE_RE = re.compile(r"^[ \t]*\}[ \t]*(?:\r?\n|$)", re.M)
LINE_RE = re.compile(r"^([ \t]*)(\w+(?:\[\d*\])?)([ \t]*:[ \t]*)([^\r\n#]*?)([ \t]*(?:#[^\r\n]*)?)(\r?\n|$)", re.M)
FIRST_NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
MODEL_RE = re.compile(r'^[ \t]*model[ \t]*:[ \t]*"([^"]+)"', re.M)


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def read(path: Path) -> str:
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as f:
        return f.read()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
        f.write(text)


class Unit:
    """One `class : name { ... }` block, kept as its exact text."""

    def __init__(self, cls: str, name: str, text: str, start: int, end: int):
        self.cls, self.name, self.text, self.start, self.end = cls, name, text, start, end

    def values(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for m in LINE_RE.finditer(self.body()):
            out.setdefault(m.group(2), []).append(m.group(4).strip())
        return out

    def body(self) -> str:
        return self.text[HEADER_RE.match(self.text).end():]


def units(text: str) -> list[Unit]:
    out = []
    for h in HEADER_RE.finditer(text):
        c = CLOSE_RE.search(text, h.end())
        if not c:
            fail(f"unit {h.group(2)}: no closing brace")
        out.append(Unit(h.group(1), h.group(2), text[h.start():c.end()], h.start(), c.end()))
    return out


def first_number(value: str) -> tuple[float, re.Match] | None:
    m = FIRST_NUM_RE.search(value)
    return (float(m.group()), m) if m else None


def fmt(value: float) -> str:
    text = f"{round(value, 4):.4f}".rstrip("0").rstrip(".")
    return text or "0"


def set_key(block: str, key: str, edit) -> str:
    """Rewrite the value token of every `key:` line in a unit block through `edit(old) -> new`."""
    def sub(m):
        if m.group(2) != key:
            return m.group(0)
        return m.group(1) + m.group(2) + m.group(3) + edit(m.group(4)) + m.group(5) + m.group(6)
    return LINE_RE.sub(sub, block)


def raise_intensity(block: str, key: str, factor: float, vanilla: str) -> tuple[str, bool]:
    """First component of `key` := max(current, factor x vanilla's). Returns (block, changed)."""
    van = first_number(vanilla)
    changed = False

    def edit(old: str) -> str:
        nonlocal changed
        cur = first_number(old)
        if not cur or not van:
            return old
        target = factor * van[0]
        if target <= cur[0]:
            return old
        changed = True
        token = van[1].group() if factor == 1.0 else fmt(target)
        return old[:cur[1].start()] + token + old[cur[1].end():]
    return set_key(block, key, edit), changed


def newline_of(text: str) -> str:
    return "\r\n" if text.count("\r\n") * 2 >= text.count("\n") else "\n"


def merge_sibling(bf_sib: Unit, base_sib: Unit, base_unit: Unit, nl: str) -> str:
    """BF's sibling block, renamed, plus every key where the base unit differs from its base sibling."""
    block = bf_sib.text.replace(bf_sib.name, base_unit.name, 1)
    want, have = base_unit.values(), base_sib.values()
    for key in sorted(set(want) | set(have)):
        if want.get(key) == have.get(key):
            continue
        if key not in want:                                   # base unit drops a key its sibling has
            block = LINE_RE.sub(lambda m: "" if m.group(2) == key else m.group(0), block)
        elif key in Unit("", "", block, 0, 0).values():       # same key, other value
            vals = iter(want[key])
            block = set_key(block, key, lambda old: next(vals, old))
        else:                                                 # new key: insert before the closing brace
            close = CLOSE_RE.search(block, HEADER_RE.match(block).end())
            lines = "".join(f"\t{key}: {v}{nl}" for v in want[key])
            block = block[:close.start()] + lines + block[close.start():]
    return block


def nearest_twin(base_unit: Unit, base_units: dict[str, Unit], bf_by_name: dict[str, Unit]) -> str | None:
    """A unit in the same base file that BF ships, same class, whose base block differs from this one in at most
    TWIN_MAX_KEYS values (e.g. flare.traffic.white.rh vs .white.r: the sprite only). Closest wins, then name."""
    want = base_unit.values()
    best = None
    for name, other in base_units.items():
        if name == base_unit.name or name not in bf_by_name or other.cls != base_unit.cls:
            continue
        have = other.values()
        diff = sum(want.get(k) != have.get(k) for k in set(want) | set(have))
        if diff <= TWIN_MAX_KEYS and (best is None or (diff, name) < best):
            best = (diff, name)
    return best[1] if best else None


def sprite_table(base: Path) -> dict[str, tuple[str, ...]]:
    """Base flare model -> BF's (model, scaling keys...), the most common treatment over both BF packs.
    `-` = BF leaves that key unset."""
    seen: dict[str, Counter] = {}
    for pack in BF_PACKS:
        for f in sorted((pack / OWNED_DIR).rglob("*.sii")):
            rel = f.relative_to(pack).as_posix()
            if rel.startswith(SKIP_PREFIX) or not (base / rel).is_file():
                continue
            twins = {u.name: u for u in units(read(base / rel))}
            for u in units(read(f)):
                b = twins.get(u.name)
                if b is None:
                    continue
                bm, uv = b.values().get("model", [None])[0], u.values()
                if bm and bm != uv.get("model", [None])[0]:
                    seen.setdefault(bm, Counter())[tuple(uv.get(k, ["-"])[0] for k in SPRITE_KEYS)] += 1
    return {bm: sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for bm, c in seen.items()}


def apply_sprite(block: str, rule: tuple[str, ...], nl: str) -> str:
    """Set BF's sprite + scaling keys on one block: edit present keys in place, insert missing ones."""
    old_model = Unit("", "", block, 0, 0).values()["model"][0]
    for key, val in zip(SPRITE_KEYS, rule):
        if val == "-":
            continue
        if key in Unit("", "", block, 0, 0).values():
            block = set_key(block, key, lambda old, v=val: v)
        else:
            indent = re.search(r"^([ \t]*)model[ \t]*:", block, re.M).group(1)
            close = CLOSE_RE.search(block, HEADER_RE.match(block).end())
            block = block[:close.start()] + f"{indent}{key}: {val}{nl}" + block[close.start():]
    if Unit("", "", block, 0, 0).values().get("model_light_source", [None])[0] == old_model:
        block = set_key(block, "model_light_source", lambda old: rule[0])
    return block


def restyle(text: str, table: dict, report: Counter, notes: list[str], rel: str, only: set | None = None) -> str:
    """Apply the sprite table to every unit (or the named ones) in `text`, back to front."""
    nl = newline_of(text)
    for u in reversed(units(text)):
        if only is not None and u.name not in only:
            continue
        model = u.values().get("model", [None])[0]
        if model is None:
            if u.cls == "light_source":
                report["env lights kept base (BF style = base at base brightness)"] += 1
            continue
        if model not in table:
            report["env flares kept vanilla (no BF sprite for it)"] += 1
            notes.append(f"kept vanilla sprite {model}: {u.name}  [{rel}]")
            continue
        text = text[:u.start] + apply_sprite(u.text, table[model], nl) + text[u.end:]
        report["env flares given BF's sprite"] += 1
        notes.append(f"BF sprite {model} -> {table[model][0]}: {u.name}  [{rel}]")
    return text


def check_versions(base: Path) -> None:
    if repo_game(ROOT) != GAME:
        fail(f"this generator is for {GAME}; pack.config.json says {repo_game(ROOT)!r}")
    meta = base / "_extract-meta.md"
    if not meta.is_file():
        fail(f"{base} has no extraction - run extract-reference for {GAME} {BASE_VERSION}")
    m = re.search(r"^- game_version:\s*(\S+)", read(meta), re.M)
    if not m or not m.group(1).startswith(BASE_VERSION + "."):
        fail(f"base extraction is {m.group(1) if m else '?'}, generator pins {BASE_VERSION}")
    for pack in BF_PACKS:
        if not (pack / "manifest.sii").is_file():
            fail(f"{pack} missing - extract Better Flares {BF_VERSION}")


def generate(levers: dict, report: Counter, notes: list[str]) -> dict[str, tuple[str, Path]]:
    """rel path -> (text, source file it must differ from to be shipped)."""
    base = base_dir(reference_root(GAME), BASE_VERSION)
    check_versions(base)
    bf_defined = {}                                           # unit name -> BF file (all BF packs)
    top: dict[str, Path] = {}                                 # rel -> pack whose copy loads (City Lights wins)
    for pack in BF_PACKS:
        for f in sorted((pack / OWNED_DIR).rglob("*.sii")):
            rel = f.relative_to(pack).as_posix()
            for u in units(read(f)):
                bf_defined.setdefault(u.name, rel)
            if not rel.startswith(SKIP_PREFIX) and rel not in FOREIGN:
                top[rel] = pack
    table = sprite_table(base) if levers["env"] else {}

    out: dict[str, tuple[str, Path]] = {}
    for rel in sorted(top):
        pack = top[rel]
        bf_file, base_file = pack / rel, base / rel
        bf_text = read(bf_file)
        if not base_file.is_file():
            report["files BF-only (left to BF)"] += 1
            out[rel] = (bf_text, bf_file)
            continue
        if pack != BF_CL and not levers["restore"]:
            out[rel] = (bf_text, bf_file)
            continue
        nl = newline_of(bf_text)
        base_units = {u.name: u for u in units(read(base_file))}
        bf_units = units(bf_text)
        bf_by_name = {u.name: u for u in bf_units}

        # 1. brightness on BF's own units (edit back to front so offsets stay valid)
        text = bf_text
        for u in reversed(bf_units if pack == BF_CL else []):  # brightness: City Lights only
            van = base_units.get(u.name)
            if u.cls != "light_source":
                continue
            report["BF lights"] += 1
            if van is None:
                report["BF lights without a base twin (kept BF)"] += 1
                notes.append(f"kept BF (no base twin): {u.name}  [{rel}]")
                continue
            uv, vv = u.values(), van.values()
            if uv.get("setup") != vv.get("setup"):
                report["BF lights with another setup (kept BF)"] += 1
                notes.append(f"kept BF (setup {vv.get('setup')} -> {uv.get('setup')}): {u.name}  [{rel}]")
                continue
            block, changed = u.text, False
            for key, factor in [(k, levers["intensity"]) for k in INTENSITY_KEYS] + [("ambient_color", levers["ambient"])]:
                if factor is None or key not in uv or key not in vv:
                    continue
                block, c = raise_intensity(block, key, factor, vv[key][0])
                changed |= c
            if changed:
                report["BF lights raised"] += 1
                text = text[:u.start] + block + text[u.end:]
            else:
                report["BF lights already at target"] += 1

        # 2. units BF's copy drops, appended in base order before the file's closing brace
        if levers["restore"]:
            added = []
            for name, bu in base_units.items():
                if name in bf_by_name:
                    continue
                if name in bf_defined:
                    report["dropped but defined elsewhere in BF (skipped)"] += 1
                    notes.append(f"skipped (BF defines it in {bf_defined[name]}): {name}  [{rel}]")
                    continue
                sib = name[:-len(SIBLING_SUFFIX)] if name.endswith(SIBLING_SUFFIX) else None
                twin = None if sib else nearest_twin(bu, base_units, bf_by_name)
                if sib and sib in bf_by_name and sib in base_units:
                    block = merge_sibling(bf_by_name[sib], base_units[sib], bu, nl)
                    report["restored, BF-styled from sibling"] += 1
                elif twin:
                    block = merge_sibling(bf_by_name[twin], base_units[twin], bu, nl)
                    report["restored, BF-styled from twin"] += 1
                    notes.append(f"restored, BF-styled from twin {twin}: {name}  [{rel}]")
                else:
                    block = bu.text.replace("\r\n", "\n").replace("\n", nl)
                    report["restored as base (no sibling)"] += 1
                    notes.append(f"restored as base (no BF sibling): {name}  [{rel}]")
                    if pack != BF_CL and table:              # BF Base file: BF's sprite where it has one
                        block = restyle(block, table, report, notes, rel)
                if bu.cls == "light_source" and block is not bu.text:
                    merged = Unit(bu.cls, name, block, 0, 0).values()
                    vv = bu.values()
                    for key, factor in [(k, levers["intensity"]) for k in INTENSITY_KEYS] + [("ambient_color", levers["ambient"])]:
                        if factor is not None and key in merged and key in vv and merged.get("setup") == vv.get("setup"):
                            block, _ = raise_intensity(block, key, factor, vv[key][0])
                if not block.endswith(("\n", "\r")):
                    block += nl
                added.append(block)
            if added:
                close = text.rstrip().rfind("}")
                text = text[:close] + nl + nl.join(added) + text[close:]
        out[rel] = (text, bf_file)

    # module env: base files no BF pack ships
    if levers["env"]:
        for f in sorted((base / OWNED_DIR).rglob("*.sii")):
            rel = f.relative_to(base).as_posix()
            if rel.startswith(SKIP_PREFIX) or rel in FOREIGN or any((p / rel).is_file() for p in BF_PACKS):
                continue
            text = read(f)
            if not re.search(r"^\s*(light_source|flare\w*)\s*:", text, re.M):
                continue
            out[rel] = (restyle(text, table, report, notes, rel), f)
    return out


def check_models(files: dict[str, tuple[str, Path]], notes: list[str]) -> None:
    """Fail on a model: path that resolves nowhere, unless the source file already carries it (BF's own dangling
    units, e.g. BF Base's unused flare.traffic.*_left -> /model/flare/tr_left_*.pmd): those ship as BF has them."""
    base = base_dir(reference_root(GAME), BASE_VERSION)
    missing = set()
    for rel, (text, source) in files.items():
        inherited = set(MODEL_RE.findall(read(source)))
        for path in MODEL_RE.findall(text):
            p = path.lstrip("/")
            if any((pack / p).is_file() for pack in BF_PACKS) or ref_exists(base, p):
                continue
            if path in inherited:
                notes.append(f"dangling model kept as the source has it: {path}  [{rel}]")
                continue
            missing.add(f"{path}  [{rel}]")
    if missing:
        fail("model paths resolve in neither the base game nor Better Flares:\n  " + "\n  ".join(sorted(missing)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--neutral", action="store_true", help="identity run: levers off, every file emitted")
    ap.add_argument("--out", type=Path, help="write here instead of src/ (required with --neutral)")
    ap.add_argument("--notes", action="store_true", help="list every kept / restored unit")
    args = ap.parse_args()
    if args.neutral and not args.out:
        ap.error("--neutral needs --out (never overwrite src/ with BF's own files)")

    report, notes = Counter(), []
    files = generate(NEUTRAL if args.neutral else LEVERS, report, notes)
    check_models(files, notes)

    target = args.out or OUT_ROOT
    owned = target / OWNED_DIR
    if owned.exists():
        shutil.rmtree(owned)
    written = 0
    for rel, (text, source) in sorted(files.items()):
        if not args.neutral and text == read(source):
            continue
        write(target / rel, text)
        written += 1

    for k, v in report.items():
        print(f"{v:5d}  {k}")
    print(f"{written:5d}  files written to {owned}")
    if args.notes:
        print("\n".join(notes))


if __name__ == "__main__":
    main()
