#!/usr/bin/env python3
"""
Generates the mod's cover/thumbnail image for the ETS2 Mod Manager listing.
Convention shared with the BetterFlares packages: 276x162 JPEG, referenced
via manifest.sii's `icon:` field.

Composited at 4x (1104x648) then downscaled for anti-aliasing.

The version badge is read from manifest.sii's package_version, so the cover
always matches the build - pack.config.json's prePack runs this before every
pack.

The game badge (bottom-left, one colour per game so the ETS2 and ATS covers
differ at thumbnail size) reads the game from pack.config.json, so it can't
disagree with the pack.
"""
import json
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
LOGO_PATH = ROOT / "logo.png"
OUT_PATH = ROOT / "src" / "cover.jpg"
MANIFEST_PATH = ROOT / "src" / "manifest.sii"
PACK_CONFIG_PATH = ROOT / "pack.config.json"

SCALE = 4
FINAL_SIZE = (276, 162)
CANVAS_SIZE = (FINAL_SIZE[0] * SCALE, FINAL_SIZE[1] * SCALE)

FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_REG = r"C:\Windows\Fonts\arial.ttf"

BG_TOP = (8, 10, 16)
BG_BOTTOM = (18, 22, 32)
LAMP_COLOR = (255, 176, 72)   # sodium street lamp
TITLE_COLOR = (255, 255, 255)
SUBTITLE_COLOR = (255, 196, 84)
BADGE_COLOR = (255, 196, 84)
BADGE_TEXT_COLOR = (20, 16, 10)
# Same values as the DriveDogs family reference (DriveDogs Pets): ETS2 blue, ATS red.
GAME_BADGES = {"ets2": ("ETS2", (40, 110, 210)), "ats": ("ATS", (200, 45, 45))}
GAME_TEXT_COLOR = (255, 255, 255)


def read_version():
    m = re.search(r'^\s*package_version:\s*"([^"]+)"', MANIFEST_PATH.read_text(encoding="utf-8"), re.MULTILINE)
    if not m:
        raise SystemExit(f"No package_version in {MANIFEST_PATH}")
    return m.group(1)


def read_game():
    game = json.loads(PACK_CONFIG_PATH.read_text(encoding="utf-8-sig")).get("game", "ets2")
    if game not in GAME_BADGES:
        raise SystemExit(f"{PACK_CONFIG_PATH} game {game!r}: no badge defined")
    return game


def make_background(size):
    w, h = size
    img = Image.new("RGB", size, BG_BOTTOM)
    px = img.load()
    for y in range(h):
        t = y / (h - 1)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    return img


def add_street_lamps(img):
    """Sodium-orange street lamps on both road edges, receding into the distance: pole, arm over the road,
    warm glow and a light pool on the asphalt. Kept in the lower band, clear of the logo and the title."""
    w, h = img.size
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    poles = ImageDraw.Draw(img)
    road_top_y = h * 0.72
    for side in (-1, 1):                                  # -1 left edge, +1 right edge
        for t in (0.15, 0.45, 0.68, 0.85):                # 0 = bottom of the picture, 1 = horizon
            k = 1 - t * 0.8                               # perspective scale
            x = w * (0.50 + side * (0.22 - 0.165 * t))    # just outside the road edge
            base_y = h - (h - road_top_y) * t
            top_y = base_y - h * 0.34 * k
            lamp = (x - side * w * 0.035 * k, top_y + h * 0.01 * k)
            poles.line([(x, base_y), (x, top_y)], fill=(58, 62, 72), width=max(1, int(8 * k)))
            poles.line([(x, top_y), lamp], fill=(58, 62, 72), width=max(1, int(6 * k)))
            r = h * 0.09 * k
            gd.ellipse([lamp[0] - r, lamp[1] - r, lamp[0] + r, lamp[1] + r], fill=(*LAMP_COLOR, 90))
            pr = r * 1.4
            gd.ellipse([lamp[0] - pr, base_y - pr * 0.2, lamp[0] + pr, base_y + pr * 0.2], fill=(*LAMP_COLOR, 55))
            c = h * 0.016 * k
            gd.ellipse([lamp[0] - c, lamp[1] - c, lamp[0] + c, lamp[1] + c], fill=(255, 244, 214, 255))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=w * 0.008))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"), (0, 0))
    return img


def add_road(img):
    w, h = img.size
    draw = ImageDraw.Draw(img)
    road_top_y = int(h * 0.72)
    draw.polygon(
        [
            (w * 0.30, h),
            (w * 0.70, h),
            (w * 0.56, road_top_y),
            (w * 0.44, road_top_y),
        ],
        fill=(28, 30, 36),
    )
    # center dashes
    dash_w = w * 0.01
    for i in range(4):
        t0 = i / 4
        t1 = (i + 0.5) / 4
        y0 = int(h - (h - road_top_y) * t0)
        y1 = int(h - (h - road_top_y) * t1)
        x0 = w * 0.50 - dash_w * (1 - t0) * 0.5
        x1 = w * 0.50 + dash_w * (1 - t0) * 0.5
        draw.rectangle([x0, y1, x1, y0], fill=(120, 110, 90))
    return img


def paste_logo(img):
    logo = Image.open(LOGO_PATH).convert("RGBA")
    target_h = int(img.height * 0.62)
    ratio = target_h / logo.height
    target_w = int(logo.width * ratio)
    logo = logo.resize((target_w, target_h), Image.LANCZOS)

    pad = int(img.height * 0.06)
    pos = (pad, pad)

    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow_logo = Image.new("RGBA", logo.size, (0, 0, 0, 160))
    shadow_logo.putalpha(logo.split()[3])
    shadow.paste(shadow_logo, (pos[0] + 6, pos[1] + 6), shadow_logo)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=8))

    base = img.convert("RGBA")
    base = Image.alpha_composite(base, shadow)
    base.paste(logo, pos, logo)
    return base.convert("RGB")


def fit_font(draw, text, font_path, max_width, start_size, min_size=10):
    size = start_size
    while size > min_size:
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(font_path, min_size)


def draw_with_outline(draw, pos, text, font, fill, outline=(0, 0, 0), width=2):
    x, y = pos
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font, fill=outline)
    draw.text((x, y), text, font=font, fill=fill)


def add_text(img):
    draw = ImageDraw.Draw(img)
    w, h = img.size

    x_start = w * 0.40
    max_width = w * 0.97 - x_start

    title_lines = ["City", "Lights"]
    subtitle = "Better Flares v4.9 add-on"

    title_size = int(h * 0.135)
    title_font = None
    for line in title_lines:
        f = fit_font(draw, line, FONT_BOLD, max_width, title_size)
        title_size = min(title_size, f.size)
        title_font = f
    title_font = ImageFont.truetype(FONT_BOLD, title_size)

    subtitle_font = fit_font(draw, subtitle, FONT_REG, max_width, int(h * 0.06))

    line_bbox = draw.textbbox((0, 0), "Ag", font=title_font)
    line_h = (line_bbox[3] - line_bbox[1]) * 1.15

    total_h = line_h * len(title_lines) + line_h * 0.9
    y = h * 0.50 - total_h / 2

    for line in title_lines:
        draw_with_outline(draw, (x_start, y), line, title_font, TITLE_COLOR, width=3)
        y += line_h

    y += line_h * 0.15
    draw_with_outline(draw, (x_start, y), subtitle, subtitle_font, SUBTITLE_COLOR, width=2)
    return img


def pill(img, text, fill, text_fill, anchor):
    """A rounded pill holding `text`; anchor = ("right", "top") for the version, ("left", "bottom") for the
    game - legible at the final 276x162 size."""
    draw = ImageDraw.Draw(img, "RGBA")
    w, h = img.size
    font = ImageFont.truetype(FONT_BOLD, int(h * 0.06))
    bbox = draw.textbbox((0, 0), text, font=font)
    pad_x, pad_y, margin = h * 0.02, h * 0.015, h * 0.03
    pw, ph = (bbox[2] - bbox[0]) + 2 * pad_x, (bbox[3] - bbox[1]) + 2 * pad_y
    x0 = w - margin - pw if anchor[0] == "right" else margin
    y0 = margin if anchor[1] == "top" else h - margin - ph
    draw.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=ph / 2, fill=(*fill, 235))
    draw.text((x0 + pad_x - bbox[0], y0 + pad_y - bbox[1]), text, font=font, fill=text_fill)
    return img


def main():
    version, game = read_version(), read_game()
    img = make_background(CANVAS_SIZE)
    img = add_road(img)
    img = add_street_lamps(img)
    img = paste_logo(img)
    img = add_text(img)
    img = pill(img, f"v{version}", BADGE_COLOR, BADGE_TEXT_COLOR, ("right", "top"))
    label, colour = GAME_BADGES[game]
    img = pill(img, label, colour, GAME_TEXT_COLOR, ("left", "bottom"))
    img = img.resize(FINAL_SIZE, Image.LANCZOS)
    img.save(OUT_PATH, "JPEG", quality=92)
    print(f"Wrote {OUT_PATH} ({img.size[0]}x{img.size[1]}, v{version}, {label})")


if __name__ == "__main__":
    main()
