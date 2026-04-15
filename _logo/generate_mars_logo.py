#!/usr/bin/env python3
"""
Generate a MARS (Multi-Arm Robotic Systems) logo
Dark tech / circuit board aesthetic with glowing accents
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import random

# Logo dimensions (wide format)
WIDTH = 1600
HEIGHT = 900

# Color palette — dark tech
BG_TOP = (8, 12, 20)  # near-black navy
BG_BOT = (14, 22, 38)  # slightly lighter deep blue
ACCENT = (0, 200, 140)  # cyan-green glow 
ACCENT2 = (0, 140, 220)  # electric blue secondary
DIM_LINE = (0, 180, 120, 40)  # faint circuit trace
GLOW_COL = (0, 220, 160)  # bright glow node color
TEXT_COL = (215, 245, 240)  # near-white with subtle cyan tint
SUB_COL = (100, 200, 170)  # muted accent for subtitle

random.seed(42)

# ---------------------------------------------------------------------------
# Base image
# ---------------------------------------------------------------------------
img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_TOP)
draw = ImageDraw.Draw(img, "RGBA")

# Vertical gradient background
for y in range(HEIGHT):
    t = y / HEIGHT
    r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
    g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
    b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
    draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))


# ---------------------------------------------------------------------------
# Circuit board trace network
# ---------------------------------------------------------------------------
def draw_circuit_traces(draw, seed=0):
    """Draw an L-shaped circuit trace network across the canvas."""
    rng = random.Random(seed)
    traces = []

    # Generate horizontal + vertical connected traces
    grid_x = list(range(80, WIDTH, 120))
    grid_y = list(range(60, HEIGHT, 110))

    for _ in range(55):
        x1 = rng.choice(grid_x)
        y1 = rng.choice(grid_y)
        # L-shaped trace: go horizontal then vertical
        dx = rng.choice([-1, 1]) * rng.randint(1, 4) * 120
        dy = rng.choice([-1, 1]) * rng.randint(1, 3) * 110
        x2 = max(0, min(WIDTH, x1 + dx))
        y2 = max(0, min(HEIGHT, y1 + dy))
        mid_x, mid_y = x2, y1  # L-bend point

        alpha = rng.randint(18, 55)
        col = (*ACCENT[:3], alpha)
        w = 1 if rng.random() < 0.7 else 2
        draw.line([(x1, y1), (mid_x, mid_y)], fill=col, width=w)
        draw.line([(mid_x, mid_y), (mid_x, y2)], fill=col, width=w)
        traces.append((x1, y1, mid_x, mid_y, x2, y2))

    return traces


traces = draw_circuit_traces(draw, seed=7)

# Glow nodes at trace junctions
rng = random.Random(99)
node_positions = []
for t in traces:
    # mid-bend point and endpoints have a chance to show a node
    for px, py in [(t[0], t[1]), (t[2], t[3])]:
        if rng.random() < 0.35:
            node_positions.append((px, py))

for px, py in node_positions:
    r = rng.randint(3, 6)
    alpha = rng.randint(90, 170)
    # Outer halo
    draw.ellipse(
        [(px - r - 2, py - r - 2), (px + r + 2, py + r + 2)],
        fill=(*GLOW_COL, alpha // 4),
    )
    # Solid node
    draw.ellipse(
        [(px - r, py - r), (px + r, py + r)],
        fill=(*GLOW_COL, alpha),
    )

# ---------------------------------------------------------------------------
# Subtle radial glow behind text (soft light bloom)
# ---------------------------------------------------------------------------
glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow_layer)

cx, cy = WIDTH // 2, HEIGHT // 2 - 30
for radius in range(380, 0, -8):
    alpha = int(32 * (1 - radius / 380) ** 2)
    glow_draw.ellipse(
        [(cx - radius, cy - radius * 0.55), (cx + radius, cy + radius * 0.55)],
        fill=(0, 160, 110, alpha),
    )

# Blur and composite the glow
glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=40))
img.paste(
    Image.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, 0)), glow_layer),
    mask=glow_layer.split()[3],
)

draw = ImageDraw.Draw(img, "RGBA")

# ---------------------------------------------------------------------------
# Horizontal accent bars (top and bottom strips)
# ---------------------------------------------------------------------------
bar_h = 4
# Top bar with gradient fade
for x in range(WIDTH):
    t = abs(x - WIDTH / 2) / (WIDTH / 2)
    alpha = int(200 * (1 - t**1.5))
    draw.line([(x, 0), (x, bar_h - 1)], fill=(*ACCENT, alpha))
    draw.line([(x, HEIGHT - bar_h), (x, HEIGHT - 1)], fill=(*ACCENT, alpha // 2))

# Thin secondary accent line below top bar
for x in range(WIDTH):
    t = abs(x - WIDTH / 2) / (WIDTH / 2)
    alpha = int(80 * (1 - t**2))
    draw.line([(x, bar_h + 2), (x, bar_h + 3)], fill=(*ACCENT2, alpha))


margin = 40
size = 70

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
font_candidates_title = [
    "/System/Library/Fonts/Avenir Next Condensed.ttc",
    "/System/Library/Fonts/SFNS.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
]
font_candidates_sub = [
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Courier.ttc",
]


def load_font(candidates, size):
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


font_title = load_font(font_candidates_title, 469)
font_sub = load_font(font_candidates_sub, 49)
font_label = load_font(font_candidates_sub, 22)

# ---------------------------------------------------------------------------
# MARS title text — with glow layering technique
# ---------------------------------------------------------------------------
title_text = "MARS"

# Use anchor='mm' so PIL centers the text on (tx, ty) exactly
tx = WIDTH // 2
# Position vertical midpoint of text slightly above canvas center
ty_mid = HEIGHT // 2 - 40

# Layer 1: wide outer glow bloom
glow_text_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow_text_layer)
gd.text((tx, ty_mid), title_text, font=font_title, anchor="mm", fill=(*ACCENT, 55))
glow_text_layer = glow_text_layer.filter(ImageFilter.GaussianBlur(radius=28))
img = img.convert("RGBA")
img = Image.alpha_composite(img, glow_text_layer)
img = img.convert("RGB")
draw = ImageDraw.Draw(img, "RGBA")

# Layer 2: medium inner glow
glow2 = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
gd2 = ImageDraw.Draw(glow2)
gd2.text((tx, ty_mid), title_text, font=font_title, anchor="mm", fill=(*ACCENT, 100))
glow2 = glow2.filter(ImageFilter.GaussianBlur(radius=10))
img = img.convert("RGBA")
img = Image.alpha_composite(img, glow2)
img = img.convert("RGB")
draw = ImageDraw.Draw(img, "RGBA")

# Layer 3: tight edge glow
glow3 = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
gd3 = ImageDraw.Draw(glow3)
gd3.text((tx, ty_mid), title_text, font=font_title, anchor="mm", fill=(*ACCENT, 60))
glow3 = glow3.filter(ImageFilter.GaussianBlur(radius=3))
img = img.convert("RGBA")
img = Image.alpha_composite(img, glow3)
img = img.convert("RGB")
draw = ImageDraw.Draw(img, "RGBA")

# Layer 4: sharp crisp text on top
draw.text((tx, ty_mid), title_text, font=font_title, anchor="mm", fill=TEXT_COL)

# Derive rule position from the actual rendered bbox bottom
bbox = draw.textbbox((tx, ty_mid), title_text, font=font_title, anchor="mm")
tw = bbox[2] - bbox[0]

# ---------------------------------------------------------------------------
# Thin horizontal rule between title and subtitle
# ---------------------------------------------------------------------------
rule_y = bbox[3] + 24
rule_w = min(tw + 60, WIDTH - 120)
rule_x0 = (WIDTH - rule_w) // 2
rule_x1 = rule_x0 + rule_w

for x in range(rule_x0, rule_x1):
    t = abs(x - WIDTH / 2) / (rule_w / 2)
    alpha = int(180 * (1 - t**2))
    draw.line([(x, rule_y), (x, rule_y + 1)], fill=(*ACCENT, alpha))

# Small diamond at center of rule
mid = WIDTH // 2
d = 5
draw.polygon(
    [
        (mid, rule_y - d),
        (mid + d, rule_y + 1),
        (mid, rule_y + d + 2),
        (mid - d, rule_y + 1),
    ],
    fill=ACCENT,
)

# ---------------------------------------------------------------------------
# Subtitle
# ---------------------------------------------------------------------------
sub_text = "MULTI-ARM ROBOTIC SYSTEM"
sbbox = draw.textbbox((0, 0), sub_text, font=font_sub)
sw = sbbox[2] - sbbox[0]
sx = (WIDTH - sw) // 2 - sbbox[0]
sy = rule_y + 20

# Subtle glow under subtitle
sub_glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
sgd = ImageDraw.Draw(sub_glow)
sgd.text((sx, sy), sub_text, font=font_sub, fill=(*ACCENT, 90))
sub_glow = sub_glow.filter(ImageFilter.GaussianBlur(radius=4))
img = img.convert("RGBA")
img = Image.alpha_composite(img, sub_glow)
img = img.convert("RGB")
draw = ImageDraw.Draw(img, "RGBA")

draw.text((sx, sy), sub_text, font=font_sub, fill=SUB_COL)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
output_path = "/Users/i/cc/mars_ned2/mars_logo.png"
img.save(output_path, "PNG")
print(f"Logo saved: {output_path}")
print(f"Dimensions: {WIDTH}x{HEIGHT}")
